# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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
Test unit for the miscutil/datastructures module.
"""

from invenio.utils.datastructures import LazyDict, LaziestDict
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

class CallCounter(object):
    """Counts number of calls."""

    def __init__(self, populate):
        self.counter = 0
        self.populate = populate

    def __call__(self, *args, **kwargs):
        self.counter = self.counter + 1
        return self.populate(*args, **kwargs)


class TestLazyDictionaries(InvenioTestCase):
    """
    Lazy dictionaries TestSuite.
    """

    def test_lazy_dictionary(self):
        """Checks content of lazy dictionary and number of evaluations."""
        populate = CallCounter(lambda: {'foo': 'bar', 1: 11, 'empty': None})

        lazy_dict = LazyDict(populate)
        self.assertEqual(populate.counter, 0)

        self.assertEqual(lazy_dict['foo'], 'bar')
        self.assertEqual(populate.counter, 1)

        self.assertEqual(lazy_dict[1], 11)
        self.assertEqual(populate.counter, 1)

        self.assertEqual(lazy_dict['empty'], None)
        self.assertEqual(populate.counter, 1)

        # clear the cache
        lazy_dict.expunge()
        self.assertEqual(lazy_dict['foo'], 'bar')
        self.assertEqual(populate.counter, 2)

    def test_lazies_dictionary(self):
        populate = CallCounter(lambda k: {'foo': 'bar', 1: 11, 'empty': None}[k])

        laziest_dict = LaziestDict(populate)
        self.assertEqual(populate.counter, 0)

        self.assertEqual(laziest_dict['foo'], 'bar')
        self.assertEqual(laziest_dict.keys(), ['foo'])
        self.assertEqual(populate.counter, 1)

        self.assertEqual(laziest_dict[1], 11)
        self.assertEqual(laziest_dict.keys(), [1, 'foo'])
        self.assertEqual(populate.counter, 2)

        self.assertEqual(laziest_dict['empty'], None)
        self.assertEqual(laziest_dict.keys(), [1, 'foo', 'empty'])
        self.assertEqual(populate.counter, 3)

        # cached result will not cause new call
        self.assertEqual(laziest_dict['foo'], 'bar')
        self.assertEqual(populate.counter, 3)

        # not existing key cause new call (even multiple times)
        self.assertEqual(laziest_dict.get('does not exists', -1), -1)
        self.assertEqual(populate.counter, 4)
        self.assertEqual(laziest_dict.get('does not exists'), None)
        self.assertEqual(populate.counter, 5)


TEST_SUITE = make_test_suite(TestLazyDictionaries, )

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
