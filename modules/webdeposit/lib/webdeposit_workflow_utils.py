from sqlalchemy import func, desc
from wtforms import FormField
#from werkzeug.contrib.cache import RedisCache
from invenio.sqlalchemyutils import db
from webdeposit_model import WebDepositDraft, \
                             WebDepositWorkflow
from invenio.webdeposit_workflow import WebDepositWorkflow

import datetime
import json
import uuid as new_uuid


def create_deposition_document(dep_type):
    def create_dep_doc(obj, eng):
        obj['dep_type'] = dep_type
        uuid = new_uuid.uuid1()
        webdeposit_workflow = WebDepositWorkflow(uuid=uuid, \
                                                 dep_type=dep_type, \
                                                 current_step=0)
        db.session.add(webdeposit_workflow)
        db.session.commit()
        obj['uuid'] = uuid
    return create_dep_doc

def authorize_user(user_id):
    def user_auth(obj, eng):
        obj['user_id'] = user_id
    return user_auth

def render_form(form):
    def render(obj, eng):
        uuid = obj['uuid']
        user_id = obj['user_id']
        dep_type = obj['dep_type']
        step = obj['step']
        status = 0
        form_type = form.__class__.__name__
        webdeposit_draft = WebDepositDraft(uuid=uuid, \
                                  user_id=user_id, \
                                  dep_type=dep_type, \
                                  form_type=form_type, \
                                  form_values='{}', \
                                  timestamp=func.current_timestamp(), \
                                  status=status)
        db.session.add(webdeposit_draft)
        db.session.commit()
