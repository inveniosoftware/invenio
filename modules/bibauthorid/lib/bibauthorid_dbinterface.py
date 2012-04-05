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

try:
    import numpy
    import cPickle
    import zlib
except ImportError:
    pass

from itertools import groupby, count, ifilter, chain
from operator import itemgetter
from invenio.access_control_engine import acc_authorize_action
from invenio.search_engine import perform_request_search

from bibauthorid_name_utils import split_name_parts
from bibauthorid_name_utils import create_canonical_name
from bibauthorid_name_utils import create_normalized_name
from bibauthorid_general_utils import update_status
from dbquery import run_sql \
                    , OperationalError \
                    , ProgrammingError


def get_sql_time():
    '''
    Returns the time acoarding to the database. The type is datetime.datetime.
    '''
    return run_sql("select now()")[0][0]


def set_personid_row(person_id, tag, value, opt1=0, opt2=0, opt3=""):
    '''
    Inserts data and the additional options of a person by a given personid and tag.
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
    Change the value associated to the given tag for a certain person.
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
        plist = list_2_SQL_str(personid_list, lambda x: str(x))
        return run_sql("select personid, bibref_table, bibref_value, bibrec, flag \
                        from aidPERSONIDPAPERS \
                        where personid in %s" \
                       % plist)
    return ()


def del_person_not_manually_claimed_papers(pid):
    '''
    Deletes papers from a person which have not been manually claimed.
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
    uid = run_sql("select data from aidPERSONIDDATA where tag='uid' and personid = %s", (pid,))
    if uid:
        return uid[0][0]
    else:
        return None


def get_new_pesonid():
    pids = (run_sql("select max(personid) from aidPERSONIDDATA")[0][0],
            run_sql("select max(personid) from aidPERSONIDPAPERS")[0][0])

    pids = tuple(int(p) for p in pids if p != None)

    if len(pids) == 2:
        return max(*pids) + 1
    elif len(pids) == 1:
        return pids[0] + 1
    else:
        return 0


def get_existing_personids():
    try:
        pids_data = set(zip(*run_sql("select distinct personid from aidPERSONIDDATA"))[0])
    except IndexError:
        pids_data = set()

    try:
        pids_pap = set(zip(*run_sql("select distinct personid from aidPERSONIDPAPERS"))[0])
    except IndexError:
        pids_pap = set()

    return pids_data | pids_pap


def get_existing_result_clusters():
    return run_sql("select distinct personid from aidRESULTS")


def create_new_person(uid= -1, uid_is_owner=False):
    '''
    Create a new person. Set the uid as owner if requested.
    '''
    pid = get_new_pesonid()
    if uid_is_owner:
        set_personid_row(pid, 'uid', str(uid))
    else:
        set_personid_row(pid, 'user-created', str(uid))
    return pid

def create_new_person_from_uid(uid):
    return create_new_person(uid, uid_is_owner=True)

def new_person_from_signature(sig, name=None):
    '''
    Creates a new person from a signature.
    '''
    pid = get_new_pesonid()
    add_signature(sig, name, pid)
    return pid


def add_signature(sig, name, pid):
    '''
    Inserts a signature in personid.
    '''
    if not name:
        name = get_name_by_bibrecref(sig)
        name = create_normalized_name(split_name_parts(name))

    run_sql("INSERT INTO aidPERSONIDPAPERS "
            "(personid, bibref_table, bibref_value, bibrec, name) "
            "VALUES (%s, %s, %s, %s, %s)"
            , (pid, str(sig[0]), sig[1], sig[2], name))


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
    return run_sql("select personid, name "
                   "from aidPERSONIDPAPERS "
                   "where name like %s",
                   (regexpr,))

def get_personids_by_canonical_name(target):
    pid = run_sql("select personid from aidPERSONIDDATA where "
                  "tag='canonical_name' and data like %s", (target,))
    if pid:
        return run_sql("select personid, name from aidPERSONIDPAPERS "
                       "where personid=%s", (pid[0][0],))
    else:
        return []

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
        #We can supposed that this person didn't have a chance to get a canonical name yet
        #because it was not fully processed by it's creator. Anyway it's safe to try to create one
        #before failing miserably
        if not canonical:
            update_personID_canonical_names([pid])
        canonical = get_canonical_name(pid)

        #assert len(canonical) == 1
        #This condition cannot hold in case claims or update daemons are run in parallel
        #with this, as it can happen that a person with papers exists for wich a canonical name
        #has not been computed yet. Hence, it will be indexed next time, so it learns.
        #Each person should have at most one canonical name, so: 
        assert len(canonical) <= 1

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


def get_person_names_count(pid):
    '''
    Returns the set of name strings and count associated to a person id
    @param pid: ID of the person
    @type pid: ('2',)
    @param value: value to be written for the tag
    @type value: string
    '''
    return run_sql("select name, count(name) from aidPERSONIDPAPERS where "
                   "personid=%s and flag > -2 group by name", (pid,))


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
    '''

    pids = run_sql("select distinct personid from aidPERSONIDPAPERS where bibrec=%s", (bibrec,))

    if pids:
        return zip(*pids)[0]
    else:
        return []

def get_personids_and_papers_from_bibrecs(bibrecs, limit_by_name=None):
    '''
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
    papers = run_sql("select bibrec from aidPERSONIDPAPERS where personid=%s", (str(pid),))

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
            title_id = run_sql("SELECT id_bibxxx "
                               "FROM bibrec_bib24x "
                               "WHERE id_bibrec = %s",
                               (paper[2],))
            if title_id:
                title_id = zip(title_id)[0]
                title_id_s = list_2_SQL_str(title_id)
                title = run_sql("SELECT value "
                                "FROM bib24x "
                                "WHERE id in %s "
                                "AND tag = '245__a'"
                                % title_id_s)

                if title:
                    ret['title'] = title[0]

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
                date_id_s = list_2_SQL_str(date_id)
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
                experiment_id_s = list_2_SQL_str(experiment_id)
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


def insert_user_log(userinfo, personid, action, tag, value, comment='', transactionid=0, timestamp=None):
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

    if not timestamp:
        timestamp = run_sql('select now()')[0][0]

#    run_sql('insert into aidUSERINPUTLOG (transactionid,timestamp,userinfo,personid,action,tag,value,comment) values '
#            '(%(transactionid)s,%(timestamp)s,%(userinfo)s,%(personid)s,%(action)s,%(tag)s,%(value)s,%(comment)s)',
#            ({'transactionid':str(transactionid),
#              'timestamp':timestamp.timestamp,
#              'userinfo':str(userinfo),
#              'personid':str(personid),
#              'action':str(action),
#              'tag':str(tag),
#              'value':str(value),
#              'comment':str(comment)}))
    run_sql('insert into aidUSERINPUTLOG '
            '(transactionid,timestamp,userinfo,personid,action,tag,value,comment) values '
            '(%s,%s,%s,%s,%s,%s,%s,%s)',
            (transactionid, timestamp, userinfo, personid,
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
    @type pid: ('2',)
    @param papers: list of papers to confirm
    @type papers: (('100:7531,9024',),)
    @param gather_list: list to store the pids to be updated rather than
    calling update_personID_names_string_set
    @typer gather_list: set([('2',), ('3',)])
    '''
    for p in papers:
        bibref, rec = p[0].split(",")
        rec = int(rec)
        table, ref = bibref.split(":")
        ref = int(ref)

        run_sql("delete from aidPERSONIDPAPERS where personid=%s and bibrec=%s", (pid[0], rec))
        run_sql("delete from aidPERSONIDPAPERS where bibref_table=%s and "
                " bibref_value = %s and bibrec=%s",
                (table, ref, rec))

        add_signature([table, ref, rec], None, pid[0])
        run_sql("update aidPERSONIDPAPERS "
                "set personid = %s "
                ", flag = %s "
                ", lcul = %s "
                "where bibref_table = %s "
                "and bibref_value = %s "
                "and bibrec = %s"
                , (str(pid[0]), '2', user_level,
                   table, ref, rec))

    update_personID_canonical_names(pid)

def reject_papers_from_person(pid, papers, user_level=0):
    '''
    Confirms the negative relationship between pid and paper, as from user input.
    @param pid: id of the person
    @type pid: ('2',)
    @param papers: list of papers to confirm
    @type papers: (('100:7531,9024',),)
    '''
    for p in papers:
        rec = p[0].split(",")[1]
        run_sql("update aidPERSONIDPAPERS "
                "set flag = %s, lcul = %s "
                "where personid=%s and bibrec=%s",
                ('-2', user_level, str(pid[0]), rec))


def reset_papers_flag(pid, papers):
    '''
    Resets the flag associated to the papers to '0'
    @param papers: list of papers to confirm
    @type papers: (('100:7531,9024',),)
    @param gather_list: list to store the pids to be updated rather than
    calling update_personID_names_string_set
    @typer gather_list: set([('2',), ('3',)])
    '''
    for p in papers:
        bibref, rec = p[0].split(",")
        table, ref = bibref.split(":")
        run_sql("update aidPERSONIDPAPERS "
                "set flag = %s, lcul = %s "
                "where bibref_table = %s "
                "and bibref_value = %s "
                "and bibrec = %s",
                ('0', '0',
                table, ref, rec))


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
    Returns the bibrecs with modification date more recent then date, or all
    the bibrecs if no date is specified.
    @param date: date
    '''
    return [p[0] for p in run_sql(
               "select id from bibrec where modification_date > %s", (date,))]


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

def get_bibrefrec_subset(table, papers, refs):
    table = "bibrec_bib%sx" % str(table)[:-1]
    contents = run_sql("select id_bibrec, id_bibxxx from %s" % table)
    papers = set(papers)
    refs = set(refs)

    return ifilter(lambda x: x[0] in papers and x[1] in refs, contents)

def get_deleted_papers():
    return run_sql("select o.id_bibrec from bibrec_bib98x o, "
                   "(select i.id as iid from bib98x i "
                   "where value = 'DELETED' "
                   "and tag like '980__a') as dummy "
                   "where o.id_bibxxx = dummy.iid")

#bibauthorid_maintenance personid update private methods
def update_personID_canonical_names(persons_list=None, overwrite=False, suggested='',
                                    verbose_prints=False):
    '''
    Updates the personID table creating or updating canonical names for persons
    @param: persons_list: persons to consider for the update  (('1'),)
    @param: overwrite: if to touch already existing canonical names
    @param: suggested: string to suggest a canonical name for the person
    '''
    if not persons_list:
        persons_list = [x[0] for x in run_sql('select distinct personid from aidPERSONIDPAPERS')]

    for idx, pid in enumerate(persons_list):
        if verbose_prints:
            update_status(float(idx) / float(len(persons_list)))
        current_canonical = run_sql("select data from aidPERSONIDDATA where "
                                    "personid=%s and tag=%s", (pid, 'canonical_name'))

        if overwrite or len(current_canonical) == 0:
            names = get_person_names_count(pid)

            names = sorted(names, key=lambda k: k[1], reverse=True)
            if len(names) < 1 and not suggested:
                continue
            else:
                if suggested:
                    canonical_name = suggested
                else:
                    canonical_name = create_canonical_name(names[0][0])

                run_sql("delete from aidPERSONIDDATA where personid=%s and tag=%s",
                        (pid, 'canonical_name'))

                existing_cnames = run_sql("select data from aidPERSONIDDATA "
                                          "where tag=%s and data like %s",
                                          ('canonical_name', str(canonical_name) + '%'))

                existing_cnames = set(name[0] for name in existing_cnames)
                for i in count(1):
                    cur_try = canonical_name + '.' + str(i)
                    if cur_try not in existing_cnames:
                        canonical_name = cur_try
                        break

                run_sql("insert into aidPERSONIDDATA (personid, tag, data) values (%s,%s,%s) ",
                         (pid, 'canonical_name', canonical_name))

    if verbose_prints:
        update_status(1.)


def personid_get_recids_affected_since(last_timestamp):
    '''
    Returns a list of recids which have been manually changed since timestamp
    @TODO: extend the system to track and signal even automatic updates (unless a full reindex is
        acceptable in case of magic automatic update)
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

    return list(vset) # I'm not sure about this cast. It might work without it.


def get_all_paper_records(pid, claimed_only=False):
    if not claimed_only:
        return run_sql("SELECT distinct bibrec FROM aidPERSONIDPAPERS WHERE personid = %s", (str(pid),))
    else:
        return run_sql("SELECT distinct bibrec FROM aidPERSONIDPAPERS WHERE "
                       "personid = %s and flag=2 or flag=-2", (str(pid),))



def get_all_names_from_personid():
    pids = run_sql("SELECT DISTINCT personid "
                   "FROM aidPERSONIDPAPERS")

    return ((p[0], [n[0] for n in run_sql(
                    "SELECT DISTINCT name "
                    "FROM aidPERSONIDPAPERS "
                    "WHERE personid = %s", p)]
                    ) for p in pids)


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
    assert len(grouped) > 0
    grouped_s = list_2_SQL_str(grouped, lambda x: str(x[0]))

    ret = {}
    for arg in args:
        qry = run_sql("SELECT value "
                      "FROM %s "
                      "WHERE tag LIKE '%s' "
                      "AND id IN %s" %
                      (target_table, arg, grouped_s))
        ret[arg] = [q[0] for q in qry]

    return ret

def get_name_by_bibrecref(bib):
    '''
    @param bib: bibrefrec or bibref
    @type bib: (mark, bibref, bibrec) OR (mark, bibref)
    '''
    table = "bib%sx" % (str(bib[0])[:-1])
    refid = bib[1]
    tag = "%s__a" % bib[0]
    ret = run_sql("select value from %s where id = '%s' and tag = '%s'" % (table, refid, tag))

    # if zero - check if the garbage collector has run
    assert len(ret) == 1
    return ret[0][0]


def get_collaboration(bibrec):
    bibxxx = run_sql("select id_bibxxx from bibrec_bib71x where id_bibrec = %s", (str(bibrec),))

    if len(bibxxx) == 0:
        return ()

    bibxxx = list_2_SQL_str(bibxxx, lambda x: str(x[0]))

    ret = run_sql("select value from bib71x where id in %s and tag like '%s'" % (bibxxx, "710__g"))
    return [r[0] for r in ret]

def get_key_words(bibrec):
    bibxxx = run_sql("select id_bibxxx from bibrec_bib69x where id_bibrec = %s", (str(bibrec),))

    if len(bibxxx) == 0:
        return ()

    bibxxx = list_2_SQL_str(bibxxx, lambda x: str(x[0]))

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


def get_bib10x():
    return run_sql("select id, value from bib10x where tag like %s", ("100__a",))

def get_bib70x():
    return run_sql("select id, value from bib70x where tag like %s", ("700__a",))

def filter_newer_bibs(bibs, last_run):
    """
    Returns all bibrefrecs which have been modified since
    'last_run' and are in bibs
    @param bibs: a list of bibrefrecs
    @type bibs: list of strings
    @param last_run: date, YYYY-MM-DD HH:MM:SS
    @type last_run: string
    @return: a list with all modified bibrefrecs
    @type return: a tuple of strings
    """
    def filty(bib):
        return len(run_sql("select last_updated "
                "from aidPERSONIDPAPERS "
                "where bibref_table = %s "
                "and bibref_value = %s "
                "and bibrec = %s "
                "and last_updated < %s"
                , (str(bib[0]), bib[1], bib[2],
                   last_run))) > 0
    return ifilter(filty, bibs)


class bib_matrix:
    '''
    This small class contains the sparse matrix
    and encapsulates it.
    '''
    # please increment this value every time you
    # change the output of the comparison functions
    current_comparison_version = 7

    special_items = ((None, -3., 'N'), ('+', -2., '+'), ('-', -1., '-'))
    special_symbols = dict((x[0], (x[1], x[2])) for x in special_items)
    special_numbers = dict((x[1], (x[0], x[2])) for x in special_items)
    special_strings = dict((x[2], (x[0], x[1])) for x in special_items)

    def __init__(self, cluster_set=None):
        if cluster_set:
            bibs = chain(*(cl.bibs for cl in cluster_set.clusters))
            self._bibmap = dict((b[1], b[0]) for b in enumerate(bibs))
            width = len(self._bibmap)
            size = ((width - 1) * width) / 2
            self._matrix = bib_matrix.create_empty_matrix(size)

    @staticmethod
    def create_empty_matrix(lenght):
        ret = numpy.ndarray(shape=(lenght, 2), dtype=float, order='C')
        ret.fill(bib_matrix.special_symbols[None][0])
        return ret

    def _resolve_entry(self, bibs):
        entry = sorted([self._bibmap[bib] for bib in bibs])
        assert entry[0] < entry[1]
        return entry[0] + ((entry[1] - 1) * entry[1]) / 2

    def __setitem__(self, bibs, val):
        entry = self._resolve_entry(bibs)

        if val in self.special_symbols:
            num = self.special_symbols[val][0]
            val = (num, num)

        self._matrix[entry] = val

    def __getitem__(self, bibs):
        entry = self._resolve_entry(bibs)
        ret = self._matrix[entry]
        if ret[0] in self.special_numbers:
            return self.special_numbers[ret[0]][0]
        return ret[0], ret[1]

    @staticmethod
    def __pickle_tuple(tupy):
        '''
        tupy can be a very special iterable. It may contain:
            * (float, float)
            * None
            * '+', '-' or '?'
        '''
        def to_str(elem):
            if elem[0] in bib_matrix.special_numbers:
                return "%s|" % bib_matrix.special_numbers[elem[0]][1]
            return "%f:%f|" % (elem[0], elem[1])

        strs = map(to_str, tupy)
        if strs:
            strs[-1] = strs[-1][:-1]
        return "".join(strs)

    @staticmethod
    def __unpickle_tuple(tupy):
        '''
        tupy must be an object created by pickle_tuple.
        '''
        def from_str(elem, index, total):
            if index % 100000 == 0:
                update_status(float(index) / float(total))
            if elem in bib_matrix.special_strings:
                nummy = bib_matrix.special_strings[elem][1]
                return (nummy, nummy)
            fls = elem.split(":")
            assert len(fls) == 2
            return (float(fls[0]), float(fls[1]))

        print "Loading the cache..."
        strs = tupy.split("|")
        if strs == ['']:
            strs = []
        ret = bib_matrix.create_empty_matrix(len(strs))
        for i, stri in enumerate(strs):
            ret[i][0], ret[i][1] = from_str(stri, i, len(strs))
        update_status(1)
        print ""
        return ret

    def load(self, name):
        '''
        This method will load the matrix from the
        database.
        '''
        row = run_sql("select bibmap, matrix "
                      "from aidPROBCACHE "
                      "where cluster like %s",
                      (name,))
        if len(row) == 0:
            self._bibmap, self._matrix = None, None
            return False
        elif len(row) == 1:
            bibmap_vs = zlib.decompress(row[0][0])
            bibmap_v = cPickle.loads(bibmap_vs)
            rec_v, self._bibmap = bibmap_v
            if (rec_v != bib_matrix.current_comparison_version or
                bib_matrix.current_comparison_version < 0): # you can use negative
                                                            # version to recalculate
                self._bibmap, self._matrix = None, None
                return False

            matrix_s = zlib.decompress(row[0][1])
            self._matrix = bib_matrix.__unpickle_tuple(matrix_s)
            return self._bibmap != None and self._matrix != None
        else:
            assert not "aidPROBCACHE is corrupted"
            return False

    def store(self, name):
        bibmap_v = (bib_matrix.current_comparison_version, self._bibmap)
        bibmap_vs = cPickle.dumps(bibmap_v)
        bibmap_vsc = zlib.compress(bibmap_vs)

        matrix_s = bib_matrix.__pickle_tuple(self._matrix)
        matrix_sc = zlib.compress(matrix_s)

        run_sql("delete from aidPROBCACHE where cluster like %s", (name,))
        run_sql("insert low_priority "
                "into aidPROBCACHE "
                "set cluster = %s, "
                "bibmap = %s, "
                "matrix = %s",
                (name, bibmap_vsc, matrix_sc))


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


def get_wrong_names():
    '''
    Returns a generator with all wrong names in aidPERSONIDPAPERS.
    Every element is (table, ref, correct_name).
    '''

    bib100 = dict(((x[0], create_normalized_name(split_name_parts(x[1]))) for x in get_bib10x()))
    bib700 = dict(((x[0], create_normalized_name(split_name_parts(x[1]))) for x in get_bib70x()))

    pidnames100 = run_sql("select distinct  bibref_value, name from aidPERSONIDPAPERS "
                          " where bibref_table='100'")
    pidnames700 = run_sql("select distinct  bibref_value, name from aidPERSONIDPAPERS "
                          " where bibref_table='700'")

    wrong100 = set(('100', x[0], bib100.get(x[0], None)) for x in pidnames100 if x[1] != bib100.get(x[0], None))
    wrong700 = set(('700', x[0], bib700.get(x[0], None)) for x in pidnames700 if x[1] != bib700.get(x[0], None))

    total = len(wrong100) + len(wrong700)

    return chain(wrong100, wrong700), total


def check_personid_papers():
    '''
    Checks all invariants of personid
    '''
    ret = True

    pids = run_sql("select distinct personid from aidPERSONIDPAPERS")
    for pid in pids:
        pid = pid[0]
        recs = run_sql("select bibrec from aidPERSONIDPAPERS where personid = %s", (pid,))
        recs = [rec[0] for rec in recs]
        for rec in set(recs):
            recs.remove(rec)

        if recs:
            ret = False
            print "Person %d has duplicated papers: %s" % (pid, str(tuple(set(recs))))

    recs = run_sql("select distinct bibrec from aidPERSONIDPAPERS")
    for rec in recs:
        rec = rec[0]
        refs = list(run_sql("select bibref_table, bibref_value from aidPERSONIDPAPERS where bibrec = %s and flag > %s", (rec, "-2")))

        for ref in set(refs):
            refs.remove(ref)

        if refs:
            ret = False
            refs = sorted(refs)
            refs = groupby(refs)
            refs = ["Found %s:%s %d times." % (key[0], key[1], len(list(data)) + 1) for key, data in refs]
            print "Paper %d has duplicated signatures:" % rec
            for ref in refs:
                print "\t%s" % ref

    wrong_names, count = get_wrong_names()

    if count > 0:
        ret = False
        print "%d corrupted names in aidPERSONIDPAPERS." % count
        for wrong_name in wrong_names:
            if wrong_name[2]:
                print "Outdated name, '%s'(%s:%d)." % (wrong_name[2], wrong_name[0], wrong_name[1])
            else:
                print "Invalid id(%s:%d)." % (wrong_name[0], wrong_name[1])

    return ret


def repair_personid():
    '''
    This should make check_personid_papers() to return true.
    '''
    pids = run_sql("select distinct personid from aidPERSONIDPAPERS")
    lpids = len(pids)
    for i, pid in enumerate((p[0] for p in pids)):
        update_status(float(i) / lpids, "Checking per-pid...")
        rows = run_sql("select bibrec, bibref_table, bibref_value, flag "
                       "from aidPERSONIDPAPERS where personid = %s", (pid,))

        rows = ((k, list(d))
                for k, d in groupby(sorted(rows, key=itemgetter(0)), itemgetter(0)))

        for rec, sigs in rows:
            if len(sigs) > 1:
                claimed = [sig for sig in sigs if sig[3] > 1]
                rejected = [sig for sig in sigs if sig[3] < -1]

                if len(claimed) == 1:
                    sigs.remove(claimed[0])
                elif len(claimed) == 0 and len(rejected) == 1:
                    sigs.remove(rejected[0])

                for sig in set(sigs):
                    run_sql("delete from aidPERSONIDPAPERS "
                            "where personid = %s "
                            "and bibrec = %s "
                            "and bibref_table = %s "
                            "and bibref_value = %s "
                            "and flag = %s"
                            , (pid, sig[0], sig[1], sig[2], sig[3]))
    update_status(1., "Done with per-pid fixing.")
    print ""

    recs = run_sql("select distinct bibrec from aidPERSONIDPAPERS")
    lrecs = len(recs)
    for i, rec in enumerate((r[0] for r in recs)):
        update_status(float(i) / lrecs, "Checking per-rec...")
        rows = run_sql("select bibref_table, bibref_value, flag from aidPERSONIDPAPERS "
                       "where bibrec = %s", (rec,))
        kfuc = itemgetter(slice(0, 2))
        rows = ((k, map(itemgetter(2), d)) for k, d in groupby(sorted(rows), kfuc))

        for bibref, flags in rows:
            if len(flags) > 1:
                claimed = sum(1 for f in flags if f > 1)
                rejected = sum(1 for f in flags if f < -1)

                if claimed == 1:
                    run_sql("delete from aidPERSONIDPAPERS "
                            "where bibrec = %s "
                            "and bibref_table = %s "
                            "and bibref_value = %s "
                            "and flag <> %s"
                            , (rec, bibref[0], bibref[1], 2))
                elif claimed == 0 and rejected == 1:
                    run_sql("delete from aidPERSONIDPAPERS "
                            "where bibrec = %s "
                            "and bibref_table = %s "
                            "and bibref_value = %s "
                            "and flag <> %s"
                            , (rec, bibref[0], bibref[1], -2))
                else:
                    run_sql("delete from aidPERSONIDPAPERS "
                            "where bibrec = %s "
                            "and bibref_table = %s "
                            "and bibref_value = %s"
                            , (rec, bibref[0], bibref[1]))
    update_status(1., "Done with per-rec fixing.")
    print ""

    update_status(0 / 1, "Fixing wrong names...")
    wrong_names, count = get_wrong_names()
    for i, w in enumerate(wrong_names):
        update_status(i / count, "Fixing wrong names...")
        if w[2]:
            run_sql("update aidPERSONIDPAPERS set name=%s where bibref_table=%s and bibref_value=%s",
                    (w[2], w[0], w[1]))
        else:
            run_sql("delete from aidPERSONIDPAPERS where bibref_table=%s and bibref_value=%s",
                    (w[2], w[0], w[1]))

    update_status(1., "Fixed all wrong names.")
    print ""


def get_all_bibrecs():
    return [x[0] for x in run_sql("select distinct bibrec from aidPERSONIDPAPERS")]


def remove_all_bibrecs(bibrecs):
    bibrecs_s = list_2_SQL_str(bibrecs)
    run_sql("delete from aidPERSONIDPAPERS where bibrec in %s" % bibrecs_s)


def empty_results_table():
    run_sql("TRUNCATE aidRESULTS")


def save_cluster(named_cluster):
    name, cluster = named_cluster
    for bib in cluster.bibs:
        run_sql("INSERT INTO aidRESULTS "
                "(personid, bibref_table, bibref_value, bibrec) "
                "VALUES (%s, %s, %s, %s) "
                , (name, str(bib[0]), bib[1], bib[2]))


def personid_name_from_signature(sig):
    return run_sql("select personid, name "
                   "from aidPERSONIDPAPERS "
                   "where bibref_table = %s and bibref_value = %s and bibrec = %s"
                   , sig)


def copy_personids():
    run_sql("DROP TABLE IF EXISTS  `aidPERSONIDDATA_copy`")
    run_sql("CREATE TABLE `aidPERSONIDDATA_copy` ( "
            "`personid` BIGINT( 16 ) UNSIGNED NOT NULL , "
            "`tag` VARCHAR( 64 ) NOT NULL , "
            "`data` VARCHAR( 256 ) NOT NULL , "
            "`opt1` MEDIUMINT( 8 ) DEFAULT NULL , "
            "`opt2` MEDIUMINT( 8 ) DEFAULT NULL , "
            "`opt3` VARCHAR( 256 ) DEFAULT NULL , "
            "KEY  `personid-b` (  `personid` ) , "
            "KEY  `tag-b` (  `tag` ) , "
            "KEY  `data-b` (  `data` ) , "
            "KEY  `opt1` (  `opt1` ) "
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
            "KEY `personid-b` ( `personid` ) , "
            "KEY `reftable-b` ( `bibref_table` ) , "
            "KEY `refvalue-b` ( `bibref_value` ) , "
            "KEY `rec-b` ( `bibrec` ) , "
            "KEY `name-b` ( `name` ) , "
            "KEY `timestamp-b` ( `last_updated` ) , "
            "KEY `ptvrf-b` ( `personid` , `bibref_table` , `bibref_value` , `bibrec` , `flag` ) "
            ") ENGINE = MyISAM DEFAULT CHARSET = utf8")
    run_sql("INSERT INTO `aidPERSONIDPAPERS_copy` "
            "SELECT * "
            "FROM `aidPERSONIDPAPERS")


def get_possible_personids_from_paperlist_old(bibrecreflist):
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

    return sorted(pid_list, key=lambda k: len(k[2]), reverse=True)

