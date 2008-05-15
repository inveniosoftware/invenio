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
from invenio.search_engine import perform_request_search
class TestSearchQueryParenthesisedParser(unittest.TestCase):
    """Test parenthesis parsing."""

    def test_parse_query(self):
        """parentheses parser - Test parsing of query with parenthesis"""
        parser = search_engine_query_parser.SearchQueryParenthesisedParser()

        # test if normal queries are parsed
        self.assertEqual(parser.parse_query('expr1'),
                         ['+', 'expr1'])

        self.assertEqual(parser.parse_query('(expr1)'),
                         ['+', 'expr1'])

        self.assertEqual(parser.parse_query("expr1 - (expr2)"),
                         ['+', 'expr1', '-', 'expr2'])

        self.assertEqual(parser.parse_query("+ expr1 - (expr2)"),
                         ['+', 'expr1', '-', 'expr2'])

        self.assertEqual(parser.parse_query("expr1 (expr2)"),
                         ['+', 'expr1', '+', 'expr2'])

        self.assertEqual(['+', 'expr1', '-', 'expr2'],
                         parser.parse_query("(expr1) - expr2"))

        self.assertEqual(parser.parse_query("(expr1)-(expr2)"),
                         ['+', 'expr1', '-', 'expr2'])

        self.assertEqual(parser.parse_query("-(expr1)-(expr2)"),
                         ['-', 'expr1', '-', 'expr2'])

        self.assertEqual(parser.parse_query('(expr1) - expr2 + (expr3) | expr4'),
                         ['+', 'expr1', '-', 'expr2', '+', 'expr3', '|', 'expr4'])

        self.assertEqual(parser.parse_query('(expr1) - expr2 + (expr3)'),
                         ['+', 'expr1', '-', 'expr2', '+', 'expr3'])

        self.assertEqual(parser.parse_query('(expr1) - expr2 + (expr3 | expr4) | "expr5 + expr6"'),
                         ['+', 'expr1', '-', 'expr2', '+', 'expr3 | expr4', '|', '"expr5 + expr6"'])

        # test parsing of queries with missing operators.
        # in this case default operator + should be included on place of the missing one
        self.assertEqual(parser.parse_query('(expr1) expr2 (expr3) | expr4'),
                         ['+', 'expr1', '+', 'expr2', '+', 'expr3', '|', 'expr4'])

    def test_parsing_of_nested_or_mismatched_parentheses(self):
        """parentheses parser - Test parsing of queries containing nested or mismatched parentheses"""

        parser = search_engine_query_parser.SearchQueryParenthesisedParser()

        # test nested parentheses - they are not supported
        self.failUnlessRaises(search_engine_query_parser.InvenioWebSearchQueryParserException,
                              parser.parse_query,"((expr))")
        # test mismatched parentheses
        self.failUnlessRaises(search_engine_query_parser.InvenioWebSearchQueryParserException,
                              parser.parse_query,"(expr")

    def test_parsing_of_and_or_and_not_operators(self):
        """parentheses parser - Test parsing of queries containing AND, OR, NOT operators"""

        parser = search_engine_query_parser.SearchQueryParenthesisedParser()

        self.assertEqual(parser.parse_query('(expr1) not expr2 and (expr3) or expr4'),
                         ['+', 'expr1', '-', 'expr2', '+', 'expr3', '|', 'expr4'])

        self.assertEqual(parser.parse_query('(expr1) not expr2 | "expressions not in and quotes | (are) not - parsed " - (expr3) or expr4'),
                         ['+', 'expr1', '-', 'expr2 | "expressions not in and quotes | (are) not - parsed "', '-', 'expr3', '|', 'expr4'])

        self.assertEqual(parser.parse_query('expr1 \\" expr2 and(expr3) not expr4 \\" and (expr5)'),
                         ['+', 'expr1 \\" expr2', '+', 'expr3', '-', 'expr4 \\"', '+', 'expr5'])

        self.assertEqual(parser.parse_query('(expr1 and expr2) or expr3'),
                         ['+', 'expr1 + expr2','|', 'expr3'])

        self.assertEqual(parser.parse_query('(expr1 and expr2) or expr3'),
                         parser.parse_query('(expr1 + expr2) | expr3'))

        self.assertEqual(parser.parse_query('(expr1 and expr2) or expr3'),
                         parser.parse_query('(expr1 + expr2) or expr3'))

    def test_parsing_of_quotes(self):
        """parentheses parser - Test parsing of queries containing single and double quotes"""

        parser = search_engine_query_parser.SearchQueryParenthesisedParser()

        #The content inside quotes should not be parsed

        # test double quotes
        self.assertEqual(parser.parse_query('(expr1) - expr2 | "expressions - in + quotes | (are) not - parsed " - (expr3) | expr4'),
                         ['+', 'expr1', '-', 'expr2 | "expressions - in + quotes | (are) not - parsed "', '-', 'expr3', '|', 'expr4'])
        # test single quotes
        self.assertEqual(parser.parse_query("(expr1) - expr2 | 'expressions - in + quotes | (are) not - parsed ' - (expr3) | expr4"),
                         ['+', 'expr1', '-', "expr2 | 'expressions - in + quotes | (are) not - parsed '", '-', 'expr3', '|', 'expr4'])

        # test escaping quotes
        # escaping single quotes
        self.assertEqual(parser.parse_query("expr1 \\' expr2 +(expr3) -expr4 \\' + (expr5)"),
                         ['+', "expr1 \\' expr2", '+', 'expr3', '-', "expr4 \\'", '+', 'expr5'])
        # escaping double quotes
        self.assertEqual(parser.parse_query('expr1 \\" expr2 +(expr3) -expr4 \\" + (expr5)'),
                         ['+', 'expr1 \\" expr2', '+', 'expr3', '-', 'expr4 \\"', '+', 'expr5'])

        # test parsing of quotes in the beginning of the query
        self.assertEqual(parser.parse_query('"expr1" - (expr2)'),
                         ['+', '"expr1"', '-', 'expr2'])
        self.assertEqual(parser.parse_query('-"expr1" - (expr2)'),
                         ['-', '"expr1"', '-', 'expr2'])



class TestSpiresToInvenioSyntaxConverter(unittest.TestCase):
    """Test parsing of SPIRES data---note these test cases are written against atlantis
    and use perform_request_search which then loads the parser
    """


    def _compare_searches(self, inv_search, spi_search):
        """Compare inv_search and spi_search for equivalence
        tests that a non-trivial result is found, that the hitsets are equal
        prints a message if both queries are parsed identically (a bonus...)
        """
        self.assert_(len(perform_request_search(p=spi_search))>0)
        self.assertEqual(perform_request_search(p=inv_search), \
                         perform_request_search(p=spi_search))


        #test operator searching
    def test_operators(self):
        """find a ellis and t colllisions
        """
        inv_search = "author:ellis and title:collisions"
        spi_search = "find a ellis and t collisions"
        self._compare_searches(inv_search, spi_search)

    def test_parens(self):
        """find a ellis and not t hadronic and not t collisions
        """
        inv_search = "author:ellis and not (title:hadronic or title:collisions)"
        spi_search = "find a ellis and not t hadronic and not t collisions "
        self._compare_searches(inv_search, spi_search)

    def test_author_simple(self):
        """find a ellis, j
        """
        inv_search = 'author:"ellis,j." or author:"ellis,j*"'
        spi_search = "find a ellis, j"
        self._compare_searches(inv_search, spi_search)

    def test_author_reverse(self):
        """ find a j ellis
        """
        inv_search = 'author"ellis, j" or author:"ellis,j*"'
        spi_search = "find a j ellis"
        self._compare_searches(inv_search, spi_search)

    def test_author_full_first(self):
        """ find a ellis, john
        """
        inv_search = "author:'ellis, john' or author:'ellis, j.' or author:'ellis, jo.'"
        spi_search = "find a ellis, john"
        self._compare_searches(inv_search, spi_search)

    def test_date(self):
        """ find date 1996
        """
        inv_search = "date:1996"
        spi_search = "find date 1996"
        self._compare_searches(inv_search, spi_search)

    def test_month(self):
        """find date 3/1996
        """
        inv_search = "date:'3/1996'"
        spi_search = "find date 3/1996"
        self._compare_searches(inv_search, spi_search)

TEST_SUITE = make_test_suite(TestSearchQueryParenthesisedParser, \
                             TestSpiresToInvenioSyntaxConverter)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

