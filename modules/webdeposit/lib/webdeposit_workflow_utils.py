# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import os
import time
from datetime import datetime
from invenio.sqlalchemyutils import db
from invenio.bibworkflow_model import Workflow
from invenio.bibfield_jsonreader import JsonReader
from tempfile import mkstemp
from invenio.bibtask import task_low_level_submission
from invenio.config import CFG_TMPSHAREDDIR, CFG_PREFIX
from invenio.dbquery import run_sql

"""
    Functions to implement workflows

    The workflow functions must have the following structure:

    def function_name(arg1, arg2):
            def fun_name2(obj, eng):
                # do stuff
            return fun_name2
"""


def authorize_user(user_id=None):
    def user_auth(obj, dummy_eng):
        if user_id is not None:
            obj.data['user_id'] = user_id
        else:
            from invenio.webuser_flask import current_user
            obj.data['user_id'] = current_user.get_id()
    return user_auth


def populate_form_data(form_data):
    """ Pass a json to initialize the values of the forms.
        If two forms use the same name for a field,
        the value is passed to the one that is rendered first."""
    def populate(obj, eng):
        obj.data['form_values'] = form_data
    return populate


def render_form(form):
    def render(obj, eng):
        from invenio.webdeposit_utils import get_last_step, CFG_DRAFT_STATUS, \
            add_draft,  get_preingested_form_data, preingest_form_data

        uuid = eng.uuid
        user_id = obj.data['user_id']
        #TODO: create out of the getCurrTaskId() which is a list
        # an incremental key that represents also steps in complex workflows.
        step = get_last_step(eng.getCurrTaskId())
        form_type = form.__name__

        if obj.data.has_key('form_values') and obj.data['form_values'] is not None:
            form_values = obj.data['form_values']
        else:
            form_values = {}
        # Prefill the form from cache
        cached_form = get_preingested_form_data(user_id, cached_data=True)

        # Check for preingested data from webdeposit API
        preingested_form_data = get_preingested_form_data(user_id, uuid)
        if preingested_form_data != {} and preingested_form_data is not None:
            form_data = preingested_form_data
        elif cached_form is not None:
            form_data = cached_form
            # Clear cache
            preingest_form_data(user_id, None, cached_data=True)
        else:
            form_data = {}

        # Filter the form_data to match the current form
        for field in form():
            if field.name in form_data:
                form_values[field.name] = form_data[field.name]

        draft = dict(form_type=form_type,
                     form_values=form_values,
                     status=CFG_DRAFT_STATUS['unfinished'],
                     timestamp=str(datetime.now()),
                     step=step)

        Workflow.set_extra_data(user_id=user_id, uuid=uuid,
                                setter=add_draft(draft))
    render.__form_type__ = form.__name__
    return render


def wait_for_submission():
    def wait(obj, eng):
        user_id = obj.data['user_id']
        uuid = eng.uuid
        from invenio.webdeposit_utils import CFG_DRAFT_STATUS, get_form_status
        status = get_form_status(user_id, uuid)
        if status == CFG_DRAFT_STATUS['unfinished']:
            # If form is unfinished stop the workflow
            eng.halt('Waiting for form submission.')
        else:
            # If form is completed, continue with next step
            eng.jumpCallForward(1)
    return wait


def export_marc_from_json():
    """ Exports marc from json using BibField """
    def export(obj, eng):
        user_id = obj.data['user_id']
        uuid = eng.uuid
        steps_num = obj.data['steps_num']

        from invenio.webdeposit_utils import get_form
        json_reader = JsonReader()

        try:
            pop_obj = Workflow.get_extra_data(user_id=user_id, uuid=uuid,
                                              key='pop_obj')
        except KeyError:
            pop_obj = None

        form_data = {}
        if 'form_values' in obj.data or pop_obj is not None:

            # copy the form values to be able to
            # delete the fields in the workflow object during iteration
            form_data = pop_obj or obj.data['form_values']

        # Populate the form with data
        for step in range(steps_num):
            form = get_form(user_id, uuid, step)

            # Insert the fields' values in bibfield's rec_json dictionary
            if form is not None:  # some steps don't have any form ...
                # Populate preingested data
                for field in form:
                    if field.name in form_data:
                        field.data = form_data.pop(field.name)
                json_reader = form.cook_json(json_reader)

        deposition_type = \
            db.session.query(Workflow.name).\
            filter(Workflow.user_id == user_id,
                   Workflow.uuid == uuid).\
            one()[0]

        # Get the collection from configuration
        # FIXME: Collection should be fully configurable.
        json_reader['collection.primary'] = deposition_type

        if 'recid' not in json_reader or 'record ID' not in json_reader:
            # Record is new, reserve record id
            recid = run_sql("INSERT INTO bibrec (creation_date, modification_date) VALUES (NOW(), NOW())")
            json_reader['recid'] = recid
            obj.data['recid'] = recid
        else:
            obj.data['recid'] = json_reader['recid']
            obj.data['title'] = json_reader['title.title']

        workflow = Workflow.query.filter(Workflow.uuid == uuid).one()
        workflow.extra_data['recid'] = obj.data['recid']
        Workflow.query.\
            filter(Workflow.uuid == uuid).\
            update({'extra_data': workflow.extra_data})

        marc = json_reader.legacy_export_as_marc()
        obj.data['marc'] = marc
    return export


def create_record_from_marc():
    """ Generates the record from marc.
    The function requires the marc to be generated,
    so the function export_marc_from_json must have been called successfully
    before
    """
    def create(obj, dummy_eng):
        marc = obj.data['marc']
        tmp_file_fd, tmp_file_name = mkstemp(suffix='.marcxml',
                                             prefix="webdeposit_%s" %
                                             time.strftime("%Y-%m-%d_%H:%M:%S"),
                                             dir=CFG_TMPSHAREDDIR)
        os.write(tmp_file_fd, marc)
        os.close(tmp_file_fd)
        os.chmod(tmp_file_name, 0644)

        obj.data['task_id'] = task_low_level_submission('bibupload',
                                                        'webdeposit', '-r',
                                                        tmp_file_name)
    return create


def bibindex():
    """ Runs BibIndex """
    def bibindex_task(obj, eng):
        cmd = "%s/bin/bibindex -u admin" % CFG_PREFIX
        if os.system(cmd):
            eng.log.error("BibIndex task failed.")

    return bibindex_task


def webcoll():
    """ Runs WebColl """
    def webcoll_task(obj, eng):
        cmd = "%s/bin/webcoll -u admin" % CFG_PREFIX
        if os.system(cmd):
            eng.log.error("WebColl task failed.")

    return webcoll_task
