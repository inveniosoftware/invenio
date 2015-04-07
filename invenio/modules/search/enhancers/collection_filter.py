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

"""Generate filter for retricted collections."""

from invenio.base.globals import cfg

from invenio_query_parser.ast import (
    AndOp, DoubleQuotedValue, Keyword, KeywordOp, NotOp, OrOp
)


def collection_formatter(value):
    """Format collection filter."""
    return KeywordOp(Keyword("collection"), DoubleQuotedValue(value))


def create_collection_query(restricted_cols, permitted_restricted_cols,
                            current_col, policy,
                            formatter=collection_formatter):
    """Create the new AST nodes that should be added to the search query.

    **Set definitions:**

    ``cc``
        current collection

    ``pr``
        permitted-restricted collections

    ``r``
        all restrincted collections

    ``r'``
        restricted collections for current user (``r' = r - pr``)

    **Policy ANY:**

        (cc AND NOT r') OR (cc and pr) -> cc AND (NOT r' OR rp)

    **Policy ALL:**

        cc AND NOT r'

    :param restricted_cols: all restricted collections
    :param permitted_restricted_cols: restricted collections that user can
                                      access
    :param current_col: name of the current collection
    :param policy: policy applied ('ANY' or enything else)
    :param format_val: a function used to format value of the boolean
                       operation
    """
    current_col_kw = formatter(current_col)
    result_tree = current_col_kw

    def union_terms(term_list):
        return reduce(OrOp, [formatter(k) for k in term_list])

    not_permitted_cols = (
        set(restricted_cols) - set(permitted_restricted_cols)
    )

    # only if not permitted collection exists
    if not_permitted_cols:
        result_tree = NotOp(union_terms(not_permitted_cols))

        if policy == 'ANY' and permitted_restricted_cols:
            # User needs to have access to at least one collection that
            # restricts the records. We need this to be able to remove records
            # that are both in a public and restricted collection.

            result_tree = OrOp(
                result_tree,
                union_terms(permitted_restricted_cols)
            )

        # intersect current collection with restrictions
        result_tree = AndOp(current_col_kw, result_tree)

    return result_tree


def apply(query, user_info=None, collection=None):
    """Enhance the query restricting not permitted collections.

    Get the permitted restricted collection for the current user from the
    user_info object and all the restriced collections from the
    restricted_collection_cache.
    """
    from invenio.modules.collections.cache import restricted_collection_cache

    policy = cfg['CFG_WEBSEARCH_VIEWRESTRCOLL_POLICY'].strip().upper()
    restricted_cols = restricted_collection_cache.cache
    permitted_restricted_cols = user_info.get(
        'precached_permitted_restricted_collections', [])
    current_col = collection or cfg['CFG_SITE_NAME']
    result_tree = create_collection_query(restricted_cols,
                                          permitted_restricted_cols,
                                          current_col, policy)
    return AndOp(query, result_tree)
