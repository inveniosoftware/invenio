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
aidPersonID maintenance algorithms.
"""
import bibauthorid_config as bconfig
import re
try:
    import multiprocessing
except ImportError:
    pass
from threading import Thread, Lock
from Queue import Queue, Empty
from search_engine import perform_request_search
from bibtask import task_sleep_now_if_required
from bibtask import task_read_status

from bibauthorid_backinterface import get_all_names_from_personid
from bibauthorid_name_utils import split_name_parts
from dbquery import close_connection

#TODO: Remove imports from bibauthorid_dbinterface.
# It is better to write emit statements in bibauthorid_backinterface
# and import them from there.

from bibauthorid_dbinterface import get_person_rt_tickets
from bibauthorid_dbinterface import get_all_person_ids
from bibauthorid_dbinterface import get_person_claimed_papers
from bibauthorid_dbinterface import get_person_rejected_papers
from bibauthorid_dbinterface import delete_personid_by_id
from bibauthorid_dbinterface import del_person_not_manually_claimed_papers
from bibauthorid_dbinterface import pfap_assign_paper_iteration
from bibauthorid_dbinterface import _pfap_printmsg
from bibauthorid_dbinterface import personid_get_recids_affected_since

import bibauthorid_dbinterface as dbinter

class status_checker:
    '''
    This class can check the status of bibsched and synchronize the
    processes of given task. It contains a shared lock.
    '''
    def __init__(self):
        self.trigger = False
        self.locky = Lock()

    def should_stop(self):
        '''
        This method should be called in a worker process. If it returns true
        the process shoud stop or terminate. When all workers are stoped or
        terminated the master should call task_sleep_now_if_required().
        '''
        self.locky.acquire()
        try:
            if self.trigger == True:
                return True
            else:
                status = task_read_status()
                if (status == 'ABOUT TO SLEEP') or (status == 'ABOUT TO STOP'):
                    self.trigger = True # once triggered there is no going back
                    return True
            return False
        finally:
            self.locky.release()

def update_personID_table_from_paper(papers_list=None, personid=None):
    '''
    Updates the personID table removing the bibrec / bibrefs couples no longer existing (after a paper has been
    updated (name changed))
    @param papers_list: list of papers to consider for the update (bibrecs) (('1'),)
    @param type papers_list: tuple/list of tuples/lists of integers/strings which represent integers
    @param personid: limit to given personid (('1',),)
    @param type personid: tuple/list of tuples/lists of integers/strings which represent integers
    @return: None
    '''

    def extract_bibrec(paper):
        '''
        Extracts bibrec from a record like 100:312,53. In the given example the function will return 53.
        '''
        try:
            return paper.split(',')[1]
        except IndexError:
            return paper

    class Worker(Thread):
        def __init__(self, q, checker):
            Thread.__init__(self)
            self.q = q
            self.checker = checker

        def run(self):
            while True:
                # check bibsched
                if self.checker.should_stop():
                    break

                try:
                    self.paper = self.q.get_nowait()
                except Empty:
                    break

                try:
                    self.check_paper()
                except BaseException, err:
                    fp = open("/tmp/super.log", "a")
                    fp.write("%s\n" % str(err))
                    fp.close()

        def check_paper(self):
            if bconfig.TABLES_UTILS_DEBUG:
                print " -> processing paper = %s" % (self.paper[0],)

            bibrefs100 = dbinter.get_authors_from_paper(self.paper[0])
            bibrefs700 = dbinter.get_coauthors_from_paper(self.paper[0])
            bibrecreflist = frozenset(["100:%s,%s" % (str(i[0]), self.paper[0]) for i in bibrefs100] +
                                      ["700:%s,%s" % (str(i[0]), self.paper[0]) for i in bibrefs700])
            pid_rows_lazy = None

            #finally, if a bibrec/ref pair is in the authornames table but not in this list that name of that paper
            #is no longer existing and must be removed from the table. The new one will be addedd by the
            #update procedure in future; this entry will be risky becouse the garbage collector may
            #decide to kill the bibref in the bibX0x table
            for row in self.paper[1]:
                if row[3] not in bibrecreflist:
                    if not pid_rows_lazy:
                        pid_rows_lazy = dbinter.collect_personid_papers(paper=(self.paper[0],),
                                                                        person=personid_q)

                    other_bibrefs = [b[0] for b in pid_rows_lazy if b[1] == row[1] and b[3] != row[3]]
                    dbinter.delete_personid_by_id(int(row[0]))
                    if bconfig.TABLES_UTILS_DEBUG:
                        print "*   deleting record with missing bibref: \
                               id = %s, personid = %s, tag = %s, data = %s, flag = %s, lcul = %s" % row
                        print "found %d other records with the same personid and bibrec" % len(other_bibrefs)
                    if len(other_bibrefs) == 1:
                        #we have one and only one sobstitute, we can switch them!
                        dbinter.update_flags_in_personid(row[4], row[5], other_bibrefs[0])
                        if bconfig.TABLES_UTILS_DEBUG:
                            print "updating id=%d with flag=%d,lcul=%d" % (other_bibrefs[0], row[4], row[5])

            persons_to_update = set([(p[1],) for p in self.paper[1]])
            dbinter.update_personID_canonical_names(persons_to_update)
            dbinter.update_personID_names_string_set(persons_to_update, single_threaded=True, wait_finished=True)
            close_connection()

    if papers_list:
        papers_list = frozenset([int(x[0]) for x in papers_list])

    deleted_recs = dbinter.get_deleted_papers()
    deleted_recs = frozenset(x[0] for x in deleted_recs)
    if bconfig.TABLES_UTILS_DEBUG:
        print "%d total deleted papers" % (len(deleted_recs),)

    if personid:
        personid_q = dbinter.list_2_SQL_str(personid, lambda x: str(x[0]))
    else:
        personid_q = None

    counter = 0
    rows_limit = 10000000
    end_loop = False
    while not end_loop:
        task_sleep_now_if_required(can_stop_too=False)
        papers_data = dbinter.collect_personid_papers(person=personid_q,
                                                      limit=(counter, rows_limit,))

        if bconfig.TABLES_UTILS_DEBUG:
            print "query with limit %d %d" % (counter, rows_limit)

        if len(papers_data) == rows_limit:
            counter += rows_limit
        else:
            end_loop = True

        papers_data = tuple((extract_bibrec(p[3]), p) for p in papers_data)
        to_remove = set()
        jobs = dict()
        for p in papers_data:
            if int(p[0]) in deleted_recs:
                to_remove.add(p[1][0])
            elif not papers_list or int(p[0]) in papers_list:
                jobs[p[0]] = jobs.get(p[0], []) + [p[1]]
        del(papers_data)

        if len(to_remove) > 0:
            task_sleep_now_if_required(can_stop_too=False)
            delta = dbinter.delete_personid_by_id(to_remove)
            counter -= delta
            if bconfig.TABLES_UTILS_DEBUG:
                print "*   deleting %d papers, from %d, marked as deleted" % (delta, len(to_remove))

        jobslist = Queue()
        for p in jobs.items():
            jobslist.put(p)
        del(jobs)

        max_processes = bconfig.CFG_BIBAUTHORID_PERSONID_SQL_MAX_THREADS
        while not jobslist.empty():
            workers = []
            checker = status_checker()
            for i in range(max_processes):
                w = Worker(jobslist, checker)
                w.start()
                workers.append(w)

            for w in workers:
                w.join()

            task_sleep_now_if_required(can_stop_too=False)


def personid_remove_automatically_assigned_papers(pids=None):
    '''
    Part of the person repair facility.
    Removes every person entity that has no prior human interaction.
    Will run on all person entities if pids == None
    @param pids: List of tuples of person IDs
    @type pids: list of tuples
    '''
    if not pids:
        pids = get_all_person_ids()

    for pid in pids:
        tickets = get_person_rt_tickets(pid[0])
        pclaims = get_person_claimed_papers(pid[0])
        nclaims = get_person_rejected_papers(pid[0])

        if len(tickets) > 0 and len(pclaims) == 0 and len(nclaims) == 0:
            continue
        elif len(tickets) == 0 and len(pclaims) == 0 and len(nclaims) == 0:
            delete_personid_by_id(pid[0])
        elif len(pclaims) > 0:
            del_person_not_manually_claimed_papers(pid)
        elif len(nclaims) > 0:
            continue


def personid_fast_assign_papers(paperslist=None, use_threading_not_multiprocessing=True):
    '''
    Assign papers to the most compatible person.
    Compares only the name to find the right person to assign to. If nobody seems compatible,
    create a new person.
    '''

    class Worker(Thread):
        def __init__(self, i, p_q, atul, personid_new_id_lock, checker):
            Thread.__init__(self)
            self.i = i
            self.checker = checker
            self.p_q = p_q
            self.atul = atul
            self.personid_new_id_lock = personid_new_id_lock

        def run(self):
            while True:
                if checker.should_stop():
                    break
                try:
                    bibrec = self.p_q.get_nowait()
                except Empty:
                    break
                close_connection()

                pfap_assign_paper_iteration(self.i, bibrec, self.atul, self.personid_new_id_lock)

    def _pfap_assign_paper(i, p_q, atul, personid_new_id_lock, checker):
        while True:
            # check bibsched
            if checker.should_stop():
                break

            try:
                bibrec = p_q.get_nowait()
            except Empty:
                break

            pfap_assign_paper_iteration(i, bibrec, atul, personid_new_id_lock)


    _pfap_printmsg('starter', 'Started')
    if not paperslist:
        #paperslist = run_sql('select id from bibrec where 1')
        paperslist = [[x] for x in perform_request_search(p="")]

    paperslist = [k[0] for k in paperslist]

    _pfap_printmsg('starter', 'Starting on %s papers ' % len(paperslist))

    if use_threading_not_multiprocessing:
        authornames_table_update_lock = Lock()
        personid_new_id_lock = Lock()
        papers_q = Queue()
    else:
        authornames_table_update_lock = multiprocessing.Lock()
        personid_new_id_lock = multiprocessing.Lock()
        papers_q = multiprocessing.Queue()

    for p in paperslist:
        papers_q.put(p)

    process_list = []
    c = 0
    if not use_threading_not_multiprocessing:
        while not papers_q.empty():
            checker = status_checker()
            while len(process_list) <= bconfig.CFG_BIBAUTHORID_MAX_PROCESSES:
                p = multiprocessing.Process(target=_pfap_assign_paper, args=(c, papers_q,
                                                                    authornames_table_update_lock,
                                                                    personid_new_id_lock, checker))
                c += 1
                process_list.append(p)
                p.start()

            for i, p in enumerate(tuple(process_list)):
                if not p.is_alive():
                    p.join()
                    process_list.remove(p)

            task_sleep_now_if_required(can_stop_too=False)
    else:
        max_processes = bconfig.CFG_BIBAUTHORID_PERSONID_SQL_MAX_THREADS
        checker = status_checker()
        workers = []
        while not papers_q.empty():
            i = 0
            while len(workers) < max_processes:
                w = Worker(i, papers_q, authornames_table_update_lock,
                           personid_new_id_lock, checker)
                i += 1
                w.start()
                workers.append(w)
            for c, p in enumerate(tuple(workers)):
                if not p.is_alive():
                    p.join()
                    workers.remove(p)

            task_sleep_now_if_required(can_stop_too=False)

def get_recids_affected_since(last_timestamp):
    '''
    Returns a list of recids which have been manually changed since timestamp
    @TODO: extend the system to track and signal even automatic updates (unless a full reindex is
        acceptable in case of magic automatic update)
    @param: last_timestamp: last update, datetime.datetime
    '''
    return personid_get_recids_affected_since(last_timestamp)


def create_lastname_list_from_personid():
    '''
    This function generates a dictionary from a last name
    to list of personids which have this lastname.
    '''
    # ((personid, fulL Name1) ... )
    all_names = get_all_names_from_personid()

    # ((personid, last_name) ... )
    artifact_removal = re.compile("[^a-zA-Z0-9]")
    all_names = tuple((row[0], artifact_removal.sub("", split_name_parts(row[1].decode('utf-8'))[0]).lower())
                      for row in all_names)

    # { (last_name : [personid ... ]) ... }
    ret = {}
    for pair in all_names:
        ret[pair[1]] = ret.get(pair[1], []) + [pair[0]]

    return ret

def compare_bibrefrecs(left_bib, right_bib):
    '''
    This function compares two bibrefrecs (100:123,456) using all metadata
    and returns:
        * a pair with two numbers in [0, 1] - the probability that the two belong
            together and the ratio of the metadata functions used to the number of
            all metadata functions.
        * '+' - the metadata showed us that the two belong together for sure.
        * '-' - the metadata showed us that the two do not belong together for sure.

        Example:
            '(0.7, 0.4)' - 2 out of 5 functions managed to compare the bibrefrecs and
                using their computations the average value of 0.7 is returned.
            '-' - the two bibrefres are in the same paper, so they dont belong together
                for sure.
            '(1, 0)' There was insufficient metadata to compare the bibrefrecs. (The
                first values in ignored).
    '''
    return (1, 1)


def update_personID_from_algorithm(RAlist=None):
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
    pass
