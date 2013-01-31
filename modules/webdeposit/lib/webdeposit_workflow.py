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
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from flask import render_template
from invenio.webdeposit_model import WebDepositWorkflow
from invenio.webdeposit_workflow_utils import create_deposition_document
from invenio.sqlalchemyutils import db
from uuid import uuid1 as new_uuid
import json

CFG_WEBDEPOSIT_WORKFLOW_STATUS = {
    'running': 0,
    'finished': 1,
    'error': -1
    }


class DepositionWorkflow(object):
    """ class for running sequential workflows

    Workflow always obtains a uuid,
    either externally or creates a new one.
    (That's because it must have allocated space for the object)

    The workflow functions must have the following structure:

    def function_name(arg1, arg2):
        def fun_name2(obj, eng):
            # do stuff
        return fun_name2
    """

    def __init__(self, obj=None, engine=None, workflow=None,
                 uuid=None, deposition_type=None):
        if obj is None:
            self.obj = dict()
        else:
            self.obj = obj

        if deposition_type is not None:
            self.set_deposition_type(deposition_type)

        self.obj['break'] = False
        self.eng = engine
        self.current_step = 0
        self.obj['step'] = self.current_step
        self.set_workflow(workflow)
        self.set_uuid(uuid)

    def set_workflow(self, workflow):
        """ Sets the workflow
        """
        self.workflow = workflow
        self.steps_num = len(workflow)

    def set_uuid(self, uuid=None):
        """ Sets the uuid or obtains a new one
            Allocates a row in the database
        """
        if uuid is None:
            uuid = new_uuid()
            self.obj['uuid'] = uuid
            # Then the workflow was not created before
            dep_create = create_deposition_document(self.obj['deposition_type'])
            dep_create(self.obj, self.eng)
        else:
            self.obj['uuid'] = uuid
            # synchronize the workflow object
            self.update_workflow_object()

    def get_uuid(self):
        return self.obj['uuid']

    def set_deposition_type(self, deposition_type=None):
        if deposition_type is not None:
            self.obj['deposition_type'] = deposition_type

    def get_status(self):
        if self.current_step >= self.steps_num:
            return CFG_WEBDEPOSIT_WORKFLOW_STATUS['finished']
        return CFG_WEBDEPOSIT_WORKFLOW_STATUS['running']

    def get_output(self):
        user_id = self.obj['user_id']
        uuid = self.obj['uuid']

        from invenio.webdeposit_utils import get_form, \
                                             draft_field_get_all
        form = get_form(user_id, uuid)

        deposition_type = self.obj['deposition_type']
        drafts = draft_field_get_all(user_id, deposition_type)

        return dict(workflow=self,
                    deposition_type=deposition_type,
                    form=form,
                    drafts=drafts,
                    uuid=uuid)

    def run(self):
        while True:
            self.run_next_step()
            if self.obj['break']:
                self.obj['break'] = False
                break

    def run_next_step(self):
        if self.current_step >= self.steps_num:
            self.obj['break'] = True
            self.update_db()
            return
        function = self.workflow[self.current_step]
        function(self.obj, self)
        self.current_step += 1
        self.obj['step'] = self.current_step
        self.update_db()

    def jump_forward(self, synchronize=False):
        self.current_step += 1
        if synchronize:
            self.update_db()

    def jump_backwards(self, synchronize=False):
        if self.current_step > 1:
            self.current_step -= 1
        else:
            self.current_step = 1
        if synchronize:
            self.update_db()

    def set_current_step(self, step, synchronize=False):
        self.current_step = step
        if synchronize:
            self.update_db()

    def get_current_step(self):
        return self.current_step

    def get_workflow_from_db(self):
        uuid = self.get_uuid()
        wf = db.session.query(WebDepositWorkflow).filter(\
                                 WebDepositWorkflow.uuid == uuid).one()
        return wf

    def update_db(self):
        uuid = self.get_uuid()
        obj = dict(**self.obj)
        # These keys have separate columns
        obj.pop('uuid')
        obj.pop('step')
        obj.pop('deposition_type')
        WebDepositWorkflow.query.filter(WebDepositWorkflow.uuid == uuid).\
            update({
                'status': self.get_status(),
                'current_step': self.current_step,
                'obj_json': obj
                })
        db.session.commit()

    def update_workflow_object(self):
        wf = self.get_workflow_from_db()
        obj = dict(**wf.obj_json)
        obj['deposition_type'] = wf.deposition_type
        obj['step'] = wf.current_step
        self.current_step = wf.current_step
        self.obj.update(obj)

    def cook_json(self):
        user_id = self.obj['user_id']
        uuid = self.get_uuid()

        from invenio.webdeposit_utils import get_form

        json_reader = {}
        for step in range(self.steps_num):
            try:
                form = get_form(user_id, uuid, step)
                for field in form:
                    json_reader = field.cook_json(json_reader)
            except:
                # some steps don't have any form ...
                pass

        return json_reader
