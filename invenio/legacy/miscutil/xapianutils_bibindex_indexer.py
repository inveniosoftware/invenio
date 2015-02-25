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
from invenio.legacy.miscutil.xapianutils_config import XAPIAN_DIR, XAPIAN_DIR_NAME


if CFG_XAPIAN_ENABLED:
    import xapian


DATABASES = dict()


def xapian_ensure_db_dir(name):
    path = CFG_CACHEDIR + "/" + name
    if not os.path.exists(path):
        os.makedirs(path)


def xapian_add(recid, field, value):
    """
    Helper function that adds word similarity ranking relevant indexes to Solr.
    """
    # FIXME: remove as soon as the fulltext indexing is moved in BibIndex to the id_range part
    if not DATABASES:
        xapian_init_databases()

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
    field = 'fulltext'
    xapian_ensure_db_dir(XAPIAN_DIR_NAME + "/" + field)
    database = xapian.WritableDatabase(XAPIAN_DIR + "/" + field, xapian.DB_CREATE_OR_OPEN)
    indexer = xapian.TermGenerator()
    stemmer = xapian.Stem("english")
    indexer.set_stemmer(stemmer)
    DATABASES[field] = (database, indexer)
