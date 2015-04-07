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

"""Test policies on restricted and permitted collections."""

from invenio.modules.search.enhancers.collection_filter import \
    create_collection_query
from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite

from invenio_query_parser.ast import AndOp, NotOp, OrOp


class MockedRecord(object):

    _all_records = []

    def __init__(self, collections):
        """
        :param: collections: A list of the collections that the record belongs
        """
        self.collections = collections
        MockedRecord._all_records.append(self)

    def __str__(self):
        return str(self.collections)

    def belongsTo(self, collection):
        return collection in self.collections

    def belongs_to_c_expr(self, c_expr):
        """
        :param c_expr: A boolean invenio_query_parser expr
                                eg. AndOp("a", "b")
                                or a collection name
        """
        if type(c_expr) is str:
            return self.belongsTo(c_expr)

        class_name = c_expr.__class__.__name__
        if class_name == "AndOp":
            return self.belongs_to_c_expr(c_expr.right) and \
                self.belongs_to_c_expr(c_expr.left)
        elif class_name == "OrOp":
            return self.belongs_to_c_expr(c_expr.right) or \
                self.belongs_to_c_expr(c_expr.left)
        elif class_name == "NotOp":
            return not self.belongs_to_c_expr(c_expr.op)


class RecordsRegistry(object):

    """Keep track of all the records that are created."""

    def __init__(self):
        self.all_records = []

    def create_record(self, collections):
        r = MockedRecord(collections)
        self.all_records.append(r)
        return r

    def filter_collections(self, c_expr):
        return filter(lambda x: x.belongs_to_c_expr(c_expr), self.all_records)


def create_query(restricted_collections, permitted_restricted_collections,
                 current_col, policy):
    return create_collection_query(restricted_collections,
                                   permitted_restricted_collections,
                                   current_col, policy,
                                   formatter=lambda x: x)


def get_records_to_show(restricted_collections,
                        permitted_restricted_colls, current_col,
                        record_registry, policy):
    collection_query = create_query(restricted_collections,
                                    permitted_restricted_colls,
                                    current_col, policy)

    return record_registry.filter_collections(collection_query)


class TestCollectionsFilterEnhancher(InvenioTestCase):

    def setUp(self):

        self.record_reg = RecordsRegistry()
        self.r1 = self.record_reg.create_record(["a", "cc"])
        self.r2 = self.record_reg.create_record(["a", "b", "cc"])
        self.r3 = self.record_reg.create_record(["b", "cc"])
        self.r4 = self.record_reg.create_record(["b", "c", "cc"])
        self.r5 = self.record_reg.create_record(["c", "cc"])
        self.r6 = self.record_reg.create_record(["a", "cc"])
        self.r7 = self.record_reg.create_record(["a", "d", "cc"])
        self.r8 = self.record_reg.create_record(["d", "cc"])
        self.r9 = self.record_reg.create_record(["d", "c", "cc"])
        self.r10 = self.record_reg.create_record(["c", "cc"])
        self.r11 = self.record_reg.create_record(["cc"])

    def test_simple(self):
        self.assertEqual(self.record_reg.filter_collections("a"),
                         [self.r1, self.r2, self.r6, self.r7])

    def test_col_expr(self):
        """Test record filtering"""
        self.assertEqual(self.r1.belongs_to_c_expr("a"), True)
        self.assertEqual(self.r1.belongs_to_c_expr("b"), False)
        self.assertEqual(self.r1.belongs_to_c_expr(AndOp("a", "b")), False)
        self.assertEqual(self.r1.belongs_to_c_expr(OrOp("a", "b")), True)
        self.assertEqual(self.r1.belongs_to_c_expr(AndOp("d", OrOp("a", "b"))),
                         False)
        self.assertEqual(self.r1.belongs_to_c_expr(AndOp("a", NotOp("b"))),
                         True)

    def test_policy_else(self):
        self.assertEqual(get_records_to_show(["a", "b", "c", "d"], ["a"],
                                             "cc", self.record_reg, "ELSE"),
                         [self.r1, self.r6, self.r11])

    def test_policy_any(self):
        self.assertEqual(get_records_to_show(["a", "b", "c", "d"], ["a"],
                                             "cc", self.record_reg, "ANY"),
                         [self.r1, self.r2, self.r6, self.r7, self.r11])

    def test_none(self):
        self.assertEqual(create_query([], [], 'cc', 'ANY'), 'cc')

    def test_no_restrict(self):
        self.assertEqual(create_query(['a', 'b'], ['a', 'b'], 'cc', 'ANY'),
                         'cc')

TEST_SUITE = make_test_suite(TestCollectionsFilterEnhancher)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
