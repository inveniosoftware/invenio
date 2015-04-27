# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2010, 2011, 2012, 2013, 2014 CERN.
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

"""Unit tests for the search engine query parsers."""

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

search_engine_query_parser = lazy_import('invenio.legacy.search_engine.query_parser')
perform_request_search = lazy_import('invenio.legacy.search_engine:perform_request_search')


class TestParserUtilityFunctions(InvenioTestCase):
    """Test utility functions for the parsing components"""

    def setUp(self):
        self.parser = search_engine_query_parser.SearchQueryParenthesisedParser()
        self.converter = search_engine_query_parser.SpiresToInvenioSyntaxConverter()

    def test_ndb_simple(self):
        """SQPP.test_nesting_depth_and_balance: ['p0']"""
        self.assertEqual((0, True, 0),
                         self.parser.nesting_depth_and_balance(['p0']))

    def test_ndb_simple_useful(self):
        """SQPP.test_nesting_depth_and_balance: ['(', 'p0', ')']"""
        self.assertEqual((1, True, 1),
                         self.parser.nesting_depth_and_balance(['(', 'p0', ')']))

    def test_ndb_slightly_complicated(self):
        """SQPP.test_nesting_depth_and_balance: ['(', 'p0', ')', '|', '(', 'p2', '+', 'p3', ')']"""
        self.assertEqual((1, True, 2),
                         self.parser.nesting_depth_and_balance(['(', 'p0', ')', '|', '(', 'p2', '+', 'p3', ')']))

    def test_ndb_sorta_hairy(self):
        """SQPP.test_nesting_depth_and_balance: ['(', '(', ')', ')', '(', '(', '(', ')', ')', ')']"""
        self.assertEqual((3, True, 2),
                         self.parser.nesting_depth_and_balance(['(', '(', ')', ')', '(', '(', '(', ')', ')', ')']))

    def test_ndb_broken_rhs(self):
        """SQPP.test_nesting_depth_and_balance: ['(', '(', ')', ')', '(', '(', '(', ')', ')', ]"""
        self.assertEqual((3, False, 2),
                         self.parser.nesting_depth_and_balance(['(', '(', ')', ')', '(', '(', '(', ')', ')', ]))

    def test_ndb_broken_lhs(self):
        """SQPP.test_nesting_depth_and_balance: ['(', ')', ')', '(', '(', '(', ')', ')', ')']"""
        self.assertEqual((3, False, 2),
                         self.parser.nesting_depth_and_balance(['(', ')', ')', '(', '(', '(', ')', ')', ]))

    def test_stisc(self):
        """Test whole convert/parse stack: SQPP.parse_query(STISC.convert_query('find a richter, burton and t quark'))"""
        self.assertEqual(self.parser.parse_query(self.converter.convert_query('find a richter, burton and t quark')),
                         ['+',
                          'author:"richter, burton*" | exactauthor:"richter, b *" | exactauthor:"richter, b" | exactauthor:"richter, bu" | exactauthor:"richter, bur" | exactauthor:"richter, burt" | exactauthor:"richter, burto" | author:"richter, burton, *"',
                          '+', 'title:quark'])

    def test_stisc_not_vs_and_not1(self):
        """Parse stack parses "find a ellis, j and not a enqvist" == "find a ellis, j not a enqvist" """
        self.assertEqual(self.parser.parse_query(self.converter.convert_query('find a ellis, j and not a enqvist')),
                         self.parser.parse_query(self.converter.convert_query('find a ellis, j not a enqvist')))

    def test_stisc_not_vs_and_not2(self):
        """Parse stack parses "find a mangano, m and not a ellis, j" == "find a mangano, m not a ellis, j" """
        self.assertEqual(self.parser.parse_query(self.converter.convert_query('find a mangano, m and not a ellis, j')),
                         self.parser.parse_query(self.converter.convert_query('find a mangano, m not a ellis, j')))


class TestSearchQueryParenthesisedParser(InvenioTestCase):
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
        """SearchQueryParenthesisedParser - expr1 - (expr2)"""
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
                         #['+', '+ expr1 | expr4', '+', '- expr2 | expr4', '+', '+ expr3 | expr4'])

    def test_sqpp_paren_expr1_minus_expr2_and_paren_expr3_or_expr4_or_quoted_expr5_and_expr6(self):
        """SearchQueryParenthesisedParser - (expr1) - expr2 + (expr3) | expr4 | \"expr5 + expr6\""""
        self.assertEqual(self.parser.parse_query('(expr1) - expr2 + (expr3 | expr4) | "expr5 + expr6"'),
                         ['+', 'expr1', '-', 'expr2', '+', 'expr3 | expr4', '|', '"expr5 + expr6"']),
                         #['+', '+ expr1 | "expr5 + expr6"', '+', '- expr2 | "expr5 + expr6"',
                         # '+', '+ expr3 | expr4 | "expr5 + expr6"'])

    def test_sqpp_quoted_expr1_and_paren_expr2_and_expr3(self):
        """SearchQueryParenthesisedParser - \"expr1\" (expr2) expr3"""
        self.assertEqual(self.parser.parse_query('"expr1" (expr2) expr3'),
                         ['+', '"expr1"', '+', 'expr2', '+', 'expr3'])

    def test_sqpp_quoted_expr1_arrow_quoted_expr2(self):
        """SearchQueryParenthesisedParser = \"expr1\"->\"expr2\""""
        self.assertEqual(self.parser.parse_query('"expr1"->"expr2"'),
                         ['+', '"expr1"->"expr2"'])

    def test_sqpp_paren_expr1_expr2_paren_expr3_or_expr4(self):
        """SearchQueryParenthesisedParser - (expr1) expr2 (expr3) | expr4"""
        # test parsing of queries with missing operators.
        # in this case default operator + should be included on place of the missing one
        self.assertEqual(self.parser.parse_query('(expr1) expr2 (expr3) | expr4'),
                          ['+', 'expr1', '+', 'expr2', '+', 'expr3', '|', 'expr4'])
                         #['+', '+ expr1 | expr4', '+', '+ expr2 | expr4', '+', '+ expr3 | expr4'])

    def test_sqpp_nested_paren_success(self):
        """SearchQueryParenthesizedParser - Arbitrarily nested parentheses: ((expr1)) + (expr2 - expr3)"""
        self.assertEqual(self.parser.parse_query('((expr1)) + (expr2 - expr3)'),
                         ['+', 'expr1', '+', 'expr2', '-', 'expr3'])
                         #['+', 'expr1', '+', 'expr2', '-', 'expr3'])

    def test_sqpp_nested_paren_really_nested(self):
        """SearchQueryParenthesisedParser - Nested parentheses where order matters: expr1 - (expr2 - (expr3 | expr4))"""
        self.assertEqual(self.parser.parse_query('expr1 - (expr2 - (expr3 | expr4))'),
                         ['+', 'expr1', '+', '- expr2 | expr3 | expr4'])

    def test_sqpp_paren_open_only_failure(self):
        """SearchQueryParenthesizedParser - Parentheses that only open should raise an exception"""
        self.failUnlessRaises(SyntaxError,
                              self.parser.parse_query,"(expr")

    def test_sqpp_paren_close_only_failure(self):
        """SearchQueryParenthesizedParser - Parentheses that only close should raise an exception"""
        self.failUnlessRaises(SyntaxError,
                              self.parser.parse_query,"expr)")

    def test_sqpp_paren_expr1_not_expr2_and_paren_expr3_or_expr4_WORDS(self):
        """SearchQueryParenthesisedParser - (expr1) not expr2 and (expr3) or expr4"""
        self.assertEqual(self.parser.parse_query('(expr1) not expr2 and (expr3) or expr4'),
                         ['+', 'expr1', '-', 'expr2', '+', 'expr3', '|', 'expr4'])
                         #['+', '+ expr1 | expr4', '+', '- expr2 | expr4', '+', '+ expr3 | expr4'])

    def test_sqpp_paren_expr1_not_expr2_or_quoted_string_not_expr3_or_expr4WORDS(self):
        """SearchQueryParenthesisedParser - (expr1) not expr2 | "expressions not in and quotes | (are) not - parsed " - (expr3) or expr4"""
        self.assertEqual(self.parser.parse_query('(expr1) not expr2 | "expressions not in and quotes | (are) not - parsed " - (expr3) or expr4'),
                         ['+', 'expr1', '-', 'expr2', '|', '"expressions not in and quotes | (are) not - parsed "', '-', 'expr3', '|', 'expr4'])
                         #['+', '+ "expressions not in and quotes | (are) not - parsed " | expr1 | expr4',
                         # '+', '- expr3 | expr1 | expr4',
                         # '+', '+ "expressions not in and quotes | (are) not - parsed " - expr2 | expr4',
                         # '+', '- expr3 - expr2 | expr4'])

    def test_sqpp_expr1_escaped_quoted_expr2_and_paren_expr3_not_expr4_WORDS(self):
        """SearchQueryParenthesisedParser - expr1 \\" expr2 foo(expr3) not expr4 \\" and (expr5)"""
        self.assertEqual(self.parser.parse_query('expr1 \\" expr2 foo(expr3) not expr4 \\" and (expr5)'),
                         ['+', 'expr1', '+', '\\"', '+', 'expr2', '+', 'foo(expr3)', '-', 'expr4', '+', '\\"', '+', 'expr5'])

    def test_sqpp_paren_expr1_and_expr2_or_expr3_WORDS(self):
        """SearchQueryParenthesisedParser - (expr1 and expr2) or expr3"""
        self.assertEqual(self.parser.parse_query('(expr1 and expr2) or expr3'),
                                     ['+', 'expr1 + expr2', '|', 'expr3'])
                         #['+', '+ expr1 | expr3', '+', '+ expr2 | expr3'])

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
                          ['+', 'expr1', '-', 'expr2', '|', '"expressions - in + quotes | (are) not - parsed "', '-', 'expr3', '|', 'expr4'])
                         #['+', '+ "expressions - in + quotes | (are) not - parsed " | expr1 | expr4',
                         # '+', '- expr3 | expr1 | expr4',
                         # '+', '+ "expressions - in + quotes | (are) not - parsed " - expr2 | expr4',
                         # '+', '- expr3 - expr2 | expr4'])

    def test_sqpp_single_quotes(self):
        """SearchQueryParenthesisedParser - Test single quotes"""
        self.assertEqual(self.parser.parse_query("(expr1) - expr2 | 'expressions - in + quotes | (are) not - parsed ' - (expr3) | expr4"),
                         ['+', 'expr1', '-', 'expr2', '|', "'expressions - in + quotes | (are) not - parsed '", '-', 'expr3', '|', 'expr4'])
                         #['+', '+ \'expressions - in + quotes | (are) not - parsed \' | expr1 | expr4',
                         # '+', '- expr3 | expr1 | expr4',
                         # '+', '+ \'expressions - in + quotes | (are) not - parsed \' - expr2 | expr4',
                         # '+', '- expr3 - expr2 | expr4'])

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
                         ['+', 'p0 | p1', '-', 'p2'])
                         #['+', '+ p0 | p1', '-', 'p2'])

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
                         ['+', 'u(1) | sl(2,z)'])

    def test_sqpp_alternation_of_quote_marks_double(self):
        """SearchQueryParenthesisedParser - Test refersto:(author:"s parke" or author:ellis)"""
        self.assertEqual(self.parser.parse_query('refersto:(author:"s parke" or author:ellis)'),
                         ['+', 'refersto:\'author:"s parke" | author:ellis\''])

    def test_sqpp_alternation_of_quote_marks_single(self):
        """SearchQueryParenthesisedParser - Test refersto:(author:'s parke' or author:ellis)"""
        self.assertEqual(self.parser.parse_query('refersto:(author:\'s parke\' or author:ellis)'),
                         ['+', 'refersto:"author:\'s parke\' | author:ellis"'])

    def test_sqpp_alternation_of_quote_marks(self):
        """SearchQueryParenthesisedParser - Test refersto:(author:"s parke")"""
        self.assertEqual(self.parser.parse_query('refersto:(author:"s parke")'),
                         ['+', 'refersto:author:"s parke"'])

    def test_sqpp_distributed_ands_equivalent(self):
        """SearchQueryParenthesisedParser - ellis and (kaluza-klein or r-parity) == ellis and (r-parity or kaluza-klein)"""
        self.assertEqual(sorted(perform_request_search(p='ellis and (kaluza-klein or r-parity)')),
                         sorted(perform_request_search(p='ellis and (r-parity or kaluza-klein)')))

    def test_sqpp_e_plus_e_minus(self):
        """SearchQueryParenthesisedParser - e(+)e(-)"""
        self.assertEqual(self.parser.parse_query('e(+)e(-)'), ['+', 'e(+)e(-)'])

    def test_sqpp_fe_2_plus(self):
        """SearchQueryParenthesisedParser - Fe(2+)"""
        self.assertEqual(self.parser.parse_query('Fe(2+)'), ['+', 'fe(2+)'])

    def test_sqpp_giant_evil_title_string(self):
        """SearchQueryParenthesisedParser - Measurements of CP-conserving trilinear gauge boson couplings WWV (V gamma, Z) in e(+)e(-) collisions at LEP2"""
        self.assertEqual(self.parser.parse_query('Measurements of CP-conserving trilinear gauge boson couplings WWV (V gamma, Z) in e(+)e(-) collisions at LEP2'),
                         ['+', 'measurements', '+', 'of', '+', 'cp-conserving', '+', 'trilinear', '+', 'gauge', \
                          '+', 'boson', '+', 'couplings', '+', 'wwv', '+', 'v + gamma, + z', \
                          '+', 'in', '+', 'e(+)e(-)', '+', 'collisions', '+', 'at', '+', 'lep2'])

    def test_sqpp_second_order_operator_operates_on_parentheses(self):
        """SearchQueryParenthesisedParser - refersto:(author:ellis or author:hawking)"""
        self.assertEqual(self.parser.parse_query('refersto:(author:ellis or author:hawking)'),
                         ['+', 'refersto:"author:ellis | author:hawking"'])


TEST_SUITE = make_test_suite(TestSearchQueryParenthesisedParser,
                             TestParserUtilityFunctions)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
