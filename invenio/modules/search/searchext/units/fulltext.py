# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Fulltext search unit."""

from flask import current_app
from intbitset import intbitset


def search_unit(query, f, m, wl=None):
    """Search in fulltext."""
    from invenio.legacy.search_engine import (
        search_unit_in_bibwords, search_pattern
    )
    from invenio.legacy.miscutil.solrutils_bibindex_searcher import (
        solr_get_bitset
    )
    from invenio.legacy.miscutil.xapianutils_bibindex_searcher import (
        xapian_get_bitset
    )
    from ...utils import get_idx_indexer

    def fix(p):
        if m and (m == 'a' or m == 'r'):  # phrase/regexp query
            if p.startswith('%') and p.endswith('%'):
                p = p[1:-1]  # fix for partial phrase
            p = '"' + p + '"'
        return p

    indexers = {
        'SOLR': solr_get_bitset,
        'XAPIAN': xapian_get_bitset,
    }
    indexer = get_idx_indexer('fulltext')
    if indexer in indexers and \
            current_app.config.get('CFG_{}_ENABLED'.format(indexer), False):
        try:
            indexers[indexer](fix(query), f, m)
        except:
            current_app.logger.exception("Fulltext search is broken.")
            return intbitset()
    elif m == 'a' or m == 'r':
        # FIXME: workaround for not having phrase index yet
        return search_pattern(p=query, f=f, m='w')
    # FIXME raise ContinueSearch(query, f, m, wl)
    return search_unit_in_bibwords(query, f, wl=wl)
