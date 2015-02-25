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


from invenio.config import CFG_XAPIAN_ENABLED
from intbitset import intbitset
from invenio.legacy.miscutil.xapianutils_config import XAPIAN_DIR


if CFG_XAPIAN_ENABLED:
    import xapian


DATABASES = dict()


def xapian_get_bitset(index, query):
    """
    Queries a Xapian index.
    Returns: an intbitset containing all record ids
    """
    if not DATABASES:
        xapian_init_databases()

    result = intbitset()

    database = DATABASES[index]
    enquire = xapian.Enquire(database)
    query_string = query
    qp = xapian.QueryParser()
    stemmer = xapian.Stem("english")
    qp.set_stemmer(stemmer)
    qp.set_database(database)
    qp.set_stemming_strategy(xapian.QueryParser.STEM_SOME)
    pattern = qp.parse_query(query_string, xapian.QueryParser.FLAG_PHRASE)
    enquire.set_query(pattern)
    matches = enquire.get_mset(0, database.get_lastdocid())

    for match in matches:
        result.add(match.docid)

    return result


def xapian_init_databases():
    """
    Initializes all database objects.
    """
    field = 'fulltext'
    database = xapian.Database(XAPIAN_DIR + "/" + field)
    DATABASES[field] = database
