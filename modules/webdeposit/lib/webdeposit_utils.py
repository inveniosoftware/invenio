from werkzeug.contrib.cache import RedisCache
from invenio.sqlalchemyutils import db

rediscache = RedisCache("localhost", default_timeout=9000)


# Draft Functions

def draft_field_get(userID, draftID, fieldName):
    userID = str(userID)
    draftID = str(draftID)
    return rediscache.get(userID + ":" + draftID + ":" + fieldName)


def draft_field_set(userID, draftID, fieldName, value):
    userID = str(userID)
    draftID = str(draftID)
    rediscache.set(userID + ":" + draftID + ":" + fieldName, value)


def new_draft(userID):
    userID = str(userID)
    draftID = get_new_draft_id(userID)
    drafts = rediscache.get(userID + ":drafts")
    if drafts is None:
        rediscache.set(str(userID) + ":drafts", str(draftID))
    else:
        newdrafts = drafts + ":" + str(draftID)
        rediscache.set(str(userID) + ":drafts", newdrafts)

    return draftID


def get_new_draft_id(userID):
    return rediscache.inc(str(userID) + ":draftcounter", delta=1)


def get_draft(userID, draftID):
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


def delete_draft(userID, draftID):
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

def get_drafts(userID):
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


def set_current_draft(userID, draftID):
    draftID = str(draftID)
    rediscache.set(str(userID) + ":current_draft", draftID)

def get_current_draft(userID):
    return rediscache.get(str(userID) + ":current_draft")


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
