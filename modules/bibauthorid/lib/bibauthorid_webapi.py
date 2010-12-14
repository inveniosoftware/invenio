# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
'''
Bibauthorid_webapi
Point of access to the documents clustering facility. 
Provides utilities to safely interact with stored data.
'''

import invenio.bibauthorid_personid_tables_utils as tu
from invenio.dbquery import OperationalError
from invenio.access_control_admin import acc_find_user_role_actions
from cgi import escape
from time import gmtime, strftime


def export_person_ids_to_marc():
    '''
    Exports person id to the correspondent marc field for the search engine
    '''
    pass


def get_possible_person_ids(name_string):
    '''
    Returns one or more person ids which best matches the name given
    (More then one: we are not sure about which person)
    '''
    pass


def get_user_level(uid):
    '''
    Finds and returns the aid-universe-internal numeric user level
    
    @param uid: the user's id
    @type uid: int
    
    @return: A numerical representation of the maximum access level of a user
    @rtype: int
    '''
    actions = [row[1] for row in acc_find_user_role_actions({'uid': uid})]
    return max([tu.resolve_paper_access_right(acc) for acc in actions])


def get_person_id_from_paper(bibref=None):
    '''
    Returns the id of the person who wrote the paper
    
    @param bibref: the bibref,bibrec pair that identifies the person
    @type bibref: str
    
    @return: the person id
    @rtype: int
    '''
    if not _is_valid_bibref(bibref):
        return - 1

    person_id = -1
    db_data = tu.get_papers_status([(bibref,)])

    try:
        person_id = db_data[0][1]
    except (IndexError):
        pass

    return person_id


def get_papers_by_person_id(person_id= -1, rec_status= -2):
    '''
    Returns all the papers written by the person

    @param person_id: identifier of the person to retrieve papers from
    @type person_id: int
    @param rec_status: minimal flag status a record must have to be displayed
    @type rec_status: int
    
    @return: list of record ids
    @rtype: list of int
    '''
    if not isinstance(person_id, int):
        try:
            person_id = int(person_id)
        except (ValueError, TypeError):
            return []

    if person_id < 0:
        return []

    if not isinstance(rec_status, int):
        return []

    db_data = tu.get_person_papers((person_id,),
                                   rec_status,
                                   show_author_name=True,
                                   show_title=False)
    records = [[row["data"].split(",")[1], row["data"], row["flag"],
                row["authorname"]] for row in db_data]

    return records


def get_papers_cluster(bibref):
    '''
    Returns the cluster of documents connected with this one

    @param bibref: the table:bibref,bibrec pair to look for
    @type bibref: str

    @return: a list of record IDs
    @rtype: list of int
    '''
    papers = []
    person_id = get_person_id_from_paper(bibref)

    if person_id > -1:
        papers = get_papers_by_person_id(person_id)

    return papers


def get_person_names_from_id(person_id= -1):
    '''
    Finds and returns the names associated with this person along with the
    frequency of occurrence (i.e. the number of papers)
    
    @param person_id: an id to find the names for
    @type person_id: int
    
    @return: name and number of occurrences of the name
    @rtype: tuple of tuple
    '''
#    #retrieve all rows for the person
    if (not person_id > -1) or (not isinstance(person_id, int)):
        return []

    return tu.get_person_names_count((person_id,))


def get_paper_status(person_id, bibref):
    '''
    Finds an returns the status of a bibrec to person assignment
    
    @param person_id: the id of the person to check against
    @type person_id: int
    @param bibref: the bibref-bibrec pair that unambiguously identifies a paper
    @type bibref: string
    '''
    db_data = tu.get_papers_status([[bibref]])
    #data,PersonID,flag
    status = None

    try:
        status = db_data[0][2]
    except IndexError:
        status = -10

    return status


def _wash_integer_id(param_id):
    '''
    Creates an int out of either int or string
    
    @param param_id: the number to be washed
    @type param_id: int or string
    
    @return: The int representation of the param or -1
    @rtype: int
    '''
    pid = -1

    try:
        pid = int(param_id)
    except (ValueError, TypeError):
        return (-1)

    return pid


def _is_valid_bibref(bibref):
    '''
    Determines if the provided string is a valid bibref-bibrec pair
    
    @param bibref: the bibref-bibrec pair that unambiguously identifies a paper
    @type bibref: string
    
    @return: True if it is a bibref-bibrec pair and False if it's not
    @rtype: boolean
    '''
    if (not isinstance(bibref, str)) or (not bibref):
        return False

    if not bibref.count(":"):
        return False

    if not bibref.count(","):
        return False

    try:
        table = bibref.split(":")[0]
        ref = bibref.split(":")[1].split(",")[0]
        bibrec = bibref.split(":")[1].split(",")[1]
    except IndexError:
        return False

    try:
        table = int(table)
        ref = int(ref)
        bibrec = int(bibrec)
    except (ValueError, TypeError):
        return False

    return True


def confirm_person_bibref_assignments(person_id, bibrefs, uid):
    '''
    Confirms a bibref-bibrec assignment to a person. That internally
    raises the flag of the entry to 2, which means 'user confirmed' and
    sets the user level to the highest level of the user provided as param
    
    @param person_id: the id of the person to confirm the assignment to
    @type person_id: int
    @param bibrefs: the bibref-bibrec pairs that unambiguously identify records
    @type bibrefs: list of strings
    @param uid: the id of the user that arranges the confirmation
    @type uid: int
    
    @return: True if the process ran smoothly, False if there was an error
    @rtype: boolean
    '''
    pid = _wash_integer_id(person_id)
    refs = []

    if pid < 0:
        return False

    if not isinstance(bibrefs, list) or not len(bibrefs):
        return False
    else:
        for bibref in bibrefs:
            if _is_valid_bibref(bibref):
                refs.append((bibref,))
            else:
                return False

    try:
        tu.confirm_papers_to_person((pid,), refs, get_user_level(uid))
    except OperationalError:
        return False

    return True


def repeal_person_bibref_assignments(person_id, bibrefs, uid):
    '''
    Repeals a bibref-bibrec assignment from a person. That internally
    sets the flag of the entry to -2, which means 'user repealed' and
    sets the user level to the highest level of the user provided as param
    
    @param person_id: the id of the person to repeal the assignment from
    @type person_id: int
    @param bibrefs: the bibref-bibrec pairs that unambiguously identify records
    @type bibrefs: list of strings
    @param uid: the id of the user that arranges the repulsion
    @type uid: int
    
    @return: True if the process ran smoothly, False if there was an error
    @rtype: boolean
    '''
    pid = _wash_integer_id(person_id)
    refs = []

    if pid < 0:
        return False

    if not isinstance(bibrefs, list) or not len(bibrefs):
        return False
    else:
        for bibref in bibrefs:
            if _is_valid_bibref(bibref):
                refs.append((bibref,))
            else:
                return False

    try:
        tu.reject_papers_from_person((pid,), refs, get_user_level(uid))
    except OperationalError:
        return False

    return True


def reset_person_bibref_decisions(person_id, bibrefs):
    '''
    Resets a bibref-bibrec assignment of a person. That internally
    sets the flag of the entry to 0, which means 'no user interaction' and
    sets the user level to 0 to give the record free for claiming/curation
    
    @param person_id: the id of the person to reset the assignment from
    @type person_id: int
    @param bibrefs: the bibref-bibrec pairs that unambiguously identify records
    @type bibrefs: list of strings
    
    @return: True if the process ran smoothly, False if there was an error
    @rtype: boolean
    '''
    pid = _wash_integer_id(person_id)
    refs = []

    if pid < 0:
        return False

    if not isinstance(bibrefs, list) or not len(bibrefs):
        return False
    else:
        for bibref in bibrefs:
            if _is_valid_bibref(bibref):
                refs.append((bibref,))
            else:
                return False

    try:
        tu.reset_papers_flag((person_id,), refs)
    except OperationalError:
        return False

    return True


def add_person_comment(person_id, message):
    '''
    Adds a comment to a person after enriching it with meta-data (date+time)
    
    @param person_id: person id to assign the comment to
    @type person_id: int
    @param message: defines the comment to set
    @type message: string
    
    @return the message incl. the metadata if everything was fine, False on err
    @rtype: string or boolean
    '''
    msg = ""
    pid = -1
    try:
        msg = str(message)
        pid = int(person_id)
    except (ValueError, TypeError):
        return False

    strtimestamp = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    msg = escape(msg, quote=True)
    dbmsg = "%s;;;%s" % (strtimestamp, msg)
    tu.set_person_data(pid, "comment", dbmsg)

    return dbmsg


def get_person_comments(person_id):
    '''
    Get all comments from a person
    
    @param person_id: person id to get the comments from
    @type person_id: int
    
    @return the message incl. the metadata if everything was fine, False on err
    @rtype: string or boolean
    '''
    pid = -1
    comments = []

    try:
        pid = int(person_id)
    except (ValueError, TypeError):
        return False

    for row in tu.get_person_data(pid, "comment"):
        comments.append(row[1])

    return comments


def search_person_ids_by_name(namequery):
    '''
    Prepares the search to search in the database
    
    @param namequery: the search query the user enquired
    @type namequery: string
    
    @return: information about the result w/ probability and occurrence
    @rtype: tuple of tuple
    '''
    query = ""
    escaped_query = ""

    try:
        query = str(namequery)
    except (ValueError, TypeError):
        return []

    if query:
        escaped_query = escape(query, quote=True)
    else:
        return []

    return tu.find_personIDs_by_name_string(escaped_query)


def log(userinfo, personid, action, tag, value, comment='', transactionid=0):
    '''
    Log an action performed by a user
    
    Examples (in the DB):
    1 2010-09-30 19:30  admin||10.0.0.1  1  assign  paper  1133:4442 'from 23'
    1 2010-09-30 19:30  admin||10.0.0.1  1  assign  paper  8147:4442
    2 2010-09-30 19:35  admin||10.0.0.1  1  reject  paper  72:4442
    
    @param userinfo: information about the user [UID|IP]
    @type userinfo: string
    @param personid: ID of the person this action is targeting
    @type personid: int
    @param action: intended action
    @type action: string
    @param tag: A tag to describe the data entered
    @type tag: string
    @param value: The value of the action described by the tag
    @type value: string
    @param comment: Optional comment to describe the transaction
    @type comment: string
    @param transactionid: May group bulk operations together
    @type transactionid: int
    
    @return: Returns the current transactionid
    @rtype: int
    '''
    userinfo = escape(str(userinfo))
    action = escape(str(action))
    tag = escape(str(tag))
    value = escape(str(value))
    comment = escape(str(comment))

    if not isinstance(personid, int):
        try:
            personid = int(personid)
        except (ValueError, TypeError):
            return - 1

    if not isinstance(transactionid, int):
        try:
            transactionid = int(transactionid)
        except (ValueError, TypeError):
            return - 1

    return tu.insert_user_log(userinfo, personid, action, tag,
                       value, comment, transactionid)


def user_can_modify_data(uid, pid):
    '''
    Determines if a user may modify the data of a person
    
    @param uid: the id of a user (invenio user id)
    @type uid: int
    @param pid: the id of a person
    @type pid: int
    
    @return: True if the user may modify data, False if not
    @rtype: boolean
    
    @raise ValueError: if the supplied parameters are invalid
    '''
    if not isinstance(uid, int):
        try:
            uid = int(uid)
        except (ValueError, TypeError):
            raise ValueError("User ID has to be a number!")

    if not isinstance(pid, int):
        try:
            pid = int(pid)
        except (ValueError, TypeError):
            raise ValueError("Person ID has to be a number!")

    return tu.user_can_modify_data(uid, pid)


def user_can_modify_paper(uid, paper):
    '''
    Determines if a user may modify the record assignments of a person
    
    @param uid: the id of a user (invenio user id)
    @type uid: int
    @param pid: the id of a person
    @type pid: int
    
    @return: True if the user may modify data, False if not
    @rtype: boolean
    
    @raise ValueError: if the supplied parameters are invalid
    '''
    if not isinstance(uid, int):
        try:
            uid = int(uid)
        except (ValueError, TypeError):
            raise ValueError("User ID has to be a number!")

    if not paper:
        raise ValueError("A bibref is expected!")

    return tu.user_can_modify_paper(uid, paper)


def person_bibref_is_touched(pid, bibref):
    '''
    Determines if an assignment has been touched by a user (i.e. check for 
    the flag of an assignment being 2 or -2)
    
    @param pid: the id of the person to check against
    @type pid: int
    @param bibref: the bibref-bibrec pair that unambiguously identifies a paper
    @type bibref: string
    
    @raise ValueError: if the supplied parameters are invalid
    '''
    if not isinstance(pid, int):
        try:
            pid = int(pid)
        except (ValueError, TypeError):
            raise ValueError("Person ID has to be a number!")

    if not bibref:
        raise ValueError("A bibref is expected!")

    return tu.person_bibref_is_touched(pid, bibref)
