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
from werkzeug.utils import cached_property, import_string

from invenio.base.globals import cfg

from .walkers.terms import Terms
from .walkers.match_unit import MatchUnit


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
        from .searchext.engines.native import search
        return search(self, user_info=user_info, collection=collection)

    def match(self, record, user_info=None):
        """Return True if record match the query."""
        return self.query.accept(MatchUnit(record))

    def terms(self, keywords=None):
        """Return list of terms for given keywords in query pattern."""
        return self.query.accept(Terms(keywords=keywords))
