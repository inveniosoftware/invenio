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

from invenio.base.globals import cfg
from invenio_query_parser.ast import (
    AndOp, KeywordOp, OrOp,
    NotOp, Keyword, Value,
    SingleQuotedValue,
    DoubleQuotedValue,
    RegexValue, RangeOp,
    ValueQuery, EmptyQuery,
    GreaterOp, GreaterEqualOp,
    LowerOp, LowerEqualOp
)

from invenio_query_parser.visitor import make_visitor


class ElasticSearchDSL(object):

    """Implement visitor to create Elastic Search DSL."""

    visitor = make_visitor()

    # pylint: disable=W0613,E0102

    def __init__(self):
        """Provide a dictinary mapping invenio keywords
        to elasticsearch fields as a list
        eg. {"author": ["author.last_name, author.first_name"]}
        """
        self.keyword_dict = cfg['SEARCH_ELASTIC_KEYWORD_MAPPING']

    def map_keyword_to_fields(self, keyword):
        """Convert keyword to keyword list for searches
           Map keyword to elasticsearch fields if needed
        """
        if self.keyword_dict:
            res = self.keyword_dict.get(keyword)
            return res if res else [str(keyword)]
        return [str(keyword)]

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
        return op(['_all'])

    @visitor(Keyword)
    def visit(self, node):
        return self.map_keyword_to_fields(node.value)

    @visitor(Value)
    def visit(self, node):
        return lambda keyword: {
            'multi_match': {
                'query': node.value,
                'fields': keyword
            }
        }

    @visitor(SingleQuotedValue)
    def visit(self, node):
        return lambda keyword: {
            'multi_match': {
                'query': node.value,
                'type': 'phrase',
                'fields': keyword
            }
        }

    @visitor(DoubleQuotedValue)
    def visit(self, node):
        def _f(keyword):
            if (len(keyword) > 1):
                return {"bool":
                        {"should": [{"term": {k: str(node.value)}}
                                    for k in keyword]}}
            else:
                return {'term': {keyword[0]: node.value}}
        return _f

    @visitor(RegexValue)
    def visit(self, node):
        def _f(keyword):
            if len(keyword) > 1:
                res = {"bool": {"should": []}}
                res["bool"]["should"] = [{'regexp': {k: node.value}}
                                         for k in keyword]
            elif keyword[0] != "_all":
                res = {'regexp': {keyword[0]: node.value}}
            else:
                raise RuntimeError("Not supported regex search for all fields")
            return res
        return _f

    @visitor(RangeOp)
    def visit(self, node, left, right):
        condition = {}
        if left:
            condition['gte'] = left(None)["multi_match"]["query"]
        if right:
            condition['lte'] = right(None)["multi_match"]["query"]

        def _f(keyword):
            if len(keyword) > 1:
                res = {"bool": {"should": []}}
                res["bool"]["should"] = [{'range': {k: condition}}
                                         for k in keyword]
            else:
                res = {'range': {keyword[0]: condition}}
            return res
        return _f

    @visitor(EmptyQuery)
    def visit(self, node):
        return {
            "match_all": {}
        }

    @staticmethod
    def _operators(node, condition):
        def _f(keyword):
            if len(keyword) > 1:
                res = {"bool": {"should": []}}
                res["bool"]["should"] = [{'range': {k: condition}}
                                         for k in keyword]
            else:
                res = {'range': {keyword[0]: condition}}
            return res
        return _f

    @visitor(GreaterOp)
    def visit(self, node, value_fn):
        condition = {"gt": value_fn(None)["multi_match"]["query"]}
        return self._operators(node, condition)

    @visitor(LowerOp)
    def visit(self, node, value_fn):
        condition = {"lt": value_fn(None)["multi_match"]["query"]}
        return self._operators(node, condition)

    @visitor(GreaterEqualOp)
    def visit(self, node, value_fn):
        condition = {"gte": value_fn(None)["multi_match"]["query"]}
        return self._operators(node, condition)

    @visitor(LowerEqualOp)
    def visit(self, node, value_fn):
        condition = {"lte": value_fn(None)["multi_match"]["query"]}
        return self._operators(node, condition)
    # pylint: enable=W0612,E0102
