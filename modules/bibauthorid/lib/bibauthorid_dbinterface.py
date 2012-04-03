# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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
    bibauthorid_bdinterface
    This is the only file in bibauthorid which should
    use the data base. It should have an interface for
    all other files in the module.
'''
import bibauthorid_config as bconfig
import re
import time
import threading
import sys

from dbquery import serialize_via_marshal
from dbquery import deserialize_via_marshal
from invenio.access_control_engine import acc_authorize_action
from invenio.search_engine import perform_request_search

from bibauthorid_name_utils import split_name_parts
from bibauthorid_name_utils import clean_name_string
from bibauthorid_name_utils import soft_compare_names, compare_names
from bibauthorid_name_utils import create_canonical_name
from bibauthorid_general_utils import get_field_values_on_condition
from invenio.data_cacher import DataCacher
import datetime
from dbquery import run_sql \
                    , OperationalError \
                    , ProgrammingError \
                    , close_connection
from bibauthorid_name_utils import create_normalized_name

try:
    import unidecode
    UNIDECODE_ENABLED = True
except ImportError:
    bconfig.LOGGER.error("Authorid will run without unidecode support! "
                         "This is not recommended! Please install unidecode!")
    UNIDECODE_ENABLED = False

DATA_CACHERS = []
"""
DATA_CACHERS is a list of Data Cacher objects to be persistent in memory
"""

def get_bibref_name_string(bibref):
    '''
    Returns the name string associated with the given bibref
    @param: bibref ((100:123,),)
    '''
    name = run_sql("select db_name from aidAUTHORNAMES where id=(select Name_id from aidAUTHORNAMESBIBREFS where bibref=%s)", (str(bibref[0][0]),))
    if len(name) > 0:
        return name[0][0]
    else:
        return ''


def get_bibrefs_from_name_string(string):
    '''
    Returns bibrefs associated to a name string
    @param: string: name
    '''
    return run_sql("select bibrefs from aidAUTHORNAMES where db_name=%s ", (str(string),))


def set_person_data(person_id, tag, value, user_level=0):
    '''
    Change the value associated to the given tag for a certain person.
    @param person_id: ID of the person
    @type person_id: int
    @param tag: tag to be updated
    @type tag: string
    @param value: value to be written for the tag
    @type value: string
    '''
    current_tag_value = []

    try:
        current_tag_value = run_sql("SELECT data FROM aidPERSONID use index (`ptf-b`) "
                                    "WHERE personid = %s AND tag = %s AND "
                                    "data = %s", (person_id, tag, value))
    except (OperationalError, ProgrammingError):
        current_tag_value = run_sql("SELECT data FROM aidPERSONID "
                                    "WHERE personid = %s AND tag = %s AND "
                                    "data = %s", (person_id, tag, value))

    if len(current_tag_value) > 0:
        run_sql("UPDATE aidPERSONID SET tag = %s, data = %s WHERE "
                "personid = %s AND tag = %s AND lcul = %s", (tag, value, person_id, tag, user_level))
    else:
        run_sql("INSERT INTO aidPERSONID (`personid`, `tag`, `data`, `flag`, `lcul`) "
                "VALUES (%s, %s, %s, %s, %s);", (person_id, tag, value, '0', user_level))
    update_personID_canonical_names([[person_id]])


def get_person_data(person_id, tag=None, select_flag=False):
    '''
    Returns all the records associated to a person.
    If tag != None only rows for the selected tag will be returned.

    @param person_id: id of the person to read the attribute from
    @type person_id: int
    @param tag: the tag to read. Optional. Default: None
    @type tag: string

    @return: the data associated with a virtual author
    @rtype: tuple of tuples
    '''
    rows = []
    if not select_flag:
        if tag:
            rows = run_sql("SELECT tag, data FROM aidPERSONID "
                           "WHERE personid = %s AND tag = %s", (person_id, tag))
        else:
            rows = run_sql("SELECT tag, data FROM aidPERSONID "
                           "WHERE personid = %s", (person_id,))
    else:
        if tag:
            rows = run_sql("SELECT tag, data, flag FROM aidPERSONID "
                           "WHERE personid = %s AND tag = %s", (person_id, tag))
        else:
            rows = run_sql("SELECT tag, data, flag FROM aidPERSONID "
                           "WHERE personid = %s", (person_id,))
    return rows


def del_person_data(tag, person_id=None, value=None):
    '''
    Change the value associated to the given tag for a certain person.
    @param person_id: ID of the person
    @type person_id: int
    @param tag: tag to be updated
    @type tag: string
    @param value: value to be written for the tag
    @type value: string
    '''
    if person_id != None:
        if not value:
            run_sql("delete from aidPERSONID where personid=%s and tag=%s", (person_id, tag,))
        else:
            run_sql("delete from aidPERSONID where personid=%s and tag=%s and data=%s", (person_id, tag, value,))
    else:
        if not value:
            run_sql("delete from aidPERSONID where tag=%s", (tag,))
        else:
            run_sql("delete from aidPERSONID where tag=%s and data=%s", (tag, value,))


def get_all_papers_of_pids(personid_list):
    '''
    Get all papers of authors in a given list and sorts the results
    by bibrefrec.
    @param personid_list: list with the authors.
    @type personid_list: iteratable of integers.
    '''
    if personid_list:
        return []

    plist = list_2_SQL_str(personid_list, lambda x: str(x))

    return run_sql("select personid, data, flag \
                   from aidPERSONID \
                   where tag like 'paper' \
                   and personid in %s \
                   order by data" \
                   % plist)


def del_person_not_manually_claimed_papers(pid):
    '''
    Deletes papers from a person which have not been manually claimed.
    '''
    run_sql("delete from aidPERSONID where tag='paper'"
            " and (flag <> '-2' and flag <> '2') and personid=%s", (pid,))

def get_personid_from_uid(uid):
    '''
    Returns the personID associated with the provided ui.
    If the personID is already associated with the person the secon parameter is True, false otherwise.
    If there is more then one compatible results the persons are listed in order of name compatibility.
    If no persons are found returns ([-1],False)
    !!!
    The guessing mechanism got outdated thus disabled and replaced by arxiv_login in webapi, the code is left
    there for future updates
    !!!
    If there is none, associates on a best effort basis the best matching personid to the uid.
    @param uid: userID
    @type uid: ((int,),)
    '''
    pid = run_sql("select personid from aidPERSONID where tag=%s and data=%s", ('uid', str(uid[0][0])))
    if len(pid) == 1:
        return (pid[0], True)
    else:
        return  ([-1], False)


def create_new_person(uid, uid_is_owner=False):
    '''
    Create a new person. Set the uid as owner if requested.
    '''
    if len(run_sql("SELECT personid FROM aidPERSONID LIMIT 1")):
        pid = run_sql("select max(personid) from aidPERSONID")[0][0]
        pid = int(pid) + 1
    else:
        pid = 0

    if uid_is_owner:
        set_person_data(pid, 'uid', str(uid))
        set_person_data(pid, 'user-created', str(uid))
    else:
        set_person_data(pid, 'user-created', str(uid))

    return pid


def update_request_ticket(person_id, tag_data_tuple, ticket_id=None):
    '''
    Creates / updates a request ticket for a personID
    @param: personid int
    @param: tag_data_tuples 'image' of the ticket: (('paper', '700:316,10'), ('owner', 'admin'), ('external_id', 'ticket_18'))
    @return: ticketid
    '''
    #tags: rt_owner (the owner of the ticket, associating the rt_number to the transaction)
    #      rt_external_id
    #      rt_paper_cornfirm, rt_paper_reject, rt_paper_forget, rt_name, rt_email, rt_whatever
    #flag: rt_number
    if not ticket_id:
        last_id = []

        try:
            last_id = run_sql("select max(flag) from aidPERSONID use index (`ptf-b`) where personid=%s and tag like %s", (str(person_id), 'rt_%'))[0][0]
        except (OperationalError, ProgrammingError):
            last_id = run_sql("select max(flag) from aidPERSONID where personid=%s and tag like %s", (str(person_id), 'rt_%'))[0][0]

        if last_id:
            ticket_id = last_id + 1
        else:
            ticket_id = 1
    delete_request_ticket(person_id, ticket_id)

    for d in tag_data_tuple:
        run_sql("insert into aidPERSONID (personid,tag,data,flag) values (%s,%s,%s,%s)", (str(person_id), 'rt_' + str(d[0]), str(d[1]), str(ticket_id)))

    return ticket_id


def delete_request_ticket(person_id, ticket_id=None):
    '''
    Removes a ticket from a person_id.
    If ticket_id is not provider removes all the tickets pending on a person.
    '''
    if ticket_id:
        run_sql("delete from aidPERSONID where personid=%s and tag like %s and flag =%s", (str(person_id), 'rt_%', str(ticket_id)))
    else:
        run_sql("delete from aidPERSONID where personid=%s and tag like %s", (str(person_id), 'rt_%'))


def find_personIDs_by_name_string(namestring, strict=False):
    '''
    Search engine to find persons matching the given string
    The matching is done on the surname first, and names if present.
    An ordered list (per compatibility) of pids and found names is returned.

    @param namestring: string name, 'surname, names I.'
    @type: string
    @param strict: Define if this shall perform an exact or a fuzzy match
    @type strict: boolean
    @return: pid list of lists
    [pid,[[name string, occur count, compatibility]]]
    '''
    canonical = []
    use_index = True

    try:
        canonical = run_sql("select personid,data from aidPERSONID use index (`tdf-b`) where data like %s and tag=%s", (namestring + '%', 'canonical_name'))
    except (ProgrammingError, OperationalError):
        canonical = run_sql("select personid,data from aidPERSONID where data like %s and tag=%s", (namestring + '%', 'canonical_name'))
        use_index = False

    namestring_parts = split_name_parts(namestring)

#   The following lines create the regexp used in the query.
    surname = clean_name_string(namestring_parts[0],
#                                replacement=".{0,3}",
                                replacement="%",
                                keep_whitespace=False,
                                trim_whitespaces=True)
    surname = surname + ',%'
    matching_pids_names_tuple = []

    if use_index:
        matching_pids_names_tuple = run_sql("select o.personid, o.data, o.flag from aidPERSONID o use index (`ptf-b`), "
                                            "(select distinct i.personid as ipid from aidPERSONID i use index (`tdf-b`) where i.tag='gathered_name' and i.data like %s)"
                                            " as dummy where  o.tag='gathered_name' and o.personid = dummy.ipid", (surname,))
#        matching_pids_names_tuple = run_sql("select personid, data, flag from aidPERSONID use index (`ptf-b`) "
#                                            "where  tag=\'gathered_name\' and personid in "
#                                            "(select distinct personid from aidPERSONID use index (`tdf-b`) "
#                                            "where tag=\'gathered_name\' and data like %s)", (surname,))
    else:
        matching_pids_names_tuple = run_sql("select o.personid, o.data, o.flag from aidPERSONID o, "
                                            "(select distinct i.personid as ipid from aidPERSONID i where i.tag='gathered_name' and i.data like %s)"
                                            " as dummy where  o.tag='gathered_name' and o.personid = dummy.ipid", (surname,))
#    print matching_pids_names_tuple
    if len(matching_pids_names_tuple) == 0 and len(surname) >= 2:
        surname = surname[0:len(surname) - 2] + '%,%'

        if use_index:
            matching_pids_names_tuple = run_sql("select o.personid, o.data, o.flag from aidPERSONID o use index (`ptf-b`), "
                                            "(select distinct i.personid as ipid from aidPERSONID i use index (`tdf-b`) where i.tag='gathered_name' and i.data like %s)"
                                            " as dummy where  o.tag='gathered_name' and o.personid = dummy.ipid", (surname,))
        else:
            matching_pids_names_tuple = run_sql("select o.personid, o.data, o.flag from aidPERSONID o, "
                                            "(select distinct i.personid as ipid from aidPERSONID i where i.tag='gathered_name' and i.data like %s)"
                                            " as dummy where  o.tag='gathered_name' and o.personid = dummy.ipid", (surname,))

    if len(matching_pids_names_tuple) == 0 and len(surname) >= 2:
        surname = '%' + surname[0:len(surname) - 2] + '%,%'

        if use_index:
            matching_pids_names_tuple = run_sql("select o.personid, o.data, o.flag from aidPERSONID o use index (`ptf-b`), "
                                            "(select distinct i.personid as ipid from aidPERSONID i use index (`tdf-b`) where i.tag='gathered_name' and i.data like %s)"
                                            " as dummy where  o.tag='gathered_name' and o.personid = dummy.ipid", (surname,))
        else:
            matching_pids_names_tuple = run_sql("select o.personid, o.data, o.flag from aidPERSONID o, "
                                            "(select distinct i.personid as ipid from aidPERSONID i where i.tag='gathered_name' and i.data like %s)"
                                            " as dummy where  o.tag='gathered_name' and o.personid = dummy.ipid", (surname,))

    matching_pids = []
#    print matching_pids_names_tuple
    for name in matching_pids_names_tuple:
        comparison = soft_compare_names(namestring, name[1])
        matching_pids.append([name[0], name[1], name[2], comparison])
#   matching_pids = sorted(matching_pids, key=lambda k: k[3], reverse=True)
#    print matching_pids
    persons = {}
    if len(canonical) > 0:
        for n in canonical:
            matching_pids.append([n[0], n[1], 1, 1])
    for n in matching_pids:
        if n[3] >= 0.4:
            if n[0] not in persons:
                persons[n[0]] = sorted([[p[1], p[2], p[3]] for p in  matching_pids if p[0] == n[0]],
                                key=lambda k: k[2], reverse=True)
#    print persons
    porderedlist = []
    for i in persons.iteritems():
        porderedlist.append([i[0], i[1]])
    porderedlist = sorted(porderedlist, key=lambda k: k[1][0][1], reverse=False)
    porderedlist = sorted(porderedlist, key=lambda k: k[1][0][0], reverse=False)
    porderedlist = sorted(porderedlist, key=lambda k: k[1][0][2], reverse=True)
    if strict and len(porderedlist) >= 1:
        return [porderedlist[0]]
    return porderedlist


def get_bibref_modification_status(bibref):
    '''
    Determines if a record attached to a person has been touched by a human
    by checking the flag.

    @param pid: The Person ID of the person to check the assignment from
    @type pid: int
    @param bibref: The paper identifier to be checked (e.g. "100:12,144")
    @type bibref: string

    returns [bool:human_modified, int:lcul]
    '''
    if not bibref:
        raise ValueError("A bibref is expected!")

    flags = []

    try:
        flags = run_sql("SELECT flag,lcul FROM aidPERSONID use index (`tdf-b`) WHERE "
                       "tag = 'paper' AND data = %s"
                       , (bibref,))
    except (OperationalError, ProgrammingError):
        flags = run_sql("SELECT flag,lcul FROM aidPERSONID WHERE "
                       "tag = 'paper' AND data = %s"
                       , (bibref,))

    try:
        flag = flags[0][0]
        lcul = flags[0][1]
    except (IndexError):
        return [False, 0]

    return [flag, lcul]


def get_canonical_id_from_personid(pid):
    '''
    Finds the person id canonical name (e.g. Ellis_J_R_1)

    @param pid
    @type int

    @return: sql result of the request
    @rtype: tuple of tuple
    '''
    return run_sql("SELECT data FROM aidPERSONID WHERE "
                   "tag='canonical_name' AND personid = %s", (str(pid),))


def get_papers_status(papers):
    '''
    Gets the personID and flag assiciated to papers
    @param papers: list of papers
    @type papers: (('100:7531,9024',),)
    @return: (('data','personID','flag',),)
    @rtype: tuple of tuples
    '''
    #lst of papers (('100:7531,9024',),)
    #for each paper gives: personid, assignment status
    papersstr = '( '
    for p in papers:
        papersstr += '\'' + str(p[0]) + '\','
    papersstr = papersstr[0:len(papersstr) - 1] + ' )'
    if len(papers) >= 1:
        ret_val = []

        try:
            ret_val = run_sql("select data,PersonID,flag from aidPERSONID use index (`tdf-b`) where tag=%s and data in " + papersstr,
                    ('paper',))
        except (ProgrammingError, OperationalError):
            ret_val = run_sql("select data,PersonID,flag from aidPERSONID where tag=%s and data in " + papersstr,
                    ('paper',))

        return ret_val
    else:
        return []


class PersonIDStatusDataCacher(DataCacher):
    '''
    Data Cacher to monitor the existence of personid data
    '''
    def __init__(self):
        '''
        Initializes the Data Cacher
        '''
        def cache_filler():
            '''
            Sets the Data Cacher content to True if the table is not empty
            '''
            try:
                if len(run_sql("SELECT personid FROM aidPERSONID "
                               "WHERE tag='paper' LIMIT 1")):
                    return True
                else:
                    return False
            except Exception:
                # database problems, return empty cache
                return False

        def timestamp_verifier():
            '''
            Verifies that the table is still empty every 2 hours
            '''
            dt = datetime.datetime.now()
            td = dt - datetime.timedelta(hours=2)
            return td.strftime("%Y-%m-%d %H:%M:%S")

        DataCacher.__init__(self, cache_filler, timestamp_verifier)


def get_persons_from_recids(recids, return_alt_names=False,
                                    return_all_person_papers=False):
    '''
    Function to find person informations as occuring on records

    @param recids: List of rec IDs
    @type recids: list of int
    @param return_alt_names: Return all name variations?
    @type return_alt_names: boolean
    @param return_all_person_papers: Return also a person's record IDs?
    @type return_all_person_papers: boolean

    return: tuple of two dicts:
        structure: ({recid: [personids]}, {personid: {personinfo}})
        example:
        ({1: [4]},
        {4: {'canonical_id' : str,
             'alternatative_names': list of str,
             'person_records': list of int
            }
        })
    rtype: tuple of two dicts
    '''
    rec_pid = {}
    pinfo = {}

    if not isinstance(recids, list) or isinstance(recids, tuple):
        if isinstance(recids, int):
            recids = [recids]
        else:
            return (rec_pid, pinfo)

    if not DATA_CACHERS:
        DATA_CACHERS.append(PersonIDStatusDataCacher())

    pid_table_cacher = DATA_CACHERS[0]
    pid_table_cacher.recreate_cache_if_needed()

    if not pid_table_cacher.cache:
        return (rec_pid, pinfo)

    for recid in recids:
        rec_names = get_field_values_on_condition(recid,
                                                  source='API',
                                                  get_table=['100', '700'],
                                                  get_tag='a')
        for rname in rec_names:
            rname = rname.encode('utf-8')
            rec_bibrefs = run_sql("select bibrefs from aidAUTHORNAMES where "
                                  "db_name=%s", (rname,))

            if not rec_bibrefs:
                continue

            rec_bibrefs = rec_bibrefs[0][0].split(',')
            bibrefrec = ""

            if len(rec_bibrefs) > 1:
                for ref in rec_bibrefs:
                    table, refid = ref.split(":")
                    tmp = None

                    if table == "100":
                        tmp = run_sql("select id_bibrec from bibrec_bib10x "
                                      "where id_bibxxx=%s and id_bibrec=%s",
                                      (refid, recid))
                    elif table == "700":
                        tmp = run_sql("select id_bibrec from bibrec_bib70x "
                                      "where id_bibxxx=%s and id_bibrec=%s",
                                      (refid, recid))
                    else:
                        continue

                    if tmp:
                        bibrefrec = "%s,%s" % (ref, recid)
                        break
            else:
                try:
                    bibrefrec = "%s,%s" % (rec_bibrefs[0], recid)
                except IndexError:
                    pass

            if bibrefrec:
                pids = []

                try:
                    pids = run_sql("select personid from aidPERSONID "
                                   "use index (`tdf-b`) where "
                                   "tag=%s and data=%s and flag > -1",
                                   ('paper', bibrefrec))
                except (ProgrammingError, OperationalError):
                    pids = run_sql("select personid from aidPERSONID "
                                   "where "
                                   "tag=%s and data=%s and flag > -1",
                                   ('paper', bibrefrec))

                pids = [i[0] for i in pids]

                for pid in pids:
                    if recid in rec_pid:
                        rec_pid[recid].append(pid)
                    else:
                        rec_pid[recid] = [pid]
                    if pid in pinfo:
                        continue

                    pinfo[pid] = {}
                    cid = ""

                    try:
                        cid = get_person_data(pid, "canonical_name")[0][1]
                    except IndexError:
                        pass

                    pinfo[pid]["canonical_id"] = cid

                    if return_alt_names:
                        anames = get_person_db_names_count((pid,))
                        pinfo[pid]["alternative_names"] = [anm[0]
                                                           for anm in anames]

                    if return_all_person_papers:
                        pinfo[pid]["person_records"] = get_person_papers(
                                                        (pid,), -1,
                                                        show_author_name=True,
                                                        show_title=False)

    return (rec_pid, pinfo)


def get_person_db_names_count(pid, sort_by_count=True):
    '''
    Returns the set of name strings and count associated to a person id.
    The name strings are as found in the database.
    @param pid: ID of the person
    @type pid: ('2',)
    '''
    docs = []

    try:
        docs = run_sql("SELECT `data` FROM `aidPERSONID` use index (`ptf-b`) where PersonID=%s and tag=%s and flag>=%s",
                        (str(pid[0]), 'paper', '-1',))
    except (ProgrammingError, OperationalError):
        docs = run_sql("SELECT `data` FROM `aidPERSONID` where PersonID=%s and tag=%s and flag>=%s",
                        (str(pid[0]), 'paper', '-1',))

    authornames = {}
    for doc in docs:
        dsplit = doc[0].split(',')
        tnum = "70"
        if str(dsplit[0].split(':')[0]) == "100":
            tnum = "10"
        sqlstr = "SELECT value FROM bib%sx WHERE  id = " % tnum + "%s"
        authorname = run_sql(sqlstr, (dsplit[0].split(':')[1],))
        if len(authorname) > 0:
            if authorname[0][0] not in authornames:
                authornames[authorname[0][0]] = 1
            else:
                authornames[authorname[0][0]] += 1
    authornames = list(authornames.iteritems())
    if sort_by_count:
        authornames = sorted(authornames, key=lambda k: k[0], reverse=False)
    return authornames


def get_person_id_from_canonical_id(canonical_id):
    '''
    Finds the person id from a canonical name (e.g. Ellis_J_R_1)

    @param canonical_id: the canonical ID
    @type canonical_id: string

    @return: sql result of the request
    @rtype: tuple of tuple
    '''
    return run_sql("SELECT personid FROM aidPERSONID WHERE "
                   "tag='canonical_name' AND data = %s", (canonical_id,))


def get_person_names_count(pid):
    '''
    Returns the set of name strings and count associated to a person id
    @param pid: ID of the person
    @type pid: ('2',)
    @param value: value to be written for the tag
    @type value: string
    '''
    ret_val = []

    try:
        ret_val = run_sql("select data,flag from aidPERSONID use index (`ptf-b`) where PersonID=%s and tag=%s",
                    (str(pid[0]), 'gathered_name',))
    except (OperationalError, ProgrammingError):
        ret_val = run_sql("select data,flag from aidPERSONID where PersonID=%s and tag=%s",
                    (str(pid[0]), 'gathered_name',))

    return ret_val


def get_person_names_set(pid):
    '''
    Returns the set of name strings associated to a person id
    @param pid: ID of the person
    @type pid: ('2',)
    @param value: value to be written for the tag
    @type value: string
    '''
    docs = []

    try:
        docs = run_sql("SELECT `data` FROM `aidPERSONID` use index (`ptf-b`) where PersonID=%s and tag=%s and flag>=%s",
                        (str(pid[0]), 'paper', '-1',))
    except (ProgrammingError, OperationalError):
        docs = run_sql("SELECT `data` FROM `aidPERSONID` where PersonID=%s and tag=%s and flag>=%s",
                    (str(pid[0]), 'paper', '-1',))

    authornames = set()
    for doc in docs:
        dsplit = doc[0].split(',')
        tnum = "70"
        if str(dsplit[0].split(':')[0]) == "100":
            tnum = "10"
        sqlstr = "SELECT value FROM bib%sx WHERE  id = " % tnum + "%s"
        authorname = run_sql(sqlstr, (dsplit[0].split(':')[1],))
        if len(authorname) > 0:
            authornames.add(authorname[0])
    return list(authornames)

def get_personids_from_bibrec(bibrec):
    '''
    Returns all the personids associated to a bibrec.
    '''
    authors = get_authors_from_paper(bibrec)
    coauthors = get_coauthors_from_paper(bibrec)

    alist = ''.join(["'100:%s,%s'," % (p[0], str(bibrec)) for p in authors])
    clist = ''.join(["'700:%s,%s'," % (p[0], str(bibrec)) for p in coauthors])
    if len(clist) > 0:
        clist = clist[0:len(clist) - 1]
    elif len(alist) > 0:
        alist = alist[0:len(alist) - 1]
    else:
        return []
    query = ("select distinct personid from aidPERSONID where tag='paper' and flag > '-1'"
            " and data in (%s)" % (alist + clist))
    pids = run_sql(query)
    return [a[0] for a in pids]


def get_person_bibrecs(pid):
    '''
    Returns bibrecs associated with a personid
    @param pid: integer personid
    @return [bibrec1,...,bibrecN]
    '''
    papers = run_sql("select data from aidPERSONID where personid=%s and tag='paper'", (str(pid),))
    bibrecs = [p[0].split(',')[1] for p in papers]
    return bibrecs

def get_person_papers(pid, flag, show_author_name=False,
                      show_title=False, show_rt_status=False):
    '''
    Returns all the paper associated to a person with a flag greater or equal
    than the given one. Eventually returns even author name and title
    associated to the papers.

    @param pid: person id
    @type pid: ('2',)
    @param flag: numerical flag, the convention is documented with the
                 database table creation script
    @type papers: integer
    @param show_author_name: Also return authorname in dict?
    @type show_author_name: Boolean
    @param show_title: Also return title in dict?
    @type show_title: Boolean
    @param show_rt_status: Also return if this paper is currently mentioned
        in a ticket to be reviewed by an operator.

    @return: [{'data': String,
               'flag': Int,
               'author_name': String,
               'title': String,
               'rt_status': Boolean}]
             author_name and title will be returned depending on the params
    @rtype: list of dicts
    '''
    #expects a pid ('2',)
    #and a flag 0
    try:
        from invenio.search_engine import get_record
    except ImportError:
        return []

    paperslist = []
    docs = []

    try:
        flag = int(flag)
    except ValueError:
        return paperslist

    try:
        docs = run_sql("SELECT data,flag FROM aidPERSONID use index (`ptf-b`) "
                       "where personid = %s "
                       "and tag = %s and flag >= %s",
                       (pid[0], 'paper', flag))
    except (ProgrammingError, OperationalError):
        docs = run_sql("SELECT data,flag FROM aidPERSONID where personid = %s"
                        " and tag = %s and flag >= %s",
                        (pid[0], 'paper', flag))

    for doc in docs:
        listdict = {}

        if show_title:
            title = "No title on paper..."

            try:
                rec_id = int(doc[0].split(',')[1])
                title = get_record(rec_id)['245'][0][0][0][1]
            except (IndexError, KeyError, ValueError):
                title = "Problem encountered while retrieving document title"

            listdict["title"] = title

        dsplit = doc[0].split(',')
        tnum = "70"

        if str(dsplit[0].split(':')[0]) == "100":
            tnum = "10"

        sqlstr = ("SELECT value FROM bib%sx WHERE  id = " % (tnum)) + '%s'
        authorname = run_sql(sqlstr, (dsplit[0].split(':')[1],))

        try:
            authorname = authorname[0][0]

            if show_author_name:
                listdict["authorname"] = authorname.decode("utf-8")
        except IndexError:
            #The paper has been modified and this bibref is no longer there
            #@TODO: this must call bibsched to update_personid_table_from_paper
            continue

        listdict["data"] = doc[0]
        listdict["flag"] = doc[1]

        if show_rt_status:
            rt_count = run_sql("SELECT count(*) FROM aidPERSONID WHERE "
                               "tag like 'rt_%%' and data = %s", (doc[0],))
            try:
                rt_count = int(rt_count[0][0])
            except (IndexError, ValueError, TypeError):
                rt_count = 0

            if rt_count > 0:
                listdict["rt_status"] = True
            else:
                listdict["rt_status"] = False

        paperslist.append(listdict)

    return paperslist


def get_persons_with_open_tickets_list():
    '''
    Finds all the persons with open tickets and returns pids and count of tickets
    @return: [[pid, ticket_count]]
    '''
    try:
        return run_sql("select o.personid, count(distinct o.flag) from "
                    "aidPERSONID o use index (`ptf-b`), "
                    "(select distinct i.personid as iid from aidPERSONID i "
                    "use index (`ptf-b`) where tag like 'rt_%') as dummy "
                    "WHERE tag like 'rt_%' AND o.personid = dummy.iid "
                    "group by o.personid")
    except (OperationalError, ProgrammingError):
        return run_sql("select o.personid, count(distinct o.flag) from "
                    "aidPERSONID o, "
                    "(select distinct i.personid as iid from aidPERSONID i "
                    "where tag like 'rt_%') as dummy "
                    "WHERE tag like 'rt_%' AND o.personid = dummy.iid "
                    "group by o.personid")
#    try:
#        return run_sql('select personid,count(distinct(flag)) from aidPERSONID use index (`ptf-b`)'
#                   'where personid in (select distinct personid from aidPERSONID use index (`ptf-b`) '
#                   'where tag like "rt_%") and tag like "rt_%" group by personid ')
#    except (OperationalError, ProgrammingError):
#        return run_sql('select personid,count(distinct(flag)) from aidPERSONID '
#                   'where personid in (select distinct personid from aidPERSONID '
#                   'where tag like "rt_%") and tag like "rt_%" group by personid ')


def get_possible_personids_from_paperlist(bibrecreflist):
    '''
    @param bibrecreflist: list of bibrecref couples, (('100:123,123',),) or bibrecs (('123',),)
    returns a list of pids and connected bibrefs in order of number of bibrefs per pid
    [ [['1'],['123:123.123','123:123.123']] , [['2'],['123:123.123']] ]
    '''

    pid_bibrecref_dict = {}
    for b in bibrecreflist:
        pids = []

        try:
            pids = run_sql("select personid from aidPERSONID "
                    "use index (`tdf-b`) where tag=%s and data=%s", ('paper', str(b[0])))
        except (OperationalError, ProgrammingError):
            pids = run_sql("select personid from aidPERSONID "
                    "where tag=%s and data=%s", ('paper', str(b[0])))

        for pid in pids:
            if pid[0] in pid_bibrecref_dict:
                pid_bibrecref_dict[pid[0]].append(str(b[0]))
            else:
                pid_bibrecref_dict[pid[0]] = [str(b[0])]

    pid_list = [[i, pid_bibrecref_dict[i]] for i in pid_bibrecref_dict]

    return sorted(pid_list, key=lambda k: len(k[1]), reverse=True)


def get_request_ticket(person_id, matching=None, ticket_id=None):
    '''
    Retrieves one or many requests tickets from a person
    @param: person_id: person id integer
    @param: matching: couple of values to match ('tag', 'value')
    @param: ticket_id: ticket id (flag) value
    @returns: [[[('tag', 'value')], ticket_id]]
        [[[('a', 'va'), ('b', 'vb')], 1L], [[('b', 'daOEIaoe'), ('a', 'caaoOUIe')], 2L]]
    '''
    use_index = True
    tickets = []

    if ticket_id:
        rows = []

        try:
            rows = [run_sql("select tag,data,flag from aidPERSONID use index (`ptf-b`) where tag like %s and personid=%s and flag=%s", ('rt_%', str(person_id), str(ticket_id)))]
        except (ProgrammingError, OperationalError):
            rows = [run_sql("select tag,data,flag from aidPERSONID where tag like %s and personid=%s and flag=%s", ('rt_%', str(person_id), str(ticket_id)))]
            use_index = False

        if len(rows) < 1:
            return []
    else:
        rows = []
        ids = []

        if use_index:
            if not matching:
                ids = run_sql("select distinct flag from aidPERSONID use index (`ptf-b`) where personid=%s and tag like %s", (str(person_id), 'rt_%'))
            else:
                ids = run_sql("select distinct flag from aidPERSONID use index (`tdf-b`) where tag=%s and data=%s and personid=%s", ('rt_' + str(matching[0]), str(matching[1]), str(person_id)))
        else:
            if not matching:
                ids = run_sql("select distinct flag from aidPERSONID where personid=%s and tag like %s", (str(person_id), 'rt_%'))
            else:
                ids = run_sql("select distinct flag from aidPERSONID where tag=%s and data=%s and personid=%s", ('rt_' + str(matching[0]), str(matching[1]), str(person_id)))

        for tid in ids:
            if use_index:
                rows.append(run_sql("select tag,data,flag from aidPERSONID use index (`ptf-b`) where tag like %s and personid=%s and flag = %s", ('rt_%', str(person_id), str(tid[0]))))
            else:
                rows.append(run_sql("select tag,data,flag from aidPERSONID where tag like %s and personid=%s and flag = %s", ('rt_%', str(person_id), str(tid[0]))))

    for row in rows:
        ticket = []
        for line in row:
            ticket.append((line[0][3:], line[1]))
        try:
            tickets.append([ticket, row[0][2]])
        except IndexError:
            pass
    return tickets


def insert_user_log(userinfo, personid, action, tag, value, comment='', transactionid=0, timestamp=''):
    '''
    Instert log entries in the user log table.
    For example of entres look at the table generation script.
    @param userinfo: username or user identifier
    @type: string
    @param personid: personid involved in the transaction
    @type: longint
    @param action: action type
    @type: string
    @param tag: tag
    @type: string
    @param value: value for the transaction
    @type: string
    @param comment: optional comment for the transaction
    @type: string
    @param transactionid: optional id for the transaction
    @type: longint

    @return: the transactionid
    @rtype: longint
    '''
#    if transactionid == 0:
#        transactionid = max(run_sql('SELECT  MAX(transactionid) FROM `aidUSERINPUTLOG`')[0][0], -1) + 1

    if timestamp:
        tsui = str(timestamp)
    else:
        tsui = run_sql('select now()')[0][0]

#    run_sql('insert into aidUSERINPUTLOG (transactionid,timestamp,userinfo,personid,action,tag,value,comment) values '
#            '(%(transactionid)s,%(timestamp)s,%(userinfo)s,%(personid)s,%(action)s,%(tag)s,%(value)s,%(comment)s)',
#            ({'transactionid':str(transactionid),
#              'timestamp':str(tsui),
#              'userinfo':str(userinfo),
#              'personid':str(personid),
#              'action':str(action),
#              'tag':str(tag),
#              'value':str(value),
#              'comment':str(comment)}))
    run_sql('insert into aidUSERINPUTLOG '
            '(transactionid,timestamp,userinfo,personid,action,tag,value,comment) values '
            '(%s,%s,%s,%s,%s,%s,%s,%s)',
            (str(transactionid), str(tsui), str(userinfo), str(personid),
             str(action), str(tag), str(value), str(comment)))

    return transactionid


def person_bibref_is_touched(pid, bibref):
    '''
    Determines if a record attached to a person has been touched by a human
    by checking the flag.

    @param pid: The Person ID of the person to check the assignment from
    @type pid: int
    @param bibref: The paper identifier to be checked (e.g. "100:12,144")
    @type bibref: string
    '''
    if not isinstance(pid, int):
        try:
            pid = int(pid)
        except (ValueError, TypeError):
            raise ValueError("Person ID has to be a number!")

    if not bibref:
        raise ValueError("A bibref is expected!")

    flag = []

    try:
        flag = run_sql("SELECT flag FROM aidPERSONID use index (`ptf-b`) WHERE "
                       "personid = %s AND tag = 'paper' AND data = %s"
                       , (pid, bibref))
    except (OperationalError, ProgrammingError):
        flag = run_sql("SELECT flag FROM aidPERSONID WHERE "
                       "personid = %s AND tag = 'paper' AND data = %s"
                       , (pid, bibref))

    try:
        flag = flag[0][0]
    except (IndexError):
        return False

    if not flag:
        return False
    elif -2 < flag < 2:
        return False
    else:
        return True


def reject_papers_from_person(pid, papers, gather_list, user_level=0):
    '''
    Confirms the negative relationship between pid and paper, as from user input.
    @param pid: id of the person
    @type pid: ('2',)
    @param papers: list of papers to confirm
    @type papers: (('100:7531,9024',),)
    @param gather_list: list to store the pids to be updated rather than
    calling update_personID_names_string_set
    @typer gather_list: set([('2',), ('3',)])
    '''
    #expects a pid ('2',)
    #and a lst of papers (('100:7531,9024',),)
    #check if already assigned by user and skip those ones
    for p in papers:
        run_sql("update aidPERSONID set flag=%s,lcul=%s where PersonID=%s and data=%s",
                ('-2', user_level, str(pid[0]), str(p[0])))

    if gather_list != None:
        gather_list.add(pid)
    else:
        update_personID_names_string_set((pid,))
    update_personID_canonical_names([pid])


def reset_papers_flag(pid, papers, gather_list):
    '''
    Resets the flag associated to the papers to '0'
    @param papers: list of papers to confirm
    @type papers: (('100:7531,9024',),)
    @param gather_list: list to store the pids to be updated rather than
    calling update_personID_names_string_set
    @typer gather_list: set([('2',), ('3',)])
    '''
    for p in papers:
        run_sql("update aidPERSONID set flag='0',lcul='0' where tag=%s and data=%s",
                ('paper', str(p[0])))

    if gather_list != None:
        gather_list.add(pid)
    else:
        update_personID_names_string_set((pid,))
    update_personID_canonical_names((pid,))


def user_can_modify_data(uid, pid):
    '''
    Return True if the uid can modify data of this personID, false otherwise.
    @param uid: the user id
    @type: int
    @param pid: the person id
    @type: int

    @return: can user mofidfy data?
    @rtype: boolean
    '''
    pid_uid = []

    try:
        pid_uid = run_sql("select data from aidPERSONID use index (`ptf-b`) "
                          "where tag = %s and personid = %s", ('uid', str(pid)))
    except (OperationalError, ProgrammingError):
        pid_uid = run_sql("select data from aidPERSONID where tag = %s"
                          " and personid = %s", ('uid', str(pid)))

    if len(pid_uid) >= 1:
        if str(uid) == str(pid_uid[0][0]):
            if acc_authorize_action(uid, bconfig.CLAIMPAPER_CHANGE_OWN_DATA)[0] == 0:
                return True
        if acc_authorize_action(uid, bconfig.CLAIMPAPER_CHANGE_OTHERS_DATA)[0] == 0:
            return True

        return False
    else:
        if acc_authorize_action(uid, bconfig.CLAIMPAPER_CHANGE_OTHERS_DATA)[0] == 0:
            return True

        return False


def get_possible_bibrecref(names, bibrec, always_match=False):
    '''
    Returns a list of bibrefs for which the surname is matching
    @param names: list of names strings
    @param bibrec: bibrec number
    @param always_match: match with all the names (full bibrefs list)
    '''
    splitted_names = []
    for n in names:
        splitted_names.append(split_name_parts(n))

    bibrec_names_100 = run_sql("select o.id, o.value from bib10x o, "
                               "(select i.id_bibxxx as iid from bibrec_bib10x i "
                               "where id_bibrec=%s) as dummy "
                               "where o.tag='100__a' AND o.id = dummy.iid",
                               (str(bibrec),))
    bibrec_names_700 = run_sql("select o.id, o.value from bib70x o, "
                               "(select i.id_bibxxx as iid from bibrec_bib70x i "
                               "where id_bibrec=%s) as dummy "
                               "where o.tag='700__a' AND o.id = dummy.iid",
                               (str(bibrec),))
#    bibrec_names_100 = run_sql("select id,value from bib10x where tag='100__a' and id in "
#                               "(select id_bibxxx from bibrec_bib10x where id_bibrec=%s)",
#                               (str(bibrec),))
#    bibrec_names_700 = run_sql("select id,value from bib70x where tag='700__a' and id in "
#                               "(select id_bibxxx from bibrec_bib70x where id_bibrec=%s)",
#                               (str(bibrec),))
    bibreflist = []

    for b in bibrec_names_100:
        spb = split_name_parts(b[1])
        for n in splitted_names:
            if (n[0].lower() == spb[0].lower()) or always_match:
                if ['100:' + str(b[0]), b[1]] not in bibreflist:
                    bibreflist.append(['100:' + str(b[0]), b[1]])

    for b in bibrec_names_700:
        spb = split_name_parts(b[1])
        for n in splitted_names:
            if (n[0].lower() == spb[0].lower()) or always_match:
                if ['700:' + str(b[0]), b[1]] not in bibreflist:
                    bibreflist.append(['700:' + str(b[0]), b[1]])

    return bibreflist


def user_can_modify_paper(uid, paper):
    '''
    Return True if the uid can modify this paper, false otherwise.
    If the paper is assigned more then one time (from algorithms) consider the most privileged
    assignment.
    @param uid: the user id
    @type: int
    @param paper: the paper bibref,bibrec pair x00:1234,4321
    @type: str

    @return: can user mofidfy paper attribution?
    @rtype: boolean
    '''
    prow = []

    try:
        prow = run_sql("select id,personid,tag,data,flag,lcul from aidPERSONID use index (`tdf-b`) where tag=%s and data =%s"
                       "order by lcul desc limit 0,1", ('paper', str(paper)))
    except (OperationalError, ProgrammingError):
        prow = run_sql("select id,personid,tag,data,flag,lcul from aidPERSONID where tag=%s and data =%s"
                       "order by lcul desc limit 0,1", ('paper', str(paper)))

    if len(prow) == 0:
        if ((acc_authorize_action(uid, bconfig.CLAIMPAPER_CLAIM_OWN_PAPERS)[0] == 0) or (acc_authorize_action(uid, bconfig.CLAIMPAPER_CLAIM_OTHERS_PAPERS)[0] == 0)):
            return True

        return False

    min_req_acc_n = int(prow[0][5])
    req_acc = resolve_paper_access_right(bconfig.CLAIMPAPER_CLAIM_OWN_PAPERS)
    pid_uid = run_sql("select data from aidPERSONID where tag = %s and personid = %s", ('uid', str(prow[0][1])))
    if len(pid_uid) > 0:
        if (str(pid_uid[0][0]) != str(uid)) and min_req_acc_n > 0:
            req_acc = resolve_paper_access_right(bconfig.CLAIMPAPER_CLAIM_OTHERS_PAPERS)

    if min_req_acc_n < req_acc:
        min_req_acc_n = req_acc

    min_req_acc = resolve_paper_access_right(min_req_acc_n)

    if (acc_authorize_action(uid, min_req_acc)[0] == 0) and (resolve_paper_access_right(min_req_acc) >= min_req_acc_n):
        return True
    else:
        return False


def resolve_paper_access_right(acc):
    '''
    Given a string or an integer, resolves to the corresponding integer or string
    If asked for a wrong/not present parameter falls back to the minimum privilege.
    '''
    access_dict = {bconfig.CLAIMPAPER_VIEW_PID_UNIVERSE: 0,
                  bconfig.CLAIMPAPER_CLAIM_OWN_PAPERS: 25,
                  bconfig.CLAIMPAPER_CLAIM_OTHERS_PAPERS: 50}

    if isinstance(acc, str):
        try:
            return access_dict[acc]
        except:
            return 0

    inverse_dict = dict([[v, k] for k, v in access_dict.items()])
    lower_accs = [a for a in inverse_dict.keys() if a <= acc]
    try:
        return inverse_dict[max(lower_accs)]
    except:
        return bconfig.CLAIMPAPER_VIEW_PID_UNIVERSE

def get_recently_modified_record_ids(date='00-00-00 00:00:00'):
    '''
    Returns the bibrecs with modification date more recent then date, or all
    the bibrecs if no date is specified.
    @param date: date
    '''
    papers = run_sql("select id from bibrec where modification_date > %s",
                     (str(date),))
    if papers:
        bibrecs = [int(i[0]) for i in papers]
        all_bibrecs = perform_request_search(p="")
        bibrecs = list(set(bibrecs).intersection(set(all_bibrecs)))
        min_date = run_sql("select max(modification_date) from bibrec")
    else:
        bibrecs = []
        min_date = run_sql("select now()")
    return [(i,) for i in bibrecs], min_date

def authornames_tables_gc(bunch_size=500):
    '''
    Performs garbage collecting on the authornames tables.
    Potentially really slow.
    '''
    bunch_start = run_sql("select min(id) from aidAUTHORNAMESBIBREFS")
    if len(bunch_start) >= 1:
        bunch_start = int(bunch_start[0][0])
    else:
        return

    abfs_ids_bunch = run_sql("select id,Name_id,bibref from aidAUTHORNAMESBIBREFS limit "
                            + str(bunch_start - 1) + "," + str(bunch_size))
    bunch_start += bunch_size

    while len(abfs_ids_bunch) >= 1:
        bib100list = []
        bib700list = []
        for i in abfs_ids_bunch:
            if i[2].split(':')[0] == '100':
                bib100list.append(i[2].split(':')[1])
            elif i[2].split(':')[0] == '700':
                bib700list.append(i[2].split(':')[1])

        bib100liststr = '( '
        for i in bib100list:
            bib100liststr += "'" + str(i) + "',"
        bib100liststr = bib100liststr[0:len(bib100liststr) - 1] + " )"

        bib700liststr = '( '
        for i in bib700list:
            bib700liststr += "'" + str(i) + "',"
        bib700liststr = bib700liststr[0:len(bib700liststr) - 1] + " )"

        if len(bib100list) >= 1:
            bib10xids = run_sql("select id from bib10x where id in %s"
                                % bib100liststr)
        else:
            bib10xids = []

        if len(bib700list) >= 1:
            bib70xids = run_sql("select id from bib70x where id in %s"
                                % bib700liststr)
        else:
            bib70xids = []

        bib10xlist = []
        bib70xlist = []

        for i in bib10xids:
            bib10xlist.append(str(i[0]))
        for i in bib70xids:
            bib70xlist.append(str(i[0]))

        bib100junk = set(bib100list).difference(set(bib10xlist))
        bib700junk = set(bib700list).difference(set(bib70xlist))

        idsdict = {}
        for i in abfs_ids_bunch:
            idsdict[i[2]] = [i[0], i[1]]

        junklist = []
        for i in bib100junk:
            junklist.append('100:' + i)
        for i in bib700junk:
            junklist.append('700:' + i)

        for junkref in junklist:
            try:
                id_to_remove = idsdict[junkref]

                run_sql("delete from aidAUTHORNAMESBIBREFS where id=%s",
                        (str(id_to_remove[0]),))
                if bconfig.TABLES_UTILS_DEBUG:
                    print ("authornames_tables_gc: idAUTHORNAMESBIBREFS deleting row "
                           + str(id_to_remove))

                authrow = run_sql("select id,Name,bibrefs,db_name from aidAUTHORNAMES where id=%s",
                                  (str(id_to_remove[1]),))

                if len(authrow[0][2].split(',')) == 1:
                    run_sql("delete from aidAUTHORNAMES where id=%s", (str(id_to_remove[1]),))
                    if bconfig.TABLES_UTILS_DEBUG:
                        print "authornames_tables_gc: aidAUTHORNAMES deleting " + str(authrow)
                else:
                    bibreflist = ''
                    for ref in authrow[0][2].split(','):
                        if ref != junkref:
                            bibreflist += ref + ','
                    bibreflist = bibreflist[0:len(bibreflist) - 1]
                    run_sql("update aidAUTHORNAMES set bibrefs=%s where id=%s",
                            (bibreflist, id_to_remove[1]))
                    if bconfig.TABLES_UTILS_DEBUG:
                        print ("authornames_tables_gc: aidAUTHORNAMES updating "
                               + str(authrow) + ' with ' + str(bibreflist))

            except (OperationalError, ProgrammingError, KeyError, IndexError,
                    ValueError, TypeError):
                pass

        abfs_ids_bunch = run_sql("select id,Name_id,bibref from aidAUTHORNAMESBIBREFS limit " +
                            str(bunch_start - 1) + ',' + str(bunch_size))
        bunch_start += bunch_size

def populate_authornames():
    """
    Author names table population from bib10x and bib70x
    Average Runtime: 376.61 sec (6.27 min) for 327k entries
    Should be called only with empty table, then use
    update_authornames_tables_from_paper with the new papers which
    are coming in or modified.
    """
    max_rows_per_run = bconfig.TABLE_POPULATION_BUNCH_SIZE

    if max_rows_per_run == -1:
        max_rows_per_run = 5000

    max100 = run_sql("SELECT COUNT(id) FROM bib10x WHERE tag = '100__a'")
    max700 = run_sql("SELECT COUNT(id) FROM bib70x WHERE tag = '700__a'")

    tables = "bib10x", "bib70x"
    authornames_is_empty_checked = 0
    authornames_is_empty = 1

#    Bring author names from bib10x and bib70x to authornames table

    for table in tables:

        if table == "bib10x":
            table_number = "100"
        else:
            table_number = "700"

        querylimiter_start = 0
        querylimiter_max = eval('max' + str(table_number) + '[0][0]')
        if bconfig.TABLES_UTILS_DEBUG:
            print "\nProcessing %s (%s entries):" % (table, querylimiter_max)
            sys.stdout.write("0% ")
            sys.stdout.flush()

        while querylimiter_start <= querylimiter_max:
            if bconfig.TABLES_UTILS_DEBUG:
                sys.stdout.write(".")
                sys.stdout.flush()
                percentage = int(((querylimiter_start + max_rows_per_run) * 100)
                                   / querylimiter_max)
                sys.stdout.write(".%s%%." % (percentage))
                sys.stdout.flush()

#            Query the Database for a list of authors from the correspondent
#            tables--several thousands at a time
            bib = run_sql("SELECT id, value FROM %s WHERE tag = '%s__a' "
                          "LIMIT %s, %s" % (table, table_number,
                                       querylimiter_start, max_rows_per_run))

            authorexists = None

            querylimiter_start += max_rows_per_run

            for i in bib:

                # For mental sanity, exclude things that are not names...
                # Yes, I know that there are strange names out there!
                # Yes, I read the 40 misconceptions about names.
                # Yes, I know!
                # However, these statistical outlaws are harmful.
                artifact_removal = re.compile("[^a-zA-Z0-9]")
                authorname = ""

                if not i[1]:
                    continue

                test_name = i[1].decode('utf-8')

                if UNIDECODE_ENABLED:
                    test_name = unidecode.unidecode(i[1].decode('utf-8'))

                raw_name = artifact_removal.sub("", test_name)

                if len(raw_name) > 1:
                    authorname = i[1].decode('utf-8')

                if not authorname:
                    continue

                if not authornames_is_empty_checked:
                    authornames_is_empty = run_sql("SELECT COUNT(id) "
                                                   "FROM aidAUTHORNAMES")
                    if authornames_is_empty[0][0] == 0:
                        authornames_is_empty_checked = 1
                        authornames_is_empty = 1

                if not authornames_is_empty:
#                    Find duplicates in the database and append id if
#                    duplicate is found
                    authorexists = run_sql("SELECT id, name, bibrefs, db_name "
                                           "FROM aidAUTHORNAMES "
                                           "WHERE db_name = %s",
                                           (authorname.encode("utf-8"),))


                bibrefs = "%s:%s" % (table_number, i[0])

                if not authorexists:
                    insert_name = ""

                    if len(authorname) > 240:
                        bconfig.LOGGER.warn("\nName too long, truncated to 254"
                                            " chars: %s" % (authorname))
                        insert_name = authorname[0:254]
                    else:
                        insert_name = authorname

                    cnn = create_normalized_name
                    snp = split_name_parts

                    aid_name = authorname

                    if UNIDECODE_ENABLED:
                        aid_name = cnn(snp(unidecode.unidecode(insert_name)))
                        aid_name = aid_name.replace("\"", "")
                    else:
                        aid_name = cnn(snp(insert_name))
                        aid_name = aid_name.replace(u"\u201c", "")
                        aid_name = aid_name.replace(u"\u201d", "")

                    run_sql("INSERT INTO aidAUTHORNAMES VALUES"
                            " (NULL, %s, %s, %s)",
                            (aid_name.encode('utf-8'), bibrefs,
                             insert_name.encode('utf-8')))

                    if authornames_is_empty:
                        authornames_is_empty = 0
                else:
                    if authorexists[0][2].count(bibrefs) >= 0:
                        upd_bibrefs = "%s,%s" % (authorexists[0][2], bibrefs)
                        run_sql("UPDATE aidAUTHORNAMES SET bibrefs = "
                                "%s WHERE id = %s",
                                (upd_bibrefs, authorexists[0][0]))
        if bconfig.TABLES_UTILS_DEBUG:
            sys.stdout.write(" Done.")
            sys.stdout.flush()

def populate_authornames_bibrefs_from_authornames():
    '''
    Populates aidAUTHORNAMESBIBREFS.

    For each entry in aidAUTHORNAMES creates a corresponding entry in aidA.B.
    so it's possible to search
    by bibrec/bibref at a reasonable speed as well and not only by name.
    '''
    nids = run_sql("select id,bibrefs from aidAUTHORNAMES")
    for nid in nids:
        for bibref in nid[1].split(','):
            if bconfig.TABLES_UTILS_DEBUG:
                print ('populate_authornames_bibrefs_from_authornames: Adding: '
                       ' %s %s' % (str(nid[0]), str(bibref)))

            run_sql("insert into aidAUTHORNAMESBIBREFS (Name_id, bibref) "
                    "values (%s,%s)", (str(nid[0]), str(bibref)))

def get_cached_author_page(pageparam):
    '''
    Return cached authorpage
    @param: pageparam (int personid)
    @return (id, 'authorpage_cache', personid, authorpage_html, date_cached)
    '''
            #TABLE: id, tag, identifier, data, date
    caches = run_sql("select id, object_name, object_key, object_value, last_updated \
                      from aidCACHE \
                      where object_name='authorpage_cache' and object_key=%s", (str(pageparam),))
    if len(caches) >= 1:
        return caches[0]
    else:
        return []

def delete_cached_author_page(personid):
    '''
    Deletes from the author page cache the page concerning one person
    '''
    run_sql("delete from aidCACHE where object_name='authorpage_cache' and object_key=%s", (str(personid),))

def update_cached_author_page_timestamp(pageparam):
    '''
    Updates cached author page timestamp
    @param pageparam: int personid
    '''
    #TABLE: id, tag, identifier, data, date
    run_sql("update aidCACHE set last_updated=now() where object_name='authorpage_cache' and object_key=%s", (str(pageparam),))


def update_cached_author_page(pageparam, page):
    '''
    Updates cached author page, deleting old caches for same pageparam
    @param pageparam: int personid
    @param page: string html authorpage
    '''
            #TABLE: id, tag, identifier, data, date
    run_sql("delete from aidCACHE where object_name='authorpage_cache' and object_key=%s", (str(pageparam),))
    run_sql("insert into aidCACHE values (Null,'authorpage_cache',%s,%s,now())", (str(pageparam), str(page)))

def get_user_log(transactionid='', userinfo='', personID='', action='', tag='', value='', comment='', only_most_recent=False):
    '''
    Get user log table entry matching all the given parameters; all of them are optional.
    IF no parameters are given retuns the complete log table
    @param transactionid: id of the transaction
    @param userinfo: user name or identifier
    @param personid: id of the person involved
    @param action: action
    @param tag: tag
    @param value: value
    @param comment: comment
    '''
    sql_query = ('select id,transactionid,timestamp,userinfo,personid,action,tag,value,comment ' +
                 'from aidUSERINPUTLOG where 1 ')
    if transactionid:
        sql_query += ' and transactionid=\'' + str(transactionid) + '\''
    if userinfo:
        sql_query += ' and userinfo=\'' + str(userinfo) + '\''
    if personID:
        sql_query += ' and personid=\'' + str(personID) + '\''
    if action:
        sql_query += ' and action=\'' + str(action) + '\''
    if tag:
        sql_query += ' and tag=\'' + str(tag) + '\''
    if value:
        sql_query += ' and value=\'' + str(value) + '\''
    if comment:
        sql_query += ' and comment=\'' + str(comment) + '\''
    if only_most_recent:
        sql_query += ' order by timestamp desc limit 0,1'
    return run_sql(sql_query)


def collect_personid_papers(person, paper="", limit=""):
    """
    Runs a sql query whit the arguments above.
    If the index is not found the function ignores it.
    """
    if paper:
        index = "use index (`tdf-b`,`ptf-b`)"
        where = "where tag='paper' and data like '%%,%s'" % paper
    else:
        index = "use index (`ptf-b`)"
        where = "where tag='paper'"

    if person:
        person = "and personid in %s" % person
    else:
        person = ""

    if limit:
        limit = "limit %d, %d" % limit

    try:
        query = "select id, personid, tag, data, flag, lcul from aidPERSONID %s %s %s %s" % (index, where, person, limit)
        return run_sql(query)
    except (ProgrammingError, OperationalError):
        query = "select id, personid, tag, data, flag, lcul from aidPERSONID %s %s %s" % (where, person, limit)
        return run_sql(query)


def list_2_SQL_str(items, f):
    """
    Concatenates all items in items to a sql string using f.
    @param items: a set of items
    @param type items: X
    @param f: a function which transforms each item from items to string
    @param type f: X:->str
    @return: "(x1, x2, x3, ... xn)" for xi in items
    @return type: string
    """
    strs = tuple("%s, " % (f(x)) for x in items)
    concat = "".join(strs)
    return "(%s)" % concat[0:len(concat) - 2]


def get_authors_from_paper(paper):
    '''
    selects all author bibrefs by a given papers
    '''
    fullbibrefs100 = run_sql("select id_bibxxx from bibrec_bib10x where id_bibrec=%s", (paper,))
    if len(fullbibrefs100) > 0:
        fullbibrefs100str = list_2_SQL_str(fullbibrefs100, lambda x: str(x[0]))
        return run_sql("select id from bib10x where tag='100__a' and id in %s" % (fullbibrefs100str,))
    return tuple()

def get_coauthors_from_paper(paper):
    '''
    selects all coauthor bibrefs by a given papers
    '''
    fullbibrefs700 = run_sql("select id_bibxxx from bibrec_bib70x where id_bibrec=%s", (paper,))
    if len(fullbibrefs700) > 0:
        fullbibrefs700str = list_2_SQL_str(fullbibrefs700, lambda x: str(x[0]))
        return run_sql("select id from bib70x where tag='700__a' and id in %s" % (fullbibrefs700str,))
    return tuple()

def delete_personid_by_id(ids):
    '''
    Deletes rows in aidPERSONID by id
    '''
    if isinstance(ids, int) or isinstance(ids, long) or isinstance(ids, str):
        return run_sql("delete from aidPERSONID where tag='paper' and id = %s", (str(ids),))
    else:
        delstr = list_2_SQL_str(ids, lambda x: str(x))
        return run_sql("delete from aidPERSONID where tag='paper' and id in %s" % (delstr,))

def get_all_person_ids():
    '''
    Get all the distinct person ids
    '''
    return run_sql("select distinct personid from aidPERSONID")

def get_person_rt_tickets(pid):
    '''
    Returns all the tickets associated to a personID
    @param pid: int
    '''
    return run_sql("select id from aidPERSONID where tag like 'rt%%' and personid=%s", (pid,))

def get_person_claimed_papers(pid):
    '''
    Returns all the papers manually claimed to a person
    @param pid: int
    '''
    return run_sql("select id from aidPERSONID where tag='paper'"
                   " and (flag='2') and personid=%s", (pid,))

def get_person_rejected_papers(pid):
    '''
    Returns all the papers manually rejected to a person
    @param pid: int
    '''
    return run_sql("select id from aidPERSONID where tag='paper'"
                   " and (flag='-2') and personid=%s", (pid,))

def get_deleted_papers():
    return run_sql("select o.id_bibrec from bibrec_bib98x o, \
                    (select i.id as iid from bib98x i \
                    where value = 'DELETED' \
                    and tag like '980__a') as dummy \
                    where o.id_bibxxx = dummy.iid")

def update_flags_in_personid(ident, flag, lcul):
    run_sql("update aidPERSONID set flag=%s,lcul=%s where id=%s", (str(flag), str(lcul), str(ident)))

#PRIVATE SERVICE METHODS
#The following are private methods used by the interfaces to fulfill their needs. The methods
#are hosted here to have a single file which is holding SQL queries.

def _pfap_printmsg(identity, msg):
    if bconfig.TABLES_UTILS_DEBUG:
        print (time.strftime('%H:%M:%S')
           + ' personid_fast_assign_papers '
           + str(identity) + ': '
           + msg)

# bibathorid_maintenance personid_fast_assign_papers private methods:
def _pfap_assign_bibrefrec(i, tab, bibref, bibrec, namestring, pnidl):
    _pfap_printmsg('BibrefAss:  ' + str(i), 'Assigning ' + str(bibref) + ' ' + str(bibrec)
                   + ' ' + str(namestring))
    name_parts = split_name_parts(namestring)
    pid_names_rows = run_sql("select personid,data from aidPERSONID where tag='gathered_name'"
                             " and data like %s ", (name_parts[0] + ',%',))
    pid_names_dict = {}
    for pid in pid_names_rows:
        pid_names_dict[pid[1]] = pid[0]
    del pid_names_rows

    names_comparison_list = []
    for name in pid_names_dict.keys():
        names_comparison_list.append([name, compare_names(name, namestring)])
    names_comparison_list = sorted(names_comparison_list, key=lambda x: x[1], reverse=True)

    _pfap_printmsg('BibrefAss:  ' + str(i),
        ' Top name comparison list against %s: %s' % (namestring, str(names_comparison_list[0:3])))

    if len(names_comparison_list) > 0 and names_comparison_list[0][1] > bconfig.PERSONID_FAST_ASSIGN_PAPERS_MIN_NAME_TRSH:
        _pfap_printmsg('BibrefAss:  ' + str(i),
                ' Assigning to the best fit: %s' % str(pid_names_dict[names_comparison_list[0][0]]))
        run_sql("insert into aidPERSONID (personid,tag,data,flag,lcul) values "
                "(%s,'paper',%s,'0','0')",
                (str(pid_names_dict[names_comparison_list[0][0]]), tab +
                                ':' + str(bibref) + ',' + str(bibrec)))
        _pfap_printmsg('BibrefAss:  ' + str(i), ' update names string set of %s'
            % str([[pid_names_dict[names_comparison_list[0][0]]]]))
        update_personID_names_string_set([[pid_names_dict[names_comparison_list[0][0]]]],
                                         wait_finished=True)
        update_personID_canonical_names([[pid_names_dict[names_comparison_list[0][0]]]])
    else:
        _pfap_printmsg('BibrefAss:  ' + str(i), 'Creating a new person...')
        pnidl.acquire()
        personid_count = run_sql("SELECT COUNT( DISTINCT personid ) FROM  `aidPERSONID` WHERE 1")[0][0]

        if personid_count > 0:
            personid = run_sql("select max(personid)+1 from aidPERSONID")[0][0]
        else:
            personid = 1

        run_sql("insert into aidPERSONID (personid,tag,data,flag,lcul) values "
                "(%s,'paper',%s,'0','0')",
                (personid, tab + ':' + str(bibref) + ',' + str(bibrec)))
        pnidl.release()
        _pfap_printmsg('BibrefAss:  ' + str(i), 'Released new pid lock')
        _pfap_printmsg('BibrefAss:  ' + str(i), ' update names string set of %s' % str([[personid]]))
        update_personID_names_string_set([[personid]], wait_finished=True)
        update_personID_canonical_names([[personid]])


def pfap_assign_paper_iteration(i, bibrec, atul, personid_new_id_lock):
    '''
    bibrec = 123
    '''
    _pfap_printmsg('Assigner:  ' + str(i), 'Starting on paper: %s' % bibrec)
    _pfap_printmsg('Assigner:  ' + str(i), 'Updating authornames table')
    atul.acquire()
    update_authornames_tables_from_paper([[bibrec]])
    atul.release()
    _pfap_printmsg('Assigner:  ' + str(i), 'Released authornames table')

    b100 = run_sql("select b.id,b.value from bib10x as b, "
                   "bibrec_bib10x as a where b.id=a.id_bibxxx and "
                   "b.tag=%s and a.id_bibrec=%s", ('100__a', bibrec))
    b700 = run_sql("select b.id,b.value from bib70x as b, "
                   "bibrec_bib70x as a where b.id=a.id_bibxxx and "
                   "b.tag=%s and a.id_bibrec=%s", ('700__a', bibrec))

    _pfap_printmsg('Assigner:  ' + str(i),
                   'Found: %s 100: and %s 700:' % (len(b100), len(b700)))

    for bibref in b100:
        present = run_sql("select count(data)>0  from aidPERSONID where "
                          "tag='paper' and data =%s and flag <> '-2'",
                          ('100:' + str(bibref[0]) + ',' + str(bibrec),))[0][0]
        if not present:
            _pfap_printmsg('Assigner:  ' + str(i), 'Found: 100:%s,%s not assigned,'
                           ' assigning...' % (str(bibref[0]), str(bibrec)))
            _pfap_assign_bibrefrec(i, '100', bibref[0], bibrec, bibref[1], personid_new_id_lock)
    for bibref in b700:
        present = run_sql("select count(data)>0  from aidPERSONID where "
                          "tag='paper' and data =%s",
                          ('700:' + str(bibref[0]) + ',' + str(bibrec),))[0][0]
        if not present:
            _pfap_printmsg('Assigner:  ' + str(i), 'Found: 700:%s,%s not assigned, '
                           'assigning...' % (str(bibref[0]), str(bibrec)))
            _pfap_assign_bibrefrec(i, '700', bibref[0], bibrec, bibref[1], personid_new_id_lock)

    _pfap_printmsg('Assigner:  ' + str(i), 'Done with: %s' % bibrec)


#bibauthorid_maintenance personid update private methods
def update_personID_canonical_names(persons_list=None, overwrite=False, suggested='',
                                     really_update_all=False):
    '''
    Updates the personID table creating or updating canonical names for persons
    @param: persons_list: persons to consider for the update  (('1'),)
    @param: overwrite: if to touch already existing canonical names
    @param: suggested: string to suggest a canonical name for the person
    '''
    use_index = True

    if not persons_list and really_update_all:
        persons_list = run_sql('select distinct personid from aidPERSONID')
    elif not persons_list:
        if bconfig.TABLES_UTILS_DEBUG:
            print "No person in persons list. Skipping"
        return

    for pid in persons_list:
        current_canonical = ""

        try:
            current_canonical = run_sql("select data from aidPERSONID use index (`ptf-b`) where "
                                        "personid=%s and tag=%s", (pid[0], 'canonical_name'))
        except (ProgrammingError, OperationalError):
            current_canonical = run_sql("select data from aidPERSONID where personid=%s and tag=%s",
                                                                        (pid[0], 'canonical_name'))
            use_index = False

        if (not overwrite) and len(current_canonical) > 0:
            if bconfig.TABLES_UTILS_DEBUG:
                print "U_PID_CANONICALNAMES: NOT updating canonical names an not overwrite and current_canonical for ", pid
        else:
            if bconfig.TABLES_UTILS_DEBUG:
                print "U_PID_CANONICALNAMES: updating canonical name for ", pid
            names = []

            if use_index:
                names = run_sql("select data,flag from aidPERSONID use index (`ptf-b`) where "
                                "personid=%s and tag=%s", (pid[0], 'gathered_name'))
            else:
                names = run_sql("select data,flag from aidPERSONID where personid=%s and tag=%s",
                                                                        (pid[0], 'gathered_name'))

            names = sorted(names, key=lambda k: k[1], reverse=True)
            if len(names) < 1 and not suggested:
                if bconfig.TABLES_UTILS_DEBUG:
                    print "No gathered names and no suggested. skipping."
                continue
            else:
                if suggested:
                    canonical_name = suggested
                else:
                    canonical_name = create_canonical_name(names[0][0])

                run_sql("delete from aidPERSONID where personid=%s and tag=%s", (pid[0],
                                                                                  'canonical_name'))
                existing_cnames = []

                if use_index:
                    existing_cnames = run_sql("select data from aidPERSONID "
                                              "use index (`tdf-b`) where tag=%s and"
                                              " data like %s", ('canonical_name',
                                                                str(canonical_name) + '%'))
                else:
                    existing_cnames = run_sql("select data from aidPERSONID where "
                                              "tag=%s and data like %s", ('canonical_name',
                                                                        str(canonical_name) + '%'))

                max_idx = 0

                for i in existing_cnames:
                    this_cid = 0

                    if i[0].count("."):
                        this_cid = i[0].split(".")[-1]

                    max_idx = max(max_idx, int(this_cid))

                canonical_name = canonical_name + '.' + str(max_idx + 1)
                run_sql("insert into aidPERSONID (personid,tag,data) values (%s,%s,%s) ",
                         (pid[0], 'canonical_name', canonical_name))
    close_connection()


def update_personID_names_string_set(PIDlist=None, really_update_all=False, wait_finished=False,
                                     single_threaded=False):
    '''
    Updates the personID table with the names gathered from documents
    @param: list of pids to consider, if omitted performs an update on the entire db
    @type: tuple of tuples

    Gets all the names associated to the bibref/bibrec couples of the person and builds a set of
    names, counting the occurrencies. The values are store in the gathered_name/flag fields of each
    person.
    The gathering of names is an expensive operation for the database (many joins), so the operation
    is threaded so to have as many parallell queries as possible.
    '''
    local_dbg = False

    if (not PIDlist or len(PIDlist) == 0):
        if really_update_all:
            PIDlist = run_sql('SELECT DISTINCT `personid` FROM `aidPERSONID`')
            close_connection()
        else:
            return

    class names_gatherer(threading.Thread):
        def __init__ (self, pid):
            threading.Thread.__init__(self)
            self.pid = pid
            self.pstr = ''
            self.person_papers = None
            self.namesdict = None
            self.needs_update = None
            self.current_namesdict = None
            self.pname = None


        def run(self):
            self.namesdict = dict()
            use_index = True

            try:
                self.person_papers = run_sql("select data from `aidPERSONID` use index (`ptf-b`)"
                                             " where tag=\'paper\' and "
                                             " flag >= \'-1\' and PersonID=%s",
                                                (str(self.pid[0]),))
            except (OperationalError, ProgrammingError):
                self.person_papers = run_sql("select data from `aidPERSONID` where"
                                             " tag=\'paper\' and "
                                             " flag >= \'-1\' and PersonID=%s",
                                                (str(self.pid[0]),))
                use_index = False

            for p in self.person_papers:
                self.pname = run_sql("select Name from aidAUTHORNAMES where id = "
                 "(select Name_id from aidAUTHORNAMESBIBREFS where bibref = %s)",
                                    (str(p[0].split(',')[0]),))
                if len(self.pname) > 0:
                    if self.pname[0][0] not in self.namesdict:
                        self.namesdict[self.pname[0][0]] = 1
                    else:
                        self.namesdict[self.pname[0][0]] += 1

            if use_index:
                self.current_namesdict = dict(run_sql("select data,flag from aidPERSONID "
                                                      "use index (`ptf-b`) where personID=%s "
                                        "and tag=\'gathered_name\'", (str(self.pid[0]),)))
            else:
                self.current_namesdict = dict(run_sql("select data,flag from aidPERSONID "
                                                      "where personID=%s "
                                        "and tag=\'gathered_name\'", (str(self.pid[0]),)))


            self.needs_update = False
            if self.current_namesdict != self.namesdict:
                self.needs_update = True
            else:
                for i in self.namesdict.iteritems():
                    if i[1] != self.current_namesdict[i[0]]:
                        self.needs_update = True
                        if bconfig.TABLES_UTILS_DEBUG and local_dbg:
                            pass
#                            sys.stdout.write(str(self.pid) + str(i[1]) +
#                                ' differs  from ' + str(self.current_namesdict[i[0]]))
#                            sys.stdout.flush()

            if self.needs_update:
                if bconfig.TABLES_UTILS_DEBUG and local_dbg:
                    pass
#                    sys.stdout.write(str(self.pid) + ' updating!')
#                    sys.stdout.flush()
                run_sql("delete from `aidPERSONID` where PersonID=%s and tag=%s",
                         (str(self.pid[0]), 'gathered_name'))

                sqlquery = 'insert into aidPERSONID (PersonID, tag, data, flag) values '
                values = ''.join(['("%s","%s","%s","%s"),' % (str(self.pid[0]),
                                'gathered_name', str(name),
                                str(self.namesdict[name])) for name in self.namesdict])
                values = values[0:len(values) - 1]
                sqlquery = sqlquery + values
                run_sql(sqlquery)
                if bconfig.TABLES_UTILS_DEBUG and local_dbg:
                    print('Update_personid_names_string_set: thread finished,'
                          ' going to close connection on ' + str(self.pid))
            close_connection()

    class starter(threading.Thread):
        def __init__ (self, single_threaded=False):
            threading.Thread.__init__(self)
            self.ST = single_threaded

        def run(self):
            if bconfig.TABLES_UTILS_DEBUG and local_dbg:
                print('Update_personid_names_string_set: spawning threads for ' + str(PIDlist))
            if self.ST:
                for pid in PIDlist:
                    if bconfig.TABLES_UTILS_DEBUG and local_dbg:
                        print('Update_personid_names_string_set: spawning ST thread on ' + str(pid))
                    current = names_gatherer(pid)
                    current.start()
                    current.join()
            else:
                wks = []
                for pid in PIDlist:
                    current = names_gatherer(pid)
                    if bconfig.TABLES_UTILS_DEBUG and local_dbg:
                        print('Update_personid_names_string_set: spawning MT thread on ' + str(pid))
                    current.start()
                    wks.append(current)
                    if len(wks) > bconfig.PERSONID_SQL_MAX_THREADS:
                        for t in list(wks):
                            t.join()
                            wks.remove(t)
                for t in list(wks):
                    t.join()
                    wks.remove(t)
                if bconfig.TABLES_UTILS_DEBUG and local_dbg:
                    print('Update_personid_names_string_set: recollected all MT threads ')

    thread = starter(single_threaded)
    if bconfig.TABLES_UTILS_DEBUG and local_dbg:
        print('Update_personid_names_string_set on ' + str(PIDlist) + '\n')
    thread.start()
    if bconfig.TABLES_UTILS_DEBUG and local_dbg:
        print('Update_personid_names_string_set main thread returned on ' + str(PIDlist) + '\n')
    if wait_finished:
        thread.join()
    if bconfig.TABLES_UTILS_DEBUG and local_dbg:
        print('Update_personid_names_string_set FINISHED on ' + str(PIDlist) + '\n')


def update_authornames_tables_from_paper(papers_list=None):
    """
    Updates the authornames tables with the names on the given papers list
    @param papers_list: list of the papers which have been updated (bibrecs) ((1,),)

    For each paper of the list gathers all names, bibrefs and bibrecs to be added to aidAUTHORNAMES
    table, taking care of updating aidA.B. as well

    NOTE: update_authornames_tables_from_paper: just to remember: get record would be faster but
        we don't have the bibref there,
        maybe there is a way to rethink everything not to use bibrefs? How to address
        authors then?
    """


    def update_authornames_tables(name, bibref):
        '''
        Update the tables for one bibref,name touple
        '''
        authornames_row = run_sql("select id,Name,bibrefs,db_name from aidAUTHORNAMES where db_name like %s",
                            (str(name),))
        authornames_bibrefs_row = run_sql("select id,Name_id,bibref from aidAUTHORNAMESBIBREFS "
                                        "where bibref like %s", (str(bibref),))

#: update_authornames_tables: if i'm not wrong there should always be only one result; will be checked further on
        if ((len(authornames_row) > 1) or (len(authornames_bibrefs_row) > 1) or
            (len(authornames_row) < len(authornames_bibrefs_row))):
            if bconfig.TABLES_UTILS_DEBUG:
                print "update_authornames_tables: More then one result or missing authornames?? Something is wrong, not updating" + str(authornames_row) + str(authornames_bibrefs_row)
                return

        if len(authornames_row) == 1:
#            we have an hit for the name string; check if there is the 'new' bibref associated,
#            if yes there is nothing to do, otherwise shold add it here and in the ANbibrefs table
            if authornames_row[0][2].count(bibref) < 1:
                if bconfig.TABLES_UTILS_DEBUG:
                    print 'update_authornames_tables: Adding new bibref to ' + str(authornames_row) + ' ' + str(name) + ' ' + str(bibref)
                run_sql("update aidAUTHORNAMES set bibrefs=%s where id=%s",
                            (authornames_row[0][2] + ',' + str(bibref), authornames_row[0][0]))
                if len(authornames_bibrefs_row) < 1:
#                we have to add the bibref to the name, would be strange if it would be already there
                    run_sql("insert into aidAUTHORNAMESBIBREFS  (Name_id,bibref) values (%s,%s)",
                        (authornames_row[0][0], str(bibref)))
            else:
                if bconfig.TABLES_UTILS_DEBUG:
                    print 'update_authornames_tables: Nothing to add to ' + str(authornames_row) + ' ' + str(name) + ' ' + str(bibref)


        else:
#@NOTE: update_authornames_tables: we don't have the name string in the db: the name associated to the bibref is changed
#            or this is a new name? Experimenting with bibulpload looks like if a name on a paper changes a new bibref is created;
#
            if len(authornames_bibrefs_row) == 1:
#               If len(authornames_row) is zero but we have a row in authornames_bibrefs_row means that
#               the name string is changed, somehow!
                if bconfig.TABLES_UTILS_DEBUG:
                    print 'update_authornames_tables: The name associated to the bibref is changed?? ' + str(name) + ' ' + str(bibref)

            else:
                artifact_removal = re.compile("[^a-zA-Z0-9]")
                authorname = ""

                test_name = name.decode('utf-8')

                if UNIDECODE_ENABLED:
                    test_name = unidecode.unidecode(name.decode('utf-8'))

                raw_name = artifact_removal.sub("", test_name)

                if len(raw_name) > 1:
                    authorname = name.decode('utf-8')

                if len(raw_name) > 1:
                    dbname = authorname
                else:
                    dbname = 'Error in name parsing!'

                clean_name = create_normalized_name(split_name_parts(name))
                authornamesid = run_sql("insert into aidAUTHORNAMES (Name,bibrefs,db_name) values (%s,%s,%s)",
                                (clean_name, str(bibref), dbname))
                run_sql("insert into aidAUTHORNAMESBIBREFS  (Name_id,bibref) values (%s,%s)",
                        (authornamesid, str(bibref)))
                if bconfig.TABLES_UTILS_DEBUG:
                    print 'update_authornames_tables: Created new name ' + str(authornamesid) + ' ' + str(name) + ' ' + str(bibref)

    tables = [['bibrec_bib10x', 'bib10x', '100__a', '100'],
              ['bibrec_bib70x', 'bib70x', '700__a', '700']]

    if not papers_list:
        papers_list = run_sql("select id from bibrec")
    for paper in papers_list:
        for table in tables:
            sqlstr = "select id_bibxxx from %s where id_bibrec=" % table[0]
            bibrefs = run_sql(sqlstr + "%s", (str(paper[0]),))
            for ref in bibrefs:
                sqlstr = "select value from %s where tag='%s' and id=" % (table[1], table[2])
                name = run_sql(sqlstr + "%s", (str(ref[0]),))
                if len(name) >= 1:
                    update_authornames_tables(name[0][0], table[3] + ':' + str(ref[0]))

def check_table(table=""):
    '''
    This function will check if a table is present in the database.
    If no table is specified, the function will return all tables.
   '''
    if table:
        return [name[0] for name in run_sql("show tables like %s", (table,))]
    else:
        return [name[0] for name in run_sql("show tables")]

def create_probability_table():
    run_sql("create table aidPROBCACHE( "
            "    cluster VARCHAR(256), "
            "    bibmap MEDIUMBLOB, "
            "    matrix LONGBLOB "
            ")")

def load_bibmap_and_matrix_from_db(last_name):
    row = run_sql("select bibmap, matrix from aidPROBCACHE where cluster like %s", (last_name,))
    if len(row) == 0:
        return (None, None)
    elif len(row) == 1:
        return (deserialize_via_marshal(row[0][0]), deserialize_via_marshal(row[0][1]))
    else:
        raise AssertionError("aidPROBCACHE is corrupted")

def save_bibmap_and_matrix_to_db(last_name, bibmap, matrix):
    run_sql("delete from aidPROBCACHE where cluster like %s", (last_name,))
    run_sql("insert low_priority "
            "into aidPROBCACHE "
            "set cluster = %s, "
            "bibmap = %s, "
            "matrix = %s",
            (last_name, serialize_via_marshal(bibmap), serialize_via_marshal(matrix)))

def personid_get_recids_affected_since(last_timestamp):
    '''
    Returns a list of recids which have been manually changed since timestamp
    @TODO: extend the system to track and signal even automatic updates (unless a full reindex is
        acceptable in case of magic automatic update)
    @param: last_timestamp: last update, datetime.datetime
    '''
    vset = set()
    values = run_sql("select value from aidUSERINPUTLOG where timestamp > %s", (last_timestamp,))
    for v in values:
        if ',' in v[0] and ':' in v[0]:
            vset.add(v[0].split(',')[1])

    pids = run_sql("select distinct personid from aidUSERINPUTLOG where  timestamp > %s", (last_timestamp,))
    pidlist = [p[0] for p in pids if p[0] >= 0]
    values = []
    if len(pidlist) > 1:
        values = run_sql("select data from aidPERSONID where tag='paper' and personid in %s", (pidlist,))
    elif len(pidlist) == 1:
        values = run_sql("select data from aidPERSONID where tag='paper' and personid = %s", (pidlist[0],))
    for v in values:
        if ',' in v[0] and ':' in v[0]:
            vset.add(v[0].split(',')[1])
    # transform output to list of integers, since we are returning recIDs:
    return [int(recid) for recid in list(vset)]


def get_all_paper_records(pid):
    return run_sql("SELECT data FROM `aidPERSONID` WHERE tag = 'paper' AND personid = %s", (str(pid),))


def create_new_person_from_uid(uid):
    #creates a new person
    pid = run_sql("select max(personid) from aidPERSONID")[0][0]

    if pid:
        try:
            pid = int(pid)
        except (ValueError, TypeError):
            pid = -1
        pid += 1

    set_person_data(pid, 'uid', str(uid))
    return pid


def confirm_papers_to_person(pid, papers, gather_list, user_level=0):
    '''
    Confirms the relationship between pid and paper, as from user input.
    @param pid: id of the person
    @type pid: ('2',)
    @param papers: list of papers to confirm
    @type papers: (('100:7531,9024',),)
    @param gather_list: list to store the pids to be updated rather than
    calling update_personID_names_string_set
    @typer gather_list: set([('2',), ('3',)])
    '''
    #expects a pid ('2',)
    #and a lst of papers (('100:7531,9024',),)

#    class names_gatherer(Thread):
#        def __init__(self, pid):
#            Thread.__init__(self)
#            self.pid = pid
#
#        def run(self):
#            update_personID_names_string_set(self.pid)
#            close_connection()

    updated_pids = set([pid])
    for p in papers:
        old_owners = []

        try:
            old_owners = run_sql("select personid from aidPERSONID use index (`tdf-b`) where"
                                 " tag=%s and data=%s", ('paper', str(p[0]),))
        except (OperationalError, ProgrammingError):
            old_owners = run_sql("select personid from aidPERSONID where tag=%s and data=%s",
                                 ('paper', str(p[0]),))

        updated_pids |= set((str(owner[0]),) for owner in old_owners)

        run_sql("delete from aidPERSONID where tag=%s and data=%s", ('paper', str(p[0]),))
        run_sql("insert into aidPERSONID (PersonID, tag, data, flag, lcul)"
                " values (%s,'paper',%s,'2', %s)",
                (str(pid[0]), str(p[0]), user_level))

    if gather_list != None:
        gather_list |= updated_pids
    else:
        update_personID_names_string_set(tuple(updated_pids))
    update_personID_canonical_names([pid])


def get_all_names_from_personid():
    return run_sql("SELECT personid, data "
                   "FROM aidPERSONID "
                   "WHERE tag LIKE %s",
                    ("gathered_name",))


def get_grouped_records(bibrefrec, *args):
    '''
    By a given bibrefrec: mark:ref,rec this function will scan
    bibmarkx table and extract all records with tag in argc, which
    are grouped togerther with this bibrec.

    Returns a dictionary with { tag : [extracted_values] }
    if the values is not found.

    @type bibrefrec: (mark(int), ref(int), rec(int))
    '''
    table, ref, rec = bibrefrec

    target_table = "bib%sx" % (str(table)[:-1])
    mapping_table = "bibrec_%s" % target_table

    group_id = run_sql("SELECT field_number "
                       "FROM %s "
                       "WHERE id_bibrec = %d "
                       "AND id_bibxxx = %d" %
                       (mapping_table, rec, ref))

    if len(group_id) == 0:
        # unfortunately the mapping is not found, so
        # we cannot find anything
        return dict((arg, []) for arg in args)
    elif len(group_id) == 1:
        # All is fine
        field_number = group_id[0][0]
    else:
        # sounds bad, but ignore the error
        field_number = group_id[0][0]

    grouped = run_sql("SELECT id_bibxxx "
                      "FROM %s "
                      "WHERE id_bibrec = %d "
                      "AND field_number = %d" %
                      (mapping_table, rec, int(field_number)))
    grouped = list_2_SQL_str([gr[0] for gr in grouped], lambda x: str(x))
    if len(grouped) == 0:
        raise AssertionError("At least the given bibrefrec should be in the group")

    ret = {}
    for arg in args:
        qry = run_sql("SELECT value "
                      "FROM %s "
                      "WHERE tag LIKE '%s' "
                      "AND id IN %s" %
                      (target_table, arg, grouped))
        ret[arg] = [q[0] for q in qry]

    return ret


def get_name_by_bibrecref(bib):
    '''
    @param bib: bibrefref
    @type bib: (mark, bibref, bibrec)
    '''
    table = "bib%sx" % (str(bib[0])[:-1])
    refid = bib[1]
    ret = run_sql("select value from %s where id = %s" % (table, refid))
    if len(ret) != 1:
        raise AssertionError("Invalid input.")
    return ret[0][0]


def get_collaboration(bibrec):
    bibxxx = run_sql("select id_bibxxx from bibrec_bib71x where 'bibrec' = %s", (str(bibrec),))

    if len(bibxxx) == 0:
        return ()

    bibxxx = list_2_SQL_str(bibxxx, lambda x: str(x[0]))

    ret = run_sql("select value from bib71x where id in %s and tag like '%s'", (bibxxx, "710__g"))
    if len(ret) != 1:
        raise AssertionError("Invalid input.")
    return ret[0][0]


def get_all_authors(bibrec):
    bibxxx_1 = run_sql("select id_bibxxx from bibrec_bib10x where id_bibrec = %s", (str(bibrec),))
    bibxxx_7 = run_sql("select id_bibxxx from bibrec_bib70x where id_bibrec = %s", (str(bibrec),))

    if bibxxx_1:
        bibxxxs_1 = list_2_SQL_str(bibxxx_1, lambda x: str(x[0]))
        authors_1 = run_sql("select value from bib10x where tag = '%s' and id in %s" % ('100__a', bibxxxs_1,))
    else:
        authors_1 = []

    if bibxxx_7:
        bibxxxs_7 = list_2_SQL_str(bibxxx_7, lambda x: str(x[0]))
        authors_7 = run_sql("select value from bib70x where tag = '%s' and id in %s" % ('700__a', bibxxxs_7,))
    else:
        authors_7 = []

    return [a[0] for a in authors_1] + [a[0] for a in authors_7]
