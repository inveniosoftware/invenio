# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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
    bibauthorid_frontinterface
    This file aims to filter and modify the interface given by
    bibauthorid_bdinterface in order to make it usable by the 
    frontend so to keep it as clean as possible.
'''

import bibauthorid_dbinterface as dbinter
from bibauthorid_dbinterface import set_person_data                    #emitting
from bibauthorid_dbinterface import get_person_data                    #emitting
from bibauthorid_dbinterface import get_personid_from_uid              #emitting
from bibauthorid_dbinterface import get_bibrefs_from_name_string       #emitting
from bibauthorid_dbinterface import create_new_person                  #emitting
from bibauthorid_dbinterface import update_request_ticket              #emitting
from bibauthorid_dbinterface import delete_request_ticket              #emitting
from bibauthorid_dbinterface import find_personIDs_by_name_string      #emitting
from bibauthorid_dbinterface import get_bibref_modification_status     #emitting
from bibauthorid_dbinterface import get_canonical_id_from_personid     #emitting
from bibauthorid_dbinterface import get_papers_status                  #emitting
from bibauthorid_dbinterface import get_person_db_names_count          #emitting
from bibauthorid_dbinterface import get_person_id_from_canonical_id    #emitting
from bibauthorid_dbinterface import get_person_names_count             #emitting
from bibauthorid_dbinterface import get_person_names_set               #emitting
from bibauthorid_dbinterface import get_person_papers                  #emitting
from bibauthorid_dbinterface import get_persons_with_open_tickets_list #emitting
from bibauthorid_dbinterface import get_possible_personids_from_paperlist    #emitting
from bibauthorid_dbinterface import get_request_ticket                 #emitting
from bibauthorid_dbinterface import insert_user_log                    #emitting
from bibauthorid_dbinterface import person_bibref_is_touched           #emitting
from bibauthorid_dbinterface import reject_papers_from_person          #emitting
from bibauthorid_dbinterface import reset_papers_flag                  #emitting
from bibauthorid_dbinterface import user_can_modify_data               #emitting
from bibauthorid_dbinterface import user_can_modify_paper              #emitting
from bibauthorid_dbinterface import update_personID_canonical_names    #emitting
from bibauthorid_dbinterface import update_personID_names_string_set   #emitting
from bibauthorid_dbinterface import get_possible_bibrecref             #emitting
from bibauthorid_dbinterface import resolve_paper_access_right         #emitting
from bibauthorid_dbinterface import delete_cached_author_page          #emitting
from bibauthorid_dbinterface import confirm_papers_to_person           #emitting

def get_bibrefrec_name_string(bibref):
    '''
    Returns the name string associated to a name string
    @param bibref: bibrefrec '100:123,123'
    @return: string
    '''
    name = ""
    ref = ""

    if not ((bibref and isinstance(bibref, str) and bibref.count(":"))):
        return name

    if bibref.count(","):
        try:
            ref = bibref.split(",")[0]
        except (ValueError, TypeError, IndexError):
            return name
    else:
        ref = bibref

    dbname = dbinter.get_bibref_name_string(((ref,),))

    if dbname:
        name = dbname

    return name


def add_person_paper_needs_manual_review(pid, bibrec):
    '''
    Adds to a person a paper which needs manual review before bibref assignment
    @param pid: personid, int
    @param bibrec: the bibrec, int
    '''
    dbinter.set_person_data(pid, 'paper_needs_bibref_manual_confirm', bibrec)


def get_person_papers_to_be_manually_reviewed(pid):
    '''
    Returns the set of papers awaiting for manual review for a person for bibref assignment
    @param pid: the personid, int
    '''
    return dbinter.get_person_data(pid, 'paper_needs_bibref_manual_confirm')


def del_person_papers_needs_manual_review(pid, bibrec):
    '''
    Deletes from the set of papers awaiting for manual review for a person
    @param pid: personid, int
    @param bibrec: the bibrec, int
    '''
    dbinter.del_person_data(person_id=pid, tag='paper_needs_bibref_manual_confirm', value=str(bibrec))


def set_processed_external_recids(pid, recid_list_str):
    '''
    Set processed external recids
    @param pid: pid
    @param recid_list_str: str
    '''
    dbinter.del_person_data(person_id=pid, tag='processed_external_recids')
    dbinter.set_person_data(pid, "processed_external_recids", recid_list_str)


def assign_person_to_uid(uid, pid):
    '''
    Assigns a person to a userid. If person already assigned to someone else, create new person.
    Returns the peron id assigned.
    @param uid: user id, int
    @param pid: person id, int, if -1 creates new person.
    @return: pid int
    '''
    if pid == -1:
        pid = dbinter.create_new_person_from_uid(uid)
        return pid
    else:
        current_uid = dbinter.get_person_data(pid, 'uid')
        if len(current_uid) == 0:
            dbinter.set_person_data(pid, 'uid', str(uid))
            return pid
        else:
            pid = dbinter.create_new_person_from_uid(uid)
            return pid


def assign_uid_to_person(uid, pid, create_new_pid=False, force=False):
    '''
    Assigns a userid to a person, counterchecknig with get_personid_from_uid.
    If uid has already other person returns other person.
    If create_new_pid and the pid is -1 creates a new person.
    If force, deletes any reference to that uid from the tables and assigns to pid, if pid wrong
    (less then zero) returns -1.
    @param uid: user id, int
    @param pid: person id, int
    @param create_new_pid: bool
    @param force, bool
    '''

    if force and pid >= 0:
        dbinter.del_person_data(tag='uid', value=str(uid))
        dbinter.set_person_data(pid, 'uid', str(uid))
        return pid
    elif force and pid < 0:
        return -1

    current = dbinter.get_personid_from_uid(((uid,),))

    if current[1]:
        return current[0][0]
    else:
        if pid >= 0:
            cuid = dbinter.get_person_data(pid, 'uid')
            if len(cuid) > 0:
                if str(cuid[0][1]) == str(uid):
                    return pid
                else:
                    if create_new_pid:
                        dbinter.create_new_person_from_uid(uid)
                    else:
                        return -1
            else:
                dbinter.set_person_data(pid, 'uid', str(uid))
                return pid
        else:
            if create_new_pid:
                dbinter.create_new_person_from_uid(uid)
            else:
                return -1


def get_personid_status_cacher():
    '''
    Returns a DataCacher object describing the status of the pid table content

    @return: DataCacher Object
    @rtype: DataCacher
    '''
    if not dbinter.DATA_CACHERS:
        dbinter.DATA_CACHERS.append(dbinter.PersonIDStatusDataCacher())

    return dbinter.DATA_CACHERS[0]


def get_processed_external_recids(pid):
    '''
    Returns processed external recids
    @param pid: pid
    @return: [str]
    '''
    db_data = dbinter.get_person_data(pid, "processed_external_recids")
    recid_list_str = ''

    if db_data and db_data[0] and db_data[0][1]:
        recid_list_str = db_data[0][1]

    return recid_list_str


def get_all_personids_recs(pid):
    records = dbinter.get_all_paper_records(pid)
    return [int(rec[0].split(',')[1]) for rec in records]


