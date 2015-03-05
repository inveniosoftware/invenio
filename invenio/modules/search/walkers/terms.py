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
    AndOp, KeywordOp, OrOp,
    NotOp, Keyword, Value,
    SingleQuotedValue,
    DoubleQuotedValue,
    RegexValue, RangeOp,
    ValueQuery, EmptyQuery
)
from invenio_query_parser.visitor import make_visitor


class Terms(object):

    """Implement visitor to get all given terms."""

    visitor = make_visitor()

    def __init__(self, keywords=None):
        """Initialize list of keywords operators."""
        self.keywords = keywords

    # pylint: disable=W0613,E0102

    @visitor(AndOp)
    def visit(self, node, left, right):
        return left + right

    @visitor(OrOp)
    def visit(self, node, left, right):
        return left + right

    @visitor(NotOp)
    def visit(self, node, op):
        return []

    @visitor(KeywordOp)
    def visit(self, node, left, right):
        return right if left else []

    @visitor(ValueQuery)
    def visit(self, node, op):
        return map(lambda p: p.strip('%'), op)

    @visitor(Keyword)
    def visit(self, node):
        return self.keywords is None or node.value in self.keywords

    @visitor(Value)
    def visit(self, node):
        return [node.value.strip('%')]

    @visitor(SingleQuotedValue)
    def visit(self, node):
        return [node.value]

    @visitor(DoubleQuotedValue)
    def visit(self, node):
        return [node.value]

    @visitor(RegexValue)
    def visit(self, node):
        return [node.value]

    @visitor(RangeOp)
    def visit(self, node, left, right):
        return ["%s->%s" % (left, right)]

    @visitor(EmptyQuery)
    def visit(self, node):
        return []

    # pylint: enable=W0612,E0102
