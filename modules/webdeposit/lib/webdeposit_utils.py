from sqlalchemy import func
from werkzeug.contrib.cache import RedisCache
from invenio.sqlalchemyutils import db
from webdeposit_model import WebSubmitDraft

import datetime
import json

#rediscache = RedisCache("localhost", default_timeout=9000)

""" Draft Functions
    implementation with redis cache of the functions is provided in comments 
"""
def draft_field_get(user_id, draft_id, form_type, fieldName):
    user_id = int(user_id)
    draft_id = int(draft_id)
    websubmit_draft = WebSubmitDraft(draft_id=draft_id, \
                                     user_id=user_id, \
                                     form_type=form_type)
    draft = db.session.query(WebSubmitDraft).filter_by(draft_id=draft_id, \
                                                       user_id=user_id, \
                                                       form_type=form_type)[0]
    values = json.loads(draft.form_values)

    try:
        return values[fieldName]
    except KeyError:
        return None
    """
    userID = str(userID)
    draftID = str(draftID)
    return rediscache.get(userID + ":" + draftID + ":" + fieldName)
    """

def draft_field_set(user_id, draft_id, form_type, field_name, value):
    user_id = int(user_id)
    draft_id = int(draft_id)

    websubmit_draft = WebSubmitDraft(draft_id=draft_id, \
                                     user_id=user_id, \
                                     form_type=form_type)
    draft = db.session.query(WebSubmitDraft).filter_by(draft_id=draft_id, \
                                                       user_id=user_id, \
                                                       form_type=form_type)[0]
    values = json.loads(draft.form_values) #get dict
    values[field_name] = value #change value
    values = json.dumps(values) #encode back to json
    draft.form_values = values
    db.session.commit()

    """
    userID = str(userID)
    draftID = str(draftID)
    rediscache.set(userID + ":" + draftID + ":" + fieldName, value)
    """

def draft_field_list_add(user_id, draft_id, form_type, field_name, value):
    user_id = int(user_id)
    draft_id = int(draft_id)

    draft = db.session.query(WebSubmitDraft).filter_by(draft_id=draft_id, \
                                                       user_id=user_id, \
                                                       form_type=form_type)[0]
    values = json.loads(draft.form_values) #get dict

    try:
        if isinstance(values[field_name], list):
            values[field_name].append(value)
        else:
            new_values_list = [values[field_name]]
            new_values_list.append(value)
            values[field_name] = new_list
    except KeyError:
        values[field_name] = [value]

    values = json.dumps(values) #encode back to json
    draft.form_values = values
    db.session.commit()


def new_draft(user_id, form_type):
    user_id = int(user_id)

    websubmit_draft = WebSubmitDraft(user_id=user_id, form_type=form_type, form_values='{}')
    db.session.add(websubmit_draft)
    db.session.commit()
    return websubmit_draft.draft_id

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

def get_new_draft_id(userID):
    return rediscache.inc(str(userID) + ":draftcounter", delta=1)


def get_draft(user_id, draft_id, form_type):
    user_id = int(user_id)
    draft_id = int(draft_id)
    draft = db.session.query(WebSubmitDraft).filter_by(draft_id=draft_id, user_id=user_id, form_type=form_type)[0]
    form_values = json.loads(draft.form_values)

    return form_values
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


def delete_draft(user_id, draft_id, form_type):
    user_id = int(user_id)
    draft_id = int(draft_id)

    db.session.query(WebSubmitDraft).filter_by(draft_id=draft_id, user_id=user_id, form_type=form_type).delete()
    db.session.commit()
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

def draft_field_get_all(user_id, form_type, field_name):
    user_id = int(user_id)
    all_drafts = []
    for draft in db.session.query(WebSubmitDraft).filter_by(user_id=user_id, \
                                                            form_type=form_type):
        draft_values = json.loads(draft.form_values)
        try:
            tmp_draft = {"draft_id" : int(draft.draft_id), field_name : draft_values[field_name]}
        except KeyError:
            tmp_draft = {"draft_id" : int(draft.draft_id), field_name : None}
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

def set_current_draft(user_id, draft_id):
    draft = db.session.query(WebSubmitDraft).filter_by(draft_id=draft_id)[0]
    draft.timestamp = datetime.datetime.now()
    db.session.commit()

    """
    draftID = str(draftID)
    rediscache.set(str(userID) + ":current_draft", draftID)
    """

def get_current_draft(userID):
    websubmit_draft = db.session.query(WebSubmitDraft).filter(\
                     WebSubmitDraft.timestamp == func.max(WebSubmitDraft.timestamp).select())[0]
    return websubmit_draft
    """
    return rediscache.get(str(userID) + ":current_draft")
    """

# Misc functions

def escape(s):
    ambersands_escape_table = { \
        "&amp;" : "&", \
        "&quot;" : '"' , \
        "&apos;" : "'", \
        "&gt;" : ">", \
        "&lt;" : "<", \
        "&#34;" : "\"" \
    }

    for (a, h) in ambersands_escape_table.items():
        s = s.replace(a, h)
    return s

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
