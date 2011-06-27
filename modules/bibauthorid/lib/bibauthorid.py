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
bibauthorid
    This module provides functions needed to start the disambiguation
    algorithm and presents the central to control the parameters
    of the algorithm.
"""
import Queue
import glob

import time
import bibauthorid_structs as dat
import bibauthorid_config as bconfig
import gc
#import random
import re

from bibauthorid_realauthor_utils import process_updated_virtualauthors
from bibauthorid_realauthor_utils import find_and_process_orphans
from bibauthorid_virtualauthor_utils import add_minimum_virtualauthor

if not bconfig.STANDALONE:
    from bibauthorid_tables_utils import populate_doclist_for_author_surname
    from bibauthorid_tables_utils import find_all_last_names
    from bibauthorid_tables_utils import write_mem_cache_to_tables
    from bibauthorid_tables_utils import get_existing_last_names
    from bibauthorid_tables_utils import init_authornames

try:
    import multiprocessing
    MP_ENABLED = True
except ImportError:
    MP_ENABLED = False
    bconfig.LOGGER.warning("Bibauthorid is operating without multiprocessing "
                           "capabilities. You might want to consider "
                           "installing the python multiprocessing module")


def debugmsg(identity, msg):
    '''
    Prints a debug statement to std out. Especially needed in unbuffered
    python execution in multiprocessing and multi-threaded environments
    @param identity: The ID of the process
    @type identity: string or int
    @param msg: The message to print
    @type msg: string
    '''
    if bconfig.TABLES_UTILS_DEBUG:
        print (time.strftime('%H:%M:%S')
               + ' '
               + str(identity) + ': '
               + msg)


def start_full_disambiguation(last_names="all",
                         process_orphans=False,
                         db_exists=False,
                         populate_doclist=True,
                         write_to_db=True,
                         populate_aid_from_personid=False):
    '''
    Starts the disambiguation process on a specified set of authors or on all
    authors while respecting specified preconditions

    @param last_names: "all" to process all authors or a specific last name
    @type last_names: string
    @param process_orphans: process the orphans left after the first process?
    @type process_orphans: boolean
    @param db_exists: is there a data representation already in memory?
    @type db_exists: boolean
    @param populate_doclist: shall we populate the document list w/ the authors
    @type populate_doclist: boolean
    @param write_to_db: write the results back to the database?
    @type write_to_db: boolean
    @param populate_aid_from_personid: Populate all AID tables as a backtrack
        from aidPERSONID?
    @type populate_aid_from_personid: boolean

    @return: True if the process went through smoothly, False if it didn't
    @rtype: boolean
    '''

    if bconfig.STANDALONE:
        bconfig.LOGGER.critical("This method is not available in "
                                "standalone mode.")
        return False

    if isinstance(last_names, str) and last_names != "all":
        job_last_names = [last_names]

    elif last_names == "all":
        job_last_names = find_all_last_names()

    elif isinstance(last_names, list):
        job_last_names = last_names

    else:
        bconfig.LOGGER.error("Failed to detect parameter type. Exiting.")
        return False

    if populate_aid_from_personid:
        dat.RUNTIME_CONFIG['populate_aid_from_personid'] = True

    if db_exists:
        db_lnames = get_existing_last_names()

        for db_lname in db_lnames:
            if db_lname in job_last_names:
                job_last_names.remove(db_lname)

        bconfig.LOGGER.log(25, "Removed %s entries from the computation list, "
                           " since they've already been processed and written "
                           " to the db"
                      % (len(db_lnames)))

        del(db_lnames)

    totale = len(job_last_names)

    if MP_ENABLED:
        mp_queue = multiprocessing.Queue()
        mp_termination_queue = multiprocessing.Queue(1)
        db_write_lock = multiprocessing.Lock()

        process_list = []

        lc = multiprocessing.Process(target=list_creation_process,
                                     name='baid-listgen',
                                     args=(mp_queue, job_last_names,
                                           mp_termination_queue))
        lc.start()
        del(job_last_names)

        for i in range(bconfig.BIBAUTHORID_MAX_PROCESSES):
            p = multiprocessing.Process(target=computation_process_starter,
                                        name='baid-worker-' + str(i),
                                        args=(i, mp_termination_queue,
                                              mp_queue, db_write_lock,
                                              populate_doclist, True,
                                              process_orphans, True,
                                              write_to_db))
            process_list.append(p)
            p.start()
        for p in process_list:
            p.join()

        lc.join()
    else:
        mp_queue = Queue.Queue()
        mp_termination_queue = Queue.Queue()
        db_write_lock = None
        list_creation_process(mp_queue, job_last_names, mp_termination_queue)
        del(job_last_names)
        computation_process_starter(0, mp_termination_queue, mp_queue,
                                    db_write_lock, populate_doclist, True,
                                    process_orphans, True, write_to_db)

#    status = 1
    bconfig.LOGGER.log(25, "Done. Loaded %s last names." % (totale))


def list_creation_process(mp_queue, job_last_names, mp_termination_queue,
                          process_pool_n=bconfig.BIBAUTHORID_MAX_PROCESSES,
                          method=bconfig.BIBAUTHORID_LIST_CREATION_METHOD):
    '''
    Sub process to build the pre-clustered last name blocks

    @param mp_queue: queue holding the last name blocks
    @type mp_queue: queue
    @param job_last_names: list of all last names in the db
    @type job_last_names: list of string
    @param mp_termination_queue: queue holding the exit token for the processes
        to terminate upon finishing all queue elements
    @type mp_termination_queue: queue
    @param method: 'mysql' or 'regexp'
    '''

    if method == 'regexp':
        debugmsg(0, "List_creator: starting names list computation in REGEXP mode")
        all_lnames = job_last_names
        rm_nonalphanumerics = re.compile("[^a-zA-Z0-9]")
        name_vars = {}

        for name in all_lnames:
            rname = rm_nonalphanumerics.sub("", name).lower()

            if rname in name_vars:
                name_vars[rname].append(name)
            else:
                name_vars[rname] = [name]
        debugmsg(0, "List_creator: appending names list:")
        for k in name_vars:
            if name_vars[k]:
                mp_queue.put(name_vars[k])
        debugmsg(0, "List_creator: All names appended!")
        debugmsg(0, "List_creator: putting exit token")
        mp_termination_queue.put(True)
        return

    if method == 'mysql':
        mp_variation_set = multiprocessing.Queue()

        list_pusher = multiprocessing.Process(target=nameset_list_pusher,
                                              args=(mp_queue, mp_variation_set,
                                                    mp_termination_queue))
        list_pusher.start()

        process_list = []
        c = 0
        for lname in job_last_names:
            c = c + 1
            if c > process_pool_n :
                loop = True
                ic = 0
                while loop:
                    for i, j in enumerate(process_list):
                        if not j.is_alive():
                            loop = False
                            debugmsg(i, "List_creator: joining %s to create %s"
                                     % (str(i), str(c)))
                            process_list[i].join()
                            process_list[i] = multiprocessing.Process(target=nameset_comp, args=(c, lname, mp_variation_set))
                            process_list[i].start()
                            ic = 0
                            break
                    ic += 1
                    if ic > 1:
                        debugmsg(0, "List_creator: busy waiting cycle...."
                                    "zzZ zzZ zzZ zzZ zzZ zzZ zzZ zzZ")
                        time.sleep(0.5)
                        ic = 0
            else:
                p = multiprocessing.Process(target=nameset_comp, args=(c, lname, mp_variation_set))
                process_list.append(p)
                p.start()
        for p in process_list:
            p.join()

        debugmsg(0, "List_creator: putting exit token")

        mp_termination_queue.put(True)
        list_pusher.join()
        return


def nameset_comp(c, lname, mp_variation_set):
    try:
        debugmsg(c, "List_creator: %s" % str(c)
                 + "  working on " + str(lname.encode('UTF-8')))
    except:
        debugmsg(c, "List_creator: %s" % str(c) + "  working on "
                 + str('Error encoding name'))

#    old_variations_set = mp_variaton_set.get()
#    mp_variaton_set.put(old_variations_set)
#    if lname in old_variations_set:
#        if bconfig.TABLES_UTILS_DEBUG:
#            print time.strftime('%H:%M:%S') + ' ' + "List_creator: %s" % str(c) + "  computation DROPPED."
#        return

    dat.reset_mem_cache(True)
    init_authornames(lname)
    nameset = set([x['name'].split(",")[0] for x in dat.AUTHOR_NAMES])


    debugmsg(c, "List_creator: %s" % str(c) + "  computation finished, pushing varset")

    mp_variation_set.put([lname, list(nameset)])

    debugmsg(c, "List_creator: %s" % str(c) + " current variations pushed")


def nameset_list_pusher(mp_queue, mp_variations_set, mp_termination_queue):
#    jl = []
    varset = []
    while mp_termination_queue.empty():
        if not mp_variations_set.empty():
            debugmsg(0, "List_creator: list pusher: getting from varset queue")
            partset = mp_variations_set.get()

            if partset[0] not in varset:
                varset = varset + partset[1]
                nameset = partset[1]
#                debugmsg(0, "List_creator: list pusher:  computation finished, getting queue")
#
#                jl[:] = mp_queue.get()
#
#                debugmsg(0, "List_creator: list pusher:  computation finished, got queue")
#
#                debugmsg(0, "List_creator: list pusher:   appending " + str(nameset) + ' with still ' + str(len(jl)) + ' elements in queue')
#
#                jl.append(nameset)
                debugmsg(0, "List_creator: list pusher:   appending "
                         + str(nameset) + ' with still '
                         + str(mp_queue.qsize()) + ' elements in queue')
                mp_queue.put(nameset)

                debugmsg(0, "List_creator: list pusher:   queue append finished")
            else:
                debugmsg(0, "List_creator: list pusher:   DROPPED name %s" % partset[0])
        else:
            time.sleep(0.5)

    debugmsg(0, "List_creator: list pusher: empty variations and exit token, quitting...")

    return


def computation_process_starter(i, mp_termination_queue, job_mp_queue,
                                db_write_lock,
                                populate_doclist=True,
                                process_doclist=True,
                                process_orphans=False,
                                print_stats=True,
                                write_to_db=False):
    '''
    Sub process that starts the disambiguation process on a specified
    set of authors.

    @param i: ID of the process (int between 0 and MAX_PROCESSES in bconfig)
    @type i: int
    @param mp_termination_queue: queue holding the exit token for the processes
        to terminate upon finishing all queue elements
    @type mp_termination_queue: queue
    @param job_mp_queue: queue holding the last name blocks
    @type job_mp_queue: queue
    @param db_write_lock: shilds the database from too many concurrent accesses
    @type db_write_lock: multiprocessing.Lock
    @param last_names: "all" to process all authors or a specific last name
    @type last_names: string
    @param process_orphans: process the orphans left after the first process?
    @type process_orphans: boolean
    @param db_exists: is there a data representation already in memory?
    @type db_exists: boolean
    @param populate_doclist: shall we populate the document list w/ the authors
    @type populate_doclist: boolean
    @param write_to_db: write the results back to the database?
    @type write_to_db: boolean
    '''
    while True:
        debugmsg(i, "getting name from queue")
        if job_mp_queue.qsize() > 0:
            job_last_names = job_mp_queue.get()
            debugmsg(i, "got queue item! %s items left in queue"
                        % job_mp_queue.qsize())

        else:
            debugmsg(i, "Queue is currently empty...")
            if not mp_termination_queue.empty():
                debugmsg(i, "Exit token there, Process %s salutes to quit!" % i)
                return
            else:
                debugmsg(i, "Exit token not present, continuing in 15s!")
                time.sleep(15)
                continue

        last_name_queue = Queue.Queue()

        last_name_queue.put(sorted(job_last_names))

        gc.collect()

        while True:

            dat.reset_mem_cache(True)
            gc.collect()

            if last_name_queue.empty():
                bconfig.LOGGER.log(25, "Done with all names.")
                break
            debugmsg(i, "starting with queue: " + str(last_name_queue.queue))

            lname_list = last_name_queue.get()
            lname = None

            if lname_list:
                lname = lname_list[0]
                del(lname_list[0])
            else:
                bconfig.LOGGER.warning("Got an empty Queue element. "
                                       "Queue seems corrupted.")
                continue
    #        bconfig.LOGGER.log(25, "Processing: %s (%d/%d)."
    #                                % (lname, status, total))

            if populate_doclist:
                populate_doclist_for_author_surname(lname, job_last_names)

            start_computation(process_orphans=process_orphans,
                              process_doclist=process_doclist,
                              print_stats=print_stats)
            post_remove_names = set()

            # The following snippet finds additionally processed last names and
            # removes them from the processing queue. E.g. 't hooft and t'hooft
            for name in [row['name'] for row in dat.AUTHOR_NAMES
                         if not row['processed']]:
                potential_removal = "%s" % (name.split(',')[0])

                if not potential_removal == "%s" % (lname):
                    post_remove_names.add(potential_removal)

            if len(post_remove_names) > 0:
                removed = 0
                removed_names = []

                for post_remove_name in post_remove_names:
                    if post_remove_name in lname_list:
                        lname_list.remove(post_remove_name)
                        removed_names.append(post_remove_name)
                        removed += 1

                bconfig.LOGGER.log(25, "-> Removed %s entries from the "
                                        "computation list: %s"
                                        % (removed, removed_names))

            if lname_list:
                last_name_queue.put(lname_list)

            if write_to_db:
                if MP_ENABLED:
                    db_write_lock.acquire()

                if dat.ID_TRACKER:
                    try:
                        write_mem_cache_to_tables()
                    except Exception, emsg:
                        bconfig.LOGGER.error("An error occurred while writing "
                                             "to the db: %s" % emsg)
                else:
                    bconfig.LOGGER.info("The ID tracker appears to be empty. "
                                         "Nothing will be written to the "
                                         "database from this job. That's ok, "
                                         "when excluding collections. Last "
                                         "processed last name: %s" % lname)

                if MP_ENABLED:
                    db_write_lock.release()

                dat.reset_mem_cache(True)
                gc.collect()


def start_computation(process_doclist=True,
                      process_orphans=False,
                      print_stats=True):
    '''
    Starts the actual computation, so start comparing virtual authors to
    real authors to match them.

    @param process_doclist: shall virtual authors be created from the doc list?
    @type process_doclist: boolean
    @param process_orphans: shall orphans from the first run be processed?
    @type process_orphans: boolean
    @param print_stats: shall statistics be printed to the looger?
    @type print_stats: boolean
    '''

    module_paths = glob.glob(bconfig.MODULE_PATH)

    if not module_paths:
        bconfig.LOGGER.exception("Sorry, no modules found for comparison.")
        raise Exception('ModuleError')

    if process_doclist:
        create_vas_from_doclist()


    bconfig.LOGGER.log(25, "Done. All Clusters identified.")
    bconfig.LOGGER.log(25, "Starting match algorithm...")


    process_updated_virtualauthors()

    if process_orphans:
        find_and_process_orphans(1)

    if print_stats:
        _print_run_stats()


def create_vas_from_doclist():
    '''
    Processes the document list and creates a new minimal virtual author
    for each author in each record.
    '''
    bconfig.LOGGER.log(25, "Creating minimal virtual authors for "
                            "all loaded docs")

    for docs in [row for row in dat.DOC_LIST]:
        for author_id in docs['authornameids']:
            author_name = [an['name'] for an in dat.AUTHOR_NAMES
                           if an['id'] == author_id]
            refrecs = [ref[1] for ref in docs['authornameid_bibrefrec']
                       if ref[0] == author_id]
            refrec = -1

            if len(refrecs) > 1:
                print "Several bibrefs on one paper?! How?"
                refrec = refrecs[0]
            elif refrecs:
                refrec = refrecs[0]

            add_minimum_virtualauthor(author_id, author_name[0],
                                          docs['bibrecid'], 0, [], refrec)


def _print_run_stats():
    '''
    Show some statistics about the run and echo it to the logging system
    '''

    docs = len(set([row['virtualauthorid'] for row in dat.VIRTUALAUTHORS]))
    ras = len(set([row['realauthorid'] for row in dat.REALAUTHORS]))
    orphans = len(set([row['virtualauthorid'] for row in dat.VIRTUALAUTHOR_DATA
                       if (row['tag'] == "connected")
                       and (row['value'] == "False")]))

    if docs > 0:
        ratio = ((float(docs) - float(orphans)) * 100.0) / float(docs)

        bconfig.LOGGER.log(25, "On %s documents, %s real authors could be "
                           "identified. %s unattributed documents remain "
                           "=> ~%.2f%% identified"
                           % (docs, ras, orphans, ratio))
    else:
        bconfig.LOGGER.log(25, "No documents have been processed for this "
                           "last name cluster.")
