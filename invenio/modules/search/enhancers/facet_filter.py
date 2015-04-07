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

"""Filter search results based on selected facets."""

import json

from itertools import groupby
from operator import itemgetter

from flask import request

from invenio.modules.search.registry import facets

from invenio_query_parser.ast import (
    AndOp, DoubleQuotedValue, Keyword, KeywordOp, NotOp, OrOp
)


def facet_formatter(key, val):
    """Format the operation that is part or the bool expressions."""
    return KeywordOp(Keyword(key), DoubleQuotedValue(val))


def get_groupped_facets(filter_data):
    """Group facets based on keyword and operator.

    :param filter_data: the request filter parameter
    :return: a dictionary with grouped facets
    """
    # Group filter data by operator and then by facet key.
    sortkeytype = itemgetter(0)
    sortfacet = itemgetter(1)
    data = sorted(filter_data, key=sortkeytype)
    out = {}
    for t, vs in groupby(data, key=sortkeytype):
        out[t] = {}
        for v, k in groupby(sorted(vs, key=sortfacet), key=sortfacet):
            out[t][v] = map(lambda i: i[2], k)
    return out


def format_facet_tree_nodes(query, filter_data, facets,
                            formatter=facet_formatter):
    """Add extra nodes to the AST.

    First get the facet filter expression from the request values.
    Group the facets and create the new AST nodes to be added.
    Combine the new nodes with the initial query in an AndOp.

    :param query: the original AST
    :param filter_data: the grouped facets dictionary
    :param facets: a list with the configured facet keys
    :return: the facet filter AST
    """
    # Intersect and diff records with selected facets.
    def union_facet_values(key, values):
        return reduce(OrOp, [formatter(key, value) for value in values])

    if '+' in filter_data:
        values = filter_data['+']
        for key in facets:
            if key in values:
                query = AndOp(query, union_facet_values(key, values[key]))

    if '-' in filter_data:
        values = filter_data['-']
        for key in facets:
            if key in values:
                query = AndOp(query, NotOp(
                    union_facet_values(key, values[key]))
                )

    return query


def apply(query, user_info=None, collection=None, **kwargs):
    """Enhance the query AST with the facet filters."""
    if 'filter' in request.values:
        if 'filter' in request.values:
            filter_data = get_groupped_facets(json.loads(
                request.values.get('filter', '[]')
            ))
            query = format_facet_tree_nodes(query, filter_data, facets)
    return query
