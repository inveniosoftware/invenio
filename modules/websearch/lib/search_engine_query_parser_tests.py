# -*- coding: utf-8 -*-
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
from invenio.search_engine import create_basic_search_units


class TestSearchQueryParenthesisedParser(unittest.TestCase):
    """Test parenthesis parsing."""

    def test_parse_query(self):
        """parenthesised search query parser - queries with parentheses"""
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
        # test special cases - parentheses after quotas
        self.assertEqual(parser.parse_query('"expr1" (expr2) expr3'),
                         ['+', '"expr1"', '+', 'expr2', '+', 'expr3'])
        # test parsing of queries with missing operators.
        # in this case default operator + should be included on place of the missing one
        self.assertEqual(parser.parse_query('(expr1) expr2 (expr3) | expr4'),
                         ['+', 'expr1', '+', 'expr2', '+', 'expr3', '|', 'expr4'])

    def test_parsing_of_nested_or_mismatched_parentheses(self):
        """parenthesised search query parser - queries containing nested or mismatched parentheses"""

        parser = search_engine_query_parser.SearchQueryParenthesisedParser()

        # test nested parentheses - they are not supported
        self.failUnlessRaises(search_engine_query_parser.InvenioWebSearchQueryParserException,
                              parser.parse_query,"((expr))")
        # test mismatched parentheses
        self.failUnlessRaises(search_engine_query_parser.InvenioWebSearchQueryParserException,
                              parser.parse_query,"(expr")

    def test_parsing_of_and_or_and_not_operators(self):
        """parenthesised search query parser - queries containing AND, OR, NOT operators"""

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
        """parenthesised search query parser - queries containing single and double quotes"""

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
    """Test SPIRES query parsing and translation to Invenio syntax."""

    def _compare_searches(self, invenio_syntax, spires_syntax):
        """Determine if two queries parse to the same search command.

        For comparison of actual search results (regression testing), see the
        tests in the Inspire module.
        """
        #parser = search_engine_query_parser.SearchQueryParenthesisedParser()
        converter = search_engine_query_parser.SpiresToInvenioSyntaxConverter()
        result_wanted = create_basic_search_units(None, invenio_syntax, '', None)

        #result_obtained = create_basic_search_units(None, parser.parse_query(converter.convert_query(spires_syntax)), '', None)
        result_obtained = create_basic_search_units(None, converter.convert_query(spires_syntax), '', None)
        #result_obtained = parser.parse_query(converter.convert_query(spires_syntax))
        #result_wanted = parser.parse_query(invenio_syntax)

        assert result_obtained == result_wanted, \
                                  """SPIRES parsed as %s instead of %s""" % \
                                  (repr(result_obtained), repr(result_wanted))
        return

        #test operator searching
    def test_operators(self):
        """SPIRES search syntax - find a ellis and t shapes"""
        invenio_search = "author:ellis and title:shapes"
        spires_search = "find a ellis and t shapes"
        self._compare_searches(invenio_search, spires_search)

    def test_parens(self):
        """SPIRES search syntax - find a ellis and not t hadronic and not t collisions"""
        invenio_search = "author:ellis and not (title:hadronic or title:collisions)"
        spires_search = "find a ellis and not t hadronic and not t collisions "
        self._compare_searches(invenio_search, spires_search)

    def test_author_simple(self):
        """SPIRES search syntax - find a ellis, j"""
        invenio_search = 'author:"ellis, j*"'
        spires_search = 'find a ellis, j'
        self._compare_searches(invenio_search, spires_search)

    def test_author_reverse(self):
        """SPIRES search syntax - find a j ellis"""
        invenio_search = 'author:"ellis, j*"'
        spires_search = 'find a j ellis'
        self._compare_searches(invenio_search, spires_search)

    def test_author_initials(self):
        """SPIRES search syntax - find a a m polyakov"""
        inv_search = 'author:"polyakov, a* m*"'
        spi_search = 'find a a m polyakov'
        self._compare_searches(inv_search, spi_search)

    def test_author_full_initial(self):
        """SPIRES search syntax - find a klebanov, igor r."""
        inv_search = 'author:"klebanov, igor* r*" or author:"klebanov, i.r." or author:"klebanov, ig.r."'
        spi_search = "find a klebanov, igor r."
        self._compare_searches(inv_search, spi_search)


    def test_author_full_first(self):
        """SPIRES search syntax - find a ellis, john"""
        invenio_search = 'author:"ellis, john" or author:"ellis, j.*" or author:"ellis, j" or author:"ellis, jo.*" or author:"ellis, jo" or author:"ellis, john *"'
        spires_search = 'find a ellis, john'
        self._compare_searches(invenio_search, spires_search)

    def test_combine_multiple(self):
        """SPIRES search syntax - find a gattringer, c and k symmetry chiral and not title chiral"""
        inv_search = "author:'gattringer, c*' keyword:chiral  keyword:symmetry -title:chiral "
        spi_search = "find a c gattringer and k symmetry chiral and not title chiral"
        self._compare_searches(inv_search, spi_search)

    def test_combine_multiple_or(self):
        """SPIRES search syntax - find a j ellis and (t report or k \"cross section\")"""
        inv_search = 'author:"ellis, j*" and (title:report or keyword:"cross section")'
        spi_search = 'find a j ellis and (t report or k "cross section")'
        self._compare_searches(inv_search, spi_search)

    def test_quotes(self):
        """SPIRES search syntax - find t 'compton scattering' and a mele"""
        inv_search = "title:'compton scattering' and author:mele"
        spi_search = "find t 'compton scattering' and a mele"
        self._compare_searches(inv_search, spi_search)

    def test_fin_to_find_trans(self):
        """SPIRES search syntax - fin a ellis, j == find a ellis, j"""
        from invenio.search_engine import perform_request_search
        fin_search = "fin a ellis, j"
        fin_result = perform_request_search(p=fin_search)
        find_search = "find a ellis, j"
        find_result = perform_request_search(p=find_search)
        # We don't care if results are [], as long as they're the same
        # Uncovered corner case: parsing could be broken and also happen to
        # return [] twice.  Unlikely though.
        self.assertEqual(fin_result, find_result)


TEST_SUITE = make_test_suite(TestSearchQueryParenthesisedParser, TestSpiresToInvenioSyntaxConverter)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

