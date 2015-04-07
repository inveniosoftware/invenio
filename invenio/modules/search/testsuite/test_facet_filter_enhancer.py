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

"""Test facet filter enhancer."""

from __future__ import unicode_literals

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite

from invenio_query_parser.ast import (
    AndOp, DoubleQuotedValue, EmptyQuery, Keyword, KeywordOp, NotOp, OrOp
)


class TestFacetFilterEnhancer(InvenioTestCase):

    def test_grouped_facets(self):
        from invenio.modules.search.enhancers.facet_filter import \
            get_groupped_facets
        facet_list = [['+', 'foo', 'bar'], ['+', 'foo', 'baz'],
                      ['-', 'bar', 'boo'], ['-', 'bar', 'bo']]

        grouped_facets = {
            '+': {
                'foo': ['bar', 'baz']
            },
            '-': {
                'bar': ['boo', 'bo']
            }
        }
        self.assertEqual(grouped_facets,
                         get_groupped_facets(facet_list))

    def test_format_tree_nodes(self):
        from invenio.modules.search.enhancers.facet_filter import \
            format_facet_tree_nodes
        grouped_facets = {
            '+': {
                'foo': ['bar', 'baz']
            },
            '-': {
                'bar': ['boo', 'bo']
            }
        }
        facet_kws = ['foo', 'bar']
        tree = format_facet_tree_nodes(EmptyQuery(''), grouped_facets,
                                       facet_kws)
        correct = AndOp(
            AndOp(
                EmptyQuery(''),
                OrOp(KeywordOp(Keyword('foo'), DoubleQuotedValue('bar')),
                     KeywordOp(Keyword('foo'), DoubleQuotedValue('baz')))
            ),
            NotOp(OrOp(
                KeywordOp(Keyword('bar'), DoubleQuotedValue('boo')),
                KeywordOp(Keyword('bar'), DoubleQuotedValue('bo')))
            )
        )
        self.assertEqual(correct, tree)

    def test_format_kw_not_in_list(self):
        from invenio.modules.search.enhancers.facet_filter import \
            format_facet_tree_nodes
        grouped_facets = {
            '+': {
                'foo': ['bar', 'baz']
            },
            '-': {
                'bar': ['boo', 'bo']
            }
        }
        facet_kws = ['foo']
        tree = format_facet_tree_nodes(EmptyQuery(''), grouped_facets,
                                       facet_kws)
        correct = AndOp(
            EmptyQuery(''),
            OrOp(KeywordOp(Keyword('foo'), DoubleQuotedValue('bar')),
                 KeywordOp(Keyword('foo'), DoubleQuotedValue('baz')))
        )
        self.assertEqual(correct, tree)

    def test_missing_part(self):
        from invenio.modules.search.enhancers.facet_filter import \
            format_facet_tree_nodes
        grouped_facets = {'-': {'bar': ['boo', 'bo']}}
        facet_kws = ['bar']
        tree = format_facet_tree_nodes(EmptyQuery(''), grouped_facets,
                                       facet_kws)
        correct = AndOp(
            EmptyQuery(''),
            NotOp(OrOp(KeywordOp(Keyword('bar'), DoubleQuotedValue('boo')),
                       KeywordOp(Keyword('bar'), DoubleQuotedValue('bo')))))
        self.assertEqual(correct, tree)

    def test_none(self):
        from invenio.modules.search.enhancers.facet_filter import \
            format_facet_tree_nodes
        self.assertEqual(format_facet_tree_nodes(None, {}, None), None)

TEST_SUITE = make_test_suite(TestFacetFilterEnhancer)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
