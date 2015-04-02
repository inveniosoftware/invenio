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

"""Unit tests for the elasticsearch AST walker"""

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase
from invenio_query_parser.ast import (
    AndOp, KeywordOp, OrOp, NotOp, Keyword, Value, SingleQuotedValue,
    DoubleQuotedValue, ValueQuery, RegexValue, RangeOp, EmptyQuery,
    GreaterOp, GreaterEqualOp, LowerOp, LowerEqualOp
)

from invenio.modules.search.walkers.elasticsearch import ElasticSearchDSL


class TestElasticSearchWalker(InvenioTestCase):

    """Test transformations from the query-parser produced AST to the
       elasticsearch DSL query
    """

    def setUp(self):
        self.converter = ElasticSearchDSL()
        self.converter.keyword_dict = {"foo": ["test1", "test2"]}

    # Empty query
    def test_empty_query(self):
        self.assertEqual(EmptyQuery("").accept(self.converter), {
            "match_all": {
                }})

    # Value queries
    def test_value_query(self):
        self.assertEqual(ValueQuery(Value("bar")).accept(self.converter), {
            "multi_match": {
                "fields": ["_all"], "query": "bar"}
            })

    def test_single_quoted_value(self):
        tree = ValueQuery(SingleQuotedValue("bar"))
        self.assertEqual(tree.accept(self.converter), {
            "multi_match": {
                "fields": ["_all"],
                "query": "bar",
                "type": "phrase"
            }
        })

    def test_double_quoted_value(self):
        tree = ValueQuery(DoubleQuotedValue("bar"))
        self.assertEqual(tree.accept(self.converter), {
            "term": {"_all": "bar"}
        })

    def test_regex_value(self):
        # FIXME implement regex value for _all fields if needed
        tree = ValueQuery(RegexValue('^E.*s$'))
        self.assertRaises(RuntimeError, lambda: tree.accept(self.converter))

    # Key-value queries
    def test_key_val_query(self):
        tree = KeywordOp(Keyword('foo'), Value('bar'))
        self.assertEqual(tree.accept(self.converter), {
            "multi_match": {
                "fields": ["test1", "test2"],
                "query": "bar"
            }
        })

    def test_key_val_single_quote(self):
        tree = KeywordOp(Keyword('foo'), SingleQuotedValue('bar'))
        self.assertEqual(tree.accept(self.converter), {
            "multi_match": {
                "fields": ["test1", "test2"],
                "query": "bar",
                "type": "phrase"
            }
        })

    def test_key_val_double_quote(self):
        tree = KeywordOp(Keyword('foo'), DoubleQuotedValue('bar'))
        self.assertEqual(tree.accept(self.converter), {
            "bool": {
                "should": [
                    {"term": {"test1": "bar"}},
                    {"term": {"test2": "bar"}}]
            }
        })

    def test_range_op(self):
        tree = KeywordOp(Keyword('year'),
                         RangeOp(Value('2000'), Value('2012')))
        self.assertEqual(tree.accept(self.converter), {
            "range": {
                "year": {
                    "gte": "2000",
                    "lte": "2012",
                }
            }
        })

    def test_key_regex(self):
        tree = KeywordOp(Keyword('boo'), RegexValue('bar'))
        print tree.accept(self.converter)
        self.assertEqual(tree.accept(self.converter), {
            "regexp": {"boo": "bar"}
        })

    # Combined queries - boolean opeations
    def test_and_query(self):
        tree = AndOp(KeywordOp(Keyword('boo'), Value('bar')),
                     ValueQuery(Value('baz')))
        self.assertEqual(tree.accept(self.converter), {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "fields": ["boo"],
                            "query": "bar",
                        }
                    },
                    {
                        "multi_match": {
                            "fields": ["_all"],
                            "query": "baz",
                        }
                    }
                ]
            }
        })

    def test_or_query(self):
        tree = OrOp(KeywordOp(Keyword('boo'), Value('bar')),
                    ValueQuery(Value('baz')))
        self.assertEqual(tree.accept(self.converter), {
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "fields": ["boo"],
                            "query": "bar",
                        }
                    },
                    {
                        "multi_match": {
                            "fields": ["_all"],
                            "query": "baz",
                        }
                    }
                ]
            }
        })

    def test_not_query(self):
        tree = AndOp(KeywordOp(Keyword('boo'), Value('bar')),
                     NotOp(KeywordOp(Keyword('boo'), Value('bar'))))
        self.assertEqual(tree.accept(self.converter), {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "fields": ["boo"],
                            "query": "bar",
                        }
                    },
                    {
                        "bool": {
                            "must_not": [
                                {
                                    "multi_match": {
                                        "fields": ["boo"],
                                        "query": "bar",
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        })

    def test_combined_bool(self):
        tree = OrOp(AndOp(AndOp(ValueQuery(Value('aaa')),
                                ValueQuery(Value('bbb'))),
                          NotOp(ValueQuery(Value('ccc')))),
                    ValueQuery(Value('ddd')))
        ll = {
                "multi_match": {
                    "fields": ["_all"],
                    "query": "ddd"
                }
             }
        rr = {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "fields": ["_all"],
                                "query": "aaa"
                            }
                        },
                        {
                            "multi_match": {
                                "fields": ["_all"],
                                "query": "bbb"
                            }
                        }
                    ]
                }
             }
        rl = {
                "bool": {
                    "must_not": [
                        {
                            "multi_match": {
                                "fields": ["_all"],
                                "query": "ccc"
                            }
                        }
                    ]
                }
             }
        r = {
                "bool": {
                    "must": [rr, rl]
                }
            }
        d = {
                "bool": {
                    "should": [r, ll]
                }
            }
        self.assertEqual(tree.accept(self.converter), d)

    # Operators
    def test_greater_op(self):
        tree = KeywordOp(Keyword('date'), GreaterOp(Value('1984')))
        self.assertEqual(tree.accept(self.converter), {
            "range": {
                "date": {"gt": "1984"}
            }
        })

    def test_lower_op(self):
        tree = KeywordOp(Keyword('date'), LowerOp(Value('1984')))
        self.assertEqual(tree.accept(self.converter), {
            "range": {
                "date": {"lt": "1984"}
            }
        })

    def test_gte_op(self):
        tree = KeywordOp(Keyword('date'), GreaterEqualOp(Value('1984')))
        self.assertEqual(tree.accept(self.converter), {
            "range": {
                "date": {"gte": "1984"}
            }
        })

    def test_lte_op(self):
        tree = KeywordOp(Keyword('date'), LowerEqualOp(Value('1984')))
        self.assertEqual(tree.accept(self.converter), {
            "range": {
                "date": {"lte": "1984"}
            }
        })

TEST_SUITE = make_test_suite(TestElasticSearchWalker)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
