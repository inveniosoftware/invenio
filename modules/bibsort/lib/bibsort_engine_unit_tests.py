## -*- mode: python; coding: utf-8; -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012 CERN.
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

"""Testing module for BibSort Engine"""

import unittest

from invenio.bibsort_engine import perform_modify_record, \
    perform_insert_record, perform_delete_record, \
    binary_search
from invenio.testutils import make_test_suite, run_test_suite


class TestBibSort(unittest.TestCase):
    """Test BibSort."""

    def test_perform_modify_record(self):
        """bibsort - testing perform_modify_record"""
        data_dict = {1:'a', 2:'c', 3:'e', 4:'g', 5:'i', 6:'k', 7:'s'}
        data_dict_ordered = {1:8, 2:16, 3:24, 4:32, 5:40, 6:48, 7:56}
        data_list_sorted = [1, 2, 3, 4, 5, 6, 7]
        spacing = 8

        # new value to be inserted somewhere in the middle (to the right)
        new_value = 'j'
        recid = 2
        self.assertEqual(4, perform_modify_record(data_dict, data_dict_ordered, data_list_sorted, new_value, recid, spacing))
        self.assertEqual([1, 3, 4, 5, 2, 6, 7], data_list_sorted)
        self.assertEqual({1:8, 2:44, 3:24, 4:32, 5:40, 6:48, 7:56}, data_dict_ordered)
        self.assertEqual({1:'a', 2:'j', 3:'e', 4:'g', 5:'i', 6:'k', 7:'s'}, data_dict)

        # new value to be inserted at the end (to the right)
        new_value = 'u'
        recid = 3
        self.assertEqual(6, perform_modify_record(data_dict, data_dict_ordered, data_list_sorted, new_value, recid, spacing))
        self.assertEqual([1, 4, 5, 2, 6, 7, 3], data_list_sorted)
        self.assertEqual({1:8, 2:44, 3:64, 4:32, 5:40, 6:48, 7:56}, data_dict_ordered)
        self.assertEqual({1:'a', 2:'j', 3:'u', 4:'g', 5:'i', 6:'k', 7:'s'}, data_dict)

        # new value to be inserted in the same place as the old one
        new_value = 'b'
        recid = 1
        self.assertEqual(0, perform_modify_record(data_dict, data_dict_ordered, data_list_sorted, new_value, recid, spacing))
        self.assertEqual([1, 4, 5, 2, 6, 7, 3], data_list_sorted)
        self.assertEqual({1:16, 2:44, 3:64, 4:32, 5:40, 6:48, 7:56}, data_dict_ordered)
        self.assertEqual({1:'b', 2:'j', 3:'u', 4:'g', 5:'i', 6:'k', 7:'s'}, data_dict)

        #new value to be inserted in the beginning (to the left)
        new_value = 'a'
        recid = 6
        self.assertEqual(0, perform_modify_record(data_dict, data_dict_ordered, data_list_sorted, new_value, recid, spacing))
        self.assertEqual([6, 1, 4, 5, 2, 7, 3], data_list_sorted)
        self.assertEqual({1:16, 2:44, 3:64, 4:32, 5:40, 6:8, 7:56}, data_dict_ordered)
        self.assertEqual({1:'b', 2:'j', 3:'u', 4:'g', 5:'i', 6:'a', 7:'s'}, data_dict)

        #new value to be inserted somewhere in the middle (to the left)
        new_value = 'd'
        recid = 5
        self.assertEqual(2, perform_modify_record(data_dict, data_dict_ordered, data_list_sorted, new_value, recid, spacing))
        self.assertEqual([6, 1, 5, 4, 2, 7, 3], data_list_sorted)
        self.assertEqual({1:16, 2:44, 3:64, 4:32, 5:24, 6:8, 7:56}, data_dict_ordered)
        self.assertEqual({1:'b', 2:'j', 3:'u', 4:'g', 5:'d', 6:'a', 7:'s'}, data_dict)

    def test_perform_insert_record(self):
        """bibsort - testing perform_insert_record"""
        data_dict = {1:'b', 2:'c', 3:'e', 4:'g', 5:'i', 6:'k', 7:'s'}
        data_dict_ordered = {1:8, 2:16, 3:24, 4:32, 5:40, 6:48, 7:56}
        data_list_sorted = [1, 2, 3, 4, 5, 6, 7]
        spacing = 8

        # new value to be inserted somewhere in the middle
        new_value = 'j'
        recid = 100
        self.assertEqual(5, perform_insert_record(data_dict, data_dict_ordered, data_list_sorted, new_value, recid, spacing))
        self.assertEqual([1, 2, 3, 4, 5, 100, 6, 7], data_list_sorted)
        self.assertEqual({1:8, 2:16, 3:24, 4:32, 5:40, 6:48, 7:56, 100:44}, data_dict_ordered)
        self.assertEqual({1:'b', 2:'c', 3:'e', 4:'g', 5:'i', 6:'k', 7:'s', 100:'j'}, data_dict)

        # new value to be inserted in the beginning
        new_value = 'a'
        recid = 101
        self.assertEqual(0, perform_insert_record(data_dict, data_dict_ordered, data_list_sorted, new_value, recid, spacing))
        self.assertEqual([101, 1, 2, 3, 4, 5, 100, 6, 7], data_list_sorted)
        self.assertEqual({1:8, 2:16, 3:24, 4:32, 5:40, 6:48, 7:56, 100:44, 101:4}, data_dict_ordered)
        self.assertEqual({1:'b', 2:'c', 3:'e', 4:'g', 5:'i', 6:'k', 7:'s', 100:'j', 101:'a'}, data_dict)

        # new value to be inserted in the end
        new_value = 'u'
        recid = 102
        self.assertEqual(9, perform_insert_record(data_dict, data_dict_ordered, data_list_sorted, new_value, recid, spacing))
        self.assertEqual([101, 1, 2, 3, 4, 5, 100, 6, 7, 102], data_list_sorted)
        self.assertEqual({1:8, 2:16, 3:24, 4:32, 5:40, 6:48, 7:56, 100:44, 101:4, 102:64}, data_dict_ordered)
        self.assertEqual({1:'b', 2:'c', 3:'e', 4:'g', 5:'i', 6:'k', 7:'s', 100:'j', 101:'a', 102:'u'}, data_dict)

        # new value to be inserted before the last element
        new_value = 't'
        recid = 103
        self.assertEqual(9, perform_insert_record(data_dict, data_dict_ordered, data_list_sorted, new_value, recid, spacing))
        self.assertEqual([101, 1, 2, 3, 4, 5, 100, 6, 7, 103, 102], data_list_sorted)
        self.assertEqual({1:8, 2:16, 3:24, 4:32, 5:40, 6:48, 7:56, 100:44, 101:4, 102:64, 103:60}, data_dict_ordered)
        self.assertEqual({1:'b', 2:'c', 3:'e', 4:'g', 5:'i', 6:'k', 7:'s', 100:'j', 101:'a', 102:'u', 103:'t'}, data_dict)

    def test_perform_delete_record(self):
        """bibsort - testing perform_delete_record"""
        data_dict = {1:'b', 2:'c', 3:'e', 4:'g', 5:'i', 6:'k', 7:'s'}
        data_dict_ordered = {1:8, 2:16, 3:24, 4:32, 5:40, 6:48, 7:56}
        data_list_sorted = [1, 2, 3, 4, 5, 6, 7]

        # delete in the middle
        recid = 3
        self.assertEqual(1, perform_delete_record(data_dict, data_dict_ordered, data_list_sorted, recid))
        self.assertEqual([1, 2, 4, 5, 6, 7], data_list_sorted)
        self.assertEqual({1:8, 2:16, 4:32, 5:40, 6:48, 7:56}, data_dict_ordered)
        self.assertEqual({1:'b', 2:'c', 4:'g', 5:'i', 6:'k', 7:'s'}, data_dict)

    def test_binary_search_odd_list(self):
        """bibsort -testing binary_search function, list with odd number of elements"""
        data_dict = {1:'b', 2:'d', 3:'e', 4:'g', 5:'i', 6:'k', 7:'s'}
        sorted_list = [1, 2, 3, 4, 5, 6, 7]

        #test insertion somewhere in the middle
        self.assertEqual(1, binary_search(sorted_list, 'c', data_dict))

        #test insertion at the beginning
        self.assertEqual(7, binary_search(sorted_list, 'u', data_dict))

        #testinsertion at the end
        self.assertEqual(0, binary_search(sorted_list, 'a', data_dict))

    def test_binary_search_even_list(self):
        """bibsort - testing binary_search function, list with even number of elements"""
        data_dict = {1:'b', 2:'d', 3:'e', 4:'g', 5:'i', 6:'k', 7:'s', 8: 'u'}
        sorted_list = [1, 2, 3, 4, 5, 6, 7, 8]

        #test insertion somewhere in the middle
        self.assertEqual(1, binary_search(sorted_list, 'c', data_dict))

        #test insertion somewhere in the middle
        self.assertEqual(7, binary_search(sorted_list, 't', data_dict))

        #test insertion at the beginning
        self.assertEqual(8, binary_search(sorted_list, 'v', data_dict))

        #testinsertion at the end
        self.assertEqual(0, binary_search(sorted_list, 'a', data_dict))

TEST_SUITE = make_test_suite(TestBibSort,
                             )

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
