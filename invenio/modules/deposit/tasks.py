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

from __future__ import print_function

import os
import dictdiffer

from tempfile import mkstemp
from functools import partial
from flask import current_app, abort, request
from flask.ext.login import current_user

from invenio.modules.records.api import Record
from invenio.modules.records.api import get_record
from invenio.legacy.dbquery import run_sql
from invenio.modules.deposit.models import Deposition, Agent, \
    DepositionDraftCacheManager
from invenio.ext.logging import register_exception
from invenio.ext.restful import error_codes
from invenio.modules.formatter import format_record
from .helpers import record_to_draft, make_record, \
    deposition_record
from invenio.legacy.bibdocfile.api import BibRecDocs
from invenio.legacy.bibsched.bibtask import task_low_level_submission, \
    bibtask_allocate_sequenceid

try:
    from invenio.pidstore_model import PersistentIdentifier
    HAS_PIDSUPPORT = True
except ImportError:
    HAS_PIDSUPPORT = False


def is_api_request(obj, eng):
    """ Check if request is an API request """
    return getattr(request, 'is_api_request', False)


def has_submission(obj, eng):
    """
    """
    d = Deposition(obj)
    return d.has_sip()


def authorize_user(action, **params):
    """
    Check if current user is authorized to perform the action.
    """
    def _authorize_user(obj, dummy_eng):
        from invenio.modules.access.engine import acc_authorize_action

        auth, message = acc_authorize_action(
            current_user.get_id(),
            action,
            **dict((k, v() if callable(v) else v)
                   for (k, v) in params.items()))
        if auth != 0:
            current_app.logger.info(message)
            abort(401)

    return _authorize_user


def prefill_draft(draft_id='_default', clear=True):
    """
    Fill draft values with values from pre-filled cache
    """
    def _prefill_draft(obj, eng):
        if not getattr(request, 'is_api_request', False):
            draft_cache = DepositionDraftCacheManager.get()
            if draft_cache.has_data():
                d = Deposition(obj)
                draft_cache.fill_draft(d, draft_id, clear=clear)
                d.update()
    return _prefill_draft


def render_form(draft_id='_default'):
    """
    Renders a form if the draft associated with it has not yet been completed.

    :param draft_id: The name of the draft to create. Must be specified if you
        put more than two ``render_form'''s in your deposition workflow.
    """
    def _render_form(obj, eng):
        d = Deposition(obj)
        draft = d.get_or_create_draft(draft_id)

        if getattr(request, 'is_api_request', False):
            form = draft.get_form(validate_draft=True)
            if form.errors:
                error_messages = []
                for field, msgs in form.errors:
                    for m in msgs:
                        error_messages.append(
                            field=field,
                            message=m,
                            code=error_codes['validation_error'],
                        )

                d.set_render_context(dict(
                    response=dict(
                        message="Bad request",
                        status=400,
                        errors=error_messages,
                    ),
                    status=400,
                ))
                eng.halt("API: Draft did not validate")
        else:
            if draft.is_completed():
                eng.jumpCallForward(1)
            else:
                form = draft.get_form(validate_draft=draft.validate)
                form.validate = True

                d.set_render_context(dict(
                    template_name_or_list=form.get_template(),
                    deposition=d,
                    deposition_type=(
                        None if d.type.is_default() else
                        d.type.get_identifier()
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


def load_record(draft_id='_default', producer='json_for_form',
                pre_process=None, post_process=None):
    """
    Load a record and map to draft data.
    """
    def _load_record(obj, eng):
        d = Deposition(obj)

        # Get record
        sip = d.get_latest_sip(sealed=True)
        record = get_record(sip.metadata.get('recid'), reset_cache=True)

        sip_version_id = sip.metadata.get('version_id')
        record_version_id = record.get('version_id')

        # Check of record in latest SIP has been uploaded (record version must
        # be newer than SIP record version.
        if record_version_id is None or (sip_version_id and
                                         sip_version_id >= record_version_id):
            if getattr(request, 'is_api_request', False):
                d.set_render_context(dict(
                    response=dict(
                        message="Conflict",
                        status=409,
                        errors="Upload not yet fully integrated. Please wait"
                               " a few moments.",
                    ),
                    status=409,
                ))
            else:
                from flask import flash
                flash(
                    "Editing is only possible after your upload have been"
                    " fully integrated. Please wait a few moments, then try"
                    " to reload the page.",
                    category='warning'
                )
                d.set_render_context(dict(
                    template_name_or_list="webdeposit_completed.html",
                    deposition=d,
                    deposition_type=(
                        None if d.type.is_default() else
                        d.type.get_identifier()
                    ),
                    uuid=d.id,
                    sip=sip,
                    my_depositions=Deposition.get_depositions(
                        current_user, type=d.type
                    ),
                    format_record=format_record,
                ))
            d.update()
            eng.halt("Wait for record to be uploaded")

        # Check if record is already loaded, if so, skip.
        if d.drafts:
            eng.jumpCallForward(1)

        # Load draft
        draft = d.get_or_create_draft(draft_id)

        # Fill draft with values from recjson
        record_to_draft(
            record, draft=draft, post_process=post_process, producer=producer
        )

        # Store initial deposition_recjson
        #draft.values['_initial'] = drafts_to_record([draft])

        d.update()

        # Stop API request
        if getattr(request, 'is_api_request', False):
            d.set_render_context(dict(
                response=d.marshal(),
                status=201,
            ))
            eng.halt("API request")
    return _load_record


def merge_record(draft_id='_default', pre_process_load=None,
                 post_process_load=None, process_export=None):
    """
    Merge recjson with a record

    This task will load the current record, diff the changes from the
    deposition against it, and apply the patch.
    """
    def _merge_record(obj, eng):
        d = Deposition(obj)
        sip = d.get_latest_sip(sealed=False)

        current_record = get_record(
            sip.metadata.get('recid'), reset_cache=True
        )

        # Diff current record  with changes from editing deposition (note,
        # only fields which actually concerns the deposition is diff'ed).
        form_class = d.get_draft(draft_id).form_class

        initial_record = deposition_record(
            current_record,
            [form_class],
            pre_process_load=pre_process_load,
            post_process_load=post_process_load,
            process_export=partial(process_export, d),
        )
        changed_record = make_record(sip.metadata)

        # Generate patch
        patch = dictdiffer.diff(
            initial_record.rec_json,
            changed_record.rec_json,
        )

        # Initial patch of current record.
        for k in initial_record:
            if k not in current_record.rec_json:
                current_record.rec_json[k] = initial_record[k]

        # Fix Pyton 2.6 compatibility issue in CoolList deepcopy'ing
        #from invenio.bibfield_utils import CoolList
        #map_fun = lambda x: list(x) if isinstance(x, CoolList) else x
        #metadata = dict([
        #    (k, map_fun(v)) for k, v in current_record.rec_json.items()
        #])

        # Apply patch
        sip.metadata = dictdiffer.patch(
            patch,
            current_record.rec_json
        )

        # Ensure we are based on latest version_id to prevent being rejected in
        # the bibupload queue.
        sip.metadata['version_id'] = current_record['version_id']

        d.update()
    return _merge_record


def create_recid():
    """
    Create a new record id.
    """
    def _create_recid(obj, dummy_eng):
        d = Deposition(obj)
        sip = d.get_latest_sip(sealed=False)
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
        recjson = d.get_latest_sip(sealed=False).metadata

        if 'recid' not in recjson:
            raise Exception("'recid' not found in sip metadata.")

        pid_text = None
        pid = recjson.get(pid_field, None)
        if not pid:
            # No pid found in recjson, so create new pid with user supplied
            # function.
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


def process_bibdocfile(process=None):
    """
    Process bibdocfiles with custom processor
    """
    def _bibdocfile_update(obj, eng):
        if process:
            d = Deposition(obj)
            sip = d.get_latest_sip(sealed=False)
            recid = sip.metadata.get('recid')
            if recid:
                brd = BibRecDocs(int(recid))
                process(d, brd)
                d.update()
    return _bibdocfile_update


def prepare_sip():
    """
    Prepare a submission information package
    """
    def _prepare_sip(obj, dummy_eng):
        d = Deposition(obj)

        sip = d.get_latest_sip(sealed=False)
        if sip is None:
            sip = d.create_sip()

        sip.metadata['fft'] = sip.metadata['files']
        del sip.metadata['files']

        sip.agents = [Agent(role='creator', from_request_context=True)]
        d.update()
    return _prepare_sip


def process_sip_metadata(processor):
    """
    Process metadata in submission information package using a custom
    processor.
    """
    def _prepare_sip(obj, dummy_eng):
        d = Deposition(obj)
        metadata = d.get_latest_sip(sealed=False).metadata
        processor(d, metadata)
        d.update()
    return _prepare_sip


def finalize_record_sip():
    """
    Finalizes the SIP by generating the MARC and storing it in the SIP.
    """
    def _finalize_sip(obj, dummy_eng):
        d = Deposition(obj)
        sip = d.get_latest_sip(sealed=False)

        json = Record()
        for k, v in sip.metadata.items():
            json.set(k, v, extend=True)

        sip.package = json.legacy_export_as_marc()

        current_app.logger.info(json['__meta_metadata__']['__errors__'])
        current_app.logger.info(json['__meta_metadata__']['__continuable_errors__'])
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
        #FIXME change share tmp directory
        from invenio.config import CFG_TMPSHAREDDIR
        d = Deposition(obj)

        sip = d.get_latest_sip(sealed=False)
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

        task_id = task_low_level_submission(
            'bibupload', 'webdeposit',
            '-r' if 'recid' in sip.metadata else '-i', tmp_file_path, '-P5',
            '-I', str(d.workflow_object.task_sequence_id)
        )

        sip.task_ids.append(task_id)

        d.update()
    return create
