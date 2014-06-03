# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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
Self citations task

Stores self-citations in a table for quick access
"""

import sys
import ConfigParser
from datetime import datetime

from invenio.config import CFG_BIBRANK_SELFCITES_USE_BIBAUTHORID, \
                           CFG_ETCDIR
from invenio.bibtask import task_set_option, \
                            task_get_option, write_message, \
                            task_sleep_now_if_required, \
                            task_update_progress
from invenio.dbquery import run_sql
from invenio.shellutils import split_cli_ids_arg
from invenio.bibrank_selfcites_indexer import update_self_cites_tables, \
                                              compute_friends_self_citations, \
                                              compute_simple_self_citations, \
                                              get_authors_tags
from invenio.bibrank_citation_searcher import get_refers_to
from invenio.bibauthorid_daemon import get_user_log as bibauthorid_user_log
from invenio.bibrank_citation_indexer import get_bibrankmethod_lastupdate

HELP_MESSAGE = """
  Scheduled (daemon) self cites options:
  -a, --new          Run on all newly inserted records.
  -m, --modified     Run on all newly modified records.
  -r, --recids       Record id for extraction.
  -c, --collections  Entire Collection for extraction.
  --rebuild          Rebuild pre-computed tables
                     * rnkRECORDSCACHE
                     * rnkEXTENDEDAUTHORS
                     * rnkSELFCITES

  Examples:
   (run a daemon job)
      selfcites -a
   (run on a set of records)
      selfcites --recids 1,2 -r 3
   (run on a collection)
      selfcites --collections "Reports"

"""
"Shown when passed options are invalid or -h is specified in the CLI"

DESCRIPTION = """This task handles the self-citations computation
It is run on modified records so that it can update the tables used for
displaying info in the citesummary format
"""
"Description of the task"

NAME = 'selfcites'


def check_options():
    """Check command line options"""
    if not task_get_option('new') \
            and not task_get_option('modified') \
            and not task_get_option('recids') \
            and not task_get_option('collections') \
            and not task_get_option('rebuild'):
        print >>sys.stderr, 'Error: No input file specified, you need' \
            ' to specify which files to run on'
        return False

    return True


def parse_option(key, value, dummy, args):
    """Parse command line options"""

    if args:
        # There should be no standalone arguments for any refextract job
        # This will catch args before the job is shipped to Bibsched
        raise StandardError("Error: Unrecognised argument '%s'." % args[0])

    if key in ('-a', '--new'):
        task_set_option('new', True)
    elif key in ('-m', '--modified'):
        task_set_option('modified', True)
    elif key == '--rebuild':
        task_set_option('rebuild', True)
    elif key in ('-c', '--collections'):
        collections = task_get_option('collections')
        if not collections:
            collections = set()
            task_set_option('collections', collections)
        collections.update(split_cli_ids_arg(value))
    elif key in ('-r', '--recids'):
        recids = task_get_option('recids')
        if not recids:
            recids = set()
            task_set_option('recids', recids)
        recids.update(split_cli_ids_arg(value))

    return True


def compute_and_store_self_citations(recid, tags, citations_fun,
                                                                verbose=False):
    """Compute and store self-cites in a table

    Args:
     - recid
     - tags: used when bibauthorid is desactivated see get_author_tags()
            in bibrank_selfcites_indexer
    """
    assert recid

    if verbose:
        write_message("* processing %s" % recid)
    references = get_refers_to(recid)
    recids_to_check = set([recid]) | set(references)
    placeholders = ','.join('%s' for r in recids_to_check)
    rec_row = run_sql("SELECT MAX(`modification_date`) FROM `bibrec`"
                      " WHERE `id` IN (%s)" % placeholders, recids_to_check)

    try:
        rec_timestamp = rec_row[0]
    except IndexError:
        write_message("record not found")
        return

    cached_citations_row = run_sql("SELECT `count` FROM `rnkSELFCITES`"
               " WHERE `last_updated` >= %s" \
               " AND `id_bibrec` = %s", (rec_timestamp[0], recid))
    if cached_citations_row and cached_citations_row[0][0]:
        if verbose:
            write_message("%s found (cached)" % cached_citations_row[0])
    else:
        cites = citations_fun(recid, tags)
        sql = """REPLACE INTO rnkSELFCITES (`id_bibrec`, `count`, `references`,
                 `last_updated`) VALUES (%s, %s, %s, NOW())"""
        references_string = ','.join(str(r) for r in references)
        run_sql(sql, (recid, len(cites), references_string))
        if verbose:
            write_message("%s found" % len(cites))


def rebuild_tables(config):
    task_update_progress('emptying tables')
    empty_self_cites_tables()
    task_update_progress('filling tables')
    fill_self_cites_tables(config)
    return True


def fetch_bibauthorid_last_update():
    bibauthorid_log = bibauthorid_user_log(userinfo='daemon',
                                           action='PID_UPDATE',
                                           only_most_recent=True)
    try:
        bibauthorid_end_date = bibauthorid_log[0][2]
    except IndexError:
        bibauthorid_end_date = datetime(year=1, month=1, day=1)

    return bibauthorid_end_date


def fetch_index_update():
    """Fetch last runtime of given task"""
    end_date = get_bibrankmethod_lastupdate('citation')

    if CFG_BIBRANK_SELFCITES_USE_BIBAUTHORID:
        bibauthorid_end_date = fetch_bibauthorid_last_update()
        end_date = min(end_date, bibauthorid_end_date)

    return end_date


def fetch_records(start_date, end_date):
    """Filter records not indexed out of recids

    We need to run after bibauthorid // bibrank citation indexer
    """
    sql = """SELECT `id` FROM `bibrec`
             WHERE `modification_date` <= %s
             AND `modification_date` > %s"""
    records = run_sql(sql, (end_date,
                            start_date))
    return [r[0] for r in records]


def fetch_concerned_records(name):
    start_date = get_bibrankmethod_lastupdate(name)
    end_date = fetch_index_update()
    return fetch_records(start_date, end_date)


def store_last_updated(name, date):
    run_sql("UPDATE rnkMETHOD SET last_updated=%s WHERE name=%s", (date, name))


def read_configuration(rank_method_code):
    filename = CFG_ETCDIR + "/bibrank/" + rank_method_code + ".cfg"
    config = ConfigParser.ConfigParser()
    try:
        config.readfp(open(filename))
    except StandardError:
        write_message("Cannot find configuration file: %s" % filename, sys.stderr)
        raise
    return config


def process_updates(rank_method_code):
    """
    This is what gets executed first when the task is started.
    It handles the --rebuild option. If that option is not specified
    we fall back to the process_one()
    """
    selfcites_config = read_configuration(rank_method_code)
    config = {
        'algorithm': selfcites_config.get(rank_method_code, "algorithm"),
        'friends_threshold': selfcites_config.get(rank_method_code, "friends_threshold")
    }
    begin_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    quick = task_get_option("quick") != "no"
    if not quick:
        return rebuild_tables(config)

    write_message("Starting")

    tags = get_authors_tags()
    recids = fetch_concerned_records(rank_method_code)
    citations_fun = get_citations_fun(config['algorithm'])

    write_message("recids %s" % str(recids))

    total = len(recids)
    for count, recid in enumerate(recids):
        task_sleep_now_if_required(can_stop_too=True)
        msg = "Extracting for %s (%d/%d)" % (recid, count + 1, total)
        task_update_progress(msg)
        write_message(msg)

        process_one(recid, tags, citations_fun)

    store_last_updated(rank_method_code, begin_date)

    write_message("Complete")
    return True


def get_citations_fun(algorithm):
    if algorithm == 'friends':
        citations_fun = compute_friends_self_citations
    else:
        citations_fun = compute_simple_self_citations
    return citations_fun


def process_one(recid, tags, citations_fun):
    """Self-cites core func, executed on each recid"""
    # First update this record then all its references
    compute_and_store_self_citations(recid, tags, citations_fun)

    references = get_refers_to(recid)
    for recordid in references:
        compute_and_store_self_citations(recordid, tags, citations_fun)


def empty_self_cites_tables():
    """
    This will empty all the self-cites tables

    The purpose is to rebuild the tables from scratch in case there is problem
    with them: inconsitencies, corruption,...
    """
    run_sql('TRUNCATE rnkSELFCITES')
    run_sql('TRUNCATE rnkEXTENDEDAUTHORS')
    run_sql('TRUNCATE rnkRECORDSCACHE')


def fill_self_cites_tables(config):
    """
    This will fill the self-cites tables with data

    The purpose of this function is to fill these tables on a website that
    never ran the self-cites daemon
    """
    algorithm = config['algorithm']
    tags = get_authors_tags()
    all_ids = [r[0] for r in run_sql('SELECT id FROM bibrec ORDER BY id')]
    citations_fun = get_citations_fun(algorithm)
    write_message('using %s' % citations_fun.__name__)
    if algorithm == 'friends':
        # We only needs this table for the friends algorithm or assimilated
        # Fill intermediary tables
        for index, recid in enumerate(all_ids):
            if index % 1000 == 0:
                msg = 'intermediate %d/%d' % (index, len(all_ids))
                task_update_progress(msg)
                write_message(msg)
                task_sleep_now_if_required()
            update_self_cites_tables(recid, config, tags)
    # Fill self-cites table
    for index, recid in enumerate(all_ids):
        if index % 1000 == 0:
            msg = 'final %d/%d' % (index, len(all_ids))
            task_update_progress(msg)
            write_message(msg)
            task_sleep_now_if_required()
        compute_and_store_self_citations(recid, tags, citations_fun)
