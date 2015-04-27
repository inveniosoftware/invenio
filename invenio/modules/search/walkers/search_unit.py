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

from intbitset import intbitset

from invenio_query_parser.ast import (
    AndOp, DoubleQuotedValue, EmptyQuery,
    GreaterOp, Keyword,
    KeywordOp, NotOp, OrOp,
    RangeOp, RegexValue,
    SingleQuotedValue,
    Value, ValueQuery,
)
from invenio_query_parser.visitor import make_visitor

from ..searchext.engines.native import search_unit


class SearchUnit(object):

    """Implement visitor using ``search_unit`` API."""

    visitor = make_visitor()

    # pylint: disable=W0613,E0102

    @visitor(AndOp)
    def visit(self, node, left, right):
        return left & right

    @visitor(OrOp)
    def visit(self, node, left, right):
        return left | right

    @visitor(NotOp)
    def visit(self, node, op):
        return intbitset(trailing_bits=1) - op

    @visitor(KeywordOp)
    def visit(self, node, left, right):
        if isinstance(right, intbitset):  # second level operator
            left.update(dict(p=right))
        else:
            left.update(right)
        return search_unit(**left)

    @visitor(ValueQuery)
    def visit(self, node, op):
        return search_unit(**op)

    @visitor(GreaterOp)
    def visit(self, node, op):
        op["p"] = "{0}->".format(op["p"])
        return op

    @visitor(Keyword)
    def visit(self, node):
        return dict(f=node.value)

    @visitor(Value)
    def visit(self, node):
        return dict(p=node.value)

    @visitor(SingleQuotedValue)
    def visit(self, node):
        return dict(p=node.value, m='p')

    @visitor(DoubleQuotedValue)
    def visit(self, node):
        return dict(p=node.value, m='e')

    @visitor(RegexValue)
    def visit(self, node):
        return dict(p=node.value, m='r')

    @visitor(RangeOp)
    def visit(self, node, left, right):
        return dict(p="%s->%s" % (left, right))

    @visitor(EmptyQuery)
    def visit(self, node):
        return intbitset(trailing_bits=1)

    # pylint: enable=W0612,E0102
