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

from invenio.webdeposit_model import WebDepositWorkflow
from invenio.webdeposit_workflow_utils import create_deposition_document
from invenio.bibworkflow_engine import BibWorkflowEngine,\
                                       CFG_WORKFLOW_STATUS
from invenio.bibworkflow_object import BibWorkflowObject
from invenio.bibworkflow_model import Workflow, WfeObject
from invenio.bibworkflow_client import run_workflow, restart_workflow
from invenio.sqlalchemyutils import db
from uuid import uuid1 as new_uuid


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

    def __init__(self, engine=None, workflow=None,
                 uuid=None, deposition_type=None, user_id=None):

        self.obj = {}
        self.set_user_id(user_id)
        self.set_uuid(uuid)

        if deposition_type is not None:
            self.set_deposition_type(deposition_type)

        self.current_step = 0
        self.set_engine(engine)
        self.set_object()
        self.set_workflow(workflow)

    def set_uuid(self, uuid=None):
        """ Sets the uuid or obtains a new one
            Allocates a row in the database
        """
        if uuid is None:
            uuid = new_uuid()
            self.uuid = uuid
            # Then the workflow was not created before
            #dep_create = create_deposition_document(self.get_deposition_type(),
            #                                        self.get_user_id())
            #dep_create(self.obj, self.eng)
        else:
            self.uuid = uuid
            # synchronize the workflow object
            #self.update_workflow_object()

    def get_uuid(self):
        return self.uuid

    def set_engine(self, engine=None):
        if engine is None:
            engine = BibWorkflowEngine(name=self.get_deposition_type(), uuid=self.get_uuid(), \
                                       user_id=self.get_user_id(), module_name="webdeposit")
        self.eng = engine
        self.eng.save()

    def set_workflow(self, workflow):
        """ Sets the workflow """

        self.eng.setWorkflow(workflow)
        self.workflow = workflow
        self.steps_num = len(workflow)

    def set_object(self):
        self.bib_obj = BibWorkflowObject(data=self.obj, workflow_id=self.get_uuid(), user_id=self.get_user_id())

    def get_object(self):
        return self.bib_obj

    def set_deposition_type(self, deposition_type=None):
        if deposition_type is not None:
            self.obj['deposition_type'] = deposition_type

    def get_deposition_type(self):
        return self.obj['deposition_type']

    def set_user_id(self, user_id=None):
        if user_id is not None:
            self.user_id = user_id
        else:
            from invenio.webuser_flask import current_user
            self.user_id = current_user.get_id()

        self.obj['user_id'] = self.user_id

    def get_user_id(self):
        return self.user_id

    def get_status(self):
        return 0
        if self.current_step >= self.steps_num:
            return CFG_WORKFLOW_STATUS['finished']
        return CFG_WORKFLOW_STATUS['running']

    def get_output(self):
        user_id = self.user_id
        uuid = self.get_uuid()

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
        starting_point = self.bib_obj.db_obj.task_counter
        restart_workflow(self.eng, [self.bib_obj], starting_point)
        #run_workflow(self.eng, [self.bib_obj])
        #restart_workflow
        #run(self.get_deposition_type(), [self.bib_obj])
        #run_by_wid(self.get_uuid(), [self.obj])

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
        return Workflow.query.filter(Workflow.uuid == self.get_uuid()).first()

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
        obj = WfeObject.query.filter(WfeObject.workflow_id == self.get_uuid()).first()

        bib_obj = BibWorkflowObject(id=obj.id, workflow_id=self.get_uuid())
        self.set_object(bib_obj)

        wf = self.get_workflow_from_db()
        self.set_user_id(wf.user_id)
        self.set_deposition_type(wf.name)
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
