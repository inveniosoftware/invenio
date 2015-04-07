# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Query results cacher."""

from invenio.modules.search.cache import get_results_cache, set_results_cache


class CacheOp(object):

    """Store results in cache."""

    def __init__(self, query, collection=None):
        """Define query that should be cached."""
        self.query = query
        self.collection = collection

    def __repr__(self):
        """Object representation."""
        return "%s(%s)" % (self.__class__.__name__, repr(self.query))

    def accept(self, visitor):
        """Store intermediate results to the cache."""
        results = get_results_cache(str(self.query), self.collection)
        if results is None:
            results = self.query.accept(visitor)
            set_results_cache(results, str(self.query), self.collection)
        return results


def apply(query, collection=None, **kwargs):
    """Decorate query with a cache operator."""
    return CacheOp(query, collection=collection)
