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

def get_groupped_facets(filter_data, facets):
    """Group facets based on the facet configuration

    :param filter_data: the request filter parameter
    :param facets: the existing facets configuration
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

def format_facet_tree_nodes(facet_dict):
    """Create the extra nodes to add to the AST

    :param facet_fict: the grouped facets dictionary
    :param query: the query AST so far
    :return: the enhanced AST
    """
    def _format_terms(key, vals):
        if len(vals)>1:
            kw1 = KeywordOp(Keyword(key), Value(vals[0]))
            kw2 = KeywordOp(Keyword(k), Value(vals[1]))
            or_term = OrOp(kw1, kw2)
            l = vals[2:]
            for val in l:
                kw = KeywordOp(Keyword(key), Value(val))
                or_term = OrOp(or_term, kw)
            return or_term
        else:
            return KeywordOp(Keyword(key), Value(vals[0]))

    ret_val = None
    plus_iteritems = iteritems(facet_dict.get("+",{}))
    try:
        k, v = plus_iteritems.next()
        ret_val = _format_terms(k, v)
    except StopIteration:
        pass
    for k, v in plus_iteritems:
        ret_val = AndOp(_format_terms(k, v), ret_val)

    minus_iteritems = iteritems(facet_dict.get("-",{}))
    if not ret_val:
        try:
            k, v = minus_iteritems.next()
            ret_val = _format_terms(k, v)
        except StopIteration:
            pass
    for k, v in minus_iteritems:
        ret_val = AndOp(NotOp(_format_terms(k, v)), ret_val)

    return ret_val


def apply_facet_filters(search_obj, *args, filter_data=None, **kwargs):
    if 'filter' in request.values:
        from invenio.modules.search.facet_builders import \
            faceted_results_filter
        from invenio.modules.search.registry import facets
        try:
            if not filter_data:
                filter_data = json.loads(request.values.get('filter', '[]'))
            out = get_groupped_facets(filter_data, facets)
            new_nodes = format_facet_tree_nodes(out)
            if new_nodes:
                ret_val = AndOp(search_obj.query, new_nodes)
            else:
                ret_val = search_obj.query
            return ret_val
        except Exception:
            flash(_('Invalid filter data'), 'error')
    return search_obj.query
