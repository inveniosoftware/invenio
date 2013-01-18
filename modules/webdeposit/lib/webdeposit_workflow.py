from sqlalchemy.orm.exc import NoResultFound
from flask import render_template
from invenio.webdeposit_model import WebDepositWorkflow
from invenio.webdeposit_workflow_utils import create_deposition_document
from invenio.sqlalchemyutils import db
import uuid as new_uuid
import json

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
            uuid = new_uuid.uuid1()
            self.obj['uuid'] = uuid
            # Then the workflow was not created before
            dep_create = create_deposition_document(self.obj['dep_type'])
            dep_create(self.obj, self.eng)
        else:
            self.obj['uuid'] = uuid
            # synchronize the workflow object
            self.update_workflow_object()

    def get_uuid(self):
        return self.obj['uuid']

    def set_deposition_type(self, deposition_type=None):
        if deposition_type is not None:
            self.obj['dep_type'] = deposition_type

    def get_status(self):
        return 0

    def get_output(self):
        user_id = self.obj['user_id']
        uuid = self.obj['uuid']

        from invenio.webdeposit_utils import get_form, \
                                             draft_field_get_all, \
                                             pretty_date
        form = get_form(user_id, uuid)

        dep_type = self.obj['dep_type']
        drafts = draft_field_get_all(user_id, dep_type, "title")
        drafts = sorted(drafts,
                        key=lambda draft: draft['timestamp'],
                        reverse=True)
        for draft in drafts:
            draft['timestamp'] = pretty_date(draft['timestamp'])

        return render_template('webdeposit.html', \
                               dep_type=dep_type,
                               form=form, \
                               drafts=drafts, \
                               draft_id=uuid)

        from flask.helpers import make_response
        return make_response("hello world!" + str(self.eng) + self.get_uuid()) #self.eng

    def run(self):
        while True:
            self.run_next_step()
            if self.obj['break']:
                self.obj['break'] = False
                break

    def run_next_step(self):
        self.update_workflow_object()
        if self.current_step >= self.steps_num:
            self.obj['break'] = True
            return
        function = self.workflow[self.current_step]
        function(self.obj, self)
        self.current_step += 1
        self.obj['step'] = self.current_step
        self.update_db()

    def jump_forward(self):
        self.current_step += 1
        self.update_db_step()

    def jump_backwards(self):
        if self.current_step >= 2:
            self.current_step -= 1
        else:
            self.current_step = 1
        self.update_db_step()

    def set_current_step(self, step):
        self.current_step = step
        self.update_db_step()

    def get_current_step(self):
        return self.current_step

    def update_db(self):
        uuid = self.obj['uuid']
        wf = db.session.query(WebDepositWorkflow).filter(\
                                 WebDepositWorkflow.uuid == uuid).one()
        wf.current_step = self.current_step
        obj = dict(**self.obj)
        # These keys have separate columns
        obj.pop('uuid')
        obj.pop('step')
        obj.pop('dep_type')
        obj_to_json = json.dumps(obj)
        wf.obj_json = obj_to_json
        db.session.commit()

    def update_db_step(self):
        uuid = self.obj['uuid']
        wf = db.session.query(WebDepositWorkflow).filter(\
                                 WebDepositWorkflow.uuid == uuid).one()
        wf.current_step = self.current_step
        db.session.commit()

    def update_db_object(self):
        uuid = self.obj['uuid']
        wf = db.session.query(WebDepositWorkflow).filter(\
                                 WebDepositWorkflow.uuid == uuid).one()
        obj = dict(self.obj)
        # These keys have separate columns
        obj.pop('uuid')
        obj.pop('step')
        obj.pop('dep_type')
        obj_to_json = json.dumps(obj)
        wf.obj_json = obj_to_json
        db.session.commit()

    def update_workflow_object(self):
        uuid = self.obj['uuid']
        wf = db.session.query(WebDepositWorkflow).filter(\
                             WebDepositWorkflow.uuid == uuid).one()

        obj = json.loads(wf.obj_json)
        obj['uuid'] = wf.uuid
        obj['dep_type'] = wf.dep_type
        obj['step'] = wf.current_step
        self.current_step = wf.current_step
        self.obj = obj
