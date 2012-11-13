from sqlalchemy import func, desc
#from werkzeug.contrib.cache import RedisCache
from invenio.sqlalchemyutils import db
from webdeposit_model import WebSubmitDraft

import datetime
import json
import uuid as new_uuid

#rediscache = RedisCache("localhost", default_timeout=9000)

""" Document Type Functions """


def create_doc_type(user_id, doc_type):
    """Creates a doc_type (initiates workflow)
    and returns the uuid and the form to be rendered
    TODO: check if doc type exists
    """

    from invenio.webdeposit_load_doc_metadata import doc_metadata

    try:
        form = doc_metadata[doc_type]()
    except KeyError:
        # doc_type not found
        return None, None
    form_type = form.__class__.__name__
    uuid = new_uuid.uuid1()
    websubmit_draft = WebSubmitDraft(uuid=uuid, \
                                     user_id=user_id, \
                                     doc_type=doc_type, \
                                     form_type=form_type, \
                                     form_values='{}', \
                                     timestamp=func.current_timestamp())
    db.session.add(websubmit_draft)
    db.session.commit()

    return websubmit_draft.uuid, form


def get_current_form(user_id, doc_type=None, uuid=None):
    """Returns the latest draft(wtform object) of the doc_type
    or the form with the specific uuid.
    if it doesn't exist, creates a new one
    """

    if user_id is None:
        return None

    from webdeposit_load_forms import forms
    globals().update(forms)

    try:
        if uuid is not None:
            websubmit_draft = db.session.query(WebSubmitDraft).filter(\
                            WebSubmitDraft.user_id == user_id, \
                            WebSubmitDraft.uuid == uuid)[0]
        elif doc_type is not None:
            websubmit_draft = db.session.query(WebSubmitDraft).filter(\
                            WebSubmitDraft.user_id == user_id, \
                            WebSubmitDraft.doc_type == doc_type, \
                            WebSubmitDraft.timestamp == func.max(\
                                WebSubmitDraft.timestamp).select())[0]
        else:
            websubmit_draft = db.session.query(WebSubmitDraft).filter(\
                            WebSubmitDraft.user_id == user_id, \
                            WebSubmitDraft.timestamp == func.max(\
                                WebSubmitDraft.timestamp).select())[0]
    except IndexError:
        if uuid is None:
            """ if a specific form was not requested
            create a new one
            """
            uuid, form = create_doc_type(user_id, doc_type)
            return uuid, form
        else:
            return None, None

    form = globals()[websubmit_draft.form_type]()
    draft_data = json.loads(websubmit_draft.form_values)

    for field_name, field_data in form.data.iteritems():
        if field_name in draft_data:
            form[field_name].process_data(draft_data[field_name])
    return websubmit_draft.uuid, form


""" Draft Functions (or instances of forms)
old implementation with redis cache of the functions is provided in comments
(works only in the article form, needs to be generic)
"""


def draft_field_get(user_id, uuid, field_name):
    """Returns the value of a field
    or, in case of error, None
    """

    draft = db.session.query(WebSubmitDraft).filter_by(uuid=uuid, \
                                                       user_id=user_id)[0]
    values = json.loads(draft.form_values)

    try:
        return values[field_name]
    except KeyError:
        return None
    """
    userID = str(userID)
    draftID = str(draftID)
    return rediscache.get(userID + ":" + draftID + ":" + fieldName)
    """


def draft_field_set(user_id, uuid, field_name, value):
    """
    Alters the value of a field
    """

    draft = db.session.query(WebSubmitDraft).filter_by(uuid=uuid, \
                                                       user_id=user_id)[0]
    values = json.loads(draft.form_values)  #get dict
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


def draft_field_list_add(user_id, uuid, field_name, value):
    """Adds value to field
    Used for fields that contain multiple values
    e.g.1: { field_name : value1 } OR
           { field_name : [value1] }
           -->
           { field_name : [value1, value2] }
    e.g.2  { }
           -->
           { field_name : [value] }
    """

    draft = db.session.query(WebSubmitDraft).filter_by(uuid=uuid, \
                                                       user_id=user_id)[0]
    values = json.loads(draft.form_values)  #get dict

    try:
        if isinstance(values[field_name], list):
            values[field_name].append(value)
        else:
            new_values_list = [values[field_name]]
            new_values_list.append(value)
            values[field_name] = new_values_list
    except KeyError:
        values[field_name] = [value]

    values = json.dumps(values)  #encode back to json
    draft.form_values = values
    db.session.commit()


def new_draft(user_id, doc_type, form_type):
    """Creates new draft
    gets new uuid
    """

    websubmit_draft = WebSubmitDraft(user_id=user_id, \
                                     form_type=form_type, \
                                     form_values='{}')
    db.session.add(websubmit_draft)
    db.session.commit()
    return websubmit_draft.uuid

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
    draft = db.session.query(WebSubmitDraft).filter_by(\
                             uuid=uuid, \
                             user_id=user_id)[0]
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


def delete_draft(user_id, doc_type, uuid):
    """ Deletes the draft with uuid=uuid
    and returns the most recently used draft
    if there is no draft left, returns None
    """

    db.session.query(WebSubmitDraft).filter_by(\
                                     uuid=uuid, \
                                     user_id=user_id).delete()
    db.session.commit()

    latest_draft = db.session.query(WebSubmitDraft).filter_by(\
                                    user_id=user_id, \
                                    doc_type=doc_type).\
                                    order_by(\
                                        desc(WebSubmitDraft.timestamp)).\
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


def draft_field_get_all(user_id, doc_type, field_names):
    all_drafts = []

    if not isinstance(field_names, list):
        field_names = [field_names]

    for draft in db.session.query(WebSubmitDraft).filter_by(user_id=user_id, \
                                                            doc_type=doc_type):
        draft_values = json.loads(draft.form_values)

        tmp_draft = {"draft_id": draft.uuid, \
                     "doc_type": draft.doc_type, \
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
    draft = db.session.query(WebSubmitDraft).filter_by(\
                                             user_id=user_id, \
                                             uuid=uuid)[0]
    draft.timestamp = datetime.datetime.now()
    db.session.commit()

    """
    draftID = str(draftID)
    rediscache.set(str(userID) + ":current_draft", draftID)
    """


def get_current_draft(user_id, doc_type):
    websubmit_draft = db.session.query(WebSubmitDraft). \
                                filter_by(\
                                    user_id=user_id, \
                                    doc_type=doc_type).\
                                order_by(desc(WebSubmitDraft.timestamp)). \
                                first()
    return websubmit_draft
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
