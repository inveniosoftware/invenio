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

from datetime import datetime
from sqlalchemy import desc
from wtforms import FormField
from sqlalchemy.orm.exc import NoResultFound
from invenio.sqlalchemyutils import db
from invenio.webdeposit_model import WebDepositDraft
from invenio.bibworkflow_model import Workflow
from invenio.bibworkflow_engine import CFG_WORKFLOW_STATUS
from invenio.webdeposit_load_forms import forms
from invenio.webuser_flask import current_user
from invenio.webdeposit_load_deposition_types import deposition_metadata
from invenio.webdeposit_workflow import DepositionWorkflow

""" Deposition Type Functions """


def get_latest_or_new_workflow(deposition_type):
    """ Creates new workflow or returns a new one """

    user_id = current_user.get_id()
    wf = deposition_metadata[deposition_type]["workflow"]

    # get latest draft in order to get workflow's uuid
    webdeposit_draft = db.session.query(WebDepositDraft).\
        join(WebDepositDraft.workflow).\
        filter(
            Workflow.user_id == user_id,
            Workflow.name == deposition_type,
            Workflow.module_name == 'webdeposit',
            Workflow.status == CFG_WORKFLOW_STATUS['running']).\
        order_by(db.desc(WebDepositDraft.timestamp)).\
        first()
    if webdeposit_draft is None:
        # We didn't find other workflows
        # Let's create a new one
        return DepositionWorkflow(deposition_type=deposition_type,
                                  workflow=wf)

    # Create a new workflow
    # based on the latest draft's uuid
    uuid = webdeposit_draft.uuid
    return DepositionWorkflow(deposition_type=deposition_type,
                              workflow=wf, uuid=uuid)


def get_workflow(deposition_type, uuid):
    """ Returns a workflow instance with uuid=uuid or None """
    try:
        wf = deposition_metadata[deposition_type]["workflow"]
    except KeyError:
        # deposition type not found
        return None
    return DepositionWorkflow(uuid=uuid,
                              deposition_type=deposition_type,
                              workflow=wf)


def create_workflow(user_id, deposition_type):
    """ Creates a new workflow and returns it """
    try:
        wf = deposition_metadata[deposition_type]["workflow"]
    except KeyError:
        # deposition type not found
        return None

    return DepositionWorkflow(deposition_type=deposition_type, workflow=wf)


def delete_workflow(user_id, deposition_type, uuid):
    """ Deletes all workflow related data
        (workflow and drafts)
    """

    db.session.query(Workflow).filter_by(\
                                      uuid=uuid,
                                      user_id=user_id).\
                                      delete()

    db.session.query(WebDepositDraft).filter_by(\
                                      uuid=uuid).\
                                      delete()
    db.session.commit()


def create_deposition_type(user_id, deposition_type):
    """Creates a deposition object (initiates workflow)
    and returns the uuid and the form to be rendered
    TODO: check if dep type exists
    (deprecated, use create_workflow instead)
    """
    try:
        wf = deposition_metadata[deposition_type]["workflow"]
    except KeyError:
        # deposition_type not found
        return None, None

    webdep_workflow = DepositionWorkflow(workflow=wf,
                                         deposition_type=deposition_type,\
                                         user_id=user_id)
    webdep_workflow.run()
    uuid = webdep_workflow.get_uuid()
    return get_current_form(user_id, uuid=uuid)


def get_current_form(user_id, deposition_type=None, uuid=None):
    """Returns the latest draft(wtform object) of the deposition_type
    or the form with the specific uuid.
    if it doesn't exist, creates a new one
    """

    if user_id is None:
        return None

    try:
        if uuid is not None:
            webdeposit_draft_query = db.session.query(WebDepositDraft).\
                                        join(Workflow).\
                                        filter(
                                        Workflow.user_id == user_id,
                                        WebDepositDraft.uuid == uuid)
            # get the draft with the max step, the latest
            webdeposit_draft = max(webdeposit_draft_query.all(), key=lambda w: w.step)
        elif deposition_type is not None:
            webdeposit_draft = db.session.query(WebDepositDraft).\
                                            join(Workflow).\
                                            filter(
                            Workflow.user_id == user_id,
                            Workflow.name == deposition_type,
                            WebDepositDraft.timestamp == db.func.max(
                            WebDepositDraft.timestamp).select())[0]
        else:
            webdeposit_draft = db.session.query(WebDepositDraft).\
                                            join(Workflow).\
                                            filter(
                                        Workflow.user_id == user_id,
                                        WebDepositDraft.timestamp == db.func.max(
                                        WebDepositDraft.timestamp).select())[0]
    except NoResultFound:
        # No Form draft was found
        return None, None

    form = forms[webdeposit_draft.form_type]()
    draft_data = webdeposit_draft.form_values

    for field_name, field_data in form.data.iteritems():
        if isinstance(form.__dict__['_fields'][field_name], FormField) \
                and field_name in draft_data:
            subfield_names = form.__dict__['_fields'][field_name].form.__dict__['_fields'].keys()
            #upperfield_name, subfield_name = field_name.split('-')
            for subfield_name in subfield_names:
                if subfield_name in draft_data[field_name]:
                    form.__dict__["_fields"][field_name].\
                        form.__dict__["_fields"][subfield_name].\
                            process_data(draft_data[field_name][subfield_name])
        elif field_name in draft_data:
            form[field_name].process_data(draft_data[field_name])

    return webdeposit_draft.uuid, form


def get_form(user_id, uuid, step=None):
    """ Returns the current state of the workflow in a form
        or a previous state (step)
    """

    if step is None:
        webdeposit_draft_query = db.session.query(WebDepositDraft).\
                                join(Workflow).\
                                filter(
                                Workflow.user_id == user_id,
                                WebDepositDraft.uuid == uuid)
        try:
            # get the draft with the max step
            webdeposit_draft = max(webdeposit_draft_query.all(), key=lambda w: w.step)
        except ValueError:
            return None
    else:
        webdeposit_draft = db.session.query(WebDepositDraft).\
                            join(Workflow).\
                            filter(
                            Workflow.user_id == user_id,
                            WebDepositDraft.uuid == uuid,
                            WebDepositDraft.step == step).one()

    form = forms[webdeposit_draft.form_type]()

    draft_data = webdeposit_draft.form_values

    for field_name, field_data in form.data.iteritems():
        if isinstance(form.__dict__['_fields'][field_name], FormField) \
                and field_name in draft_data:
            subfield_names = form.__dict__['_fields'][field_name].\
                             form.__dict__['_fields'].keys()
            #upperfield_name, subfield_name = field_name.split('-')
            for subfield_name in subfield_names:
                if subfield_name in draft_data[field_name]:
                    form.__dict__["_fields"][field_name].\
                        form.__dict__["_fields"][subfield_name].\
                            process_data(draft_data[field_name][subfield_name])
        elif field_name in draft_data:
            form[field_name].process_data(draft_data[field_name])

    return form


def get_last_step(steps):
    if type(steps[-1]) is list:
        return get_last_step[-1]
    else:
        return steps[-1]


def get_current_step(user_id, uuid):
    webdep_workflow = db.session.query(Workflow).filter(\
                Workflow.uuid == uuid).one()
    steps = webdep_workflow.task_counter

    return get_last_step(steps)


""" Draft Functions (or instances of forms)
old implementation with redis cache of the functions is provided in comments
(works only in the article form, needs to be generic)
"""


def draft_field_get(user_id, uuid, field_name, subfield_name=None):
    """ Returns the value of a field
        or, in case of error, None
    """

    webdeposit_draft_query = db.session.query(WebDepositDraft).\
                            join(Workflow).\
                            filter(
                            Workflow.user_id == user_id,
                            WebDepositDraft.uuid == uuid)
    # get the draft with the max step
    draft = max(webdeposit_draft_query.all(), key=lambda w: w.step)

    values = draft.form_values

    try:
        if subfield_name is not None:
            return values[field_name][subfield_name]
        return values[field_name]
    except KeyError:
        return None


def draft_field_error_check(user_id, uuid, field_name, value):
    """ Retrieves the form based on the uuid
        and returns a json string evaluating the field's value
    """

    form = get_form(user_id, uuid=uuid)

    subfield_name = None
    subfield_name = None
    if '-' in field_name:  # check if its subfield
        field_name, subfield_name = field_name.split('-')

        form = form.__dict__["_fields"][field_name].form
        field_name = subfield_name

    form.__dict__["_fields"][field_name].process_data(value)
    return form.__dict__["_fields"][field_name].pre_validate(form)


def draft_field_set(user_id, uuid, field_name, value):
    """ Alters the value of a field """

    webdeposit_draft_query = db.session.query(WebDepositDraft).\
                            join(Workflow).\
                            filter(
                            Workflow.user_id == user_id,
                            WebDepositDraft.uuid == uuid)
    # get the draft with the max step
    draft = max(webdeposit_draft_query.all(), key=lambda w: w.step)
    values = draft.form_values

    subfield_name = None
    if '-' in field_name:  # check if its subfield
        field_name, subfield_name = field_name.split('-')

    if subfield_name is not None:
        try:
            values[field_name][subfield_name] = value
        except (KeyError, TypeError):
            values[field_name] = dict()
            values[field_name][subfield_name] = value
    else:
        values[field_name] = value  # change value
    #draft.form_values = values
    #draft.timestamp = datetime.now()  # update draft's timestamp
    webdeposit_draft_query = db.session.query(WebDepositDraft).\
                            filter(WebDepositDraft.uuid == uuid,
                                   WebDepositDraft.step == draft.step).\
                            update({"form_values": values,
                                   "timestamp": datetime.now()})


def draft_field_list_add(user_id, uuid, field_name, value, key=None, subfield=None):
    """Adds value to field
    Used for fields that contain multiple values
    e.g.1: { field_name : value1 } OR
           { field_name : [value1] }
           -->
           { field_name : [value1, value2] }
    e.g.2  { }
           -->
           { field_name : [value] }
    e.g.3  { }
           -->
           { field_name : {key : value} }
    """

    webdeposit_draft_query = db.session.query(WebDepositDraft).\
                            join(Workflow).\
                            filter(
                            Workflow.user_id == user_id,
                            WebDepositDraft.uuid == uuid)
    # get the draft with the max step
    draft = max(webdeposit_draft_query.all(), key=lambda w: w.step)
    values = draft.form_values

    try:
        if isinstance(values[field_name], list):
            values[field_name].append(value)
        elif key is not None:
            if not isinstance(values[field_name], dict):
                values[field_name] = dict()
            values[field_name][subfield] = value
        else:
            new_values_list = [values[field_name]]
            new_values_list.append(value)
            values[field_name] = new_values_list
    except KeyError:
        values[field_name] = [value]

    webdeposit_draft_query.update({"form_values": values,
                                   "timestamp": datetime.now()})


def new_draft(user_id, deposition_type, form_type):
    """ Creates new draft
        gets new uuid
        (deprecated inside workflow context)
    """

    webdeposit_draft = WebDepositDraft(user_id=user_id, \
                                     form_type=form_type, \
                                     form_values={})
    db.session.add(webdeposit_draft)
    db.session.commit()
    return webdeposit_draft.uuid


def get_draft(user_id, uuid, field_name=None):
    """ Returns draft values in a field_name => field_value dictionary
        or if field_name is defined, returns the associated value
    """

    webdeposit_draft_query = db.session.query(WebDepositDraft).\
                            join(Workflow).\
                            filter(
                            Workflow.user_id == user_id,
                            WebDepositDraft.uuid == uuid)
    # get the draft with the max step
    draft = max(webdeposit_draft_query.all(), key=lambda w: w.step)

    form_values = draft.form_values

    if field_name is None:
        return form_values
    else:
        try:
            return form_values[field_name]
        except KeyError:  # field_name doesn't exist
            return form_values  # return whole row


def delete_draft(user_id, deposition_type, uuid):
    """ Deletes the draft with uuid=uuid
        and returns the most recently used draft
        if there is no draft left, returns None
        (usage not recommended inside workflow context)
    """

    db.session.query(WebDepositDraft).filter_by(\
                                     uuid=uuid, \
                                     user_id=user_id).delete()
    db.session.commit()

    latest_draft = db.session.query(WebDepositDraft).filter_by(\
                                    user_id=user_id, \
                                    deposition_type=deposition_type).\
                                    order_by(\
                                        desc(WebDepositDraft.timestamp)).\
                                    first()
    if latest_draft is None:  # There is no draft left
        return None
    else:
        return latest_draft.uuid


def draft_field_get_all(user_id, deposition_type):
    """ Returns a list with values of the field_names specified
        containing all the latest drafts
        of deposition of type=deposition_type
    """

    ## Select drafts with max step from each uuid.
    subquery = db.session.query(WebDepositDraft.uuid,
                                db.func.max(WebDepositDraft.step)).\
                    join(WebDepositDraft.workflow).\
                    filter(db.and_(
                        Workflow.status == CFG_WORKFLOW_STATUS['running'],
                        Workflow.user_id == user_id,
                        Workflow.name == deposition_type,
                        Workflow.module_name == 'webdeposit'
                    )).\
                    group_by(WebDepositDraft.uuid)

    drafts = WebDepositDraft.query.filter(db.tuple_(WebDepositDraft.uuid,
                                                    WebDepositDraft.step).\
                                          in_(subquery)).\
                                   order_by(db.desc(WebDepositDraft.timestamp)).\
                                   all()
    return drafts


def set_current_draft(user_id, uuid):
    webdeposit_draft_query = db.session.query(WebDepositDraft).\
                            join(Workflow).\
                            filter(
                            Workflow.user_id == user_id,
                            WebDepositDraft.uuid == uuid)
    # get the draft with the max step
    draft = max(webdeposit_draft_query.all(), key=lambda w: w.step)

    draft.timestamp = datetime.now()
    db.session.commit()


def get_current_draft(user_id, deposition_type):
    webdeposit_draft = db.session.query(WebDepositDraft).\
                        join(Workflow).\
                        filter(
                        Workflow.user_id == user_id,
                        Workflow.name == deposition_type).\
                        order_by(desc(WebDepositDraft.timestamp)). \
                        first()
    return webdeposit_draft
