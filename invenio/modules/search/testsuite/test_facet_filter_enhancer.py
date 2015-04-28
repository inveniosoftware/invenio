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

"""Tests for the facet filter enhancer"""

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase
from invenio_query_parser.ast import (
        AndOp, OrOp, NotOp, Keyword, KeywordOp, Value
)
from invenio.modules.search.enhancers.facet_filter import \
        get_groupped_facets, format_facet_tree_nodes, apply_facet_filters


class TestFacetFilterEnhancer(InvenioTestCase):

    def test_grouped_facets(self):
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
        grouped_facets = {
                '+': {
                    'foo': ['bar', 'baz']
                },
                '-': {
                    'bar': ['boo', 'bo']
                }
            }
        facet_kws = ['foo', 'bar']
        tree = format_facet_tree_nodes(grouped_facets, facet_kws)
        correct = AndOp(NotOp(OrOp(KeywordOp(Keyword('bar'), Value('boo')),
                              KeywordOp(Keyword('bar'), Value('bo')))),
                        OrOp(KeywordOp(Keyword('foo'), Value('bar')),
                             KeywordOp(Keyword('foo'), Value('baz'))))
        self.assertEqual(correct, tree)

    def test_format_kw_not_in_list(self):
        grouped_facets = {
                '+': {
                    'foo': ['bar', 'baz']
                },
                '-': {
                    'bar': ['boo', 'bo']
                }
            }
        facet_kws = ['foo']
        tree = format_facet_tree_nodes(grouped_facets, facet_kws)
        correct = OrOp(KeywordOp(Keyword('foo'), Value('bar')),
                       KeywordOp(Keyword('foo'), Value('baz')))
        self.assertEqual(correct, tree)

    def test_missing_part(self):
        grouped_facets = {
                '-': {
                    'bar': ['boo', 'bo']
                }
            }
        facet_kws = ['bar']
        tree = format_facet_tree_nodes(grouped_facets, facet_kws)
        correct = NotOp(OrOp(KeywordOp(Keyword('bar'), Value('boo')),
                             KeywordOp(Keyword('bar'), Value('bo'))))
        self.assertEqual(correct, tree)

    def test_none(self):
        self.assertEqual(format_facet_tree_nodes({}, None), None)

TEST_SUITE = make_test_suite(TestFacetFilterEnhancer)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
