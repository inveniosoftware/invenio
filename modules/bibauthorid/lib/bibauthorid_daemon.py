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
Bibauthorid Daemon
    This module IS NOT standalone safe - it should never be run this way.
"""

import sys
import os
import Queue
import os.path as osp
import bibauthorid_config as bconfig
import bibauthorid_structs as dat

from bibauthorid_tables_utils import populate_doclist_for_author_surname
from bibauthorid_tables_utils import find_all_last_names
from bibauthorid_tables_utils import write_mem_cache_to_tables
from bibauthorid_tables_utils import populate_authornames
from bibauthorid_tables_utils import populate_authornames_bibrefs_from_authornames
from bibauthorid_tables_utils import get_len_authornames_bibrefs
from bibauthorid_tables_utils import check_and_create_aid_tables
from bibauthorid_tables_utils import load_mem_cache_from_tables
from bibauthorid_tables_utils import load_records_to_mem_cache
from bibauthorid_tables_utils import init_authornames
from bibauthorid_tables_utils import get_papers_recently_modified
from bibauthorid_tables_utils import update_authornames_tables_from_paper
from bibauthorid_tables_utils import authornames_tables_gc
from bibauthorid_tables_utils import update_tables_from_mem_cache
from bibauthorid_tables_utils import empty_aid_tables
from bibauthorid_virtualauthor_utils import add_minimum_virtualauthor
from bibauthorid_virtualauthor_utils import get_va_ids_by_recid_lname
from bibauthorid_virtualauthor_utils import delete_virtual_author
from bibauthorid_virtualauthor_utils import get_virtualauthor_records
from bibauthorid_realauthor_utils import get_realauthors_by_virtuala_id
from bibauthorid_realauthor_utils import remove_va_from_ra
from bibauthorid_realauthor_utils import del_ra_data_by_vaid
from bibauthorid_file_utils import write_mem_cache_to_files
from bibauthorid_file_utils import populate_structs_from_files
from bibauthorid_file_utils import tail
from bibauthorid import start_full_disambiguation
from bibauthorid import start_computation
from bibauthorid_utils import get_field_values_on_condition
from bibauthorid_utils import split_name_parts
from bibauthorid_authorname_utils import update_doclist
from bibauthorid_personid_tables_utils import get_user_log
from bibauthorid_personid_tables_utils import insert_user_log
from bibauthorid_personid_tables_utils import update_personID_table_from_paper
from bibauthorid_personid_tables_utils import update_personID_from_algorithm
from bibauthorid_personid_tables_utils import personid_remove_automatically_assigned_papers

import bibtask


# Global variables allowing to retain the progress of the task.
_INDEX = 0
_RECIDS_NUMBER = 0


def bibauthorid_daemon():
    """Constructs the Bibauthorid bibtask."""
    bibtask.task_init(authorization_action='runbibclassify',
        authorization_msg="Bibauthorid Task Submission",
        description="""
Purpose:
  Disambiguate Authors and find their identities.
Examples:
  - Process all records that hold an author with last name 'Ellis':
      $ bibauthorid -u admin --lastname 'Ellis'
  - Process all records and regard all authors:
      $ bibauthorid -u admin --process-all
  - Prepare job packages in folder 'gridfiles' with the sub directories
    prefixed with 'task' and a maximum number of 2000 records per package:
      $ bibauthorid -u admin --prepare-grid -d gridfiles -p task -m 2000
""",
        help_specific_usage="""
  NOTE: Options -n, -a, -U, -G and -R are mutually exclusive (XOR)!
  -n, --lastname=STRING     Process only authors with this last name.
  -a, --process-all         The option for cleaning all authors.
  -U, --update-universe     Update bibauthorid universe. Find modified and
                            newly entered records and process all the authors
                            on these records.
  -G, --prepare-grid        Prepares a set of files that supply the
                            pre-clustered data needed for stand alone job to
                            run (e.g. needed on the grid). The behavior of
                            this export can be controlled with the
                            options -d (required), -p and -m (both optional).
  -R, --load-grid-results   Loads the results from the grid jobs
                            and writes them to the database. The behavior of
                            this import can be controlled with the
                            options -d (required).
  -d, --data-dir=DIRNAME    Specifies the data directory, in which the data for
                            the grid preparation will be stored to or loaded
                            from. It requires the -G or -R switch.
  -p, --prefix=STRING       Specifies the prefix of the directories created
                            under the --data-dir directory. Optional.
                            Defaults to 'job'. It requires the -G switch.
  -m, --max-records         Specifies the number of records that
                            shall be stored per job package. Optional.
                            Defaults to 4000 and requires -G switch.
      --update-cache        Updates caches to the newly introduced changes
                            (new and modified documents).
                            This should be called daily or better more then
                            once per day, to ensure the correct operation of
                            the frontend (and the backend).
      --clean-cache         Clean the cache from out of date contents
                            (deleted documents).
  -r, --record-ids          Specifies a list of record ids. To use as on option
                            for --update-universe to limit the update to the
                            selected records
  --all-records             To use as on option for --update-universe to
                            perform the update an all existing record ids. Be
                            WARNED that this will empty and re-fill all aid*
                            tables in the process!
  --repair-personid         Deletes untouched person entities to then
                            re-create and updated these entities.
""",
        version="Invenio Bibauthorid v%s" % bconfig.VERSION,
        specific_params=("r:d:n:p:m:GURa",
            [
             "data-dir=",
             "lastname=",
             "prefix=",
             "max-records=",
             "process-all",
             "prepare-grid",
             "load-grid-results",
             "update-universe",
             "update-cache",
             "clean-cache",
             "record-ids=",
             "all-records",
             "repair-personid"
            ]),
        task_submit_elaborate_specific_parameter_fnc=
            _task_submit_elaborate_specific_parameter,
        task_submit_check_options_fnc=_task_submit_check_options,
        task_run_fnc=_task_run_core)


def _task_submit_elaborate_specific_parameter(key, value, opts, args):
    """
    Given the string key it checks it's meaning, eventually using the
    value. Usually, it fills some key in the options dict.
    It must return True if it has elaborated the key, False, if it doesn't
    know that key.
    """
    if key in ("-n", "--lastname"):
        if value == "None," or value == "None":
            bibtask.write_message("The value specified for --lastname must "
                "be a valid name. Not '%s'." % value, stream=sys.stdout,
                verbose=0)
            return False

        bibtask.task_set_option('lastname', value)

    elif key in ("-a", "--process-all"):
        bibtask.task_set_option("process_all", True)

    elif key in ("-U", "--update-universe"):
        bibtask.task_set_option("update", True)

    elif key in ("-G", "--prepare-grid"):
        bibtask.task_set_option("prepare_grid", True)

    elif key in ("-R", "--load-grid-results"):
        bibtask.task_set_option("load_grid_results", True)

    elif key in ("-d", "--data-dir"):
        bibtask.task_set_option("data_dir", value)

    elif key in ("-p", "--prefix"):
        bibtask.task_set_option("prefix", value)

    elif key in ("-m", "--max-records"):
        bibtask.task_set_option("max_records", value)

    elif key in ("--update-cache",):
        bibtask.task_set_option("update_cache", True)

    elif key in ("--clean-cache",):
        bibtask.task_set_option("clean_cache", True)

    elif key in ("--record-ids", '-r'):
        if value.count("="):
            value = value[1:]

        value = value.split(",")
        bibtask.task_set_option("record_ids", value)

    elif key in ("--all-records"):
        bibtask.task_set_option("all_records", True)

    elif key in ("--repair-personid"):
        bibtask.task_set_option("repair_pid", True)

    else:
        return False

    return True


def _task_run_core():
    """
    Runs the requested task in the bibsched environment.
    """

    lastname = bibtask.task_get_option('lastname')
    process_all = bibtask.task_get_option('process_all')
    prepare_grid = bibtask.task_get_option('prepare_grid')
    load_grid = bibtask.task_get_option('load_grid_results')
    data_dir = bibtask.task_get_option('data_dir')
    prefix = bibtask.task_get_option('prefix')
    max_records_option = bibtask.task_get_option('max_records')
    update = bibtask.task_get_option('update')
    clean_cache = bibtask.task_get_option('clean_cache')
    update_cache = bibtask.task_get_option('update_cache')
    record_ids = bibtask.task_get_option('record_ids')
    record_ids_nested = None
    all_records = bibtask.task_get_option('all_records')
    repair_pid = bibtask.task_get_option('repair_pid')

    if record_ids:
        record_ids_nested = [[p] for p in record_ids]
#    automated_daemon_mode_p = True

    if lastname:
        bibtask.write_message("Processing last name %s" % (lastname),
                              stream=sys.stdout, verbose=0)

    if process_all:
        if bconfig.STANDALONE:
            bibtask.write_message("Processing not possible in standalone!",
                                  stream=sys.stdout, verbose=0)
            return 0

        bibtask.write_message("Processing all names...",
                              stream=sys.stdout, verbose=0)

        lengths = get_len_authornames_bibrefs()

        if not check_and_create_aid_tables():
            bibtask.write_message("Failed to create database tables!",
                                  stream=sys.stdout, verbose=0)
            return 0

        if lengths['names'] < 1:
            bibtask.write_message("Populating Authornames table. It's Empty.",
                                  stream=sys.stdout, verbose=0)
            bibtask.task_update_progress('Populating Authornames table.')
            populate_authornames()
            insert_user_log('daemon', '-1', 'UATFP', 'bibsched', 'status',
                            comment='bibauthorid_daemon, '
                            'update_authornames_tables_from_paper')


        if lengths['bibrefs'] < 1:
            bibtask.write_message("Populating Bibrefs lookup. It's Empty.",
                                  stream=sys.stdout, verbose=0)
            bibtask.task_update_progress('Populating Bibrefs lookup table.')
            populate_authornames_bibrefs_from_authornames()

        bibtask.task_update_progress('Processing all authors.')
        start_full_disambiguation(last_names="all",
                                 process_orphans=True,
                                 db_exists=False,
                                 populate_doclist=True,
                                 write_to_db=True)
        update_personID_from_algorithm()
        insert_user_log('daemon', '-1', 'update_aid', 'bibsched', 'status',
                    comment='bibauthorid_daemon, update_authorid_universe')

    if prepare_grid:
        bibtask.write_message("Preparing Grid Job",
                              stream=sys.stdout, verbose=0)
        data_dir_name = "grid_data"
        workdir_prefix = "job"
        max_records = 4000

        if data_dir:
            data_dir_name = data_dir

        if prefix:
            workdir_prefix = prefix

        if max_records_option:
            max_records = max_records_option

        _prepare_data_files_from_db(data_dir_name, workdir_prefix, max_records)

    if load_grid:
        bibtask.write_message("Reading Grid Job results and will write"
                              " them to the database.",
                              stream=sys.stdout, verbose=0)

        _write_data_files_to_db(data_dir)

    if update or update_cache:
        bibtask.write_message("update-cache: Processing recently updated"
                              " papers", stream=sys.stdout, verbose=0)
        bibtask.task_update_progress('update-cache: Processing recently'
                                     ' updated papers')
        _run_update_authornames_tables_from_paper(record_ids_nested, all_records)
        bibtask.write_message("update-cache: Finished processing papers",
                              stream=sys.stdout, verbose=0)
        bibtask.task_update_progress('update-cache: DONE')

    if update:
        bibtask.write_message("updating authorid universe",
                              stream=sys.stdout, verbose=0)
        bibtask.task_update_progress('updating authorid universe')
        _update_authorid_universe(record_ids, all_records)
        bibtask.write_message("done updating authorid universe",
                              stream=sys.stdout, verbose=0)
        bibtask.task_update_progress('done updating authorid universe')

    if clean_cache:
        bibtask.write_message("clean-cache: Processing recently updated"
                              " papers", stream=sys.stdout, verbose=0)
        bibtask.task_update_progress('clean-cache: Processing recently updated'
                                     ' papers for names')
        _run_authornames_tables_gc()
        bibtask.write_message("update-cache: Finished cleaning authornames "
                              "tables", stream=sys.stdout, verbose=0)
        bibtask.task_update_progress('clean-cache: Processing recently updated'
                                     ' papers for persons')
        _run_update_personID_table_from_paper(record_ids_nested, all_records)
        bibtask.write_message("update-cache: Finished cleaning PersonID"
                              " table", stream=sys.stdout, verbose=0)
        bibtask.task_update_progress('clean-cache: DONE')

    if repair_pid:
        bibtask.task_update_progress('Updating names cache...')
        _run_update_authornames_tables_from_paper()
        bibtask.task_sleep_now_if_required(can_stop_too=False)
        bibtask.task_update_progress('Removing person entities not touched by '
                                     'humans...')
        personid_remove_automatically_assigned_papers()
        bibtask.task_sleep_now_if_required(can_stop_too=False)
        bibtask.task_update_progress('Updating person entities...')
        update_personID_from_algorithm()
        bibtask.task_sleep_now_if_required(can_stop_too=False)
        bibtask.task_update_progress('Cleaning person tables...')
        _run_update_personID_table_from_paper()
        bibtask.task_sleep_now_if_required(can_stop_too=False)
        bibtask.task_update_progress('All repairs done.')

    return 1


def _task_submit_check_options():
    """
    Required by bibtask. Checks the options.
    """
    lastname = bibtask.task_get_option('lastname')
    process_all = bibtask.task_get_option('process_all')
    prepare_grid = bibtask.task_get_option('prepare_grid')
    load_grid = bibtask.task_get_option('load_grid_results')
    data_dir = bibtask.task_get_option('data_dir')
    prefix = bibtask.task_get_option('prefix')
    max_records = bibtask.task_get_option('max_records')
    update = bibtask.task_get_option('update')
    clean_cache = bibtask.task_get_option('clean_cache')
    update_cache = bibtask.task_get_option('update_cache')
    record_ids = bibtask.task_get_option('record_ids')
    all_records = bibtask.task_get_option('all_records')
    repair_pid = bibtask.task_get_option('repair_pid')

    if (record_ids and all_records):
        bibtask.write_message("ERROR: conflicting options: --record-ids and "
                              "--all-records cannot be specified at the same "
                              "time.", stream=sys.stdout, verbose=0)
        return False

    if (lastname == "None," or lastname == "None"):
        lastname = False

    if (not lastname and not process_all and not update
        and not prepare_grid and not load_grid and not clean_cache
        and not update_cache):
        bibtask.write_message("ERROR: One of the options -a, -n, -U, -G, -R, "
                              "--clean-cache, --update-cache is"
                              " required!", stream=sys.stdout, verbose=0)
        return False
    elif not (bool(lastname) ^ bool(process_all) ^ bool(update)
              ^ bool(prepare_grid) ^ bool(load_grid) ^ bool(clean_cache)
              ^ bool(update_cache) ^ bool(repair_pid)):
        bibtask.write_message("ERROR: Options -a -n -U -R -G --clean-cache "
                              "--update-cache --repair-personid are mutually"
                              " exclusive!", stream=sys.stdout, verbose=0)
        return False
    elif ((not prepare_grid and (data_dir or prefix or max_records)) and
          (not load_grid and (data_dir))):
        bibtask.write_message("ERROR: The options -d, -m and -p require -G or "
                              "-R to run!", stream=sys.stdout, verbose=0)
        return False
    elif load_grid and not bool(data_dir):
        bibtask.write_message("ERROR: The option -R requires the option -d "
                              "to run!", stream=sys.stdout, verbose=0)
        return False

    return True


def _write_data_files_to_db(data_dir_name):
    '''
    Reads all the files of a specified directory and writes the content
    to the memory cache and from there to the database.

    @param data_dir_name: Directory where to look for the files
    @type data_dir_name: string
    '''

    if data_dir_name.endswith("/"):
        data_dir_name = data_dir_name[0:-1]

    if not data_dir_name:
        bibtask.write_message("Data directory not specified. Task failed.",
                              stream=sys.stdout, verbose=0)
        return False

    if not osp.isdir(data_dir_name):
        bibtask.write_message("Specified Data directory is not a directory. "
                              "Task failed.",
                              stream=sys.stdout, verbose=0)
        return False

    job_dirs = os.listdir(data_dir_name)

    total = len(job_dirs)
    status = 0

    for job_dir in job_dirs:
        status += 1
        job_dir = "%s/%s" % (data_dir_name, job_dir)

        if not osp.isdir(job_dir):
            bibtask.write_message("This is not a directory and therefore "
                                  "skipped: %s." % job_dir,
                              stream=sys.stdout, verbose=0)
            continue

        results_dir = "%s/results/" % (job_dir,)

        if not osp.isdir(results_dir):
            bibtask.write_message("No result set found in %s"
                                  % (results_dir,), stream=sys.stdout,
                                  verbose=0)
            continue

        log_name = osp.abspath(job_dir).split("/")
        logfile = "%s/%s.log" % (job_dir, log_name[-1])
        logfile_lastline = ""

        if not osp.isfile(logfile):
            bibtask.write_message("No log file found in %s" % (job_dir,),
                                  stream=sys.stdout, verbose=0)
            continue

        try:
            logfile_lastline = tail(logfile)
        except IOError:
            logfile_lastline = ""

        if logfile_lastline.count("Finish! The computation finished in") < 1:
            bibtask.write_message("Log file indicates broken results for %s"
                                  % (job_dir,), stream=sys.stdout, verbose=0)
            continue

        correct_files = set(['realauthors.dat',
                             'ids.dat',
                             'virtual_author_clusters.dat',
                             'virtual_authors.dat',
                             'doclist.dat',
                             'virtual_author_data.dat',
                             'authornames.dat',
                             'virtual_author_cluster_cache.dat',
                             'realauthor_data.dat',
                             'ra_va_cache.dat']
                            )
        result_files = os.listdir(results_dir)

        if not correct_files.issubset(set(result_files)):
            bibtask.write_message("Reults folder does not hold the "
                                  "correct files: %s" % (results_dir,),
                                  stream=sys.stdout, verbose=0)
            continue

        bibtask.task_update_progress('Loading job %s of %s: %s'
                                     % (status, total, log_name[-1]))

        if (populate_structs_from_files(results_dir, results=True) and
            write_mem_cache_to_tables(sanity_checks=True)):
            bibtask.write_message("All Done.",
                                  stream=sys.stdout, verbose=0)
        else:
            bibtask.write_message("Could not write data to the tables from %s"
                                  % (results_dir,),
                                  stream=sys.stdout, verbose=0)


def _prepare_data_files_from_db(data_dir_name="grid_data",
                                workdir_prefix="job",
                                max_records=4000):
    '''
    Prepares grid jobs. Is a task running in bibsched.
    Meaning:
        1. Find all last names in the database
        2. For each last name:
            - find all documents regarding this last name (ignore first names)
            - if number of documents loaded into memory exceeds max_records,
              write the memory cache into files (cf. Files section).
              Each write back procedure will happen into a newly created
              directory. The prefix for the respective job directory may
              be specified as well as the name of the data directory where
              these job directories will be created.
    Files:
        - authornames.dat
        - virtual_authors.dat
        - virtual_author_data.dat
        - virtual_author_clusters.dat
        - virtual_author_cluster_cache.dat
        - realauthors.dat
        - realauthor_data.dat
        - doclist.dat
        - records.dat
        - ids.dat
        - ra_va_cache.dat

    @param data_dir_name: the name of the directory that will hold all the
        sub directories for the jobs.
    @type data_dir_name: string
    @param workdir_prefix: prefix for the job sub directories.
    @type workdir_prefix: string
    @param max_records: maximum number of records after which the memory
        cache is to be flushed to files.
    @type max_records: int
    '''
    try:
        max_records = int(max_records)
    except ValueError:
        max_records = 4000

    bibtask.write_message("Loading last names", stream=sys.stdout, verbose=0)
    bibtask.write_message("Limiting files to %s records" % (max_records,),
                          stream=sys.stdout, verbose=0)
    bibtask.task_update_progress('Loading last names...')

    last_names = find_all_last_names()
    last_name_queue = Queue.Queue()

    for last_name in sorted(last_names):
        last_name_queue.put(last_name)

    total = len(last_names)
    status = 1
    bibtask.write_message("Done. Loaded %s last names."
                          % (total), stream=sys.stdout, verbose=0)
    job_id = 0
    data_dir = ""

    if data_dir_name.startswith("/"):
        data_dir = data_dir_name
    else:
        data_dir = "%s/%s/" % (bconfig.FILE_PATH, data_dir_name)

    if not data_dir.endswith("/"):
        data_dir = "%s/" % (data_dir,)

    job_lnames = []

    while True:
        if last_name_queue.empty():
            bibtask.write_message("Done with all names.",
                                    stream=sys.stdout, verbose=0)
            break

        bibtask.task_sleep_now_if_required(can_stop_too=False)
        lname_list = last_name_queue.get()
        lname = None

        if lname_list:
            lname = lname_list[0]
            del(lname_list[0])
        else:
            bconfig.LOGGER.warning("Got an empty Queue element. "
                                   "Queue seems corrupted.")
            continue

        job_lnames.append(lname)
        bibtask.task_update_progress('Preparing job %d of %d: %s.'
                                     % (status, total, lname))
        bibtask.write_message(("Processing: %s (%d/%d).")
                                    % (lname, status, total),
                                    stream=sys.stdout, verbose=0)

        bibtask.task_sleep_now_if_required(can_stop_too=False)
        populate_doclist_for_author_surname(lname)
        post_remove_names = set()

        for name in [row['name'] for row in dat.AUTHOR_NAMES
                     if not row['processed']]:
            potential_removal = "%s," % (name.split(',')[0],)

            if not potential_removal == "%s" % (lname,):
                post_remove_names.add(potential_removal)

        if len(post_remove_names) > 1:
            removed = 0
            removed_names = []

            for post_remove_name in post_remove_names:
                if post_remove_name in lname_list:
                    lname_list.remove(post_remove_name)
                    removed_names.append(post_remove_name)
                    removed += 1

            bibtask.write_message(("-> Removed %s entries from the "
                                    + "computation list: %s")
                                    % (removed, removed_names),
                                    stream=sys.stdout, verbose=0)
            total -= removed

        if lname_list:
            last_name_queue.put(lname_list)

        if len(dat.RELEVANT_RECORDS) >= max_records:
            if not os.path.exists(data_dir):
                os.mkdir(data_dir)

            work_dir = "%s%s%s" % (data_dir, workdir_prefix, job_id)

            _write_to_files(work_dir, job_lnames)
            bibtask.task_sleep_now_if_required(can_stop_too=True)
            job_lnames = []
            job_id += 1

        status += 1

    if dat.RELEVANT_RECORDS:
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)

        work_dir = "%s%s%s" % (data_dir, workdir_prefix, job_id)

        _write_to_files(work_dir, job_lnames)
        bibtask.task_sleep_now_if_required(can_stop_too=True)

    return True


def _update_authorid_universe(record_ids=None, all_records=False):
    '''
    Updates all data related to the authorid algorithm.

    Sequence of operations:
        - Get all recently updated papers and remember time in the log
        - Get all authors on all papers
        - Extract collection of last names
        - For each last name:
            - Populate mem cache with cluster data
            - Delete updated records and their virtual authors from mem cache
            - Create virtual authors for new and updated records
            - Start matching algorithm
        - Update tables with results of the computation
        - Start personid update procedure
    '''

    def create_vas_from_specific_doclist(bibrec_ids):
        '''
        Processes the document list and creates a new minimal virtual author
        for each author in each record specified in the given list.

        @param bibrec_ids: Record IDs to concern in this update
        @type bibrec_ids: list of int
        '''
        num_docs = len([row for row in dat.DOC_LIST
                     if row['bibrecid'] in bibrec_ids])

        bconfig.LOGGER.log(25, "Creating minimal virtual authors for "
                                "all loaded docs (%s)"
                                % (num_docs))

        for docs in [row for row in dat.DOC_LIST
                     if row['bibrecid'] in bibrec_ids]:
            for author_id in docs['authornameids']:
                author_name = [an['name'] for an in dat.AUTHOR_NAMES
                               if an['id'] == author_id]
                refrecs = [ref[1] for ref in docs['authornameid_bibrefrec']
                           if ref[0] == author_id]
                refrec = -1

                if len(refrecs) > 1:
                    refrec = refrecs[0]
                elif refrecs:
                    refrec = refrecs[0]

                if refrec and author_name:
                    add_minimum_virtualauthor(author_id, author_name[0],
                                              docs['bibrecid'], 0, [], refrec)
                elif author_name:
                    add_minimum_virtualauthor(author_id, author_name[0],
                                              docs['bibrecid'], 0, [])

    dat.reset_mem_cache(True)
    last_log = None
    updated_records = []

    if not record_ids and not all_records:
        last_log = get_user_log(userinfo='daemon',
                                action='update_aid',
                                only_most_recent=True)
        if last_log:
            #select only the most recent papers
            recently_modified, last_update_time = get_papers_recently_modified(
                                                        date=last_log[0][2])
            insert_user_log('daemon', '-1', 'update_aid', 'bibsched', 'status',
                        comment='bibauthorid_daemon, update_authorid_universe',
                        timestamp=last_update_time[0][0])
            bibtask.write_message("Update authorid will operate on %s records."
                                  % (len(recently_modified)), stream=sys.stdout,
                                  verbose=0)
    
            if not recently_modified:
                bibtask.write_message("Update authorid: Nothing to do",
                                      stream=sys.stdout, verbose=0)
                return
    
            for rec in recently_modified:
                updated_records.append(rec[0])
                dat.update_log("rec_updates", rec[0])
    
        else:
            bibtask.write_message("Update authorid: Nothing to do",
                                  stream=sys.stdout, verbose=0)
            return

    elif record_ids and not all_records:
        updated_records = record_ids

    elif not record_ids and all_records:
        bibtask.write_message("Update is going to empty all aid tables...",
                              stream=sys.stdout, verbose=0)
        empty_aid_tables()
        bibtask.write_message("Update authorid will operate on all! records.",
                              stream=sys.stdout, verbose=0)
        bibtask.task_update_progress('Update is operating on all! records.')
        start_full_disambiguation(process_orphans=True,
                                  db_exists=False,
                                  populate_doclist=True,
                                  write_to_db=True)
        bibtask.task_update_progress('Update is done.')
        return

    bibtask.task_sleep_now_if_required(can_stop_too=True)
    authors = []
    author_last_names = set()

    bibtask.task_update_progress('Reading authors from updated records')
    bibtask.write_message("Reading authors from updated records",
                                stream=sys.stdout, verbose=0)
    updated_ras = set()

    # get all authors from all updated records
    for rec in updated_records:
        rec_authors = get_field_values_on_condition(rec, ['100', '700'], "a",
                                                    source="API")

        for rec_author in rec_authors:
            if not rec_author:
                bconfig.LOGGER.error("Invalid empty author string, which "
                                     "will be skipped on record %s"
                                     % (rec))
                continue

            author_in_list = [row for row in authors
                              if row['db_name'] == rec_author]

            if author_in_list:
                for upd in [row for row in authors
                            if row['db_name'] == rec_author]:
                    upd['records'].append(rec)
            else:
                last_name = split_name_parts(rec_author)[0]
                author_last_names.add(last_name)
                authors.append({'db_name': rec_author,
                                'records': [rec],
                                'last_name': last_name})

    for status, author_last_name in enumerate(author_last_names):
        bibtask.task_sleep_now_if_required(can_stop_too=False)
        current_authors = [row for row in authors
                           if row['last_name'] == author_last_name]
        total_lnames = len(author_last_names)
        total_authors = len(current_authors)
        bibtask.task_update_progress('Processing %s of %s cluster: "%s" '
                                     '(%s authors)'
                                     % (status + 1, total_lnames,
                                        author_last_name, total_authors))
        bibtask.write_message('Processing %s of %s cluster: "%s" '
                              '(%s authors)'
                              % (status + 1, total_lnames, author_last_name,
                                 total_authors), stream=sys.stdout, verbose=0)
        dat.reset_mem_cache(True)
        init_authornames(author_last_name)
        load_mem_cache_from_tables()
        bconfig.LOGGER.log(25, "-- Relevant data successfully read into memory"
                               " to start processing")

        for current_author in current_authors:
            load_records_to_mem_cache(current_author['records'])
            authornamesid = [row['id'] for row in dat.AUTHOR_NAMES
                             if row['db_name'] == current_author['db_name']]

            if not authornamesid:
                bconfig.LOGGER.error("The author '%s' rec '%s' is not in authornames "
                                     "and will be skipped. You might want "
                                     "to run authornames update before?"
                                     % (current_author['db_name'], rec))
                continue
            else:
                try:
                    authornamesid = int(authornamesid[0])
                except (IndexError, TypeError, ValueError):
                    bconfig.LOGGER.error("Invalid authornames ID!")
                    continue

            if not current_author['records']:
                bconfig.LOGGER.error("The author '%s' is not associated to any"
                                     " document and will be skipped."
                                     % (current_author['db_name']))
                continue

            for rec in current_author['records']:
                # remove VAs already existing for the record
                va_ids = get_va_ids_by_recid_lname(rec,
                                                   current_author["last_name"])

                if va_ids:
                    for va_id in va_ids:
                        ra_list = get_realauthors_by_virtuala_id(va_id)

                        for ra_id in ra_list:
                            remove_va_from_ra(ra_id, va_id)
                            del_ra_data_by_vaid(ra_id, va_id)

                        va_anames_id = get_virtualauthor_records(va_id,
                                                        "orig_authorname_id")

                        for an_list in [row['authornameids'] for row in
                                    dat.DOC_LIST if row['bibrecid'] == rec]:
                            try:
                                an_list.remove(va_anames_id)
                            except (ValueError):
                                # This names id is not in the list...don't care
                                pass

                        delete_virtual_author(va_id)

                # create new VAs for the record.
                update_doclist(rec, authornamesid)
                dat.update_log("rec_updates", rec)

            create_vas_from_specific_doclist(current_author['records'])

        bconfig.LOGGER.log(25, "-- Relevant data pre-processed successfully.")
        bibtask.task_sleep_now_if_required(can_stop_too=False)
        start_computation(process_doclist=False,
                          process_orphans=True,
                          print_stats=True)
        bconfig.LOGGER.log(25, "-- Computation finished. Will write back to "
                               "the database now.")
        update_db_result = update_tables_from_mem_cache(return_ra_updates=True)
        bibtask.task_sleep_now_if_required(can_stop_too=True)

        if not update_db_result[0]:
            bconfig.LOGGER.log(25, "Writing to persistence layer failed.")
        else:
            if update_db_result[1]:
                for updated_ra in update_db_result[1]:
                    if updated_ra:
                        updated_ras.add(updated_ra[0])

            bconfig.LOGGER.log(25, "Done updating authorid universe.")

    personid_ra_format = []

    for ra_id in updated_ras:
        personid_ra_format.append((ra_id,))

    bconfig.LOGGER.log(25, "Will now run personid update to make the "
                       "changes visible also on the front end and to "
                       "create person IDs for %s newly created and changed "
                       "authors." % len(updated_ras))
    bibtask.task_update_progress('Updating persistent Person IDs')
    bibtask.task_sleep_now_if_required(can_stop_too=False)
    update_personID_from_algorithm(personid_ra_format)
    bconfig.LOGGER.log(25, "Done updating everything. Thanks for flying "
                       "with bibauthorid!")


def _write_to_files(work_dir, job_lnames):
    '''
    Wrapper function around this internal write process.
    Triggers the write-back to the files to the mem cache.

    @param work_dir: where shall the files be stored?
    @type work_dir: string
    @param job_lnames: list of names
    @type job_lnames: list
    '''
    bibtask.task_update_progress('Writing to files in %s' % (work_dir))
    bibtask.write_message("Writing cluster with %s entries to "
                          "files in %s"
                          % (len(dat.RELEVANT_RECORDS), work_dir,),
                            stream=sys.stdout, verbose=0)

    if not os.path.exists(work_dir):
        os.mkdir(work_dir)

    write_mem_cache_to_files(work_dir, job_lnames)
    dat.reset_mem_cache(True)


def _run_update_authornames_tables_from_paper(record_ids=None, all_records=False):
    '''
    Runs the update on the papers which have been modified since the last run

    @note: This should be run as often as possible to keep authornames and
           authornames_bibrefs cache tables up to date.
    '''
    if not all_records and not record_ids:
        last_log = get_user_log(userinfo='daemon', action='UATFP', only_most_recent=True)
        if len(last_log) >= 1:
            #select only the most recent papers
            recently_modified, min_date = get_papers_recently_modified(date=last_log[0][2])
            insert_user_log('daemon', '-1', 'UATFP', 'bibsched', 'status', comment='bibauthorid_daemon, update_authornames_tables_from_paper', timestamp=min_date[0][0])

            if not recently_modified:
                bibtask.write_message("update_authornames_tables_from_paper: "
                                      "All names up to date.",
                                      stream=sys.stdout, verbose=0)
            else:
                bibtask.write_message("update_authornames_tables_from_paper: Running on %s papers " % str(len(recently_modified)), stream=sys.stdout, verbose=0)
                update_authornames_tables_from_paper(recently_modified)
        else:
            #this is the first time the utility is run, run on all the papers?
            #Probably better to write the log on the first authornames population
            #@todo: authornames population writes the log
            recently_modified, min_date = get_papers_recently_modified()
            insert_user_log('daemon', '-1', 'UATFP', 'bibsched', 'status', comment='bibauthorid_daemon, update_authornames_tables_from_paper', timestamp=min_date[0][0])
            bibtask.write_message("update_authornames_tables_from_paper: Running on %s papers " % str(len(recently_modified)), stream=sys.stdout, verbose=0)
            update_authornames_tables_from_paper(recently_modified)
    else:
        bibtask.write_message("update_authornames_tables_from_paper: Running "
                              "on all papers ",
                              stream=sys.stdout, verbose=0)
        update_authornames_tables_from_paper(record_ids)


def _run_update_personID_table_from_paper(record_ids=None, all_records=False):
    '''
    Runs the update on the papers which have been modified since the last run
    This is removing no-longer existing papers from the personid table.

    @note: Update recommended monthly.
    @warning: quite resource intensive.
    '''
    if not record_ids and not all_records:
        last_log = get_user_log(userinfo='daemon', action='UPITFP', only_most_recent=True)
        if len(last_log) >= 1:
            #select only the most recent papers
            recently_modified, min_date = get_papers_recently_modified(date=last_log[0][2])
            insert_user_log('daemon', '-1', 'UPITFP', 'bibsched', 'status', comment='bibauthorid_daemon, update_personID_table_from_paper', timestamp=min_date[0][0])

            if not recently_modified:
                bibtask.write_message("update_personID_table_from_paper: "
                                      "All person entities up to date.",
                                      stream=sys.stdout, verbose=0)
            else:
                bibtask.write_message("update_personID_table_from_paper: Running on: " + str(recently_modified), stream=sys.stdout, verbose=0)
                update_personID_table_from_paper(recently_modified)
        else:
            # Should not process all papers, hence authornames population writes
            # the appropriate log. In case the log is missing, process everything.
            recently_modified, min_date = get_papers_recently_modified()
            insert_user_log('daemon', '-1', 'UPITFP', 'bibsched', 'status', comment='bibauthorid_daemon, update_personID_table_from_paper', timestamp=min_date[0][0])
            bibtask.write_message("update_personID_table_from_paper: Running on: " + str(recently_modified), stream=sys.stdout, verbose=0)
            update_personID_table_from_paper(recently_modified)
        # @todo: develop a method that removes the respective VAs from the database
        # as well since no reference will be there for them any longer. VAs can be
        # found by searching for the authornames ID in the VA table. The
        # method has to kill RA data based on the VA (cf. del_ra_data_by_vaid in
        # ra utils as a reference), all VA2RA links, all VA data, all VAs and
        # finally all doclist refs that point to the respective bibrefs.
    else:
        update_personID_table_from_paper(record_ids)


def _run_authornames_tables_gc():
    '''
    Runs the garbage collector on the authornames tables, to get rid of
    deleted bibrefs in the respective author tables
    '''
    insert_user_log('daemon', '-1', 'ANTGC', 'bibsched', 'status', comment='bibauthorid_daemon, authornames_tables_gc')
    authornames_tables_gc()
