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

import json

from flask import request, flash
from invenio.base.i18n import _
from operator import itemgetter
from itertools import groupby
from six import iteritems

from invenio_query_parser.ast import (
        AndOp, OrOp, NotOp, KeywordOp, Keyword, Value
)

"""This enhancer enhancers the search query with the facet filters that are
send as part of the HTTP request.
"""


def kw_formatter(key, val):
    """Format the operation that is part or the bool expressions"""
    return KeywordOp(Keyword(key), Value(val))


def get_groupped_facets(filter_data):
    """Group facets based on keyword and operator

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


def format_facet_tree_nodes(facet_dict, facets, format_vals=kw_formatter):
    """Create the extra nodes to add to the AST
    If a facet_dict key is not in facets list, will not be taken into
    consideration

    :param facet_fict: the grouped facets dictionary
    :param facets: a list with the configured facet keys
    :return: the facet filter AST
    """
    # FIXME
    def _format_terms(key, vals):
        if key in facets:
            return reduce(OrOp, [format_vals(key, k) for k in vals])
        else:
            return None

    ret_val = None
    plus_iteritems = iteritems(facet_dict.get("+", {}))
    formatted_plus = [_format_terms(k, v) for k, v in plus_iteritems]
    formatted_plus = filter(None, formatted_plus)
    ret_val = reduce(AndOp, formatted_plus) if formatted_plus else None

    minus_iteritems = iteritems(facet_dict.get("-", {}))
    formatted_minus = [_format_terms(k, v) for k, v in minus_iteritems]
    formatted_minus = filter(None, formatted_minus)
    ret_val = reduce(lambda x, y: AndOp(NotOp(y), x) if x else NotOp(y),
                     formatted_minus, ret_val)

    return ret_val


def apply_facet_filters(search_obj, *args, **kwargs):
    """ Enhance the query AST with the facet filters
    First get the facet filter expression from the request values.
    Group the facets and create the new AST nodes to be added.
    Combine the new nodes with the initial query in an AndOp.
    """
    if 'filter' in request.values:
        from invenio.modules.search.facet_builders import \
            faceted_results_filter
        from invenio.modules.search.registry import facets
        try:
            filter_data = json.loads(request.values.get('filter', '[]'))
            out = get_groupped_facets(filter_data)
            new_nodes = format_facet_tree_nodes(out, facets)
            if new_nodes:
                ret_val = AndOp(search_obj.query, new_nodes)
            else:
                ret_val = search_obj.query
            return ret_val
        except Exception:
            flash(_('Invalid filter data'), 'error')
    return search_obj.query
