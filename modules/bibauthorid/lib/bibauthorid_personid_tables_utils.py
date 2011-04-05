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
"""
bibauthorid_personid_tables_utils
    Bibauthorid's personid related DB handler
"""
import sys
import time
import threading
import datetime
import bibauthorid_config as bconfig

from bibauthorid_utils import split_name_parts, create_normalized_name, create_canonical_name
from bibauthorid_utils import clean_name_string, get_field_values_on_condition
from bibauthorid_authorname_utils import soft_compare_names
from bibauthorid_tables_utils import get_bibrefs_from_name_string

from threading import Thread

try:
    from dbquery import run_sql, close_connection
    from dbquery import OperationalError, ProgrammingError
    from access_control_engine import acc_authorize_action
#    from webuser import collect_user_info
    from data_cacher import DataCacher
except ImportError:
    from invenio.data_cacher import DataCacher
    from invenio.dbquery import run_sql
    from invenio.dbquery import OperationalError, ProgrammingError
    from invenio.access_control_engine import acc_authorize_action
#    from invenio.webuser import collect_user_info

DATA_CACHERS = []


class PersonIDStatusDataCacher(DataCacher):
    '''
    Data Cacher to monitor the existence of personid data
    '''
    def __init__(self):
        def cache_filler():
            try:
                res = run_sql("SELECT count(personid) FROM aidPERSONID "
                              "where tag='paper'")
                if res and res[0] and res[0][0] > 0:
                    return True
                else:
                    return False
            except Exception:
                # database problems, return empty cache
                return False

        def timestamp_verifier():
            dt = datetime.datetime.now()
            td = dt - datetime.timedelta(hours=2)
            return td.strftime("%Y-%m-%d %H:%M:%S")

        DataCacher.__init__(self, cache_filler, timestamp_verifier)


def create_new_person(uid, uid_is_owner=False):
        #creates a new person
        pid = run_sql("select max(personid) from aidPERSONID")[0][0]

        if pid:
            try:
                pid = int(pid)
            except (ValueError, TypeError):
                pid = -1
            pid += 1
        if uid_is_owner:
            set_person_data(pid, 'uid', str(uid))
            set_person_data(pid, 'user-created', str(uid))
        else:
            set_person_data(pid, 'user-created', str(uid))

        return pid

def get_pid_from_name_bibrec(bibrecs, name_string):
    '''
    Finds a Person ID for a specific name on a specific list of record IDs

    @param bibrecs: list of record IDs
    @type bibrecs: list of int
    @param name_string: the name of an author on the papers
    @type name_string: string

    @return: a Person ID
    @rtype: int
    '''
    found_bibrecs = bibrecs
    surname = name_string

    bibrec_names = []
    for b in found_bibrecs:
        bibrec_names.append([b, get_field_values_on_condition(b, source='API', get_table=['100','700'], get_tag='a')])

    for n in bibrec_names:
        for i in list(n[1]):
            if soft_compare_names(surname.encode('utf-8'), i.encode('utf-8')) < 0.4:
                if i in n[1]:
                    n[1].remove(i)
    #bibrec_names = [[78, set([u'M\xfcck, W'])]]

    #what is left are only suitable names for each record.
    bibrefrecs = []
    for bibrec in bibrec_names:
        for name in bibrec[1]:
            bibrefs = get_bibrefs_from_name_string(name.encode('utf-8'))
            if len(bibrefs) < 1:
                continue
            for bibref in bibrefs[0][0].split(','):
                bibrefrecs.append(str(bibref)+','+str(bibrec[0]))
    #bibrefrec = ['100:116,78', '700:505,78']

    brr = [[i] for i in bibrefrecs]
    possible_persons = get_possible_personids_from_paperlist(brr)
    #[[0L, ['700:316,10']]]
    possible_persons = sorted(possible_persons, key = lambda k: len(k[1]))

    return possible_persons


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

def get_persons_with_open_tickets_list():
    '''
    Finds all the persons with open tickets and returns pids and count of tickets
    @return: [[pid,ticket_count]]
    '''
    try:
        return run_sql('select personid,count(distinct(flag)) from aidPERSONID use index (`ptf-b`)'
                   'where personid in (select distinct personid from aidPERSONID use index (`ptf-b`) '
                   'where tag like "rt_%") and tag like "rt_%" group by personid ')
    except (OperationalError, ProgrammingError):
        return run_sql('select personid,count(distinct(flag)) from aidPERSONID '
                   'where personid in (select distinct personid from aidPERSONID '
                   'where tag like "rt_%") and tag like "rt_%" group by personid ')

def get_request_ticket(person_id, matching=None, ticket_id=None):
    '''
    Retrieves one or many requests tickets from a person
    @param: person_id: person id integer
    @param: matching: couple of values to match ('tag','value')
    @param: ticket_id: ticket id (flag) value
    @returns: [[[('tag','value')],ticket_id]]
        [[[('a', 'va'), ('b', 'vb')], 1L],[[('b', 'daOEIaoe'), ('a', 'caaoOUIe')], 2L]]
    '''
    use_index = True
    tickets = []

    if ticket_id:
        rows= []

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
        tickets.append([ticket, row[0][2]])

    return tickets


def update_request_ticket(person_id, tag_data_tuple, ticket_id=None):
    '''
    Creates/updates a request ticket for a personID
    @param: personid int
    @param: tag_data_tuples 'image' of the ticket: (('paper','700:316,10'),('owner','admin'),('external_id','ticket_18'))
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


def update_personID_canonical_names(persons_list=[], overwrite=False, suggested=''):
    '''
    Updates the personID table creating or updating canonical names for persons
    @param: persons_list: persons to consider for the update  (('1'),)
    @param: overwrite: if to touch already existing canonical names
    @param: suggested: string to suggest a canonical name for the person
    '''
    use_index = True

    if not persons_list:
        persons_list = run_sql('select distinct personid from aidPERSONID')

    for pid in persons_list:
        current_canonical = ""

        try:
            current_canonical = run_sql("select data from aidPERSONID use index (`ptf-b`) where personid=%s and tag=%s", (pid[0], 'canonical_name'))
        except (ProgrammingError, OperationalError):
            current_canonical = run_sql("select data from aidPERSONID where personid=%s and tag=%s", (pid[0], 'canonical_name'))
            use_index = False

        if (not overwrite) and len(current_canonical) > 0:
            continue
        else:
            names = []

            if use_index:
                names = run_sql("select data,flag from aidPERSONID use index (`ptf-b`) where personid=%s and tag=%s", (pid[0], 'gathered_name'))
            else:
                names = run_sql("select data,flag from aidPERSONID where personid=%s and tag=%s", (pid[0], 'gathered_name'))

            names = sorted(names, key=lambda k: k[1], reverse=True)
            if len(names) < 1 and not suggested:
                continue
            else:
                if suggested:
                    canonical_name = suggested
                else:
                    canonical_name = create_canonical_name(names[0][0])

                run_sql("delete from aidPERSONID where personid=%s and tag=%s", (pid[0], 'canonical_name'))
                existing_cnames = []

                if use_index:
                    existing_cnames = run_sql("select data from aidPERSONID use index (`tdf-b`) where tag=%s and data like %s", ('canonical_name', str(canonical_name) + '%'))
                else:
                    existing_cnames = run_sql("select data from aidPERSONID where tag=%s and data like %s", ('canonical_name', str(canonical_name) + '%'))

                max_idx = 0

                for i in existing_cnames:
                    this_cid = 0

                    if i[0].count("."):
                        this_cid = i[0].split(".")[-1]

                    max_idx = max(max_idx, int(this_cid))

                canonical_name = canonical_name + '.' + str(max_idx + 1)
                run_sql("insert into aidPERSONID (personid,tag,data) values (%s,%s,%s) ", (pid[0], 'canonical_name', canonical_name))


def update_personID_table_from_paper(papers_list=[], personid=None):
    '''
    Updates the personID table removing the bibrec/bibrefs couples no longer existing (after a paper has been
    updated (name changed))
    @param: list of papers to consider for the update (bibrecs) (('1'),)
    @param: limit to given personid (('1',),)
    '''

    personid_q = ''
    if personid:
        personid_q = '( '
        for p in personid:
            personid_q += " '" + str(p[0]) + "',"
        personid_q = personid_q[0:len(personid_q)-1]   + ' )'

    if not papers_list and personid_q:
        papers_list = []
        try:
            bibrefrec_list = run_sql("select data from aidPERSONID use index (`ptf-b`) where tag='paper' and personid in %s" % (personid_q))
        except (ProgrammingError, OperationalError):
            bibrefrec_list = run_sql("select data from aidPERSONID where tag='paper' and personid in %s" % (personid_q))
            
        for b in bibrefrec_list:
            papers_list.append(b)
               
    elif not papers_list:
        papers_list = []
        try:
            bibrefrec_list = run_sql("select data from aidPERSONID use index (`tdf-b`) where tag='paper'")
        except (ProgrammingError, OperationalError):
            bibrefrec_list = run_sql("select data from aidPERSONID where tag='paper'")
            
        for b in bibrefrec_list:
            papers_list.append(b)
            
    if bconfig.TABLES_UTILS_DEBUG:
            print "update_personID_table_from_paper: bibrefrec selected:  " + str(len(papers_list))
    
    bibreclist = []
    for p in papers_list:
        try:
            br = [p[0].split(',')[1]]
            if br not in bibreclist:
                bibreclist.append(br)
            if bconfig.TABLES_UTILS_DEBUG:
                print 'update_personID_table_from_paper: Selected ' + str(p[0].split(',')[1]) +' from '+str(p)
        except IndexError:
            continue
            
    full_papers_list = papers_list
    papers_list = bibreclist
    if bconfig.TABLES_UTILS_DEBUG:
        print "update_personID_table_from_paper: After duplicate removing remaining bibrecs:  " + str(len(papers_list))
        
    for paper in papers_list:
        fullbibrefs100 = run_sql("select id_bibxxx from bibrec_bib10x where id_bibrec=%s", (paper[0],))
        fullbibrefs700 = run_sql("select id_bibxxx from bibrec_bib70x where id_bibrec=%s", (paper[0],))

        fullbibrefs100str = '( '
        for i in fullbibrefs100:
            fullbibrefs100str += " '" + str(i[0]) + "',"
        fullbibrefs100str = fullbibrefs100str[0:len(fullbibrefs100str) - 1] + ' )'

        fullbibrefs700str = '( '
        for i in fullbibrefs700:
            fullbibrefs700str += " '" + str(i[0]) + "',"
        fullbibrefs700str = fullbibrefs700str[0:len(fullbibrefs700str) - 1] + ' )'
        #NOTE: values are taken only from bibrec_bibXXX tables which are considered safe.
        if len(fullbibrefs100) >= 1:
            sqlquery = "select id from bib10x where tag='100__a' and id in %s" % fullbibrefs100str
            bibrefs100 = run_sql(sqlquery)
        else:
            bibrefs100 = []
        if len(fullbibrefs700) >= 1:
            sqlquery = "select id from bib70x where tag='700__a' and id in %s" % fullbibrefs700str
            bibrefs700 = run_sql(sqlquery)
        else:
            bibrefs700 = []

        bibrecreflist = []
        for i in bibrefs100:
            bibrecreflist.append('100:' + str(i[0]) + ',' + str(paper[0]))
        for i in bibrefs700:
            bibrecreflist.append('700:' + str(i[0]) + ',' + str(paper[0]))

        if bconfig.TABLES_UTILS_DEBUG:
            print "update_personID_table_from_paper: searching for pids owning " + str(paper[0])

        pid_rows = []

        if personid_q:
            try:
                query = "select id,personid,tag,data,flag,lcul from aidPERSONID use index (`tdf-b`,`ptf-b`) where tag='paper'  and personid in %s" %  personid_q + " and data like %s"
                pid_rows = run_sql(query, ('%,' + str(paper[0]),))
            except (ProgrammingError, OperationalError):
                query = "select id,personid,tag,data,flag,lcul from aidPERSONID where tag='paper'  and personid in %s" %  personid_q + " and data like %s"
                pid_rows = run_sql(query, ('%,' + str(paper[0]),))
        else:
            try:
                pid_rows = run_sql("select id,personid,tag,data,flag,lcul from aidPERSONID use index (`tdf-b`,`ptf-b`) where tag='paper' and data like %s", ('%,' + str(paper[0]),))
            except (ProgrammingError, OperationalError):
                pid_rows = run_sql("select id,personid,tag,data,flag,lcul from aidPERSONID where tag='paper' and data like %s", ('%,' + str(paper[0]),))

        #finally, if a bibrec/ref pair is in the authornames table but not in this list that name of that paper
        #is no longer existing and must be removed from the table. The new one will be addedd by the
        #update procedure in future; this entry will be risky becouse the garbage collector may
        #decide to kill the bibref in the bibX0x table
        for row in pid_rows:
            if row[3] not in bibrecreflist:
                other_bibrefs = [b[3] for b in pid_rows if b[1] == row[1] and b[3] != row[3]]
                if len(other_bibrefs) == 1:
                    if bconfig.TABLES_UTILS_DEBUG:
                        print "update_personID_table_from_paper: deleting " + str(row) + ' and  updating ' + str(other_bibrefs[0])
                    #we have one and only one sobstitute, we can switch them!
                    run_sql("delete from aidPERSONID where id = %s", (str(row[0]),))
                    run_sql("update aidPERSONID set flag=%s,lcul=%s where id=%s", (str(row[4]), str(row[5]), str(other_bibrefs[0][0])))
                else:
                    if bconfig.TABLES_UTILS_DEBUG:
                        print "update_personID_table_from_paper: deleting " + str(row)
                    run_sql("delete from aidPERSONID where id = %s", (str(row[0]),))
            else:
                if bconfig.TABLES_UTILS_DEBUG:
                    print "update_personID_table_from_paper: not touching " + str(row)
        persons_to_update = []
        for p in pid_rows:
            if p[1] not in persons_to_update:
                persons_to_update.append([p[1]])
        if bconfig.TABLES_UTILS_DEBUG:
                    print "update_personID_table_from_paper: updating canonical names of" + str(persons_to_update)
        update_personID_canonical_names(persons_to_update)


def personid_perform_cleanup():
    '''
    Performs a consistency cleanup on the data in personID tables.
    It is  usually not needed to have papers manually assigned to a personID
    to be even rejected from a different personID.
    This method thus takes care of eliminating such a redudancy in the table where
    it happens. It's not done during the update process for speed reasons.
    '''
    #consistency check:
    #papers which have been assigned by users should appear in only one place
    #This will no longer be needed if the update_from_algorithm will  be modified
    #to take that into account, now it is not for performance reasons
    run_sql("delete from aidPERSONID where tag='paper' and flag <='-1' and \
            data in (select data from aidPERSONID where tag='paper' and flag='2')")
    update_personID_canonical_names()


def confirm_papers_to_person(pid, papers, user_level=0):
    '''
    Confirms the relationship between pid and paper, as from user input.
    @param pid: id of the person
    @type pid: ('2',)
    @param papers: list of papers to confirm
    @type papers: (('100:7531,9024',),)
    '''
    #expects a pid ('2',)
    #and a lst of papers (('100:7531,9024',),)

    class names_gatherer(Thread):
        def __init__ (self, pid):
            Thread.__init__(self)
            self.pid = pid

        def run(self):
            update_personID_names_string_set(self.pid)
            close_connection()

    updated_pids = []
    for p in papers:
        old_owners = []

        try:
            old_owners = run_sql("select personid from aidPERSONID use index (`tdf-b`) where tag=%s and data=%s", ('paper', str(p[0]),))
        except (OperationalError, ProgrammingError):
            old_owners = run_sql("select personid from aidPERSONID where tag=%s and data=%s", ('paper', str(p[0]),))

        if len(old_owners) > 0:
            for owner in old_owners:
                updated_pids.append((str(owner[0]),))
        run_sql("delete from aidPERSONID where tag=%s and data=%s", ('paper', str(p[0]),))
        run_sql("insert into aidPERSONID (PersonID, tag, data, flag, lcul) values (%s,'paper',%s,'2', %s)",
                (str(pid[0]), str(p[0]), user_level))
    update_personID_names_string_set((pid,))
    #upd_thread = names_gatherer(tuple(updated_pids))
    #upd_thread.start()
    update_personID_names_string_set(tuple(updated_pids))
    update_personID_canonical_names([pid])



def reject_papers_from_person(pid, papers, user_level=0):
    '''
    Confirms the negative relationship between pid and paper, as from user input.
    @param pid: id of the person
    @type pid: ('2',)
    @param papers: list of papers to confirm
    @type papers: (('100:7531,9024',),)
    '''
    #expects a pid ('2',)
    #and a lst of papers (('100:7531,9024',),)
    #check if already assigned by user and skip those ones
    for p in papers:
        run_sql("update aidPERSONID set flag=%s,lcul=%s where PersonID=%s and data=%s",
                ('-2', user_level, str(pid[0]), str(p[0])))
    update_personID_names_string_set((pid,))
    update_personID_canonical_names([pid])

def reset_papers_flag(pid, papers):
    '''
    Resets the flag associated to the papers to '0'
    @param papers: list of papers to confirm
    @type papers: (('100:7531,9024',),)
    '''
    for p in papers:
        run_sql("update aidPERSONID set flag='0',lcul='0' where tag=%s and data=%s", ('paper', str(p[0])))
    update_personID_names_string_set((pid,))
    update_personID_canonical_names()


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


def get_person_papers(pid, flag, show_author_name=False, show_title=False):
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

    @return: [{'data': "", 'flag': "", 'author_name': "", 'title': ""}]
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
        docs = run_sql("SELECT data,flag FROM aidPERSONID use index (`ptf-b`) where personid = %s"
                        " and tag = %s and flag >= %s",
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
            listdict["data"] = doc[0]
            listdict["flag"] = doc[1]
            paperslist.append(listdict)
        except IndexError:
            #The paper has been modified and this bibref is no longer there
            #@TODO: this must call bibsched to update_personid_table_from_paper
            continue

    return paperslist


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
    return get_person_data(pid, 'paper_needs_bibref_manual_confirm')


def del_person_papers_needs_manual_review(pid, bibrec):
    '''
    Deletes from the set of papers awaiting for manual review for a person
    @param pid: personid, int
    @param bibrec: the bibrec, int
    '''
    del_person_data(pid, 'paper_needs_bibref_manual_confirm', bibrec)


def get_person_data(person_id, tag=None):
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

    if tag:
        rows = run_sql("SELECT tag, data FROM aidPERSONID "
                       "WHERE personid = %s AND tag = %s", (person_id, tag))
    else:
        rows = run_sql("SELECT tag, data FROM aidPERSONID "
                       "WHERE personid = %s", (person_id,))
    return rows


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


def del_person_data(person_id, tag, value=None):
    '''
    Change the value associated to the given tag for a certain person.
    @param person_id: ID of the person
    @type person_id: int
    @param tag: tag to be updated
    @type tag: string
    @param value: value to be written for the tag
    @type value: string
    '''
    if not value:
        run_sql("delete from aidPERSONID where personid=%s and tag=%s", (person_id, tag))
    else:
        run_sql("delete from aidPERSONID where personid=%s and tag=%s and data=%s", (person_id, tag, value))


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


def get_person_db_names_count_old(pid):
    '''
    Returns the set of name strings and count associated to a person id.
    The name strings are as found in the database.
    @param pid: ID of the person
    @type pid: ('2',)
    @param value: value to be written for the tag
    @type value: string
    '''
    norm_names_count = []

    try:
        norm_names_count = run_sql("select data,flag from aidPERSONID use index (`ptf-b`) "
                                   "where PersonID=%s and tag='gathered_name'",
                                   (str(pid[0]),))
    except (OperationalError, ProgrammingError):
        norm_names_count = run_sql("select data,flag from aidPERSONID where "
                                   "PersonID=%s and tag='gathered_name'",
                                   (str(pid[0]),))

    norm_names_count_dict = {}
    db_names_count_dict = {}
    db_names = get_person_names_set(pid)
    return_list = []

    for name, count in norm_names_count:
        norm_names_count_dict[name] = count

    names_to_join = []
    for name in norm_names_count_dict:
        names_to_join.append([[name], []])

    for db_name in db_names:
        try:
            ndb_name = create_normalized_name(split_name_parts(db_name[0]))
            db_names_count_dict[db_name[0]] = norm_names_count_dict[ndb_name]
            for i in names_to_join:
                if ndb_name in i[0]:
                    i[1].append(db_name[0])

        except (KeyError):
            db_names_count_dict[db_name[0]] = 1

    for nl in names_to_join:
        name_string = ''
        for n in nl[1]:
            name_string += '"' + str(n) + '" '
        if len(nl[1]) < 1:
            name_string = '"' + str(nl[0][0]) + '" '
        return_list.append((name_string, norm_names_count_dict[nl[0][0]]))
#    for name, count in db_names_count_dict.iteritems():
#        return_list.append((name, count))
#
    return_list = sorted(return_list, key=lambda k: k[0], reverse=False)
    return tuple(return_list)


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


def find_personIDs_by_name_string(namestring, strict=False):
    '''
    Search engine to find persons matching the given string
    @param: string name, 'surname, names I.'
    @type: string
    @return: pid list of lists [pid,[[name string, occur count, compatibility]]]

    The matching is done on the surname first, and names if present.
    An ordered list (per compatibility) of pids and found names is returned.
    '''
    canonical = []
    use_index = True

    try:
        canonical = run_sql("select personid,data from aidPERSONID use index (`tdf-b`) where data like %s and tag=%s", (namestring+'%','canonical_name'))
    except (ProgrammingError, OperationalError):
        canonical = run_sql("select personid,data from aidPERSONID where data like %s and tag=%s", (namestring+'%','canonical_name'))
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
                                            " as dummy where  o.tag='gathered_name' and o.personid = dummy.ipid",(surname,))
#        matching_pids_names_tuple = run_sql("select personid, data, flag from aidPERSONID use index (`ptf-b`) "
#                                            "where  tag=\'gathered_name\' and personid in "
#                                            "(select distinct personid from aidPERSONID use index (`tdf-b`) "
#                                            "where tag=\'gathered_name\' and data like %s)", (surname,))
    else:
        matching_pids_names_tuple = run_sql("select o.personid, o.data, o.flag from aidPERSONID o, "
                                            "(select distinct i.personid as ipid from aidPERSONID i where i.tag='gathered_name' and i.data like %s)"
                                            " as dummy where  o.tag='gathered_name' and o.personid = dummy.ipid",(surname,))
#    print matching_pids_names_tuple
    if len(matching_pids_names_tuple) == 0 and len(surname) >= 2:
        surname = surname[0:len(surname) - 2] + '%,%'

        if use_index:
            matching_pids_names_tuple = run_sql("select o.personid, o.data, o.flag from aidPERSONID o use index (`ptf-b`), "
                                            "(select distinct i.personid as ipid from aidPERSONID i use index (`tdf-b`) where i.tag='gathered_name' and i.data like %s)"
                                            " as dummy where  o.tag='gathered_name' and o.personid = dummy.ipid",(surname,))
        else:
            matching_pids_names_tuple = run_sql("select o.personid, o.data, o.flag from aidPERSONID o, "
                                            "(select distinct i.personid as ipid from aidPERSONID i where i.tag='gathered_name' and i.data like %s)"
                                            " as dummy where  o.tag='gathered_name' and o.personid = dummy.ipid",(surname,))

    if len(matching_pids_names_tuple) == 0 and len(surname) >= 2:
        surname = '%' + surname[0:len(surname) - 2] + '%,%'

        if use_index:
            matching_pids_names_tuple = run_sql("select o.personid, o.data, o.flag from aidPERSONID o use index (`ptf-b`), "
                                            "(select distinct i.personid as ipid from aidPERSONID i use index (`tdf-b`) where i.tag='gathered_name' and i.data like %s)"
                                            " as dummy where  o.tag='gathered_name' and o.personid = dummy.ipid",(surname,))
        else:
            matching_pids_names_tuple = run_sql("select o.personid, o.data, o.flag from aidPERSONID o, "
                                            "(select distinct i.personid as ipid from aidPERSONID i where i.tag='gathered_name' and i.data like %s)"
                                            " as dummy where  o.tag='gathered_name' and o.personid = dummy.ipid",(surname,))

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
            matching_pids.append([n[0],n[1], 1, 1])
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


def update_personID_names_string_set(PIDlist=[]):
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
    if len(PIDlist) == 0:
        PIDlist = run_sql('SELECT DISTINCT `personid` FROM `aidPERSONID`')

    class names_gatherer(Thread):
        def __init__ (self, pid):
            Thread.__init__(self)
            self.pid = pid
            self.pstr = ''

        def run(self):
            self.namesdict = dict()
            use_index = True

            try:
                self.person_papers = run_sql("select data from `aidPERSONID` use index (`ptf-b`) where tag=\'paper\' and "
                                              " flag >= \'-1\' and PersonID=%s",
                                                (str(self.pid[0]),))
            except (OperationalError, ProgrammingError):
                self.person_papers = run_sql("select data from `aidPERSONID` where tag=\'paper\' and "
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
                self.current_namesdict = dict(run_sql("select data,flag from aidPERSONID use index (`ptf-b`) where personID=%s "
                                        "and tag=\'gathered_name\'", (str(self.pid[0]),)))
            else:
                self.current_namesdict = dict(run_sql("select data,flag from aidPERSONID where personID=%s "
                                        "and tag=\'gathered_name\'", (str(self.pid[0]),)))

            self.needs_update = False
            if self.current_namesdict != self.namesdict:
                self.needs_update = True
            else:
                for i in self.namesdict.iteritems():
                    if i[1] != self.current_namesdict[i[0]]:
                        self.needs_update = True
                        if bconfig.TABLES_UTILS_DEBUG:
                            pass
#                            sys.stdout.write(str(self.pid) + str(i[1]) + ' differs  from ' + str(self.current_namesdict[i[0]]))
#                            sys.stdout.flush()

            if self.needs_update:
                if bconfig.TABLES_UTILS_DEBUG:
                    pass
#                    sys.stdout.write(str(self.pid) + ' updating!')
#                    sys.stdout.flush()
                run_sql("delete from `aidPERSONID` where PersonID=%s and tag=%s", (str(self.pid[0]), 'gathered_name'))
                for name in self.namesdict:
                    if bconfig.TABLES_UTILS_DEBUG:
                        #print 'insert into aidPERSONID (PersonID, tag, data, flag) values ('+ str(self.pid[0]) + ',\'gathered_name\',\"' + str(name)+ '\",\"' + str(self.namesdict[name]) + '\")'
                        pass
#                    self.pstr += '  ' + str(self.pid[0]) + '    ...processing: ' + str(name) + ' ' + str(self.namesdict[name])
#                    run_sql('insert into aidPERSONID (PersonID, tag, data, flag) values ('
#                            + str(self.pid[0]) + ',\'gathered_name\',\"' + str(name)
#                            + '\",\"' + str(self.namesdict[name]) + '\")')
                    run_sql('insert into aidPERSONID (PersonID, tag, data, flag) values (%s,%s,%s,%s)',
                            (str(self.pid[0]),'gathered_name',str(name),str(self.namesdict[name])))

            close_connection()
#                else:
#                    sys.stdout.write(str(self.pid) + ' not updating!')
#                    sys.stdout.flush()
#                sys.stdout.write(self.pstr + '\n')
#                sys.stdout.flush()

    tgath = []
    for pid in PIDlist:
        current = names_gatherer(pid)
        tgath.append(current)
        current.start()
        if bconfig.TABLES_UTILS_DEBUG:
            sys.stdout.write(str(pid) + '.\n')
            sys.stdout.flush()
        while threading.activeCount() > bconfig.PERSONID_SQL_MAX_THREADS:
            time.sleep(0.02)
    for t in tgath:
        t.join()


def update_personID_from_algorithm(RAlist=[]):
    '''
    Updates the personID table with the results of the algorithm, taking into account
    user inputs
    @param: list of realauthors to consider, if omitted performs an update on the entire db
    @type: tuple of tuples

    This is the core of the matching between the bibauthorid world and the personid world.
    For each RA of the list, tries to find the person it should be (in an ideal world there is
    100% matching in the list of papers, and the association is trivial).
    In the real world an RA might be wrongly carrying papers of more then one person (or a person
    might have papers of more then one RAs) so the matching must be done on a best-effort basis:
    -find the most compatible person
        -if it's compatible enough, merge the person papers with the ra papers (after
             a backtracking to find all the other RAs which the person might 'contain')
        -if nobody is compatible enough create a new person with RA papers

    Given the fuzzy nature of both the computation of RAs and the matching with persons, it has been
    decided to stick to the person all and only the papers which are carried by the RAs over a certain
    threshold.
    '''

    def get_bibreclist(currentRA):
        #[['700:157610,453095', '1.0']]
        VAlist = run_sql("SELECT `virtualauthorID`,`p` FROM `aidREALAUTHORS`  WHERE `realauthorID`=%s",
                        (str(currentRA[0]),))

        bibreclist = []

        class get_va_bibreclist(Thread):
            def __init__ (self, va):
                Thread.__init__(self)
                self.va = va
                self.bibreclist = []

            def run(self):
                bibrec = run_sql("select value from aidVIRTUALAUTHORSDATA where virtualauthorID=%s and tag=%s ", (str(self.va[0]), 'bibrefrecpair'))
                if len(bibrec) > 0:
                    self.bibreclist.append([str(bibrec[0][0]) , str(self.va[1])])
                    close_connection() # !!Important!!
                    return

                if bconfig.TABLES_UTILS_DEBUG:
                    pass
                    #print '   --debug: thread spawn for bibreclist of va: ' + str(self.va)
                bibrec = dict(run_sql("SELECT `tag`,`value` FROM `aidVIRTUALAUTHORSDATA` WHERE "
                            "virtualauthorID=%s and (tag=%s or tag=%s)",
                            (str(self.va[0]), 'bibrec_id', 'orig_authorname_id')))

                if (not bibrec.has_key("orig_authorname_id")) or (not bibrec.has_key("bibrec_id")):
                    if bconfig.TABLES_UTILS_DEBUG:
                        print ("WARNING: VA %s holds no data." % self.va[0])
                    return

                bibreflist = run_sql("SELECT `bibrefs` FROM `aidAUTHORNAMES` WHERE `id`=%s",
                                    (str(bibrec['orig_authorname_id']),))
                bibreflist = bibreflist[0][0].split(',')

                bibref100string = '('
                bibref700string = '('

                for br in bibreflist:
                    if br.split(':')[0] == '100':
                        bibref100string += '\'' + br.split(':')[1] + '\','
                    else:
                        bibref700string += '\'' + br.split(':')[1] + '\','

                if bibref100string[len(bibref100string) - 1] == ',':
                    bibref100string = bibref100string[0:len(bibref100string) - 1] + ')'
                else:
                    bibref100string = ''

                if bibref700string[len(bibref700string) - 1] == ',':
                    bibref700string = bibref700string[0:len(bibref700string) - 1] + ')'
                else:
                    bibref700string = ''

                if bibref100string:
                    bibrec100list = run_sql("SELECT `id_bibxxx` FROM `bibrec_bib10x` WHERE `id_bibrec`=%s"
                                            " and `id_bibxxx` in " + bibref100string,
                                            (str(bibrec['bibrec_id']),))
                else:
                    bibrec100list = []

                if bibref700string:
                    bibrec700list = run_sql("SELECT `id_bibxxx` FROM `bibrec_bib70x` WHERE `id_bibrec`=%s"
                                            " and `id_bibxxx` in" + bibref700string,
                                            (str(bibrec['bibrec_id']),))
                else:
                    bibrec700list = []

                for br in bibreflist:
                    if (long(br.split(':')[1]),) in bibrec100list:
                        if br not in self.bibreclist:
                            self.bibreclist.append([br + ',' + bibrec['bibrec_id'] , str(self.va[1])])
                        break
                    elif (long(br.split(':')[1]),) in bibrec700list:
                        if br not in self.bibreclist:
                            self.bibreclist.append([br + ',' + bibrec['bibrec_id'] , str(self.va[1])])
                        break

                close_connection()

        tbibreclist = []
        if bconfig.TABLES_UTILS_DEBUG:
            print 'update_personID_from_algorithm: get_bibreclist threads: '
        for va in VAlist:
            tempbibreclist = []
            bibrec = run_sql("select value from aidVIRTUALAUTHORSDATA where virtualauthorID=%s and tag=%s ", (str(va[0]), 'bibrefrecpair'))
            if len(bibrec) > 0:
                tempbibreclist.append([str(bibrec[0][0]) , str(va[1])])
                for b in tempbibreclist:
                    if b not in bibreclist:
                        bibreclist.append(b)
            else:
                current = get_va_bibreclist(va)
                tbibreclist.append(current)
                if bconfig.TABLES_UTILS_DEBUG:
                    sys.stdout.write('.')
                    sys.stdout.flush()
                current.start()

            while threading.activeCount() > bconfig.PERSONID_SQL_MAX_THREADS:
                time.sleep(0.02)

        for t in tbibreclist:
            t.join()
            for b in t.bibreclist:
                if b not in bibreclist:
                    bibreclist.append(b)

        if bconfig.TABLES_UTILS_DEBUG:
            print '\nupdate_personID_from_algorithm: get_bibreclist ---------------- Considering RA: ' + str(currentRA)
        return bibreclist

    def create_new_person(bibreclist):
        #creating new personid
        PID = max(run_sql('SELECT  MAX(PersonID) FROM `aidPERSONID`')[0][0], -1) + 1
        SQLquery = ''
        for br in bibreclist:
            flag = 0
            if br[1] >= bconfig.PERSONID_CNP_FLAG_1:
                flag = 1
            elif br[1] < bconfig.PERSONID_CNP_FLAG_MINUS1:
                flag = -1
            SQLquery += ('insert into `aidPERSONID` (PersonID, tag, data, flag) values ('
                + str(PID) + ', \'paper\',%s,\'' + str(flag) + '\');') % ('\'' + br[0] + '\'')
        if SQLquery:
            run_sql(SQLquery)
        update_personID_names_string_set(((str(PID),),))
        if bconfig.TABLES_UTILS_DEBUG:
            print 'update_personID_from_algorithm: create_new_person ---------------- ' + str(PID)

    def get_person_ra(person_papers):
        inverse_ra_list = []
        papers_vas = []

        class get_va_from_paper(Thread):
            def __init__ (self, paper):
                Thread.__init__(self)
                self.paper = paper
                self.vas = []
            def run(self):
                self.authnameid = run_sql("select Name_id from aidAUTHORNAMESBIBREFS where bibref=%s",
                        (str(self.paper[0].split(',')[0]),))
                if len(self.authnameid)>0:
                    self.va = run_sql(
                      "select a.virtualauthorID from aidVIRTUALAUTHORSDATA as a inner join "
                      "aidVIRTUALAUTHORSDATA as b on a.virtualauthorID=b.virtualauthorID "
                      "where ((a.tag=%s and a.value=%s) and (b.tag=%s and b.value=%s))",
                      ('bibrec_id', str(self.paper[0].split(',')[1]), 'orig_authorname_id', str(self.authnameid[0][0])))
    
                    #This is left here for benchmarking, it is still not clear which approach is the fastest
                    #self.va = run_sql('select virtualauthorID from `aidVIRTUALAUTHORSDATA` where ( virtualauthorID in ('
                    #         + ('select virtualauthorID from `aidVIRTUALAUTHORSDATA` where tag=\'bibrec_id\' and value=\'%s\'')
                    #             % (str(self.paper[0].split(',')[1]))
                    #         + ')) and ((tag, value) = (\'orig_authorname_id\', \''
                    #         + str(authnameid[0][0]) + '\'))')
                    for i in self.va:
                        self.vas.append(i[0])
                close_connection()

        tvapaper = []
        if bconfig.TABLES_UTILS_DEBUG:
            print 'update_personID_from_algorithm: get_va_from_paper threads: '
        for paper in person_papers:
            current = get_va_from_paper(paper)
            tvapaper.append(current)
            if bconfig.TABLES_UTILS_DEBUG:
                sys.stdout.write('.')
                sys.stdout.flush()
            current.start()
            while threading.activeCount() > bconfig.PERSONID_SQL_MAX_THREADS:
                time.sleep(0.02)

        for t in tvapaper:
            t.join()
            for b in t.vas:
                if b not in papers_vas:
                    papers_vas.append(b)

        papers_vas_string = '( '
        for i in papers_vas:
            papers_vas_string += '\'' + str(i) + '\','
        papers_vas_string = papers_vas_string[0:len(papers_vas_string) - 1] + ' )'
        if len(papers_vas) >= 1:
            r = run_sql("select distinct `realauthorID` "
                    " from `aidREALAUTHORS` where virtualauthorID in " + papers_vas_string)
            if len(r)>0:
                inverse_ra_list.append(r)
        else:
            inverse_ra_list = []
        if bconfig.TABLES_UTILS_DEBUG:
            print '\nupdate_personID_from_algorithm: get_person_ra ---------------- on ' + str(person_papers)
        return inverse_ra_list

    def merge_update_person_with_ra(pids, person_paper_list, currentRA, bibreclist):
        ras = get_person_ra(person_paper_list)
#        bibrecslists = []
        bibrecset = set()
        person_rejected_papers = run_sql("select data from `aidPERSONID` where "
                        ' tag=%s and  flag=%s and PersonID=%s',
                        ('paper', '-2', str(pids[0])))
        person_confirmed_papers = run_sql("select data from `aidPERSONID` where "
                        ' tag=%s and  flag=%s and PersonID=%s',
                        ('paper', '2', str(pids[0])))

        person_rejected_papers_set = set()
        for paper in person_rejected_papers:
            person_rejected_papers_set.add(paper[0])

        person_confirmed_papers_set = set()
        for paper in person_confirmed_papers:
            person_confirmed_papers_set.add(paper[0])

        for ra in ras:
            list = get_bibreclist(ra[0])
#            bibrecslists.append(list)
            for doc in list:
                if doc[1] >= bconfig.PERSONID_MIN_P_FROM_BCTKD_RA:
                    bibrecset.add(doc[0])

        for doc in bibreclist:
            if doc[1] >= bconfig.PERSONID_MIN_P_FROM_NEW_RA:
                bibrecset.add(doc[0])

        person_paper_set = set()
        for paper in person_paper_list:
            person_paper_set.add(paper[0])

        p_to_add = bibrecset.difference(person_paper_set)
        p_to_add = p_to_add.difference(person_rejected_papers_set)
        p_to_add = p_to_add.difference(person_confirmed_papers_set)

#       we might consider the case in which the algorithm is clustering two papers which are
#       manually assigned to different persons. That would mean adding a potentially really slow query
#       and once tthe algorithm will be able to take into consideration user input logs that should never happen
#       so this will be left to be done once we will see if it is really necessary to slow down everything
#       when the algorithm is clustering nicely this shouldn't happen anyway

        p_to_remove = person_paper_set.difference(bibrecset)
        p_to_remove = p_to_remove.difference(person_confirmed_papers_set)
        p_to_remove = p_to_remove.difference(person_rejected_papers_set)
        SQLquery = ''
        for br in p_to_add:
            SQLquery += ('insert into `aidPERSONID` (PersonID, tag, data, flag) values ('
                        + str(pids[0]) + ', \'paper\',%s,\'0\');') % ('\'' + br + '\'')
        if SQLquery:
            run_sql(SQLquery)
        SQLquery = ''
        for br in p_to_remove:
            SQLquery += ('delete from `aidPERSONID` where PersonID=\''
                         + str(pids[0]) + '\' and tag=\'paper\' and data=\''
                         + str(br) + '\';')
        if SQLquery:
            run_sql(SQLquery)
        update_personID_names_string_set((pids,))
        if bconfig.TABLES_UTILS_DEBUG:
            print 'update_personID_from_algorithm: Merging ----------------' + str(pids) + ' with realauthor ' + str(currentRA) + ' and found ras ' + str(ras)
#        print 'adding ' + str(p_to_add)
#        print 'removing ' + str(p_to_remove)

    if len(RAlist) == 0:
        RAlist = run_sql('SELECT DISTINCT `realauthorID` FROM `aidREALAUTHORS`')# LIMIT 1 , 15')


    for currentRA in RAlist:
        if bconfig.TABLES_UTILS_DEBUG:
            print '---|||||--- considering RA ' + str(currentRA)

        #bibreclist is the list of bibrefs associated with a RA
        bibreclist = get_bibreclist(currentRA)

        if not bibreclist:
            if bconfig.TABLES_UTILS_DEBUG:
                print "update_personID_from_algorithm: Skipping RA. Got no data from VA."
            continue

        bibrecsqlstring = '( '
        for i in bibreclist:
            bibrecsqlstring += '\'' + str(i[0]) + '\','
        bibrecsqlstring = bibrecsqlstring[0:(len(bibrecsqlstring) - 1)] + ' )'
        sqlstr = "SELECT DISTINCT PersonID FROM `aidPERSONID` WHERE tag=%s and `flag` >= %s and `data` in " + bibrecsqlstring
        if len(bibreclist) >= 1:
            pids = run_sql(sqlstr, ('paper', '0'))
        else:
            pids = []
        if bconfig.TABLES_UTILS_DEBUG:
            print 'update_personID_from_algorithm: Possible PIDS: ' + str(pids)

        if len(pids) < 1:
            create_new_person(bibreclist)

        else:
            #collect all the bibrefs
            #find all RA involved
            #decide which ones are really connected (>threshold)
            #merge them in the person found

            person_paper_list = []
            for pid in pids:
                person_papers = []

                try:
                    person_papers = run_sql("select data from `aidPERSONID` use index (`ptf-b`) where tag=%s and "
                                             "flag >= %s and PersonID=%s",
                                             ('paper', str(bconfig.PERSONID_UPFA_PPLMF), str(pid[0])))
                except (OperationalError, ProgrammingError):
                    person_papers = run_sql("select data from `aidPERSONID` where tag=%s and "
                                             "flag >= %s and PersonID=%s",
                                             ('paper', str(bconfig.PERSONID_UPFA_PPLMF), str(pid[0])))

                person_paper_list.append(person_papers)

            docn = len(bibreclist)
            bibrectdict = dict(bibreclist)
            compatibility_list = []
            compatible_papers_count = []
            for pid in person_paper_list:
                sum = 0.0
                p_c = 0.0
                for doc in pid:
                    try:
                        sum += float(bibrectdict[doc[0]])
                        p_c += 1
                    except:
                        pass
                        #print 'noindex exception!'
                compatibility_list.append(sum / docn)
                compatible_papers_count.append(p_c / docn)

            if bconfig.TABLES_UTILS_DEBUG:
                print 'update_personID_from_algorithm: Compatibility list: ' + str(compatibility_list)

            if max(compatibility_list) < bconfig.PERSONID_MAX_COMP_LIST_MIN_TRSH:
                if bconfig.TABLES_UTILS_DEBUG:
                    print 'update_personID_from_algorithm: Max compatibility list < than 0.5!!!'
                pidindex = compatible_papers_count.index(max(compatible_papers_count))
                if compatible_papers_count[pidindex] >= bconfig.PERSONID_MAX_COMP_LIST_MIN_TRSH_P_N:
                    merge_update_person_with_ra(pids[pidindex],
                        person_paper_list[pidindex], currentRA, bibreclist)
                else:
                    create_new_person(bibreclist)
            else:
                maxcount = compatibility_list.count(max(compatibility_list))
                if maxcount == 1:
                    #merge
                    pidindex = compatibility_list.index(max(compatibility_list))
                    merge_update_person_with_ra(pids[pidindex],
                        person_paper_list[pidindex], currentRA, bibreclist)
                elif maxcount > 1:
                    if bconfig.TABLES_UTILS_DEBUG:
                        print 'update_personID_from_algorithm: !!!!!!!!!!!!! Passing by, no maximum in compatibility list??'
                    #resolve merge
                else:
                    if bconfig.TABLES_UTILS_DEBUG:
                        print 'update_personID_from_algorithm: !!!!!!!!!!!!! Error: no one is compatible!!? not doing anything...'

    update_personID_canonical_names()


def export_personid_to_spiresid_validation(filename='/tmp/inspirepid', filename_oids='/tmp/inspirepidoids'):
    '''
    WARNING: still to be consolidated, but output is usable
    WARNING^2: S  L  O  W  .
    @fixme: export_personid_to_spiresid_validation: use get_record, might be much faster
    '''
    fp = open(filename, 'w')
    fp2 = open(filename_oids, 'w')
    fp.write('Personid->inspireid match:\n\n')
    fp2.write('Personid->inspireid match: INSPERE IDS only \n\n')
    pids = run_sql('SELECT personid FROM `aidPERSONID` WHERE 1 group by personid')
    for pid in pids:
        print 'considering:' + str(pid)
        fp.write('Considering pid' + str(pid) + '\n')
        fp2.write('Considering pid' + str(pid) + '\n')
        papers = run_sql('select data from aidPERSONID where tag=\'paper\' and '
                         'personid=\'' + str(pid[0]) + '\' ')
        parray = []
        for paper in papers:
            if paper[0].split(':')[0] == '700':
                print '  -' + str(paper)
                fields = run_sql('select id,value from bib70x where '
                                 '(tag=\'700__a\') and '
                                 'id=\'' + str(paper[0].split(',')[0].split(':')[1])
                                 + '\'')
                insid = run_sql('select id,value from bib70x where tag=\'700__i\' '
                         'and (id) in '
                         '(select a.id_bibxxx from bibrec_bib70x as a inner join '
                         'bibrec_bib70x as b using(id_bibrec)'
                         'where a.field_number = b.field_number and '
                         'b.id_bibxxx = \'' + str(paper[0].split(',')[0].split(':')[1])
                         + '\' and b.id_bibrec = \'' +
                         str(paper[0].split(',')[1]) + '\')')
                parray.append([fields, insid, paper])
        for p in parray:
            fp.write('  - ' + str(p[0]) + ' ' + str(p[1]) + ' from ' + str(p[2]) + '\n')
            if len(p[1]) >= 1:
                fp2.write('  - ' + str(p[0]) + ' ' + str(p[1]) + ' from ' + str(p[2]) + '\n')
    fp.close()
    fp2.close()


def export_spiresid_to_personid_validation(filename='/tmp/inspireid'):
    '''Build human readable validation for the SPIRES export

    User log case usages and contents reference.

    Table structure:
        id  trans_id    timestamp   userinfo    personID    action  tag     value   comment
        int int         time        char255     int         char50  char50  char200 text
    Operations on papers:
    * Assignment:
        - assign bibrec,bibref to personid
            id    trans_id    timestamp   userinfo          personID    action   tag     value          comment
            xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        assign   paper   x00:xxxx,xxxx  NULL
            xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        assign   paper   x00:xxxx,xxxx  'telephone request of the author bla bla bla'
            xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        assign   paper   x00:xxxx,xxxx  'first manual assignment, moved from pid: xxxx'

    * Rejection:
        - reject bibrec,bibref from personid
            id    trans_id    timestamp   userinfo          personID    action   tag     value          comment
            xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        reject   paper   x00:xxxx,xxxx  NULL
            xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        reject   paper   x00:xxxx,xxxx  'telephone request of the author bla bla bla'
            xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        reject   paper   x00:xxxx,xxxx  'manual inspection of the paper'

    * Reset:
        - Reset bibrec,bibref status (don't know who really is the author)
            id    trans_id    timestamp   userinfo          personID    action   tag     value          comment
            xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        reset    paper   x00:xxxx,xxxx  NULL
            xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        reset    paper   x00:xxxx,xxxx  'discovered error'
            xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        reset    paper   x00:xxxx,xxxx  'not enough information on the paper'

    Action,tag allowed couples:
        * assign,paper
        * reject,paper
        * reset,paper

    Operations on person ids:
    * Add:
        - assign info to personid
            id    trans_id    timestamp   userinfo          personID    action   tag              value            comment
            xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        data_add inspire_uid      uid_inspire_xxx  NULL
            xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        data_add email_addr       xxx@xxx.xxx      NULL
            xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        data_mod email_addr       zzz@xxx.xxx      NULL

    Action,tag allowed couples:
        * data_add,inspire_uid
        * data_add,email_addr
        * data_add,full_name
        * data_add,address
        * data_add,telephone_[home|office|...]
        ** data_mod, data_del: same as data_add

    NOTE: new action/tag can be addedd as needed
    NOTE: in case of need comment can be used instead of value (which is limited to 255 chars), but it is
            important to be consistent: if a field is using comment instead of value that _must_ be done _always_.

    Automated operations:
    * Table updates:
        - Update_authornames_table_from_paper
            id    trans_id    timestamp   userinfo          personID    action   tag       value          comment
            xxx   xxxxx       xxxx-xx-xx  daemon            -1          UATFP    bibsched  status         NULL

    Actions:
        * update_auntornames_table_from_paper: UATFP
        * authornames_tables_gc: ATGC
        * update_personid_table_from_paper: UPITFP
    '''
    fp = open(filename, 'w')
    bibrefs = run_sql('SELECT id,tag,value,count(value)  FROM `bib70x` WHERE '
                      '`tag` LIKE \'700__i\' group by value order by value')
    fp.write('Inspireid->personid match:\n\n')
    for i in bibrefs:
        print 'considering:' + str(i)
#        bibref = run_sql('select id,value from bib70x where tag=\'700__a\' '
#                         'and (id) in (select id_bibxxx from bibrec_bib70x where '
#                         '(id_bibrec,field_number) in '
#                         '(select id_bibrec,field_number from bibrec_bib70x '
#                         'where id_bibxxx = \''+str(i[0])+'\'))')
        bibref = run_sql('select id,value from bib70x where tag=\'700__a\' '
                         'and (id) in '
                         '(select a.id_bibxxx from bibrec_bib70x as a inner join '
                         'bibrec_bib70x as b using(id_bibrec)'
                         'where a.field_number = b.field_number and '
                         'b.id_bibxxx = \'' + str(i[0]) + '\')')

        print '  found ' + str(bibref)
        for bib in bibref:
            fp.write(' -\n')
            pids = run_sql('select personid from aidPERSONID where tag=\'paper\''
                           ' and data like \'700:%,' + str(bib[0]) + '\'')
            fp.write(str(i) + ':\n')
            for pid in pids:
                names = run_sql('select data,flag from aidPERSONID where'
                                ' tag=\'gathered_name\''
                                ' and personID=\'' + str(pid[0]) + '\'')
                fp.write('  -' + str(pid) + ': ' + str(names) + '\n ')
        fp.write('\n')
    fp.close()


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
    sql_query = 'select id,transactionid,timestamp,userinfo,personid,action,tag,value,comment from aidUSERINPUTLOG where 1 '
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


def insert_user_log(userinfo, personid, action, tag, value, comment='', transactionid=0, timestamp=''):
    '''
    Instert log entries in the user log table. For example of entres look at the table generation script.
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
        tsui = '\',\'' + str(timestamp) + '\',\'' + str(userinfo)
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
    run_sql('insert into aidUSERINPUTLOG (transactionid,timestamp,userinfo,personid,action,tag,value,comment) values '
            '(%s,%s,%s,%s,%s,%s,%s,%s)',
            (str(transactionid),str(tsui),str(userinfo),str(personid),str(action),str(tag),str(value),str(comment)))

    return transactionid


def export_personID_to_human_readable_file(filename='/tmp/hrexport.txt', Pids=[]):
    '''
    @deprecated: support for legacy software
    Export the personID of each document to a human readable file, for brief inspection purposes.
    @param file: filename to output to
    @type: string
    @param Pids: list of persons ids to limit the export
    @type: (('2',),)
    '''
    try:
        from invenio.search_engine import get_record
    except ImportError:
        print "not able to import get_record!"

    if len(Pids) == 0:
        Pids = run_sql('SELECT DISTINCT `PersonID` FROM `aidPERSONID`')# LIMIT 1,20')

    destfile = open(filename, 'w')

    for pid in Pids:
        if bconfig.TABLES_UTILS_DEBUG:
            print 'Exporting ' + str(pid) + '...'
        infos = run_sql('SELECT tag,data FROM `aidPERSONID` where PersonID=\''
                       + str(pid[0]) + '\' and not tag=\'paper\'')
        docs = run_sql('SELECT `data` FROM `aidPERSONID` where PersonID=\''
                      + str(pid[0]) + '\' and tag=\'paper\' and flag>=\'-1\'')
        destfile.write('Person ID: ' + str(pid[0]) + '\n')
        for info in infos:
            destfile.write('  info [' + str(info[0]) + ']: ' + str(info[1]) + '\n')
        for doc in docs:
            #title = run_sql('SELECT `value` FROM `bib24x` WHERE  `id` in \
            #        ((select id_bibxxx from bibrec_bib24x where id_bibrec=\'' + str(doc[0].split(',')[1]) + '\')) and tag=\'245__a\'')
            #id = run_sql('SELECT `id_bibxxx` FROM `bibrec_bib' + ('10' if str(doc[0].split(',')[0].split(':')[0]) == '100' else '70')
            #              + 'x` WHERE  and `id`=\'' + str(doc[0].split(',')[0].split(':')[1]) + '\'')

            title = "No title on paper..."

            try:
                title = get_record(int(doc[0].split(',')[1]))['245'][0][0][0][1]
            except (IndexError, KeyError, ValueError):
                title = "Problem encountered while retrieving document title"

            dsplit = doc[0].split(',')
            tnum = "70"

            if str(dsplit[0].split(':')[0]) == "100":
                tnum = "10"

            authorname = run_sql("SELECT value FROM bib%sx "
                                 "WHERE  id = %s" %
                                 (tnum, dsplit[0].split(':')[1]))
            destfile.write('  name: ' + str(authorname)
                + ' paper: [' + str(doc[0]) + ']: ' + str(title) + '\n')
        destfile.write('------------------------------------------------------------------------------\n')
    destfile.close()


def export_personID_to_spires(filename='/tmp/spiresexport.txt', Pids=[]):
    '''
    @deprecated: support for legacy software
    Export the personID of each document to SPIRES syntax.
    @param file: filename to output to
    @type: string
    @param Pids: list of persons ids to limit the export
    @type: (('2',),)
    '''
    if len(Pids) == 0:
        Pids = run_sql('SELECT DISTINCT `PersonID` FROM `aidPERSONID`')# LIMIT 0,20')

    destfile = open(filename, 'w')

    for pid in Pids:
        if bconfig.TABLES_UTILS_DEBUG:
            print 'Exporting ' + str(pid) + '...'
        docs = run_sql('SELECT `data` FROM `aidPERSONID` where PersonID=\''
                      + str(pid[0]) + '\' and tag=\'paper\' and flag>=\'-1\'')
        for doc in docs:
            f970a = docs = run_sql('SELECT `value` FROM `bib97x` where id=\''
                                + str(doc[0].split(',')[1])
                                + '\' and tag=\'970__a\'')

            dsplit = doc[0].split(',')
            tnum = "70"

            if str(dsplit[0].split(':')[0]) == "100":
                tnum = "10"

            author_number = run_sql("SELECT field_number FROM bibrec_bib%sx "
                                    "WHERE  id_bibrec = %s "
                                    "AND id_bibxxx = %s" %
                                    (tnum, dsplit[1], dsplit[0].split(':')[1]))

            author_offset = run_sql("SELECT min(field_number) FROM bibrec_bib%sx "
                                    "WHERE id_bibrec = %s" %
                                    (tnum, dsplit[1]))

#            print  f970a, author_number, doc
#            if len(author_number) >= 1:
#                destfile.write('merge = ' + str(f970a[0][0].split('-')[1]) + ';\nastr('
#                               + str(author_number[0][0]) + ');\nauthor-note(100)=INSPIRE-AUTO-'
#                               + str(pid[0]) + ';\n;\n')


            if str(doc[0].split(',')[0].split(':')[0]) == '100':
                author_exp = 1
            else:
                if len(author_number) >= 1:
                    author_exp = author_number[0][0] - author_offset[0][0] + 2
                else:
                    if bconfig.TABLES_UTILS_DEBUG:
                        print "No authornumber, setting -1!!!"
                    author_exp = -1


            if bconfig.TABLES_UTILS_DEBUG:
                print  f970a, author_number, author_offset, author_exp, doc


            destfile.write('merge = ' + str(f970a[0][0].split('-')[1]) + ';\nastr('
                           + str(author_exp) + ');\nauthor-note(100)=INSPIRE-AUTO-'
                           + str(pid[0]) + ';\n;\n')

    destfile.close()
    #        IRN = <value of 970a>;
    #        ASTR;
    #        A= <author name from record>;
    #        AFF = <affiliation from record 100/700u>;
    #        DESY-AUTHOR = INSPIRE-BIBAUTHOR-<ID from bibauthor>;


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
        pid_uid = run_sql("select data from aidPERSONID use index (`ptf-b`) where tag = %s and personid = %s", ('uid', str(pid)))
    except (OperationalError, ProgrammingError):
        pid_uid = run_sql("select data from aidPERSONID where tag = %s and personid = %s", ('uid', str(pid)))

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


def resolve_data_access_right(acc):
    '''
    Given a string or an integer, resolves to the corresponding integer or string
    If asked for a wrong/not present parameter falls back to the minimum privilege.
    '''
    access_dict = {bconfig.CLAIMPAPER_VIEW_PID_UNIVERSE: 0,
                   bconfig.CLAIMPAPER_CHANGE_OWN_DATA: 25,
                   bconfig.CLAIMPAPER_CHANGE_OTHERS_DATA: 50}

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
    elif - 2 < flag < 2:
        return False
    else:
        return True


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

    if flag == 2 or flag == -2:
        return [True, lcul]
    else:
        return [False, lcul]


def assign_person_to_uid(uid, pid):
    '''
    Assigns a person to a userid. If person already assigned to someone else, create new person.
    Returns the peron id assigned.
    @param uid: user id, int
    @param pid: person id, int, if -1 creates new person.
    @return: pid int
    '''
    def create_new_person(uid):
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

    if pid == -1:
        pid = create_new_person(uid)
        return pid
    else:
        current_uid = get_person_data(pid, 'uid')
        if len(current_uid) == 0:
            set_person_data(pid, 'uid', str(uid))
            return pid
        else:
            pid = create_new_person(uid)
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

    def create_new_person(uid):
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

    if force and pid >= 0:
        run_sql("delete from aidPERSONID where tag=%s and data=%s", ('uid', uid))
        set_person_data(pid, 'uid', str(uid))
        return pid
    elif force and pid < 0:
        return - 1

    current = get_personid_from_uid(((uid,),))

    if current[1]:
        return current[0][0]
    else:
        if pid >= 0:
            cuid = get_person_data(pid, 'uid')
            if len(cuid) > 0:
                if str(cuid[0][1]) == str(uid):
                    return pid
                else:
                    if create_new_pid:
                        create_new_person(uid)
                    else:
                        return - 1
            else:
                set_person_data(pid, 'uid', str(uid))
                return pid
        else:
            if create_new_pid:
                create_new_person(uid)
            else:
                return - 1


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
    pid = run_sql("select id,personid,tag,data,flag,lcul from aidPERSONID where tag=%s and data=%s", ('uid', str(uid[0][0])))
    if len(pid) == 1:
        return ([pid[0][1]], True)
    else:
        return  ([-1], False)


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

    bibrec_names_100 = run_sql("select id,value from bib10x where tag='100__a' and id in "
                               "(select id_bibxxx from bibrec_bib10x where id_bibrec=%s)",
                               (str(bibrec),))
    bibrec_names_700 = run_sql("select id,value from bib70x where tag='700__a' and id in "
                               "(select id_bibxxx from bibrec_bib70x where id_bibrec=%s)",
                               (str(bibrec),))
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
            pids = run_sql("select personid from aidPERSONID use index (`tdf-b`) where tag=%s and data=%s", ('paper', str(b[0])))
        except (OperationalError, ProgrammingError):
            pids = run_sql("select personid from aidPERSONID where tag=%s and data=%s", ('paper', str(b[0])))

        for pid in pids:
            if pid[0] in pid_bibrecref_dict:
                pid_bibrecref_dict[pid[0]].append(str(b[0]))
            else:
                pid_bibrecref_dict[pid[0]] = [str(b[0])]

    pid_list = [[i, pid_bibrecref_dict[i]] for i in pid_bibrecref_dict]

    return sorted(pid_list, key=lambda k: len(k[1]), reverse=True)


def get_processed_external_recids(pid):
    '''
    Returns processed external recids
    @param pid: pid
    @return: [str]
    '''
    db_data = get_person_data(pid, "processed_external_recids")
    recid_list_str = ''

    if db_data and db_data[0] and db_data[0][1]:
        recid_list_str = db_data[0][1]

    return recid_list_str


def set_processed_external_recids(pid, recid_list_str):
    '''
    Set processed external recids
    @param pid: pid
    @param recid_list_str: str
    '''
    del_person_data(pid, "processed_external_recids")
    set_person_data(pid, "processed_external_recids", recid_list_str)


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
                                                  get_table=['100','700'],
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


def get_personid_status_cacher():
    '''
    Returns a DataCacher object describing the status of the pid table content

    @return: DataCacher Object
    @rtype: DataCacher
    '''
    if not DATA_CACHERS:
        DATA_CACHERS.append(PersonIDStatusDataCacher())

    return DATA_CACHERS[0]
