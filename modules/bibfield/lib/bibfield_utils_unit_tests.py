# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2013 CERN.
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

"""
BibFieldUtils Unit tests.
"""

import unittest

from invenio.bibfield_utils import prepare_field_keys, build_data_structure, CoolList, CoolDict, BibFieldDict

from invenio.testutils import make_test_suite, run_test_suite


class BibFieldCoolListDictUnitTests(unittest.TestCase):
    """
    Test class to verify the correct behaviour of the classes involved into the
    intermediate structure
    """

    def test_cool_list(self):
        """Bibfield Utils, CoolList - Unit tests"""
        ll = CoolList()
        ll.append(1)
        ll.append(2)
        ll.append(3)
        self.assertFalse(ll.consumed)
        ll[1]
        self.assertEqual(ll._consumed, [False, True, False])
        self.assertFalse(ll.consumed)
        [i for i in ll]
        self.assertTrue(ll.consumed)
        ll[1] = [4, 5, 6]
        self.assertFalse(ll.consumed)
        self.assertEqual(ll._consumed, [True, [False, False, False], True])
        [i for i in ll]
        self.assertFalse(ll.consumed)
        self.assertEqual(ll._consumed, [True, [False, False, False], True])
        ll[1]
        self.assertFalse(ll.consumed)
        [i for i in ll[1]]
        self.assertTrue(ll.consumed)

    def test_cool_dict(self):
        """Bibfield Utils, CoolDict - Unit tests"""
        d = CoolDict()
        d['a'] = 1
        d['b'] = 2
        d['c'] = 3
        self.assertFalse(d.consumed)
        d['a']
        self.assertFalse(d.consumed)
        [v for dummy_k, v in d.iteritems()]
        self.assertTrue(d.consumed)
        d['b'] = {'d': 1}
        self.assertFalse(d.consumed)
        d['b']
        self.assertFalse(d.consumed)
        [v for dummy_k, v in d['b'].iteritems()]
        self.assertTrue(d.consumed)
        d.extend('a', 11)
        self.assertFalse(d.consumed)
        self.assertTrue(isinstance(d['a'], CoolList))
        [i for i in d['a']]
        self.assertTrue(d.consumed)

    def test_cool_list_and_dict(self):
        """Bibfield Utils, CoolList and CoolDict - Unit tests"""
        d = CoolDict()
        l = CoolList()
        d['a'] = l
        self.assertTrue(d.consumed)
        l.append(1)
        l.append(2)
        d['a'] = l
        self.assertFalse(d.consumed)
        d['b'] = CoolList([{'a':1}, {'a':2}])
        self.assertFalse(d.consumed)
        [v for dummy_k, v in d.iteritems()]
        self.assertFalse(d.consumed)
        [i for i in d['a']]
        [v for i in d['b'] for dummy_k, v in i.iteritems()]
        self.assertTrue(d.consumed)


class BibFieldUtilsUnitTests(unittest.TestCase):
    """
    Test class for bibfield utilities
    """

    def test_prepare_field_keys(self):
        """BibField Utils, prepare_field_keys - Unit Test"""
        key = 'authors'
        self.assertEqual(prepare_field_keys(key), ['["authors"]'])
        self.assertEqual(prepare_field_keys(key, write=True), ['["authors"]'])
        key = 'authors[0]'
        self.assertEqual(prepare_field_keys(key), ['["authors"][0]'])
        self.assertEqual(prepare_field_keys(key, True), ['["authors"]', '[0]'])
        key = 'authors[n]'
        self.assertEqual(prepare_field_keys(key), ['["authors"][-1]'])
        self.assertEqual(prepare_field_keys(key, True), ['["authors"]', '[-1]'])
        key = 'authors.ln'
        self.assertEqual(prepare_field_keys(key), ['["authors"]', '["ln"]'])
        self.assertEqual(prepare_field_keys(key, True), ['["authors"]', '["ln"]'])

        key = 'a[1].b[0].c.d[n]'
        self.assertEqual(prepare_field_keys(key), ['["a"][1]', '["b"][0]', '["c"]', '["d"][-1]'])
        self.assertEqual(prepare_field_keys(key, True), ['["a"]', '[1]', '["b"]', '[0]', '["c"]', '["d"]', '[-1]'])

    def test_build_data_structure(self):
        """BibField Utils, build_data_structure - Unit Test"""
        d = dict()
        build_data_structure(d, 'authors')
        self.assertEqual(d, {'authors': None})
        build_data_structure(d, 'authors[0]')
        self.assertEqual(d, {'authors': [None]})
        build_data_structure(d, 'authors[n]')
        self.assertEqual(d, {'authors': [None, None]})

        d = dict()
        build_data_structure(d, 'a[0].b[n].c.d[n]')
        self.assertEqual(d, {'a': [{'b': [{'c': {'d': [None]}}]}]})


class BibFieldDictUnitTest(unittest.TestCase):
    """
    Test class for bibfield base dictionary
    """

    def test_bibfielddict(self):
        """BibFieldDict - Unit Test"""
        import random
        from invenio.bibfield_utils import BibFieldDict
        d = BibFieldDict()
        d['foo'] = {'a': 'world', 'b': 'hello'}
        d['a'] = [{'b': 1}, {'b': 2}, {'b': 3}]
        d['_c'] = 1
        d['_cc'] = random.random()

        d['__do_not_cache'].append('_cc')
        d['__calculated_functions']['_c'] = "random.random()"
        d['__calculated_functions']['_cc'] = "random.random()"
        d['__aliases']['aa'] = 'a'

        self.assertTrue(len(d.keys()) == 7)
        self.assertTrue('foo' in d)
        self.assertTrue('a.b' in d)

        self.assertEqual(d['foo'], {'a': 'world', 'b': 'hello'})
        self.assertEqual(d['a'], d.get('a'))
        self.assertEqual(d['a[-1].b'], 3)

        self.assertEqual(d['a'], d['aa'])
        self.assertEqual(d['a[1].b'], d['aa[1].b'])

        self.assertEqual(d['_c'], 1)
        self.assertNotEqual(d['_c'], d.get('_c', reset_cache=True))

        self.assertNotEqual(d['_cc'], 1)
        self.assertNotEqual(d['_cc'], d.get('_cc'))

        #Python 2.5 or higher
        #self.assertEqual('hello world!', d.get('foo', formatstring="{0[b]} {0[a]}!"))

        def dummy(s):
            return s.upper()
        self.assertEqual('HELLO', d.get('foo.b', formatfunction=dummy))


TEST_SUITE = make_test_suite(BibFieldCoolListDictUnitTests, BibFieldUtilsUnitTests, BibFieldDictUnitTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
