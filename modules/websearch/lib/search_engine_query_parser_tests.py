# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Unit tests for the search engine query parsers."""

__revision__ = \
    "$Id$"

import unittest

from invenio import search_engine_query_parser

from invenio.testutils import make_test_suite, run_test_suite

class TestSearchQueryParenthesisedParser(unittest.TestCase):
    """Test parenthesis parsing."""

    def test_parse_query(self):
        """parentheses parser - Test parsing of query with parenthesis"""
        parser = search_engine_query_parser.SearchQueryParenthesisedParser()

        # test if normal queries are parsed
        self.assertEqual(['+', 'op1'],
                         parser.parse_query('op1'))

        self.assertEqual(['+', 'op1'],
                         parser.parse_query('(op1)'))

        self.assertEqual(['+', 'op1', '-', 'op2'],
                         parser.parse_query("op1 - (op2)"))

        self.assertEqual(['+', 'op1', '-', 'op2'],
                         parser.parse_query("+ op1 - (op2)"))

        self.assertEqual(['+', 'op1', '+', 'op2'],
                         parser.parse_query("op1 (op2)"))

        self.assertEqual(['+', 'op1', '-', 'op2'],
                         parser.parse_query("(op1) - op2"))

        self.assertEqual(['+', 'op1', '-', 'op2'],
                         parser.parse_query("(op1)-(op2)"))

        self.assertEqual(['-', 'op1', '-', 'op2'],
                         parser.parse_query("-(op1)-(op2)"))

        self.assertEqual(['+', 'op1', '-', 'op2', '+', 'op3', '|', 'op4'],
                         parser.parse_query('(op1) - op2 + (op3) | op4'))

        self.assertEqual(['+', 'op1', '-', 'op2', '+', 'op3'],
                         parser.parse_query('(op1) - op2 + (op3)'))

        self.assertEqual(['+', 'op1', '-', 'op2', '+', 'op3 | op4', '|', '"op5 + op6"'],
                         parser.parse_query('(op1) - op2 + (op3 | op4) | "op5 + op6"'))

        # test parsing of queries with missing operators.
        # in this case default operator + should be included on place of the missing one
        self.assertEqual(['+', 'op1', '+', 'op2', '+', 'op3', '|', 'op4'],
                         parser.parse_query('(op1) op2 (op3) | op4'))

    def test_parsing_of_nested_or_mismatched_parentheses(self):
        """parentheses parser - Test parsing of queries containing nested or mismatched parentheses"""

        parser = search_engine_query_parser.SearchQueryParenthesisedParser()

        # test nested parentheses - they are not supported
        self.failUnlessRaises(search_engine_query_parser.InvenioWebSearchQueryParserException,
                              parser.parse_query,"((op))")
        # test mismatched parentheses
        self.failUnlessRaises(search_engine_query_parser.InvenioWebSearchQueryParserException,
                              parser.parse_query,"(op")

    def test_parsing_of_and_or_and_not_operators(self):
        """parentheses parser - Test parsing of queries containing AND, OR, AND NOT operators"""

        parser = search_engine_query_parser.SearchQueryParenthesisedParser()

        self.assertEqual(['+', 'op1', '-', 'op2', '+', 'op3', '|', 'op4'],
                         parser.parse_query('(op1) and not op2 and (op3) or op4'))

        self.assertEqual(['+', 'op1', '-', 'op2 | "expressions and not in and quotes | (are) not - parsed "', '-', 'op3', '|', 'op4'],
                         parser.parse_query('(op1) and not op2 | "expressions and not in and quotes | (are) not - parsed " - (op3) or op4'))

        self.assertEqual(['+', 'op1 \\" op2', '+', 'op3', '-', 'op4 \\"', '+', 'op5'],
                         parser.parse_query('op1 \\" op2 and(op3) and not op4 \\" and (op5)'))

    def test_parsing_of_quotes(self):
        """parentheses parser - Test parsing of queries containing single and double quotes"""

        parser = search_engine_query_parser.SearchQueryParenthesisedParser()

        #The content inside quotes should not be parsed

        # test double quotes
        self.assertEqual(['+', 'op1', '-', 'op2 | "expressions - in + quotes | (are) not - parsed "', '-', 'op3', '|', 'op4'],
                         parser.parse_query('(op1) - op2 | "expressions - in + quotes | (are) not - parsed " - (op3) | op4'))
        # test single quotes
        self.assertEqual(['+', 'op1', '-', "op2 | 'expressions - in + quotes | (are) not - parsed '", '-', 'op3', '|', 'op4'],
                         parser.parse_query("(op1) - op2 | 'expressions - in + quotes | (are) not - parsed ' - (op3) | op4"))

        # test escaping quotes
        # escaping single quotes
        self.assertEqual(['+', "op1 \\' op2", '+', 'op3', '-', "op4 \\'", '+', 'op5'],
                         parser.parse_query("op1 \\' op2 +(op3) -op4 \\' + (op5)"))
        # escaping double quotes
        self.assertEqual(['+', 'op1 \\" op2', '+', 'op3', '-', 'op4 \\"', '+', 'op5'],
                         parser.parse_query('op1 \\" op2 +(op3) -op4 \\" + (op5)'))

        # test parsing of quotes in the beginning of the query
        self.assertEqual(['+', '"expr1"', '-', 'expr2'],
                         parser.parse_query('"expr1" - (expr2)'))
        self.assertEqual(['-', '"expr1"', '-', 'expr2'],
                         parser.parse_query('-"expr1" - (expr2)'))



TEST_SUITE = make_test_suite(TestSearchQueryParenthesisedParser)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

