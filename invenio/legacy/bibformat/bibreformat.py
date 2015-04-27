# -*- mode: python; coding: utf-8; -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2010, 2011, 2012, 2014, 2015 CERN.
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

from __future__ import print_function

"""Call BibFormat engine and create HTML brief (and other) formats cache for
   bibliographic records."""

__revision__ = "$Id$"

import os
from intbitset import intbitset
from datetime import datetime

from invenio.base.factory import with_app_context
from invenio.legacy.dbquery import run_sql
from invenio.legacy.search_engine import perform_request_search, search_pattern
from invenio.legacy.bibrank.citation_searcher import get_cited_by
from invenio.legacy.bibrank.citation_indexer import get_bibrankmethod_lastupdate
from invenio.legacy.bibformat.dblayer import save_preformatted_record
from invenio.utils.shell import split_cli_ids_arg
from invenio.modules.records.api import get_record
from invenio.legacy.bibsched.bibtask import task_init, \
    write_message, \
    task_set_option, \
    task_get_option, \
    task_update_progress, \
    task_has_option, \
    task_sleep_now_if_required
from invenio.modules.formatter.engine import format_record_1st_pass


def fetch_last_updated(fmt):
    select_sql = "SELECT last_updated FROM format WHERE code = %s"
    row = run_sql(select_sql, (fmt.lower(), ))

    # Fallback in case we receive None instead of a valid date
    last_date = row[0][0] or datetime(year=1900, month=1, day=1)

    return last_date


def store_last_updated(fmt, iso_date):
    sql = "UPDATE format SET last_updated = %s " \
        "WHERE code = %s AND (last_updated < %s or last_updated IS NULL)"
    run_sql(sql, (iso_date, fmt.lower(), iso_date))


# run the bibreformat task bibsched scheduled

@with_app_context()
def bibreformat_task(fmt, recids, without_fmt, process):
    """BibReformat main task.

    @param fmt: output format to use
    @param process:
    @param recids: a list of record IDs to reformat
    @return: None
    """
    write_message("Processing format %s" % fmt)

    t1 = os.times()[4]

    start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    latest_bibrank_run = get_bibrankmethod_lastupdate('citation')

    def related_records(recids, recids_processed):
        if fmt == "HDREF" and recids:
            # HDREF represents the references tab
            # the tab needs to be recomputed not only when the record changes
            # but also when one of the citations changes
            sql = """SELECT id, modification_date FROM bibrec
                     WHERE id in (%s)""" % ','.join(str(r) for r in recids)

            def check_date(mod_date):
                return mod_date.strftime(
                    "%Y-%m-%d %H:%M:%S") < latest_bibrank_run
            rel_recids = intbitset([recid for recid, mod_date in run_sql(sql)
                                    if check_date(mod_date)])
            for r in rel_recids:
                recids |= intbitset(get_cited_by(r))

        # To not process recids twice
        recids -= recids_processed
        # Adds to the set of processed recids
        recids_processed += recids

        return recids

    def recid_chunker(recids):
        recids_processed = intbitset()
        chunk = intbitset()

        for recid in recids:
            if len(chunk) == 5000:
                for r in related_records(chunk, recids_processed):
                    yield r
                recids_processed += chunk
                chunk = intbitset()

            if recid not in recids_processed:
                chunk.add(recid)

        if chunk:
            for r in related_records(chunk, recids_processed):
                yield r

    recIDs = list(recid_chunker(recids))

### list of corresponding record IDs was retrieved
### now format the selected records

    if without_fmt:
        write_message("Records to be processed: %d" % len(recIDs))
        write_message("Out of it records without existing cache: %d" %
                      len(without_fmt))
    else:
        write_message("Records to be processed: %d" % len(recIDs))

### Initialize main loop

    total_rec = 0     # Total number of records
    tbibformat = 0     # time taken up by external call
    tbibupload = 0     # time taken up by external call

### Iterate over all records prepared in lists I (option)
    if process:
        total_rec_1, tbibformat_1, tbibupload_1 = iterate_over_new(recIDs, fmt)
        total_rec += total_rec_1
        tbibformat += tbibformat_1
        tbibupload += tbibupload_1

### Store last run time
    if task_has_option("last"):
        write_message("storing run date to %s" % start_date)
        store_last_updated(fmt, start_date)

### Final statistics

    t2 = os.times()[4]

    elapsed = t2 - t1
    message = "total records processed: %d" % total_rec
    write_message(message)

    message = "total processing time: %2f sec" % elapsed
    write_message(message)

    message = "Time spent on external call (os.system):"
    write_message(message)

    message = " bibformat: %2f sec" % tbibformat
    write_message(message)

    message = " bibupload: %2f sec" % tbibupload
    write_message(message)


def check_validity_input_formats(input_formats):
    """Check the validity of every input format.

    :param input_formats: list of given formats
    :type input_formats: list
    :return: if there is any invalid input format it returns this value
    :rtype: string
    """
    from invenio.modules.formatter import registry
    tested_formats = set([aformat.lower() for aformat in input_formats])
    invalid_formats = tested_formats - set(registry.output_formats.keys())
    return invalid_formats[0] if len(invalid_formats) else ''


### Bibreformat all selected records (using new python bibformat)
### (see iterate_over_old further down)


def _update_recjson_format(recid, *args, **kwargs):
    """Update RECJSON cache.

    :param int recid: record id to process
    """
    dummy = get_record(recid, reset_cache=True)


def _update_format(recid, fmt):
    """Usual format update procedure, gets the formatted record and saves it.

    :param int recid: record id to process
    :param str fmt: format to update/create, i.e. 'HB'
    """
    record, needs_2nd_pass = format_record_1st_pass(recID=recid,
                                                    of=fmt,
                                                    on_the_fly=True,
                                                    save_missing=False)
    save_preformatted_record(recID=recid,
                             of=fmt,
                             res=record,
                             needs_2nd_pass=needs_2nd_pass,
                             low_priority=True)


_CFG_BIBFORMAT_UPDATE_FORMAT_FUNCTIONS = {'recjson': _update_recjson_format}
"""Specific functions to be used for each format if needed.
If not set `_update_format` will be used.
"""


def iterate_over_new(recIDs, fmt):
    """Iterate over list of IDs.

    @param list: the list of record IDs to format
    @param fmt: the output format to use
    @return: tuple (total number of records, time taken to format, time taken
        to insert)
    """
    tbibformat = 0     # time taken up by external call
    tbibupload = 0     # time taken up by external call

    tot = len(recIDs)
    reformat_function = _CFG_BIBFORMAT_UPDATE_FORMAT_FUNCTIONS.get(
        fmt.lower(), _update_format)
    for count, recID in enumerate(recIDs):
        t1 = os.times()[4]
        reformat_function(recID, fmt)
        t2 = os.times()[4]
        tbibformat += t2 - t1
        if count % 100 == 0:
            write_message("   ... formatted %s records out of %s" %
                          (count, tot))
            task_update_progress('Formatted %s out of %s' % (count, tot))
            task_sleep_now_if_required(can_stop_too=True)

    if tot % 100 != 0:
        write_message("   ... formatted %s records out of %s" % (tot, tot))

    return tot, tbibformat, tbibupload


def all_records():
    """Produce record IDs for all available records."""
    return intbitset(run_sql("SELECT id FROM bibrec"))


def outdated_caches(fmt, last_updated, chunk_size=5000):
    sql = """SELECT br.id
             FROM bibrec AS br
             INNER JOIN bibfmt AS bf ON bf.id_bibrec = br.id
             WHERE br.modification_date >= %s
             AND bf.format = %s
             AND bf.last_updated < br.modification_date
             AND br.id BETWEEN %s AND %s"""

    last_updated_str = last_updated.strftime('%Y-%m-%d %H:%M:%S')
    recids = intbitset()
    max_id = run_sql("SELECT max(id) FROM bibrec")[0][0] or 0
    for start in xrange(1, max_id + 1, chunk_size):
        end = start + chunk_size
        recids += intbitset(run_sql(sql, (last_updated_str, fmt, start, end)))

    return recids


def missing_caches(fmt, chunk_size=100000):
    """Produce record IDs to be formated, because their fmt cache is missing.

    @param fmt: format to query for
    @return: record IDs generator without pre-created format cache
    """
    write_message("Querying database for records without cache...")

    all_recids = intbitset()
    max_id = run_sql("SELECT max(id) FROM bibrec")[0][0] or 0
    for start in xrange(1, max_id + 1, chunk_size):
        end = start + chunk_size
        sql = "SELECT id FROM bibrec WHERE id BETWEEN %s AND %s"
        recids = intbitset(run_sql(sql, (start, end)))
        sql = """SELECT id_bibrec FROM bibfmt
                 WHERE id_bibrec BETWEEN %s AND %s
                 AND format = %s"""
        without_fmt = intbitset(run_sql(sql, (start, end, fmt)))
        all_recids += recids - without_fmt

    return all_recids


def query_records(params):
    """Produce record IDs from given query parameters.

    By passing the appriopriate CLI options, we can query here for additional
    records.
    """
    write_message("Querying database (records query)...")
    res = intbitset()
    if params['field'] or params['collection'] or params['pattern']:

        if not params['collection']:
            # use search_pattern() whenever possible, as it can search
            # even in private collections
            res = search_pattern(p=params['pattern'],
                                 f=params['field'],
                                 m=params['matching'])
        else:
            # use perform_request_search when '-c' argument has been
            # defined, as it is not supported by search_pattern()
            res = intbitset(perform_request_search(req=None,
                                                   of='id',
                                                   c=params['collection'],
                                                   p=params['pattern'],
                                                   f=params['field']))
    return res


def task_run_core():
    """Run the task by fetching arguments from the BibSched task queue.

    This is what BibSched will be invoking via daemon call.
    """
    fmts = task_get_option('format', 'HB,RECJSON')
    for fmt in fmts.split(','):
        last_updated = fetch_last_updated(fmt)
        write_message("last stored run date is %s" % last_updated)

        recids = intbitset()

        if task_has_option("all"):
            recids += all_records()

        if task_has_option("last"):
            recids += outdated_caches(fmt, last_updated)

        if task_has_option('ignore_without'):
            without_fmt = intbitset()
        else:
            without_fmt = missing_caches(fmt)
            recids += without_fmt

        cli_recids = split_cli_ids_arg(task_get_option('recids', ''))
        recids += cli_recids

        query_params = {'collection': task_get_option('collection', ''),
                        'field': task_get_option('field', ''),
                        'pattern': task_get_option('pattern', ''),
                        'matching': task_get_option('matching', '')}
        recids += query_records(query_params)

        bibreformat_task(fmt,
                         recids,
                         without_fmt,
                         not task_has_option('noprocess'))

    return True


def main():
    """Main that construct all the bibtask."""
    task_init(authorization_action='runbibformat',
              authorization_msg="BibReformat Task Submission",
              description="""
BibReformat formats the records and saves the produced outputs for
later retrieval.

BibReformat is usually run periodically via BibSched in order to (1)
format new records in the database and to (2) reformat records for
which the meta data has been modified.

BibReformat has to be run manually when (3) format config files have
been modified, in order to see the changes in the web interface.

Although it is not necessary to run BibReformat to display formatted
records in the web interface, BibReformat allows to improve serving
speed by precreating the outputs. It is suggested to run
BibReformat for 'HB' output.

Option -m cannot be used at the same time as option -c.
Option -c prevents from finding records in private collections.

Examples:
  bibreformat                    Format all new or modified records (in HB and RECJSON).
  bibreformat -o HD              Format all new or modified records in HD.
  bibreformat -o HD,HB           Format all new or modified records in HD and HB.

  bibreformat -a                 Force reformatting all records (in HB).
  bibreformat -c 'Photos'        Force reformatting all records in 'Photos' collection (in HB).
  bibreformat -c 'Photos' -o HD  Force reformatting all records in 'Photos' collection in HD.

  bibreformat -i 15              Force reformatting record 15 (in HB).
  bibreformat -i 15:20           Force reformatting records 15 to 20 (in HB).
  bibreformat -i 15,16,17        Force reformatting records 15, 16 and 17 (in HB).

  bibreformat -n                 Show how many records are to be (re)formatted.
  bibreformat -n -c 'Articles'   Show how many records are to be (re)formatted in 'Articles' collection.

  bibreformat -oHB -s1h          Format all new and modified records every hour, in HB.
""", help_specific_usage="""  -o,  --formats         \t Specify output format/s (default HB)
  -n,  --noprocess      \t Count records to be formatted (no processing done)
Reformatting options:
  -a,  --all            \t Force reformatting all records
  -c,  --collection     \t Force reformatting records by collection
  -f,  --field          \t Force reformatting records by field
  -p,  --pattern        \t Force reformatting records by pattern
  -i,  --id             \t Force reformatting records by record id(s)
  --no-missing          \t Ignore reformatting records without format
Pattern options:
  -m,  --matching       \t Specify if pattern is exact (e), regular expression (r),
                        \t partial (p), any of the words (o) or all of the words (a)
""",
              version=__revision__,
              specific_params=("ac:f:p:lo:nm:i:",
                               ["all",
                                "collection=",
                                "matching=",
                                "field=",
                                "pattern=",
                                "format=",
                                "noprocess",
                                "id=",
                                "no-missing"]),
              task_submit_check_options_fnc=task_submit_check_options,
              task_submit_elaborate_specific_parameter_fnc=
                 task_submit_elaborate_specific_parameter,
              task_run_fnc=task_run_core)


def task_submit_check_options():
    """Last checks and updating on the options..."""
    if not (task_has_option('all') or task_has_option('collection')
            or task_has_option('field') or task_has_option('pattern')
            or task_has_option('matching') or task_has_option('recids')):
        task_set_option('last', 1)
    return True


def task_submit_elaborate_specific_parameter(key, value, opts, args):  # pylint: disable-msg=W0613
    """
    Elaborate specific CLI parameters of BibReformat.

    @param key: a parameter key to check
    @param value: a value associated to parameter X{Key}
    @return: True for known X{Key} else False.
    """
    if key in ("-a", "--all"):
        task_set_option("all", 1)
    elif key in ("--no-missing", ):
        task_set_option("ignore_without", 1)
    elif key in ("-c", "--collection"):
        task_set_option("collection", value)
    elif key in ("-n", "--noprocess"):
        task_set_option("noprocess", 1)
    elif key in ("-f", "--field"):
        task_set_option("field", value)
    elif key in ("-p", "--pattern"):
        task_set_option("pattern", value)
    elif key in ("-m", "--matching"):
        task_set_option("matching", value)
    elif key in ("-o", "--format"):
        input_formats = value.split(',')
        # check the validity of the given output formats
        invalid_format = check_validity_input_formats(input_formats)
        if invalid_format:
            try:
                raise Exception('Invalid output format.')
            except Exception:  # pylint: disable-msg=W0703
                from invenio.ext.logging import register_exception
                register_exception(
                    prefix="The given output format '%s' is not available or "
                           "is invalid. Please try again" %
                           (invalid_format, ), alert_admin=True)
                return
        else:  # every given format is available
            task_set_option("format", value)
    elif key in ("-i", "--id"):
        task_set_option("recids", value)
    else:
        return False
    return True


### okay, here we go:
if __name__ == '__main__':
    main()
