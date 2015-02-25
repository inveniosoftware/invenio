# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2013 CERN.
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

"""Unit tests for logic library."""

from invenio.utils.logic import expr, Expr, to_cnf, pl_true
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class exprExprOpsTest(InvenioTestCase):
    """Testing expr and Expr against one another."""

    def test_trivial_expr(self):
        """logicutils - create trivial Expr with expr()"""
        self.assertEqual(expr('a | b'), Expr('|', 'a', 'b'))

    def test_deep_expr(self):
        """logicutils - create deep Expr with expr()"""
        self.assertEqual(expr('a | b | c | d | e'),
                         Expr('|', Expr('|', Expr('|', Expr('|', 'a', 'b'), 'c'), 'd'), 'e'))


class toCNFTest(InvenioTestCase):
    """Testing conversion to conjunctive normal form"""

    def test_singleton(self):
        """logicutils - singletons are already in CNF"""
        self.assertEqual(to_cnf(expr('a')),
                         Expr('a'))

    def test_complex_example_Norvig(self):
        """logicutils - (P&Q) | (~P & ~Q) in CNF"""
        self.assertEqual(str(to_cnf('(P&Q) | (~P & ~Q)')),
                         str('((~P | P) & (~Q | P) & (~P | Q) & (~Q | Q))'))

    def test_ORed_pair(self):
        """logicutils - ORed pair should be in CNF"""
        self.assertEqual(to_cnf(expr('a | b')),
                         Expr('|', 'a', 'b'))

    def test_ANDed_pair(self):
        """logicutils - ANDed pair should be in CNF"""
        self.assertEqual(to_cnf(expr('a & b')),
                         Expr('&', 'a', 'b'))


class prop_logicTest(InvenioTestCase):
    """Testing basic propositional logic functionality"""
    P = Expr('P')

    def test_pl_true_P_true(self):
        """logicutils - True thing is evaluated as such"""
        self.assertEqual(pl_true(self.P, {self.P: True}),
                         True)

    def test_pl_true_P_false(self):
        """logicutils - False thing is evaluated as such"""
        self.assertEqual(pl_true(self.P, {self.P: False}),
                         False)


TEST_SUITE = make_test_suite(exprExprOpsTest, toCNFTest, prop_logicTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
