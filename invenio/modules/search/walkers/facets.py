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

"""Implement AST vistor."""

from invenio_query_parser.ast import (
    AndOp,
    DoubleQuotedValue,
    EmptyQuery,
    Keyword,
    KeywordOp,
    NotOp,
    OrOp,
    RangeOp,
    RegexValue,
    SingleQuotedValue,
    Value,
    ValueQuery,
)

from invenio_query_parser.visitor import make_visitor


class FacetsVisitor(object):

    """Implement visitor to extract all facets filters."""

    visitor = make_visitor()

    @staticmethod
    def jsonable(parsedFacets):
        """Convert a visited query result to a structure which can be jsonified.

        :param parsedFacets: a visited query result.
        """
        result = {}
        # sets cannot be converted to json. We need to convert them to lists.
        for facet_name in parsedFacets:
            result[facet_name] = {
                'inc': list(parsedFacets[facet_name]['inc']),
                'exc': list(parsedFacets[facet_name]['exc']),
            }
        return result

    # pylint: disable=W0613,E0102,F999,D102

    def _merge_facets(self, left, right):
        """merge faceting for an AND or OR operator.

        :param left: left child node faceting
        :param right: right child node faceting
        """
        for k in right:
            if k in left:
                inc = left[k]['inc'].union(right[k]['inc'])
                exc = left[k]['exc'].union(right[k]['exc'])
                # Don't mark as included or excluded if only partially
                # included/excluded
                left[k] = {
                    'inc': inc.difference(exc),
                    'exc': exc.difference(inc),
                }
            else:
                left[k] = right[k]
        return left

    def _invert_facets(self, facets):
        """invert facet filters included <-> excluded.

        :param facets: facet filters
        """
        for k in facets:
            facets[k] = {
                'inc': facets[k]['exc'],
                'exc': facets[k]['inc'],
            }
        return facets

    @visitor(AndOp)
    def visit(self, node, left, right):
        return self._merge_facets(left, right)

    @visitor(OrOp)
    def visit(self, node, left, right):
        return self._merge_facets(left, right)

    @visitor(NotOp)
    def visit(self, node, op):
        return self._invert_facets(op)

    @visitor(KeywordOp)
    def visit(self, node, left, right):
        return {
            node.left.value: {
                'inc': set([node.right.value]),
                'exc': set()
            }
        }

    @visitor(ValueQuery)
    def visit(self, node, op):
        return {}

    @visitor(Keyword)
    def visit(self, node):
        return {}

    @visitor(Value)
    def visit(self, node):
        return {}

    @visitor(SingleQuotedValue)
    def visit(self, node):
        return {}

    @visitor(DoubleQuotedValue)
    def visit(self, node):
        return {}

    @visitor(RegexValue)
    def visit(self, node):
        return {}

    @visitor(RangeOp)
    def visit(self, node, left, right):
        return {}

    @visitor(EmptyQuery)
    def visit(self, node):
        return {}
    # pylint: enable=W0612,E0102,F999,D102
