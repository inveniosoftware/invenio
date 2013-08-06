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
Solr utilities.
"""


import time
from invenio.config import CFG_SOLR_URL
from invenio.bibtask import write_message, task_get_option, task_update_progress, \
                            task_sleep_now_if_required
from invenio.dbquery import run_sql
from invenio.search_engine import get_fieldvalues, record_exists
from invenio.bibdocfile import BibRecDocs
from invenio.bibrank_bridge_config import CFG_MARC_ABSTRACT, \
                                          CFG_MARC_AUTHOR_NAME, \
                                          CFG_MARC_ADDITIONAL_AUTHOR_NAME, \
                                          CFG_MARC_TITLE, \
                                          CFG_MARC_KEYWORD
from invenio.solrutils_bibindex_indexer import replace_invalid_solr_characters
from invenio.bibindex_engine import create_range_list
from invenio.errorlib import register_exception


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

    # Indexes latest records first by reversing
    # This allows the ranker to return better results during long indexing
    # runs as the ranker cuts the hitset using latest records
    id_ranges_to_index.reverse()
    for id_range_to_index in id_ranges_to_index:
        lower_recid = id_range_to_index[0]
        upper_recid = id_range_to_index[1]
        status_msg = "Solr ranking indexer called for %s-%s" % (lower_recid, upper_recid)
        write_message(status_msg)
        task_update_progress(status_msg)
        solr_add_range(lower_recid, upper_recid)


def solr_add_range(lower_recid, upper_recid):
    """
    Adds the regarding field values of all records from the lower recid to the upper one to Solr.
    It preserves the fulltext information.
    """
    for recid in range(lower_recid, upper_recid + 1):
        if record_exists(recid):
            try:
                abstract = unicode(get_fieldvalues(recid, CFG_MARC_ABSTRACT)[0], 'utf-8')
            except:
                abstract = ""
            try:
                first_author = get_fieldvalues(recid, CFG_MARC_AUTHOR_NAME)[0]
                additional_authors = reduce(lambda x, y: x + " " + y, get_fieldvalues(recid, CFG_MARC_ADDITIONAL_AUTHOR_NAME), '')
                author = unicode(first_author + " " + additional_authors, 'utf-8')
            except:
                author = ""
            try:
                bibrecdocs = BibRecDocs(recid)
                fulltext = unicode(bibrecdocs.get_text(), 'utf-8')
            except:
                fulltext = ""
            try:
                keyword = unicode(reduce(lambda x, y: x + " " + y, get_fieldvalues(recid, CFG_MARC_KEYWORD), ''), 'utf-8')
            except:
                keyword = ""
            try:
                title = unicode(get_fieldvalues(recid, CFG_MARC_TITLE)[0], 'utf-8')
            except:
                title = ""
            solr_add(recid, abstract, author, fulltext, keyword, title)

    SOLR_CONNECTION.commit()
    task_sleep_now_if_required(can_stop_too=True)


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
        res = run_sql('SELECT last_updated FROM rnkMETHOD WHERE name="wrd"')

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
            run_sql('UPDATE rnkMETHOD SET last_updated=%s WHERE name="wrd"', (starting_time, ))
        else:
            write_message("No new records. Solr index is up to date")

    write_message("Solr ranking indexer completed")
