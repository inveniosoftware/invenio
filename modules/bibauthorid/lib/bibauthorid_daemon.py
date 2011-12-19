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
import bibauthorid_config as bconfig

from bibauthorid_backinterface import get_papers_recently_modified
from bibauthorid_backinterface import update_authornames_tables_from_paper
from bibauthorid_backinterface import get_user_log
from bibauthorid_backinterface import insert_user_log
from bibauthorid_personid_maintenance import update_personID_table_from_paper
from bibauthorid_personid_maintenance import update_personID_from_algorithm
from bibauthorid_personid_maintenance import personid_remove_automatically_assigned_papers
from bibauthorid_personid_maintenance import personid_fast_assign_papers

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
  --repair-personid         Deletes untouched person entities to then
                            re-create and updated these entities.
  --fast-update-personid    Updates personid adding not yet assigned papers to the system,
                            in a fast, best effort basis. Use -r to limit to a comma separated
                            set of records.
  --personid-gc             Garbage collects personid for stale records. Use -r to limit to a comma
                            separated set of records.
  -r, --record-ids          Specifies a list of record ids. To use as on option
                            for --update-universe to limit the update to the
                            selected records
  --all-records             To use as on option for --update-universe to
                            perform the update an all existing record ids. Be
                            WARNED that this will empty and re-fill all aid*
                            tables in the process!
""",
        version="Invenio Bibauthorid v%s" % bconfig.VERSION,
        specific_params=("r:",
            [
             "record-ids=",
             "all-records",
             "repair-personid",
             "fast-update-personid",
             "personid-gc"
            ]),
        task_submit_elaborate_specific_parameter_fnc
=_task_submit_elaborate_specific_parameter,
        task_submit_check_options_fnc
=_task_submit_check_options,
        task_run_fnc
=_task_run_core)


def _task_submit_elaborate_specific_parameter(key, value, opts, args):
    """
    Given the string key it checks it's meaning, eventually using the
    value. Usually, it fills some key in the options dict.
    It must return True if it has elaborated the key, False, if it doesn't
    know that key.
    """

    if key in ("--repair-personid",):
        bibtask.task_set_option("repair_pid", True)

    elif key in ("--fast-update-personid",):
        bibtask.task_set_option("fast_update_personid", True)

    elif key in ("--personid-gc",):
        bibtask.task_set_option("personid_gc", True)

    elif key in ("--record-ids", '-r'):
        if value.count("="):
            value = value[1:]
        value = value.split(",")
        bibtask.task_set_option("record_ids", value)

    elif key in ("--all-records",):
        bibtask.task_set_option("all_records", True)

    else:
        return False

    return True


def _task_run_core():
    """
    Runs the requested task in the bibsched environment.
    """

    repair_pid = bibtask.task_get_option('repair_pid')
    fast_update_personid = bibtask.task_get_option('fast_update_personid')
    personid_gc = bibtask.task_get_option('personid_gc')
    record_ids = bibtask.task_get_option('record_ids')
    all_records = bibtask.task_get_option('all_records')

    if record_ids:
        record_ids_nested = [[p] for p in record_ids]
    else:
        record_ids_nested = None

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

    if fast_update_personid:
        bibtask.task_update_progress('Updating personid...')
        _run_personid_fast_assign_papers(record_ids_nested, all_records)
        bibtask.task_update_progress('PersonID update finished!')

    if personid_gc:
        bibtask.task_update_progress('Updating personid (GC)...')
        _run_personid_gc(record_ids_nested, all_records)
        bibtask.task_update_progress('PersonID update finished (GC)!')
    return 1


def _task_submit_check_options():
    """
    Required by bibtask. Checks the options.
    """
    record_ids = bibtask.task_get_option('record_ids')
    all_records = bibtask.task_get_option('all_records')
    repair_pid = bibtask.task_get_option('repair_pid')
    fast_update_personid = bibtask.task_get_option('fast_update_personid')
    personid_gc = bibtask.task_get_option('personid_gc')

    params = bool(record_ids) + bool(all_records)
    if params > 1:
        bibtask.write_message("ERROR: conflicting options: --record-ids and "
                              "--all-records cannot be specified at the same "
                              "time.", stream=sys.stdout, verbose=0)
        return False

    if record_ids:
        for iden in record_ids:
            if not iden.isdigit():
                bibtask.write_message("ERROR: Record_ids expects numbers. "
                                      "Provided: %s." % iden)
                return False

    opts = bool(repair_pid) + bool(fast_update_personid) + bool(personid_gc)
    if opts == 0:
        bibtask.write_message("ERROR: One of the options --fast-update-personid, "
                              "--personid-gc, --repair-personid is required!"
                              , stream=sys.stdout, verbose=0)
        return False
    elif opts > 1:
        bibtask.write_message("ERROR: Options --fast-update-personid, "
                              "--personid-gc, --repair-personid "
                              "are mutually exclusive!", stream=sys.stdout, verbose=0)
        return False

    if repair_pid and params:
        bibtask.write_message("ERROR: --repair_pid does not require any parameters!"
                              , stream=sys.stdout, verbose=0)
        return False

    return True


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
            insert_user_log('daemon', '-1', 'UATFP', 'bibsched', 'status',
                            comment='bibauthorid_daemon, update_authornames_tables_from_paper',
                            timestamp=min_date[0][0])

            if not recently_modified:
                bibtask.write_message("update_authornames_tables_from_paper: "
                                      "All names up to date.",
                                      stream=sys.stdout, verbose=0)
            else:
                bibtask.write_message(
                                "update_authornames_tables_from_paper: Running on %s papers " % str(
                                len(recently_modified)), stream=sys.stdout, verbose=0)
                update_authornames_tables_from_paper(recently_modified)
        else:
            #this is the first time the utility is run, run on all the papers?
            #Probably better to write the log on the first authornames population
            #@todo: authornames population writes the log
            recently_modified, min_date = get_papers_recently_modified()
            insert_user_log('daemon', '-1', 'UATFP', 'bibsched', 'status',
                            comment='bibauthorid_daemon, update_authornames_tables_from_paper',
                            timestamp=min_date[0][0])
            bibtask.write_message(
                            "update_authornames_tables_from_paper: Running on %s papers " % str(
                            len(recently_modified)), stream=sys.stdout, verbose=0)
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
            insert_user_log('daemon', '-1', 'UPITFP', 'bibsched', 'status',
                            comment='bibauthorid_daemon, update_personID_table_from_paper',
                            timestamp=min_date[0][0])

            if not recently_modified:
                bibtask.write_message("update_personID_table_from_paper: "
                                      "All person entities up to date.",
                                      stream=sys.stdout, verbose=0)
            else:
                bibtask.write_message("update_personID_table_from_paper: Running on: " +
                                      str(recently_modified), stream=sys.stdout, verbose=0)
                update_personID_table_from_paper(recently_modified)
        else:
            # Should not process all papers, hence authornames population writes
            # the appropriate log. In case the log is missing, process everything.
            recently_modified, min_date = get_papers_recently_modified()
            insert_user_log('daemon', '-1', 'UPITFP', 'bibsched', 'status',
                            comment='bibauthorid_daemon, update_personID_table_from_paper',
                            timestamp=min_date[0][0])
            bibtask.write_message("update_personID_table_from_paper: Running on: "
                                  + str(recently_modified), stream=sys.stdout, verbose=0)
            update_personID_table_from_paper(recently_modified)
    else:
        update_personID_table_from_paper(record_ids)

def _run_personid_fast_assign_papers(paperslist, all_records=False):
#    insert_user_log('daemon', '-1', 'PFAP', 'bibsched', 'status',
#                    comment='bibauthorid_daemon, personid_fast_assign_papers on ' + str(paperslist))
    if not paperslist and all_records:
        insert_user_log('daemon', '-1', 'PFAP', 'bibsched', 'status',
                    comment='bibauthorid_daemon, personid_fast_assign_papers on all papers')
        #update_authornames_tables_from_paper()
        personid_fast_assign_papers()
    elif not paperslist:
        last_log = get_user_log(userinfo='daemon', action='PFAP', only_most_recent=True)
        if len(last_log) >= 1:
            #select only the most recent papers
            recently_modified, min_date = get_papers_recently_modified(date=last_log[0][2])
            insert_user_log('daemon', '-1', 'PFAP', 'bibsched', 'status',
                            comment='bibauthorid_daemon, run_personid_fast_assign_papers on '
                            + str([paperslist, all_records, recently_modified]),
                            timestamp=min_date[0][0])
            if not recently_modified:
                bibtask.write_message("update_personID_table_from_paper: "
                                      "All person entities up to date.",
                                      stream=sys.stdout, verbose=0)
            else:
                bibtask.write_message("update_personID_table_from_paper: Running on: " +
                                      str(recently_modified), stream=sys.stdout, verbose=0)
                update_authornames_tables_from_paper()
                personid_fast_assign_papers(recently_modified)
        else:
            insert_user_log('daemon', '-1', 'PFAP', 'bibsched', 'status',
                    comment='bibauthorid_daemon, personid_fast_assign_papers on all papers')
        update_authornames_tables_from_paper()
        personid_fast_assign_papers()
    else:
        insert_user_log('daemon', '-1', 'PFAP', 'bibsched', 'status',
                    comment='bibauthorid_daemon, personid_fast_assign_papers on ' + str(paperslist))
        update_authornames_tables_from_paper(paperslist)
        personid_fast_assign_papers(paperslist)

def _run_personid_gc(paperslist, all_records=False):
#    insert_user_log('daemon', '-1', 'PGC', 'bibsched', 'status',
#                    comment='bibauthorid_daemon, personid_gc (update_personid_from_papers) on '
#                    + str(paperslist))
    if not paperslist and  all_records:
        #update_authornames_tables_from_paper()
        insert_user_log('daemon', '-1', 'PGC', 'bibsched', 'status',
            comment='bibauthorid_daemon, personid_gc (update_personid_from_papers) on all papers')
        update_personID_table_from_paper()
    elif not paperslist:
        last_log = get_user_log(userinfo='daemon', action='PGC', only_most_recent=True)
        if len(last_log) >= 1:
            #select only the most recent papers
            recently_modified, min_date = get_papers_recently_modified(date=last_log[0][2])
            insert_user_log('daemon', '-1', 'PGC', 'bibsched', 'status',
                            comment='bibauthorid_daemon, update_personid_from_papers on '
                            + str([paperslist, all_records, recently_modified]),
                            timestamp=min_date[0][0])

            if not recently_modified:
                bibtask.write_message("update_personID_table_from_paper: "
                                      "All person entities up to date.",
                                      stream=sys.stdout, verbose=0)
            else:
                bibtask.write_message("update_personID_table_from_paper: Running on: " +
                                      str(recently_modified), stream=sys.stdout, verbose=0)
                personid_fast_assign_papers(recently_modified)
        else:
            insert_user_log('daemon', '-1', 'PGC', 'bibsched', 'status',
            comment='bibauthorid_daemon, personid_gc (update_personid_from_papers) on all papers')
            update_personID_table_from_paper()
    else:
        insert_user_log('daemon', '-1', 'PGC', 'bibsched', 'status',
                comment='bibauthorid_daemon, personid_gc (update_personid_from_papers) on '
                + str(paperslist))
        update_authornames_tables_from_paper(paperslist)
        update_personID_table_from_paper(paperslist)


