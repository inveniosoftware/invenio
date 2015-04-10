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

from invenio.base.globals import cfg
from invenio_query_parser.ast import (
        AndOp, OrOp, NotOp, KeywordOp, Keyword, Value
)

def kw_formatter(val):
    return KeywordOp(Keyword("collection"), Value(val))

def create_collection_query(restricted_cols, permitted_restricted_cols,
                            current_col, policy, format_vals=kw_formatter):
    """
    cc = current collection
    rp = permitted-restricted collections
    r = restrincted collections
    r' = r - rp

    Policy ANY:
    (cc AND NOT r') OR (cc and rp)

    Policy ELSE:
    cc AND NOT r'
    """

    r_prime = set(restricted_cols) - set(permitted_restricted_cols)

    r_prime_list = list(r_prime)
    r_prime_tree = None

    def _format_terms(term_list):
        if len(term_list) > 1:
            kw1 = format_vals(term_list[0])
            kw2 = format_vals(term_list[1])
            or_term = OrOp(kw1, kw2)
            for val in term_list[2:]:
                kw = format_vals(val)
                or_term = OrOp(or_term, kw)
            return or_term
        elif len(term_list) == 1:
            return term_list[0]
        else:
            return None

    r_prime = set(restricted_cols) - set(permitted_restricted_cols)
    r_prime_list = list(r_prime)
    r_prime_tree = _format_terms(r_prime_list)

    current_col_kw = format_vals(current_col)
    result_tree = AndOp(current_col_kw, NotOp(r_prime_tree)) if r_prime_tree \
        else current_col_kw

    if policy == 'ANY':
        # User needs to have access to at least one collection that restricts
        # the records. We need this to be able to remove records that are both
        # in a public and restricted collection.

        rp_tree = _format_terms(permitted_restricted_cols)
        right_tree = AndOp(current_col_kw, rp_tree) if rp_tree else \
            current_col_kw
        result_tree = OrOp(result_tree, right_tree) if right_tree \
            else result_tree

    return result_tree


def apply_collection_filters(search_obj, user_info=None, collection=None):

    from invenio.modules.collections.cache import restricted_collection_cache

    policy = cfg['CFG_WEBSEARCH_VIEWRESTRCOLL_POLICY'].strip().upper()
    restricted_cols = restricted_collection_cache.cache
    permitted_restricted_cols = user_info.get('precached_permitted_\
            restricted_collections', [])
    current_col = collection or cfg['CFG_SITE_NAME']
    collection_tree = create_collection_query(restricted_cols,
                                              permitted_restricted_cols,
                                              current_col, policy)
    return AndOp(search_obj.query, collection_tree)
