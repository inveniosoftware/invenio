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
import six

from flask_login import current_user
from flask import g
from werkzeug.utils import cached_property, import_string

from invenio.base.globals import cfg
from invenio.modules.search.cache import get_results_cache, set_results_cache

from .walkers.terms import Terms
from .walkers.match_unit import MatchUnit


def query_enhancers():
    functions = getattr(g, 'search_query_enhancers', None)
    if functions is None:
        functions = []
        for enhancer in cfg['SEARCH_QUERY_ENHANCERS']:
            if isinstance(enhancer, six.string_types):
                enhancer = import_string(enhancer)
                functions.append(enhancer)
        setattr(g, 'search_query_enhancers', functions)
    return functions

class SearchEngine(object):

    """Search engine implemetation."""

    def __init__(self, query):
        """Initialize with search query."""
        self._query = query

    @cached_property
    def parser(self):
        query_parser = cfg['SEARCH_QUERY_PARSER']
        if isinstance(query_parser, six.string_types):
            query_parser = import_string(query_parser)
        return query_parser

    @cached_property
    def query(self):
        """Parse query string using given grammar."""
        tree = pypeg2.parse(self._query, self.parser, whitespace="")
        for walker in cfg['SEARCH_QUERY_WALKERS']:
            if isinstance(walker, six.string_types):
                walker = import_string(walker)
            tree = tree.accept(walker())
        return tree

    def search(self, user_info=None, collection=None):
        """Search records."""
        user_info = user_info or current_user
        # Enhance query first
        query = self.query
        for enhancer in query_enhancers():
                query = enhancer(query, user_info=user_info,
                                 collection=collection)

        from invenio.modules.search.walkers.search_unit import SearchUnit
        #results = get_results_cache(self._query, collection)
        results = None
        if results is None:
            results = query.accept(SearchUnit())
            # set_results_cache(results, self._query, collection)
        return results

    def match(self, record, user_info=None):
        """Return True if record match the query."""
        return self.query.accept(MatchUnit(record))

    def terms(self, keywords=None):
        """Return list of terms for given keywords in query pattern."""
        return self.query.accept(Terms(keywords=keywords))
