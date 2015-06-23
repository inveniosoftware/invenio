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


class SearchOp(object):

    """Store results in cache."""

    def __init__(self, query):
        """Define query that should be cached."""
        self.query = query

    def __repr__(self):
        """Object representation."""
        return "%s(%s)" % (self.__class__.__name__, repr(self.query))

    def accept(self, visitor):
        """Store intermediate results to the cache."""
        self.query = self.query.accept(visitor)
        return visitor.visit(self)


def apply(query, **kwargs):
    """Decorate query with a cache operator."""
    return SearchOp(query)
