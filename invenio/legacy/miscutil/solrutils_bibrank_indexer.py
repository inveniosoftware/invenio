# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2015 CERN.
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
Solr utilities.
"""


import time
from invenio.config import CFG_SOLR_URL
from invenio.legacy.bibsched.bibtask import write_message, task_get_option, task_update_progress, \
                            task_sleep_now_if_required
from invenio.legacy.dbquery import run_sql
from invenio.legacy.search_engine import record_exists
from invenio.legacy.bibdocfile.api import BibRecDocs
from invenio.legacy.miscutil.solrutils_bibindex_indexer import replace_invalid_solr_characters
from invenio.legacy.bibindex.engine import create_range_list
from invenio.ext.logging import register_exception
from invenio.legacy.bibrank.bridge_utils import get_tags, get_field_content_in_utf8


if CFG_SOLR_URL:
    import solr
    SOLR_CONNECTION = solr.SolrConnection(CFG_SOLR_URL) # pylint: disable=E1101


def solr_add_ranges(id_ranges):
    sub_range_length = task_get_option("flush")
    id_ranges_to_index = []
    for id_range in id_ranges:
        lower_recid = id_range[0]
        upper_recid = id_range[1]
        i_low = lower_recid
        while i_low <= upper_recid:
            i_up = min(i_low + sub_range_length - 1, upper_recid)
            id_ranges_to_index.append((i_low, i_up))
            i_low += sub_range_length

    tags_to_index = get_tags()
    # Indexes latest records first by reversing
    # This allows the ranker to return better results during long indexing
    # runs as the ranker cuts the hitset using latest records
    id_ranges_to_index.reverse()
    next_commit_counter = 0
    for id_range_to_index in id_ranges_to_index:
        lower_recid = id_range_to_index[0]
        upper_recid = id_range_to_index[1]
        status_msg = "Solr ranking indexer called for %s-%s" % (lower_recid, upper_recid)
        write_message(status_msg)
        task_update_progress(status_msg)
        next_commit_counter = solr_add_range(lower_recid, upper_recid, tags_to_index, next_commit_counter)

    solr_commit_if_necessary(next_commit_counter, final_commit=True)


def solr_commit_if_necessary(next_commit_counter, final_commit=False, recid=None):
    # Counter full or final commit if counter set
    if next_commit_counter == task_get_option("flush") - 1 or (final_commit and next_commit_counter > 0):
        recid_info = ''
        if recid:
            recid_info = ' for recid=%s' % recid
        status_msg = 'Solr ranking indexer COMMITTING' + recid_info
        write_message(status_msg)
        task_update_progress(status_msg)

        try:
            # Commits might cause an exception, most likely a
            # timeout while hitting a background merge
            # Changes will then be committed later by the
            # calling (periodical) task
            # Also, autocommits can be used in the solrconfig
            SOLR_CONNECTION.commit()
        except:
            register_exception(alert_admin=True)
        next_commit_counter = 0

        task_sleep_now_if_required(can_stop_too=True)
    else:
        next_commit_counter = next_commit_counter + 1
    return next_commit_counter


def solr_add_range(lower_recid, upper_recid, tags_to_index, next_commit_counter):
    """
    Adds the regarding field values of all records from the lower recid to the upper one to Solr.
    It preserves the fulltext information.
    """
    for recid in range(lower_recid, upper_recid + 1):
        if record_exists(recid):
            abstract        = get_field_content_in_utf8(recid, 'abstract', tags_to_index)
            author          = get_field_content_in_utf8(recid, 'author', tags_to_index)
            keyword         = get_field_content_in_utf8(recid, 'keyword', tags_to_index)
            title           = get_field_content_in_utf8(recid, 'title', tags_to_index)
            try:
                bibrecdocs  = BibRecDocs(recid)
                fulltext    = unicode(bibrecdocs.get_text(), 'utf-8')
            except:
                fulltext    = ''

            solr_add(recid, abstract, author, fulltext, keyword, title)
            next_commit_counter = solr_commit_if_necessary(next_commit_counter,recid=recid)

    return next_commit_counter


def solr_add(recid, abstract, author, fulltext, keyword, title):
    """
    Helper function that adds word similarity ranking relevant indexes to Solr.
    """
    try:
        SOLR_CONNECTION.add(id=recid,
                            abstract=replace_invalid_solr_characters(abstract),
                            author=replace_invalid_solr_characters(author),
                            fulltext=replace_invalid_solr_characters(fulltext),
                            keyword=replace_invalid_solr_characters(keyword),
                            title=replace_invalid_solr_characters(title))
    except:
        register_exception(alert_admin=True)


def word_similarity_solr(run):
    return word_index(run)


def get_recIDs_by_date(dates=""):
    """Returns recIDs modified between DATES[0] and DATES[1].
       If DATES is not set, then returns records modified since the last run of
       the ranking method.
    """
    if not dates:
        write_message("Using the last update time for the rank method")
        res = run_sql("""SELECT last_updated FROM "rnkMETHOD" WHERE name='wrd'""")

        if not res:
            return
        if not res[0][0]:
            dates = ("0000-00-00",'')
        else:
            dates = (res[0][0],'')

    if dates[1]:
        res = run_sql('SELECT id FROM bibrec WHERE modification_date >= %s AND modification_date <= %s ORDER BY id ASC', (dates[0], dates[1]))
    else:
        res = run_sql('SELECT id FROM bibrec WHERE modification_date >= %s ORDER BY id ASC', (dates[0],))

    return create_range_list([row[0] for row in res])


def word_index(run): # pylint: disable=W0613
    """
    Runs the indexing task.
    """
    # Explicitly set ids
    id_option = task_get_option("id")
    if len(id_option):
        solr_add_ranges([(id_elem[0], id_elem[1]) for id_elem in id_option])

    # Indexes modified ids since last run
    else:
        starting_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        id_ranges = get_recIDs_by_date()
        if id_ranges:
            solr_add_ranges([(id_range[0], id_range[1]) for id_range in id_ranges])
            run_sql("""UPDATE "rnkMETHOD" SET last_updated=%s WHERE name='wrd'""", (starting_time, ))
        else:
            write_message("No new records. Solr index is up to date")

    write_message("Solr ranking indexer completed")
