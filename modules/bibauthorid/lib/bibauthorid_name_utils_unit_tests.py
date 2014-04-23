# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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

"""Unit tests for the search engine."""

__revision__ = \
    "$Id$"

from operator import ge, le

# name_tests: name string, split_name_parts,

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

from invenio.testutils import InvenioTestCase, make_test_suite, run_test_suite
from invenio.bibauthorid_name_utils import split_name_parts, distance, create_canonical_name, create_normalized_name, create_unified_name, soft_compare_names
from invenio.bibauthorid_name_utils import full_names_are_equal_composites, full_names_are_substrings, surname_compatibility, initials_compatibility, compare_names
from invenio.bibauthorid_name_utils import create_name_tuples
from invenio.bibauthorid_name_utils import create_matchable_name, \
    _split_by_first_occurence, _is_unseperated_initials, \
    _remove_ignored_characters_for_name, _replace_content_in_parentheses, \
    _apply_character_mapping_to_name, _remove_special_characters_and_numbers, \
    _get_number_of_words, generate_last_name_cluster_str, clean_string


class Test_distance_functions(InvenioTestCase):
    """ Test string distance functions """

    def test_simple_distance(self):
        self.assertEqual(distance('aaaaa', 'aaaaa'), 0)
        self.assertEqual(distance('aaaaa', 'aa'), 3)
        self.assertEqual(distance('aaaaa', 'aaaab'), 1)
        self.assertEqual(distance('aaaaa', 'bbbbb'), 5)
        self.assertEqual(distance('eecbr', 'bbbbb'), 4)


class Test_split_name_parts(InvenioTestCase):
    'Test splitting of names'
    names_split_name_parts = {
        'Test, m. e.': ['Test', ['m', 'e'], [], []],
        'Test, me': ['Test', ['m'], ['me'], [0]],
        'Test, me with m. u. ltiple names a. n. d. initials':
        ['Test', ['m', 'w', 'm', 'u', 'l', 'n', 'a', 'n', 'd', 'i'],
                 ['me', 'with', 'ltiple', 'names', 'initials'], [0, 1, 4, 5, 9]],
        'Test, me with multiple names':
        ['Test', ['m', 'w', 'm', 'n'], ['me', 'with', 'multiple', 'names'], [0, 1, 2, 3]],
        'me test': ['test', ['m'], ['me'], [0]],
        's. s. b. test': ['test', ['s', 's', 'b'], [], []],
        'should s. b. test': ['test', ['s', 's', 'b'], ['should'], [0]],
        'should still be test': ['test', ['s', 's', 'b'], ['should', 'still', 'be'], [0, 1, 2]],
        'test with -aoe}[/])+ junk, but with comma': [
            'test with -aoe}[/])+ junk', ['b', 'w', 'c'], ['but', 'with', 'comma'], [0, 1, 2]],
        'test,': ['test', [], [], []],
        'test, m initials morder': ['test', ['m', 'i', 'm'], ['initials', 'morder'], [1, 2]],
        'test, mix initials m.': ['test', ['m', 'i', 'm'], ['mix', 'initials'], [0, 1]],
        'test, s. s. b.': ['test', ['s', 's', 'b'], [], []],
        'test, s. still be': ['test', ['s', 's', 'b'], ['still', 'be'], [1, 2]],
        'with .[+)* ] just but without comma test': ['test', ['w', '[', '*', ']', 'j', 'b', 'w', 'c'],
                             ['with', '[+', 'just', 'but', 'without', 'comma'], [0, 1, 4, 5, 6, 7]],
        'test-dash': ['test-dash', [], [], []],
        'test-dash,': ['test-dash', [], [], []]
    }

    def test_split_name_parts(self):
        for tn in self.names_split_name_parts.keys():
            self.assertEqual(split_name_parts(tn), self.names_split_name_parts[tn])


class Test_create_canonical_names(InvenioTestCase):
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
        'test with -aoe}[/])+ junk, but with comma': 'B.W.C.Test.With.Aoe.Junk',
        'test,': 'Test',
        'test, m initials morder': 'M.I.M.Test',
        'test, mix initials m.': 'M.I.M.Test',
        'test, mix initials morder': 'M.I.M.Test',
        'test, s. s. b.': 'S.S.B.Test',
        'test, s. still be': 'S.S.B.Test',
        'with .[+)* ] just but without comma test': 'W.J.B.W.C.Test'
    }

    def test_create_canonical_name(self):
        for tn in self.names_create_canonical_names.keys():
            self.assertEqual(create_canonical_name(tn), self.names_create_canonical_names[tn])


class Test_create_normalized_name(InvenioTestCase):
    'Test creation of normalized names'
    tc = {
        'Hyphened-surname, hyphened-name and normal': 'Hyphened-Surname, Hyphened Name And Normal',
        'Test, m. e.': 'Test, M. E.',
        'Test, me': 'Test, Me',
        'Test, me with m. u. ltiple names a. n. d. initials': 'Test, Me With M. U. Ltiple Names A. N. D. Initials',
        'Test, me with multiple names': 'Test, Me With Multiple Names',
        'me test': 'Test, Me',
        's. s. b. test': 'Test, S. S. B.',
        'should s. b. test': 'Test, Should S. B.',
        'should still be test': 'Test, Should Still Be',
        'test with -aoe}[/])+ junk, but with comma': 'Test With -Aoe}[/])+ Junk, But With Comma',
        'test,': 'Test',
        'test, m initials morder': 'Test, M. Initials Morder',
        'test, mix initials m.': 'Test, Mix Initials M.',
        'test, mix initials morder': 'Test, Mix Initials Morder',
        'test, s. s. b.': 'Test, S. S. B.',
        'test, s. still be': 'Test, S. Still Be',
        'with .[+)* ] just but without comma test': 'Test, With [+ *. ]. Just But Without Comma'}

    def test_create_normalized_name(self):
        for tn in self.tc.keys():
            self.assertEqual(create_normalized_name(split_name_parts(tn), fix_capitalization=True), self.tc[tn])


class Test_create_unified_name(InvenioTestCase):
    'Test creation of unified names'
    tc = {
        'Hyphened-surname, hyphened-name and normal': 'Hyphened-surname, h. n. a. n. ',
        'Test, m. e.': 'Test, m. e. ',
        'Test, me': 'Test, m. ',
        'Test, me with m. u. ltiple names a. n. d. initials': 'Test, m. w. m. u. l. n. a. n. d. i. ',
        'Test, me with multiple names': 'Test, m. w. m. n. ',
        'me test': 'test, m. ',
        's. s. b. test': 'test, s. s. b. ',
        'should s. b. test': 'test, s. s. b. ',
        'should still be test': 'test, s. s. b. ',
        'test with -aoe}[/])+ junk, but with comma': 'test with -aoe}[/])+ junk, b. w. c. ',
        'test,': 'test, ',
        'test, m initials morder': 'test, m. i. m. ',
        'test, mix initials m.': 'test, m. i. m. ',
        'test, mix initials morder': 'test, m. i. m. ',
        'test, s. s. b.': 'test, s. s. b. ',
        'test, s. still be': 'test, s. s. b. ',
        'with .[+)* ] just but without comma test': 'test, w. [. *. ]. j. b. w. c. '}

    def test_create_unified_name(self):
        for tn in self.tc.keys():
            self.assertEqual(create_unified_name(tn), self.tc[tn])


class Test_soft_name_comparison(InvenioTestCase):
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
        'Test, nonamo': ['Test', [(ge, 0.5), (le, 1.)]],
    }

    def test_value_ranges(self):
        cn = soft_compare_names
        for n1 in self.tc.keys():
            n2 = self.tc[n1][0]
            tests = self.tc[n1][1]
            for test in tests:
                self.assertTrue(cn(n1, n2) == cn(n2, n1))
                self.assertTrue(test[0](cn(n1, n2), test[1]))


class Test_name_comparison(InvenioTestCase):
    'Test name comparison'
    tc = {
        'Test, Name': ['Test, Name', [(ge, 0.7), (le, 1.)]],
        'Test, N': ['Test, Name', [(ge, 0.6), (le, 0.8)]],
        'Test, Cane': ['Test, Name', [(ge, 0.0), (le, .2)]],
        'Test, C': ['Test, Name', [(ge, 0.0), (le, .2)]],
        'Test, Cane Name': ['Test, Name Cane', [(ge, 0.0), (le, 1.)]],
        'Test, C N': ['Test, N C', [(ge, 0.4), (le, 0.7)]],
        'Tast, C N': ['Test, C N', [(ge, 0.0), (le, 0.7)]],
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
        self.assertEqual(cn(['n1', 'n2', 'n3']), ['n1 n2 n3', 'N1n2 n3', 'n1 N2n3', 'N1n2n3'])
        self.assertEqual(cn(['n1', 'n2']), ['n1 n2', 'N1n2'])
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
        self.assertEqual(cn('Surname', 'Surname'), 1.0)
        self.assertEqual(cn('Surname', 'Verynotthesame'), 0.0)
        self.assertEqual(cn('Surname', 'Surnam'), 0.0)
        self.assertEqual(cn('Surname', 'Surnam'), 0.0)
        self.assertEqual(cn('Surname', 'Surnαme'), 1.0)

    def test_initials_compatibility(self):
        cn = initials_compatibility
        self.assertEqual(cn(['a', 'b', 'c'], ['a', 'b', 'c']), 1.0)
        self.assertEqual(cn(['a', 'b', 'c'], ['d', 'e', 'f']), 0.0)
        self.assertTrue(cn(['a', 'b'], ['a', 'c']) > 0.25)
        self.assertTrue(cn(['a', 'b'], ['a', 'c']) < 0.5)
        self.assertTrue(cn(['a', 'b'], ['c', 'a']) > 0.25)
        self.assertTrue(cn(['a', 'b'], ['c', 'a']) < 0.5)

    def test_value_ranges(self):
        cn = compare_names
        for n1 in self.tc.keys():
            n2 = self.tc[n1][0]
            tests = self.tc[n1][1]
            for test in tests:
                # print 'TESTING: ', n1, '|', n2, ' -- ', cn(n1,n2), cn(n1,n2), test[1]
                self.assertTrue(cn(n1, n2) == cn(n2, n1))
                self.assertTrue(test[0](cn(n1, n2), test[1]))


class TestMatchableName(InvenioTestCase):

    '''
    Unit tests for the matchable name transformation function.
    '''

    def test_split_by_first_occurence(self):
        self.assertEqual(_split_by_first_occurence('surname, name', ','),
                         ['surname', 'name'])
        self.assertEqual(_split_by_first_occurence('surname name', ','),
                         ['surname name', ''])
        self.assertEqual(_split_by_first_occurence('surname, name, secondname', ','),
                         ['surname', 'name, secondname'])
        self.assertNotEqual(_split_by_first_occurence('surname, name, secondname', ','),
                            ['surname', 'name', 'secondname'])
        self.assertEqual(_split_by_first_occurence(',', ','),
                         ['', ''])
        self.assertEqual(_split_by_first_occurence('surname\t name', '\t'),
                         ['surname', 'name'])

    def test_remove_ignored_characters_for_name(self):
        ignore_list = ['etc.', 'ignore me']
        self.assertEquals(_remove_ignored_characters_for_name('some text and etc.',
                                                              ignore_list),
                          'some text and ')
        self.assertEquals(_remove_ignored_characters_for_name('some text ignore me and etc.',
                                                              ignore_list),
                          'some text  and ')
        self.assertEquals(_remove_ignored_characters_for_name('some text andetc.',
                                                              ignore_list),
                          'some text and')
        self.assertEquals(_remove_ignored_characters_for_name('some text andetc.ignore me',
                                                              ignore_list),
                          'some text and')
        self.assertEquals(_remove_ignored_characters_for_name('ignore me',
                                                              ignore_list), '')

    def test_is_unseperated_initials(self):
        self.assertTrue(_is_unseperated_initials('AB'))
        self.assertFalse(_is_unseperated_initials('AB etc'))
        self.assertFalse(_is_unseperated_initials(''))
        self.assertFalse(_is_unseperated_initials('A'))
        self.assertFalse(_is_unseperated_initials('A.B'))
        self.assertFalse(_is_unseperated_initials('A..'))
        self.assertFalse(_is_unseperated_initials('aB'))
        self.assertFalse(_is_unseperated_initials('ABC'))
        self.assertFalse(_is_unseperated_initials('..'))

    def test_apply_character_mapping_to_name(self):
        mapping = {'a': 'b', 'x': 'y'}
        self.assertEquals(_apply_character_mapping_to_name('abcxyz', mapping),
                          'bbcyyz')
        self.assertEquals(_apply_character_mapping_to_name('kkkkkk', mapping),
                          'kkkkkk')
        self.assertEquals(_apply_character_mapping_to_name('abcxyz', dict()),
                          'abcxyz')

    def test_replace_content_in_parentheses(self):
        self.assertEquals(_replace_content_in_parentheses('abc(def)', ''), 'abc')
        self.assertEquals(_replace_content_in_parentheses('abc', ''), 'abc')
        self.assertEquals(_replace_content_in_parentheses('(def)', ''), '')
        self.assertEquals(_replace_content_in_parentheses('()', ''), '')
        self.assertEquals(_replace_content_in_parentheses('(def', ''), '(def')

    def test_remove_special_characters_and_numbers(self):
        self.assertEquals(_remove_special_characters_and_numbers('abc ?>%$9'),
                          'abc ')
        self.assertEquals(_remove_special_characters_and_numbers('123\"\"\"'),
                          '')
        self.assertEquals(_remove_special_characters_and_numbers('{}][:s ! '),
                          's  ')

    def test_get_number_of_words(self):
        self.assertEquals(_get_number_of_words(' word1  word2   word3'), 3)

    def test_create_matchable_name(self):
        '''
        This can act as a regression test of the whole function.
        '''
        self.assertEquals(create_matchable_name('Surname, Name'),
                          'name surname')
        self.assertEquals(create_matchable_name('Surname'),
                          'surname')
        self.assertEquals(create_matchable_name('Surname, Name (removed)'),
                          'name surname')
        self.assertEquals(create_matchable_name('Surname, Name'),
                          'name surname')
        self.assertEquals(create_matchable_name('Surname Secondsurname, Name',
                                                get_surname_words_length=True)[1], 2)


class TestPrebucketingFunction(InvenioTestCase):

    def test_generate_last_name_cluster(self):
        str_to_check = 'Surnameone Surnametwo, Name'
        self.assertEquals(generate_last_name_cluster_str(str_to_check),
                          'surnameonesurnametwo')


class TestCleanStringFunction(InvenioTestCase):

    cs = {'astring astring': 'astring astring',
          'astr123': 'astr',
          'astr123 456': 'astr ',
          '@#$!1a $, ': 'a  ',
          ',,,,<...': '   '
          }

    def test_clean_string(self):
        for name in self.cs.keys():
            self.assertEquals(clean_string(name), self.cs[name])

TEST_SUITE = make_test_suite(Test_distance_functions,
                             Test_split_name_parts,
                             Test_create_canonical_names,
                             Test_create_normalized_name,
                             Test_create_unified_name,
                             Test_soft_name_comparison,
                             Test_name_comparison,
                             TestMatchableName,
                             TestPrebucketingFunction,
                             TestCleanStringFunction)


if __name__ == '__main__':
    run_test_suite(TEST_SUITE)