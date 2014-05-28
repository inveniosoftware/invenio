# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

"""Affiliation related functions

This is called in bibauthorid and using BibAuthorId data generates a table with
the affiliations for each author appearing in a paper. This is used later in:
* BibEdit to propose affiliations for those authors that don't have one.
* Rabbit to use the affiliation to assign papers in a fast way.
"""

import json

from itertools import islice
from datetime import datetime
from itertools import chain

from invenio.intbitset import intbitset
from invenio.dbquery import run_sql
from invenio.bibtask import write_message, task_update_progress as bibtask_update_progress, task_sleep_now_if_required
from invenio.docextract_task import fetch_last_updated, store_last_updated
from invenio.docextract_record import get_record
from unidecode import unidecode


CHUNK_SIZE = 10000


class RecomputeException(Exception):
    pass

def recompute_affiliation(pid):
    author_recids = run_sql("""SELECT bibrec, name FROM aidPERSONIDPAPERS
                               WHERE personid = %s ORDER BY bibrec DESC""", [pid])
    for recid, name in author_recids:
        record = get_record(recid)
        for field in chain(record['100'], record['700']):
            try:
                if field['a'][0] == name and field['u']:
                    return {'aff': field['u'][0],
                            'last_recid': recid,
                            'last_occurence': get_creation_date(recid)}
            except IndexError, e:
                print 'WARNING: problem in recomputing affiliations for pid ', pid
                raise RecomputeException(str(e))


def process_affiliations(record_ids=None, all_records=False):
    name = 'affiliations'

    if all_records:
        records = intbitset(run_sql("SELECT id FROM bibrec"))
        start_time = datetime.now()
    elif record_ids:
        records = intbitset(record_ids)
        start_time = None
    else:
        dummy_last_recid, last_updated = fetch_last_updated(name)
        start_time = datetime.now()
        sql = """SELECT `id` FROM `bibrec`
                 WHERE `modification_date` >= %s
                 AND `modification_date` <= %s
                 ORDER BY `modification_date`"""
        records = intbitset(run_sql(sql, [last_updated.isoformat(), start_time.isoformat()]))

    records_iter = iter(records)
    processed_records_count = 0
    while True:
        task_sleep_now_if_required()
        chunk = list(islice(records_iter, CHUNK_SIZE))
        if not chunk:
            break
        process_and_store(chunk)
        processed_records_count += len(chunk)
        task_update_progress('processed %s out of %s persons' % (processed_records_count, len(records)))
    if start_time:
        store_last_updated(None, start_time, name)


def task_update_progress(msg):
    bibtask_update_progress(msg)
    write_message(msg)


def get_personids(recid):
    pids_100_rows = run_sql("""SELECT personid, bib10x.value as name
                               FROM aidPERSONIDPAPERS INNER JOIN bib10x
                               ON aidPERSONIDPAPERS.bibref_value = bib10x.id
                               WHERE bibrec = %s and bibref_table = '100'""", [recid])
    pids_700_rows = run_sql("""SELECT personid, bib70x.value as name
                               FROM aidPERSONIDPAPERS INNER JOIN bib70x
                               ON aidPERSONIDPAPERS.bibref_value = bib70x.id
                               WHERE bibrec = %s and bibref_table = '700'""", [recid])
    pids = {}
    for personid, name in chain(pids_100_rows, pids_700_rows):
        pids[name.decode('utf-8')] = personid
    return pids


def get_creation_date(recid):
    return run_sql("SELECT creation_date FROM bibrec WHERE id = %s", [recid])[0][0]


def update_aff(pid, aff_info):
    run_sql("DELETE FROM aidAFFILIATIONS WHERE personid = %s", [pid])
    insert_aff(pid, aff_info)


def insert_aff(pid, aff_info):
    for affiliation in set(aff_info['aff']):
        run_sql("""INSERT IGNORE INTO aidAFFILIATIONS (personid, affiliation, last_recid, last_occurence)
                   VALUES (%s, %s, %s, %s)""", (pid,
                                                affiliation,
                                                aff_info['last_recid'],
                                                aff_info['last_occurence'].strftime("%Y-%m-%d %H:%M:%S")))


def process_chunk(recids):
    # Map for PID -> Affiliation info
    aff = {}

    for recid in recids:
        pids = get_personids(recid)
        record = get_record(recid)

        # Check for authors removed from papers
        missing_pids = intbitset(run_sql("SELECT personid FROM aidAFFILIATIONS WHERE last_recid = %s", [recid]))
        if pids:
            missing_pids -= intbitset(pids.values())
        for pid in missing_pids:
            try:
                recomputed_aff_info = recompute_affiliation(pid)
            except RecomputeException:
                continue
            if recomputed_aff_info:
                if pid not in aff or aff[pid]['last_occurence'] <= recomputed_aff_info['last_occurence']:
                    aff[pid] = recomputed_aff_info
            else:
                run_sql("DELETE FROM aidAFFILIATIONS WHERE personid = %s", [pid])

        if not pids:
            continue

        # Check for new affiliations
        for field in chain(record['100'], record['700']):
            if not field['a']:
                continue
            field_author = field['a'][0]
            field_aff = field['u']
            if field_aff:
                try:
                    pid = pids[field_author]
                except KeyError:
                    # Name stored by an older version of bibauthorid
                    pid = pids[unidecode(field_author)]
                record_date = get_creation_date(recid)
                if pid not in aff or aff[pid]['last_occurence'] <= record_date:
                    aff[pid] = {'aff': field_aff,
                                'last_recid': recid,
                                'last_occurence': record_date}

    return aff


def store_aff(cur_aff, aff):
    # Now we need to update aidAFFILIATIONS
    for pid, aff_info in aff.iteritems():
        cur_aff_info = cur_aff.get(pid, None)
        if aff_info != cur_aff_info:
            # write_message('Affiliation changed for %s, new info %s @ %s in %s' % (pid, aff_info['aff'], aff_info['last_occurence'].strftime("%Y-%m-%d %H:%M:%S"), aff_info['last_recid']))
            if cur_aff_info:
                update_aff(pid, aff_info)
            else:
                insert_aff(pid, aff_info)


def get_current_aff(pids):
    sql_placeholders = ','.join('%s' for dummy in pids)
    aff_rows = run_sql("""SELECT personid, affiliation, last_recid, last_occurence
                          FROM aidAFFILIATIONS
                          WHERE personid IN (%s)""" % sql_placeholders, pids)

    cur_aff = {}
    for personid, affiliation, last_recid, last_occurence in aff_rows:
        if personid in cur_aff:
            cur_el = cur_aff[personid]
            cur_el['aff'].append(affiliation)
            if cur_el['last_occurence'] <= last_occurence:
                cur_el['last_recid'] = last_recid
                cur_el['last_occurence'] = last_occurence
        else:
            cur_aff[personid] = {'aff': [affiliation],
                                 'last_recid': last_recid,
                                 'last_occurence': last_occurence}
    return cur_aff


def process_and_store(chunk):
    aff = process_chunk(chunk)
    if aff:
        cur_aff = get_current_aff(aff.keys())
        store_aff(cur_aff, aff)


if __name__ == '__main__':
    process_affiliations(all_records=True)
