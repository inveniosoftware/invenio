# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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

"""Unit tests for the search engine."""

__revision__ = \
    "$Id$"

import unittest
from operator import ge,le,eq


#name_tests: name string, split_name_parts,

names = [
 'Test, m. e.',
 'Test, me',
 'Test, me with m. u. ltiple names a. n. d. initials',
 'Test, me with multiple names',
 'me test',
 's. s. b. test',
 'should s. b. test',
 'should still be test',
 'test with -aoe}[/])+ junk, but with comma',
 'test,',
 'test, m initials morder',
 'test, mix initials m.',
 'test, mix initials morder',
 'test, s. s. b.',
 'test, s. still be',
 'with .[+)* ] just but without comma test']

from invenio.bibauthorid_name_utils import split_name_parts, distance, create_canonical_name, create_normalized_name, create_unified_name, soft_compare_names
from invenio.bibauthorid_name_utils import full_names_are_equal_composites, full_names_are_substrings, surname_compatibility, initials_compatibility, compare_names
from invenio.bibauthorid_name_utils import create_name_tuples

class Test_distance_functions(unittest.TestCase):
    """ Test string distance functions """

    def test_simple_distance(self):
        self.assertEqual(distance('aaaaa','aaaaa'), 0)
        self.assertEqual(distance('aaaaa','aa'), 3)
        self.assertEqual(distance('aaaaa','aaaab'), 1)
        self.assertEqual(distance('aaaaa','bbbbb'), 5)
        self.assertEqual(distance('eecbr','bbbbb'), 4)


class Test_split_name_parts(unittest.TestCase):
    'Test splitting of names'
    names_split_name_parts = {
         'Test, m. e.': ['Test', ['M', 'E'], [], []],
         'Test, me': ['Test', ['M'], ['Me'], [0]],
         'Test, me with m. u. ltiple names a. n. d. initials': ['Test', ['M', 'W', 'M', 'U', 'L', 'N', 'A', 'N', 'D', 'I'],['Me', 'With', 'Ltiple', 'Names', 'Initials'],[0, 1, 4, 5, 9]],
         'Test, me with multiple names': ['Test',['M', 'W', 'M', 'N'],['Me', 'With', 'Multiple', 'Names'],[0, 1, 2, 3]],
         'me test': ['Test', ['M'], ['Me'], [0]],
         's. s. b. test': ['Test', ['S', 'S', 'B'], [], []],
         'should s. b. test': ['Test', ['S', 'S', 'B'], ['Should'], [0]],
         'should still be test': ['Test',['S', 'S', 'B'],['Should', 'Still', 'Be'],[0, 1, 2]],
         'test with -aoe}[/])+ junk, but with comma': ['Test with -Aoe}[/])+ junk',['B', 'W', 'C'],['But', 'With', 'Comma'],[0, 1, 2]],
         'test,': ['Test', [], [], []],
         'test, m initials morder': ['Test',['M', 'I', 'M'],['Initials', 'Morder'],[1, 2]],
         'test, mix initials m.': ['Test',['M', 'I', 'M'],['Mix', 'Initials'],[0, 1]],
         'test, mix initials morder': ['Test',['M', 'I', 'M'],['Mix', 'Initials', 'Morder'],[0, 1, 2]],
         'test, s. s. b.': ['Test', ['S', 'S', 'B'], [], []],
         'test, s. still be': ['Test', ['S', 'S', 'B'], ['Still', 'Be'], [1, 2]],
         'with .[+)* ] just but without comma test': ['Test',['W', '[', '*', ']', 'J', 'B', 'W', 'C'],['With', '[+', 'Just', 'But', 'Without', 'Comma'],[0, 1, 4, 5, 6, 7]],
         'test-dash': ['Test-Dash', [], [], []],
         'test-dash,': ['Test-Dash', [], [], []]
         }

    def test_split_name_parss(self):
        for tn in self.names_split_name_parts.keys():
            self.assertEqual(split_name_parts(tn), self.names_split_name_parts[tn])


class Test_create_canonical_names(unittest.TestCase):
    'Test creation of canonical names'
    names_create_canonical_names = {
     'Test': 'Test',
     'Test, m. e.': 'M.E.Test',
     'Test, me': 'M.Test',
     'Test, me with m. u. ltiple names a. n. d. initials': 'M.W.M.U.L.N.A.N.D.I.Test',
     'Test, me with multiple names': 'M.W.M.N.Test',
     'me test': 'M.Test',
     's. s. b. test': 'S.S.B.Test',
     'should s. b. test': 'S.S.B.Test',
     'should still be test': 'S.S.B.Test',
     'test with -aoe}[/])+ junk, but with comma': 'B.W.C.Test.with.Aoe.junk',
     'test,': 'Test',
     'test, m initials morder': 'M.I.M.Test',
     'test, mix initials m.': 'M.I.M.Test',
     'test, mix initials morder': 'M.I.M.Test',
     'test, s. s. b.': 'S.S.B.Test',
     'test, s. still be': 'S.S.B.Test',
     'with .[+)* ] just but without comma test': 'W..J.B.W.C.Test'
     }
    def test_create_canonical_name(self):
        for tn in self.names_create_canonical_names.keys():
            self.assertEqual(create_canonical_name(tn), self.names_create_canonical_names[tn])


class Test_create_normalized_name(unittest.TestCase):
    'Test creation of normalized names'
    tc ={
     'Hyphened-surname, hyphened-name and normal': 'Hyphened-Surname, Hyphened Name And Normal',
     'Test, m. e.': 'Test, M. E.',
     'Test, me': 'Test, Me',
     'Test, me with m. u. ltiple names a. n. d. initials': 'Test, Me With M. U. Ltiple Names A. N. D. Initials',
     'Test, me with multiple names': 'Test, Me With Multiple Names',
     'me test': 'Test, Me',
     's. s. b. test': 'Test, S. S. B.',
     'should s. b. test': 'Test, Should S. B.',
     'should still be test': 'Test, Should Still Be',
     'test with -aoe}[/])+ junk, but with comma': 'Test with -Aoe}[/])+ junk, But With Comma',
     'test,': 'Test',
     'test, m initials morder': 'Test, M. Initials Morder',
     'test, mix initials m.': 'Test, Mix Initials M.',
     'test, mix initials morder': 'Test, Mix Initials Morder',
     'test, s. s. b.': 'Test, S. S. B.',
     'test, s. still be': 'Test, S. Still Be',
     'with .[+)* ] just but without comma test': 'Test, With [+ *. ]. Just But Without Comma'}


    def test_create_normalized_name(self):
        for tn in self.tc.keys():
            self.assertEqual(create_normalized_name(split_name_parts(tn)), self.tc[tn])



class Test_create_uinified_name(unittest.TestCase):
    'Test creation of unified names'
    tc = {
     'Hyphened-surname, hyphened-name and normal': 'Hyphened-Surname, H. N. A. N. ',
     'Test, m. e.': 'Test, M. E. ',
     'Test, me': 'Test, M. ',
     'Test, me with m. u. ltiple names a. n. d. initials': 'Test, M. W. M. U. L. N. A. N. D. I. ',
     'Test, me with multiple names': 'Test, M. W. M. N. ',
     'me test': 'Test, M. ',
     's. s. b. test': 'Test, S. S. B. ',
     'should s. b. test': 'Test, S. S. B. ',
     'should still be test': 'Test, S. S. B. ',
     'test with -aoe}[/])+ junk, but with comma': 'Test with -Aoe}[/])+ junk, B. W. C. ',
     'test,': 'Test, ',
     'test, m initials morder': 'Test, M. I. M. ',
     'test, mix initials m.': 'Test, M. I. M. ',
     'test, mix initials morder': 'Test, M. I. M. ',
     'test, s. s. b.': 'Test, S. S. B. ',
     'test, s. still be': 'Test, S. S. B. ',
     'with .[+)* ] just but without comma test': 'Test, W. [. *. ]. J. B. W. C. '}

    def test_create_unified_name(self):
        for tn in self.tc.keys():
            self.assertEqual(create_unified_name(tn), self.tc[tn])

class Test_soft_name_comparison(unittest.TestCase):
    'Test soft name comparison'

    tc = {
        'Test, Name': ['Test, Name', [(ge, 0.7), (le, 1.)]],
        'Test, N': ['Test, Name', [(ge, 0.7), (le, 1.)]],
        'Test, Cane': ['Test, Name', [(ge, 0.5), (le, 1.)]],
        'Test, C': ['Test, Name', [(ge, 0.5), (le, 1.)]],
        'Test, Cane Name': ['Test, Name Cane', [(ge, 0.5), (le, 1.)]],
        'Test, C N': ['Test, N C', [(ge, 0.5), (le, 1.)]],
        'Tast, C N': ['Test, N C', [(ge, 0.0), (le, 0.5)]],
        'Diff, C N': ['Erent, C N', [(ge, 0.0), (le, 0.4)]],
        'Diff, Con Nome': ['Erent, Con Nome', [(ge, 0.0), (le, 0.4)]],
        'Diff, Con Nomee': ['Erent, Che Noun', [(ge, 0.0), (le, 0.2)]],
        'Diff, Name': ['Erent, Completely', [(ge, 0.0), (le, 0.1)]],
        'Test-dash': ['Test-dash', [(ge, 0.5), (le, 1.)]],
        'Test, noname': ['Test,', [(ge, 0.5), (le, 1.)]],
        'Test, noname': ['Test', [(ge, 0.5), (le, 1.)]],
        }

    def test_value_ranges(self):
        cn = soft_compare_names
        for n1 in self.tc.keys():
            n2 = self.tc[n1][0]
            tests = self.tc[n1][1]
            for test in tests:
                self.assertTrue(cn(n1,n2) == cn(n2,n1))
                self.assertTrue(test[0](cn(n1,n2), test[1]))


class Test_name_comparison(unittest.TestCase):
    'Test name comparison'
    tc = {
        'Test, Name': ['Test, Name', [(ge, 0.7), (le, 1.)]],
        'Test, N': ['Test, Name', [(ge, 0.6), (le, 0.8)]],
        'Test, Cane': ['Test, Name', [(ge, 0.0), (le, .2)]],
        'Test, C': ['Test, Name', [(ge, 0.0), (le, .2)]],
        'Test, Cane Name': ['Test, Name Cane', [(ge, 0.0), (le, 1.)]],
        'Test, C N': ['Test, N C', [(ge, 0.4), (le, 0.7)]],
        'Tast, C N': ['Test, C N', [(ge, 0.4), (le, 0.7)]],
        'Diff, C N': ['Erent, C N', [(ge, 0.0), (le, 0.2)]],
        'Diff, Con Nome': ['Erent, Con Nome', [(ge, 0.0), (le, 0.2)]],
        'Diff, Con Nomee': ['Erent, Che Noun', [(ge, 0.0), (le, 0.2)]],
        'Diff, Name': ['Erent, Completely', [(ge, 0.0), (le, 0.1)]],
        'Chen, Xiaoli': ['Chen, Xiao Li', [(ge, 0.6), (le, 0.8)]],
        'Chen, Xiaolo': ['Chen, Xiao', [(ge, 0.7), (le, 0.8)]],
        'Chen, Xiaola': ['Chen, Xia', [(ge, 0.6), (le, 0.7)]],
        'Chen, Xiaolu': ['Chen, Xi', [(ge, 0.4), (le, 0.6)]],
        }

    def test_create_name_tuples(self):
        cn = create_name_tuples
        self.assertEqual(cn(['n1','n2','n3']), ['n1 n2 n3', 'N1n2 n3', 'n1 N2n3', 'N1n2n3'])
        self.assertEqual(cn(['n1','n2']), ['n1 n2', 'N1n2'])
        self.assertEqual(cn(['n1']), ['n1'])

    def test_full_names_are_equal_composites(self):
        cn = full_names_are_equal_composites
        self.assertTrue(cn('surname, comp-osite', 'surname, comp osite'))
        self.assertTrue(cn('surname, comp [{} ) osite', 'surname, comp osite'))
        self.assertTrue(cn('surname, composite', 'surname, comp osite'))
        self.assertFalse(cn('surname, comp-osite', 'surname, notcomp osite'))
        self.assertFalse(cn('surname, comp-osite', 'surname, comp nosite'))
        self.assertFalse(cn('surname, comp-osite', 'surname, compo osite'))
        self.assertFalse(cn('surname, comp-osite', 'surname, comp osited'))

    def test_full_names_are_substrings(self):
        cn = full_names_are_substrings
        self.assertTrue(cn('Sur, longname', 'Sur, long'))
        self.assertFalse(cn('Sur, longname', 'Sur, name'))
        self.assertTrue(cn('Sur, long', 'Sur, long'))
        self.assertFalse(cn('Sur, l', 'Sur, long'))
        self.assertFalse(cn('Sur, name', 'Sur, word'))

    def test_surname_compatibility(self):
        cn = surname_compatibility
        self.assertEqual(cn('Surname','Surname'), 1.0)
        self.assertEqual(cn('Surname','Verynotthesame'), 0.0)
        self.assertTrue(cn('Surname', 'Surnam') > 0.5)
        self.assertTrue(cn('Surname','Surnam' ) < 1.0)
        self.assertTrue(cn('Surname', 'Curname') > 0.5)
        self.assertTrue(cn('test','tast') > 0.5)

    def test_initials_compatibility(self):
        cn = initials_compatibility
        self.assertEqual(cn(['a','b','c'],['a','b','c']), 1.0)
        self.assertEqual(cn(['a','b','c'],['d','e','f']), 0.0)
        self.assertTrue(cn(['a','b'], ['a','c']) > 0.25)
        self.assertTrue(cn(['a','b'], ['a','c']) < 0.5)
        self.assertTrue(cn(['a','b'], ['c','a']) > 0.25)
        self.assertTrue(cn(['a','b'], ['c','a']) < 0.5)

    def test_value_ranges(self):
        cn = compare_names
        for n1 in self.tc.keys():
            n2 = self.tc[n1][0]
            tests = self.tc[n1][1]
            for test in tests:
                #print 'TESTING: ', n1, n2, ' -- ', cn(n1,n2)
                self.assertTrue(cn(n1,n2) == cn(n2,n1))
                self.assertTrue(test[0](cn(n1,n2), test[1]))

if __name__ == '__main__':
    #run_test_suite(TEST_SUITE)
    unittest.main(verbosity=2)