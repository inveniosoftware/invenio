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
    bibauthorid_frontinterface
    This file aims to filter and modify the interface given by
    bibauthorid_bdinterface in order to make it usable by the
    frontend so to keep it as clean as possible.
'''
import re
from invenio.bibauthorid_name_utils import most_relevant_name
from invenio.bibauthorid_name_utils import split_name_parts  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_name_utils import soft_compare_names
from invenio.bibauthorid_name_utils import create_normalized_name  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_search_engine import find_personids_by_name
import invenio.bibauthorid_dbinterface as dbinter
from invenio.bibauthorid_name_utils import generate_last_name_cluster_str as get_surname
from invenio.bibauthorid_name_utils import clean_string
from invenio.textutils import translate_to_ascii
from cgi import escape

# Well this is bad, BUT otherwise there must 100+ lines
# of the form from dbinterface import ...  # emitting
from invenio.bibauthorid_dbinterface import *  # pylint:  disable-msg=W0614

canonical_name_type = re.compile("\S*[.](\d)+$")


def set_person_data(person_id, tag, value, user_level=None):
    '''
    @param person_id:
    @type person_id: int
    @param tag:
    @type tag: string
    @param value:
    @type value: string
    @param user_level:
    @type user_level: int
    '''
    old = dbinter.get_author_data(person_id, tag)
    old_data = [tup[0] for tup in old]
    if value not in old_data:
        dbinter.add_author_data(person_id, tag, value, opt2=user_level)


def get_persons_data(person_id_list, tag=None):
    '''
    @param person_id_list:
    @type person_id_list: list
    @param tag:
    @type tag: string
    @return: persons_data
    @rtype: dict(tuple,)
    '''
    persons_data = dict()

    for person_id in person_id_list:
        res = dbinter.get_author_data(person_id, tag)
        persons_data[person_id] = res

    return persons_data


def del_person_data(tag, person_id=None, value=None):
    dbinter.remove_author_data(tag, person_id, value)


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

    table, ref = ref.split(":")
    dbname = get_name_by_bibref((int(table), int(ref)))

    if dbname:
        name = dbname

    return name


def add_person_paper_needs_manual_review(pid, bibrec):
    '''
    Adds to a person a paper which needs manual review before bibref assignment
    @param pid: personid, int
    @param bibrec: the bibrec, int
    '''
    set_person_data(pid, 'paper_needs_bibref_manual_confirm', bibrec)


def get_person_papers_to_be_manually_reviewed(pid):
    '''
    Returns the set of papers awaiting for manual review for a person for bibref assignment
    @param pid: the personid, int
    '''
    res = get_persons_data([pid], 'paper_needs_bibref_manual_confirm')
    if res[pid]:
        return [res[pid][0][1], res[0][0]]
    return list()


def del_person_papers_needs_manual_review(pid, bibrec):
    '''
    Deletes from the set of papers awaiting for manual review for a person
    @param pid: personid, int
    @param bibrec: the bibrec, int
    '''
    del_person_data(person_id=pid, tag='paper_needs_bibref_manual_confirm', value=str(bibrec))


def set_processed_external_recids(pid, recid_list_str):
    '''
    Set processed external recids
    @param pid: pid
    @param recid_list_str: str
    '''
    del_person_data(person_id=pid, tag='processed_external_recids')
    set_person_data(pid, "processed_external_recids", recid_list_str)


def assign_person_to_uid(uid, pid):
    '''
    Assigns a person to a userid. If person already assigned to someone else, create new person.
    Returns two value. Firstly the person id assigned and secondly if uid was succesfully assigned to given pid.
    If parameter pid equals to -1 then we assign the uid to a new person
    @param uid: user id, int
    @param pid: person id, int, if -1 creates new person.
    @return: pid int, bool
    '''
    if pid == -1:
        pid = dbinter.create_new_author_by_uid(uid, uid_is_owner=True)
        return pid, True
    else:
        current_uid = get_persons_data([pid], 'uid')
        if len(current_uid[pid]) == 0:
            dbinter.add_userid_to_author(pid, str(uid))
            return pid, True
        return -1, False


def get_processed_external_recids(pid):
    '''
    Returns processed external recids
    @param pid: pid
    @return: [str]
    '''
    db_data = get_persons_data([pid], "processed_external_recids")
    recid_list_str = ''

    if pid in db_data.keys() and db_data[pid] and db_data[pid][0][0]:
        recid_list_str = db_data[pid][0][0]

    return recid_list_str


def get_all_personids_recs(pid, claimed_only=False):
    return dbinter.get_papers_of_author(pid, claimed_only)


def mark_internal_id_as_old(person_id, uid):
    remove_author_data('uid', pid=person_id, value=uid)
    add_author_data(person_id, 'uid-old', value=uid)


def fallback_find_personids_by_name_string(target):
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
    family = get_surname(target)
    ascii_family = get_surname(translate_to_ascii(target)[0])
    clean_family = get_surname(clean_string(target))

    #SANITY: avoid empty queries
    if not family:
        return list()

    levels = (  # target + '%', #this introduces a weird problem: different results for mele, salvatore and salvatore mele
        family + '%',
        '%' + family + ',%',
        '%' + family[1:-1] + '%')

    if len(family) <= 4:
        levels = [levels[0], levels[2]]

    names = list(set().union(*map(get_authors_by_name_regexp,(family + ',%',
                                                              ascii_family + ',%',
                                                              clean_family + ',%'))))

    if not names:
        for lev in levels:
            names = dbinter.get_authors_by_name_regexp(lev)
            if names:
                break

    is_canonical = False
    if not names:
        names = dbinter.get_authors_by_canonical_name_regexp(target)
        is_canonical = True


    names = groupby(sorted(names))
    names = [(key[0], key[1], len(list(data)), soft_compare_names(target, key[1])) for key, data in names]
    names = groupby(names, itemgetter(0))
    names = [(key, sorted([(d[1], d[2], d[3]) for d in data if (d[3] > 0.5 or is_canonical)],
             key=itemgetter(2), reverse=True)) for key, data in names]
    names = [name for name in names if name[1]]
    names = sorted(names, key=lambda x: (x[1][0][2], x[1][0][0], x[1][0][1]), reverse=True)

    return names


def person_search_engine_query(query_string):
    '''
    docstring

    @param query_string:
    @type query_string:

    @return:
    @rtype:
    '''

    if canonical_name_type.match(query_string):
        canonical_name_matches = list(get_authors_by_canonical_name_regexp(query_string))

        if canonical_name_matches:
            canonical_name_matches = [i for i in canonical_name_matches]
            return canonical_name_matches

    if '@' in query_string:
        uid = dbinter.get_user_id_by_email(query_string)
        if uid is not None:
            pid = dbinter.get_author_by_uid(uid)
            if pid:
                return [(pid, [])]

    try:
        pids = list()
        n = int(query_string)
        pid = dbinter.get_author_by_uid(n)
        if pid:
            pids.append((pid, []))
        if dbinter.author_exists(n):
            pids.append((n, []))
        return pids

    except ValueError:
        pass

    search_engine_status = dbinter.search_engine_is_operating()

    if search_engine_status:
        personids_list = find_personids_by_name(query_string, trust_is_operating=True)
        personid_list = [(i, []) for i in personids_list]
        if personid_list:
            return personid_list

    return fallback_find_personids_by_name_string(query_string)


def check_personids_availability(picked_profile, uid):

    if picked_profile == -1:
        return create_new_author_by_uid(uid, uid_is_owner=True)
    else:
        if not get_uid_of_author(picked_profile):
            dbinter.add_author_data(picked_profile, 'uid', uid)
            return picked_profile
        else:
            return create_new_author_by_uid(uid, uid_is_owner=True)


def find_most_compatible_person(bibrecs, name_variants):
    '''
    Find if a profile in inspire matches to the profile that the user has in arXiv
    (judging from the papers the name etc)


    @param bibrecs: external system's record ids
    @type bibrecs: list

    @param name_variants: names of the user
    @type name_variants: list

    @return: person id of the most compatible person
    @rtype: int
    '''
    if name_variants:
        relevant_name = most_relevant_name(name_variants)

        pidlist = get_author_to_papers_mapping(bibrecs, limit_by_name=relevant_name)

        for p in pidlist:
            if not get_uid_of_author(p[0]):
                return p[0]
    return -1
