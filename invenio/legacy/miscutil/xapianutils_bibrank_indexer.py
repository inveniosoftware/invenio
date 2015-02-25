# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011 CERN.
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
Xapian utilities.
"""


import os
from invenio.config import CFG_CACHEDIR, CFG_XAPIAN_ENABLED
from invenio.legacy.bibsched.bibtask import write_message, task_get_option
from invenio.legacy.dbquery import run_sql
from invenio.legacy.search_engine import get_fieldvalues
from invenio.legacy.miscutil.xapianutils_config import DATABASES, XAPIAN_DIR, XAPIAN_DIR_NAME, INDEXES
from invenio.legacy.bibdocfile.api import BibRecDocs
from invenio.legacy.bibrank.bridge_config import CFG_MARC_ABSTRACT, \
                                          CFG_MARC_AUTHOR_NAME, \
                                          CFG_MARC_ADDITIONAL_AUTHOR_NAME, \
                                          CFG_MARC_KEYWORD, \
                                          CFG_MARC_TITLE


if CFG_XAPIAN_ENABLED:
    import xapian


def xapian_ensure_db_dir(name):
    path = CFG_CACHEDIR + "/" + name
    if not os.path.exists(path):
        os.makedirs(path)


def xapian_add_all(lower_recid, upper_recid):
    """
    Adds the regarding field values of all records from the lower recid to the upper one to Xapian.
    It preserves the fulltext information.
    """
    xapian_init_databases()
    for recid in range(lower_recid, upper_recid + 1):
        try:
            abstract = unicode(get_fieldvalues(recid, CFG_MARC_ABSTRACT)[0], 'utf-8')
        except:
            abstract = ""
        xapian_add(recid, "abstract", abstract)

        try:
            first_author = get_fieldvalues(recid, CFG_MARC_AUTHOR_NAME)[0]
            additional_authors = reduce(lambda x, y: x + " " + y, get_fieldvalues(recid, CFG_MARC_ADDITIONAL_AUTHOR_NAME), '')
            author = unicode(first_author + " " + additional_authors, 'utf-8')
        except:
            author = ""
        xapian_add(recid, "author", author)

        try:
            bibrecdocs = BibRecDocs(recid)
            fulltext = unicode(bibrecdocs.get_text(), 'utf-8')
        except:
            fulltext = ""
        xapian_add(recid, "fulltext", fulltext)

        try:
            keyword = unicode(reduce(lambda x, y: x + " " + y, get_fieldvalues(recid, CFG_MARC_KEYWORD), ''), 'utf-8')
        except:
            keyword = ""
        xapian_add(recid, "keyword", keyword)

        try:
            title = unicode(get_fieldvalues(recid, CFG_MARC_TITLE)[0], 'utf-8')
        except:
            title = ""
        xapian_add(recid, "title", title)


def xapian_add(recid, field, value):
    """
    Helper function that adds word similarity ranking relevant indexes to Solr.
    """
    content_string = value
    doc = xapian.Document()
    doc.set_data(content_string)
    (database, indexer) = DATABASES[field]
    indexer.set_document(doc)
    indexer.index_text(content_string)
    database.replace_document(recid, doc)


def xapian_init_databases():
    """
    Initializes all database objects.
    """
    xapian_ensure_db_dir(XAPIAN_DIR_NAME)
    for field in INDEXES:
        xapian_ensure_db_dir(XAPIAN_DIR_NAME + "/" + field)
        database = xapian.WritableDatabase(XAPIAN_DIR + "/" + field, xapian.DB_CREATE_OR_OPEN)
        indexer = xapian.TermGenerator()
        stemmer = xapian.Stem("english")
        indexer.set_stemmer(stemmer)
        DATABASES[field] = (database, indexer)


def word_similarity_xapian(run):
    return word_index(run)


def word_index(run): # pylint: disable=W0613
    """
    Runs the indexing task.
    """
    id_option = task_get_option("id")
    if len(id_option):
        for id_elem in id_option:
            lower_recid= id_elem[0]
            upper_recid = id_elem[1]
            write_message("Xapian ranking indexer called for %s-%s" % (lower_recid, upper_recid))
            xapian_add_all(lower_recid, upper_recid)
            write_message("Xapian ranking indexer completed")

    else:
        max_recid = 0
        res = run_sql("SELECT max(id) FROM bibrec")
        if res and res[0][0]:
            max_recid = int(res[0][0])

        write_message("Xapian ranking indexer called for %s-%s" % (1, max_recid))
        xapian_add_all(1, max_recid)
        write_message("Xapian ranking indexer completed")
