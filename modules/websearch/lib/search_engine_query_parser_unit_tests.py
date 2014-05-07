# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2010, 2011, 2012, 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Unit tests for the search engine query parsers."""


from invenio.testutils import InvenioTestCase
import datetime

from invenio import search_engine_query_parser

from invenio.testutils import make_test_suite, run_test_suite
from invenio.search_engine import create_basic_search_units, perform_request_search
from invenio.config import CFG_WEBSEARCH_SPIRES_SYNTAX

if search_engine_query_parser.GOT_DATEUTIL:
    import dateutil
    from dateutil.relativedelta import relativedelta as du_delta
    DATEUTIL_AVAILABLE = True
else:
    DATEUTIL_AVAILABLE = False


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

class TestSpiresToInvenioSyntaxConverter(InvenioTestCase):
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

    if CFG_WEBSEARCH_SPIRES_SYNTAX > 0:
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
            invenio_search = 'author:"ellis, john*" or exactauthor:"ellis, j *" or exactauthor:"ellis, j" or exactauthor:"ellis, jo" or exactauthor:"ellis, joh" or author:"ellis, john, *"'
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

        def test_find_first_author(self):
            """SPIRES search syntax - find fa ellis"""
            inv_search = 'firstauthor:ellis'
            spi_search = 'find fa ellis'
            self._compare_searches(inv_search, spi_search)

        def test_find_first_author_initial(self):
            """SPIRES search syntax - find fa j ellis"""
            inv_search = 'firstauthor:"ellis, j*"'
            spi_search = 'find fa j ellis'
            self._compare_searches(inv_search, spi_search)

        def test_first_author_full_initial(self):
            """SPIRES search syntax - find fa klebanov, ig.r."""
            inv_search = 'firstauthor:"klebanov, ig* r*" or exactfirstauthor:"klebanov, i r"'
            spi_search = "find fa klebanov, ig.r."
            self._compare_searches(inv_search, spi_search)

        def test_citedby_author(self):
            """SPIRES search syntax - find citedby author doggy"""
            inv_search = 'citedby:author:doggy'
            spi_search = 'find citedby author doggy'
            self._compare_searches(inv_search, spi_search)

        def test_refersto_author(self):
            """SPIRES search syntax - find refersto author kitty"""
            inv_search = 'refersto:author:kitty'
            spi_search = 'find refersto author kitty'
            self._compare_searches(inv_search, spi_search)

        def test_refersto_author_multi_name(self):
            """SPIRES search syntax - find a ellis and refersto author \"parke, sj\""""
            inv_search = 'author:ellis refersto:author:"parke, s. j."'
            spi_search = 'find a ellis and refersto author "parke, s. j."'
            self._compare_searches(inv_search, spi_search)

        def test_refersto_author_multi_name_no_quotes(self):
            """SPIRES search syntax - find a ellis and refersto author parke, sj"""
            inv_search = 'author:ellis refersto:(author:"parke, sj*"  or exactauthor:"parke, s *"  or exactauthor:"parke, s" or author:"parke, sj, *")'
            spi_search = "find a ellis and refersto author parke, sj"
            self._compare_searches(inv_search, spi_search)

        def test_refersto_multi_word_no_quotes_no_index(self):
            """SPIRES search syntax - find refersto s parke"""
            inv_search = 'refersto:"s parke"'
            spi_search = 'find refersto s parke'
            self._compare_searches(inv_search, spi_search)

        def test_citedby_refersto_author(self):
            """SPIRES search syntax - find citedby refersto author penguin"""
            inv_search = 'refersto:citedby:author:penguin'
            spi_search = 'find refersto citedby author penguin'
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

        def test_topcite(self):
            """SPIRES search syntax - find topcite 50+"""
            inv_search = "cited:50->999999999"
            spi_search = "find topcite 50+"
            self._compare_searches(inv_search, spi_search)

        def test_topcit(self):
            """SPIRES search syntax - find topcit 50+"""
            inv_search = "cited:50->999999999"
            spi_search = "find topcit 50+"
            self._compare_searches(inv_search, spi_search)

        def test_caption(self):
            """SPIRES search syntax - find caption muon"""
            inv_search = "caption:muon"
            spi_search = "find caption muon"
            self._compare_searches(inv_search, spi_search)

        def test_caption_multi_word(self):
            """SPIRES search syntax - find caption quark mass"""
            inv_search = "caption:quark and caption:mass"
            spi_search = "find caption quark mass"
            self._compare_searches(inv_search, spi_search)

        def test_quotes(self):
            """SPIRES search syntax - find t 'compton scattering' and a mele"""
            inv_search = "title:'compton scattering' and author:mele"
            spi_search = "find t 'compton scattering' and a mele"
            self._compare_searches(inv_search, spi_search)

        def test_equals_sign(self):
            """SPIRES search syntax - find a beacom and date = 2000"""
            inv_search = "author:beacom year:2000"
            spi_search = "find a beacom and date = 2000"
            self._compare_searches(inv_search, spi_search)

        def test_type_code(self):
            """SPIRES search syntax - find tc/ps/scl review"""
            inv_search = "collection:review"
            spi_search = "find tc review"
            self._compare_searches(inv_search, spi_search)
            inv_search = "collection:review"
            spi_search = "find ps review"
            self._compare_searches(inv_search, spi_search)
            inv_search = "collection:review"
            spi_search = "find scl review"
            self._compare_searches(inv_search, spi_search)

        def test_field_code(self):
            """SPIRES search syntax - f f p"""
            inv_search = "subject:p"
            spi_search = "f f p"
            self._compare_searches(inv_search, spi_search)

        def test_coden(self):
            """SPIRES search syntax - find coden aphys"""
            inv_search = "journal:aphys"
            spi_search = "find coden aphys"
            self._compare_searches(inv_search, spi_search)

        def test_job_title(self):
            """SPIRES search syntax - find job engineer not position programmer"""
            inv_search = 'title:engineer not title:programmer'
            spi_search = 'find job engineer not position programmer'
            self._compare_searches(inv_search, spi_search)

        def test_job_rank(self):
            """SPIRES search syntax - find rank Postdoc"""
            inv_search = 'rank:Postdoc'
            spi_search = 'find rank Postdoc'
            self._compare_searches(inv_search, spi_search)

        def test_job_region(self):
            """SPIRES search syntax - find region EU not continent Europe"""
            inv_search = 'region:EU not region:Europe'
            spi_search = 'find region EU not continent Europe'
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
            """SPIRES search syntax - find aff SLAC and Stanford ->affiliation:SLAC and affiliation:Stanford"""
            # motivated by trac-187
            spi_search = "find aff SLAC and Stanford"
            inv_search = "affiliation:SLAC and affiliation:Stanford"
            self._compare_searches(inv_search, spi_search)

        def test_distribution_with_phrases(self):
            """SPIRES search syntax - find aff Penn State U -> affiliation:"Penn State U"""
            # motivated by trac-517
            spi_search = "find aff Penn State U"
            inv_search = "affiliation:\"Penn State U\""
            self._compare_searches(inv_search, spi_search)

        def test_distribution_with_many_clauses(self):
            """SPIRES search syntax - find a mele and brooks and holtkamp and o'connell"""
            spi_search = "find a mele and brooks and holtkamp and o'connell"
            inv_search = "author:mele author:brooks author:holtkamp author:o'connell"
            self._compare_searches(inv_search, spi_search)

        def test_keyword_as_kw(self):
            """SPIRES search syntax - find kw something ->keyword:something"""
            spi_search = "find kw meson"
            inv_search = "keyword:meson"
            self._compare_searches(inv_search, spi_search)

        def test_recid(self):
            """SPIRES search syntax - find recid 11111"""
            spi_search = 'find recid 111111'
            inv_search = 'recid:111111'
            self._compare_searches(inv_search, spi_search)

        def test_desy_keyword_translation(self):
            """SPIRES search syntax - find dk "B --> pi pi" """
            spi_search = "find dk \"B --> pi pi\""
            inv_search = "695__a:\"B --> pi pi\""
            self._compare_searches(inv_search, spi_search)

        def test_journal_section_joining(self):
            """SPIRES search syntax - journal Phys.Lett, 0903, 024 -> journal:Phys.Lett,0903,024"""
            spi_search = "find j Phys.Lett, 0903, 024"
            inv_search = "journal:Phys.Lett,0903,024"
            self._compare_searches(inv_search, spi_search)

        def test_journal_search_with_colon(self):
            """SPIRES search syntax - find j physics 1:195 -> journal:physics,1,195"""
            spi_search = "find j physics 1:195"
            inv_search = "journal:physics,1,195"
            self._compare_searches(inv_search, spi_search)

        def test_journal_non_triple_syntax(self):
            """SPIRES search syntax - find j physics jcap"""
            spi_search = "find j physics jcap"
            inv_search = "journal:physics and journal:jcap"
            self._compare_searches(inv_search, spi_search)

        def test_journal_triple_with_many_spaces(self):
            """SPIRES search syntax - find j physics        0903            024"""
            spi_search = 'find j physics        0903            024'
            inv_search = 'journal:physics,0903,024'
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

        def test_syntax_converter_expand_fulltext(self):
            """SPIRES search syntax - fulltext support"""
            spi_search = "find ft The holographic RG is based on"
            inv_search = "fulltext:The and fulltext:holographic and fulltext:RG and fulltext:is and fulltext:based and fulltext:on"
            self._compare_searches(inv_search, spi_search)

        def test_syntax_converter_expand_fulltext_within_larger(self):
            """SPIRES search syntax - fulltext subsearch support"""
            spi_search = "find au taylor and ft The holographic RG is based on and t brane"
            inv_search = "author:taylor fulltext:The and fulltext:holographic and fulltext:RG and fulltext:is and fulltext:based and fulltext:on title:brane"
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

        def test_date_invalid(self):
            """SPIRES search syntax - searching an invalid date"""
            spi_search = "find date foo"
            inv_search = "year:foo"
            self._compare_searches(inv_search, spi_search)

        def test_date_by_yr(self):
            """SPIRES search syntax - searching by date year"""
            spi_search = "find date 2002"
            inv_search = "year:2002"
            self._compare_searches(inv_search, spi_search)

        def test_date_by_lt_yr(self):
            """SPIRES search syntax - searching by date < year"""
            spi_search = "find date < 2002"
            inv_search = 'year:0->2002 AND NOT year:2002'
            self._compare_searches(inv_search, spi_search)

        def test_date_by_gt_yr(self):
            """SPIRES search syntax - searching by date > year"""
            spi_search = "find date > 1980"
            inv_search = 'year:1980->9999 AND NOT year:1980'
            self._compare_searches(inv_search, spi_search)

        def test_date_by_yr_mo(self):
            """SPIRES search syntax - searching by date 1976-04"""
            spi_search = "find date 1976-04"
            inv_search = 'year:1976-04'
            self._compare_searches(inv_search, spi_search)

        def test_date_by_yr_mo_day_wholemonth_and_suffix(self):
            """SPIRES search syntax - searching by date 1976-04-01 and t dog"""
            spi_search = "find date 1976-04-01 and t dog"
            inv_search = 'year:1976-04-01 and title:dog'
            self._compare_searches(inv_search, spi_search)

        def test_date_by_yr_mo_day_and_suffix(self):
            """SPIRES search syntax - searching by date 1976-04-05 and t dog"""
            spi_search = "find date 1976-04-05 and t dog"
            inv_search = 'year:1976-04-05 and title:dog'
            self._compare_searches(inv_search, spi_search)

        def test_date_by_yr_mo_d(self):
            """SPIRES search syntax - searching by date 1978-10-21"""
            spi_search = "find date 1978-10-21"
            inv_search = 'year:1978-10-21'
            self._compare_searches(inv_search, spi_search)

        def test_date_by_lt_yr_mo(self):
            """SPIRES search syntax - searching by date < 1978-10"""
            spi_search = "find date < 1978-10"
            inv_search = 'year:0->1978-10 AND NOT year:1978-10'
            self._compare_searches(inv_search, spi_search)

        def test_date_by_gt_yr_mo(self):
            """SPIRES search syntax - searching by date > 1978-10"""
            spi_search = "find date > 1978-10"
            inv_search = 'year:1978-10->9999 AND NOT year:1978-10'
            self._compare_searches(inv_search, spi_search)

        def test_date_by_lt_yr_mo_d(self):
            """SPIRES search syntax - searching by date < 1978-10-21"""
            spi_search = "find date < 1978-10-21"
            inv_search = 'year:0->1978-10-21 AND NOT year:1978-10-21'
            self._compare_searches(inv_search, spi_search)

        def test_date_by_gt_yr_mo_d(self):
            """SPIRES search syntax - searching by date > 1978-10-21"""
            spi_search = "find date > 1978-10-21"
            inv_search = 'year:1978-10-21->9999 AND NOT year:1978-10-21'
            self._compare_searches(inv_search, spi_search)

        def test_date_before_1900(self):
            """SPIRES search syntax - searching by date 1976-04"""
            spi_search = "find date 1895-04"
            inv_search = 'year:1895-04'
            self._compare_searches(inv_search, spi_search)

        if DATEUTIL_AVAILABLE:
            def test_date_2_digits_year_month_day(self):
                """SPIRES search syntax - searching by date > 78-10-21"""
                spi_search = "find date 78-10-21"
                inv_search = 'year:1978-10-21'
                self._compare_searches(inv_search, spi_search)

        if DATEUTIL_AVAILABLE:
            def test_date_2_digits_year(self):
                """SPIRES search syntax - searching by date 78"""
                spi_search = "find date 78"
                inv_search = 'year:1978'
                self._compare_searches(inv_search, spi_search)

        if DATEUTIL_AVAILABLE:
            def test_date_2_digits_year_future(self):
                """SPIRES search syntax - searching by date 2 years in the future"""
                d = datetime.datetime.today() + datetime.timedelta(days=730)
                spi_search = "find date %s" % d.strftime("%y")
                inv_search = 'year:%s' % d.strftime("%Y")
                self._compare_searches(inv_search, spi_search)

        if DATEUTIL_AVAILABLE:
            def test_date_2_digits_month_year(self):
                """SPIRES search syntax - searching by date feb 12"""
                # This should give us "feb 12" with us locale
                d = datetime.datetime(year=2012, month=2, day=1)
                date_str = d.strftime('%b %y')
                spi_search = "find date %s" % date_str
                inv_search = 'year:2012-02'
                self._compare_searches(inv_search, spi_search)

        def test_spires_syntax_trailing_colon(self):
            """SPIRES search syntax - test for blowup with trailing colon"""
            spi_search = "find a watanabe:"
            invenio_search = "author:watanabe:"
            self._compare_searches(invenio_search, spi_search)

        if DATEUTIL_AVAILABLE:
            def test_date_by_d_MO_yr(self):
                """SPIRES search syntax - searching by date 23 Sep 2010: will only work with dateutil installed"""
                spi_search = "find date 23 Sep 2010"
                inv_search = 'year:2010-09-23'
                self._compare_searches(inv_search, spi_search)

            def test_date_by_lt_d_MO_yr(self):
                """SPIRES search syntax - searching by date < 23 Sep 2010: will only work with dateutil installed"""
                spi_search = "find date < 23 Sep 2010"
                inv_search = 'year:0->2010-09-23 AND NOT year:2010-09-23'
                self._compare_searches(inv_search, spi_search)

            def test_date_by_d_MO_yr_parentheses(self):
                """SPIRES search syntax - searching by date 23 Sep 2010 using parentheses: will only work with dateutil installed"""
                spi_search = "find (date 23 Sep 2010)"
                inv_search = 'year:2010-09-23'
                self._compare_searches(inv_search, spi_search)

            def test_date_before_1900(self):
                """SPIRES search syntax - searching by date < 23 Sep 1889: will only work with dateutil installed"""
                spi_search = "find date < 23 Sep 1889"
                inv_search = 'year:0->1889-09-23 AND NOT year:1889-09-23'
                self._compare_searches(inv_search, spi_search)

            def test_date_by_gt_d_MO_yr(self):
                """SPIRES search syntax - searching by date > 12 Jun 1960: will only work with dateutil installed"""
                spi_search = "find date > 12 Jun 1960"
                inv_search = 'year:1960-06-12->9999 AND NOT year:1960-06-12'
                self._compare_searches(inv_search, spi_search)

            def test_date_accept_today(self):
                """SPIRES search syntax - searching by today"""
                spi_search = "find date today"
                inv_search = "year:" + datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d')
                self._compare_searches(inv_search, spi_search)

            def test_date_accept_yesterday(self):
                """SPIRES search syntax - searching by yesterday"""
                import dateutil.relativedelta
                spi_search = "find date yesterday"
                inv_search = "year:" + datetime.datetime.strftime(datetime.datetime.today()+dateutil.relativedelta.relativedelta(days=-1), '%Y-%m-%d')
                self._compare_searches(inv_search, spi_search)

            def test_date_accept_this_month(self):
                """SPIRES search syntax - searching by this month"""
                spi_search = "find date this month"
                inv_search = "year:" + datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m')
                self._compare_searches(inv_search, spi_search)

            def test_date_accept_last_month(self):
                """SPIRES search syntax - searching by last month"""
                spi_search = "find date last month"
                inv_search = "year:" + datetime.datetime.strftime(datetime.datetime.today()\
                                                    +dateutil.relativedelta.relativedelta(months=-1), '%Y-%m')
                self._compare_searches(inv_search, spi_search)

            def test_date_accept_this_week(self):
                """SPIRES search syntax - searching by this week"""
                spi_search = "find date this week"
                begin = datetime.datetime.today()
                days_to_remove = datetime.datetime.today().isoweekday() % 7
                begin += du_delta(days=-days_to_remove)
                begin_str = datetime.datetime.strftime(begin, '%Y-%m-%d')
                # Only 6 days cause the last day is included in the search
                end = datetime.datetime.today()
                end_str = datetime.datetime.strftime(end, '%Y-%m-%d')
                inv_search = "year:%s->%s" % (begin_str, end_str)
                self._compare_searches(inv_search, spi_search)

            def test_date_accept_last_week(self):
                """SPIRES search syntax - searching by last week"""
                spi_search = "find date last week"
                begin = datetime.datetime.today()
                days_to_remove = 7 + datetime.datetime.today().isoweekday() % 7
                begin += du_delta(days=-days_to_remove)
                begin_str = datetime.datetime.strftime(begin, '%Y-%m-%d')
                # Only 6 days cause the last day is included in the search
                end = begin + du_delta(days=6)
                end_str = datetime.datetime.strftime(end, '%Y-%m-%d')
                inv_search = "year:%s->%s" % (begin_str, end_str)
                self._compare_searches(inv_search, spi_search)

            def test_date_accept_date_minus_days(self):
                """SPIRES search syntax - searching by 2011-01-03 - 2"""
                spi_search = "find date 2011-01-03 - 2"
                inv_search = "year:2011-01-01"
                self._compare_searches(inv_search, spi_search)

            def test_date_accept_date_minus_days_with_month_wrap(self):
                """SPIRES search syntax - searching by 2011-03-01 - 1"""
                spi_search = "find date 2011-03-01 - 1"
                inv_search = "year:2011-02-28"
                self._compare_searches(inv_search, spi_search)

            def test_date_accept_date_minus_days_with_year_wrap(self):
                """SPIRES search syntax - searching by 2011-01-01 - 1"""
                spi_search = "find date 2011-01-01 - 1"
                inv_search = "year:2010-12-31"
                self._compare_searches(inv_search, spi_search)

            def test_date_accept_date_minus_days_with_leapyear_february(self):
                """SPIRES search syntax - searching by 2008-03-01 - 1"""
                spi_search = "find date 2008-03-01 - 1"
                inv_search = "year:2008-02-29"
                self._compare_searches(inv_search, spi_search)

            def test_date_accept_date_minus_many_days(self):
                """SPIRES search syntax - searching by 2011-02-24 - 946"""
                spi_search = "find date 2011-02-24 - 946"
                inv_search = "year:2008-07-23"
                self._compare_searches(inv_search, spi_search)

            def test_date_accept_date_plus_days(self):
                """SPIRES search syntax - searching by 2011-01-03 + 2"""
                spi_search = "find date 2011-01-01 + 2"
                inv_search = "year:2011-01-03"
                self._compare_searches(inv_search, spi_search)

            def test_date_accept_plus_days_with_month_wrap(self):
                """SPIRES search syntax - searching by 2011-03-31 + 2"""
                spi_search = "find date 2011-03-31 + 2"
                inv_search = "year:2011-04-02"
                self._compare_searches(inv_search, spi_search)

            def test_date_accept_date_plus_days_with_year_wrap(self):
                """SPIRES search syntax - searching by 2011-12-31 + 1"""
                spi_search = "find date 2011-12-31 + 1"
                inv_search = "year:2012-01-01"
                self._compare_searches(inv_search, spi_search)

            def test_date_accept_date_plus_days_with_leapyear_february(self):
                """SPIRES search syntax - searching by 2008-02-29 + 2"""
                spi_search = "find date 2008-02-28 + 2"
                inv_search = "year:2008-03-01"
                self._compare_searches(inv_search, spi_search)

            def test_date_accept_date_plus_many_days(self):
                """SPIRES search syntax - searching by 2011-02-24 + 666"""
                spi_search = "find date 2011-02-24 + 666"
                inv_search = "year:2012-12-21"
                self._compare_searches(inv_search, spi_search)

        def test_spires_syntax_detected_f(self):
            """SPIRES search syntax - test detection f t p"""
            # trac #261
            converter = search_engine_query_parser.SpiresToInvenioSyntaxConverter()
            spi_search = converter.is_applicable("f t p")
            self.assertEqual(spi_search, True)

        def test_spires_syntax_detected_fin(self):
            """SPIRES search syntax - test detection fin t p"""
            # trac #261
            converter = search_engine_query_parser.SpiresToInvenioSyntaxConverter()
            spi_search = converter.is_applicable("fin t p")
            self.assertEqual(spi_search, True)

        def test_spires_keyword_distribution_before_conjunctions(self):
            """SPIRES search syntax - test find journal phys.lett. 0903 024"""
            spi_search = 'find journal phys.lett. 0903 024'
            inv_search = '(journal:phys.lett.,0903,024)'
            self._compare_searches(inv_search, spi_search)

        def test_spires_keyword_distribution_with_parens(self):
            """SPIRES search syntax - test find cn d0 and (a abachi or abbott or abazov)"""
            spi_search = "find cn d0 and (a abachi or abbott or abazov)"
            inv_search = "collaboration:d0 and (author:abachi or author:abbott or author:abazov)"
            self._compare_searches(inv_search, spi_search)

        def test_super_short_author_name(self):
            """SPIRES search syntax - test fin a er and cn cms"""
            spi_search = "fin a er and cn cms"
            inv_search = "author:er collaboration:cms"
            self._compare_searches(inv_search, spi_search)

        def test_simple_syntax_mixing(self):
            """SPIRES and invenio search syntax - find a ellis and citedby:hawking"""
            combo_search = "find a ellis and citedby:hawking"
            inv_search = "author:ellis citedby:hawking"
            self._compare_searches(inv_search, combo_search)

        def test_author_first_syntax_mixing(self):
            """SPIRES and invenio search syntax - find a dixon, l.j. cited:10->52"""
            combo_search = 'find a dixon, l.j. cited:10->52'
            inv_search = 'author:"dixon, l* j*" cited:10->52'
            self._compare_searches(inv_search, combo_search)

        def test_minus_boolean_syntax_mixing(self):
            """SPIRES and invenio search syntax - find a ellis -title:muon"""
            combo_search = 'find a ellis -title:muon'
            inv_search = 'author:ellis -title:muon'
            self._compare_searches(inv_search, combo_search)

        def test_plus_boolean_syntax_mixing(self):
            """SPIRES and invenio search syntax - find a ellis +title:muon"""
            combo_search = 'find a ellis +title:muon'
            inv_search = 'author:ellis title:muon'
            self._compare_searches(inv_search, combo_search)

        def test_second_level_syntax_mixing(self):
            """SPIRES and invenio search syntax - find a ellis refersto:author:hawking"""
            combo_search = 'find a ellis refersto:author:hawking'
            inv_search = 'author:ellis refersto:author:hawking'
            self._compare_searches(inv_search, combo_search)

    if CFG_WEBSEARCH_SPIRES_SYNTAX > 1:
        def test_absorbs_naked_a_search(self):
            """SPIRES search syntax - a ellis"""
            invenio_search = "author:ellis"
            naked_search = "a ellis"
            self._compare_searches(invenio_search, naked_search)

        def test_absorbs_naked_author_search(self):
            """SPIRES search syntax - author ellis"""
            invenio_search = "author:ellis"
            spi_search = "author ellis"
            self._compare_searches(invenio_search, spi_search)

        def test_spires_syntax_detected_naked_a(self):
            """SPIRES search syntax - test detection a ellis"""
            converter = search_engine_query_parser.SpiresToInvenioSyntaxConverter()
            spi_search = converter.is_applicable("a ellis")
            self.assertEqual(spi_search, True)

        def test_spires_syntax_detected_naked_author(self):
            """SPIRES search syntax - test detection author ellis"""
            converter = search_engine_query_parser.SpiresToInvenioSyntaxConverter()
            spi_search = converter.is_applicable("author ellis")
            self.assertEqual(spi_search, True)

        def test_spires_syntax_detected_naked_author_leading_spaces(self):
            """SPIRES search syntax - test detection              author ellis"""
            converter = search_engine_query_parser.SpiresToInvenioSyntaxConverter()
            spi_search = converter.is_applicable("             author ellis")
            self.assertEqual(spi_search, True)

        def test_spires_syntax_detected_naked_title(self):
            """SPIRES search syntax - test detection t muon"""
            converter = search_engine_query_parser.SpiresToInvenioSyntaxConverter()
            spi_search = converter.is_applicable("t muon")
            self.assertEqual(spi_search, True)

        def test_spires_syntax_detected_second_keyword(self):
            """SPIRES search syntax - test detection author:ellis and t muon"""
            converter = search_engine_query_parser.SpiresToInvenioSyntaxConverter()
            spi_search = converter.is_applicable("author:ellis and t muon")
            self.assertEqual(spi_search, True)

    def test_spires_syntax_detected_invenio(self):
        """SPIRES search syntax - test detection Not SPIRES"""
        # trac #261
        converter = search_engine_query_parser.SpiresToInvenioSyntaxConverter()
        inv_search = converter.is_applicable("t:p a:c")
        self.assertEqual(inv_search, False)

    def test_invenio_syntax_only_second_level(self):
        """invenio search syntax - citedby:reportnumber:hep-th/0205061"""
        inv_search = 'citedby:reportnumber:hep-th/0205061'
        self._compare_searches(inv_search, inv_search)

    def test_invenio_syntax_only_boolean(self):
        """invenio search syntax - author:ellis and not title:hadronic and not title:collisions"""
        inv_search = "author:ellis and not title:hadronic and not title:collisions"
        self._compare_searches(inv_search, inv_search)

TEST_SUITE = make_test_suite(TestSearchQueryParenthesisedParser,
                             TestSpiresToInvenioSyntaxConverter,
                             TestParserUtilityFunctions)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
    #run_test_suite(make_test_suite(TestParserUtilityFunctions, TestSearchQueryParenthesisedParser))  # DEBUG
