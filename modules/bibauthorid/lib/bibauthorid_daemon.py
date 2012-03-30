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
import bibtask

from bibauthorid_backinterface import get_papers_recently_modified
from bibauthorid_backinterface import get_user_log
from bibauthorid_backinterface import insert_user_log
from bibauthorid_backinterface import get_sql_time

try:
    any([True])
except:
    def any(x):
        for element in x:
            if element:
                return True
        return False


def bibauthorid_daemon():
    """Constructs the Bibauthorid bibtask."""
    bibtask.task_init(authorization_action='runbibclassify',
        authorization_msg="Bibauthorid Task Submission",
        description="""
Purpose:
  Disambiguate Authors and find their identities.
Examples:
  - Process all records that hold an author with last name 'Ellis':
      $ bibauthorid -u admin --update-personid --all-records
  - Disambiguate all records on a fresh installation
      $ bibauthorid -u admin --disambiguate --from-scratch
""",
        help_specific_usage="""
  bibauthorid [COMMAND] [OPTIONS]

  COMMAND
    You can choose only one from the following:
      --update-personid     Updates personid adding not yet assigned papers
                            to the system, in a fast, best effort basis.
                            Cleans the table from stale records.

      --disambiguate        Disambiguates all signatures in the database
                            using the tortoise/wedge algorithm. This usually
                            takes a LOT of time so the results are stored in
                            a special table. Use --merge to use the results.

      --merge               Updates the personid tables with the results from
                            the --disambiguate algorithm.

  OPTIONS
    Options for update personid
      (default)             Will update only the modified records since last
                            run.

      -i, --record-ids      Force the procedure to work only on the specified
                            records. This option is exclusive with --all-records.

      --all-records         Force the procedure to work on all records. This
                            option is exclusive with --record-ids.

    Options for disambiguate
      (default)             Performs full disambiguation of all records in the
                            current personid tables with respect to the user
                            decisions.

      --from-scratch        Ignores the current information in the personid
                            tables and disambiguates everything from scratch.

    There are no options for the merger.
""",
        version="Invenio Bibauthorid v%s" % bconfig.VERSION,
        specific_params=("i:",
            [
             "record-ids=",
             "disambiguate",
             "merge",
             "all-records",
             "update-personid",
             "from-scratch"
            ]),
        task_submit_elaborate_specific_parameter_fnc=_task_submit_elaborate_specific_parameter,
        task_submit_check_options_fnc=_task_submit_check_options,
        task_run_fnc=_task_run_core)


def _task_submit_elaborate_specific_parameter(key, value, opts, args):
    """
    Given the string key it checks it's meaning, eventually using the
    value. Usually, it fills some key in the options dict.
    It must return True if it has elaborated the key, False, if it doesn't
    know that key.
    """

    if key in ("--update-personid",):
        bibtask.task_set_option("update_personid", True)
    elif key in ("--record-ids", '-i'):
        if value.count("="):
            value = value[1:]
        value = value.split(",")
        bibtask.task_set_option("record_ids", value)
    elif key in ("--all-records",):
        bibtask.task_set_option("all_records", True)
    elif key in ("--disambiguate",):
        bibtask.task_set_option("disambiguate", True)
    elif key in ("--merge",):
        bibtask.task_set_option("merge", True)
    elif key in ("--from-scratch",):
        bibtask.task_set_option("from_scratch", True)
    else:
        return False

    return True


def _task_run_core():
    """
    Runs the requested task in the bibsched environment.
    """
    if bibtask.task_get_option('update_personid'):
        record_ids = bibtask.task_get_option('record_ids')
        if record_ids:
            record_ids = map(int, record_ids)
        all_records = bibtask.task_get_option('all_records')

        bibtask.task_update_progress('Updating personid...')
        run_rabbit(record_ids, all_records)
        bibtask.task_update_progress('PersonID update finished!')

    if bibtask.task_get_option("disambiguate"):
        bibtask.task_update_progress('Performing full disambiguation...')
        run_tortoise(bool(bibtask.task_get_option("from_scratch")))
        bibtask.task_update_progress('Full disambiguation finished!')

    if bibtask.task_get_option("merge"):
        bibtask.task_update_progress('Merging results...')
        run_merge()
        bibtask.task_update_progress('Merging finished!')

    return 1


def _task_submit_check_options():
    """
    Required by bibtask. Checks the options.
    """
    update_personid = bibtask.task_get_option("update_personid")
    disambiguate = bibtask.task_get_option("disambiguate")
    merge = bibtask.task_get_option("merge")

    record_ids = bibtask.task_get_option("record_ids")
    all_records = bibtask.task_get_option("all_records")
    from_scratch = bibtask.task_get_option("from_scratch")

    commands = bool(update_personid) + bool(disambiguate) + bool(merge)

    if commands == 0:
        bibtask.write_message("ERROR: At least one command should be specified!"
                              , stream=sys.stdout, verbose=0)
        return False

    if commands > 1:
        bibtask.write_message("ERROR: The options --update-personid, --disambiguate "
                              "and --merge are mutually exclusive."
                              , stream=sys.stdout, verbose=0)
        return False

    assert commands == 1

    if update_personid:
        if any((from_scratch,)):
            bibtask.write_message("ERROR: The only options which can be specified "
                                  "with --update-personid are --record-ids and "
                                  "--all-records"
                                  , stream=sys.stdout, verbose=0)
            return False

        options = bool(record_ids) + bool(all_records)
        if options > 1:
            bibtask.write_message("ERROR: conflicting options: --record-ids and "
                                  "--all-records are mutually exclusive."
                                  , stream=sys.stdout, verbose=0)
            return False

        if record_ids:
            for iden in record_ids:
                if not iden.isdigit():
                    bibtask.write_message("ERROR: Record_ids expects numbers. "
                                          "Provided: %s." % iden)
                    return False

    if disambiguate:
        if any((record_ids, all_records)):
            bibtask.write_message("ERROR: The only option which can be specified "
                                  "with --disambiguate is from-scratch"
                                  , stream=sys.stdout, verbose=0)
            return False

    if merge:
        if any((record_ids, all_records, from_scratch)):
            bibtask.write_message("ERROR: There are no options which can be "
                                  "specified along with --merge"
                                  , stream=sys.stdout, verbose=0)
            return False

    return True


def rabbit_with_log(papers, check_invalid_papers, log_comment):
    from bibauthorid_rabbit import rabbit

    starting_time = get_sql_time()
    rabbit(papers, check_invalid_papers)
    insert_user_log('daemon', '-1', 'PID_UPDATE', 'bibsched', 'status', comment=log_comment, timestamp=starting_time)

def run_rabbit(paperslist, all_records=False):
    if not paperslist and all_records:
        rabbit_with_log(None, True, 'bibauthorid_daemon, update_personid on all papers')
    elif not paperslist:
        last_log = get_user_log(userinfo='daemon', action='PID_UPDATE', only_most_recent=True)

        if len(last_log) >= 1:
            #select only the most recent papers
            recently_modified = get_papers_recently_modified(date=last_log[0][2])
            if not recently_modified:
                bibtask.write_message("update_personID_table_from_paper: "
                                      "All person entities up to date.",
                                      stream=sys.stdout, verbose=0)
            else:
                bibtask.write_message("update_personID_table_from_paper: Running on: " +
                                      str(recently_modified), stream=sys.stdout, verbose=0)
                rabbit_with_log(recently_modified, True, 'bibauthorid_daemon, run_personid_fast_assign_papers on '
                                                 + str([paperslist, all_records, recently_modified]))
        else:
            rabbit_with_log(None, True, 'bibauthorid_daemon, update_personid on all papers')
    else:
        rabbit_with_log(paperslist, True, 'bibauthorid_daemon, personid_fast_assign_papers on ' + str(paperslist))


def run_tortoise(from_scratch):
    from bibauthorid_tortoise import tortoise, tortoise_from_scratch
    if from_scratch:
        tortoise_from_scratch()
    else:
        tortoise()


def run_merge():
    from bibauthorid_merge import merge
    merge()

