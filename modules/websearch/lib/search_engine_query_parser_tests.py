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

    def setUp(self):
        self.parser = search_engine_query_parser.SearchQueryParenthesisedParser()

    def test_sqpp_atom(self):
        """SearchQueryParenthesisedParser - expr1"""
        self.assertEqual(self.parser.parse_query('expr1'),
                         ['+', 'expr1'])

    def test_sqpp_parened_atom(self):
        """SearchQueryParenthesisedParser - (expr1)"""
        self.assertEqual(self.parser.parse_query('(expr1)'),
                         ['+', 'expr1'])

    def test_sqpp_expr1_minus_expr2(self):
        """SearchQueryParenthesisedParser - (expr1 - (expr2)"""
        self.assertEqual(self.parser.parse_query("expr1 - (expr2)"),
                         ['+', 'expr1', '-', 'expr2'])

    def test_sqpp_plus_expr1_minus_paren_expr2(self):
        """SearchQueryParenthesisedParser - + expr1 - (expr2)"""
        self.assertEqual(self.parser.parse_query("+ expr1 - (expr2)"),
                         ['+', 'expr1', '-', 'expr2'])

    def test_sqpp_expr1_paren_expr2(self):
        """SearchQueryParenthesisedParser - expr1 (expr2)"""
        self.assertEqual(self.parser.parse_query("expr1 (expr2)"),
                         ['+', 'expr1', '+', 'expr2'])

    def test_sqpp_paren_expr1_minus_expr2(self):
        """SearchQueryParenthesisedParser - (expr1) - expr2"""
        self.assertEqual(self.parser.parse_query("(expr1) - expr2"),
                         ['+', 'expr1', '-', 'expr2'])

    def test_sqpp_paren_expr1_minus_paren_expr2(self):
        """SearchQueryParenthesisedParser - (expr1)-(expr2)"""
        self.assertEqual(self.parser.parse_query("(expr1)-(expr2)"),
                         ['+', 'expr1', '-', 'expr2'])

    def test_sqpp_minus_paren_expr1_minus_paren_expr2(self):
        """SearchQueryParenthesisedParser - -(expr1)-(expr2)"""
        self.assertEqual(self.parser.parse_query("-(expr1)-(expr2)"),
                         ['-', 'expr1', '-', 'expr2'])

    def test_sqpp_paren_expr1_minus_expr2_and_paren_expr3(self):
        """SearchQueryParenthesisedParser - (expr1) - expr2 + (expr3)"""
        self.assertEqual(self.parser.parse_query('(expr1) - expr2 + (expr3)'),
                         ['+', 'expr1', '-', 'expr2', '+', 'expr3'])

    def test_sqpp_paren_expr1_minus_expr2_and_paren_expr3_or_expr4(self):
        """SearchQueryParenthesisedParser - (expr1) - expr2 + (expr3) | expr4"""
        self.assertEqual(self.parser.parse_query('(expr1) - expr2 + (expr3) | expr4'),
                         ['+', 'expr1', '-', 'expr2', '+', 'expr3', '|', 'expr4'])

    def test_sqpp_paren_expr1_minus_expr2_and_paren_expr3_or_expr4_or_quoted_expr5_and_expr6(self):
        """SearchQueryParenthesisedParser - (expr1) - expr2 + (expr3) | expr4 | \"expr5 + expr6\""""
        self.assertEqual(self.parser.parse_query('(expr1) - expr2 + (expr3 | expr4) | "expr5 + expr6"'),
                         ['+', 'expr1', '-', 'expr2', '+', 'expr3 | expr4', '|', '"expr5 + expr6"'])

    def test_sqpp_quoted_expr1_and_paren_expr2_and_expr3(self):
        """SearchQueryParenthesisedParser - \"expr1\" (expr2) expr3"""
        # test special cases - parentheses after quotas
        self.assertEqual(self.parser.parse_query('"expr1" (expr2) expr3'),
                         ['+', '"expr1"', '+', 'expr2', '+', 'expr3'])

    def test_sqpp_paren_expr1_expr2_paren_expr3_or_expr4(self):
        """SearchQueryParenthesisedParser - (expr1) expr2 (expr3) | expr4"""
        # test parsing of queries with missing operators.
        # in this case default operator + should be included on place of the missing one
        self.assertEqual(self.parser.parse_query('(expr1) expr2 (expr3) | expr4'),
                         ['+', 'expr1', '+', 'expr2', '+', 'expr3', '|', 'expr4'])

    def test_sqpp_nested_paren_failure(self):
        """SearchQueryParenthesisedParser - Nested parentheses should raise an exception"""
        # test nested parentheses - they are not supported (yet)
        self.failUnlessRaises(search_engine_query_parser.InvenioWebSearchQueryParserException,
                              self.parser.parse_query,"((expr))")

    def test_sqpp_paren_open_only_failure(self):
        """SearchQueryParenthesisedParser - Parentheses that only open should raise an exception"""
        self.failUnlessRaises(search_engine_query_parser.InvenioWebSearchQueryParserException,
                              self.parser.parse_query,"(expr")

    def test_sqpp_paren_close_only_failure(self):
        """SearchQueryParenthesisedParser - Parentheses that only close should raise an exception"""
        self.failUnlessRaises(search_engine_query_parser.InvenioWebSearchQueryParserException,
                              self.parser.parse_query,"expr)")

    def test_sqpp_paren_expr1_not_expr2_and_paren_expr3_or_expr4_WORDS(self):
        """SearchQueryParenthesisedParser - (expr1) not expr2 and (expr3) or expr4"""
        self.assertEqual(self.parser.parse_query('(expr1) not expr2 and (expr3) or expr4'),
                         ['+', 'expr1', '-', 'expr2', '+', 'expr3', '|', 'expr4'])

    def test_sqpp_paren_expr1_not_expr2_or_quoted_string_not_expr3_or_expr4WORDS(self):
        """SearchQueryParenthesisedParser - (expr1) not expr2 | "expressions not in and quotes | (are) not - parsed " - (expr3) or expr4"""
        self.assertEqual(self.parser.parse_query('(expr1) not expr2 | "expressions not in and quotes | (are) not - parsed " - (expr3) or expr4'),
                         ['+', 'expr1', '-', 'expr2 | "expressions not in and quotes | (are) not - parsed "', '-', 'expr3', '|', 'expr4'])

    def test_sqpp_expr1_escaped_quoted_expr2_and_paren_expr3_not_expr4_WORDS(self):
        """SearchQueryParenthesisedParser - expr1 \\" expr2 and(expr3) not expr4 \\" and (expr5)"""
        self.assertEqual(self.parser.parse_query('expr1 \\" expr2 and(expr3) not expr4 \\" and (expr5)'),
                         ['+', 'expr1 \\" expr2', '+', 'expr3', '-', 'expr4 \\"', '+', 'expr5'])

    def test_sqpp_paren_expr1_and_expr2_or_expr3_WORDS(self):
        """SearchQueryParenthesisedParser - (expr1 and expr2) or expr3"""
        self.assertEqual(self.parser.parse_query('(expr1 and expr2) or expr3'),
                         ['+', 'expr1 + expr2','|', 'expr3'])

    def test_sqpp_paren_expr1_and_expr2_or_expr3_WORDS_equiv(self):
        """SearchQueryParenthesisedParser - (expr1 and expr2) or expr3 == (expr1 + expr2) | expr3"""
        self.assertEqual(self.parser.parse_query('(expr1 and expr2) or expr3'),
                         self.parser.parse_query('(expr1 + expr2) | expr3'))

    def test_sqpp_paren_expr1_and_expr2_or_expr3_WORDS_equiv_SYMBOLS(self):
        """SearchQueryParenthesisedParser - (expr1 and expr2) or expr3 == (expr1 + expr2) or expr3"""
        self.assertEqual(self.parser.parse_query('(expr1 and expr2) or expr3'),
                         self.parser.parse_query('(expr1 + expr2) or expr3'))

    def test_sqpp_double_quotes(self):
        """SearchQueryParenthesisedParser - Test double quotes"""
        self.assertEqual(self.parser.parse_query('(expr1) - expr2 | "expressions - in + quotes | (are) not - parsed " - (expr3) | expr4'),
                         ['+', 'expr1', '-', 'expr2 | "expressions - in + quotes | (are) not - parsed "', '-', 'expr3', '|', 'expr4'])

    def test_sqpp_single_quotes(self):
        """SearchQueryParenthesisedParser - Test single quotes"""
        self.assertEqual(self.parser.parse_query("(expr1) - expr2 | 'expressions - in + quotes | (are) not - parsed ' - (expr3) | expr4"),
                         ['+', 'expr1', '-', "expr2 | 'expressions - in + quotes | (are) not - parsed '", '-', 'expr3', '|', 'expr4'])

    def test_sqpp_escape_single_quotes(self):
        """SearchQueryParenthesisedParser - Test escaping single quotes"""
        self.assertEqual(self.parser.parse_query("expr1 \\' expr2 +(expr3) -expr4 \\' + (expr5)"),
                         ['+', "expr1 \\' expr2", '+', 'expr3', '-', "expr4 \\'", '+', 'expr5'])

    def test_sqpp_escape_double_quotes(self):
        """SearchQueryParenthesisedParser - Test escaping double quotes"""
        self.assertEqual(self.parser.parse_query('expr1 \\" expr2 +(expr3) -expr4 \\" + (expr5)'),
                         ['+', 'expr1 \\" expr2', '+', 'expr3', '-', 'expr4 \\"', '+', 'expr5'])

    def test_sqpp_beginning_double_quotes(self):
        """SearchQueryParenthesisedParser - Test parsing double quotes at beginning"""
        self.assertEqual(self.parser.parse_query('"expr1" - (expr2)'),
                         ['+', '"expr1"', '-', 'expr2'])

    def test_sqpp_beginning_double_quotes_negated(self):
        """SearchQueryParenthesisedParser - Test parsing negated double quotes at beginning"""
        self.assertEqual(self.parser.parse_query('-"expr1" - (expr2)'),
                         ['-', '"expr1"', '-', 'expr2'])


class TestSpiresToInvenioSyntaxConverter(unittest.TestCase):
    """Test SPIRES query parsing and translation to Invenio syntax."""

    def _compare_searches(self, invenio_syntax, spires_syntax):
        """Determine if two queries parse to the same search command.

        For comparison of actual search results (regression testing), see the
        tests in the Inspire module.
        """
        parser = search_engine_query_parser.SearchQueryParenthesisedParser()
        converter = search_engine_query_parser.SpiresToInvenioSyntaxConverter()

        parsed_query = parser.parse_query(converter.convert_query(spires_syntax))
        #parse_query removes any parens that convert_query added, but then
        #we have to rejoin the list it returns and create basic searches

        result_obtained = create_basic_search_units(
            None,
            ' '.join(parsed_query).replace('+ ',''),
            '',
            None
            )

        # incase the desired result has parens
        parsed_wanted = parser.parse_query(invenio_syntax)
        result_wanted = create_basic_search_units(
            None,
            ' '.join(parsed_wanted).replace('+ ',''),
            '',
            None)



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

    def test_nots(self):
        """SPIRES search syntax - find a ellis and not t hadronic and not t collisions"""
        invenio_search = "author:ellis and not title:hadronic and not title:collisions"
        spires_search = "find a ellis and not t hadronic and not t collisions"
        self._compare_searches(invenio_search, spires_search)

    def test_author_simplest(self):
        """SPIRES search syntax - find a ellis"""
        invenio_search = 'author:ellis'
        spires_search = 'find a ellis'
        self._compare_searches(invenio_search, spires_search)

    def test_author_simple(self):
        """SPIRES search syntax - find a ellis, j"""
        invenio_search = 'author:"ellis, j*"'
        spires_search = 'find a ellis, j'
        self._compare_searches(invenio_search, spires_search)

    def test_exactauthor_simple(self):
        """SPIRES search syntax - find ea ellis, j"""
        invenio_search = 'exactauthor:"ellis, j"'
        spires_search = 'find ea ellis, j'
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

    def test_author_many_initials(self):
        """SPIRES search syntax - find a p d q bach"""
        inv_search = 'author:"bach, p* d* q*"'
        spi_search = 'find a p d q bach'
        self._compare_searches(inv_search, spi_search)

    def test_author_many_lastnames(self):
        """SPIRES search syntax - find a alvarez gaume, j r r"""
        inv_search = 'author:"alvarez gaume, j* r* r*"'
        spi_search = 'find a alvarez gaume, j r r'
        self._compare_searches(inv_search, spi_search)

    def test_author_full_initial(self):
        """SPIRES search syntax - find a klebanov, ig.r."""
        inv_search = 'author:"klebanov, ig* r*" or exactauthor:"klebanov, i r"'
        spi_search = "find a klebanov, ig.r."
        self._compare_searches(inv_search, spi_search)


    def test_author_full_first(self):
        """SPIRES search syntax - find a ellis, john"""
        invenio_search = 'author:"ellis, john*" or exactauthor:"ellis, j" or exactauthor:"ellis, jo" or exactauthor:"ellis, joh"'
        spires_search = 'find a ellis, john'
        self._compare_searches(invenio_search, spires_search)

    def test_combine_multiple(self):
        """SPIRES search syntax - find a gattringer, c and k symmetry chiral and not title chiral"""
        inv_search = 'author:"gattringer, c*" keyword:chiral  keyword:symmetry -title:chiral'
        spi_search = "find a c gattringer and k chiral symmetry and not title chiral"
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

    def test_distribution_of_search_terms(self):
        """ SPIRES search syntax - find t this and not that ->title:this and not title:that"""

        spi_search = "find t this and not that"
        inv_search = "title:this and not title:that"
        self._compare_searches(inv_search, spi_search)

TEST_SUITE = make_test_suite(TestSearchQueryParenthesisedParser, TestSpiresToInvenioSyntaxConverter)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

