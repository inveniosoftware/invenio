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

"""Implement AST convertor to Elastic Search DSL."""

from invenio_query_parser.ast import (
    AndOp, KeywordOp, OrOp,
    NotOp, Keyword, Value,
    SingleQuotedValue,
    DoubleQuotedValue,
    RegexValue, RangeOp,
    ValueQuery, EmptyQuery
)
from invenio_query_parser.visitor import make_visitor


class ElasticSearchDSL(object):

    """Implement visitor to create Elastic Search DSL."""

    visitor = make_visitor()

    # pylint: disable=W0613,E0102

    @visitor(AndOp)
    def visit(self, node, left, right):
        return {'bool': {'must': [left, right]}}

    @visitor(OrOp)
    def visit(self, node, left, right):
        return {'bool': {'should': [left, right]}}

    @visitor(NotOp)
    def visit(self, node, op):
        return {'bool': {'must_not': [op]}}

    @visitor(KeywordOp)
    def visit(self, node, left, right):
        if callable(right):
            return right(left)
        raise RuntimeError("Not supported second level operation.")

    @visitor(ValueQuery)
    def visit(self, node, op):
        return op('_all')

    @visitor(Keyword)
    def visit(self, node):
        # FIXME add mapping
        return node.value

    @visitor(Value)
    def visit(self, node):
        return lambda keyword: {
            'multi_match': {
                'query': node.value,
                'fields': [keyword]
            }
        }

    @visitor(SingleQuotedValue)
    def visit(self, node):
        return lambda keyword: {
            'multi_match': {
                'query': node.value,
                'type': 'phrase',
                'fields': [keyword]
            }
        }

    @visitor(DoubleQuotedValue)
    def visit(self, node):
        return lambda keyword: {
            'term': {keyword: node.value}
        }

    @visitor(RegexValue)
    def visit(self, node):
        return lambda keyword: {
            'regexp': {keyword: node.value}
        }

    @visitor(RangeOp)
    def visit(self, node, left, right):
        condition = {}
        if left:
            condition['gte'] = left
        if right:
            condition['lte'] = right
        return lambda keyword: {
            'range': {keyword: condition}
        }

    @visitor(EmptyQuery)
    def visit(self, node):
        return {
            "match_all": {}
        }

    # pylint: enable=W0612,E0102
