from sqlalchemy import func, desc
from wtforms import FormField
from invenio.sqlalchemyutils import db
from invenio.webdeposit_model import WebDepositDraft, \
                                     WebDepositWorkflow

import datetime
import json
import uuid as new_uuid


def create_deposition_document(deposition_type):
    def create_dep_doc(obj, eng):
        obj['dep_type'] = deposition_type
        uuid = obj['uuid']
        temp_obj = dict(obj)
        temp_obj.pop('uuid')
        temp_obj.pop('step')
        temp_obj.pop('dep_type')
        obj_json = json.dumps(temp_obj)
        webdeposit_workflow = WebDepositWorkflow(uuid=uuid,
                                                 dep_type=deposition_type,
                                                 obj_json=obj_json,
                                                 current_step=0,
                                                 status=0)
        db.session.add(webdeposit_workflow)
        db.session.commit()
    return create_dep_doc

def authorize_user(user_id=None):
    def user_auth(obj, eng):
        if user_id is not None:
            obj['user_id'] = user_id
        else:
            from invenio.webuser_flask import current_user
            obj['user_id'] = current_user.get_id()
    return user_auth

def render_form(form):
    def render(obj, eng):
        uuid = obj['uuid']
        if 'user_id' in obj:
            user_id = obj['user_id']
        else:
            from invenio.webuser_flask import current_user
            user_id = current_user.get_id()
        dep_type = obj['dep_type']
        step = obj['step']
        form_type = form.__name__
        webdeposit_draft = WebDepositDraft(uuid=uuid, \
                                  user_id=user_id, \
                                  dep_type=dep_type, \
                                  form_type=form_type, \
                                  form_values='{}', \
                                  step=step,
                                  timestamp=func.current_timestamp())
        db.session.add(webdeposit_draft)
        db.session.commit()
    return render

def wait_for_submission():
    def wait(obj, eng):
        obj['break'] = True
        eng.current_step -= 1
    return wait
