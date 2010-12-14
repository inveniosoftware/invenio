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

"""
bibauthorid
    This module provides functions needed to start the disambiguation
    algorithm and presents the central to control the parameters 
    of the algorithm.
"""
import Queue
import glob

import bibauthorid_structs as dat
import bibauthorid_config as bconfig

from bibauthorid_realauthor_utils import process_updated_virtualauthors
from bibauthorid_realauthor_utils import find_and_process_orphans
from bibauthorid_virtualauthor_utils import add_minimum_virtualauthor

if not bconfig.STANDALONE:
    from bibauthorid_tables_utils import populate_doclist_for_author_surname
    from bibauthorid_tables_utils import find_all_last_names
    from bibauthorid_tables_utils import write_mem_cache_to_tables
    from bibauthorid_tables_utils import get_existing_last_names


def start_full_disambiguation(last_names="all",
                         process_orphans=False,
                         db_exists=False,
                         populate_doclist=True,
                         write_to_db=True):
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

    if db_exists:
        db_lnames = get_existing_last_names()

        for db_lname in db_lnames:
            if db_lname in job_last_names:
                job_last_names.remove(db_lname)

        bconfig.LOGGER.log(25, "Removed %s entries from the computation list, "
                           " since they've already been processed and written "
                           " to the db"
                      % (len(db_lnames)))

    last_name_queue = Queue.Queue()

    for last_name in sorted(job_last_names):
        last_name_queue.put(last_name)

    total = len(job_last_names)
    status = 1
    bconfig.LOGGER.log(25, "Done. Loaded %s last names." % (total))

    while True:
        dat.reset_mem_cache(True)

        if last_name_queue.empty():
            bconfig.LOGGER.log(25, "Done with all names.")
            break

        lname = last_name_queue.get()
        bconfig.LOGGER.log(25, "Processing: %s (%d/%d)."
                                % (lname, status, total))

        if populate_doclist:
            populate_doclist_for_author_surname(lname)

        start_computation(process_orphans=process_orphans)
        post_remove_names = set()

        # The following snippet finds additionally processed last names
        # and removes them from the processing queue. E.g. 't hooft and t'hooft
        for name in [row['name'] for row in dat.AUTHOR_NAMES
                     if not row['processed']]:
            potential_removal = "%s," % (name.split(',')[0],)

            if not potential_removal == "%s" % (lname,):
                post_remove_names.add(potential_removal)

        if len(post_remove_names) > 1:
            removed = 0
            removed_names = []

            for post_remove_name in post_remove_names:
                if post_remove_name in last_name_queue.queue:
                    last_name_queue.queue.remove(post_remove_name)
                    removed_names.append(post_remove_name)
                    removed += 1

            bconfig.LOGGER.log(25, "-> Removed %s entries from the "
                                    "computation list: %s"
                                    % (removed, removed_names))
            total -= removed

        if write_to_db:
            if dat.ID_TRACKER:
                write_mem_cache_to_tables()
            else:
                bconfig.LOGGER.error("The ID tracker appears to be empty. "
                                     "Nothing will be written to the "
                                     "database from this job. Last "
                                     "processed last name: %s" % lname)


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

            add_minimum_virtualauthor(author_id, author_name[0],
                                          docs['bibrecid'], 0, [])


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
        bconfig.LOGGER.error("No documents have been processed.")
