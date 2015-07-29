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

import re
from collections import MutableMapping, MutableSequence

import six
from invenio_query_parser.ast import AndOp, DoubleQuotedValue, EmptyQuery, \
    Keyword, KeywordOp, NotOp, OrOp, RangeOp, RegexValue, SingleQuotedValue, \
    Value, ValueQuery
from invenio_query_parser.visitor import make_visitor

from invenio.utils.memoise import memoize


@memoize
def get_field_tags(field, tagtype="marc"):
    """Returns a list of tags for the field code 'field'.

    Example: field='author', output=['100__%','700__%'].
    """
    from invenio.modules.search.models import Field
    return list(Field.get_field_tags(field, tagtype=tagtype))


def match_unit(record, p, f=None, m='a', wl=None):
    """Match record to basic match unit."""
    if record is None:
        return p is None

    if f is not None:
        fields = (get_field_tags(f, 'nonmarc') + [f])
        for field in fields:
            if match_unit(record.get(field), p, f=None, m=m, wl=None):
                return True
        return False

    # compile search value only once for non exact search
    if m != 'e' and isinstance(p, six.string_types):
        p = re.compile(p)

    if isinstance(record, MutableSequence):
        return any([match_unit(field, p, f=f, m=m, wl=wl)
                    for field in record])
    elif isinstance(record, MutableMapping):
        return any([match_unit(field, p, f=f, m=m, wl=wl)
                    for field in record.values()])

    if m == 'e':
        return six.text_type(record) == p
    return p.search(six.text_type(record)) is not None


class MatchUnit(object):

    """Implement visitor using ``match_unit`` API."""

    visitor = make_visitor()

    def __init__(self, record):
        self.record = record

    # pylint: disable=W0613,E0102

    @visitor(AndOp)
    def visit(self, node, left, right):
        return left & right

    @visitor(OrOp)
    def visit(self, node, left, right):
        return left | right

    @visitor(NotOp)
    def visit(self, node, op):
        return not op

    @visitor(KeywordOp)
    def visit(self, node, left, right):
        if isinstance(right, bool):  # second level operator
            left.update(dict(p=right))
        else:
            left.update(right)
        return match_unit(self.record, **left)

    @visitor(ValueQuery)
    def visit(self, node, op):
        return match_unit(self.record, **op)

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
        return True

    # pylint: enable=W0612,E0102
