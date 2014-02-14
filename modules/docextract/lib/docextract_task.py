# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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

"""Generic Framework for extracting metadata from records using bibsched"""

from datetime import datetime
from itertools import chain
from invenio.bibtask import task_get_option, write_message, \
                            task_sleep_now_if_required, \
                            task_update_progress
from invenio.dbquery import run_sql
from invenio.search_engine import get_collection_reclist


def task_run_core_wrapper(name, core_func, extra_vars=None, post_process=None):
    def fun():
        return task_run_core(name,
                             core_func,
                             extra_vars=extra_vars,
                             post_process=post_process)
    return fun


def fetch_last_updated(name):
    select_sql = """SELECT last_recid, last_updated FROM xtrJOB
                    WHERE name = %s LIMIT 1"""
    row = run_sql(select_sql, (name,))
    if not row:
        sql = """INSERT INTO xtrJOB (name, last_updated, last_recid)
                 VALUES (%s, '1970-01-01', 0)"""
        run_sql(sql, (name,))
        row = run_sql(select_sql, (name,))

    # Fallback in case we receive None instead of a valid date
    last_recid = row[0][0] or 0
    last_date = row[0][1] or datetime(year=1, month=1, day=1)

    return last_recid, last_date


def store_last_updated(recid, creation_date, name):
    if recid is not None:
        sql = "UPDATE xtrJOB SET last_recid = %s WHERE name=%s AND last_recid < %s"
        run_sql(sql, (recid, name, recid))
    if creation_date is not None:
        sql = """UPDATE xtrJOB SET last_updated = %s
                 WHERE name=%s AND last_updated < %s"""
        iso_date = creation_date.isoformat()
        run_sql(sql, (iso_date, name, iso_date))


def fetch_concerned_records(name):
    task_update_progress("Fetching record ids")

    dummy, last_date = fetch_last_updated(name)

    if task_get_option('new'):
        # Fetch all records inserted since last run
        sql = """SELECT `id_bibrec`, `cd` FROM `bibdocfsinfo`
                 INNER JOIN `bibrec_bibdoc`
                 ON `bibdocfsinfo`.`id_bibdoc` = `bibrec_bibdoc`.`id_bibdoc`
                 WHERE `cd` >= %s AND format IN ('.pdf', '.PDF', '.pdfa')
                 ORDER BY `cd`"""
        records = run_sql(sql, [last_date.isoformat()])
    else:
        given_recids = task_get_option('recids')
        for collection in task_get_option('collections'):
            given_recids.add(get_collection_reclist(collection))

        if given_recids:
            format_strings = ','.join(['%s'] * len(given_recids))
            records = run_sql("""SELECT `id`, NULL FROM `bibrec`
                                 WHERE `id` IN (%s)
                                 ORDER BY `id`""" % format_strings,
                              list(given_recids))
        else:
            records = []

    task_update_progress("Done fetching record ids")

    return records


def process_records(name, records, func, extra_vars):
    count = 1
    total = len(records)
    for recid, date in records:
        task_sleep_now_if_required(can_stop_too=True)
        msg = "Extracting for %s (%d/%d)" % (recid, count, total)
        task_update_progress(msg)
        write_message(msg)
        func(recid, **extra_vars)
        if date:
            store_last_updated(None, date, name)
        count += 1


def task_run_core(name, func, extra_vars=None, post_process=None):
    """Calls extract_references in refextract"""
    if task_get_option('task_specific_name'):
        name = "%s:%s" % (name, task_get_option('task_specific_name'))
    write_message("Starting %s" % name)

    if extra_vars is None:
        extra_vars = {}

    records = fetch_concerned_records(name)
    process_records(name, records, func, extra_vars)

    if post_process:
        post_process(**extra_vars)

    write_message("Complete")
    return True


def split_ids(value):
    """
    Split ids given in the command line
    Possible formats are:
    * 1
    * 1,2,3,4
    * 1-5,20,30,40
    Returns respectively
    * set([1])
    * set([1,2,3,4])
    * set([1,2,3,4,5,20,30,40])
    """
    def parse(el):
        el = el.strip()
        if not el:
            ret = []
        elif '-' in el:
            start, end = el.split('-', 1)
            ret = xrange(int(start), int(end) + 1)
        else:
            ret = [int(el)]
        return ret
    return chain(*(parse(c) for c in value.split(',') if c.strip()))
