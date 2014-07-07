# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
'''
Bibauthorid_webapi
Point of access to the documents clustering facility.
Provides utilities to safely interact with stored data.
'''
import os
from itertools import chain
from copy import deepcopy
from collections import defaultdict

import invenio.bibauthorid_config as bconfig
import invenio.bibauthorid_frontinterface as dbapi
import invenio.bibauthorid_name_utils as nameapi
import invenio.webauthorprofile_interface as webauthorapi

from invenio.bibauthorid_config import PROFILE_IDENTIFIER_URL_MAPPING, PROFILE_IDENTIFIER_WHITELIST
import invenio.search_engine as search_engine
from invenio.bibformat import format_record
from invenio.search_engine import perform_request_search, get_record
from cgi import escape
from invenio.dateutils import strftime
from time import time, gmtime, ctime
from invenio.access_control_admin import acc_find_user_role_actions
from invenio.webuser import collect_user_info, get_session, getUid, email_valid_p
from invenio.webuser import isUserSuperAdmin, get_nickname
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_admin import acc_get_role_id, acc_get_user_roles
from invenio.external_authentication_robot import ExternalAuthRobot
from invenio.external_authentication_robot import load_robot_keys
from invenio.config import CFG_INSPIRE_SITE, CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL, \
    CFG_BIBAUTHORID_ENABLED_REMOTE_LOGIN_SYSTEMS, CFG_WEBAUTHORPROFILE_MAX_HEP_CHOICES, \
    CFG_WEBAUTHORPROFILE_CFG_HEPNAMES_EMAIL, CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG, \
    CFG_BIBUPLOAD_EXTERNAL_OAIID_PROVENANCE_TAG, CFG_BIBAUTHORID_ENABLED
from invenio.config import CFG_SITE_URL
from invenio.mailutils import send_email
from invenio.bibauthorid_name_utils import most_relevant_name
from invenio.bibauthorid_general_utils import is_arxiv_id_or_doi
from invenio.shellutils import retry_mkstemp
from invenio.bibrecord import record_xml_output, record_add_field, record_get_field_instances,\
    record_get_field_value, record_get_field_values, record_has_field
from invenio.bibtask import task_low_level_submission
from invenio.bibauthorid_dbinterface import get_external_ids_of_author, add_arxiv_papers_to_author, get_arxiv_papers_of_author  # pylint: disable-msg=W0614


#
# DB Data Accessors              #
#
def is_profile_available(pid):
    '''
    check if the profile with pid is not claimed to a user

    @param person_id: person id
    @type person_id: int

    @return: returns if profile is available
    @rtype: boolean
    '''
    uid = get_uid_from_personid(pid)

    if uid == -1:
        return True
    return False


def get_bibrec_from_bibrefrec(bibrefrec):

    tmp_split_list = bibrefrec.split(':')
    if len(tmp_split_list) == 1:
        return -1
    tmp_split_list = tmp_split_list[1].split(',')
    if len(tmp_split_list) == 1:
        return -1
    return int(tmp_split_list[1])


def get_bibrefs_from_bibrecs(bibreclist):
    '''
    Retrieve all bibrefs for all the recids in the list

    @param bibreclist: list of record IDs
    @type bibreclist: list of int

    @return: a list of record->bibrefs
    @return: list of lists
    '''
    return [[bibrec, dbapi.get_matching_bibrefs_for_paper([''], bibrec, always_match=True)]
            for bibrec in bibreclist]


def get_canonical_id_from_person_id(person_id):
    '''
    Finds the person  canonical name from personid (e.g. 1)

    @param person_id: person id
    @type person_id: int

    @return: result from the request or person_id on failure
    @rtype: int
    '''
    if not person_id:
        return None

    canonical_name = person_id

    try:
        canonical_name = dbapi.get_canonical_name_of_author(person_id)[0][0]
    except IndexError:
        pass

    return canonical_name


def get_external_ids_from_person_id(pid):
    '''
    Finds the person  external ids (doi, arxivids, ..) from personid (e.g. 1)

    @param person_id: person id
    @type person_id: int

    @return: dictionary of external ids
    @rtype: dict()
    '''
    if not pid or not (isinstance(pid, str) or isinstance(pid, (int, long))):
        return dict()

    if isinstance(pid, str):
        return None

    external_ids = dbapi.get_external_ids_of_author(pid)
    return external_ids


def get_internal_user_id_from_person_id(pid):
    '''
    Finds the person  external ids (doi, arxivids, ..) from personid (e.g. 1)

    @param person_id: person id
    @type person_id: int

    @return: dictionary of external ids
    @rtype: dict()
    '''
    if not pid or not (isinstance(pid, str) or isinstance(pid, (int, long))):
        return dict()

    if isinstance(pid, str):
        return None

    return dbapi.get_internal_user_id_of_author(pid)


def get_longest_name_from_pid(person_id=-1):
    '''
    Finds the longest name of a person to be representative for this person.

    @param person_id: the person ID to look at
    @type person_id: int

    @return: returns the longest normalized name of a person
    @rtype: string
    '''
    if (not person_id > -1) or (not isinstance(person_id, (int, long))):
        if ',' in str(person_id):
            return person_id
        return "This doesn't look like a person ID!"

    longest_name = ""

    for name in dbapi.get_names_count_of_author(person_id):
        if name and len(name[0]) > len(longest_name):
            longest_name = name[0]

    if longest_name:
        return longest_name
    else:
        return "This person does not seem to have a name!"


def get_most_frequent_name_from_pid(person_id=-1, allow_none=False):
    '''
    Finds the most frequent name of a person to be
    representative for this person.

    @param person_id: the person ID to look at
    @type person_id: int

    @return: returns the most frequent normalized name of a person
    @rtype: string
    '''
    pid = wash_integer_id(person_id)

    if (not pid > -1) or (not isinstance(pid, int)):
        if allow_none:
            return None
        else:
            return "'%s' doesn't look like a person ID!" % person_id
    person_id = pid

    mf_name = ""

    try:
        nn = dbapi.get_names_count_of_author(person_id)
        mf_name = sorted(nn, key=lambda k: k[1], reverse=True)[0][0]
    except IndexError:
        pass

    if mf_name:
        return mf_name
    else:
        if allow_none:
            return None
        else:
            return "This person does not seem to have a name!"


def get_papers_by_person_id(person_id=-1, rec_status=-2, ext_out=False):
    '''
    Returns all the papers written by the person

    @param person_id: identifier of the person to retrieve papers from
    @type person_id: int
    @param rec_status: minimal flag status a record must have to be displayed
    @type rec_status: int
    @param ext_out: Extended output (w/ author aff and date)
    @type ext_out: boolean

    @return: list of record info
    @rtype: list of lists of info
    '''
    if not isinstance(person_id, (int, long)):
        try:
            person_id = int(person_id)
        except (ValueError, TypeError):
            return []

    if person_id < 0:
        return []

    if not isinstance(rec_status, int):
        return []

    records = []
    db_data = dbapi.get_papers_info_of_author(person_id,
                                              rec_status,
                                              show_author_name=True,
                                              show_title=False,
                                              show_rt_status=True,
                                              show_affiliations=ext_out,
                                              show_date=ext_out,
                                              show_experiment=ext_out)
    if not ext_out:
        records = [[int(row["data"].split(",")[1]), row["data"], row["flag"],
                    row["authorname"]] for row in db_data]
    else:
        for row in db_data:
            recid = row["data"].split(",")[1]
            bibref = row["data"]
            flag = row["flag"]
            authorname = row["authorname"]
            rt_status = row['rt_status']
            authoraff = ", ".join(row['affiliation'])

            try:
                date = sorted(row['date'], key=len)[0]
            except IndexError:
                date = "Not available"

            exp = ", ".join(row['experiment'])
            # date = ""
            records.append([int(recid), bibref, flag, authorname,
                            authoraff, date, rt_status, exp])

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


def get_paper_status(bibref):
    '''
    Finds an returns the status of a bibrec to person assignment

    @param bibref: the bibref-bibrec pair that unambiguously identifies a paper
    @type bibref: string
    '''
    db_data = dbapi.get_author_and_status_of_signature(bibref)
    # data,PersonID,flag
    status = None

    try:
        status = db_data[0][2]
    except IndexError:
        status = -10

    status = wash_integer_id(status)

    return status


def get_person_redirect_link(pid):
    '''
    Returns the canonical name of a pid if found, the pid itself otherwise
    @param pid: int
    '''
    cname = dbapi.get_canonical_name_of_author(pid)
    if len(cname) > 0:
        return str(cname[0][0])
    else:
        return str(pid)


def get_person_id_from_canonical_id(canonical_id):
    '''
    Finds the person id from a canonical name (e.g. Ellis_J_R_1)

    @param canonical_id: the canonical ID
    @type canonical_id: string

    @return: result from the request or -1 on failure
    @rtype: int
    '''
    if not canonical_id or not isinstance(canonical_id, str):
        return -1

    pid = -1

    try:
        pid = dbapi.get_author_by_canonical_name(canonical_id)[0][0]
    except IndexError:
        pass

    return pid


def get_person_id_from_paper(bibref=None):
    '''
    Returns the id of the person who wrote the paper

    @param bibref: the bibref,bibrec pair that identifies the person
    @type bibref: str

    @return: the person id
    @rtype: int
    '''
    if not is_valid_bibref(bibref):
        return -1

    person_id = -1
    db_data = dbapi.get_author_and_status_of_signature(bibref)

    try:
        person_id = db_data[0][1]
    except (IndexError):
        pass

    return person_id


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

    for row in dbapi.get_persons_data([pid], "comment"):
        comments.append(row[1])

    return comments


def get_person_db_names_from_id(person_id=-1):
    '''
    Finds and returns the names associated with this person as stored in the
    meta data of the underlying data set along with the
    frequency of occurrence (i.e. the number of papers)

    @param person_id: an id to find the names for
    @type person_id: int

    @return: name and number of occurrences of the name
    @rtype: tuple of tuple
    '''
    # retrieve all rows for the person
    if (not person_id > -1) or (not isinstance(person_id, (int, long))):
        return []

    return dbapi.get_names_of_author(person_id)


def get_person_names_from_id(person_id=-1):
    '''
    Finds and returns the names associated with this person along with the
    frequency of occurrence (i.e. the number of papers)

    @param person_id: an id to find the names for
    @type person_id: int

    @return: name and number of occurrences of the name
    @rtype: tuple of tuple
    '''
    # retrieve all rows for the person
    if (not person_id > -1) or (not isinstance(person_id, (int, long))):
        return []

    return dbapi.get_names_count_of_author(person_id)


def get_person_request_ticket(pid=-1, tid=None):
    '''
    Returns the list of request tickets associated to a person.
    @param pid: person id
    @param tid: ticket id, to select if want to retrieve only a particular one
    @return: tickets [[],[]]
    '''
    if pid < 0:
        return list()

    request_tickets = list()
    r_tickets = dbapi.get_validated_request_tickets_for_author(pid, tid)

    for r_ticket in r_tickets:
        tid = None
        request_ticket = list()

        for tag, value in r_ticket.iteritems():
            if tag == 'operations':
                request_ticket += value
            elif tag == 'tid':
                tid = value
            else:
                request_ticket.append((tag, value))

        request_tickets.append([request_ticket, tid])

    return request_tickets


def get_persons_with_open_tickets_list():
    '''
    Finds all the persons with open tickets and returns pids and count of tickets
    @return: [[pid,ticket_count]]
    '''
    return dbapi.get_authors_with_open_tickets()


def get_pid_from_uid(uid):
    '''
    Return the PID associated with the uid

    @param uid: the internal ID of a user
    @type uid: int

    @return: the Person ID attached to the user or -1 if none found
    '''
    if isinstance(uid, tuple):
        uid = uid[0][0]
        assert False, (
            "AAAAARGH problem in get_pid_from_uid webapi. Got uid as a tuple instead of int.Uid = %s" %
            str(uid))
    pid = dbapi.get_author_by_uid(uid)
    if not pid:
        return -1
    return pid


def get_possible_bibrefs_from_pid_bibrec(pid, bibreclist, always_match=False, additional_names=None):
    '''
    Returns for each bibrec a list of bibrefs for which the surname matches.
    @param pid: person id to gather the names strings from
    @param bibreclist: list of bibrecs on which to search
    @param always_match: match all bibrefs no matter the name
    @param additional_names: [n1,...,nn] names to match other then the one from personid
    '''
    pid = wash_integer_id(pid)

    pid_names = dbapi.get_author_names_from_db(pid)
    if additional_names:
        pid_names += zip(additional_names)
    lists = []
    for bibrec in bibreclist:
        lists.append([bibrec, dbapi.get_matching_bibrefs_for_paper([n[0] for n in pid_names], bibrec,
                                                                   always_match)])
    return lists


def get_processed_external_recids(pid):
    '''
    Get list of records that have been processed from external identifiers

    @param pid: Person ID to look up the info for
    @type pid: int

    @return: list of record IDs
    @rtype: list of strings
    '''

    list_str = dbapi.get_processed_external_recids(pid)

    return list_str.split(";")


def get_review_needing_records(pid):
    '''
    Returns list of records associated to pid which are in need of review
    (only bibrec ma no bibref selected)
    @param pid: pid
    '''
    pid = wash_integer_id(pid)
    db_data = dbapi.get_person_papers_to_be_manually_reviewed(pid)

    return [int(row[0][1]) for row in db_data if row[0][1]]


def get_uid_from_personid(pid):
    '''
    Return the uid associated with the pid

    @param pid: the person id
    @type uid: int

    @return: the internal ID of a user or -1 if none found
    '''
    result = dbapi.get_uid_of_author(pid)

    if not result:
        return -1

    return result


def get_user_level(uid):
    '''
    Finds and returns the aid-universe-internal numeric user level

    @param uid: the user's id
    @type uid: int

    @return: A numerical representation of the maximum access level of a user
    @rtype: int
    '''
    actions = [row[1] for row in acc_find_user_role_actions({'uid': uid})]
    return max([dbapi.get_paper_access_right(acc) for acc in actions])


def search_person_ids_by_name(namequery, limit_to_recid=None, exact_name_match=False):
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
        return list()

    if query:
        escaped_query = escape(query, quote=True)
    else:
        return list()

    results = dbapi.person_search_engine_query(escaped_query)

    if not limit_to_recid:
        return results
    else:
        limit_to_persons = set([x[0] for x in dbapi.get_author_to_papers_mapping([limit_to_recid])])
        return filter(lambda x: x[0] in limit_to_persons, results)


#
# DB Data Mutators               #
#

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
    dbapi.set_person_data(pid, "comment", dbmsg)

    return dbmsg


def add_person_external_id(person_id, ext_sys, ext_id, userinfo=''):
    '''
    Adds an external id for the person
    @param person_id: person id
    @type person_id: int
    @param ext_sys: external system
    @type ext_sys: str
    @param ext_id: external id
    @type ext_id: str
    '''
    if userinfo.count('||'):
        uid = userinfo.split('||')[0]
    else:
        uid = ''

    tag = 'extid:%s' % ext_sys
    dbapi.set_person_data(person_id, tag, ext_id)
    webauthorapi.expire_all_cache_for_personid(person_id)

    log_value = '%s %s %s' % (person_id, tag, ext_id)
    dbapi.insert_user_log(
        userinfo,
        person_id,
        'data_insertion',
        'CMPUI_addexternalid',
        log_value,
        'External id manually added.',
        userid=uid)


def set_person_uid(person_id, dest_uid, userinfo=''):
    '''
    Adds an external id for the person
    @param person_id: person id
    @type person_id: int
    @param ext_sys: external system
    @type ext_sys: str
    @param ext_id: external id
    @type ext_id: str
    '''
    if userinfo.count('||'):
        uid = userinfo.split('||')[0]
    else:
        uid = ''

    dbapi.add_userid_to_author(person_id, int(dest_uid))

    log_value = '%s %s %s' % (person_id, 'uid', int(dest_uid))
    dbapi.insert_user_log(
        userinfo,
        person_id,
        'data_insertion',
        'CMPUI_set_uid',
        log_value,
        'UID manually set to person.',
        userid=uid)


def add_review_needing_record(pid, bibrec_id):
    '''
    Add record in need of review to a person
    @param pid: pid
    @param bibrec_id: bibrec
    '''
    pid = wash_integer_id(pid)
    bibrec_id = wash_integer_id(bibrec_id)
    dbapi.add_person_paper_needs_manual_review(pid, bibrec_id)


def delete_person_external_ids(person_id, existing_ext_ids, userinfo=''):
    '''
    Deletes external ids of the person
    @param person_id: person id
    @type person_id: int
    @param existing_ext_ids: external ids to delete
    @type existing_ext_ids: list
    '''
    if userinfo.count('||'):
        uid = userinfo.split('||')[0]
    else:
        uid = ''

    deleted_ids = []
    for el in existing_ext_ids:
        if el.count('||'):
            ext_sys = el.split('||')[0]
            ext_id = el.split('||')[1]
        else:
            continue
        tag = 'extid:%s' % ext_sys
        dbapi.del_person_data(tag, person_id, ext_id)
        deleted_ids.append((person_id, tag, ext_id))

    dbapi.insert_user_log(
        userinfo,
        person_id,
        'data_deletion',
        'CMPUI_deleteextid',
        '',
        'External ids manually deleted: ' + str(deleted_ids),
        userid=uid)


def del_review_needing_record(pid, bibrec_id):
    '''
    Removes a record in need of review from a person
    @param pid: personid
    @param bibrec_id: bibrec
    '''
    pid = wash_integer_id(pid)
    bibrec_id = wash_integer_id(bibrec_id)
    dbapi.del_person_papers_needs_manual_review(pid, bibrec_id)


def insert_log(userinfo, personid, action, tag, value, comment='', transactionid=0):
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
            return -1

    if not isinstance(transactionid, int):
        try:
            transactionid = int(transactionid)
        except (ValueError, TypeError):
            return -1

    if userinfo.count('||'):
        uid = userinfo.split('||')[0]
    else:
        uid = ''

    return dbapi.insert_user_log(userinfo, personid, action, tag,
                                 value, comment, transactionid, userid=uid)


def move_internal_id(person_id_of_owner, person_id_of_receiver):
    '''
    Assign an existing uid to another profile while keeping it to the old profile under the tag 'uid-old'

    @param person_id_of_owner pid: Person ID of the profile that currently has the internal id
    @type pid: int
    @param person_id_of_receiver pid: Person ID of the profile that will be assigned the internal id
    @type pid: int
    '''
    internal_id = dbapi.get_uid_of_author(person_id_of_owner)

    if not internal_id:
        return False

    dbapi.mark_internal_id_as_old(person_id_of_owner, internal_id)
    dbapi.add_author_data(person_id_of_receiver, 'uid', internal_id)
    return True


def move_external_ids(person_id_of_owner, person_id_of_receiver):
    '''
    Assign existing external ids to another profile

    @param person_id_of_owner pid: Person ID of the profile that currently has the internal id
    @type pid: int
    @param person_id_of_receiver pid: Person ID of the profile that will be assigned the internal id
    @type pid: int
    '''
    pass


def set_processed_external_recids(pid, recid_list):
    '''
    Set list of records that have been processed from external identifiers

    @param pid: Person ID to set the info for
    @type pid: int
    @param recid_list: list of recids
    @type recid_list: list of int
    '''
    if isinstance(recid_list, list):
        recid_list_str = ";".join(recid_list)

    dbapi.set_processed_external_recids(pid, recid_list_str)


def swap_person_canonical_name(person_id, desired_cname, userinfo=''):
    '''
    Swaps the canonical names of person_id and the person who withholds the desired canonical name.
    @param person_id: int
    @param desired_cname: string
    '''
    personid_with_desired_cname = get_person_id_from_canonical_id(desired_cname)
    if personid_with_desired_cname == person_id:
        return

    if userinfo.count('||'):
        uid = userinfo.split('||')[0]
    else:
        uid = ''

    current_cname = get_canonical_id_from_person_id(person_id)
    create_log_personid_with_desired_cname = False

    # nobody withholds the desired canonical name
    if personid_with_desired_cname == -1:
        dbapi.modify_canonical_name_of_authors([(person_id, desired_cname)])
    # person_id doesn't own a canonical name
    elif not isinstance(current_cname, str):
        dbapi.modify_canonical_name_of_authors([(person_id, desired_cname)])
        dbapi.update_canonical_names_of_authors([personid_with_desired_cname], overwrite=True)
        create_log_personid_with_desired_cname = True
    # both person_id and personid_with_desired_cname own a canonical name
    else:
        dbapi.modify_canonical_name_of_authors(
            [(person_id, desired_cname), (personid_with_desired_cname, current_cname)])
        create_log_personid_with_desired_cname = True

    dbapi.insert_user_log(
        userinfo,
        person_id,
        'data_update',
        'CMPUI_changecanonicalname',
        '',
        'Canonical name manually updated.',
        userid=uid)
    if create_log_personid_with_desired_cname:
        dbapi.insert_user_log(
            userinfo,
            personid_with_desired_cname,
            'data_update',
            'CMPUI_changecanonicalname',
            '',
            'Canonical name manually updated.',
            userid=uid)


def update_person_canonical_name(person_id, canonical_name, userinfo=''):
    '''
    Updates a person's canonical name
    @param person_id: person id
    @param canonical_name: string
    '''
    if userinfo.count('||'):
        uid = userinfo.split('||')[0]
    else:
        uid = ''
    dbapi.update_canonical_names_of_authors([person_id], overwrite=True, suggested=canonical_name)
    dbapi.insert_user_log(
        userinfo,
        person_id,
        'data_update',
        'CMPUI_changecanonicalname',
        '',
        'Canonical name manually updated.',
        userid=uid)

#
# NOT TAGGED YET                 #
#


def wash_integer_id(param_id):
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


def is_valid_bibref(bibref):
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


def is_valid_canonical_id(cid):
    '''
    Checks if presented canonical ID is valid in structure
    Must be of structure: ([Initial|Name]\.)*Lastname\.Number
    Example of valid cid: J.Ellis.1

    @param cid: The canonical ID to check
    @type cid: string

    @return: Is it valid?
    @rtype: boolean
    '''
    if not cid.count("."):
        return False

    xcheck = -1
    sp = cid.split(".")

    if not (len(sp) > 1 and sp[-1]):
        return False

    try:
        xcheck = int(sp[-1])
    except (ValueError, TypeError, IndexError):
        return False

    if xcheck and xcheck > -1:
        return True
    else:
        return False


def author_has_papers(pid):
    '''
    Checks if the given author identifier has papers.

    @param pid: author identifier
    @type pid: int

    @return: author has papers
    @rtype: bool
    '''
    try:
        pid = int(pid)
    except ValueError:
        return False

    papers = dbapi.get_papers_of_author(pid)
    if papers:
        return True

    return False


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

    return dbapi.user_can_modify_data_of_author(uid, pid)


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

    return dbapi.user_can_modify_paper(uid, paper)


def person_bibref_is_touched_old(pid, bibref):
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

    return dbapi.paper_affirmed_from_user_input(pid, bibref)

# def is_logged_in_through_arxiv(req):
#    '''
#    Checks if the user is logged in through the arXiv.
#
#    @param req: Apache request object
#    @type req: Apache request object
#    '''
#    session = get_session(req)
# THOMAS: ask samK about this variables: probably it would be better to rename them in the session as arxiv_sso_blabla
# THOMAS: ask samK if this is correct, what other way there is to discover is we are SSOed through arxiv?
# user_info = collect_user_info(req)
# isGuestUser(req)
# TO DO THIS SHOULD BE CHANGED
#    if 'user_info' in session.keys() and 'email' in session['user_info'].keys() and session['user_info']['email']:
#        return True
#    return False
#
# def is_logged_in_through_orcid(req):
#    '''
#    Checks if the user is logged in through the orcid.
#
#    @param req: Apache request object
#    @type req: Apache request object
#    '''
#    session_bareinit(req)
#    session = get_session(req)
#    pinfo = session['personinfo']
#
#    if 'orcid' in pinfo and pinfo['orcid']['id'] and pinfo['orcid']['access_token']:
#        return True
#
#    return False


def get_user_role(req):
    '''
    Determines whether a user is guest, user or admin
    '''
    minrole = 'guest'
    role = 'guest'

    if not req:
        return minrole

    uid = getUid(req)

    if not isinstance(uid, int):
        return minrole

    admin_role_id = acc_get_role_id(bconfig.CLAIMPAPER_ADMIN_ROLE)
    user_role_id = acc_get_role_id(bconfig.CLAIMPAPER_USER_ROLE)

    user_roles = acc_get_user_roles(uid)

    if admin_role_id in user_roles:
        role = 'admin'
    elif user_role_id in user_roles:
        role = 'user'

    if role == 'guest' and is_external_user(uid):
        role = 'user'

    return role


def display_name_from_hepnames(record):
    display_name = (record_get_field_value(record, '880', '', '', 'a') or
                    record_get_field_value(record, '100', '', '', 'q') or
                    record_get_field_value(record, '100', '', '', 'a'))

    return display_name


def main_hepnames_email(record):
    email = (record_get_field_values(record, '371', '', '', 'm',
                                     filter_subfield_code='z',
                                     filter_subfield_value='Current|current|CURRENT',
                                     filter_subfield_mode='r') or
             record_get_field_value(record, '371', '', '', 'm'))

    return email


def emails_from_hepnames(record):
    return record_get_field_values(record, '371', '', '', 'm')


def map_subfields(sub_fields, mapping):
    output = {}
    for code, value in sub_fields:
        if code in mapping:
            output[mapping[code]] = value

    return output


def institution_history(record):

    def extract_institution(sub_fields):
        mapping = {
            'a': 'name',
            'r': 'rank',
            's': 'start',
            't': 'end'
        }
        institution = map_subfields(sub_fields, mapping)
        if 'start' not in institution:
            institution['start'] = ''
        if 'name' not in institution:
            institution = None

        return institution or None

    if (not record_has_field(record, '371')):
        return None

    field_instances = record_get_field_instances(record, '371', '', '')
    institutions = [extract_institution(x[0]) for x in field_instances if extract_institution(x[0]) is not None]

    institutions.sort(key=lambda x: x['start'])

    return institutions


class HepNamesIdentifierError(Exception):

    def __init__(self, msg, value=None):
        self.msg = msg
        self.value = value

    def __str__(self):
        error_str = self.msg

        if self.value:
            error_str = '%s - %s' % (self.msg, repr(self.value))

        return error_str


def hepnames_ids(record):

    def extract_identifier(sub_fields):
        mapping = {
            '9': 'type',
            'a': 'value'
        }
        return map_subfields(sub_fields, mapping) or None

    field_instances = record_get_field_instances(record, '035', '', '')
    record_id = record_get_field_value(record, '001', '', '', '')
    ids = [extract_identifier(x[0]) for x in field_instances if extract_identifier(x[0]) is not None]

    for identifier in ids:
        identifier.update({'hepnames_recid': record_id})

    return ids


def author_profile_from_hepnames(identifiers):
    try:
        test = lambda item: item['type'] == "BAI"
        bai = filter(test, identifiers)
        return bai.pop()['value']
    except (IndexError, KeyError):
        return None


def identifier_permitted_for_display(identifier):
    try:
        id_type_lower = identifier['type'].lower()
    except KeyError:
        raise HepNamesIdentifierError("Malformed, missing key: type", identifier)

    return id_type_lower in PROFILE_IDENTIFIER_WHITELIST


def link_identifier(identifier):
    id_type = identifier['type'].lower()
    value = identifier['value']
    if id_type in PROFILE_IDENTIFIER_URL_MAPPING:
        return PROFILE_IDENTIFIER_URL_MAPPING[id_type].format(value)
    else:
        return None

def identifier_priority_of(identifier_type):
    '''
    Retrieves priority of identifier based on identifier type.

    Default is 0 if not set which is the highest priority.
    '''
    id_type_lower = identifier_type.lower()
    try:
        return PROFILE_IDENTIFIER_WHITELIST[id_type_lower]
    except KeyError:
        return 0

def identifier_context_for(identifier):
    '''
    Creates a rendering context for a single ID from a HepNames record.

    Input identifier must contain a `type` and `value` key.
    '''
    try:
        id_type = identifier['type']
        id_value = identifier['value']
    except KeyError, e:
        raise HepNamesIdentifierError("Malformed or missing keys", identifier)

    id_context = {
        "priority": identifier_priority_of(id_type),
        "label": id_type,
        "type": id_type.lower(),
        "value":id_value
    }

    link = link_identifier(identifier)
    if link:
        id_context['link'] = link

    return id_context


def permitted_identifier_context_for(identifier):
    if identifier_permitted_for_display(identifier):
        return identifier_context_for(identifier)
    else:
        return None


def context_for_identifiers(identifiers):
    if any(PROFILE_IDENTIFIER_WHITELIST):
        identifier_context = permitted_identifier_context_for
    else:
        identifier_context = identifier_context_for

    identifiers_with_context = []
    if identifiers:
        for identifier in identifiers:
            try:
                context = identifier_context(identifier)
                if context:
                    identifiers_with_context.append(context)
            except HepNamesIdentifierError:
                pass # log/email bad identifiers

    return identifiers_with_context


def hepnames_context(record):
    '''
    Generates template context of a HepNames record.
    '''
    identifiers = hepnames_ids(record)
    context = {
        'record_id': record_get_field_value(record, '001', '', '', ''),
        'display_name': display_name_from_hepnames(record),
        'urls': record_get_field_values(record, '856', '4', '', 'u'),
        'fields': record_get_field_values(record, '650', '1', '7', 'a'),
        'experiments': record_get_field_values(record, '693', '', '', 'e'),
        'identifiers': context_for_identifiers(identifiers),
        'author_profile': author_profile_from_hepnames(identifiers),
        'emails': emails_from_hepnames(record),
        'institution_history': institution_history(record)

    }

    return context


def get_hepnames(person_id, bibauthorid_data=None):
    '''
    Returns hepnames data.
    @param bibauthorid_data: dict with 'is_baid':bool, 'cid':canonicalID, 'pid':personid
    @return: [data, bool]
    '''
    def get_bibauthorid_data(person_id):
        bibauthorid_data = {"is_baid": True, "pid": person_id, "cid": person_id}

        cname = get_person_redirect_link(person_id)

        if is_valid_canonical_id(cname):
            bibauthorid_data['cid'] = cname

        return bibauthorid_data

    if bibauthorid_data is None:
        bibauthorid_data = get_bibauthorid_data(person_id)

    searchid = '035:"%s"' % bibauthorid_data['cid']
    hepRecord = perform_request_search(rg=0, cc='HepNames', p=' %s ' % searchid)[:CFG_WEBAUTHORPROFILE_MAX_HEP_CHOICES]

    hepnames_data = {}

    hepnames_data['cid'] = bibauthorid_data['cid']
    hepnames_data['pid'] = person_id

    if not hepRecord or len(hepRecord) > 1:
        # present choice dialog with alternatives?
        dbnames = [name for name, count in dbapi.get_names_of_author(person_id)]
        query = ' or '.join(['author:"%s"' % str(n) for n in dbnames])
        additional_records = perform_request_search(rg=0, cc='HepNames', p=query)[:CFG_WEBAUTHORPROFILE_MAX_HEP_CHOICES]
        hepRecord += additional_records
        hepnames_data['have_hep'] = False
        hepnames_data['choice'] = bool(hepRecord)
        # limit possible choiches!
        hepnames_data['choice_list'] = [hepnames_context(get_record(x)) for x in hepRecord]
        hepnames_data['bd'] = bibauthorid_data
    else:
        # show the heprecord we just found.
        hepnames_data['have_hep'] = True
        hepnames_data['choice'] = False
        hepnames_data['record'] = hepnames_context(get_record(hepRecord[0]))
        hepnames_data['bd'] = bibauthorid_data

    return hepnames_data


def _update_ulevel(req, pinfo):
    if 'ulevel' not in pinfo:
        uid = getUid(req)
        ulevel = get_user_role(req)

        if isUserSuperAdmin({'uid': uid}):
            ulevel = 'admin'

        pinfo['ulevel'] = ulevel


def _update_uid(req, pinfo):
    if 'uid' not in pinfo:
        pinfo['uid'] = int(getUid(req))


def _update_pid(req, pinfo):
    if 'pid' not in pinfo:
        pinfo['pid'] = int(get_pid_from_uid(getUid(req)))


def _initialize_should_check_to_autoclaim(pinfo):
    if 'should_check_to_autoclaim' not in pinfo:
        pinfo['should_check_to_autoclaim'] = False


def _initialize_login_info_message(pinfo):
    if 'login_info_message' not in pinfo:
        pinfo["login_info_message"] = None


def _initialize_merge_info_message(pinfo):
    if 'merge_info_message' not in pinfo:
        pinfo["merge_info_message"] = None


def _initialize_claimpaper_admin_last_viewed_pid(pinfo):
    if "claimpaper_admin_last_viewed_pid" not in pinfo:
        pinfo["claimpaper_admin_last_viewed_pid"] = -2


def _initialize_ln(pinfo):
    if 'ln' not in pinfo:
        pinfo["ln"] = 'en'


def _initialize_merge_primary_profile(pinfo):
    if 'merge_primary_profile' not in pinfo:
        pinfo["merge_primary_profile"] = None


def _initialize_merge_profiles(pinfo):
    if 'merge_profiles' not in pinfo:
        pinfo["merge_profiles"] = list()


def _initialize_orcid(pinfo):
    if 'orcid' not in pinfo:
        pinfo['orcid'] = {'imported_pubs': list(), 'import_pubs': False, 'has_orcid_id': False}


def _initialize_arxiv_status(pinfo):
    if 'arxiv_status' not in pinfo:
        pinfo['arxiv_status'] = False


def _initialize_autoclaim(pinfo):
    if not 'autoclaim' in pinfo:
        pinfo['autoclaim'] = dict()
        pinfo['autoclaim']['ticket'] = list()
        pinfo['autoclaim']['external_pubs_association'] = dict()
        pinfo['autoclaim']['res'] = None


def _initialize_marked_visit(pinfo):
    if 'marked_visit' not in pinfo:
        pinfo['marked_visit'] = None


def _initialize_visit_diary(pinfo):
    if 'visit_diary' not in pinfo:
        pinfo['visit_diary'] = defaultdict(list)


def _initialize_diary_size_per_category(pinfo):
    if 'diary_size_per_category' not in pinfo:
        pinfo['diary_size_per_category'] = 5


def _initialize_most_compatible_person(pinfo):
    if 'most_compatible_person' not in pinfo:
        pinfo['most_compatible_person'] = None


def _initialize_profile_suggestion_info(pinfo):
    if 'profile_suggestion_info' not in pinfo:
        pinfo["profile_suggestion_info"] = None


def _initialize_ticket(pinfo):
    if 'ticket' not in pinfo:
        pinfo["ticket"] = list()


def _initialize_users_open_tickets_storage(pinfo):
    if 'users_open_tickets_storage' not in pinfo:
        pinfo["users_open_tickets_storage"] = list()


def _initialize_claim_in_process(pinfo):
    if 'claim_in_process' not in pinfo:
        pinfo['claim_in_process'] = False


def _initialize_incomplete_autoclaimed_tickets_storage(pinfo):
    if 'incomplete_autoclaimed_tickets_storage' not in pinfo:
        pinfo["incomplete_autoclaimed_tickets_storage"] = list()


def _initialize_remote_login_system(pinfo):
    if 'remote_login_system' not in pinfo:
        pinfo["remote_login_system"] = dict()
        for system in CFG_BIBAUTHORID_ENABLED_REMOTE_LOGIN_SYSTEMS:
            if system not in pinfo["remote_login_system"]:
                pinfo['remote_login_system'][system] = {'name': None, 'email': None}


def session_bareinit(req):
    '''
    Initializes session personinfo entry if none exists
    @param req: Apache Request Object
    @type req: Apache Request Object
    '''
    session = get_session(req)

    if 'personinfo' not in session:
        session['personinfo'] = dict()

    pinfo = session['personinfo']

    _update_ulevel(req, pinfo)
    _update_uid(req, pinfo)
    _update_pid(req, pinfo)
    _initialize_should_check_to_autoclaim(pinfo)
    _initialize_login_info_message(pinfo)
    _initialize_merge_info_message(pinfo)
    _initialize_claimpaper_admin_last_viewed_pid(pinfo)
    _initialize_ln(pinfo)
    _initialize_merge_primary_profile(pinfo)
    _initialize_merge_profiles(pinfo)
    _initialize_orcid(pinfo)
    _initialize_arxiv_status(pinfo)
    _initialize_autoclaim(pinfo)
    _initialize_marked_visit(pinfo)
    _initialize_visit_diary(pinfo)
    _initialize_diary_size_per_category(pinfo)
    _initialize_most_compatible_person(pinfo)
    _initialize_profile_suggestion_info(pinfo)
    _initialize_ticket(pinfo)
    _initialize_users_open_tickets_storage(pinfo)
    _initialize_claim_in_process(pinfo)
    _initialize_incomplete_autoclaimed_tickets_storage(pinfo)
    _initialize_remote_login_system(pinfo)

    session.dirty = True

# all teh get_info methods should standardize the content:


def get_arxiv_info(req, uinfo):
    session_bareinit(req)
    session = get_session(req)
    arXiv_info = dict()

    try:
        name = uinfo['external_firstname']
    except KeyError:
        name = ''
    try:
        surname = uinfo['external_familyname']
    except KeyError:
        surname = ''

    if surname:
        session['personinfo']['remote_login_system']['arXiv']['name'] = nameapi.create_normalized_name(
            nameapi.split_name_parts(surname + ', ' + name))
    else:
        session['personinfo']['remote_login_system']['arXiv']['name'] = ''

    session['personinfo']['remote_login_system']['arXiv']['email'] = uinfo['email']
    arXiv_info['name'] = session['personinfo']['remote_login_system']['arXiv']['name']
    arXiv_info['email'] = uinfo['email']
    session.dirty = True

    return arXiv_info
    # {the dictionary we define in _webinterface}

# all teh get_info methods should standardize the content:


def get_orcid_info(req, uinfo):
    return dict()
    # {the dictionary we define in _webinterface}


def get_remote_login_systems_info(req, remote_logged_in_systems):
    '''
    For every remote_login_system get all of their info but for records and store them into a session dictionary

    @param req: Apache request object
    @type req: Apache request object

    @param remote_logged_in_systems: contains all remote_logged_in_systems tha the user is logged in through
    @type remote_logged_in_systems: dict
    '''
    session_bareinit(req)
    user_remote_logged_in_systems_info = dict()

    uinfo = collect_user_info(req)

    for system in remote_logged_in_systems:
        user_remote_logged_in_systems_info[system] = REMOTE_LOGIN_SYSTEMS_FUNCTIONS[system](req, uinfo)

    return user_remote_logged_in_systems_info


def get_ids_from_arxiv(req):
    '''
    Collects the external ids that the user has in arXiv.

    @param req: Apache request object
    @type req: Apache request object

    @return: external ids
    @rtype: list
    '''
    uinfo = collect_user_info(req)
    current_external_ids = []

    if 'external_arxivids' in uinfo.keys() and uinfo['external_arxivids']:
        current_external_ids = uinfo['external_arxivids'].split(';')

    return current_external_ids


def get_ids_from_orcid(req):
    '''
    Collects the external ids that the user has in orcid.

    @param req: Apache request object
    @type req: Apache request object

    @return: external ids
    @rtype: list
    '''
    session_bareinit(req)
    session = get_session(req)
    pinfo = session['personinfo']

    dois = list()
    if 'imported_pubs' in pinfo['orcid']:
        for doi in pinfo['orcid']['imported_pubs']:
            dois.append(doi)

    return dois


def get_external_ids_type(external_id):
    pass


def get_external_ids_to_recids_association(req, external_ids):
    '''
    Associates the external ids of remote login systems to inspire recids

    @param req: Apache request object
    @type req: Apache request object

    @param external_ids: external ids
    @type external_ids: list

    @return: recids
    @rtype: list
    '''
    session = get_session(req)
    pinfo = session['personinfo']

    recids_from_external_system = []
    # stored so far association in the session
    cached_ids_association = pinfo['autoclaim']['external_pubs_association']

    for external_id in external_ids:
        id_type = is_arxiv_id_or_doi(external_id)
        if (id_type, external_id) in cached_ids_association:
            recid = cached_ids_association[(id_type, external_id)]
            recids_from_external_system.append(recid)
        else:
            # recid_list =
            # perform_request_search(p=bconfig.CFG_BIBAUTHORID_REMOTE_LOGIN_SYSTEMS_IDENTIFIERS['arXiv']
            # + str(arxivid), of='id', rg=0)
            recid_list = perform_request_search(
                p=external_id,
                f=bconfig.CFG_BIBAUTHORID_REMOTE_LOGIN_SYSTEMS_IDENTIFIERS[id_type],
                m1='e',
                cc='HEP')
            if len(recid_list) == 1:
                recid = recid_list[0]
                recids_from_external_system.append(recid)
                cached_ids_association[(id_type, external_id)] = recid
    pinfo['autoclaim']['external_pubs_association'] = cached_ids_association
    session.dirty = True
    return recids_from_external_system


def get_remote_login_systems_recids(req, remote_logged_in_systems):
    '''
    Collects the equivalent inspire id of the remote login system's id for every system that the user is logged in through.

    @param req: Apache request object
    @type req: Apache request object

    @param remote_logged_in_systems: the remote logged in systems
    @type remote_logged_in_systems: list

    @return: recids
    @rtype: list
    '''
    session_bareinit(req)
    remote_login_systems_recids = []

    for system in remote_logged_in_systems:
        # collect system's external ids
        external_ids = REMOTE_LOGIN_SYSTEMS_GET_RECIDS_FUNCTIONS[system](req)
        # associate the external ids to recids
        system_recids = get_external_ids_to_recids_association(req, external_ids)
        remote_login_systems_recids += system_recids

    # mocking
    # remote_login_systems_recids = [14, 18, 8, 11]
    return list(set(remote_login_systems_recids))


def get_cached_id_association(req):
    '''
    get external ids to recid association saved in the session so far

    @param req: Apache request object
    @type req: Apache request object

    @return: the associaton in the following form: {(system1, external_id1):recid1, (system1, external_id2):recid2, (system2, external_id3):recid3...}
    @rtype: dict
    '''
    session_bareinit(req)
    session = get_session(req)
    pinfo = session['personinfo']

    return pinfo['autoclaim']['external_pubs_association']


def get_user_pid(uid):
    '''
    find user's pid by his uid

    @param uid: the user ID to check permissions for
    @type uid: int

    @return: user's person id or -1 if has none
    @rtype: int
    '''
    pid = dbapi.get_author_by_uid(uid)

    if not pid:
        return -1

    return pid


def merge_is_allowed(primary_pid, pids_to_merge, is_admin):
    '''
    Check if merging is allowed by finding the number of profiles that are owned by user. Merging can be perform
    only if at most one profile is connected to a user. Only admins can merge profile when 2 or more of them have claimed papers

    @param profiles: all the profiles that are going to be merged including the primary profile
    @type list

    @return: returs if merge is allowed
    @rtype: boolean
    '''
    try:
        primary_orcid = dbapi.get_orcid_id_of_author(primary_pid)[0][0]
    except IndexError:
        primary_orcid = None

    for pid in pids_to_merge:
        has_uid = bool(dbapi.get_uid_of_author(pid))
        if has_uid:
            return False, pid

        if primary_orcid:
            try:
                orcid = dbapi.get_orcid_id_of_author(pid)[0][0]
            except IndexError:
                orcid = None

            if orcid and primary_orcid != orcid:
                return False, pid

        if not is_admin:
            has_claimed_papers = bool(dbapi.get_claimed_papers_of_author(pid))
            if has_claimed_papers:
                return False, pid

    return True, None


# def open_ticket_for_papers_of_merged_profiles(req, primary_profile, profiles):
#    '''
#    instead of actually merging the papers it opens a ticket for them to be merged
#    '''
#    records = dbapi.defaultdict(list)
#
#    profiles.append(primary_profile)
#    for pid in profiles:
#        papers = get_papers_by_person_id(pid)
#        if papers:
#            for rec_info in papers:
#                records[rec_info[0]] += [rec_info[1]]
#
#    recs_to_merge = []
#    for recid in records.keys():
# if more than one with the same recid we append only the recid and we let the user to solve tha problem in ticket_review
#        if len(records[recid]) > 1:
#            recs_to_merge.append(recid)
#        else:
#            recs_to_merge.append(records[recid][0])
#
#    add_tickets(req, primary_profile, recs_to_merge, 'assign')

def get_papers_of_merged_profiles(primary_profile, profiles):
    '''
    Get the papers of the merged profiles that can be merged

    @param primary_profile: the Person id of the primary profile
    @type primary_profile: int

    @param profiles: a list of person ids
    @type profiles: list

    @return: bibrecrefs
    @rtype: list
    '''
    records = dict()
    # firstly the papers of the primary profile should be added as they should
    # be preffered from similar papers of other profiles with the same level of claim

    for pid in [primary_profile] + profiles:
        papers = get_papers_by_person_id(pid)
        for paper in papers:
            # if paper is rejected skip
            if paper[2] == -2:
                continue
            # if there is already a paper with the same record
            # and the new one is claimed while the existing one is not
            # keep only the claimed one
            if not paper[0] in records:
                records[paper[0]] = paper
            elif records[paper[0]] and records[paper[0]][2] == 0 and paper[2] == 2:
                records[paper[0]] = paper

    return [records[recid] for recid in records.keys()]


def get_uid_for_merged_profiles(persons_data):
    '''
    Get the uid of the merged profiles. It should be max 1

    @param persons_data: data of the profiles
    @type persons_data: dict

    @return: uid tuple
    @rtype: tuple
    '''
    for pid in persons_data.keys():
        for data in persons_data[pid]:
            if data[-1] == 'uid':
                return data
    return None


def get_data_union_for_merged_profiles(persons_data, new_profile_bibrecrefs):
    '''
    Get the union of all the data that exist in the given profiles but for the papers, the uid, the canonical ids and rt repeal tickets

    @param persons_data: data of the profiles
    @type persons_data: dict

    @param new_profile_bibrecrefs: the bibrecrefs of the new profile
    @type new_profile_bibrecrefs: list

    @return: union of persons' data
    @rtype: list
    '''
    new_profile_data = list()
    # rt_new_counter will deal with the enumeration of rt_ticket in the merged profile
    rt_new_counter = 1
    rt_old_counter = -1

    for pid in persons_data.keys():
        for data in persons_data[pid]:
            if data[-1].startswith("rt_repeal") and not data[0] in new_profile_bibrecrefs:
                continue
            elif data[-1] == 'uid':
                continue
            elif data[-1] == 'canonical_name':
                continue
            elif data[-1].startswith("rt_"):
                if rt_old_counter != data[1]:
                    rt_old_counter = data[1]
                    rt_new_counter += 1
                data = (data[0], rt_new_counter, data[2], data[3], data[4])
            new_profile_data.append(data)
    return list(set(new_profile_data))


def merge_profiles(primary_pid, pids_to_merge):

    def merge_papers():
        primary_recs = [rec[0] for rec in dbapi.get_papers_of_author(primary_pid)]
        for pid in pids_to_merge:
            papers_data = list(dbapi.get_all_paper_data_of_author(pid))
            for paper_data in list(papers_data):
                rec = paper_data[3]
                if rec in primary_recs:
                    papers_data.remove(paper_data)
            dbapi.transfer_papers_to_author(papers_data, primary_pid)

    def merge_data():
        primary_request_tickets = dbapi.get_request_tickets_for_author(primary_pid)

        for pid in pids_to_merge:
            author_data = list(dbapi.get_all_author_data_of_author(pid))
            for data in list(author_data):
                tag = data[1]
                if tag in ['canonical_name', 'arxiv_papers']:
                    author_data.remove(data)
                elif tag in ['request_tickets']:
                    author_data.remove(data)
                    request_tickets = dbapi.get_request_tickets_for_author(pid)
                    dbapi.remove_request_ticket_for_author(pid)
                    primary_request_tickets += request_tickets

            dbapi.transfer_data_to_author(author_data, primary_pid)

        dbapi.remove_request_ticket_for_author(primary_pid)
        for request_ticket in primary_request_tickets:
            try:
                del request_ticket['tid']
            except KeyError:
                pass
            dbapi.update_request_ticket_for_author(primary_pid, request_ticket)

    merge_papers()
    merge_data()

    dbapi.remove_empty_authors()


def auto_claim_papers(req, pid, recids):
    '''
    finding the unclaimed recids and add them in the ticket

    @param req: Apache request object
    @type req: Apache request object

    @param pid: the Person id
    @type pid: int

    @param recids: the records that need to be autoclaimed
    @type recids: list
    '''

    session_bareinit(req)

    # retrieve users existing papers
    pid_bibrecs = set([i[0] for i in dbapi.get_all_personids_recs(pid, claimed_only=True)])
    # retrieve the papers that need to be imported
    missing_bibrecs = list(set(recids) - pid_bibrecs)

    # store any users open ticket elsewhere until we have processed the autoclaimed tickets
    store_users_open_tickets(req)

    # add autoclaimed tickets to the session
    add_tickets(req, pid, missing_bibrecs, 'assign')


def get_name_variants_list_from_remote_systems_names(remote_login_systems_info):
    '''
    return the names that a user has in the external systems

    @param remote_logged_in_systems: contains all remote_logged_in_systems tha the user is logged in through
    @type remote_logged_in_systems: dict

    @return: name variants
    @rtype: list
    '''
    name_variants = []

    for system in remote_login_systems_info.keys():
        try:
            name = remote_login_systems_info[system]['name']
            name_variants.append(name)
        except KeyError:
            pass

    return list(set(name_variants))


def match_profile(req, recids, remote_login_systems_info):
    '''
    Find if a profile in inspire matches to the profile that the user has in arXiv
    (judging from the papers the name etc)

    @param req: Apache request object
    @type req: Apache request object

    @param recids: arXiv record ids
    @type recids: list

    @param remote_logged_in_systems: contains all remote_logged_in_systems tha the user is logged in through
    @type remote_logged_in_systems: dict

    @return: person id of the most compatible person
    @rtype: int
    '''
    session_bareinit(req)
    session = get_session(req)
    pinfo = session['personinfo']
    most_compatible_person = pinfo['most_compatible_person']

    if most_compatible_person is not None:
        return most_compatible_person

    name_variants = get_name_variants_list_from_remote_systems_names(remote_login_systems_info)
    most_compatible_person = dbapi.find_most_compatible_person(recids, name_variants)
    pinfo['most_compatible_person'] = most_compatible_person
    return most_compatible_person


def get_profile_suggestion_info(req, pid, recids_in_arXiv):
    '''
    get info on the profile that we are suggesting to the user coming from an external system to login
    @param req: Apache request object
    @type req: Apache request object


    @param pid: the profile's id
    @type pid: int

    @param recids_in_arXiv: recids from arxiv
    @type recids_in_arXiv: list

    @return: pid, if the claim was succesfull
    @rtype: dict
    '''
    session_bareinit(req)
    session = get_session(req)
    pinfo = session['personinfo']
    profile_suggestion_info = pinfo['profile_suggestion_info']

    if profile_suggestion_info is not None and pid == profile_suggestion_info['pid']:
        return profile_suggestion_info

    profile_suggestion_info = dict()
    profile_suggestion_info['canonical_id'] = dbapi.get_canonical_name_of_author(pid)
    name_variants = [element[0] for element in get_person_names_from_id(pid)]
    name = most_relevant_name(name_variants)
    profile_suggestion_info['name_string'] = "[No name available]  "

    profile_suggestion_info['num_of_arXiv_papers'] = len(recids_in_arXiv)
    # find the number of papers that are both in recids and probable person's papers
    profile_suggestion_info['num_of_recids_intersection'] = len(
        set(recids_in_arXiv) & set([bibrecref[0] for bibrecref in get_papers_by_person_id(pid)]))
    if name is not None:
        profile_suggestion_info['name_string'] = name

    if len(profile_suggestion_info['canonical_id']) > 0:
        profile_suggestion_info['canonical_name_string'] = "(" + profile_suggestion_info['canonical_id'][0][0] + ")"
        profile_suggestion_info['canonical_id'] = str(profile_suggestion_info['canonical_id'][0][0])
    else:
        profile_suggestion_info['canonical_name_string'] = "(" + str(pid) + ")"
        profile_suggestion_info['canonical_id'] = str(pid)

    profile_suggestion_info['pid'] = pid
    pinfo['profile_suggestion_info'] = profile_suggestion_info
    return profile_suggestion_info


def claim_profile(uid, pid):
    '''
    Try to claim the profile pid for the user uid

    @param uid: the user ID
    @type uid: int

    @param pid: the profile's id
    @type pid: int

    @return: pid, if the claim was succesfull
    @rtype: int, boolean
    '''
    return dbapi.assign_person_to_uid(uid, pid)


def external_user_can_perform_action(uid):
    '''
    Check for SSO user and if external claims will affect the
    decision wether or not the user may use the Invenio claiming platform

    @param uid: the user ID to check permissions for
    @type uid: int

    @return: is user allowed to perform actions?
    @rtype: boolean
    '''
    # If no EXTERNAL_CLAIMED_RECORDS_KEY we bypass this check
    if not bconfig.EXTERNAL_CLAIMED_RECORDS_KEY:
        return True

    uinfo = collect_user_info(uid)
    keys = []
    for k in bconfig.EXTERNAL_CLAIMED_RECORDS_KEY:
        if k in uinfo:
            keys.append(k)

    full_key = False
    for k in keys:
        if uinfo[k]:
            full_key = True
            break

    return full_key


def is_external_user(uid):
    '''
    Check for SSO user and if external claims will affect the
    decision wether or not the user may use the Invenio claiming platform

    @param uid: the user ID to check permissions for
    @type uid: int

    @return: is user allowed to perform actions?
    @rtype: boolean
    '''
    # If no EXTERNAL_CLAIMED_RECORDS_KEY we bypass this check
    if not bconfig.EXTERNAL_CLAIMED_RECORDS_KEY:
        return False

    uinfo = collect_user_info(uid)
    keys = []
    for k in bconfig.EXTERNAL_CLAIMED_RECORDS_KEY:
        if k in uinfo:
            keys.append(k)

    full_key = False
    for k in keys:
        if uinfo[k]:
            full_key = True
            break

    return full_key


def check_transaction_permissions(uid, bibref, pid, action):
    '''
    Check if the user can perform the given action on the given pid,bibrefrec pair.
    return in: granted, denied, warning_granted, warning_denied

    @param uid: The internal ID of a user
    @type uid: int
    @param bibref: the bibref pair to check permissions for
    @type bibref: string
    @param pid: the Person ID to check on
    @type pid: int
    @param action: the action that is to be performed
    @type action: string

    @return: granted, denied, warning_granted xor warning_denied
    @rtype: string
    '''
    c_own = True
    c_override = False
    is_superadmin = isUserSuperAdmin({'uid': uid})

    access_right = _resolve_maximum_acces_rights(uid)
    bibref_status = dbapi.get_status_of_signature(bibref)
    old_flag = bibref_status[0]

    if old_flag == 2 or old_flag == -2:
        if action in ['assign']:
            new_flag = 2
        elif action in ['reject']:
            new_flag = -2
        elif action in ['reset']:
            new_flag = 0
        c_override = True

    if dbapi.get_author_by_uid(uid) != int(pid):
        c_own = False

    # if we cannot override an already touched bibref, no need to go on checking
    if c_override:
        if is_superadmin:
            return 'warning_granted'
        if access_right[1] < bibref_status[1]:
            return "denied"
    else:
        if is_superadmin:
            return 'granted'

    # let's check if invenio is allowing us the action we want to perform
    if c_own:
        action = bconfig.CLAIMPAPER_CLAIM_OWN_PAPERS
    else:
        action = bconfig.CLAIMPAPER_CLAIM_OTHERS_PAPERS
    auth = acc_authorize_action(uid, action)

    if auth[0] != 0:
        return "denied"

    # now we know if claiming for ourselfs, we can ask for external ideas
    if c_own:
        action = 'claim_own_paper'
    else:
        action = 'claim_other_paper'

    ext_permission = external_user_can_perform_action(uid)

    # if we are here invenio is allowing the thing and we are not overwriting a
    # user with higher privileges, if externals are ok we go on!
    if ext_permission:
        if not c_override:
            return "granted"
        else:
            return "warning_granted"

    return "denied"


def delete_request_ticket(pid, tid):
    '''
    Delete a request ticket associated to a person
    @param pid: pid (int)
    @param ticket: ticket id (int)
    '''
    dbapi.remove_request_ticket_for_author(pid, tid)


def delete_transaction_from_request_ticket(pid, tid, action, bibrefrec):
    '''
    Deletes a transaction from a ticket. If ticket empty, deletes it.
    @param pid: pid
    @param tid: ticket id
    @param action: action
    @param bibref: bibref
    '''
    try:
        request_ticket = dbapi.get_validated_request_tickets_for_author(pid, tid)[0]
    except IndexError:
        return

    for operation in list(request_ticket['operations']):
        op_action, op_bibrefrec = operation
        if op_action == action and op_bibrefrec == bibrefrec:
            request_ticket['operations'].remove(operation)

    if not request_ticket['operations']:
        dbapi.remove_request_ticket_for_author(pid, tid)
    else:
        dbapi.update_request_ticket_for_author(pid, request_ticket, tid)


def create_request_ticket(userinfo, ticket):
    '''
    Creates a request ticket and sends an email to RT.

    @param usernfo: dictionary of info about user
    @param ticket: dictionary ticket
    '''
    udata = list()
    mailcontent = list()
    m = mailcontent.append

    m("A user sent a change request through the web interface.")
    m("User Information:")

    for k, v in userinfo.iteritems():
        udata.append([k, v])
        if v:
            m("    %s: %s" % (k, v))

    m("\nOperations:")

    tic = dict()
    for op in ticket:
        bibrefrec = op['bibref'] + ',' + str(op['rec'])

        if not op['action'] in ['assign', 'reject', 'reset']:
            return False
        elif op['pid'] < 0:
            return False
        elif not is_valid_bibref(bibrefrec):
            return False

        # ignore reset operations
        if op['action'] == 'reset':
            continue

        cname = get_person_redirect_link(op['pid'])

        try:
            tic[(op['pid'], cname)].append((op['action'], bibrefrec))
        except KeyError:
            tic[(op['pid'], cname)] = [(op['action'], bibrefrec), ]

        preposition = 'to' if op['action'] == 'assign' else 'from'
        m("    %s %s %s %s" % (op['action'].title(), bibrefrec, preposition, cname))

    m("\nLinks to all issued Person-based requests:\n")

    for pid, cname in tic:
        data = list()
        for i in udata:
            data.append(i)
        data.append(['date', ctime()])
        data.append(['operations', tic[(pid, cname)]])

        dbapi.update_request_ticket_for_author(pid, dict(data))
        m("%s/author/claim/%s?open_claim=True#tabTickets" % (CFG_SITE_URL, cname))

    m("\nPlease remember that you have to be logged in "
      "in order to see the ticket of a person.\n")

    if ticket and tic and mailcontent:
        sender = CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL

        if bconfig.TICKET_SENDING_FROM_USER_EMAIL and userinfo['email']:
            sender = userinfo['email']

        send_email(sender,
                   CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL,
                   subject="[Author] Change Request",
                   content="\n".join(mailcontent))

    return True


def create_request_message(userinfo, subj=None):
    '''
    Creates a request message
    @param userinfo: dictionary of info about user
    @type: dict
    @param subj: the subject of the message
    @param subj: string
    '''
    mailcontent = []

    for info_type in userinfo:
        mailcontent.append(info_type + ': ')
        mailcontent.append(str(userinfo[info_type]) + '\n')

    sender = CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL

    if bconfig.TICKET_SENDING_FROM_USER_EMAIL and userinfo['email']:
        sender = userinfo['email']

    if not subj:
        subj = "[Author] Help Request"
    send_email(sender,
               CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL,
               subject=subj,
               content="\n".join(mailcontent))


def send_user_commit_notification_email(userinfo, ticket):
    '''
    Sends commit notification email to RT system
    '''
    # send eMail to RT
    mailcontent = []
    m = mailcontent.append
    m("A user committed a change through the web interface.")
    m("User Information:")

    for k, v in userinfo.iteritems():
        if v:
            m("    %s: %s" % (k, v))

    m("\nChanges:\n")

    for t in ticket:
        m(" --- <start> --- \n")
        for k, v in t.iteritems():
            m("    %s: %s \n" % (str(k), str(v)))
            if k == 'bibref':
                try:
                    br = int(v.split(',')[1])
                    m("        Title: %s\n" % search_engine.get_fieldvalues(br, "245__a"))
                except (TypeError, ValueError, IndexError):
                    pass
        m(" --- <end> --- \n")

    if ticket and mailcontent:
        sender = CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL
        send_email(sender,
                   CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL,
                   subject="[Author] NO ACTIONS NEEDED. Changes performed by SSO user.",
                   content="\n".join(mailcontent))

    return True


def user_can_view_CMP(uid):
    action = bconfig.CLAIMPAPER_VIEW_PID_UNIVERSE
    auth = acc_authorize_action(uid, action)
    if auth[0] == 0:
        return True
    else:
        return False


def _resolve_maximum_acces_rights(uid):
    '''
    returns [max_role, lcul] to use in execute_action and check_transaction_permissions.
    Defaults to ['guest',0] if user has no roles assigned.
    Always returns the maximum privilege.
    '''

    roles = {bconfig.CLAIMPAPER_ADMIN_ROLE: acc_get_role_id(bconfig.CLAIMPAPER_ADMIN_ROLE),
             bconfig.CLAIMPAPER_USER_ROLE: acc_get_role_id(bconfig.CLAIMPAPER_USER_ROLE)}
    uroles = acc_get_user_roles(uid)

    max_role = ['guest', 0]

    for r in roles:
        if roles[r] in uroles:
            rright = bconfig.CMPROLESLCUL[r]
            if rright >= max_role[1]:
                max_role = [r, rright]

    return max_role


def create_new_person(uid, uid_is_owner=False):
    '''
    Create a new person.

    @param uid: User ID to attach to the person
    @type uid: int
    @param uid_is_owner: Is the uid provided owner of the new person?
    @type uid_is_owner: bool

    @return: the resulting person ID of the new person
    @rtype: int
    '''
    pid = dbapi.create_new_author_by_uid(uid, uid_is_owner=uid_is_owner)

    return pid


def execute_action(action, pid, bibref, uid, userinfo='', comment=''):
    '''
    Executes the action, setting the last user right according to uid

    @param action: the action to perform
    @type action: string
    @param pid: the Person ID to perform the action on
    @type pid: int
    @param bibref: the bibref pair to perform the action for
    @type bibref: string
    @param uid: the internal user ID of the currently logged in user
    @type uid: int

    @return: list of a tuple: [(status, message), ] or None if something went wrong
    @rtype: [(bool, str), ]
    '''
    pid = wash_integer_id(pid)

    if not action in ['assign', 'reject', 'reset']:
        return None
    elif pid == bconfig.CREATE_NEW_PERSON:
        pid = create_new_person(uid, uid_is_owner=False)
    elif pid < 0:
        return None
    elif not is_valid_bibref(bibref):
        return None

    if userinfo.count('||'):
        uid = userinfo.split('||')[0]
    else:
        uid = ''

    user_level = _resolve_maximum_acces_rights(uid)[1]

    res = None
    if action in ['assign']:
        dbapi.insert_user_log(userinfo, pid, 'assign', 'CMPUI_ticketcommit', bibref, comment, userid=uid)
        res = dbapi.confirm_papers_to_author(pid, [bibref], user_level)
    elif action in ['reject']:
        dbapi.insert_user_log(userinfo, pid, 'reject', 'CMPUI_ticketcommit', bibref, comment, userid=uid)
        res = dbapi.reject_papers_from_author(pid, [bibref], user_level)
    elif action in ['reset']:
        dbapi.insert_user_log(userinfo, pid, 'reset', 'CMPUI_ticketcommit', bibref, comment, userid=uid)
        res = dbapi.reset_papers_of_author(pid, [bibref])

    # This is the only point which modifies a person, so this can trigger the
    # deletion of a cached page
    webauthorapi.expire_all_cache_for_personid(pid)

    return res


def sign_assertion(robotname, assertion):
    '''
    Sign an assertion for the export of IDs

    @param robotname: name of the robot. E.g. 'arxivz'
    @type robotname: string
    @param assertion: JSONized object to sign
    @type assertion: string

    @return: The signature
    @rtype: string
    '''
    robotname = ""
    secr = ""

    if not robotname:
        return ""

    robot = ExternalAuthRobot()
    keys = load_robot_keys()

    try:
        secr = keys["Robot"][robotname]
    except:
        secr = ""

    return robot.sign(secr, assertion)


def get_orcids_by_pid(pid):
    orcids = dbapi.get_orcid_id_of_author(pid)

    return tuple(str(x[0]) for x in orcids)


def add_orcid_to_pid(pid, orcid):
    if orcid in get_orcids_by_pid(pid):
        return

    dbapi.add_orcid_id_to_author(pid, orcid)
    webauthorapi.expire_all_cache_for_personid(pid)


def get_person_info_by_pid(pid):
    '''
    Collect person's info such as name variants, name and canonical_id
    by his person id
    @param uid: the person id of the user
    @type uid: int

    @return: person's info
    @rtype: dict
    '''
    person_info = dict()
    person_info['pid'] = pid
    name_variants = [x for (x, y) in get_person_db_names_from_id(pid)]
    person_info['name'] = most_relevant_name(name_variants)
    person_info['canonical_name'] = get_canonical_id_from_person_id(pid)
    return person_info

#
# Ticket Functions               #
#


def add_tickets(req, pid, bibrefs, action):
    '''
    adding the missing bibrecs in the ticket

    @param req: Apache request object
    @type req: Apache request object

    @param pid: the Person id
    @type pid: int

    @param bibrefs: the missing records that need to be autoclaimed
    @type bibrefs: list

    @param action: the action that is required to be performed on the tickets
    @type action: string
    '''
    session = get_session(req)
    pinfo = session["personinfo"]
    ticket = pinfo["ticket"]

    # the user wanted to create a new person to resolve the tickets to it
    if pid == bconfig.CREATE_NEW_PERSON:
        uid = getUid(req)
        pid = create_new_person(uid)

    tempticket = []
    for bibref in bibrefs:
        tempticket.append({'pid': pid, 'bibref': bibref, 'action': action})

    # check if ticket targets (bibref for pid) are already in ticket
    for t in tempticket:
        tempticket_is_valid_bibref = is_valid_bibref(t['bibref'])
        should_append = True
        for e in list(ticket):
            ticket_is_valid_bibref = is_valid_bibref(e['bibref'])
            # if they are the same leave ticket as it is and continue to the next tempticket
            if e['bibref'] == t['bibref'] and e['pid'] == t['pid']:
                ticket.remove(e)
                break
            # if we are comparing two different bibrefrecs with the same recids we
            # remove the current bibrefrec and we add their recid
            elif e['pid'] == t['pid'] and tempticket_is_valid_bibref and ticket_is_valid_bibref and t['bibref'].split(',')[1] == e['bibref'].split(',')[1]:
                ticket.remove(e)
                ticket.append({'pid': pid, 'bibref': t['bibref'].split(',')[1], 'action': action})
                should_append = False
                break
            elif e['pid'] == t['pid'] and is_valid_bibref(e['bibref']) and str(t['bibref']) == e['bibref'].split(',')[1]:
                should_append = False
                break
            elif e['pid'] == t['pid'] and is_valid_bibref(t['bibref']) and str(e['bibref']) == t['bibref'].split(',')[1]:
                ticket.remove(e)
                break

        if should_append:
            ticket.append(t)
    session.dirty = True

# def manage_tickets(req, autoclaim_show_review, autoclaim):
#    '''
#    managing the tickets. This involves reviewing them, try to guess the correct one if a ticket is incomplete,
#    give them to the user for a review, handle the results of that review, check if the permissions to commit a ticket are granted, commit the ticket if possible
#
#    @param req: Apache request object
#    @type req: Apache request object
#
#    @param autoclaim_show_review: shows if the user pressed the button review auto assigned in his manage profile page
#    @type autoclaim_show_review: boolean
#
#    @param bibrefs: shows if we are autoassigning papers or not
#    @type bibrefs: list
#
#    '''
#    session = get_session(req)
#    pinfo = session["personinfo"]
#    ticket = pinfo["ticket"]
#
#    page_info = dict()
# check if there is user review that needs to be handled
#    reviews_to_handle = is_ticket_review_handling_required(req)
#
#    if not reviews_to_handle:
# check if the tickets need review
#        is_required, incomplete_tickets = is_ticket_review_required(req)
#
#        if is_required:
# if review is required and we are not in the workflow that builds the autoassigned papers box of the manage profile page
# then it returns to the user for review
#            if not autoclaim or autoclaim_show_review:
#                bibrefs_auto_assigned, bibrefs_to_confirm = ticket_review(req, incomplete_tickets)
#                page_info['type'] = 'Submit Attribution'
#                page_info['title'] = 'Submit Attribution Information'
#                page_info['body_params'] = [bibrefs_auto_assigned, bibrefs_to_confirm]
#                return page_info
#            else:
# tries to guess the incomplete tickets, move the still incomplete to their storage, and user can review them by clicking the button
# of the autoassigned papers box in the manage profile page
#                guess_signature(req, incomplete_tickets)
#                failed_to_autoclaim_tickets = []
#                for t in list(ticket):
#                    if 'incomplete' in t:
#                        failed_to_autoclaim_tickets.append(t)
#                        ticket.remove(t)
#                store_incomplete_autoclaim_tickets(req, failed_to_autoclaim_tickets)
#                session.dirty = True
#    else:
#        handle_ticket_review_results(req, autoclaim_show_review)
#
#    for t in ticket:
#        if 'incomplete' in t:
#            assert False, "Wtf one ticket is incomplete " + str(pinfo)
#        if ',' not in str(t['bibref']) or  ':' not in str(t['bibref']):
#            assert False, "Wtf one ticket is invalid " + str(pinfo)
#    uid = getUid(req)
#
#    for t in ticket:
# TODO be carefull if an admin connects through arxiv
#        t['status'] = check_transaction_permissions(uid,
#                                                       t['bibref'],
#                                                       t['pid'],
#                                                       t['action'])
#    failed_to_autoclaim_tickets = []
#    if autoclaim and not autoclaim_show_review:
#        for t in ticket:
#            if 'status' not in t or t['status'] != 'granted':
#                failed_to_autoclaim_tickets.append(t)
#                ticket.remove(t)
#        store_incomplete_autoclaim_tickets(req, failed_to_autoclaim_tickets)
#
#    session.dirty = True
#
#    add_user_data_to_ticket(req)
#
#    if not can_commit_ticket(req):
#        mark_yours, mark_not_yours, mark_theirs, mark_not_theirs = confirm_valid_ticket(req)
#        page_info['type'] = 'review actions'
#        page_info['title'] = 'Please review your actions'
#        page_info['body_params'] = [mark_yours, mark_not_yours, mark_theirs, mark_not_theirs]
#        return page_info
#
#    ticket_commit(req)
#    page_info['type'] = 'dispatch end'
#    return page_info


def confirm_valid_ticket(req):
    '''
    displays the user what can/cannot finally be done
    '''
    session = get_session(req)
    pinfo = session["personinfo"]
    ticket = pinfo["ticket"]
    ticket = [row for row in ticket if not "execution_result" in row]
    upid = pinfo["upid"]

    for tt in list(ticket):
        if not 'bibref' in tt or not 'pid' in tt:
            del(ticket[tt])
            continue

        tt['authorname_rec'] = dbapi.get_bibrefrec_name_string(tt['bibref'])
        tt['person_name'] = get_most_frequent_name_from_pid(tt['pid'])

    mark_yours = []
    mark_not_yours = []

    if upid >= 0:
        mark_yours = [row for row in ticket
                      if (str(row["pid"]) == str(upid) and
                          row["action"] in ["to_other_person", "assign"])]
        mark_not_yours = [row for row in ticket
                          if (str(row["pid"]) == str(upid) and
                              row["action"] in ["reject", "reset"])]
    mark_theirs = [row for row in ticket
                   if ((not str(row["pid"]) == str(upid)) and
                       row["action"] in ["to_other_person", "assign"])]

    mark_not_theirs = [row for row in ticket
                       if ((not str(row["pid"]) == str(upid)) and
                           row["action"] in ["reject", "reset"])]

    session.dirty = True

    return mark_yours, mark_not_yours, mark_theirs, mark_not_theirs


def guess_signature(req, incomplete_tickets):
    '''
    Tries to guess a bibrecref based on a recid and names of the person. It writes the fix directly in the session

    @param req: apache request object
    @type req: apache request object

    @param incomplete_tickets: list of incomplete tickets
    @type incomplete_tickets: list
    '''
    session = get_session(req)
    pinfo = session["personinfo"]
    tickets = pinfo["ticket"]

    if 'arxiv_name' in pinfo:
        arxiv_name = [pinfo['arxiv_name']]
    else:
        arxiv_name = None

    for incomplete_ticket in incomplete_tickets:
        # convert recid from string to int
        recid = wash_integer_id(incomplete_ticket['bibref'])

        if recid < 0:
            # this doesn't look like a recid--discard!
            tickets.remove(incomplete_ticket)
        else:
            pid = incomplete_ticket['pid']
            possible_signatures_per_rec = get_possible_bibrefs_from_pid_bibrec(
                pid, [recid], additional_names=arxiv_name)

            for [rec, possible_signatures] in possible_signatures_per_rec:
                # if there is only one bibreceref candidate for the given recid
                if len(possible_signatures) == 1:
                    # fix the incomplete ticket with the retrieved bibrecref
                    for ticket in list(tickets):
                        if incomplete_ticket['bibref'] == ticket['bibref'] and incomplete_ticket['pid'] == ticket['pid']:
                            ticket['bibref'] = possible_signatures[0][0] + ',' + str(rec)
                            ticket.pop('incomplete', True)
                            break
    session.dirty = True


def ticket_review(req, needs_review):
    '''
    Tries to guess the full ticket if incomplete and when finished it shows all the tickets to the user to review them

    @param req: apache request object
    @type req: apache request object

    @param needs_review: list of incomplete tickets
    @type needs_review: list
    '''
    session = get_session(req)
    pinfo = session["personinfo"]
    tickets = pinfo["ticket"]

    if 'arxiv_name' in pinfo:
        arxiv_name = [pinfo['arxiv_name']]
    else:
        arxiv_name = None

    bibrefs_auto_assigned = {}
    bibrefs_to_confirm = {}

    guess_signature(req, needs_review)

    for ticket in list(tickets):
        pid = ticket['pid']
        person_name = get_most_frequent_name_from_pid(pid, allow_none=True)

        if not person_name:
            if arxiv_name:
                person_name = ''.join(arxiv_name)
            else:
                person_name = " "

        if 'incomplete' not in ticket:
            recid = get_bibrec_from_bibrefrec(ticket['bibref'])

            if recid == -1:
                # No bibrefs on record--discard
                tickets.remove(ticket)
                continue
            bibrefs_per_recid = get_bibrefs_from_bibrecs([recid])
            for bibref in bibrefs_per_recid[0][1]:
                if bibref[0] == ticket['bibref'].split(",")[0]:
                    most_possible_bibref = bibref
                    bibrefs_per_recid[0][1].remove(bibref)

            sorted_bibrefs = most_possible_bibref + sorted(bibrefs_per_recid[0][1], key=lambda x: x[1])
            if not pid in bibrefs_to_confirm:
                bibrefs_to_confirm[pid] = {
                    'person_name': person_name,
                    'canonical_id': "TBA",
                    'bibrecs': {recid: sorted_bibrefs}}
            else:
                bibrefs_to_confirm[pid]['bibrecs'][recid] = sorted_bibrefs
        else:
            # convert recid from string to int
            recid = wash_integer_id(ticket['bibref'])
            bibrefs_per_recid = get_bibrefs_from_bibrecs([recid])

            try:
                name = bibrefs_per_recid[0][1]
                sorted_bibrefs = sorted(name, key=lambda x: x[1])
            except IndexError:
                # No bibrefs on record--discard
                tickets.remove(ticket)
                continue

            # and add it to bibrefs_to_confirm list
            if not pid in bibrefs_to_confirm:
                bibrefs_to_confirm[pid] = {
                    'person_name': person_name,
                    'canonical_id': "TBA",
                    'bibrecs': {recid: sorted_bibrefs}}
            else:
                bibrefs_to_confirm[pid]['bibrecs'][recid] = sorted_bibrefs

        if bibrefs_to_confirm or bibrefs_auto_assigned:
            pinfo["bibref_check_required"] = True
            baa = deepcopy(bibrefs_auto_assigned)
            btc = deepcopy(bibrefs_to_confirm)

            for pid in baa:
                for rid in baa[pid]['bibrecs']:
                    baa[pid]['bibrecs'][rid] = []

            for pid in btc:
                for rid in btc[pid]['bibrecs']:
                    btc[pid]['bibrecs'][rid] = []

            pinfo["bibrefs_auto_assigned"] = baa
            pinfo["bibrefs_to_confirm"] = btc
        else:
            pinfo["bibref_check_required"] = False

    session.dirty = True
    return bibrefs_auto_assigned, bibrefs_to_confirm


def add_user_data_to_ticket(req):
    session = get_session(req)
    uid = getUid(req)
    userinfo = collect_user_info(uid)
    pinfo = session["personinfo"]
    upid = -1
    user_first_name = ""
    user_first_name_sys = False
    user_last_name = ""
    user_last_name_sys = False
    user_email = ""
    user_email_sys = False

    if ("external_firstname" in userinfo
       and userinfo["external_firstname"]):
        user_first_name = userinfo["external_firstname"]
        user_first_name_sys = True
    elif "user_first_name" in pinfo and pinfo["user_first_name"]:
        user_first_name = pinfo["user_first_name"]

    if ("external_familyname" in userinfo
       and userinfo["external_familyname"]):
        user_last_name = userinfo["external_familyname"]
        user_last_name_sys = True
    elif "user_last_name" in pinfo and pinfo["user_last_name"]:
        user_last_name = pinfo["user_last_name"]

    if ("email" in userinfo
       and not userinfo["email"] == "guest"):
        user_email = userinfo["email"]
        user_email_sys = True
    elif "user_email" in pinfo and pinfo["user_email"]:
        user_email = pinfo["user_email"]

    pinfo["user_first_name"] = user_first_name
    pinfo["user_first_name_sys"] = user_first_name_sys
    pinfo["user_last_name"] = user_last_name
    pinfo["user_last_name_sys"] = user_last_name_sys
    pinfo["user_email"] = user_email
    pinfo["user_email_sys"] = user_email_sys

    # get pid by user id
    if "upid" in pinfo and pinfo["upid"]:
        upid = pinfo["upid"]
    else:
        upid = get_pid_from_uid(uid)

        pinfo["upid"] = upid

    session.dirty = True


def can_commit_ticket(req):
    '''
    checks if the tickets can be commited

    @param req: apache request object
    @type req: apache request object


    '''
    session = get_session(req)
    pinfo = session["personinfo"]
    ticket = pinfo["ticket"]
    ticket = [row for row in ticket if not "execution_result" in row]
    skip_checkout_page = True
    skip_checkout_page2 = True

    if not (pinfo["user_first_name"] or pinfo["user_last_name"] or pinfo["user_email"]):
        skip_checkout_page = False

    if [row for row in ticket
        if row["status"] in ["denied", "warning_granted",
                             "warning_denied"]]:
        skip_checkout_page2 = False

    if (not ticket or skip_checkout_page2
        or ("checkout_confirmed" in pinfo
            and pinfo["checkout_confirmed"]
            and "checkout_faulty_fields" in pinfo
            and not pinfo["checkout_faulty_fields"]
            and skip_checkout_page)):
        return True
    return False

# def clean_ticket(req):
#    '''
#    Removes from a ticket the transactions with an execution_result flag
#    '''
#    session = get_session(req)
#    pinfo = session["personinfo"]
#    ticket = pinfo["ticket"]
#    for t in list(ticket):
#        if 'execution_result' in t:
#            ticket.remove(t)
#    session.dirty = True


def is_ticket_review_handling_required(req):
    '''
    checks if the results of ticket reviewing should be handled
    @param req: Apache request object
    @type req: Apache request object
    '''

    session = get_session(req)
    pinfo = session["personinfo"]

    # if check is needed
    if ("bibref_check_required" in pinfo and pinfo["bibref_check_required"]
       and "bibref_check_reviewed_bibrefs" in pinfo):
        return True
    return False


def handle_ticket_review_results(req, autoclaim):
    '''
    handle the results of ticket reviewing by either fixing tickets or removing them based on the review performed
    @param req: Apache request object
    @type req: Apache request object
    '''

    session = get_session(req)
    pinfo = session["personinfo"]
    ticket = pinfo["ticket"]
    # for every bibref in need of review
    for rbibreft in pinfo["bibref_check_reviewed_bibrefs"]:
        # if it's not in proper form skip it ( || delimiter is being added in bibauthorid_templates:tmpl_bibref_check function, coma delimiter
        # are being added in bibauthorid_webinterface: action function )
        # rbibreft ex: 'pid||bibrecref','8||100:4,45'
        if not rbibreft.count("||") or not rbibreft.count(","):
            continue

        # get pid and bibrecref
        rpid, rbibref = rbibreft.split("||")
        # get recid out of bibrecref
        rrecid = rbibref.split(",")[1]
        # convert string pid to int
        rpid = wash_integer_id(rpid)
        # updating ticket status with fixed bibrefs
        # and removing them from incomplete
        for ticket_update in [row for row in ticket
                              if (str(row['bibref']) == str(rrecid) and
                                  str(row['pid']) == str(rpid))]:
            ticket_update["bibref"] = rbibref

            if "incomplete" in ticket_update:
                del(ticket_update["incomplete"])
        session.dirty = True
    # tickets that could't be fixed will be removed or if they were to be autoclaimed they will be stored elsewhere
    if autoclaim:
        failed_to_autoclaim_tickets = []

        for ticket_remove in [row for row in ticket
                              if ('incomplete' in row)]:
            failed_to_autoclaim_tickets.append(ticket_remove)
            ticket.remove(ticket_remove)
        if failed_to_autoclaim_tickets:
            store_incomplete_autoclaim_tickets(req, failed_to_autoclaim_tickets)
    else:
        for ticket_remove in [row for row in ticket
                              if ('incomplete' in row)]:
            ticket.remove(ticket_remove)

    # delete also all bibrefs_auto_assigned, bibrefs_to_confirm and
    # bibref_check_reviewed_bibrefs since the have been handled
    if ("bibrefs_auto_assigned" in pinfo):
        del(pinfo["bibrefs_auto_assigned"])

    if ("bibrefs_to_confirm" in pinfo):
        del(pinfo["bibrefs_to_confirm"])

    del(pinfo["bibref_check_reviewed_bibrefs"])
    # now there is no check required
    pinfo["bibref_check_required"] = False
    session.dirty = True


def is_ticket_review_required(req):
    '''
    checks if there are transactions inside ticket in need for review
    @param req: Apache request object
    @type req: Apache request object

    @return: returns if review is required plus the list of the tickets to be reviewed
    @rtype: tuple(boolean, list)
    '''
    session = get_session(req)
    pinfo = session["personinfo"]
    ticket = pinfo["ticket"]
    needs_review = []

    # for every transaction in tickets check if there ara transaction that require review
    for transaction in ticket:
        if not is_valid_bibref(transaction['bibref']):
            transaction['incomplete'] = True
            needs_review.append(transaction)
    session.dirty = True
    if not needs_review:
        return (False, [])
    return (True, needs_review)


def restore_users_open_tickets(req):
    '''
    restores any users open ticket, that is in storage , in session as autoclaiming has finished
    @param req: Apache request object
    @type req: Apache request object
    '''
    session_bareinit(req)
    session = get_session(req)
    ticket = session['personinfo']['ticket']
    temp_storage = session['personinfo']['users_open_tickets_storage']

    for t in list(temp_storage):
        ticket.append(t)
        temp_storage.remove(t)
    temp_storage = []


def store_users_open_tickets(req):
    '''
    stores any users open ticket elsewhere until we have processed the autoclaimed tickets
    @param req: Apache request object
    @type req: Apache request object
    '''
    session_bareinit(req)
    session = get_session(req)
    ticket = session['personinfo']['ticket']
    temp_storage = session['personinfo']['users_open_tickets_storage']
    for t in list(ticket):
        temp_storage.append(t)
        ticket.remove(t)


def store_incomplete_autoclaim_tickets(req, failed_to_autoclaim_tickets):
    '''
    stores incomplete autoclaim's tickets elsewhere waiting for user interference in order not to mess with new tickets
    @param req: Apache request object
    @type req: Apache request object
    '''
    session_bareinit(req)
    session = get_session(req)
    temp_storage = session['personinfo']['incomplete_autoclaimed_tickets_storage']

    for incomplete_ticket in failed_to_autoclaim_tickets:
        if incomplete_ticket not in temp_storage:
            temp_storage.append(incomplete_ticket)


def restore_incomplete_autoclaim_tickets(req):
    '''
    restores any users open ticket, that is in storage , in session as autoclaiming has finished
    @param req: Apache request object
    @type req: Apache request object
    '''
    session_bareinit(req)
    session = get_session(req)
    ticket = session['personinfo']['ticket']
    temp_storage = session['personinfo']['incomplete_autoclaimed_tickets_storage']

    for t in list(temp_storage):
        ticket.append(t)
        temp_storage.remove(t)


def get_stored_incomplete_autoclaim_tickets(req):
    '''
    gets the records that its claim to the user profile was unsuccesfull
    @param req: Apache request object
    @type req: Apache request object
    '''
    session_bareinit(req)
    session = get_session(req)
    temp_storage = session['personinfo']['incomplete_autoclaimed_tickets_storage']
    return temp_storage


def add_cname_to_hepname_record(cname, recid, uid=None):
    """
    Schedule a BibUpload that will append the given personid to the specified record.
    """
    rec = {}
    record_add_field(rec, '001', controlfield_value=str(recid))
    record_add_field(rec,
                     tag=CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[:3],
                     ind1=CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3:4],
                     ind2=CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4:5],
                     subfields=[
                     (CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[5:6], str(cname)),
                     (CFG_BIBUPLOAD_EXTERNAL_OAIID_PROVENANCE_TAG[5:6], 'BAI')])
    tmp_file_fd, tmp_file_name = retry_mkstemp(suffix='.xml', prefix="bibauthorid-%s" % recid)
    tmp_file = os.fdopen(tmp_file_fd, "w")
    tmp_file.write(record_xml_output(rec))
    tmp_file.close()
    task_low_level_submission('bibupload', get_nickname(uid) or "", "-a", tmp_file_name, "-P5", "-N", "bibauthorid")


def connect_author_with_hepname(cname, hepname):
    subject = "HepNames record match: %s %s" % (cname, hepname)
    content = "Hello! Please connect the author profile %s " \
              "with the HepNames record %s. Best regards" % (cname, hepname)
    send_email(CFG_WEBAUTHORPROFILE_CFG_HEPNAMES_EMAIL,
               CFG_WEBAUTHORPROFILE_CFG_HEPNAMES_EMAIL,
               subject=subject,
               content=content)


def connect_author_with_orcid(cname, orcid):
    subject = "ORCiD record match: %s %s" % (cname, orcid)
    content = "Hello! Please connect the author profile %s " \
              "with the HepNames record %s. Best regards" % (cname, orcid)
    send_email(CFG_WEBAUTHORPROFILE_CFG_HEPNAMES_EMAIL,
               CFG_WEBAUTHORPROFILE_CFG_HEPNAMES_EMAIL,
               subject=subject,
               content=content)


#
# Exposed Ticket Functions            #
#

def construct_operation(operation_parts, pinfo, uid, should_have_bibref=False):
    pid = operation_parts['pid']
    if pid == bconfig.CREATE_NEW_PERSON:
        pid = create_new_person(uid)
    action = operation_parts['action']
    bibref, rec = split_bibrefrec(operation_parts['bibrefrec'])
    bibrefs = None

    if rec < 0 or pid < 0 or action not in ['assign', 'reject', 'reset']:
        return None

    if bibref is None:
        bibref = _guess_bibref(pid, rec, pinfo)
        if bibref is None:
            bibrefs = dbapi.get_all_signatures_of_paper(rec)

    # No bibref specified and no bibref candidates to select from.
    if not bibref and not bibrefs:
        send_email(CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL,
                   CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL,
                   subject="[Author] No authors on record: %s" % rec,
                   content="No authors seem to exist on record %s" % rec)
        return None

    if should_have_bibref and not bibref:
        return None

    operation = {'pid': pid,
                 'action': action,
                 'rec': rec,
                 'bibref': bibref,
                 'has_bibref': bibref is not None,
                 'bibrefs': bibrefs,
                 'has_all_metadata': False}

    return operation


def fill_out_userinfo(additional_info, uid, ip, ulevel, strict_check=True):
    if strict_check:
        if not additional_info['first_name'] or not additional_info['last_name'] or not email_valid_p(additional_info['email']):
            return None

    userinfo = {'uid-ip': '%s||%s' % (uid, ip),
                'comments': additional_info['comments'],
                'firstname': additional_info['first_name'],
                'lastname': additional_info['last_name'],
                'email': additional_info['email']}

    if ulevel in ['guest', 'user'] and not userinfo['comments']:
        userinfo['comments'] = 'No comments submitted.'

    return userinfo


def get_ticket_status(ticket):
    for op in ticket:
        _fill_out_operation(op)

    return ticket


def update_ticket_status(ticket):
    clean_ticket(ticket)


def add_operation_to_ticket(op, ticket):
    not_commited_operations = list(ticket)
    clean_ticket(not_commited_operations)
    for existing_op in not_commited_operations:
        if existing_op['pid'] == op['pid'] and existing_op['rec'] == op['rec']:

            # if the operation already exists don't do anything
            if existing_op['bibref'] == op['bibref'] and existing_op['action'] == op['action']:
                return False

            # if an existing operation differs in the bibref or the action replace the new with the old one
            ticket.remove(existing_op)
            ticket.append(op)
            return True

    # the operation doesn't exist in the ticket so it is added
    ticket.append(op)
    return True


def modify_operation_from_ticket(updated_op, ticket):
    not_commited_operations = list(ticket)
    clean_ticket(not_commited_operations)
    for existing_op in not_commited_operations:
        if existing_op['pid'] == updated_op['pid'] and existing_op['rec'] == updated_op['rec']:
            # Preserve bibrefs
            updated_op['bibrefs'] = existing_op['bibrefs']
            # if an existing operation differs in the bibref or the action replace the new with the old one
            ticket.remove(existing_op)
            ticket.append(updated_op)
            return True

    # the operation doesn't exist in the ticket
    return False


def remove_operation_from_ticket(op, ticket):
    not_commited_operations = list(ticket)
    clean_ticket(not_commited_operations)
    for existing_op in not_commited_operations:
        if existing_op['pid'] == op['pid'] and existing_op['rec'] == op['rec']:

            # if an existing operation differs in the bibref or the action, delete it
            ticket.remove(existing_op)
            return True

    # the operation doesn't exist in the ticket
    return False


def commit_operations_from_ticket(ticket, userinfo, uid, ulevel):
    incomplete_operations = list()
    for op in list(ticket):
        if not op['has_bibref']:
            ticket.remove(op)
            incomplete_operations.append(op)

    for op in ticket:
        bibrefrec = op['bibref'] + ',' + str(op['rec'])
        op['status'] = _check_operation_permission(uid, bibrefrec, op['pid'], op['action'])

    _commit_ticket(ticket, userinfo, uid, ulevel)

    ticket += incomplete_operations


def abort_ticket(ticket, delete_ticket=True):
    if delete_ticket:
        for op in list(ticket):
            ticket.remove(op)


def clean_ticket(ticket):
    for op in list(ticket):
        if 'execution_result' in op:
            ticket.remove(op)

#
# Not Exposed Ticket Functions        #
#


def split_bibrefrec(bibrefrec):
    if is_valid_bibref(bibrefrec):
        bibref, rec = bibrefrec.split(',')
        rec = int(rec)
    else:
        bibref = None
        rec = int(bibrefrec)

    return bibref, rec


def _guess_bibref(pid, rec, pinfo):
    try:
        arxiv_names = [pinfo['arxiv_name']]
    except KeyError:
        arxiv_names = list()

    _, possible_signatures = get_possible_bibrefs_from_pid_bibrec(pid, [rec], additional_names=arxiv_names)[0]

    if len(possible_signatures) == 1:
        return possible_signatures[0][0]

    return None


def _fill_out_operation(op):
    if not op['has_all_metadata'] and not 'execution_result' in op:
        op['rec_title'] = dbapi.get_title_of_paper(op['rec'])
        try:
            op['cname'] = dbapi.get_canonical_name_of_author(op['pid'])[0][0]
        except IndexError:
            op['cname'] = None
        op['has_all_metadata'] = True


def _check_operation_permission(uid, bibrefrec, pid, action):
    # user is superadmin so transaction permission is granted
    is_superadmin = isUserSuperAdmin({'uid': uid})
    if is_superadmin:
        return 'granted'

    owner_of_paper = False
    if pid == dbapi.get_author_by_uid(uid):
        owner_of_paper = True

    if owner_of_paper:
        action = bconfig.CLAIMPAPER_CLAIM_OWN_PAPERS
    else:
        action = bconfig.CLAIMPAPER_CLAIM_OTHERS_PAPERS

    auth, _ = acc_authorize_action(uid, action)

    if auth != 0:
        return 'denied'

    old_flag, old_lcul = dbapi.get_status_of_signature(bibrefrec)
    override_claim = False
    if old_flag in [2, -2]:
        override_claim = True

    if not override_claim:
        return 'granted'

    access_right = _resolve_maximum_acces_rights(uid)
    if override_claim and access_right[1] >= old_lcul:
        return 'granted'

    return 'denied'


def _commit_ticket(ticket, userinfo, uid, ulevel):

    def commit_ticket_guest(ticket, userinfo, uid, modified_pids):
        create_request_ticket(userinfo, ticket)

        for op in ticket:
            op['execution_result'] = {'success': True, 'operation': 'ticketized'}

    def commit_ticket_user(ticket, userinfo, uid, modified_pids):
        ok_ops = list()
        for op in list(ticket):
            if op['status'] == 'granted':
                bibrefrec = op['bibref'] + ',' + str(op['rec'])
                op['execution_result'] = _execute_operation(
                    op['action'],
                    op['pid'],
                    bibrefrec,
                    uid,
                    userinfo['uid-ip'],
                    str(userinfo))
                # This is the only point which modifies a person,
                # so this can trigger the deletion of a cached page.
                modified_pids.add(op['pid'])
                ok_ops.append(op)
                ticket.remove(op)

        if ticket:
            create_request_ticket(userinfo, ticket)

        if CFG_INSPIRE_SITE and ok_ops:
            send_user_commit_notification_email(userinfo, ok_ops)

        for op in ticket:
            op['execution_result'] = {'success': True, 'operation': 'ticketized'}

        ticket += ok_ops

    def commit_ticket_admin(ticket, userinfo, uid, modified_pids):
        for op in ticket:
            bibrefrec = op['bibref'] + ',' + str(op['rec'])
            op['execution_result'] = _execute_operation(
                op['action'],
                op['pid'],
                bibrefrec,
                uid,
                userinfo['uid-ip'],
                str(userinfo))
            # This is the only point which modifies a person,
            # so this can trigger the deletion of a cached page.
            modified_pids.add(op['pid'])

    commit = {'guest': commit_ticket_guest,
              'user': commit_ticket_user,
              'admin': commit_ticket_admin}

    modified_pids = set()

    not_already_executed_ops = [t for t in ticket if 'execution_result' not in t]

    commit[ulevel](not_already_executed_ops, userinfo, uid, modified_pids)

    for pid in modified_pids:
        webauthorapi.expire_all_cache_for_personid(pid)


def _execute_operation(action, pid, bibrefrec, uid, userinfo='', comment=''):
    res = None
    user_level = _resolve_maximum_acces_rights(uid)[1]

    if action == 'assign':
        dbapi.insert_user_log(userinfo, pid, 'assign', 'CMPUI_ticketcommit', bibrefrec, comment, userid=uid)
        res = dbapi.confirm_papers_to_author(pid, [bibrefrec], user_level)[0]
    elif action == 'reject':
        dbapi.insert_user_log(userinfo, pid, 'reject', 'CMPUI_ticketcommit', bibrefrec, comment, userid=uid)
        res = dbapi.reject_papers_from_author(pid, [bibrefrec], user_level)[0]
    elif action == 'reset':
        dbapi.insert_user_log(userinfo, pid, 'reset', 'CMPUI_ticketcommit', bibrefrec, comment, userid=uid)
        res = dbapi.confirm_papers_to_author(pid, [bibrefrec], user_level)[0]
        res = dbapi.reset_papers_of_author(pid, [bibrefrec])[0]

    return res

#
# Exposed Autoclaim-relevant Functions    #
#


def get_login_info(uid, params):
    login_info = {'logged_in_to_remote_systems': list(),
                  'uid': uid,
                  'logged_in': uid != 0}

    for system in CFG_BIBAUTHORID_ENABLED_REMOTE_LOGIN_SYSTEMS:
        if IS_LOGGED_IN_THROUGH[system](params[system]):
            login_info['logged_in_to_remote_systems'].append(system)

    return login_info


def get_papers_from_remote_systems(remote_systems, params, external_pubs_association):
    pubs = list()

    for system in remote_systems:
        pubs += GET_PUBS_FROM_REMOTE_SYSTEM[system](params[system])

    papers_from_remote_systems = _get_current_system_related_papers(set(pubs), external_pubs_association)

    return papers_from_remote_systems

#
# Not Exposed Autoclaim-relevant Functions    #
#


def _is_logged_in_through_arxiv(user_info):
    # TODO: ask Kaplun more accurate way to discover if we are SSOed through arxiv
    # WARNING: this assumes that any user logged in and which have an email was logged in through arXiv
    if user_info and 'email' in user_info and user_info['email']:
        return True

    return False


def _is_logged_in_through_orcid(orcid_info):
    return orcid_info['has_orcid_id'] and orcid_info['import_pubs']


def _get_pubs_from_arxiv(user_info):
    pubs_from_arxiv = list()

    if 'external_arxivids' in user_info and user_info['external_arxivids']:
        pubs_from_arxiv = user_info['external_arxivids'].split(';')

    return pubs_from_arxiv


def _get_pubs_from_orcid(orcid_info):
    pubs_from_orcid = list()

    if 'imported_pubs' in orcid_info and orcid_info['imported_pubs']:
        for doi in orcid_info['imported_pubs']:
            pubs_from_orcid.append(doi)

    return pubs_from_orcid


def _get_current_system_related_papers(pubs, external_pubs_association):
    papers = set()

    for pub in pubs:
        id_type = is_arxiv_id_or_doi(pub)

        try:
            recid = external_pubs_association[(id_type, pub)]
            papers.add(recid)
        except KeyError:
            recids = perform_request_search(
                p=pub,
                f=bconfig.CFG_BIBAUTHORID_REMOTE_LOGIN_SYSTEMS_IDENTIFIERS[id_type],
                m1='e',
                cc='HEP')
            if len(recids) == 1:
                recid = recids[0]
                papers.add(recid)
                external_pubs_association[(id_type, pub)] = recid

    return papers


IS_LOGGED_IN_THROUGH = {'arXiv': _is_logged_in_through_arxiv, 'orcid': _is_logged_in_through_orcid}
GET_PUBS_FROM_REMOTE_SYSTEM = {'arXiv': _get_pubs_from_arxiv, 'orcid': _get_pubs_from_orcid}

#
# Visit diary Functions            #
#


def history_log_visit(req, page, pid=None, params=None):
    """
    logs in the session the page that a user visited to use it when he needs to redirect
    @param page: string (claim, manage_profile, profile, search)
    @param parameters: string (?param=aoeuaoeu&param2=blabla)
    """
    session_bareinit(req)
    session = get_session(req)
    pinfo = session['personinfo']
    my_diary = pinfo['visit_diary']

    my_diary[page].append({'page': page, 'pid': pid, 'params': params, 'timestamp': time()})

    if len(my_diary[page]) > pinfo['diary_size_per_category']:
        my_diary[page].pop(0)
    session.dirty = True


def _get_sorted_history(visit_diary, limit_to_page=None):
    history = list()

    if not limit_to_page:
        history = visit_diary.values()
    else:
        for page in limit_to_page:
            history += visit_diary[page]

    history = list(chain(*visit_diary.values()))

    history = sorted(history, key=lambda x: x['timestamp'], reverse=True)

    return history


def history_get_last_visited_url(visit_diary, limit_to_page=None, just_page=False):
    '''
    getting a redirect link according to the last page visit of the user.
    The limit to page shortens the list of page canditates

    @param req: Apache request object
    @type req: Apache request object

    @param limit_to_page: By giving the subset of pages intrested in redirecting it shortens the list of page canditates
    @type limit_to_page: list of strings

    @return: redirect link
    @rtype: string
    '''
    history = _get_sorted_history(visit_diary, limit_to_page)
    try:
        history = history[0]
    except IndexError:
        return ''

    if just_page:
        return history['page']

    link = [CFG_SITE_URL + '/author/', history['page']]

    if history['pid']:
        link.append('/' + str(get_canonical_id_from_person_id(history['pid'])))
    if history['params']:
        link.append(history['params'])

    return ''.join(link)


def history_get_last_visited_pid(visit_diary, limit_to_page=None):
    history = _get_sorted_history(visit_diary, limit_to_page)
    for visit in history:
        if visit['pid']:
            return visit['pid']


def set_marked_visit_link(req, page, pid=None, params=None):
    '''
    store a marked redirect link for redirect purpose.

    @param req: Apache request object
    @type req: Apache request object

    @param page: the page to redirect
    @type page: string

    @param pid: person id
    @type pid: int

    @param params: url parameters if any of the following format: (?param1_name=param1&param2_name=param2)
    @type: string
    '''
    session_bareinit(req)
    session = get_session(req)
    pinfo = session['personinfo']
    if not page:
        pinfo['marked_visit'] = None
    else:
        link = [CFG_SITE_URL + '/author/', page]

        if pid:
            link.append('/' + str(get_canonical_id_from_person_id(pid)))
        if params:
            link.append(params)

        pinfo['marked_visit'] = ''.join(link)
    session.dirty = True


def get_marked_visit_link(req):
    '''
    getting a marked redirect link if stored there.
    Links to hopage if not

    @param req: Apache request object
    @type req: Apache request object

    @return: redirect link
    @rtype: string
    '''
    session_bareinit(req)
    session = get_session(req)
    pinfo = session['personinfo']

    return pinfo['marked_visit']


def reset_marked_visit_link(req):
    '''
    empty the marked redirect link.

    @param req: Apache request object
    @type req: Apache request object
    '''
    set_marked_visit_link(req, None)


def get_fallback_redirect_link(req):
    '''
    getting a redirect link if there is no other info at all.
    Links to manage profile of the user if logged in.
    Links to hopage if not

    @param req: Apache request object
    @type req: Apache request object

    @return: redirect link
    @rtype: string
    '''
    uid = getUid(req)
    pid = get_pid_from_uid(uid)
    if uid <= 0 and pid < 0:
        return '%s' % (CFG_SITE_URL,)
    return '%s/author/manage_profile/%s' % (CFG_SITE_URL, get_canonical_id_from_person_id(pid))

REMOTE_LOGIN_SYSTEMS_FUNCTIONS = {'arXiv': get_arxiv_info, 'orcid': get_orcid_info}
REMOTE_LOGIN_SYSTEMS_GET_RECIDS_FUNCTIONS = {'arXiv': get_ids_from_arxiv, 'orcid': get_ids_from_orcid}
