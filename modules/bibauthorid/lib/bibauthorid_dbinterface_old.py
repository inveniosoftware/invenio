# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013 CERN.
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
import invenio.bibauthorid_config as bconfig
import numpy
import cPickle
from cPickle import UnpicklingError
from invenio.htmlutils import X

import os
import gc

# python2.4 compatibility
from invenio.bibauthorid_general_utils import bai_all as all

from itertools import groupby, count, ifilter, chain, imap, repeat
from operator import itemgetter

from invenio.search_engine import perform_request_search
from invenio.access_control_engine import acc_authorize_action
from invenio.config import CFG_SITE_URL
from invenio.bibauthorid_config import QGRAM_LEN

from invenio.bibauthorid_name_utils import split_name_parts
from invenio.bibauthorid_name_utils import create_canonical_name
from invenio.bibauthorid_name_utils import create_normalized_name
from invenio.bibauthorid_general_utils import bibauthor_print
from invenio.bibauthorid_general_utils import update_status \
                                    , update_status_final
from dbquery import run_sql

try:
    from collections import defaultdict
except ImportError:
    class defaultdict(dict):
        '''
        Implementation of defaultdict to supply missing collections library in python <= 2.4
        '''
        def __init__(self, default_factory, *args, **kwargs):
            super(defaultdict, self).__init__(*args, **kwargs)
            self.default_factory = default_factory

        def __missing__(self, key):
            try:
                self[key] = self.default_factory()
            except TypeError:
                raise KeyError("Missing key %s" % (key,))
            else:
                return self[key]

        def __getitem__(self, key):
            try:
                return super(defaultdict, self).__getitem__(key)
            except KeyError:
                return self.__missing__(key)

MARC_100_700_CACHE = None

COLLECT_INSPIRE_ID = bconfig.COLLECT_EXTERNAL_ID_INSPIREID


def get_sql_time():
    '''
    Returns the time according to the database. The type is datetime.datetime.
    '''
    return run_sql("select now()")[0][0]


def set_personid_row(person_id, tag, value, opt1=None, opt2=None, opt3=None):
    '''
    Inserts data and additional info into aidPERSONIDDATA
    @param person_id:
    @type person_id: int
    @param tag:
    @type tag: string
    @param value:
    @type value: string
    @param opt1:
    @type opt1: int
    @param opt2:
    @type opt2: int
    @param opt3:
    @type opt3: string
    '''
    run_sql("INSERT INTO aidPERSONIDDATA "
            "(`personid`, `tag`, `data`, `opt1`, `opt2`, `opt3`) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (person_id, tag, value, opt1, opt2, opt3))


def get_personid_row(person_id, tag):
    '''
    Returns all the records associated to a person and a tag.

    @param person_id: id of the person to read the attribute from
    @type person_id: int
    @param tag: the tag to read.
    @type tag: string

    @return: the data associated with a virtual author
    @rtype: tuple of tuples
    '''
    return run_sql("SELECT data, opt1, opt2, opt3 "
                   "data FROM aidPERSONIDDATA "
                   "WHERE personid = %s AND tag = %s",
                   (person_id, tag))


def del_personid_row(tag, person_id=None, value=None):
    '''
    Delete the value associated to the given tag for a certain person.
    Can delete all tags regardless of person_id or value, or restrict the deletion using either of
    both of them.
    @param person_id: ID of the person
    @type person_id: int
    @param tag: tag to be updated
    @type tag: string
    @param value: value to be written for the tag
    @type value: string
    '''
    if person_id:
        if value:
            run_sql("delete from aidPERSONIDDATA where personid=%s and tag=%s and data=%s", (person_id, tag, value,))
        else:
            run_sql("delete from aidPERSONIDDATA where personid=%s and tag=%s", (person_id, tag,))
    else:
        if value:
            run_sql("delete from aidPERSONIDDATA where tag=%s and data=%s", (tag, value,))
        else:
            run_sql("delete from aidPERSONIDDATA where tag=%s", (tag,))


def get_all_papers_of_pids(personid_list):
    '''
    Get all papers of authors in a given list and sorts the results
    by bibrefrec.
    @param personid_list: list with the authors.
    @type personid_list: iteratable of integers.
    '''
    if personid_list:
        plist = list_2_SQL_str(personid_list)
        paps = run_sql("select personid, bibref_table, bibref_value, bibrec, flag "
                       "from aidPERSONIDPAPERS "
                       "where personid in %s "
                       % plist)

        inner = set(row[1:4] for row in paps if row[4] > -2)

        return (x for x in paps if x[1:4] in inner)

    return ()


def del_person_not_manually_claimed_papers(pid):
    '''
    Deletes papers from a person which have not been manually claimed.
    @param pid:
    @type pid: int
    '''
    run_sql("delete from aidPERSONIDPAPERS "
            "where and (flag <> '-2' and flag <> '2') and personid=%s", (pid,))

def get_personid_from_uid(uid):
    '''
    Returns the personID associated with the provided ui.
    If the personID is already associated with the person the secon parameter is True, false otherwise.
    @param uid: userID
    @type uid: ((int,),)
    '''
    pid = run_sql("select personid from aidPERSONIDDATA where tag=%s and data=%s", ('uid', str(uid[0][0])))
    if len(pid) == 1:
        return (pid[0], True)
    else:
        return  ([-1], False)

def get_uid_from_personid(pid):
    '''
    Get the invenio user id associated to a pid if exists.
    @param pid: person_id
    @type pid: int
    '''
    uid = run_sql("select data from aidPERSONIDDATA where tag='uid' and personid = %s", (pid,))
    if uid:
        return uid[0][0]
    else:
        return None


def get_new_personid():
    '''
    Get a free personid number
    '''
    pids = (run_sql("select max(personid) from aidPERSONIDDATA")[0][0],
            run_sql("select max(personid) from aidPERSONIDPAPERS")[0][0])

    pids = tuple(int(p) for p in pids if p != None)

    if len(pids) == 2:
        return max(*pids) + 1
    elif len(pids) == 1:
        return pids[0] + 1
    else:
        return 0

def get_existing_personids(with_papers_only=False):
    '''
    Get a set of existing person_ids.
    @param with_papers_only: if True, returns only ids holding papers discarding ids holding only information in aidPERSONIDDATA
    @type with_papers_only: Bool
    '''
    if not with_papers_only:
        try:
            pids_data = set(map(int, zip(*run_sql("select distinct personid from aidPERSONIDDATA"))[0]))
        except IndexError:
            pids_data = set()
    else:
        pids_data = set()
    try:
        pids_pap = set(map(int, zip(*run_sql("select distinct personid from aidPERSONIDPAPERS"))[0]))
    except IndexError:
        pids_pap = set()
    return pids_data | pids_pap


def get_existing_result_clusters():
    '''
    Get existing relult clusters, for private use of Tortoise and merger
    '''
    return run_sql("select distinct personid from aidRESULTS")


def create_new_person(uid=-1, uid_is_owner=False):
    '''
    Create a new person. Set the uid as owner if requested.
    @param uid: User id to associate to the newly created person
    @type uid: int
    @param uid_is_owner: If true, the person will hold the uid as owned, otherwise the id is only remembered as the creator
    @type uid_is_owner: bool
    '''
    personid_with_uid = run_sql("select personid from aidPERSONIDDATA where tag=%s and data=%s", ('uid', uid))

    if personid_with_uid:
        return personid_with_uid[0][0]

    pid = get_new_personid()
    if uid_is_owner:
        set_personid_row(pid, 'uid', str(uid))
    else:
        set_personid_row(pid, 'user-created', str(uid))
    return pid

def create_new_person_from_uid(uid):
    '''
    Commodity stub for create_new_person(...)
    @param uid: user id
    @type uid: int
    '''
    return create_new_person(uid, uid_is_owner=True)

def new_person_from_signature(sig, name=None):
    '''
    Creates a new person from a signature.
    @param sig: signature tuple ([100|700],bibref,bibrec)
    @type sig: tuple
    @param name:
    @type name: string
    '''
    pid = get_new_personid()
    add_signature(sig, name, pid)
    return pid


def add_signature(sig, name, pid):
    '''
    Inserts a signature in personid.
    @param sig: signature tuple
    @type sig: tuple
    @param name: name string
    @type name: string
    @param pid: personid to which assign the signature
    @type pid: int
    '''
    if not name:
        name = get_name_by_bibrecref(sig)
        name = create_normalized_name(split_name_parts(name))

    run_sql("INSERT INTO aidPERSONIDPAPERS "
            "(personid, bibref_table, bibref_value, bibrec, name) "
            "VALUES (%s, %s, %s, %s, %s)"
            , (pid, str(sig[0]), sig[1], sig[2], name))

def move_signature(sig, pid, force_claimed=False, unclaim=False):
    '''
    Moves a signature to a different person id
    @param sig: signature tuple
    @type sig: tuple
    @param pid: personid
    @type pid: int
    '''
    upd = "update aidPERSONIDPAPERS set personid=%s" % pid
    if unclaim:
        upd += ',flag=0 '
    sel = " where bibref_table like '%s' and bibref_value=%s and bibrec=%s " % sig

    sql = upd + sel
    if not force_claimed:
        sql += '  and flag <> 2 and flag <> -2'

    run_sql(sql)

def find_conflicts(sig, pid):
    '''
    Helper for merger algorithm, find signature given personid
    @param sig: signature tuple
    @type sig: tuple
    @param pid: personid id
    @type pid: integer
    '''
    return run_sql("select bibref_table, bibref_value, bibrec, flag "
                   "from aidPERSONIDPAPERS where "
                   "personid = %s and "
                   "bibrec = %s and "
                   "flag <> -2"
                   , (pid, sig[2]))

def update_request_ticket(person_id, tag_data_tuple, ticket_id=None):
    '''
    Creates / updates a request ticket for a personID
    @param: personid int
    @param: tag_data_tuples 'image' of the ticket: (('paper', '700:316,10'), ('owner', 'admin'), ('external_id', 'ticket_18'))
    @return: ticketid
    '''
    # tags: rt_owner (the owner of the ticket, associating the rt_number to the transaction)
    #      rt_external_id
    #      rt_paper_cornfirm, rt_paper_reject, rt_paper_forget, rt_name, rt_email, rt_whatever
    # flag: rt_number
    if not ticket_id:
        last_id = run_sql("select max(opt1) from aidPERSONIDDATA where personid=%s and tag like %s", (str(person_id), 'rt_%'))[0][0]

        if last_id:
            ticket_id = last_id + 1
        else:
            ticket_id = 1
    else:
        delete_request_ticket(person_id, ticket_id)

    for d in tag_data_tuple:
        run_sql("insert into aidPERSONIDDATA (personid, tag, data, opt1) "
                "values (%s,%s,%s,%s)",
                 (str(person_id), 'rt_' + str(d[0]), str(d[1]), str(ticket_id)))

    return ticket_id


def delete_request_ticket(person_id, ticket_id=None):
    '''
    Removes a ticket from a person_id.
    If ticket_id is not provider removes all the tickets pending on a person.
    '''
    if ticket_id:
        run_sql("delete from aidPERSONIDDATA where personid=%s and tag like %s and opt1 =%s", (str(person_id), 'rt_%', str(ticket_id)))
    else:
        run_sql("delete from aidPERSONIDDATA where personid=%s and tag like %s", (str(person_id), 'rt_%'))


def get_all_personids_by_name(regexpr):
    '''
    Search personids matching SQL expression in the name field
    @param regexpr: string SQL regexp
    @type regexpr: string
    '''
    return run_sql("select personid, name "
                   "from aidPERSONIDPAPERS "
                   "where name like %s "
                   "and flag > -2",
                   (regexpr,))

def get_personids_by_canonical_name(target):
    '''
    Find personids by canonical name
    @param target:
    @type target:
    '''
    return run_sql("select personid, data from aidPERSONIDDATA where "
                  "tag='canonical_name' and data like %s", (target,))

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

    head, rec = bibref.split(',')
    table, ref = head.split(':')
    flags = run_sql("SELECT flag, lcul FROM aidPERSONIDPAPERS WHERE "
                    "bibref_table = %s and bibref_value = %s and bibrec = %s"
                    , (table, ref, rec))
    if flags:
        return flags[0]
    else:
        return (False, 0)


def get_canonical_id_from_personid(pid):
    '''
    Finds the person id canonical name (e.g. Ellis_J_R_1)

    @param pid
    @type int

    @return: sql result of the request
    @rtype: tuple of tuple
    '''
    return run_sql("SELECT data FROM aidPERSONIDDATA WHERE "
                   "tag = %s AND personid = %s", ('canonical_name', str(pid)))


def get_papers_status(paper):
    '''
    Gets the personID and flag assiciated to papers
    @param papers: list of papers
    @type papers: '100:7531,9024'
    @return: (('data','personID','flag',),)
    @rtype: tuple of tuples
    '''
    head, bibrec = paper.split(',')
    _table, bibref = head.split(':')

    rets = run_sql("select PersonID, flag "
                             "from aidPERSONIDPAPERS "
                             "where bibref_table = %s "
                             "and bibref_value = %s "
                             "and bibrec = %s"
                             % (head, bibrec, bibref))
    return [[paper] + list(x) for x in rets]


def get_persons_from_recids(recids, return_alt_names=False,
                            return_all_person_papers=False):
    '''
    Helper for search engine indexing. Gives back a dictionary with important info about a person, for example:
     get_persons_from_recids([1], True, True) returns
      ({1: [16591L]},
      {16591L: {'alternatative_names': ['Wong, Yung Chow'],
      'canonical_id': 'Y.C.Wong.1',
      'person_records': [275304, 1, 51394, 128250, 311629]}})

    @param recids:
    @type recids:
    @param return_alt_names:
    @type return_alt_names:
    @param return_all_person_papers:
    @type return_all_person_papers:
    '''
    rec_2_pid = dict()
    pid_2_data = dict()
    all_pids = set()

    def get_canonical_name(pid):
        return run_sql("SELECT data "
                            "FROM aidPERSONIDDATA "
                            "WHERE tag = %s "
                            "AND personid = %s",
                            ('canonical_name', pid))

    for rec in recids:
        pids = run_sql("SELECT personid "
                       "FROM aidPERSONIDPAPERS "
                       "WHERE bibrec = %s "
                       " and flag > -2 ",
                       (rec,))

        # for some reason python's set is faster than a mysql distinct
        pids = set(p[0] for p in pids)
        all_pids |= pids
        rec_2_pid[rec] = list(pids)

    for pid in all_pids:
        pid_data = {}

        canonical = get_canonical_name(pid)
        # We can supposed that this person didn't have a chance to get a canonical name yet
        # because it was not fully processed by it's creator. Anyway it's safe to try to create one
        # before failing miserably
        if not canonical:
            update_personID_canonical_names([pid])
        canonical = get_canonical_name(pid)

        # assert len(canonical) == 1
        # This condition cannot hold in case claims or update daemons are run in parallel
        # with this, as it can happen that a person with papers exists for wich a canonical name
        # has not been computed yet. Hence, it will be indexed next time, so it learns.
        # Each person should have at most one canonical name, so:
        assert len(canonical) <= 1, "A person cannot have more than one canonical name"

        if len(canonical) == 1:
            pid_data = {'canonical_id' : canonical[0][0]}

        if return_alt_names:
            names = run_sql("SELECT name "
                            "FROM aidPERSONIDPAPERS "
                            "WHERE personid = %s "
                            " and flag > -2 ",
                            (pid,))
            names = set(n[0] for n in names)

            pid_data['alternatative_names'] = list(names)

        if return_all_person_papers:
            recs = run_sql("SELECT bibrec "
                           "FROM aidPERSONIDPAPERS "
                           "WHERE personid = %s "
                           " and flag > -2 ",
                           (pid,))
            recs = set(r[0] for r in recs)

            pid_data['person_records'] = list(recs)

        pid_2_data[pid] = pid_data

    return (rec_2_pid, pid_2_data)


def get_person_db_names_count(pid, sort_by_count=True):
    '''
    Returns the set of name strings and count associated to a person id.
    The name strings are as found in the database.
    @param pid: ID of the person
    @type pid: ('2',)
    '''

    id_2_count = run_sql("select bibref_table, bibref_value "
                         "from aidPERSONIDPAPERS "
                         "where personid = %s "
                         "and flag > -2", (pid,))

    ref100 = [refid[1] for refid in id_2_count if refid[0] == '100']
    ref700 = [refid[1] for refid in id_2_count if refid[0] == '700']

    ref100_count = dict((key, len(list(data))) for key, data in groupby(sorted(ref100)))
    ref700_count = dict((key, len(list(data))) for key, data in groupby(sorted(ref700)))

    if ref100:
        ref100_s = list_2_SQL_str(ref100, str)
        id100_2_str = run_sql("select id, value "
                              "from bib10x "
                              "where id in %s"
                              % ref100_s)
    else:
        id100_2_str = tuple()

    if ref700:
        ref700_s = list_2_SQL_str(ref700, str)
        id700_2_str = run_sql("select id, value "
                              "from bib70x "
                              "where id in %s"
                              % ref700_s)
    else:
        id700_2_str = tuple()

    ret100 = [(name, ref100_count[refid]) for refid, name in id100_2_str]
    ret700 = [(name, ref700_count[refid]) for refid, name in id700_2_str]

    ret = ret100 + ret700
    if sort_by_count:
        ret = sorted(ret, key=itemgetter(1), reverse=True)
    return ret


def get_person_id_from_canonical_id(canonical_id):
    '''
    Finds the person id from a canonical name (e.g. Ellis_J_R_1)

    @param canonical_id: the canonical ID
    @type canonical_id: string

    @return: sql result of the request
    @rtype: tuple of tuple
    '''
    return run_sql("SELECT personid FROM aidPERSONIDDATA WHERE "
                   "tag='canonical_name' AND data = %s", (canonical_id,))


#def get_person_names_count(pid):
#    '''
#    Returns the set of name strings and count associated to a person id
#    @param pid: ID of the person
#    @type pid: ('2',)
#    '''
#    return run_sql("select name, count(name) from aidPERSONIDPAPERS where "
#                   "personid=%s and flag > -2 group by name", (pid,))

### After testing it seems that on average the above query is slower than the function below ###

def get_person_names_count(pid):
    '''
    Returns the set of name strings and count associated to a person id
    @param pid: ID of the person
    @type pid: ('2',)
    '''
    res = run_sql("select name from aidPERSONIDPAPERS where "
                  "personid=%s and flag > -2", (pid,))
    reslist = [x[0] for x in res]
    names_count = defaultdict(int)
    for name in reslist:
        names_count[name]+=1

    return names_count.items()


def get_person_db_names_set(pid):
    '''
    Returns the set of db_name strings associated to a person id
    @param pid: ID of the person
    @type pid: 2
    '''

    names = get_person_db_names_count(pid)
    if names:
        return zip(set(zip(*names)[0]))
    else:
        return []

def get_personids_from_bibrec(bibrec):
    '''
    Returns all the personids associated to a bibrec.
    @param bibrec: record id
    @type bibrec: int
    '''

    pids = run_sql("select personid from aidPERSONIDPAPERS where bibrec=%s and flag > -2", (bibrec,))

    if pids:
        return set((x[0] for x in pids))
    else:
        return set()

def get_personids_and_papers_from_bibrecs(bibrecs, limit_by_name=None):
    '''
    Gives back a list of tuples (personid, set_of_papers_owned_by) limited to the given list of bibrecs.
    @param bibrecs:
    @type bibrecs:
    @param limit_by_name:
    @type limit_by_name:
    '''
    if not bibrecs:
        return []
    else:
        bibrecs = list_2_SQL_str(bibrecs)
    if limit_by_name:
        try:
            surname = split_name_parts(limit_by_name)[0]
        except IndexError:
            surname = None
    else:
        surname = None
    if not surname:
        data = run_sql("select personid,bibrec from aidPERSONIDPAPERS where bibrec in %s" % (bibrecs,))
    else:
        surname = split_name_parts(limit_by_name)[0]
        data = run_sql(("select personid,bibrec from aidPERSONIDPAPERS where bibrec in %s "
                       "and name like " % bibrecs) + ' %s ', (surname + '%',))
    pidlist = [(k, set([s[1] for s in d]))
               for k, d in groupby(sorted(data, key=lambda x:x[0]), key=lambda x:x[0])]
    pidlist = sorted(pidlist, key=lambda x:len(x[1]), reverse=True)
    return pidlist

def get_person_bibrecs(pid):
    '''
    Returns bibrecs associated with a personid
    @param pid: integer personid
    @return [bibrec1,...,bibrecN]
    '''
    papers = run_sql("select bibrec from aidPERSONIDPAPERS where personid=%s and flag > -2", (str(pid),))
    if papers:
        return list(set(zip(*papers)[0]))
    else:
        return []

def get_person_papers(pid, flag,
                      show_author_name=False,
                      show_title=False,
                      show_rt_status=False,
                      show_affiliations=False,
                      show_date=False,
                      show_experiment=False):
    '''
    Get all papers of person with flag greater than flag. Gives back a dictionary like:
     get_person_papers(16591,-2,True,True,True,True,True,True) returns
      [{'affiliation': ['Hong Kong U.'],
      'authorname': 'Wong, Yung Chow',
      'data': '100:1,1',
      'date': ('1961',),
      'experiment': [],
      'flag': 0,
      'rt_status': False,
      'title': ('Isoclinic N planes in Euclidean 2N space, Clifford parallels in elliptic (2N-1) space, and the Hurwitz matrix equations',)},
        ...]
    @param pid:
    @type pid:
    @param flag:
    @type flag:
    @param show_author_name:
    @type show_author_name:
    @param show_title:
    @type show_title:
    @param show_rt_status:
    @type show_rt_status:
    @param show_affiliations:
    @type show_affiliations:
    @param show_date:
    @type show_date:
    @param show_experiment:
    @type show_experiment:
    '''
    query = "bibref_table, bibref_value, bibrec, flag"
    if show_author_name:
        query += ", name"

    all_papers = run_sql("SELECT " + query + " "
                         "FROM aidPERSONIDPAPERS "
                         "WHERE personid = %s "
                         "AND flag >= %s",
                         (pid, flag))

    def format_paper(paper):
        bibrefrec = "%s:%d,%d" % paper[:3]
        ret = {'data' : bibrefrec,
               'flag' : paper[3]
              }

        if show_author_name:
            ret['authorname'] = paper[4]

        if show_title:
            ret['title'] = ""
            title = get_title_from_rec(paper[2])
            if title:
                ret['title'] = (title,)

        if show_rt_status:
            rt_count = run_sql("SELECT count(personid) "
                               "FROM aidPERSONIDDATA WHERE "
                               "tag like 'rt_%%' and data = %s"
                               , (bibrefrec,))

            ret['rt_status'] = (rt_count[0][0] > 0)

        if show_affiliations:
            tag = '%s__u' % paper[0]
            ret['affiliation'] = get_grouped_records(paper[:3], tag)[tag]

        if show_date:
            ret['date'] = []
            date_id = run_sql("SELECT id_bibxxx "
                              "FROM bibrec_bib26x "
                              "WHERE id_bibrec = %s "
                              , (paper[2],))

            if date_id:
                date_id_s = list_2_SQL_str(date_id, lambda x: x[0])
                date = run_sql("SELECT value "
                               "FROM bib26x "
                               "WHERE id in %s "
                               "AND tag = %s"
                               % (date_id_s, "'269__c'"))
                if date:
                    ret['date'] = zip(*date)[0]


        if show_experiment:
            ret['experiment'] = []
            experiment_id = run_sql("SELECT id_bibxxx "
                                    "FROM bibrec_bib69x "
                                    "WHERE id_bibrec = %s "
                                    , (paper[2],))

            if experiment_id:
                experiment_id_s = list_2_SQL_str(experiment_id, lambda x: x[0])
                experiment = run_sql("SELECT value "
                                     "FROM bib69x "
                                     "WHERE id in %s "
                                     "AND tag = %s"
                                     % (experiment_id_s, "'693__e'"))
                if experiment:
                    ret['experiment'] = zip(*experiment)[0]

        return ret

    return [format_paper(paper) for paper in all_papers]


def get_persons_with_open_tickets_list():
    '''
    Finds all the persons with open tickets and returns pids and count of tickets
    @return: [[pid, ticket_count]]
    '''
    return run_sql("select personid, count(distinct opt1) from "
                    "aidPERSONIDDATA where tag like 'rt_%' group by personid")


def get_request_ticket(person_id, ticket_id=None):
    '''
    Retrieves one or many requests tickets from a person
    @param: person_id: person id integer
    @param: matching: couple of values to match ('tag', 'value')
    @param: ticket_id: ticket id (flag) value
    @returns: [[[('tag', 'value')], ticket_id]]
        [[[('a', 'va'), ('b', 'vb')], 1L], [[('b', 'daOEIaoe'), ('a', 'caaoOUIe')], 2L]]
    '''
    if ticket_id:
        tstr = " and opt1='%s' " % ticket_id
    else:
        tstr = " "
    tickets = run_sql("select tag,data,opt1 from aidPERSONIDDATA where personid=%s and "
                      " tag like 'rt_%%' " + tstr , (person_id,))
    return [[[(s[0][3:], s[1]) for s in d], k] for k, d in groupby(sorted(tickets, key=lambda k: k[2]), key=lambda k: k[2])]


def get_validated_request_ticket(person_id, ticket_id=None):
    '''
    Validates request tickets before returning them.
    '''
    tickets = get_request_ticket(person_id, ticket_id)
    for ticket in list(tickets):
        for entry in list(ticket[0]):
            # those should be the only possible actions in a ticket!
            if entry[0] == 'reject' or entry[0] == 'assign':
                try:
                    bibref, bibrec = entry[1].split(',')
                    tab, val = bibref.split(':')
                    sig = (int(tab), int(val), int(bibrec))
                    present = bool(run_sql("select * from aidPERSONIDPAPERS where bibref_table like %s and bibref_value = %s and bibrec = %s ", sig))
                    if not present:
                        ticket[0].remove(entry)
                # No matter what goes wrong, that's an invalid entry in the ticket. let's discard it.
                except:
                    ticket[0].remove(entry)

    for ticket in list(tickets):
        tags = [x[0] for x in ticket[0]]
        if 'reject' not in tags and 'assign' not in tags:
            tickets.remove(ticket)

    return tickets


def insert_user_log(userinfo, personid, action, tag, value, comment='', transactionid=0, timestamp=None, userid=0):
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
    if not timestamp:
        timestamp = run_sql('select now()')[0][0]

    run_sql('insert into aidUSERINPUTLOG '
            '(transactionid,timestamp,userinfo,userid,personid,action,tag,value,comment) values '
            '(%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            (transactionid, timestamp, userinfo, userid, personid,
             action, tag, value, comment))

    return transactionid


def person_bibref_is_touched_old(pid, bibref):
    '''
    Determines if a record attached to a person has been touched by a human
    by checking the flag.

    @param pid: The Person ID of the person to check the assignment from
    @type pid: int
    @param bibref: The paper identifier to be checked (e.g. "100:12,144")
    @type bibref: string
    '''
    bibref, rec = bibref.split(",")
    table, ref = bibref.split(":")

    flag = run_sql("SELECT flag "
                   "FROM aidPERSONIDPAPERS "
                   "WHERE personid = %s "
                   "AND bibref_table = %s "
                   "AND bibref_value = %s "
                   "AND bibrec = %s"
                   , (pid, table, ref, rec))

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


def confirm_papers_to_person(pid, papers, user_level=0):
    '''
    Confirms the relationship between pid and paper, as from user input.
    @param pid: id of the person
    @type pid: integer
    @param papers: list of papers to confirm
    @type papers: ((str,),)   e.g. (('100:7531,9024',),)
    @return: list of tuples: (status, message_key)
    @rtype: [(bool, str), ]
    '''
    pids_to_update = set([pid])
    res = []

    for p in papers:
        bibref, rec = p.split(",")
        rec = int(rec)
        table, ref = bibref.split(":")
        ref = int(ref)
        sig = (table, ref, rec)

        # Check the status of pid: the paper should be present, either assigned or rejected
        gen_papers = run_sql("select bibref_table, bibref_value, bibrec, personid, flag, name "
                             "from aidPERSONIDPAPERS "
                             "where bibrec=%s "
                             "and flag >= -2"
                       , (rec,))

        paps = [el[0:3] for el in gen_papers if el[3] == pid and el[4] > -2]
        # run_sql("select bibref_table, bibref_value, bibrec "
        #               "from aidPERSONIDPAPERS "
        #               "where personid=%s "
        #               "and bibrec=%s "
        #               "and flag > -2"
        #               , (pid, rec))

        other_paps = [el[0:3] for el in gen_papers if el[3] != pid and el[4] > -2]
        # other_paps = run_sql("select bibref_table, bibref_value, bibrec "
        #               "from aidPERSONIDPAPERS "
        #               "where personid <> %s "
        #               "and bibrec=%s "
        #               "and flag > -2"
        #               , (pid, rec))

        rej_paps = [el[0:3] for el in gen_papers if el[3] == pid and el[4] == -2]
        # rej_paps = run_sql("select bibref_table, bibref_value, bibrec "
        #               "from aidPERSONIDPAPERS "
        #               "where personid=%s "
        #               "and bibrec=%s "
        #               "and flag = -2"
        #               , (pid, rec))

        bibref_exists = [el[0:3] for el in gen_papers if el[0] == table and el[1] == ref and el[4] > -2]
        # bibref_exists = run_sql("select * "
        #                        "from aidPERSONIDPAPERS "
        #                        "and bibref_table=%s "
        #                        "and bibref_value=%s "
        #                        "and bibrec=%s "
        #                        "and flag > -2"
        #                        , (table, ref, rec))


        # All papers that are being claimed should be present in aidPERSONIDPAPERS, thus:
        # assert paps or rej_paps or other_paps, 'There should be at least something regarding this bibrec!'
        # should always be valid.
        # BUT, it usually happens that claims get done out of the browser/session cache which is hours/days old,
        # hence it happens that papers are claimed which no longer exists in the system.
        # For the sake of mental sanity, instead of crashing from now on we just ignore such cases.
        if not (paps or other_paps or rej_paps) or not bibref_exists:
            res.append((False, 'confirm_failure'))
            continue
        res.append((True, 'confirm_success'))

        # It should not happen that a paper is assigned more then once to the same person.
        # But sometimes it happens in rare unfortunate cases of bad concurrency circumstances,
        # so we try to fix it directly instead of crashing here.
        # Once a better solution for dealing with concurrency will be found, the following asserts
        # shall be reenabled, to allow better control on what happens.

        # assert len(paps) < 2, "This paper should not be assigned to this person more then once! %s" % paps
        # assert len(other_paps) < 2, "There should not be more then one copy of this paper! %s" % other_paps

        # if the bibrec is present with a different bibref, the present one must be moved somwhere
        # else before we can claim the incoming one
        if paps:
            for pap in paps:
                # kick out all unwanted signatures
                if  sig != pap:
                    new_pid = get_new_personid()
                    pids_to_update.add(new_pid)
                    move_signature(pap, new_pid)

        # Make sure that the incoming claim is unique and get rid of all rejections, they are useless
        # from now on
        run_sql("delete from aidPERSONIDPAPERS where bibref_table like %s and "
                " bibref_value = %s and bibrec=%s"
                , sig)

        add_signature(sig, None, pid)
        run_sql("update aidPERSONIDPAPERS "
                "set personid = %s "
                ", flag = %s "
                ", lcul = %s "
                "where bibref_table = %s "
                "and bibref_value = %s "
                "and bibrec = %s"
                , (pid, '2', user_level,
                   table, ref, rec))

    update_personID_canonical_names(pids_to_update)
    return res


def reject_papers_from_person(pid, papers, user_level=0):
    '''
    Confirms the negative relationship between pid and paper, as from user input.
    @param pid: id of the person
    @type pid: integer
    @param papers: list of papers to confirm
    @type papers: ((str,),)   e.g. (('100:7531,9024',),)
    @return: list of tuples: (status, message_key)
    @rtype: [(bool, str), ]
    '''

    new_pid = get_new_personid()
    pids_to_update = set([pid])
    res = []

    for p in papers:
        brr, rec = p.split(",")
        table, ref = brr.split(':')

        sig = (table, ref, rec)
        # To be rejected, a record should be present!
        records = personid_name_from_signature(sig)
        # For the sake of mental sanity (see commentis in confirm_papers_to_personid, just ignore in case this paper is no longer existent
        # assert(records)
        if not records:
            res.append((False, 'reject_failure'))
            continue
        res.append((True, 'reject_success'))

        fpid, name = records[0]
        # If the record is assigned to a different person already, the rejection is meaningless
        # Otherwise, we assign the paper to someone else (not important who it will eventually
        # get moved by tortoise) and add the rejection to the current person

        if fpid == pid:
            move_signature(sig, new_pid, force_claimed=True, unclaim=True)
            pids_to_update.add(new_pid)
            run_sql("INSERT INTO aidPERSONIDPAPERS "
                    "(personid, bibref_table, bibref_value, bibrec, name, flag, lcul) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    , (pid, table, ref, rec, name, -2, user_level))

    update_personID_canonical_names(pids_to_update)

    return res


def reset_papers_flag(pid, papers):
    '''
    Resets the flag associated to the papers to '0'
    @param pid: id of the person
    @type pid: integer
    @param papers: list of papers to confirm
    @type papers: ((str,),)   e.g. (('100:7531,9024',),)
    @return: list of tuples: (status, message_key)
    @rtype: [(bool, str), ]
    '''
    res = []
    for p in papers:
        bibref, rec = p.split(",")
        table, ref = bibref.split(":")
        ref = int(ref)
        sig = (table, ref, rec)
        gen_papers = run_sql("select bibref_table, bibref_value, bibrec, flag "
                       "from aidPERSONIDPAPERS "
                       "where bibrec=%s "
                       "and personid=%s"
                       , (rec, pid))

        paps = [el[0:3] for el in gen_papers]
        # run_sql("select bibref_table, bibref_value, bibrec "
        #               "from aidPERSONIDPAPERS "
        #               "where personid=%s "
        #               "and bibrec=%s "
        #               , (pid, rec))

        rej_paps = [el[0:3] for el in gen_papers if el[3] == -2]
        # rej_paps = run_sql("select bibref_table, bibref_value, bibrec "
        #               "from aidPERSONIDPAPERS "
        #               "where personid=%s "
        #               "and bibrec=%s "
        #               "and flag = -2"
        #               , (pid, rec))

        pid_bibref_exists = [el[0:3] for el in gen_papers if el[0] == table and el[1] == ref and el[3] > -2]
        # bibref_exists = run_sql("select * "
        #                        "from aidPERSONIDPAPERS "
        #                        "and bibref_table=%s "
        #                        "and bibref_value=%s "
        #                        "and personid=%s "
        #                        "and bibrec=%s "
        #                        "and flag > -2"
        #                        , (table, ref, pid, rec))

        # again, see confirm_papers_to_person for the sake of mental sanity
        # assert paps or rej_paps
        if rej_paps or not pid_bibref_exists:
            res.append((False, 'reset_failure'))
            continue
        res.append((True, 'reset_success'))
        assert len(paps) < 2

        run_sql("delete from aidPERSONIDPAPERS where bibref_table like %s and "
                "bibref_value = %s and bibrec = %s",
                (sig))
        add_signature(sig, None, pid)

    return res


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

    pid_uid = run_sql("select data from aidPERSONIDDATA where tag = %s"
                          " and personid = %s", ('uid', str(pid)))

    if len(pid_uid) >= 1 and str(uid) == str(pid_uid[0][0]):
        rights = bconfig.CLAIMPAPER_CHANGE_OWN_DATA
    else:
        rights = bconfig.CLAIMPAPER_CHANGE_OTHERS_DATA

    return acc_authorize_action(uid, rights)[0] == 0


def get_possible_bibrecref(names, bibrec, always_match=False):
    '''
    Returns a list of bibrefs for which the surname is matching
    @param names: list of names strings
    @param bibrec: bibrec number
    @param always_match: match with all the names (full bibrefs list)
    '''
    splitted_names = [split_name_parts(n) for n in names]

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
    bibref, rec = paper.split(",")
    table, ref = bibref.split(":")
    prow = run_sql("select personid, lcul from aidPERSONIDPAPERS "
                   "where bibref_table = %s and bibref_value = %s and bibrec = %s "
                   "order by lcul desc limit 0,1",
                   (table, ref, rec))

    if len(prow) == 0:
        return ((acc_authorize_action(uid, bconfig.CLAIMPAPER_CLAIM_OWN_PAPERS)[0] == 0) or
                (acc_authorize_action(uid, bconfig.CLAIMPAPER_CLAIM_OTHERS_PAPERS)[0] == 0))

    min_req_acc_n = int(prow[0][1])
    req_acc = resolve_paper_access_right(bconfig.CLAIMPAPER_CLAIM_OWN_PAPERS)
    pid_uid = run_sql("select data from aidPERSONIDDATA where tag = %s and personid = %s", ('uid', str(prow[0][0])))
    if len(pid_uid) > 0:
        if (str(pid_uid[0][0]) != str(uid)) and min_req_acc_n > 0:
            req_acc = resolve_paper_access_right(bconfig.CLAIMPAPER_CLAIM_OTHERS_PAPERS)

    if min_req_acc_n < req_acc:
        min_req_acc_n = req_acc

    min_req_acc = resolve_paper_access_right(min_req_acc_n)

    return (acc_authorize_action(uid, min_req_acc)[0] == 0) and (resolve_paper_access_right(min_req_acc) >= min_req_acc_n)


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


def get_recently_modified_record_ids(date):
    '''
    Returns the bibrecs with modification date more recent then date.
    @param date: date
    '''
    touched_papers = frozenset(p[0] for p in run_sql(
            "select id from bibrec "
            "where modification_date >= %s"
            , (date,)))
    return touched_papers & frozenset(get_all_valid_bibrecs())


def filter_modified_record_ids(bibrecs, date):
    '''
    Returns the bibrecs with modification date before the date.
    @param date: date
    '''
    return ifilter(
        lambda x: run_sql("select count(*) from bibrec "
                          "where id = %s and "
                          "modification_date < %s"
                          , (x[2], date))[0][0]
        , bibrecs)


def get_user_log(transactionid='', userinfo='', userid='', personID='', action='', tag='', value='', comment='', only_most_recent=False):
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
    if userid:
        sql_query += ' and userid=\'' + str(userid) + '\''
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

def list_2_SQL_str(items, f=lambda x: x):
    """
    Concatenates all items in items to a sql string using f.
    @param items: a set of items
    @param type items: X
    @param f: a function which transforms each item from items to string
    @param type f: X:->str
    @return: "(x1, x2, x3, ... xn)" for xi in items
    @return type: string
    """
    strs = (str(f(x)) for x in items)
    return "(%s)" % ", ".join(strs)


def _get_authors_from_paper_from_db(paper):
    '''
    selects all author bibrefs by a given papers
    '''
    fullbibrefs100 = run_sql("select id_bibxxx from bibrec_bib10x where id_bibrec=%s", (paper,))
    if len(fullbibrefs100) > 0:
        fullbibrefs100str = list_2_SQL_str(fullbibrefs100, lambda x: str(x[0]))
        return run_sql("select id from bib10x where tag='100__a' and id in %s" % (fullbibrefs100str,))
    return tuple()

def _get_authors_from_paper_from_cache(paper):
    '''
    selects all author bibrefs by a given papers
    '''
    try:
        ids = MARC_100_700_CACHE['brb100'][paper]['id'].keys()
        refs = [i for i in ids if '100__a' in MARC_100_700_CACHE['b100'][i][0]]
    except KeyError:
        return tuple()
    return zip(refs)

def get_authors_from_paper(paper):
    if MARC_100_700_CACHE:
        if bconfig.DEBUG_CHECKS:
            assert _get_authors_from_paper_from_cache(paper) == _get_authors_from_paper_from_cache(paper)
        return _get_authors_from_paper_from_cache(paper)
    else:
        return _get_authors_from_paper_from_db(paper)

def _get_coauthors_from_paper_from_db(paper):
    '''
    selects all coauthor bibrefs by a given papers
    '''
    fullbibrefs700 = run_sql("select id_bibxxx from bibrec_bib70x where id_bibrec=%s", (paper,))
    if len(fullbibrefs700) > 0:
        fullbibrefs700str = list_2_SQL_str(fullbibrefs700, lambda x: str(x[0]))
        return run_sql("select id from bib70x where tag='700__a' and id in %s" % (fullbibrefs700str,))
    return tuple()

def _get_coauthors_from_paper_from_cache(paper):
    '''
    selects all author bibrefs by a given papers
    '''
    try:
        ids = MARC_100_700_CACHE['brb700'][paper]['id'].keys()
        refs = [i for i in ids if '700__a' in MARC_100_700_CACHE['b700'][i][0]]
    except KeyError:
        return tuple()
    return zip(refs)

def get_coauthors_from_paper(paper):
    if MARC_100_700_CACHE:
        if bconfig.DEBUG_CHECKS:
            assert _get_coauthors_from_paper_from_cache(paper) == _get_coauthors_from_paper_from_db(paper)
        return _get_coauthors_from_paper_from_cache(paper)
    else:
        return _get_coauthors_from_paper_from_db(paper)

def get_bibrefrec_subset(table, papers, refs):
    table = "bibrec_bib%sx" % str(table)[:-1]
    contents = run_sql("select id_bibrec, id_bibxxx from %s" % table)
    papers = set(papers)
    refs = set(refs)

    # yes, there are duplicates and we must set them
    return set(ifilter(lambda x: x[0] in papers and x[1] in refs, contents))

def get_deleted_papers():
    return run_sql("select o.id_bibrec from bibrec_bib98x o, "
                   "(select i.id as iid from bib98x i "
                   "where value = 'DELETED' "
                   "and tag like '980__a') as dummy "
                   "where o.id_bibxxx = dummy.iid")

def add_personID_external_id(personid, external_id_str, value):
    run_sql("insert into aidPERSONIDDATA (personid,tag,data) values (%s,%s,%s)",
            (personid, 'extid:%s' % external_id_str, value))

def remove_personID_external_id(personid, external_id_str, value=False):
    if not value:
        run_sql("delete from aidPERSONIDDATA where personid=%s and tag=%s",
                (personid, 'extid:%s' % external_id_str))
    else:
        run_sql("delete from aidPERSONIDDATA where personid=%s and tag=%s and data=%s",
                (personid, 'extid:%s' % external_id_str, value))

def get_personiID_external_ids(personid):
    ids = run_sql("select tag,data from aidPERSONIDDATA where personid=%s and tag like 'extid:%%'",
                  (personid,))

    extids = {}
    for i in ids:
        id_str = i[0].split(':')[1]
        idd = i[1]
        try:
            extids[id_str].append(idd)
        except KeyError:
            extids[id_str] = [idd]
    return extids

def change_personID_canonical_names(personid_cname_list=None):
    '''
    Changes the existing canonical name of a person with the given one.
    @param: personid_cname_list: list of tuples [(person_id, new_canonical_name),]
    '''
    for idx, pid_cname in enumerate(personid_cname_list):
        person_id, new_canonical_name = pid_cname
        update_status(float(idx) / float(len(personid_cname_list)), "Changing canonical_names...")
        # delete the current canonical name of person_id and the current holder of new_canonical_name
        run_sql("delete from aidPERSONIDDATA where tag=%s and (personid=%s or data=%s)", ('canonical_name', person_id, new_canonical_name))
        run_sql("insert into aidPERSONIDDATA (personid, tag, data) values (%s,%s,%s) ", (person_id, 'canonical_name', new_canonical_name))
    update_status_final("Changing canonical_names finished.")


# bibauthorid_maintenance personid update private methods
def update_personID_canonical_names(persons_list=None, overwrite=False, suggested='', overwrite_not_claimed_only=False):
    '''
    Updates the personID table creating or updating canonical names for persons
    @param: persons_list: persons to consider for the update  (('1'),)
    @param: overwrite: if to touch already existing canonical names
    @param: suggested: string to suggest a canonical name for the person
    '''
    if not persons_list and overwrite:
        persons_list = set([x[0] for x in run_sql('select personid from aidPERSONIDPAPERS')])
    elif not persons_list:
        persons_list = set([x[0] for x in run_sql('select personid from aidPERSONIDPAPERS')])
        existing_cnamed_pids = set(
                              [x[0] for x in run_sql('select personid from aidPERSONIDDATA where tag=%s',
                                                    ('canonical_name',))])
        persons_list = persons_list - existing_cnamed_pids

    for idx, pid in enumerate(persons_list):
        update_status(float(idx) / float(len(persons_list)), "Updating canonical_names...")
        if overwrite_not_claimed_only:
            has_claims = run_sql("select personid from aidPERSONIDPAPERS where personid = %s and flag = 2", (pid,))
            if has_claims:
                continue
        current_canonical = run_sql("select data from aidPERSONIDDATA where "
                                    "personid=%s and tag=%s", (pid, 'canonical_name'))

        if overwrite or len(current_canonical) == 0:
            run_sql("delete from aidPERSONIDDATA where personid=%s and tag=%s",
                    (pid, 'canonical_name'))

            names = get_person_names_count(pid)
            names = sorted(names, key=lambda k: k[1], reverse=True)
            if len(names) < 1 and not suggested:
                continue
            else:
                if suggested:
                    canonical_name = suggested
                else:
                    canonical_name = create_canonical_name(names[0][0])

                existing_cnames = run_sql("select data from aidPERSONIDDATA "
                                          "where tag=%s and data like %s",
                                          ('canonical_name', str(canonical_name) + '%'))

                existing_cnames = set(name[0].lower() for name in existing_cnames)
                for i in count(1):
                    cur_try = canonical_name + '.' + str(i)
                    if cur_try.lower() not in existing_cnames:
                        canonical_name = cur_try
                        break

                run_sql("insert into aidPERSONIDDATA (personid, tag, data) values (%s,%s,%s) ",
                         (pid, 'canonical_name', canonical_name))

    update_status_final("Updating canonical_names finished.")


def personid_get_recids_affected_since(last_timestamp):
    '''
    Returns a list of recids which have been manually changed since timestamp)
    @param: last_timestamp: last update, datetime.datetime
    '''
    vset = set(int(v[0].split(',')[1]) for v in run_sql(
               "select distinct value from aidUSERINPUTLOG "
               "where timestamp > %s", (last_timestamp,))
               if ',' in v[0] and ':' in v[0])

    pids = set(int(p[0]) for p in run_sql(
               "select distinct personid from aidUSERINPUTLOG "
               "where timestamp > %s", (last_timestamp,))
               if p[0] > 0)

    if pids:
        pids_s = list_2_SQL_str(pids)
        vset |= set(int(b[0]) for b in run_sql(
                    "select bibrec from aidPERSONIDPAPERS "
                    "where personid in %s" % pids_s))
    # I'm not sure about this cast. It might work without it.
    return list(vset)


def get_all_paper_records(pid, claimed_only=False):
    if not claimed_only:
        result = run_sql("SELECT bibrec FROM aidPERSONIDPAPERS WHERE personid = %s", (str(pid),))
    else:
        result = run_sql("SELECT bibrec FROM aidPERSONIDPAPERS WHERE "
                       "personid = %s and flag=2 or flag=-2", (str(pid),))

    return tuple(set(result))


def get_all_modified_names_from_personid(since=None):
    if since:
        all_pids = run_sql("SELECT DISTINCT personid "
                           "FROM aidPERSONIDPAPERS "
                           "WHERE flag > -2 "
                           "AND last_updated > %s"
                           % since)
    else:
        all_pids = run_sql("SELECT DISTINCT personid "
                           "FROM aidPERSONIDPAPERS "
                           "WHERE flag > -2 ")

    return ((name[0][0], set(n[1] for n in name), len(name))
            for name in (run_sql(
            "SELECT personid, name "
            "FROM aidPERSONIDPAPERS "
            "WHERE personid = %s "
            "AND flag > -2", p)
        for p in all_pids))


def destroy_partial_marc_caches():
    global MARC_100_700_CACHE
    MARC_100_700_CACHE = None
    gc.collect()

def populate_partial_marc_caches():
    global MARC_100_700_CACHE

    if MARC_100_700_CACHE:
        return

    def br_dictionarize(maptable):
        gc.disable()
        md = defaultdict(dict)
        maxiters = len(set(map(itemgetter(0), maptable)))
        for i, v in enumerate(groupby(maptable, itemgetter(0))):
            if i % 1000 == 0:
                update_status(float(i) / maxiters, 'br_dictionarizing...')
#            if i % 1000000 == 0:
#                update_status(float(i) / maxiters, 'br_dictionarizing...GC')
#                gc.collect()
            idx = defaultdict(list)
            fn = defaultdict(list)
            for _, k, z in v[1]:
                idx[k].append(z)
                fn[z].append(k)
            md[v[0]]['id'] = idx
            md[v[0]]['fn'] = fn
        update_status_final('br_dictionarizing done')
        gc.enable()
        return md

    def bib_dictionarize(bibtable):
        return dict((i[0], (i[1], i[2])) for i in bibtable)

    update_status(.0, 'Populating get_grouped_records_table_cache')
    bibrec_bib10x = sorted(run_sql("select id_bibrec,id_bibxxx,field_number from bibrec_bib10x"))
    update_status(.125, 'Populating get_grouped_records_table_cache')
    brd_b10x = br_dictionarize(bibrec_bib10x)
    del bibrec_bib10x

    update_status(.25, 'Populating get_grouped_records_table_cache')
    bibrec_bib70x = sorted(run_sql("select id_bibrec,id_bibxxx,field_number from bibrec_bib70x"))
    update_status(.375, 'Populating get_grouped_records_table_cache')
    brd_b70x = br_dictionarize(bibrec_bib70x)
    del bibrec_bib70x

    update_status(.5, 'Populating get_grouped_records_table_cache')
    bib10x = (run_sql("select id,tag,value from bib10x"))
    update_status(.625, 'Populating get_grouped_records_table_cache')
    bibd_10x = bib_dictionarize(bib10x)
    del bib10x

    update_status(.75, 'Populating get_grouped_records_table_cache')
    bib70x = (run_sql("select id,tag,value from bib70x"))
    update_status(.875, 'Populating get_grouped_records_table_cache')
    bibd_70x = bib_dictionarize(bib70x)
    del bib70x

    update_status_final('Finished populating get_grouped_records_table_cache')
    MARC_100_700_CACHE = {'brb100':brd_b10x, 'brb700':brd_b70x, 'b100':bibd_10x, 'b700':bibd_70x}

def _get_grouped_records_using_caches(brr, *args):
    try:
        c = MARC_100_700_CACHE['brb%s' % str(brr[0])][brr[2]]
        fn = c['id'][brr[1]]
    except KeyError:
        return dict((arg, []) for arg in args)
    if not fn or len(fn) > 1:
        # if len fn > 1 it's BAD: the same signature is at least twice on the same paper.
        # Let's default to nothing, to be on the safe side.
        return dict((arg, []) for arg in args)
    ids = set(chain(*(c['fn'][i] for i in fn)))
    tuples = [MARC_100_700_CACHE['b%s' % str(brr[0])][i] for i in ids]
    results = {}
    for t in tuples:
        present = [x for x in args if x in t[0]]
        assert len(present) <= 1
        if present:
            arg = present[0]
            try:
                results[arg].append(t[1])
            except KeyError:
                results[arg] = [t[1]]
    for arg in args:
        if arg not in results.keys():
            results[arg] = []
    return results

def _get_grouped_records_from_db(bibrefrec, *args):
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
        field_number = min(x[0] for x in group_id)

    grouped = run_sql("SELECT id_bibxxx "
                      "FROM %s "
                      "WHERE id_bibrec = %d "
                      "AND field_number = %d" %
                      (mapping_table, rec, int(field_number)))
    assert len(grouped) > 0, "There should be a most one grouped value per tag."
    grouped_s = list_2_SQL_str(grouped, lambda x: str(x[0]))

    ret = {}
    for arg in args:
        qry = run_sql("SELECT value "
                      "FROM %s "
                      "WHERE tag LIKE '%%%s%%' "
                      "AND id IN %s" %
                      (target_table, arg, grouped_s))
        ret[arg] = [q[0] for q in qry]

    return ret

def get_grouped_records(bibrefrec, *args):
    if MARC_100_700_CACHE:
        if bconfig.DEBUG_CHECKS:
            assert _get_grouped_records_using_caches(bibrefrec, *args) == _get_grouped_records_from_db(bibrefrec, *args)
        return _get_grouped_records_using_caches(bibrefrec, *args)
    else:
        return _get_grouped_records_from_db(bibrefrec, *args)

def get_person_with_extid(idd, match_tag=False):
    if match_tag:
        mtag = " and tag = '%s'" % 'extid:' + match_tag
    else:
        mtag = ''
    pids = run_sql("select personid from aidPERSONIDDATA where data=%s" % '%s' + mtag, (idd,))
    return set(pids)

def get_inspire_id(p):
    '''
    Gets inspire id for a signature (bibref_table,bibref_value.bibrec)
    '''
    return get_grouped_records((str(p[0]), p[1], p[2]), str(p[0]) + '__i').values()[0]

def get_claimed_papers_from_papers(papers):
    '''
    Given a set of papers it returns the subset of claimed papers
    @param papers: set of papers
    @type papers: frozenset
    @return: tuple
    '''
    papers_s = list_2_SQL_str(papers)
    claimed_papers = run_sql("select bibrec from aidPERSONIDPAPERS "
                             "where bibrec in %s and flag = 1" % papers_s)
    return claimed_papers

def collect_personID_external_ids_from_papers(personid, limit_to_claimed_papers=False):
    gathered_ids = {}

    if limit_to_claimed_papers:
        flag = 1
    else:
        flag = -2

    person_papers = run_sql("select bibref_table,bibref_value,bibrec from aidPERSONIDPAPERS where "
                            "personid=%s and flag > %s", (personid, flag))

    if COLLECT_INSPIRE_ID:
        inspireids = []
        for p in person_papers:
            extid = get_inspire_id(p)
            if extid:
                inspireids.append(extid)
        inspireids = set((i[0] for i in inspireids))

        gathered_ids['INSPIREID'] = inspireids

#    if COLLECT_ORCID:
#        orcids = []
#        for p in person_papers:
#            extid = get_orcid(p)
#            if extid:
#                orcids.append(extid)
#        orcids = set((i[0] for i in orcids))
#        gathered_ids['ORCID'] = orcids

#    if COLLECT_ARXIV_ID:
#        arxivids = []
#        for p in person_papers:
#            extid = get_arxiv_id(p)
#            if extid:
#                arxivids.append(extid)
#        arxivids = set((i[0] for i in arxivids))
#        gathered_ids['ARXIVID'] = arxivids

    return gathered_ids

def update_personID_external_ids(persons_list=None, overwrite=False,
                                 limit_to_claimed_papers=False, force_cache_tables=False):
    if force_cache_tables:
        populate_partial_marc_caches()

    if not persons_list:
        persons_list = set([x[0] for x in run_sql('select personid from aidPERSONIDPAPERS')])

    for idx, pid in enumerate(persons_list):
        update_status(float(idx) / float(len(persons_list)), "Updating external ids...")

        collected = collect_personID_external_ids_from_papers(pid, limit_to_claimed_papers=limit_to_claimed_papers)
        present = get_personiID_external_ids(pid)

        if overwrite:
            for idd in present.keys():
                for k in present[idd]:
                    remove_personID_external_id(pid, idd, value=k)
            present = {}

        for idd in collected.keys():
            for k in collected[idd]:
                if idd not in present or k not in present[idd]:
                    add_personID_external_id(pid, idd, k)

    if force_cache_tables:
        destroy_partial_marc_caches()

    update_status_final("Updating external ids finished.")

def _get_name_by_bibrecref_from_db(bib):
    '''
    @param bib: bibrefrec or bibref
    @type bib: (mark, bibref, bibrec) OR (mark, bibref)
    '''
    table = "bib%sx" % str(bib[0])[:-1]
    refid = bib[1]
    tag = "%s__a" % str(bib[0])
    ret = run_sql("select value from %s where id = '%s' and tag = '%s'" % (table, refid, tag))

    assert len(ret) == 1, "A bibrefrec must have exactly one name(%s)" % str(bib)
    return ret[0][0]

def _get_name_by_bibrecref_from_cache(bib):
    '''
    @param bib: bibrefrec or bibref
    @type bib: (mark, bibref, bibrec) OR (mark, bibref)
    '''
    table = "b%s" % bib[0]
    refid = bib[1]
    tag = "%s__a" % str(bib[0])
    ret = None
    try:
        if tag in MARC_100_700_CACHE[table][refid][0]:
            ret = MARC_100_700_CACHE[table][refid][1]
    except (KeyError, IndexError), e:
        # The GC did run and the table is not clean?
        # We might want to allow empty response here
        raise Exception(str(bib) + str(e))
    if bconfig.DEBUG_CHECKS:
        assert ret == _get_name_by_bibrecref_from_db(bib)
    return ret

def get_name_by_bibrecref(bib):
    if MARC_100_700_CACHE:
        if bconfig.DEBUG_CHECKS:
            assert _get_name_by_bibrecref_from_cache(bib) == _get_name_by_bibrecref_from_db(bib)
        return _get_name_by_bibrecref_from_cache(bib)
    else:
        return _get_name_by_bibrecref_from_db(bib)

def get_collaboration(bibrec):
    bibxxx = run_sql("select id_bibxxx from bibrec_bib71x where id_bibrec = %s", (str(bibrec),))

    if len(bibxxx) == 0:
        return ()

    bibxxx = list_2_SQL_str(bibxxx, lambda x: str(x[0]))

    ret = run_sql("select value from bib71x where id in %s and tag like '%s'" % (bibxxx, "710__g"))
    return [r[0] for r in ret]


def get_key_words(bibrec):
    if bconfig.CFG_ADS_SITE:
        bibxxx = run_sql("select id_bibxxx from bibrec_bib65x where id_bibrec = %s", (str(bibrec),))
    else:
        bibxxx = run_sql("select id_bibxxx from bibrec_bib69x where id_bibrec = %s", (str(bibrec),))

    if len(bibxxx) == 0:
        return ()

    bibxxx = list_2_SQL_str(bibxxx, lambda x: str(x[0]))

    if bconfig.CFG_ADS_SITE:
        ret = run_sql("select value from bib69x where id in %s and tag like '%s'" % (bibxxx, "6531_a"))
    else:
        ret = run_sql("select value from bib69x where id in %s and tag like '%s'" % (bibxxx, "695__a"))

    return [r[0] for r in ret]


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

def get_title_from_rec(rec):
    """
    Returns the name of the paper like str if found.
    Otherwise returns None.
    """
    title_id = run_sql("SELECT id_bibxxx "
                        "FROM bibrec_bib24x "
                        "WHERE id_bibrec = %s",
                        (rec,))

    if title_id:
        title_id_s = list_2_SQL_str(title_id, lambda x: x[0])
        title = run_sql("SELECT value "
                        "FROM bib24x "
                        "WHERE id in %s "
                        "AND tag = '245__a'"
                        % title_id_s)

        if title:
            return title[0][0]

def get_bib10x():
    return run_sql("select id, value from bib10x where tag like %s", ("100__a",))


def get_bib70x():
    return run_sql("select id, value from bib70x where tag like %s", ("700__a",))


class Bib_matrix(object):
    '''
    This small class contains the sparse matrix
    and encapsulates it.
    '''
    # please increment this value every time you
    # change the output of the comparison functions
    current_comparison_version = 10

    __special_items = ((None, -3.), ('+', -2.), ('-', -1.))
    special_symbols = dict((x[0], x[1]) for x in __special_items)
    special_numbers = dict((x[1], x[0]) for x in __special_items)

    def __init__(self, cluster_set=None):
        if cluster_set:
            self._bibmap = dict((b[1], b[0]) for b in enumerate(cluster_set.all_bibs()))
            width = len(self._bibmap)
            size = ((width - 1) * width) / 2
            self._matrix = Bib_matrix.create_empty_matrix(size)
        else:
            self._bibmap = dict()

        self.creation_time = get_sql_time()

    @staticmethod
    def create_empty_matrix(lenght):
        ret = numpy.ndarray(shape=(lenght, 2), dtype=float, order='C')
        ret.fill(Bib_matrix.special_symbols[None])
        return ret

    def _resolve_entry(self, bibs):
        assert len(bibs) == 2
        first = self._bibmap[bibs[0]]
        second = self._bibmap[bibs[1]]
        if first > second:
            first, second = second, first
        return first + ((second - 1) * second) / 2

    def __setitem__(self, bibs, val):
        self._matrix[self._resolve_entry(bibs)] = Bib_matrix.special_symbols.get(val, val)

    def __getitem__(self, bibs):
        #without temporary variable it's faster!
        #entry = self._resolve_entry(bibs)
        #ret = tuple(self._matrix[entry])
        #return Bib_matrix.special_numbers.get(ret[0], ret)
        ret = tuple(self._matrix[self._resolve_entry(bibs)])
        return  Bib_matrix.special_numbers.get(ret[0], ret)

    def __contains__(self, bib):
        return bib in self._bibmap

    def get_keys(self):
        return self._bibmap.keys()

    @staticmethod
    def get_file_dir(name):
        sub_dir = name[:2]
        if not sub_dir:
            sub_dir = "empty_last_name"
        return "%s%s/" % (bconfig.TORTOISE_FILES_PATH, sub_dir)

    @staticmethod
    def get_map_path(dir_path, name):
        return "%s%s.bibmap" % (dir_path, name)

    @staticmethod
    def get_matrix_path(dir_path, name):
        return "%s%s.npy" % (dir_path, name)

    def load(self, name, load_map=True, load_matrix=True):
        files_dir = Bib_matrix.get_file_dir(name)

        if not os.path.isdir(files_dir):
            self._bibmap = dict()
            return False

        try:
            if load_map:
                bibmap_v = cPickle.load(open(Bib_matrix.get_map_path(files_dir, name), 'r'))
                rec_v, self.creation_time, self._bibmap = bibmap_v
                if (rec_v != Bib_matrix.current_comparison_version or
                    # you can use negative version to recalculate
                    Bib_matrix.current_comparison_version < 0):

                    self._bibmap = dict()
                    return False

            if load_matrix:
                self._matrix = numpy.load(Bib_matrix.get_matrix_path(files_dir, name))
        except (IOError, UnpicklingError):
            if load_map:
                self._bibmap = dict()
                self.creation_time = get_sql_time()
                return False
        return True

    def store(self, name):
        files_dir = Bib_matrix.get_file_dir(name)

        if not os.path.isdir(files_dir):
            try:
                os.mkdir(files_dir)
            except OSError, e:
                if e.errno == 17 or 'file exists' in str(e.strerror).lower():
                    pass
                else:
                    raise e

        bibmap_v = (Bib_matrix.current_comparison_version, self.creation_time, self._bibmap)
        cPickle.dump(bibmap_v, open(Bib_matrix.get_map_path(files_dir, name), 'w'))

        numpy.save(open(Bib_matrix.get_matrix_path(files_dir, name), "w"), self._matrix)

def delete_paper_from_personid(rec):
    '''
    Deletes all information in PERSONID about a given paper
    '''
    run_sql("delete from aidPERSONIDPAPERS where bibrec = %s", (rec,))


def get_signatures_from_rec(bibrec):
    '''
    Retrieves all information in PERSONID
    about a given bibrec.
    '''
    return run_sql("select personid, bibref_table, bibref_value, bibrec, name "
                   "from aidPERSONIDPAPERS where bibrec = %s"
                   , (bibrec,))


def modify_signature(oldref, oldrec, newref, newname):
    '''
    Modifies a signature in aidPERSONIDpapers.
    '''
    return run_sql("UPDATE aidPERSONIDPAPERS "
                   "SET bibref_table = %s, bibref_value = %s, name = %s "
                   "WHERE bibref_table = %s AND bibref_value = %s AND bibrec = %s"
                   , (str(newref[0]), newref[1], newname,
                      str(oldref[0]), oldref[1], oldrec))


def find_pids_by_name(name):
    '''
    Finds names and personids by a prefix name.
    '''
    return set(run_sql("SELECT personid, name "
                       "FROM aidPERSONIDPAPERS "
                       "WHERE name like %s"
                       , (name + ',%',)))

def find_pids_by_exact_name(name):
    """
    Finds names and personids by a name.
    """
    return set(run_sql("SELECT personid "
                   "FROM aidPERSONIDPAPERS "
                   "WHERE name = %s"
                   , (name,)))

def remove_sigs(signatures):
    '''
    Removes records from aidPERSONIDPAPERS
    '''
    for sig in signatures:
        run_sql("DELETE FROM aidPERSONIDPAPERS "
                "WHERE bibref_table like %s AND bibref_value = %s AND bibrec = %s"
                , (str(sig[0]), sig[1], sig[2]))


def remove_personid_papers(pids):
    '''
    Removes all signatures from aidPERSONIDPAPERS with pid in pids
    '''
    if pids:
        run_sql("delete from aidPERSONIDPAPERS where personid in %s"
                % list_2_SQL_str(pids))


def get_full_personid_papers(table_name="`aidPERSONIDPAPERS`"):
    '''
    Get all columns and rows from aidPERSONIDPAPERS
    or any other table with the same structure.
    '''
    return run_sql("select personid, bibref_table, "
                   "bibref_value, bibrec, name, flag, "
                   "lcul from %s" % table_name)


def get_full_results():
    '''
    Depricated. Should be removed soon.
    '''
    return run_sql("select personid, bibref_table, bibref_value, bibrec "
                   "from aidRESULTS")


def get_lastname_results(last_name):
    '''
    Returns rows from aidRESULTS which share a common last name.
    '''
    return run_sql("select personid, bibref_table, bibref_value, bibrec "
                   "from aidRESULTS "
                   "where personid like '" + last_name + ".%'")


def get_full_personid_data(table_name="`aidPERSONIDDATA`"):
    '''
    Get all columns and rows from aidPERSONIDDATA
    or any other table with the same structure.
    '''
    return run_sql("select personid, tag, data, "
                   "opt1, opt2, opt3 from %s" % table_name)


def get_specific_personid_full_data(pid):
    '''
    Get all columns and rows from aidPERSONIDDATA
    '''
    return run_sql("select personid, tag, data, "
                   "opt1, opt2, opt3 from aidPERSONIDDATA where personid=%s "
                   , (pid,))


def get_canonical_names_by_pid(pid):
    '''
    Get all data that has as a tag canonical_name from aidPERSONIDDATA
    '''
    return run_sql("select data "
                   "from aidPERSONIDDATA where personid=%s and tag=%s"
                   , (pid, "canonical_name"))


def get_orcids_by_pids(pid):
    '''
    Get all data that has as a tag extid:ORCID from aidPERSONIDDATA
    '''
    return run_sql("select data "
                   "from aidPERSONIDDATA where personid=%s and tag=%s"
                   , (pid, "extid:ORCID"))


def get_inspire_ids_by_pids(pid):
    '''
    Get all data that has as a tag extid:INSPIREID from aidPERSONIDDATA
    '''
    return run_sql("select data "
                   "from aidPERSONIDDATA where personid=%s and tag=%s"
                   , (pid, "extid:INSPIREID"))

def get_uids_by_pids(pid):
    '''
    Get all data that has as a tag uid from aidPERSONIDDATA
    '''
    return run_sql("select data "
                   "from aidPERSONIDDATA where personid=%s and tag=%s"
                   , (pid, "uid"))

def get_name_string_to_pid_dictionary():
    '''
    Get a dictionary which maps name strigs to person ids
    '''
    namesdict = {}
    all_names = run_sql("select personid,name from aidPERSONIDPAPERS")
    for x in all_names:
        namesdict.setdefault(x[1], set()).add(x[0])
    return namesdict

# could be useful to optimize rabbit, still unused and untested, watch out.
def get_bibrecref_to_pid_dictuonary():
    brr2pid = {}
    all_brr = run_sql("select personid,bibref_table,bibref_value.bibrec from aidPERSONIDPAPERS")
    for x in all_brr:
        brr2pid.setdefault(tuple(x[1:]), set()).add(x[0])
    return brr2pid


def check_personid_papers(output_file=None):   ### check_author_paper_associations
    '''
    It examines if there are records in aidPERSONIDPAPERS table which are in an
    impaired state. If 'output_file' is specified it writes the output in that
    file, otherwise in stdout.

    @param output_file: file to write output
    @type output_file: str
    @return: damaged records are found
    @rtype: bool
    '''
    if output_file:
        fp = open(output_file, "w")
        printer = lambda x: fp.write(x + '\n')
    else:
        printer = bibauthor_print

    checkers = (check_duplicated_lines,
                check_wrong_names,
                check_duplicated_papers,
                check_duplicated_signatures,
                check_wrong_rejection,
                check_canonical_names,
                check_empty_personids
                # check_claim_inspireid_contradiction
                )
    # avoid writing f(a) or g(a), because one of the calls might be optimized
    return all([check(printer) for check in checkers])


def repair_personid(output_file=None):
    '''
    This should make check_personid_papers() to return true.
    '''
    if output_file:
        fp = open(output_file, "w")
        printer = lambda x: fp.write(x + '\n')
    else:
        printer = bibauthor_print

    checkers = (
                check_duplicated_lines,
                check_wrong_names,
                check_duplicated_papers,
                check_duplicated_signatures,
                check_wrong_rejection,
                check_canonical_names,
                check_empty_personids
                # check_claim_inspireid_contradiction
                )

    first_check = [check(printer) for check in checkers]
    repair_pass = [check(printer, repair=True) for check in checkers]
    last_check = [check(printer) for check in checkers]

    if not all(first_check):
        assert not(all(repair_pass))
        assert all(last_check)

    return all(last_check)

def check_duplicated_lines(printer, repair=False):
    '''
    For some reasons it happens that some lines in the database are duplicated. This is of course to
    be corrected, removing the duplicate line and leaving there only one copy.
    '''

    all_ok = True

    aid_table = run_sql('select personid, bibref_table, bibref_value, bibrec, name, flag, lcul, last_updated from aidPERSONIDPAPERS')
    aid_table = sorted(aid_table)
    duplicates = set([x for i, x in enumerate(aid_table[0:len(aid_table)-1]) if x == aid_table[i+1]])

    if duplicates:
        all_ok = False
        printer("There are duplicated lines in aidPERSONIDPAPERS: ")
        printer(str(duplicates))

    if repair:
        fields = ['personid=%s','bibref_table=%s','bibref_value=%s', 'bibrec=%s','name=%s','flag=%s','lcul=%s','last_updated=%s']
        for l in duplicates:
            used_fields = list()
            data = list()
            for i,f in enumerate(l):
                if f:
                    used_fields.append(fields[i])
                    data.append(f)
            run_sql("delete from aidPERSONIDPAPERS where "+' and '.join(used_fields), data)
            run_sql("insert into aidPERSONIDPAPERS  (personid, bibref_table, bibref_value, bibrec, name, flag, lcul, last_updated) "
                    "value (%s,%s,%s,%s,%s,%s,%s,%s)", l)

    aid_table = run_sql('select  personid, tag, data, opt1, opt2, opt3, last_updated from aidPERSONIDDATA')
    aid_table = sorted(aid_table)
    duplicates = set([x for i, x in enumerate(aid_table[0:len(aid_table)-1]) if x == aid_table[i+1]])

    if duplicates:
        all_ok = False
        printer("There are duplicated lines in aidPERSONIDDATA: ")
        printer(str(duplicates))

    if repair:
        fields = ['personid=%s','tag=%s','data=%s','opt1=%s','opt2=%s','opt3=%s','last_updated=%s']
        for l in duplicates:
            used_fields = list()
            data = list()
            for i,f in enumerate(l):
                if f:
                    used_fields.append(fields[i])
                    data.append(f)
            run_sql("delete from aidPERSONIDDATA where "+' and '.join(used_fields), data)
            run_sql("insert into aidPERSONIDDATA  (personid, tag, data, opt1, opt2, opt3, last_updated) "
                    "value (%s,%s,%s,%s,%s,%s,%s)", l)
    return all_ok


def check_duplicated_papers(printer, repair=False):   ### duplicated_conirmed_papers_exist
    '''
    It examines if there are records of confirmed papers in aidPERSONIDPAPERS
    table which are in an impaired state (duplicated) and repairs them if
    specified.

    @param printer: for log keeping
    @type printer: func
    @param repair: fix the duplicated records
    @type repair: bool
    @return: duplicated records are found
    @rtype: bool
    '''
    all_ok = True
    author_confirmed_papers = defaultdict(list)
    to_reassign = list()

    confirmed_papers = run_sql("""select personid, bibrec
                                  from aidPERSONIDPAPERS
                                  where flag <> %s""",
                                  (-2,) )

    for pid, rec in confirmed_papers:
        author_confirmed_papers[pid].append(rec)

    for pid, recs in author_confirmed_papers.iteritems():

        if not len(recs) == len(set(recs)):
            all_ok = False

            duplicates = sorted(recs)
            duplicates = set([rec for i, rec in enumerate(duplicates[:-1]) if rec == duplicates[i+1]])
            printer("Person %d has duplicated papers: %s" % (pid, duplicates))

            if repair:
                for duprec in duplicates:
                    printer("Repairing duplicated bibrec %s" % str(duprec))
                    claimed_from_involved = run_sql("""select personid, bibref_table, bibref_value, bibrec, flag
                                                       from aidPERSONIDPAPERS
                                                       where personid=%s
                                                       and bibrec=%s
                                                       and flag >= 2""",
                                                       (pid, duprec) )
                    if len(claimed_from_involved) != 1:
                        to_reassign.append(duprec)
                        _delete_from_aidpersonidpapers_where(rec=duprec, pid=pid)
                    else:
                        run_sql("""delete from aidPERSONIDPAPERS
                                   where personid=%s
                                   and bibrec=%s
                                   and flag < 2""",
                                   (pid, duprec) )

    if repair and to_reassign:
        printer("Reassigning deleted bibrecs %s" % str(to_reassign))
        from bibauthorid_rabbit import rabbit
        rabbit(to_reassign)

    return all_ok


def check_duplicated_signatures(printer, repair=False):   # duplicated_confirmed_signatures_exist
    '''
    It examines if there are records of confirmed signatures in
    aidPERSONIDPAPERS table which are in an impaired state (duplicated) and
    repairs them if specified.

    @param printer: for log keeping
    @type printer: func
    @param repair: fix the duplicated signatures
    @type repair: bool
    @return: duplicated signatures are found
    @rtype: bool
    '''
    all_ok = True
    paper_confirmed_bibrefs = dict()
    to_reassign = list()

    confirmed_sigs = run_sql("""select bibref_table, bibref_value, bibrec
                                from aidPERSONIDPAPERS
                                where flag > %s""",
                                (-2,) )

    for table, ref, rec in confirmed_sigs:
        paper_confirmed_bibrefs.setdefault(rec, []).append((table, ref))

    for rec, bibrefs in paper_confirmed_bibrefs.iteritems():

        if not len(bibrefs) == len(set(bibrefs)):
            all_ok = False

            duplicates = sorted(bibrefs)
            duplicates = set([bibref for i, bibref in enumerate(duplicates[:-1]) if bibref == duplicates[i+1]])
            printer("Paper %d has duplicated signatures: %s" % (rec, duplicates))

            if repair:
                for table, ref in duplicates:
                    printer("Repairing duplicated signature %s" % str((table, ref)))
                    claimed = _select_from_aidpersonidpapers_where(select=['personid', 'bibref_table', 'bibref_value', 'bibrec'], table=table, ref=ref, rec=rec, flag=2)

                    if len(claimed) != 1:
                        to_reassign.append(rec)
                        _delete_from_aidpersonidpapers_where(table=table, ref=ref, rec=rec)
                    else:
                        run_sql("""delete from aidPERSONIDPAPERS
                                   where bibref_table=%s
                                   and bibref_value=%s
                                   and bibrec=%s
                                   and flag < 2""",
                                   (table, ref, rec) )

    if repair and to_reassign:
        printer("Reassigning deleted bibrecs %s" % str(to_reassign))
        from bibauthorid_rabbit import rabbit
        rabbit(to_reassign)

    return all_ok


def get_wrong_names():
    '''
    Returns a generator with all wrong names in aidPERSONIDPAPERS.
    Every element is (table, ref, correct_name).
    '''

    bib100 = dict(((x[0], create_normalized_name(split_name_parts(x[1]))) for x in get_bib10x()))
    bib700 = dict(((x[0], create_normalized_name(split_name_parts(x[1]))) for x in get_bib70x()))

    pidnames100 = set(run_sql("select bibref_value, name from aidPERSONIDPAPERS "
                          " where bibref_table='100'"))
    pidnames700 = set(run_sql("select bibref_value, name from aidPERSONIDPAPERS "
                          " where bibref_table='700'"))

    wrong100 = set(('100', x[0], bib100.get(x[0], None)) for x in pidnames100 if x[1] != bib100.get(x[0], None))
    wrong700 = set(('700', x[0], bib700.get(x[0], None)) for x in pidnames700 if x[1] != bib700.get(x[0], None))

    total = len(wrong100) + len(wrong700)

    return chain(wrong100, wrong700), total


def check_wrong_names(printer, repair=False):   ### wrong_names_exist
    '''
    It examines if there are records in aidPERSONIDPAPERS table which carry a
    wrong name and repairs them if specified.

    @param printer: for log keeping
    @type printer: func
    @param repair: fix the found wrong names
    @type repair: bool
    @return: wrong names are found
    @rtype: bool
    '''
    wrong_names_exist = False
    wrong_names, wrong_names_count = get_wrong_names()

    if wrong_names_count > 0:
        wrong_names_exist = True
        printer("%d corrupted names in aidPERSONIDPAPERS." % wrong_names_count)
        for wrong_name in wrong_names:
            if wrong_name[2]:
                printer("Outdated name, '%s'(%s:%d)." % (wrong_name[2], wrong_name[0], wrong_name[1]))
            else:
                printer("Invalid id(%s:%d)." % (wrong_name[0], wrong_name[1]))

            if repair:
                printer("Fixing wrong name: %s" % str(wrong_name))
                if wrong_name[2]:
                    run_sql("""update aidPERSONIDPAPERS
                               set name=%s
                               where bibref_table=%s
                               and bibref_value=%s""",
                               (wrong_name[2], wrong_name[0], wrong_name[1]) )
                else:
                    _delete_from_aidpersonidpapers_where(table=wrong_name[0], ref=wrong_name[1])

    return not wrong_names_exist


def check_canonical_names(printer, repair=False):   ### impaired_canonical_names_exist
    '''
    It examines if there are authors who carry less or more than one canonical
    name and repairs them if specified.

    @param printer: for log keeping
    @type printer: func
    @param repair: fix authors with less/more than one canonical name
    @type repair: bool
    @return: authors with less/more than one canonical name exist
    @rtype: bool
    '''
    all_ok = True

    authors_cnames = _select_from_aidpersoniddata_where(select=['personid', 'data'], tag='canonical_name')
    authors_cnames = sorted(authors_cnames, key=itemgetter(0))
    author_cnames_count = dict((pid, len(list(cnames))) for pid, cnames in groupby(authors_cnames, key=itemgetter(0)))

    to_update = list()

    for pid in get_existing_personids():
        cnames_count = author_cnames_count.get(pid, 0)

        if cnames_count != 1:
            if cnames_count == 0:
                papers_count = _select_from_aidpersonidpapers_where(select=['count(*)'], pid=pid)[0][0]
                if papers_count != 0:
                    all_ok = False
                    printer("Personid %d does not have a canonical name, but has %d papers." % (pid, papers_count))
                    to_update.append(pid)
            else:
                all_ok = False
                printer("Personid %d has %d canonical names.", (pid, cnames_count))
                to_update.append(pid)

    if repair and not all_ok:
        printer("Repairing canonical names for pids: %s" % str(to_update))
        update_personID_canonical_names(to_update, overwrite=True)

    return all_ok


def check_empty_personids(printer, repair=False):   ### empty_authors_exist
    '''
    It examines if there are empty authors (that is authors with no papers or
    other defined data) and deletes them if specified.

    @param printer: for log keeping
    @type printer: func
    @param repair: delete empty authors
    @type repair: bool
    @return: empty authors are found
    @rtype: bool
    '''
    empty_pids = delete_empty_persons(remove=repair)

    empty_authors_exist = False
    if empty_pids:
        empty_authors_exist = True

    for pid in empty_pids:
        printer("Personid %d has no papers and nothing else than canonical_name." % pid)

        if repair:
            printer("Deleting empty person %s." % pid)

    return not empty_authors_exist


def check_wrong_rejection(printer, repair=False):   ### impaired_rejections_exist
    '''
    It examines if there are records of rejected papers in aidPERSONIDPAPERS
    table which are in an impaired state (not assigned or both confirmed and
    rejected for the same author) and repairs them if specified.

    @param printer: for log keeping
    @type printer: func
    @param repair: fix the damaged records
    @type repair: bool
    @return: damaged records are found
    @rtype: bool
    '''
    all_ok = True
    to_reassign = list()
    to_deal_with = list()

    rejected_papers = set(_select_from_aidpersonidpapers_where(select=['bibref_table', 'bibref_value', 'bibrec'], flag=-2))

    confirmed_papers = set(run_sql("""select bibref_table, bibref_value, bibrec
                                      from aidPERSONIDPAPERS
                                      where flag > %s""",
                                      (-2,) ))
    not_assigned_papers = rejected_papers - confirmed_papers

    for paper in not_assigned_papers:
        printer("Paper (%s:%s,%s) was rejected but never reassigned" % paper)
        to_reassign.append(paper)

    rejected_papers = set(_select_from_aidpersonidpapers_where(select=['personid', 'bibref_table', 'bibref_value', 'bibrec'], flag=-2))

    confirmed_papers = set(run_sql("""select personid, bibref_table, bibref_value, bibrec
                                      from aidPERSONIDPAPERS
                                      where flag > %s""",
                                      (-2,) ))
    # papers which are both confirmed and rejected for/from the same author
    both_confirmed_and_rejected_papers = rejected_papers & confirmed_papers

    for paper in both_confirmed_and_rejected_papers:
        printer("Conflicting assignment/rejection: %s" % str(paper))
        to_deal_with.append(paper)

    if not_assigned_papers or both_confirmed_and_rejected_papers:
        all_ok = False

    if repair and (to_reassign or to_deal_with):
        from bibauthorid_rabbit import rabbit

        if to_reassign:
            # Rabbit is not designed to reassign signatures which are rejected but not assigned:
            # All signatures should be assigned. If a rejection occurs, the signature should get
            # moved to a new place and the rejection entry added, but never exist as a rejection only.
            # Hence, to force rabbit to reassign it we have to delete the rejection.
            printer("Reassigning bibrecs with missing entries: %s" % str(to_reassign))
            for sig in to_reassign:
                table, ref, rec = sig
                _delete_from_aidpersonidpapers_where(table=table, ref=ref, rec=rec, flag=-2)

            recs = [paper[2] for paper in to_reassign]
            rabbit(recs)

        if to_deal_with:
            # We got claims and rejections on the same paper for the same person. Let's forget about
            # it and reassign it automatically, they'll make up their minds sooner or later.
            printer("Deleting and reassigning bibrefrecs with conflicts %s" % str(to_deal_with))
            for sig in to_deal_with:
                pid, table, ref, rec = sig
                _delete_from_aidpersonidpapers_where(table=table, ref=ref, rec=rec, pid=pid)

            recs = map(itemgetter(3), to_deal_with)
            rabbit(recs)

    return all_ok


def _delete_from_aidpersonidpapers_where(pid=None, table=None, ref=None, rec=None, name=None, flag=None, lcul=None):
    '''
    Deletes the records from aidPERSONIDPAPERS table with the given attributes.
    If no parameters are given it deletes all records.

    @param pid: author identifier
    @type pid: int
    @param table: bibref_table
    @type table: int
    @param ref: bibref_value
    @type ref: int
    @param rec: paper identifier
    @type rec: int
    @param name: author name
    @type name: str
    @param flag: flag
    @type flag: int
    @param lcul: lcul
    @type lcul: int
    '''
    conditions = list()
    add_condition = conditions.append
    args = list()
    add_arg = args.append

    if pid is not None:
        add_condition('personid=%s')
        add_arg(pid)
    if table is not None:
        add_condition('bibref_table=%s')
        add_arg(str(table))
    if ref is not None:
        add_condition('bibref_value=%s')
        add_arg(ref)
    if rec is not None:
        add_condition('bibrec=%s')
        add_arg(rec)
    if name is not None:
        add_condition('name=%s')
        add_arg(name)
    if flag is not None:
        add_condition('flag=%s')
        add_arg(flag)
    if lcul is not None:
        add_condition('lcul=%s')
        add_arg(lcul)

    if not conditions:
        return

    conditions_str = " and ".join(conditions)
    query = "delete from aidPERSONIDPAPERS where %s" % conditions_str

    run_sql(query, tuple(args) )


def _select_from_aidpersonidpapers_where(select=None, pid=None, table=None, ref=None, rec=None, name=None, flag=None, lcul=None):
    '''
    Selects the given fields from the records of aidPERSONIDPAPERS table
    with the specified attributes. If no parameters are given it returns all
    records.

    @param select: fields to select
    @type select: list [str,]
    @param pid: author identifier
    @type pid: int
    @param table: bibref_table
    @type table: int
    @param ref: bibref_value
    @type ref: int
    @param rec: paper identifier
    @type rec: int
    @param name: author name
    @type name: str
    @param flag: author-paper association status
    @type flag: int
    @param lcul: lcul
    @type lcul: int
    @return: given fields of the records with the specified attributes
    @rtype: tuple
    '''
    if not select:
        return None

    conditions = list()
    add_condition = conditions.append
    args = list()
    add_arg = args.append

    add_condition('True')
    if pid is not None:
        add_condition('personid=%s')
        add_arg(pid)
    if table is not None:
        add_condition('bibref_table=%s')
        add_arg(str(table))
    if ref is not None:
        add_condition('bibref_value=%s')
        add_arg(ref)
    if rec is not None:
        add_condition('bibrec=%s')
        add_arg(rec)
    if name is not None:
        add_condition('name=%s')
        add_arg(name)
    if flag is not None:
        add_condition('flag=%s')
        add_arg(flag)
    if lcul is not None:
        add_condition('lcul=%s')
        add_arg(lcul)

    select_fields_str = "%s" % ", ".join(select)
    conditions_str = "%s" % " and ".join(conditions)
    query = """select %s
               from aidPERSONIDPAPERS
               where %s""" % (select_fields_str, conditions_str)

    return run_sql(query, tuple(args) )


def _select_from_aidpersoniddata_where(select=None, pid=None, tag=None, data=None, opt1=None, opt2=None, opt3=None):
    '''
    Selects the given fields from the records of aidPERSONIDDATA table
    with the specified attributes. If no parameters are given it returns all
    records.

    @param select: fields to select
    @type select: list [str,]
    @param pid: author identifier
    @type pid: int
    @param tag: data tag
    @type tag: str
    @param data: data tag value
    @type data: str
    @param opt1: opt1
    @type opt1: int
    @param opt2: opt2
    @type opt2: int
    @param opt3: opt3
    @type opt3: str
    @return: given fields of the records with the specified attributes
    @rtype: tuple
    '''
    if not select:
        return None

    conditions = list()
    add_condition = conditions.append
    args = list()
    add_arg = args.append

    add_condition('True')
    if pid is not None:
        add_condition('personid=%s')
        add_arg(pid)
    if tag is not None:
        add_condition('tag=%s')
        add_arg(tag)
    if data is not None:
        add_condition('data=%s')
        add_arg(data)
    if opt1 is not None:
        add_condition('opt1=%s')
        add_arg(opt1)
    if opt2 is not None:
        add_condition('opt2=%s')
        add_arg(opt2)
    if opt3 is not None:
        add_condition('opt3=%s')
        add_arg(opt3)

    select_fields_str = "%s" % ", ".join(select)
    conditions_str = "%s" % " and ".join(conditions)
    query = """select %s
               from aidPERSONIDDATA
               where %s""" % (select_fields_str, conditions_str)

    return run_sql(query, tuple(args) )


def check_merger():
    '''
    This function presumes that copy_personid was
    called before the merger.
    '''
    is_ok = True

    old_claims = set(run_sql("select personid, bibref_table, bibref_value, bibrec, flag "
                             "from aidPERSONIDPAPERS_copy "
                             "where flag = -2 or flag = 2"))

    cur_claims = set(run_sql("select personid, bibref_table, bibref_value, bibrec, flag "
                             "from aidPERSONIDPAPERS "
                             "where flag = -2 or flag = 2"))

    errors = ((old_claims - cur_claims, "Some claims were lost during the merge."),
              (cur_claims - old_claims, "Some new claims appeared after the merge."))
    act = { -2 : 'Rejection', 2 : 'Claim' }

    for err_set, err_msg in errors:
        if err_set:
            is_ok = False
            bibauthor_print(err_msg)
            bibauthor_print("".join("    %s: personid %d %d:%d,%d\n" %
                            (act[cl[4]], cl[0], int(cl[1]), cl[2], cl[3]) for cl in err_set))

    old_assigned = set(run_sql("select bibref_table, bibref_value, bibrec "
                               "from aidPERSONIDPAPERS_copy"))
                                # "where flag <> -2 and flag <> 2"))

    cur_assigned = set(run_sql("select bibref_table, bibref_value, bibrec "
                               "from aidPERSONIDPAPERS"))
                                # "where flag <> -2 and flag <> 2"))

    errors = ((old_assigned - cur_assigned, "Some signatures were lost during the merge."),
              (cur_assigned - old_assigned, "Some new signatures appeared after the merge."))

    for err_sig, err_msg in errors:
        if err_sig:
            is_ok = False
            bibauthor_print(err_msg)
            bibauthor_print("".join("    %s:%d,%d\n" % sig for sig in err_sig))

    return is_ok

def check_results():
    is_ok = True

    all_result_rows = run_sql("select personid,bibref_table,bibref_value,bibrec from aidRESULTS")

    keyfunc = lambda x: x[1:]
    duplicated = (d for d in (list(d) for k, d in groupby(sorted(all_result_rows, key=keyfunc), key=keyfunc)) if len(d) > 1)

    for dd in duplicated:
        is_ok = False
        for d in dd:
            print "Duplicated row in aidRESULTS"
            print "%s %s %s %s" % d
        print


    clusters = {}
    for rr in all_result_rows:
        clusters[rr[0]] = clusters.get(rr[0], []) + [rr[3]]

    faulty_clusters = dict((cid, len(recs) - len(set(recs)))
                               for cid, recs in clusters.items()
                                   if not len(recs) == len(set(recs)))

    if faulty_clusters:
        is_ok = False
        print "Recids NOT unique in clusters!"
        print ("A total of %s clusters hold an average of %.2f duplicates" %
               (len(faulty_clusters), (sum(faulty_clusters.values()) / float(len(faulty_clusters)))))

        for c in faulty_clusters:
            print "Name: %-20s      Size: %4d      Faulty: %2d" % (c, len(clusters[c]), faulty_clusters[c])

    return is_ok

def check_claim_inspireid_contradiction():
    iids10x = run_sql("select id from bib10x where tag = '100__i'")
    iids70x = run_sql("select id from bib70x where tag = '700__i'")

    refs10x = set(x[0] for x in run_sql("select id from bib10x where tag = '100__a'"))
    refs70x = set(x[0] for x in run_sql("select id from bib70x where tag = '700__a'"))

    if iids10x:
        iids10x = list_2_SQL_str(iids10x, lambda x: str(x[0]))

        iids10x = run_sql("select id_bibxxx, id_bibrec, field_number "
                          "from bibrec_bib10x "
                          "where id_bibxxx in %s"
                          % iids10x)

        iids10x = ((row[0], [(ref, rec) for ref, rec in run_sql(
                                "select id_bibxxx, id_bibrec "
                                "from bibrec_bib10x "
                                "where id_bibrec = '%s' "
                                "and field_number = '%s'"
                                % row[1:])
                               if ref in refs10x])
                      for row in iids10x)
    else:
        iids10x = ()

    if iids70x:
        iids70x = list_2_SQL_str(iids70x, lambda x: str(x[0]))

        iids70x = run_sql("select id_bibxxx, id_bibrec, field_number "
                          "from bibrec_bib70x "
                          "where id_bibxxx in %s"
                          % iids70x)

        iids70x = ((row[0], [(ref, rec) for ref, rec in run_sql(
                                "select id_bibxxx, id_bibrec "
                                "from bibrec_bib70x "
                                "where id_bibrec = '%s' "
                                "and field_number = '%s'"
                                % (row[1:]))
                               if ref in refs70x])
                      for row in iids70x)
    else:
        iids70x = ()

    # [(iids, [bibs])]
    inspired = list(chain(((iid, list(set(('100',) + bib for bib in bibs))) for iid, bibs in iids10x),
                          ((iid, list(set(('700',) + bib for bib in bibs))) for iid, bibs in iids70x)))

    assert all(len(x[1]) == 1 for x in inspired)

    inspired = ((k, map(itemgetter(0), map(itemgetter(1), d)))
                    for k, d in groupby(sorted(inspired, key=itemgetter(0)), key=itemgetter(0)))

    # [(inspireid, [bibs])]
    inspired = [([(run_sql("select personid "
                            "from aidPERSONIDPAPERS "
                            "where bibref_table = %s "
                            "and bibref_value = %s "
                            "and bibrec = %s "
                            "and flag = '2'"
                            , bib), bib)
                        for bib in cluster[1]], cluster[0])
                    for cluster in inspired]

    # [([([pid], bibs)], inspireid)]
    for cluster, iid in inspired:
        pids = set(chain.from_iterable(imap(itemgetter(0), cluster)))

        if len(pids) > 1:
            print "InspireID: %s links the following papers:" % iid
            print map(itemgetter(1), cluster)
            print "More than one personid claimed them:"
            print list(pids)
            print
            continue

        if len(pids) == 0:
            # not even one paper with this inspireid has been
            # claimed, screw it
            continue

        pid = list(pids)[0][0]

        # The last step is to check all non-claimed papers for being
        # claimed by the person on some different signature.
        problem = (run_sql("select bibref_table, bibref_value, bibrec "
                           "from aidPERSONIDPAPERS "
                           "where bibrec = %s "
                           "and personid = %s "
                           "and flag = %s"
                           , (bib[2], pid, 2))
                       for bib in (bib for lpid, bib in cluster if not lpid))
        problem = list(chain.from_iterable(problem))

        if problem:
            print "A personid has claimed a paper from an inspireid cluster and a contradictory paper."
            print "Personid %d" % pid
            print "Inspireid cluster %s" % str(map(itemgetter(1), cluster))
            print "Contradicting claims: %s" % str(problem)
            print

def get_all_bibrecs():
    '''
    Get all record ids present in aidPERSONIDPAPERS
    '''
    return set([x[0] for x in run_sql("select bibrec from aidPERSONIDPAPERS")])

def get_bibrefrec_to_pid_flag_mapping():
    '''
    create a map between signatures and personid/flag
    '''
    whole_table = run_sql("select bibref_table,bibref_value,bibrec,personid,flag from aidPERSONIDPAPERS")
    gc.disable()
    ret = {}
    for x in whole_table:
        sig = (x[0], x[1], x[2])
        pid_flag = (x[3], x[4])
        ret[sig] = ret.get(sig , []) + [pid_flag]
    gc.collect()
    gc.enable()
    return ret

def remove_all_bibrecs(bibrecs):
    '''
    Remove give record ids from aidPERSONIDPAPERS table
    @param bibrecs:
    @type bibrecs:
    '''
    bibrecs_s = list_2_SQL_str(bibrecs)
    run_sql("delete from aidPERSONIDPAPERS where bibrec in %s" % bibrecs_s)


def empty_results_table():
    '''
    Get rid of all tortoise results
    '''
    run_sql("TRUNCATE aidRESULTS")


def save_cluster(named_cluster):
    '''
    Save a cluster in aidRESULTS
    @param named_cluster:
    @type named_cluster:
    '''
    name, cluster = named_cluster
    for bib in cluster.bibs:
        run_sql("INSERT INTO aidRESULTS "
                "(personid, bibref_table, bibref_value, bibrec) "
                "VALUES (%s, %s, %s, %s) "
                , (name, str(bib[0]), bib[1], bib[2]))


def remove_result_cluster(name):
    '''
    Remove result cluster using name string
    @param name:
    @type name:
    '''
    run_sql("DELETE FROM aidRESULTS "
            "WHERE personid like '%s.%%'"
            % name)


def personid_name_from_signature(sig):
    '''
    Find personid and name string of a signature
    @param sig:
    @type sig:
    '''
    ret = run_sql("select personid, name "
                  "from aidPERSONIDPAPERS "
                  "where bibref_table = %s and bibref_value = %s and bibrec = %s "
                  "and flag > '-2'"
                  , sig)
    assert len(ret) < 2, ret
    return ret

def personid_from_signature(sig):
    '''
    Find personid owner of a signature
    @param sig:
    @type sig:
    '''
    ret = run_sql("select personid, flag "
                  "from aidPERSONIDPAPERS "
                  "where bibref_table = %s and bibref_value = %s and bibrec = %s "
                  "and flag > '-2'"
                  , sig)
    assert len(ret) < 2, ret
    return ret

def get_signature_info(sig):
    '''
    Get personid and flag relative to a signature
    @param sig:
    @type sig:
    '''
    ret = run_sql("select personid, flag "
                  "from aidPERSONIDPAPERS "
                  "where bibref_table = %s and bibref_value = %s and bibrec = %s "
                  "order by flag"
                  , sig)
    return ret

def get_claimed_papers(pid):
    '''
    Find all papers which have been manually claimed
    @param pid:
    @type pid:
    '''
    return run_sql("select bibref_table, bibref_value, bibrec "
                   "from aidPERSONIDPAPERS "
                   "where personid = %s "
                   "and flag > %s",
                   (pid, 1))


def copy_personids():
    '''
    Make a copy of aidPERSONID tables to aidPERSONID*_copy tables for later comparison/restore
    '''
    run_sql("DROP TABLE IF EXISTS  `aidPERSONIDDATA_copy`")
    run_sql("CREATE TABLE `aidPERSONIDDATA_copy` ( "
            "`personid` BIGINT( 8 ) UNSIGNED NOT NULL , "
            "`tag` VARCHAR( 64 ) NOT NULL , "
            "`data` VARCHAR( 256 ) NOT NULL , "
            "`opt1` MEDIUMINT( 8 ) DEFAULT NULL , "
            "`opt2` MEDIUMINT( 8 ) DEFAULT NULL , "
            "`opt3` VARCHAR( 256 ) DEFAULT NULL , "
            "`last_updated` TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP , "
            "INDEX  `personid-b` (  `personid` ) , "
            "INDEX  `tag-b` (  `tag` ) , "
            "INDEX  `data-b` (  `data` ) , "
            "INDEX  `opt1` (  `opt1` ) , "
            "INDEX `timestamp-b` ( `last_updated` ) "
            ") ENGINE = MYISAM DEFAULT CHARSET = utf8")
    run_sql("INSERT INTO `aidPERSONIDDATA_copy` "
            "SELECT * "
            "FROM `aidPERSONIDDATA`")

    run_sql("DROP TABLE IF EXISTS `aidPERSONIDPAPERS_copy`")
    run_sql("CREATE TABLE `aidPERSONIDPAPERS_copy` ( "
            "`personid` bigint( 16 ) unsigned NOT NULL , "
            "`bibref_table` enum( '100', '700' ) NOT NULL , "
            "`bibref_value` mediumint( 8 ) unsigned NOT NULL , "
            "`bibrec` mediumint( 8 ) unsigned NOT NULL , "
            "`name` varchar( 256 ) NOT NULL , "
            "`flag` smallint( 2 ) NOT NULL DEFAULT '0', "
            "`lcul` smallint( 2 ) NOT NULL DEFAULT '0', "
            "`last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP , "
            "INDEX `personid-b` ( `personid` ) , "
            "INDEX `reftable-b` ( `bibref_table` ) , "
            "INDEX `refvalue-b` ( `bibref_value` ) , "
            "INDEX `rec-b` ( `bibrec` ) , "
            "INDEX `name-b` ( `name` ) , "
            "INDEX `pn-b` (`personid`, `name`) , "
            "INDEX `timestamp-b` (`last_updated`) , "
            "INDEX `flag-b` (`flag`) , "
            "INDEX `personid-flag-b` (`personid`,`flag`) , "
            "INDEX `ptvrf-b` (`personid`, `bibref_table`, `bibref_value`, `bibrec`, `flag`) "
            ") ENGINE = MyISAM DEFAULT CHARSET = utf8")
    run_sql("INSERT INTO `aidPERSONIDPAPERS_copy` "
            "SELECT * "
            "FROM `aidPERSONIDPAPERS")


def delete_empty_persons(remove=True):   ### remove_empty_authors
    '''
    Gets all empty authors (that is authors with no papers or other defined
    data) and by default deletes all data associated with them, except if
    specified differently.

    @param remove: delete empty authors
    @type remove: bool
    @return: empty author identifiers set(pid,)
    @rtype: set set(int,)
    '''
    pids_with_papers = set(pid[0] for pid in _select_from_aidpersonidpapers_where(select=['personid']))
    pids_tags = _select_from_aidpersoniddata_where(select=['personid', 'tag'])
    pids_with_data = set(pid for pid, tag in pids_tags)
    not_empty_pids = set(pid for pid, tag in pids_tags if tag in bconfig.NON_EMPTY_PERSON_TAGS)

    empty_pids = pids_with_data - (pids_with_papers | not_empty_pids)

    if empty_pids and remove:
        run_sql("""delete from aidPERSONIDDATA
                   where personid in %s"""
                   % list_2_SQL_str(empty_pids) )

    return empty_pids


def restore_personids():
    '''
    Restore personid tables from last copy saved with copy_personids
    '''
    run_sql("TRUNCATE  `aidPERSONIDDATA`")
    run_sql("INSERT INTO `aidPERSONIDDATA` "
            "SELECT * "
            "FROM `aidPERSONIDDATA_copy`")

    run_sql("TRUNCATE `aidPERSONIDPAPERS`")
    run_sql("INSERT INTO `aidPERSONIDPAPERS` "
            "SELECT * "
            "FROM `aidPERSONIDPAPERS_copy")

def resolve_affiliation(ambiguous_aff_string):
    """
    This is a method available in the context of author disambiguation in ADS
    only. No other platform provides the db table used by this function.
    @warning: to be used in an ADS context only.
    @param ambiguous_aff_string: Ambiguous affiliation string
    @type ambiguous_aff_string: str
    @return: The normalized version of the name string as presented in the database
    @rtype: str
    """
    if not ambiguous_aff_string or not bconfig.CFG_ADS_SITE:
        return "None"

    aff_id = run_sql("select aff_id from ads_affiliations where affstring=%s", (ambiguous_aff_string,))

    if aff_id:
        return aff_id[0][0]
    else:
        return "None"

def get_free_pids():
    '''
    Returns an iterator with all free personids.
    It's cool, because it fills holes.
    '''
    all_pids = frozenset(x[0] for x in chain(
            run_sql("select personid from aidPERSONIDPAPERS") ,
            run_sql("select personid from aidPERSONIDDATA")))
    return ifilter(lambda x: x not in all_pids, count())


def remove_results_outside(many_names):
    '''
    Delete results from aidRESULTS not including many_names
    @param many_names:
    @type many_names:
    '''
    many_names = frozenset(many_names)
    res_names = frozenset(x[0].split(".")[0] for x in run_sql("select personid from aidRESULTS"))

    for name in res_names - many_names:
        run_sql("delete from aidRESULTS where personid like '%s.%%'" % name)


def get_signatures_from_bibrefs(bibrefs):
    '''
    @param bibrefs:
    @type bibrefs:
    '''
    bib10x = ifilter(lambda x: x[0] == 100, bibrefs)
    bib10x_s = list_2_SQL_str(bib10x, lambda x: x[1])
    bib70x = ifilter(lambda x: x[0] == 700, bibrefs)
    bib70x_s = list_2_SQL_str(bib70x, lambda x: x[1])
    valid_recs = set(get_all_valid_bibrecs())

    if bib10x_s != '()':
        sig10x = run_sql("select 100, id_bibxxx, id_bibrec "
                         "from bibrec_bib10x "
                         "where id_bibxxx in %s"
                         % (bib10x_s,))
    else:
        sig10x = ()

    if bib70x_s != '()':
        sig70x = run_sql("select 700, id_bibxxx, id_bibrec "
                         "from bibrec_bib70x "
                         "where id_bibxxx in %s"
                         % (bib70x_s,))
    else:
        sig70x = ()

    return ifilter(lambda x: x[2] in valid_recs, chain(set(sig10x), set(sig70x)))


def get_all_valid_bibrecs():
    '''
    Returns a list of valid record ids
    '''
    collection_restriction_pattern = " or ".join(["980__a:\"%s\"" % x for x in bconfig.LIMIT_TO_COLLECTIONS])
    return perform_request_search(p="%s" % collection_restriction_pattern, rg=0)


def get_coauthor_pids(pid, exclude_bibrecs=None):
    '''
    Find personids sharing bibrecs with given pid, eventually excluding a given set of common bibrecs.
    @param pid:
    @type pid:
    @param exclude_bibrecs:
    @type exclude_bibrecs:
    '''
    papers = get_person_bibrecs(pid)
    if exclude_bibrecs:
        papers = set(papers) - set(exclude_bibrecs)

    if not papers:
        return []

    papers_s = list_2_SQL_str(papers)

    pids = run_sql("select personid,bibrec from aidPERSONIDPAPERS "
                   "where bibrec in %s and flag > -2" % papers_s)


    pids = set((int(p[0]), int(p[1])) for p in pids if p[0] != pid)
    pids = sorted([p[0] for p in pids])
    pids = groupby(pids)
    pids = [(key, len(list(val))) for key, val in pids if key != pid]
    pids = sorted(pids, key=lambda x: x[1], reverse=True)

    return pids

def get_doi_from_rec(recid):
    """
    Returns the doi of the paper like str if found.
    Otherwise returns None.
    0247 $2 DOI $a id
    """
    idx = run_sql("SELECT id_bibxxx, field_number FROM bibrec_bib02x WHERE id_bibrec = %s", (recid,))
    if idx:
        doi_id_s = list_2_SQL_str(idx, lambda x: x[0])
        doi = run_sql("SELECT id, tag, value FROM bib02x WHERE id in %s " % doi_id_s)
        if doi:
            grouped = groupby(idx, lambda x: x[1])
            doi_dict = dict((x[0], x[1:]) for x in doi)
            for group in grouped:
                elms = [x[0] for x in list(group[1])]
                found = False
                code = None
                for el in elms:
                    if doi_dict[el][0] == '0247_2' and doi_dict[el][1] == 'DOI':
                        found = True
                    elif doi_dict[el][0] == '0247_a':
                        code = doi_dict[el][1]
                    if found and code:
                        return code
        return None

def export_person(person_id):
    '''list of records table: personidpapers and personiddate check existing function for getting the records!!!
       exports a structure of dictunaries of tuples of [...] if strings, like:

       {'name':('namestring',),
        'repeatable_field':({'field1':('val1',)},{'field1':'val2'})}
    '''

    person_info = defaultdict(defaultdict)

    full_names = get_person_db_names_set(person_id)
    if full_names:
        splitted_names = [split_name_parts(n[0]) for n in full_names]
        splitted_names = [x + [len(x[2])] for x in splitted_names]
        max_first_names = max([x[4] for x in splitted_names])
        full_name_candidates = filter(lambda x: x[4] == max_first_names, splitted_names)
        full_name = create_normalized_name(full_name_candidates[0])


        person_info['names']['full_name'] = (full_name,)
        person_info['names']['surname'] = (full_name_candidates[0][0],)
        if full_name_candidates[0][2]:
            person_info['names']['first_names'] = (' '.join(full_name_candidates[0][2]),)
        person_info['names']['name_variants'] = ('; '.join([create_normalized_name(x) for x in splitted_names]),)

    bibrecs = get_person_bibrecs(person_id)

    recids_data = []
    for recid in bibrecs:
        recid_dict = defaultdict(defaultdict)
        recid_dict['INSPIRE-record-id'] = (str(recid),)
        recid_dict['INSPIRE-record-url'] = ('%s/record/%s' % (CFG_SITE_URL, str(recid)),)
        rec_doi = get_doi_from_rec(recid)
        if rec_doi:
            recid_dict['DOI'] = (str(rec_doi),)
        recids_data.append(recid_dict)

    person_info['records']['record'] = tuple(recids_data)


    person_info['identifiers']['INSPIRE_person_ID'] = (str(person_id),)


    canonical_names = get_canonical_names_by_pid(person_id)
    if canonical_names:
        person_info['identifiers']['INSPIRE_canonical_name'] = (str(canonical_names[0][0]),)
        person_info['profile_page']['INSPIRE_profile_page'] = ('%s/author/%s' % (CFG_SITE_URL, canonical_names[0][0]),)
    else:
        person_info['profile_page']['INSPIRE_profile_page'] = ('%s/author/%s' % (CFG_SITE_URL, str(person_id)),)

    orcids = get_orcids_by_pids(person_id)
    if orcids:
        person_info['identifiers']['ORCID'] = tuple(str(x[0]) for x in orcids)


    inspire_ids = get_inspire_ids_by_pids(person_id)
    if inspire_ids:
        person_info['identifiers']['INSPIREID'] = tuple(str(x[0]) for x in inspire_ids)


    return person_info


def export_person_to_foaf(person_id):
    '''
    Exports to foaf xml a dictionary of dictionaries or tuples of strings as retured by export_person
    '''

    infodict = export_person(person_id)

    def export(val, indent=0):
        if isinstance(val, dict):
            contents = list()
            for k, v in val.iteritems():
                if isinstance(v, tuple):
                    contents.append(''.join([ X[str(k)](indent=indent, body=export(c)) for c in v]))
                else:
                    contents.append(X[str(k)](indent=indent, body=export(v, indent=indent + 1)))
            return ''.join(contents)
        elif isinstance(val, str):
            return str(X.escaper(val))
        else:
            raise Exception('WHAT THE HELL DID WE GET HERE? %s' % str(val))

    return X['person'](body=export(infodict, indent=1))

def flush_data(table_name, column_names, args):
    '''
    docstring

    @param table_name:
    @type table_name:
    @param column_names:
    @type column_names:
    @param args:
    @type args:
    '''
    column_num = len(column_names)

    assert len(args) % column_num == 0, 'Trying to flush data in table %s. Wrong number of arguments passed.' % table_name

    values_tuple = "(%s)" % ", ".join(repeat("%s", column_num))
    multiple_values_tuple = ", ".join(repeat(values_tuple, len(args)/column_num))
    insert_query = 'insert into %s (%s) values %s' % (table_name, ", ".join(column_names), multiple_values_tuple)

    run_sql(insert_query, args)

def trancate_table(table_name):
    '''
    docstring

    @param table_name:
    @type table_name:
    '''
    run_sql("truncate table %s" % (table_name,))

def set_dense_index_ready():
    '''
    docstring
    '''
    run_sql("insert into aidDENSEINDEX (name_id,person_name,personids) values (%s,%s,%s)", (-1,'',''))

def set_inverted_lists_ready():
    '''
    docstring
    '''
    run_sql("insert into aidINVERTEDLISTS (qgram,inverted_list,list_cardinality) values (%s,%s,%s)", ('!'*QGRAM_LEN,'',0))

def get_inverted_lists(qgrams):
    '''
    docstring

    @param table_name:
    @type table_name:
    @return:
    @rtype:
    '''
    inverted_lists = run_sql("select inverted_list, list_cardinality from aidINVERTEDLISTS where qgram in %s"
                                % (list_2_SQL_str(qgrams, f=lambda x: "'%s'" % x), ))
    return inverted_lists

def get_indexable_name_personids(nameids):
    '''
    docstring

    @param table_name:
    @type table_name:
    @return:
    @rtype:
    '''
    name_personids = run_sql("select person_name, personids from aidDENSEINDEX where name_id in %s" % (list_2_SQL_str(nameids),) )
    return name_personids

def check_search_engine_status():
    '''
    docstring

    @return:
    @rtype:
    '''
    dense_index_exists = bool(run_sql("select * from aidDENSEINDEX where name_id=%s", (-1,)))
    inverted_lists_exists = bool(run_sql("select * from aidINVERTEDLISTS where qgram=%s", ('!'*QGRAM_LEN,) ))

    if dense_index_exists and inverted_lists_exists:
        return True

    return False
