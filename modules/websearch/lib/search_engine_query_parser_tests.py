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


import unittest

from invenio import search_engine_query_parser

from invenio.testutils import make_test_suite, run_test_suite
from invenio.search_engine import create_basic_search_units, perform_request_search


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
                         ['+', '+ expr1 | expr4', '+', '- expr2 | expr4', '+', '+ expr3 | expr4'])

    def test_sqpp_paren_expr1_minus_expr2_and_paren_expr3_or_expr4_or_quoted_expr5_and_expr6(self):
        """SearchQueryParenthesisedParser - (expr1) - expr2 + (expr3) | expr4 | \"expr5 + expr6\""""
        self.assertEqual(self.parser.parse_query('(expr1) - expr2 + (expr3 | expr4) | "expr5 + expr6"'),
                         ['+', '+ expr1 | "expr5 + expr6"', '+', '- expr2 | "expr5 + expr6"',
                          '+', '+ expr3 | expr4 | "expr5 + expr6"'])

    def test_sqpp_quoted_expr1_and_paren_expr2_and_expr3(self):
        """SearchQueryParenthesisedParser - \"expr1\" (expr2) expr3"""
        self.assertEqual(self.parser.parse_query('"expr1" (expr2) expr3'),
                         ['+', '"expr1"', '+', 'expr2', '+', 'expr3'])

    def test_sqpp_paren_expr1_expr2_paren_expr3_or_expr4(self):
        """SearchQueryParenthesisedParser - (expr1) expr2 (expr3) | expr4"""
        # test parsing of queries with missing operators.
        # in this case default operator + should be included on place of the missing one
        self.assertEqual(self.parser.parse_query('(expr1) expr2 (expr3) | expr4'),
                         ['+', '+ expr1 | expr4', '+', '+ expr2 | expr4', '+', '+ expr3 | expr4'])

    def test_sqpp_nested_paren_success(self):
        """SearchQueryParenthesizedParser: Arbitrarily nested parentheses: ((expr1)) + (expr2 - expr3)"""
        self.assertEqual(self.parser.parse_query('((expr1)) + (expr2 - expr3)'),
                         ['+', 'expr1', '+', 'expr2', '-', 'expr3'])

    def test_sqpp_nested_paren_really_nested(self):
        """SearchQueryParenthesisedParser: Nested parentheses where order matters: expr1 - ((expr2 - expr3) | expr4)"""
        self.assertEqual(self.parser.parse_query('expr1 - (expr2 - (expr3 | expr4))'),
                         ['+', 'expr1', '+', '- expr2 | expr3 | expr4'])

    def test_sqpp_paren_open_only_failure(self):
        """SearchQueryParenthesizedParser: Parentheses that only open should raise an exception"""
        self.failUnlessRaises(SyntaxError,
                              self.parser.parse_query,"(expr")
        #self.failUnlessRaises(search_engine_query_parser.InvenioWebSearchMismatchedParensError,
        #                      self.parser.parse_query,"(expr")

    def test_sqpp_paren_close_only_failure(self):
        """SearchQueryParenthesizedParser: Parentheses that only close should raise an exception"""
        self.failUnlessRaises(SyntaxError,
                              self.parser.parse_query,"expr)")
        #self.failUnlessRaises(search_engine_query_parser.InvenioWebSearchMismatchedParensError,
        #                      self.parser.parse_query,"expr)")

    def test_sqpp_paren_expr1_not_expr2_and_paren_expr3_or_expr4_WORDS(self):
        """SearchQueryParenthesisedParser - (expr1) not expr2 and (expr3) or expr4"""
        self.assertEqual(self.parser.parse_query('(expr1) not expr2 and (expr3) or expr4'),
                         ['+', '+ expr1 | expr4', '+', '- expr2 | expr4', '+', '+ expr3 | expr4'])

    def test_sqpp_paren_expr1_not_expr2_or_quoted_string_not_expr3_or_expr4WORDS(self):
        """SearchQueryParenthesisedParser - (expr1) not expr2 | "expressions not in and quotes | (are) not - parsed " - (expr3) or expr4"""
        self.assertEqual(self.parser.parse_query('(expr1) not expr2 | "expressions not in and quotes | (are) not - parsed " - (expr3) or expr4'),
                         ['+', '+ "expressions not in and quotes | (are) not - parsed " | expr1 | expr4',
                          '+', '- expr3 | expr1 | expr4',
                          '+', '+ "expressions not in and quotes | (are) not - parsed " - expr2 | expr4',
                          '+', '- expr3 - expr2 | expr4'])

    def test_sqpp_expr1_escaped_quoted_expr2_and_paren_expr3_not_expr4_WORDS(self):
        """SearchQueryParenthesisedParser - expr1 \\" expr2 foo(expr3) not expr4 \\" and (expr5)"""
        self.assertEqual(self.parser.parse_query('expr1 \\" expr2 foo(expr3) not expr4 \\" and (expr5)'),
                         ['+', 'expr1', '+', '\\"', '+', 'expr2', '+', 'foo(expr3)', '-', 'expr4', '+', '\\"', '+', 'expr5'])

    def test_sqpp_paren_expr1_and_expr2_or_expr3_WORDS(self):
        """SearchQueryParenthesisedParser - (expr1 and expr2) or expr3"""
        self.assertEqual(self.parser.parse_query('(expr1 and expr2) or expr3'),
                         ['+', '+ expr1 | expr3', '+', '+ expr2 | expr3'])

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
        self.assertEqual(self.parser.parse_query(
                           '(expr1) - expr2 | "expressions - in + quotes | (are) not - parsed " - (expr3) | expr4'),
                         ['+', '+ "expressions - in + quotes | (are) not - parsed " | expr1 | expr4',
                          '+', '- expr3 | expr1 | expr4',
                          '+', '+ "expressions - in + quotes | (are) not - parsed " - expr2 | expr4',
                          '+', '- expr3 - expr2 | expr4'])

    def test_sqpp_single_quotes(self):
        """SearchQueryParenthesisedParser - Test single quotes"""
        self.assertEqual(self.parser.parse_query("(expr1) - expr2 | 'expressions - in + quotes | (are) not - parsed ' - (expr3) | expr4"),
                         ['+', '+ \'expressions - in + quotes | (are) not - parsed \' | expr1 | expr4',
                          '+', '- expr3 | expr1 | expr4',
                          '+', '+ \'expressions - in + quotes | (are) not - parsed \' - expr2 | expr4',
                          '+', '- expr3 - expr2 | expr4'])

    def test_sqpp_escape_single_quotes(self):
        """SearchQueryParenthesisedParser - Test escaping single quotes"""
        self.assertEqual(self.parser.parse_query("expr1 \\' expr2 +(expr3) -expr4 \\' + (expr5)"),
                         ['+', 'expr1', '+', "\\'", '+', 'expr2', '+', 'expr3', '-', 'expr4', '+', "\\'", '+', 'expr5'])

    def test_sqpp_escape_double_quotes(self):
        """SearchQueryParenthesisedParser - Test escaping double quotes"""
        self.assertEqual(self.parser.parse_query('expr1 \\" expr2 +(expr3) -expr4 \\" + (expr5)'),
                         ['+', 'expr1', '+', '\\"', '+', 'expr2', '+', 'expr3', '-', 'expr4', '+', '\\"', '+', 'expr5'])

    def test_sqpp_beginning_double_quotes(self):
        """SearchQueryParenthesisedParser - Test parsing double quotes at beginning"""
        self.assertEqual(self.parser.parse_query('"expr1" - (expr2)'),
                         ['+', '"expr1"', '-', 'expr2'])

    def test_sqpp_beginning_double_quotes_negated(self):
        """SearchQueryParenthesisedParser - Test parsing negated double quotes at beginning"""
        self.assertEqual(self.parser.parse_query('-"expr1" - (expr2)'),
                         ['-', '"expr1"', '-', 'expr2'])

    def test_sqpp_long_or_chain(self):
        """SearchQueryParenthesisedParser - Test long or chains being parsed flat"""
        self.assertEqual(self.parser.parse_query('p0 or p1 or p2 or p3 or p4'),
                         ['+', 'p0', '|', 'p1', '|', 'p2', '|', 'p3', '|', 'p4'])

    def test_sqpp_not_after_recursion(self):
        """SearchQueryParenthesisedParser - Test operations after recursive calls"""
        self.assertEqual(self.parser.parse_query('(p0 or p1) not p2'),
                         ['+', '+ p0 | p1', '-', 'p2'])

    def test_sqpp_oddly_capped_operators(self):
        """SearchQueryParenthesisedParser - Test conjunctions in any case"""
        self.assertEqual(self.parser.parse_query('foo oR bar'),
                         ['+', 'foo', '|', 'bar'])

    def test_space_before_last_paren(self):
        """SearchQueryParenthesisedParser - Test (ellis )"""
        self.assertEqual(self.parser.parse_query('(ellis )'),
                         ['+', 'ellis'])

    def test_sqpp_nested_U1_or_SL2(self):
        """SearchQueryParenthesisedParser - Test (U(1) or SL(2,Z))"""
        self.assertEqual(self.parser.parse_query('(U(1) or SL(2,Z))'),
                         ['+', 'u(1)', '|', 'sl(2,z)'])

    def test_sqpp_distributed_ands_equivalent(self):
        """SearchQueryParenthesisedParser - ellis and (kaluza-klein or r-parity) == ellis and (r-parity or kaluza-klein)"""
        self.assertEqual(sorted(perform_request_search(p='ellis and (kaluza-klein or r-parity)')),
                         sorted(perform_request_search(p='ellis and (r-parity or kaluza-klein)')))


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

    def test_irn_processing(self):
        """SPIRES search syntax - find irn 1360337 == find irn SPIRES-1360337"""
        # Added for trac-130
        with_spires = "fin irn SPIRES-1360337"
        with_result = perform_request_search(p=with_spires)
        without_spires = "fin irn 1360337"
        without_result = perform_request_search(p=without_spires)
        # We don't care if results are [], as long as they're the same
        # Uncovered corner case: parsing could be broken and also happen to
        # return [] twice.  Unlikely though.
        self.assertEqual(with_result, without_result)

    def test_quotes(self):
        """SPIRES search syntax - find t 'compton scattering' and a mele"""
        inv_search = "title:'compton scattering' and author:mele"
        spi_search = "find t 'compton scattering' and a mele"
        self._compare_searches(inv_search, spi_search)

    def test_fin_to_find_trans(self):
        """SPIRES search syntax - fin a ellis, j == find a ellis, j"""
        fin_search = "fin a ellis, j"
        fin_result = perform_request_search(p=fin_search)
        find_search = "find a ellis, j"
        find_result = perform_request_search(p=find_search)
        # We don't care if results are [], as long as they're the same
        # Uncovered corner case: parsing could be broken and also happen to
        # return [] twice.  Unlikely though.
        self.assertEqual(fin_result, find_result)

    def test_distribution_of_notted_search_terms(self):
        """SPIRES search syntax - find t this and not that ->title:this and not title:that"""
        spi_search = "find t this and not that"
        inv_search = "title:this and not title:that"
        self._compare_searches(inv_search, spi_search)

    def test_distribution_without_spacing(self):
        """SPIRES search syntax - find t this and that ->title:this and title:that"""
        # motivated by trac-187
        spi_search = "find aff SLAC and Stanford"
        inv_search = "affiliation:SLAC and affiliation:Stanford"
        self._compare_searches(inv_search, spi_search)

    def test_keyword_as_kw(self):
        """SPIRES search syntax - find kw something ->keyword:something"""
        spi_search = "find kw meson"
        inv_search = "keyword:meson"
        self._compare_searches(inv_search, spi_search)

    def test_desy_keyword_translation(self):
        """SPIRES search syntax - find dk "B --> pi pi" """
        spi_search = "find dk \"B --> pi pi\""
        inv_search = "695__a:\"B --> pi pi\""
        self._compare_searches(inv_search, spi_search)

    def test_distribution_of_search_terms(self):
        """SPIRES search syntax - find t this and that ->title:this and title:that"""
        spi_search = "find t this and that"
        inv_search = "title:this and title:that"
        self._compare_searches(inv_search, spi_search)

    def test_syntax_converter_expand_search_patterns_alone(self):
        """SPIRES search syntax - simplest expansion"""
        spi_search = "find t bob sam"
        inv_search = "title:bob and title:sam"
        self._compare_searches(inv_search, spi_search)

    def test_syntax_converter_expand_search_patterns_conjoined(self):
        """SPIRES search syntax - simplest distribution"""
        spi_search = "find t bob and sam"
        inv_search = "title:bob and title:sam"
        self._compare_searches(inv_search, spi_search)

    def test_syntax_converter_expand_search_patterns_multiple(self):
        """SPIRES search syntax - expansion (no distribution)"""
        spi_search = "find t bob sam and k couch"
        inv_search = "title:bob and title:sam and keyword:couch"
        self._compare_searches(inv_search, spi_search)

    def test_syntax_converter_expand_search_patterns_multiple_conjoined(self):
        """SPIRES search syntax - distribution and expansion"""
        spi_search = "find t bob sam and couch"
        inv_search = "title:bob and title:sam and title:couch"
        self._compare_searches(inv_search, spi_search)


TEST_SUITE = make_test_suite(TestSearchQueryParenthesisedParser,
                             TestSpiresToInvenioSyntaxConverter)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
    #run_test_suite(make_test_suite(TestSearchQueryParenthesisedParser))
