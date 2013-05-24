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
from sqlalchemy import func
from invenio.sqlalchemyutils import db
from invenio.webdeposit_config_utils import WebDepositConfiguration
from invenio.webdeposit_model import WebDepositDraft
from invenio.bibworkflow_model import Workflow
from invenio.bibfield_jsonreader import JsonReader
from tempfile import mkstemp
from invenio.bibtask import task_low_level_submission
from invenio.config import CFG_TMPSHAREDDIR

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


def render_form(form):
    def render(obj, eng):
        uuid = eng.uuid
        # TODO: get the current step from the object
        step = max(obj.db_obj.task_counter)  # data['step']
        form_type = form.__name__
        from invenio.webdeposit_utils import CFG_DRAFT_STATUS
        webdeposit_draft = WebDepositDraft(uuid=uuid,
                                           form_type=form_type,
                                           form_values={},
                                           step=step,
                                           status=CFG_DRAFT_STATUS['unfinished'],
                                           timestamp=func.current_timestamp())
        db.session.add(webdeposit_draft)
        db.session.commit()
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
    def export(obj, eng):
        user_id = obj.data['user_id']
        uuid = eng.uuid
        steps_num = obj.data['steps_num']

        from invenio.webdeposit_utils import get_form
        json_reader = JsonReader()
        for step in range(steps_num):
            form = get_form(user_id, uuid, step)
            # Insert the fields' values in bibfield's rec_json dictionary
            if form is not None:  # some steps don't have any form ...
                json_reader = form.cook_json(json_reader)

        deposition_type = \
            db.session.query(Workflow.name).\
            filter(Workflow.user_id == user_id,
                   Workflow.uuid == uuid).\
            one()[0]

        # Get the collection from configuration
        deposition_conf = WebDepositConfiguration(deposition_type=deposition_type)
        # or if it's not there, name the collection after the deposition type
        json_reader['collection.primary'] = \
            deposition_conf.get_collection() or deposition_type

        if 'recid' in json_reader or 'record ID' in json_reader:
            obj.data['update_record'] = True
        else:
            obj.data['update_record'] = False
        marc = json_reader.legacy_export_as_marc()
        obj.data['marc'] = marc
    return export


def create_record_from_marc():
    def create(obj, dummy_eng):
        marc = obj.data['marc']
        tmp_file_fd, tmp_file_name = mkstemp(suffix='.marcxml',
                                             prefix="webdeposit_%s" %
                                             time.strftime("%Y-%m-%d_%H:%M:%S"),
                                             dir=CFG_TMPSHAREDDIR)
        os.write(tmp_file_fd, marc)
        os.close(tmp_file_fd)
        os.chmod(tmp_file_name, 0644)

        if obj.data['update_record']:
            obj.data['task_id'] = task_low_level_submission('bibupload',
                                                            'webdeposit', '-r',
                                                            tmp_file_name)
        else:
            obj.data['task_id'] = task_low_level_submission('bibupload',
                                                            'webdeposit', '-i',
                                                            tmp_file_name)
    return create
