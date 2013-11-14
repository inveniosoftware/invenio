# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""

"""

import os
from tempfile import mkstemp

from flask import current_app, abort
from flask.ext.login import current_user

from invenio.bibtask import task_low_level_submission, \
    bibtask_allocate_sequenceid
from invenio.legacy.bibfield.bibfield_jsonreader import JsonReader
from invenio.config import CFG_TMPSHAREDDIR
from invenio.legacy.dbquery import run_sql
from invenio.modules.deposit.models import Deposition, Agent, \
    DepositionDraftCacheManager
from invenio.ext.logging import register_exception
try:
    from invenio.pidstore_model import PersistentIdentifier
    HAS_PIDSUPPORT = True
except ImportError:
    HAS_PIDSUPPORT = False


def authorize_user(action, **params):
    """
    Check if current user is authorized to perform the action.
    """
    def _authorize_user(obj, dummy_eng):
        from invenio.access_control_engine import acc_authorize_action

        auth, message = acc_authorize_action(
            current_user.get_id(),
            action,
            **dict((k, v() if callable(v) else v)
                   for (k, v) in params.items()))
        if auth != 0:
            current_app.logger.info(message)
            abort(401)

    return _authorize_user


def prefill_draft(form_class, draft_id='_default', clear=True):
    """
    Fill draft values with values from pre-filled cache
    """
    def _prefill_draft(obj, eng):
        draft_cache = DepositionDraftCacheManager.get()
        if draft_cache.has_data():
            d = Deposition(obj)
            draft_cache.fill_draft(
                d, draft_id, form_class=form_class, clear=clear
            )
            d.update()
    return _prefill_draft


def render_form(form_class, draft_id='_default'):
    """
    Renders a form if the draft associated with it has not yet been completed.

    :param form_class: The form class which should be rendered.
    :param draft_id: The name of the draft to create. Must be specified if you
        put more than two ``render_form'''s in your deposition workflow.
    """
    def _render_form(obj, eng):
        d = Deposition(obj)
        draft = d.get_or_create_draft(draft_id, form_class=form_class)

        if draft.is_completed():
            eng.jumpCallForward(1)
        else:
            form = draft.get_form(validate_draft=draft.validate)
            form.validate = True

            d.set_render_context(dict(
                template_name_or_list=form.get_template(),
                deposition=d,
                deposition_type=(
                    None if d.type.is_default() else d.type.get_identifier()
                ),
                uuid=d.id,
                draft=draft,
                form=form,
                my_depositions=Deposition.get_depositions(
                    current_user, type=d.type
                ),
            ))

            d.update()
            eng.halt('Wait for form submission.')
    return _render_form


def create_recid():
    """
    Create a new record id.
    """
    def _create_recid(obj, dummy_eng):
        d = Deposition(obj)
        sip = d.get_latest_sip(include_sealed=False)
        if sip is None:
            raise Exception("No submission information package found.")

        if 'recid' not in sip.metadata:
            sip.metadata['recid'] = run_sql(
                "INSERT INTO bibrec (creation_date, modification_date) "
                "VALUES (NOW(), NOW())"
            )
        d.update()
    return _create_recid


def mint_pid(pid_field='doi', pid_creator=None, pid_store_type='doi',
             existing_pid_checker=None):
    """
    Register a persistent identifier internally.

    :param pid_field: The recjson key for where to look for a pre-reserved pid.
        Defaults to 'pid'.
    :param pid_creator: Callable taking one argument (the recjson) that when
        called will generate and return a pid string.
    :param pid_store_type: The PID store type. Defaults to 'doi'.
    :param existing_pid_checker: A callable taking two arguments
        (pid_str, recjson) that will check if an pid found using ``pid_field''
        should be registered or not.
    """
    if not HAS_PIDSUPPORT:
        def _mint_pid_dummy(dummy_obj, dummy_eng):
            pass
        return _mint_pid_dummy

    def _mint_pid(obj, dummy_eng):
        d = Deposition(obj)
        recjson = d.get_latest_sip(include_sealed=False).metadata

        if 'recid' not in recjson:
            raise Exception("'recid' not found in sip metadata.")

        pid_text = None
        pid = recjson.get(pid_field, None)
        if not pid:
            # No pid found in recjson, so create new pid with user supplied
            # function.
            current_app.logger.info("Registering pid %s" % pid_text)
            pid_text = recjson[pid_field] = pid_creator(recjson)
        else:
            # Pid found - check if it should be minted
            if existing_pid_checker and existing_pid_checker(pid, recjson):
                pid_text = pid

        # Create an assign pid internally - actually registration will happen
        # asynchronously later.
        if pid_text:
            current_app.logger.info("Registering pid %s" % pid_text)
            pid_obj = PersistentIdentifier.create(pid_store_type, pid_text)
            if pid_obj is None:
                pid_obj = PersistentIdentifier.get(pid_store_type, pid_text)

            try:
                pid_obj.assign("rec", recjson['recid'])
            except Exception:
                register_exception(alert_admin=True)

        d.update()
    return _mint_pid


def prepare_sip():
    """
    Prepare a submission information package
    """
    def _prepare_sip(obj, dummy_eng):
        d = Deposition(obj)

        sip = d.get_latest_sip(include_sealed=False)
        if sip is None:
            sip = d.create_sip()

        sip.metadata['fft'] = sip.metadata['files']
        del sip.metadata['files']

        sip.agents = [Agent(role='creator', from_request_context=True)]
        d.update()
    return _prepare_sip


def finalize_record_sip():
    """
    Finalizes the SIP by generating the MARC and storing it in the SIP.
    """
    def _finalize_sip(obj, dummy_eng):
        d = Deposition(obj)
        sip = d.get_latest_sip(include_sealed=False)

        jsonreader = JsonReader()
        for k, v in sip.metadata.items():
            jsonreader[k] = v

        sip.package = jsonreader.legacy_export_as_marc()

        current_app.logger.info(jsonreader['__error_messages'])
        current_app.logger.info(sip.package)

        d.update()
    return _finalize_sip


def upload_record_sip():
    """
    Generates the record from marc.
    The function requires the marc to be generated,
    so the function export_marc_from_json must have been called successfully
    before
    """
    def create(obj, dummy_eng):
        current_app.logger.info("Upload sip")
        d = Deposition(obj)

        sip = d.get_latest_sip(include_sealed=False)
        sip.seal()

        tmp_file_fd, tmp_file_path = mkstemp(
            prefix="webdeposit-%s-%s" % (d.id, sip.uuid),
            suffix='.xml',
            dir=CFG_TMPSHAREDDIR,
        )

        os.write(tmp_file_fd, sip.package)
        os.close(tmp_file_fd)

        # Trick to have access to task_sequence_id in subsequent tasks.
        d.workflow_object.task_sequence_id = bibtask_allocate_sequenceid()

        task_low_level_submission(
            'bibupload', 'webdeposit',
            '-r' if 'recid' in sip.metadata else '-i', tmp_file_path, '-P5',
            '-I', str(d.workflow_object.task_sequence_id)
        )

        d.update()
    return create
