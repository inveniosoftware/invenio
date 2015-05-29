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

"""Search engine API."""

import pypeg2

from flask_login import current_user
from werkzeug.utils import cached_property

from .utils import parser, query_enhancers, query_walkers, search_walkers
from .walkers.match_unit import MatchUnit
from .walkers.terms import Terms


class Query(object):

    """Search engine implemetation.

    .. versionadded:: 2.1
       New search and match API.
    """

    def __init__(self, query):
        """Initialize with search query."""
        self._query = query

    @cached_property
    def query(self):
        """Parse query string using given grammar."""
        tree = pypeg2.parse(self._query, parser(), whitespace="")
        for walker in query_walkers():
            tree = tree.accept(walker)
        return tree

    def search(self, user_info=None, collection=None):
        """Search records."""
        user_info = user_info or current_user
        # Enhance query first
        query = self.query
        for enhancer in query_enhancers():
            query = enhancer(query, user_info=user_info,
                             collection=collection)

        for walker in search_walkers():
            query = query.accept(walker)
        return query

    def match(self, record, user_info=None):
        """Return True if record match the query."""
        return self.query.accept(MatchUnit(record))

    def terms(self, keywords=None):
        """Return list of terms for given keywords in query pattern."""
        return self.query.accept(Terms(keywords=keywords))
