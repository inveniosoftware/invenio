from sqlalchemy import func, desc
from wtforms import FormField
#from werkzeug.contrib.cache import RedisCache
from invenio.sqlalchemyutils import db
from sqlalchemy.orm.exc import NoResultFound
from webdeposit_model import WebDepositDraft, \
                             WebDepositWorkflow
from invenio.webdeposit_workflow import DepositionWorkflow
from webdeposit_load_forms import forms

import datetime
import json
import uuid as new_uuid

#rediscache = RedisCache("localhost", default_timeout=9000)

""" Deposition Type Functions """


def get_latest_or_new_workflow(deposition_type):
    from invenio.webuser_flask import current_user
    from invenio.webdeposit_load_dep_metadata import dep_metadata

    user_id = current_user.get_id()

    try:
        wf = dep_metadata[deposition_type]["workflow"]
    except KeyError:
        # deposition type not found
        return None

    try:
        webdeposit_draft = db.session.query(WebDepositDraft).filter(\
                WebDepositDraft.user_id == user_id, \
                WebDepositDraft.dep_type == deposition_type, \
                WebDepositDraft.timestamp == func.max(\
                    WebDepositDraft.timestamp).select()).one()
    except NoResultFound:
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
    from invenio.webdeposit_load_dep_metadata import dep_metadata
    try:
        wf = dep_metadata[deposition_type]["workflow"]
    except KeyError:
        # deposition type not found
        raise
        return None
    return DepositionWorkflow(uuid=uuid,
                              deposition_type=deposition_type,
                              workflow=wf)


def create_workflow(user_id, deposition_type):
    from invenio.webdeposit_load_dep_metadata import dep_metadata

    try:
        wf = dep_metadata[deposition_type]["workflow"]
    except KeyError:
        # deposition type not found
        return None

    return DepositionWorkflow(deposition_type=deposition_type, workflow=wf)


def create_dep_type(user_id, dep_type):
    """Creates a deposition object (initiates workflow)
    and returns the uuid and the form to be rendered
    TODO: check if dep type exists
    """

    from invenio.webdeposit_load_dep_metadata import dep_metadata

    try:
        wf = dep_metadata[dep_type]["workflow"]
    except KeyError:
        # dep_type not found
        return None, None

    webdep_workflow = DepositionWorkflow(workflow=wf, deposition_type=dep_type)
    webdep_workflow.run()
    uuid = webdep_workflow.get_uuid()
    return get_current_form(user_id, uuid=uuid)

    form_type = form.__class__.__name__
    uuid = new_uuid.uuid1()
    status = 0 # not completed
    webdeposit_draft = WebDepositDraft(uuid=uuid, \
                                     user_id=user_id, \
                                     dep_type=dep_type, \
                                     form_type=form_type, \
                                     form_values='{}', \
                                     timestamp=func.current_timestamp(), \
                                     status=status)
    db.session.add(webdeposit_draft)
    db.session.commit()

    return webdeposit_draft.uuid, form


def get_current_form(user_id, dep_type=None, uuid=None):
    """Returns the latest draft(wtform object) of the dep_type
    or the form with the specific uuid.
    if it doesn't exist, creates a new one
    """

    if user_id is None:
        return None

    try:
        if uuid is not None:
            webdeposit_draft_query = db.session.query(WebDepositDraft).filter(\
                            WebDepositDraft.user_id == user_id, \
                            WebDepositDraft.uuid == uuid)
            webdeposit_draft = webdeposit_draft_query.\
                                   group_by(WebDepositDraft.uuid).\
                                   having(func.max(WebDepositDraft.step))[0]
        elif dep_type is not None:
            webdeposit_draft = db.session.query(WebDepositDraft).filter(\
                            WebDepositDraft.user_id == user_id, \
                            WebDepositDraft.dep_type == dep_type, \
                            WebDepositDraft.timestamp == func.max(\
                                WebDepositDraft.timestamp).select())[0]
        else:
            webdeposit_draft = db.session.query(WebDepositDraft).filter(\
                            WebDepositDraft.user_id == user_id, \
                            WebDepositDraft.timestamp == func.max(\
                                WebDepositDraft.timestamp).select())[0]
    except NoResultFound:
        # No Form draft was found
        return None, None

    form = forms[webdeposit_draft.form_type]()
    draft_data = json.loads(webdeposit_draft.form_values)

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
        webdeposit_draft_query = db.session.query(WebDepositDraft).filter(\
                                WebDepositDraft.user_id == user_id, \
                                WebDepositDraft.uuid == uuid)
        try:
            # get the draft with the max step
            webdeposit_draft = max(webdeposit_draft_query.all(), key=lambda w: w.step)
        except ValueError:
            return None
    else:
        webdeposit_draft = db.session.query(WebDepositDraft).filter(\
                            WebDepositDraft.user_id == user_id, \
                            WebDepositDraft.uuid == uuid,
                            WebDepositDraft.step == step).one()

    form = forms[webdeposit_draft.form_type]()

    draft_data = json.loads(webdeposit_draft.form_values)

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


def get_current_step(user_id, uuid):
    webdep_workflow = db.session.query(WebDepositWorkflow).filter(\
                WebDepositWorkflow.uuid == uuid).one()
    return webdep_workflow.current_step


""" Draft Functions (or instances of forms)
old implementation with redis cache of the functions is provided in comments
(works only in the article form, needs to be generic)
"""


def draft_field_get(user_id, uuid, field_name, subfield_name=None):
    """Returns the value of a field
    or, in case of error, None
    """

    draft = db.session.query(WebDepositDraft).filter(WebDepositDraft.uuid == uuid, \
                                                     WebDepositDraft.user_id == user_id)[0]
    values = json.loads(draft.form_values)

    try:
        if subfield_name is not None:
             return values[field_name][subfield_name]
        return values[field_name]
    except KeyError:
        return None
    """
    userID = str(userID)
    draftID = str(draftID)
    return rediscache.get(userID + ":" + draftID + ":" + fieldName)
    """


def draft_field_set(user_id, uuid, field_name, value, subfield_name=None):
    """
    Alters the value of a field
    """

    webdeposit_draft_query = db.session.query(WebDepositDraft).filter(\
                            WebDepositDraft.user_id == user_id, \
                            WebDepositDraft.uuid == uuid)
    draft = webdeposit_draft_query.\
                           group_by(WebDepositDraft.uuid).\
                           having(func.max(WebDepositDraft.step))[0]

    values = json.loads(draft.form_values)  #get dict
    if subfield_name is not None:
        try:
            values[field_name][subfield_name] = value
        except (KeyError, TypeError) as e:
            values[field_name] = dict()
            values[field_name][subfield_name] = value
    else:
        values[field_name] = value  #change value
    values = json.dumps(values)  #encode back to json
    draft.form_values = values
    draft.timestamp = datetime.datetime.now() #update draft's timestamp
    db.session.commit()

    """
    userID = str(userID)
    draftID = str(draftID)
    rediscache.set(userID + ":" + draftID + ":" + fieldName, value)
    """


def draft_field_list_add(user_id, uuid, field_name, value, subfield=None):
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

    webdeposit_draft_query = db.session.query(WebDepositDraft).filter(\
                            WebDepositDraft.user_id == user_id, \
                            WebDepositDraft.uuid == uuid)
    draft = webdeposit_draft_query.\
                           group_by(WebDepositDraft.uuid).\
                           having(func.max(WebDepositDraft.step))[0]
    values = json.loads(draft.form_values)  #get dict

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

    values = json.dumps(values)  #encode back to json
    draft.form_values = values
    db.session.commit()


def new_draft(user_id, dep_type, form_type):
    """Creates new draft
    gets new uuid
    (deprecated inside workflow context)
    """

    webdeposit_draft = WebDepositDraft(user_id=user_id, \
                                     form_type=form_type, \
                                     form_values='{}')
    db.session.add(webdeposit_draft)
    db.session.commit()
    return webdeposit_draft.uuid

    """
    userID = str(userID)
    draftID = get_new_draft_id(userID)
    drafts = rediscache.get(userID + ":drafts")
    if drafts is None:
        rediscache.set(str(userID) + ":drafts", str(draftID))
    else:
        newdrafts = drafts + ":" + str(draftID)
        rediscache.set(str(userID) + ":drafts", newdrafts)

    return draftID
    """

#def get_new_draft_id(userID):
#    return rediscache.inc(str(userID) + ":draftcounter", delta=1)

def get_draft(user_id, uuid, field_name=None):
    """Returns draft values in a field_name => field_value dictionary
    or if field_name is defined, returns the associated value
    """

    form_values = json.loads(draft.form_values)

    if field_name is None:
        return form_values
    else:
        try:
            return form_values[field_name]
        except KeyError: # field_name doesn't exist
            return form_values #return whole row
    """
    userID = str(userID)
    if draftID is None:
        return None
    else:
        drafts = rediscache.get(userID + ":drafts")
        if drafts is None:
            return None
        elif str(draftID) not in drafts.split(":"):
            return None
        else:
            draftID = str(draftID)
            publisher, journal, issn, doctitle, author, \
            abstract, pagesnum, language, date, notes, conditions \
 = rediscache.get_many(userID + ":" + draftID + ":publisher", \
                                   userID + ":" + draftID + ":journal", \
                                   userID + ":" + draftID + ":issn", \
                                   userID + ":" + draftID + ":doctitle", \
                                   userID + ":" + draftID + ":author", \
                                   userID + ":" + draftID + ":abstract", \
                                   userID + ":" + draftID + ":pagesnum", \
                                   userID + ":" + draftID + ":language", \
                                   userID + ":" + draftID + ":date", \
                                   userID + ":" + draftID + ":notes", \
                                   userID + ":" + draftID + ":conditions")
            return { "id"        : draftID, \
                     "publisher" : publisher, \
                     "journal"   : journal, \
                     "issn"      : issn, \
                     "doctitle"  : doctitle, \
                     "author"    : author, \
                     "abstract"  : abstract, \
                     "pagesnum"  : pagesnum, \
                     "language"  : language, \
                     "date"      : date, \
                     "notes"     : notes, \
                     "conditions": conditions
                    }
    """


def delete_draft(user_id, dep_type, uuid):
    """ Deletes the draft with uuid=uuid
    and returns the most recently used draft
    if there is no draft left, returns None
    """

    db.session.query(WebDepositDraft).filter_by(\
                                     uuid=uuid, \
                                     user_id=user_id).delete()
    db.session.commit()

    latest_draft = db.session.query(WebDepositDraft).filter_by(\
                                    user_id=user_id, \
                                    dep_type=dep_type).\
                                    order_by(\
                                        desc(WebDepositDraft.timestamp)).\
                                    first()
    if latest_draft is None: # There is no draft left
        return None
    else:
        return latest_draft.uuid


    """
    userID = str(userID)
    draftID = str(draftID)
    drafts = rediscache.get(userID + ":drafts")
    newdrafts = ""
    i = 0;
    for did in drafts.split(":"):
        if did != draftID:
            print did + "not equal to" + draftID
            if i is not 0:
                newdrafts += ":" + did
            else:
                newdrafts += did
            i += 1
    rediscache.set(userID + ":drafts", newdrafts)
    draftIDs = newdrafts.split(":")
    i = len(draftIDs) - 1
    set_current_draft(userID, draftIDs[i])
    #return the last draft
    return draftIDs[i]
    """


def draft_field_get_all(user_id, dep_type, field_names):
    all_drafts = []

    if not isinstance(field_names, list):
        field_names = [field_names]

    for draft in db.session.query(WebDepositDraft).filter_by(user_id=user_id, \
                                                            dep_type=dep_type).\
                                                   group_by(WebDepositDraft.uuid).\
                                                   having(func.max(WebDepositDraft.step)):
        draft_values = json.loads(draft.form_values)

        tmp_draft = {"draft_id": draft.uuid, \
                     "dep_type": draft.dep_type, \
                     "timestamp": draft.timestamp}
        for field_name in field_names:
            try:
                tmp_draft[field_name] = draft_values[field_name]
            except KeyError:
                    tmp_draft[field_name] = None
        all_drafts.append(tmp_draft)


    return all_drafts

    """
    userID = str(userID)
    drafts = rediscache.get(userID + ":drafts")
    if drafts is None:
        drafts = ""
    draftIDs = drafts.split(":")
    allDrafts = []
    for draftID in draftIDs:
        tempDraft = get_draft(userID, draftID)
        allDrafts.append(tempDraft)

    return allDrafts
    """


def set_current_draft(user_id, uuid):
    webdeposit_draft_query = db.session.query(WebDepositDraft).filter(\
                            WebDepositDraft.user_id == user_id, \
                            WebDepositDraft.uuid == uuid)
    draft = webdeposit_draft_query.\
                           group_by(WebDepositDraft.uuid).\
                           having(func.max(WebDepositDraft.step))[0]
    draft.timestamp = datetime.datetime.now()
    db.session.commit()

    """
    draftID = str(draftID)
    rediscache.set(str(userID) + ":current_draft", draftID)
    """


def get_current_draft(user_id, dep_type):
    webdeposit_draft = db.session.query(WebDepositDraft). \
                                filter_by(\
                                    user_id=user_id, \
                                    dep_type=dep_type).\
                                order_by(desc(WebDepositDraft.timestamp)). \
                                first()
    return webdeposit_draft
    """
    return rediscache.get(str(userID) + ":current_draft")
    """

""" Misc functions """


def pretty_date(time=False):
    """ Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    from datetime import datetime

    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return  "a minute ago"
        if second_diff < 3600:
            return str(second_diff / 60) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(second_diff / 3600) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff / 7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff / 30) + " months ago"
    return str(day_diff / 365) + " years ago"


def escape(s):
    ambersands_escape_table = { \
        "&amp;": "&", \
        "&quot;": '"', \
        "&apos;": "'", \
        "&gt;": ">", \
        "&lt;": "<", \
        "&#34;": "\""}

    for (a, h) in ambersands_escape_table.items():
        s = s.replace(a, h)
    return s
