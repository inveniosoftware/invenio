# -*- mode: python; coding: utf-8; -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2010, 2011, 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
BibRank ranking daemon.

Usage: bibrank [options]
     Ranking examples:
       bibrank -wjif -a --id=0-30000,30001-860000 --verbose=9
       bibrank -wjif -d --modified='2002-10-27 13:57:26'
       bibrank -wwrd --rebalance --collection=Articles
       bibrank -wwrd -a -i 234-250,293,300-500 -u admin

 Ranking options:
 -w, --run=r1[,r2]         runs each rank method in the order given

 -c, --collection=c1[,c2]  select according to collection
 -i, --id=low[-high]       select according to doc recID
 -m, --modified=from[,to]  select according to modification date
 -l, --lastupdate          select according to last update

 -a, --add                 add or update words for selected records
 -d, --del                 delete words for selected records
 -S, --stat                show statistics for a method

 -R, --recalculate         recalculate weigth data, used by word frequency
                           and citation methods, should be used if ca 1%
                           of the document has been changed since last
                           time -R was used

 -E, --extcites=NUM        print the top entries of the external cites table.
                           These are entries that should be entered in
                           your collection, since they have been cited
                           by NUM or more other records present in the
                           system.  Useful for cataloguers to input
                           external papers manually.

 Repairing options:
 -k,  --check              check consistency for all records in the table(s)
                           check if update of ranking data is necessary
 -r, --repair              try to repair all records in the table(s)
 Scheduling options:
 -u, --user=USER           user name to store task, password needed
 -s, --sleeptime=SLEEP     time after which to repeat tasks (no)
                            e.g.: 1s, 30m, 24h, 7d
 -t, --time=TIME           moment for the task to be active (now)
                            e.g.: +15s, 5m, 3h , 2002-10-27 13:57:26
 General options:
 -h, --help                print this help and exit
 -V, --version             print version and exit
 -v, --verbose=LEVEL       verbose level (from 0 to 9, default 1)
"""

__revision__ = "$Id$"


import sys
import ConfigParser

from invenio.legacy.dbquery import run_sql
from invenio.legacy.bibsched.bibtask import task_init, write_message, \
    task_get_option, task_set_option, get_datetime, task_sleep_now_if_required
from invenio.base.factory import with_app_context

# pylint: disable=W0611
# Disabling unused import pylint check, since these are needed to get
# imported here, and are called later dynamically.
from invenio.legacy.bibrank.tag_based_indexer import \
     single_tag_rank_method, \
     citation, \
     download_weight_filtering_user, \
     download_weight_total, \
     file_similarity_by_times_downloaded, \
     index_term_count
from invenio.legacy.bibrank.word_indexer import word_similarity
from invenio.legacy.bibrank.citerank_indexer import citerank
from invenio.legacy.miscutil.solrutils_bibrank_indexer import \
    word_similarity_solr
from invenio.legacy.miscutil.xapianutils_bibrank_indexer import \
    word_similarity_xapian
from invenio.legacy.bibrank.selfcites_task import process_updates as selfcites
# pylint: enable=W0611
from invenio.modules.ranker.registry import configuration


nb_char_in_line = 50  # for verbose pretty printing
chunksize = 1000 # default size of chunks that the records will be treated by
base_process_size = 4500 # process base size

def split_ranges(parse_string):
    """Split ranges of numbers"""
    recIDs = []
    ranges = parse_string.split(",")
    for rang in ranges:
        tmp_recIDs = rang.split("-")

        if len(tmp_recIDs)==1:
            recIDs.append([int(tmp_recIDs[0]), int(tmp_recIDs[0])])
        else:
            if int(tmp_recIDs[0]) > int(tmp_recIDs[1]): # sanity check
                tmp = tmp_recIDs[0]
                tmp_recIDs[0] = tmp_recIDs[1]
                tmp_recIDs[1] = tmp
            recIDs.append([int(tmp_recIDs[0]), int(tmp_recIDs[1])])
    return recIDs

def get_date_range(var):
    "Returns the two dates contained as a low,high tuple"
    limits = var.split(",")
    if len(limits)==1:
        low = get_datetime(limits[0])
        return low, None
    if len(limits)==2:
        low = get_datetime(limits[0])
        high = get_datetime(limits[1])
        return low, high

def task_run_core():
    """Run the indexing task. The row argument is the BibSched task
    queue row, containing if, arguments, etc.
    Return 1 in case of success and 0 in case of failure.
    """
    if not task_get_option("run"):
        task_set_option("run", [name[0] for name in run_sql("SELECT name from rnkMETHOD")])

    for key in task_get_option("run"):
        task_sleep_now_if_required(can_stop_too=True)
        write_message("")
        filename = configuration.get(key + '.cfg', '')
        write_message("Getting configuration from file: %s" % filename,
            verbose=9)
        config = ConfigParser.ConfigParser()
        try:
            config.readfp(open(filename))
        except StandardError:
            write_message("Cannot find configuration file: %s. "
                "The rankmethod may also not be registered using "
                "the BibRank Admin Interface." % filename, sys.stderr)
            raise

        #Using the function variable to call the function related to the
        #rank method
        cfg_function = config.get("rank_method", "function")
        func_object = globals().get(cfg_function)
        if func_object:
            func_object(key)
        else:
            write_message("Cannot run method '%s', no function to call"
                % key)

    return True

@with_app_context()
def main():
    """Main that construct all the bibtask."""
    task_init(authorization_action='runbibrank',
            authorization_msg="BibRank Task Submission",
            description="""Ranking examples:
       bibrank -wjif -a --id=0-30000,30001-860000 --verbose=9
       bibrank -wjif -d --modified='2002-10-27 13:57:26'
       bibrank -wjif --rebalance --collection=Articles
       bibrank -wsbr -a -i 234-250,293,300-500 -u admin
       bibrank -u admin -w citation -E 10
       bibrank -u admin -w citation -A
""",
            help_specific_usage="""Ranking options:
 -w, --run=r1[,r2]         runs each rank method in the order given

 -c, --collection=c1[,c2]  select according to collection
 -i, --id=low[-high]       select according to doc recID
 -m, --modified=from[,to]  select according to modification date
 -l, --lastupdate          select according to last update

 -a, --add                 add or update words for selected records
 -d, --del                 delete words for selected records
 -S, --stat                show statistics for a method

 -R, --recalculate         recalculate weight data, used by word frequency
                           and citation methods, should be used if ca 1%
                           of the documents have been changed since last
                           time -R was used.  NOTE: This will replace the
                           entire set of weights, regardless of date/id
                           selection.

 -E, --extcites=NUM        print the top entries of the external cites table.
                           These are entries that should be entered in
                           your collection, since they have been cited
                           by NUM or more other records present in the
                           system.  Useful for cataloguers to input
                           external papers manually.

 -A --author-citations     Calculate author citations.

 Repairing options:
 -k,  --check              check consistency for all records in the table(s)
                           check if update of ranking data is necessary
 -r, --repair              try to repair all records in the table(s)
""",
            version=__revision__,
            specific_params=("AE:ladSi:m:c:kUrRM:f:w:", [
                "author-citations",
                "print-extcites=",
                "lastupdate",
                "add",
                "del",
                "repair",
                "maxmem",
                "flush",
                "stat",
                "rebalance",
                "id=",
                "collection=",
                "check",
                "modified=",
                "update",
                "run="]),
            task_submit_elaborate_specific_parameter_fnc=
                task_submit_elaborate_specific_parameter,
            task_run_fnc=task_run_core)


def task_submit_elaborate_specific_parameter(key, value, opts, dummy):
    """Elaborate a specific parameter of CLI bibrank."""
    if key in ("-a", "--add"):
        task_set_option("cmd", "add")
        if ("-x","") in opts or ("--del","") in opts:
            raise StandardError, "--add incompatible with --del"
    elif key in ("--run", "-w"):
        task_set_option("run", [])
        run = value.split(",")
        for run_key in range(0, len(run)):
            task_get_option('run').append(run[run_key])
    elif key in ("-r", "--repair"):
        task_set_option("cmd", "repair")
    elif key in ("-E", "--print-extcites"):
        try:
            task_set_option("print-extcites", int(value))
        except:
            task_set_option("print-extcites", 10) # default fallback value
        task_set_option("cmd", "print-missing")
    elif key in ("-A", "--author-citations"):
        task_set_option("author-citations", "1")
    elif key in ("-d", "--del"):
        task_set_option("cmd", "del")
    elif key in ("-k", "--check"):
        task_set_option("cmd", "check")
    elif key in ("-S", "--stat"):
        task_set_option("cmd", "stat")
    elif key in ("-i", "--id"):
        task_set_option("id", task_get_option("id") + split_ranges(value))
        task_set_option("last_updated", "")
    elif key in ("-c", "--collection"):
        task_set_option("collection", value)
    elif key in ("-R", "--rebalance"):
        task_set_option("quick", "no")
    elif key in ("-f", "--flush"):
        task_set_option("flush", int(value))
    elif key in ("-M", "--maxmem"):
        task_set_option("maxmem", int(value))
        if task_get_option("maxmem") < base_process_size + 1000:
            raise StandardError, "Memory usage should be higher than %d kB" % \
                (base_process_size + 1000)
    elif key in ("-m", "--modified"):
        task_set_option("modified", get_date_range(value))#2002-10-27 13:57:26)
        task_set_option("last_updated", "")
    elif key in ("-l", "--lastupdate"):
        task_set_option("last_updated", "last_updated")
    else:
        return False
    return True
