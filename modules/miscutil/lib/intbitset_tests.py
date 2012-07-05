# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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

"""Unit tests for the intbitset data structure."""

__revision__ = "$Id$"

import unittest
import sys
import zlib
import os
import re

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

from invenio.intbitset import intbitset
from invenio.testutils import make_test_suite, run_test_suite
from invenio.config import CFG_TMPDIR

CFG_INTBITSET_BIG_EXAMPLE = open(os.path.join(CFG_TMPDIR, "intbitset_example.int")).read()

def _check_enough_ram():
    """
    Return if there is enough RAM, i.e. if free outputs more than 1G of ram.
    """
    from invenio.shellutils import run_shell_command
    try:
        return int(re.sub(r'\s+', ' ', run_shell_command("free")[1].splitlines()[1]).split(' ')[1]) > 1024 * 1024
    except:
        ## Are we really on Linux? Maybe on a BSD system?
        try:
            return int(run_shell_command("sysctl -n hw.memsize")[1]) > 1024 * 1024
        except:
            # Still no luck
            return False

CFG_ENOUGH_RAM = _check_enough_ram()

class IntBitSetTest(unittest.TestCase):
    """Test functions related to intbitset data structure."""
    def setUp(self):
        self.sets = [
            [10, 20],
            [10, 40],
            [60, 70],
            [60, 80],
            [10, 20, 60, 70],
            [10, 40, 60, 80],
            [1000],
            [10000],
            [23, 45, 67, 89, 110, 130, 174, 1002, 2132, 23434],
            [700, 2000],
        ]
        self.fncs_list = [
            (intbitset.__and__, set.__and__, int.__and__, False),
            (intbitset.__or__, set.__or__, int.__or__, False),
            (intbitset.__xor__, set.__xor__, int.__xor__, False),
            (intbitset.__sub__, set.__sub__, int.__sub__, False),
            (intbitset.__iand__, set.__iand__, int.__and__, True),
            (intbitset.__ior__, set.__ior__, int.__or__, True),
            (intbitset.__ixor__, set.__ixor__, int.__xor__, True),
            (intbitset.__isub__, set.__isub__, int.__sub__, True),
        ]

        self.cmp_list = [
            (intbitset.__eq__, set.__eq__, lambda x, y: cmp(x, y) == 0),
            (intbitset.__ge__, set.__ge__, lambda x, y: cmp(x, y) >= 0),
            (intbitset.__gt__, set.__gt__, lambda x, y: cmp(x, y) > 0),
            (intbitset.__le__, set.__le__, lambda x, y: cmp(x, y) <= 0),
            (intbitset.__lt__, set.__lt__, lambda x, y: cmp(x, y) < 0),
            (intbitset.__ne__, set.__ne__, lambda x, y: cmp(x, y) != 0),
        ]

        self.big_examples = [list(intbitset(CFG_INTBITSET_BIG_EXAMPLE))]

        self.corrupted_strdumps = [
            "ciao",
            intbitset([2, 6000000]).strbits(),
            "djflsdkfjsdljfsldkfjsldjlfk",
        ]

    def tearDown(self):
        del self.big_examples
        del self.corrupted_strdumps

    def _helper_sanity_test(self, intbitset1, msg=''):
        wordbitsize = intbitset1.get_wordbitsize()
        size1 = intbitset1.get_size()
        allocated1 = intbitset1.get_allocated()
        creator_list = intbitset1.extract_finite_list()
        up_to1 = creator_list and max(creator_list) or -1
        self.failUnless(up_to1 <= size1 * wordbitsize < allocated1 * wordbitsize, "up_to1=%s, size1=%s, allocated1=%s while testing %s during %s" % (up_to1, size1 * wordbitsize, allocated1 * wordbitsize, intbitset1, msg))
        tmp = intbitset(intbitset1.fastdump())
        size2 = tmp.get_size()
        allocated2 = tmp.get_allocated()
        creator_list = tmp.extract_finite_list()
        up_to2 = creator_list and max(creator_list) or -1
        self.failUnless(up_to2 <= size2 * wordbitsize < allocated2 * wordbitsize, "After serialization up_to2=%s, size2=%s, allocated2=%s while testing %s during %s" % (up_to2, size2 * wordbitsize, allocated2 * wordbitsize, intbitset1, msg))


    def _helper_test_via_fncs_list(self, fncs, intbitset1, intbitset2):
        orig1 = intbitset(intbitset1)
        orig2 = intbitset(intbitset2)

        msg = "Testing %s(%s, %s)" % (fncs[0].__name__, repr(intbitset1), repr(intbitset2))

        trailing1 = intbitset1.is_infinite()
        trailing2 = intbitset2.is_infinite()

        if fncs[3]:
            fncs[0](intbitset1, intbitset2)
            trailing1 = fncs[2](trailing1, trailing2) > 0
            up_to = intbitset1.extract_finite_list() and max(intbitset1.extract_finite_list()) or -1
        else:
            intbitset3 = fncs[0](intbitset1, intbitset2)
            trailing3 = fncs[2](trailing1, trailing2) > 0
            up_to = intbitset3.extract_finite_list() and max(intbitset3.extract_finite_list()) or -1

        set1 = set(orig1.extract_finite_list(up_to))
        set2 = set(orig2.extract_finite_list(up_to))

        if fncs[3]:
            fncs[1](set1, set2)
        else:
            set3 = fncs[1](set1, set2)

        self._helper_sanity_test(intbitset1, msg)
        self._helper_sanity_test(intbitset2, msg)

        if fncs[3]:
            self.assertEqual(set1 & set(intbitset1.extract_finite_list(up_to)), set(intbitset1.extract_finite_list(up_to)), "%s not equal to %s after executing %s(%s, %s)" % (set1, set(intbitset1.extract_finite_list(up_to)), fncs[0].__name__, repr(orig1), repr(orig2)))
            self.assertEqual(set1 | set(intbitset1.extract_finite_list(up_to)), set1, "%s not equal to %s after executing %s(%s, %s)" % (set1, set(intbitset1.extract_finite_list(up_to)), fncs[0].__name__, repr(orig1), repr(orig2)))
            self.assertEqual(trailing1, intbitset1.is_infinite(), "%s is not %s as it is supposed to be after executing %s(%s, %s)" % (intbitset1, trailing1 and 'infinite' or 'finite', fncs[0].__name__, repr(orig1), repr(orig2)))
        else:
            self._helper_sanity_test(intbitset3, msg)
            self.assertEqual(set3 & set(intbitset3.extract_finite_list(up_to)), set(intbitset3.extract_finite_list(up_to)), "%s not equal to %s after executing %s(%s, %s)" % (set3, set(intbitset3.extract_finite_list(up_to)), fncs[0].__name__, repr(orig1), repr(orig2)))
            self.assertEqual(set3 | set(intbitset3.extract_finite_list(up_to)), set3, "%s not equal to %s after executing %s(%s, %s)" % (set3, set(intbitset3.extract_finite_list(up_to)), fncs[0].__name__, repr(orig1), repr(orig2)))
            self.assertEqual(trailing3, intbitset3.is_infinite(), "%s is not %s as it is supposed to be after executing %s(%s, %s)" % (intbitset3, trailing3 and 'infinite' or 'finite', fncs[0].__name__, repr(orig1), repr(orig2)))


    def _helper_test_normal_set(self, fncs):
        for set1 in self.sets:
            for set2 in self.sets:
                self._helper_test_via_fncs_list(fncs, intbitset(set1), intbitset(set2))

    def _helper_test_empty_set(self, fncs):
        for set1 in self.sets:
            self._helper_test_via_fncs_list(fncs, intbitset(set1), intbitset([]))
            self._helper_test_via_fncs_list(fncs, intbitset([]), intbitset(set1))
        self._helper_test_via_fncs_list(fncs, intbitset([]), intbitset([]))

    def _helper_test_inifinite_set(self, fncs):
        for set1 in self.sets:
            for set2 in self.sets:
                self._helper_test_via_fncs_list(fncs, intbitset(set1), intbitset(set2, trailing_bits=True))
                self._helper_test_via_fncs_list(fncs, intbitset(set1, trailing_bits=True), intbitset(set2))
                self._helper_test_via_fncs_list(fncs, intbitset(set1, trailing_bits=True), intbitset(set2, trailing_bits=True))

    def _helper_test_infinite_vs_empty(self, fncs):
        for set1 in self.sets:
            self._helper_test_via_fncs_list(fncs, intbitset(set1, trailing_bits=True), intbitset([]))
            self._helper_test_via_fncs_list(fncs, intbitset([]), intbitset(set1, trailing_bits=True))
        self._helper_test_via_fncs_list(fncs, intbitset([]), intbitset(trailing_bits=True))
        self._helper_test_via_fncs_list(fncs, intbitset(trailing_bits=True), intbitset([]))


    def test_set_intersection(self):
        """intbitset - set intersection, normal set"""
        self._helper_test_normal_set(self.fncs_list[0])

    def test_set_intersection_empty(self):
        """intbitset - set intersection, empty set"""
        self._helper_test_empty_set(self.fncs_list[0])

    def test_set_intersection_infinite(self):
        """intbitset - set intersection, infinite set"""
        self._helper_test_inifinite_set(self.fncs_list[0])

    def test_set_intersection_infinite_empty(self):
        """intbitset - set intersection, infinite vs empty"""
        self._helper_test_infinite_vs_empty(self.fncs_list[0])

    def test_set_union(self):
        """intbitset - set union, normal set"""
        self._helper_test_normal_set(self.fncs_list[1])

    def test_set_union_empty(self):
        """intbitset - set union, empty set"""
        self._helper_test_empty_set(self.fncs_list[1])

    def test_set_union_infinite(self):
        """intbitset - set union, infinite set"""
        self._helper_test_inifinite_set(self.fncs_list[1])

    def test_set_union_infinite_empty(self):
        """intbitset - set union, infinite vs empty"""
        self._helper_test_infinite_vs_empty(self.fncs_list[1])

    def test_set_symmetric_difference(self):
        """intbitset - set symmetric difference, normal set"""
        self._helper_test_normal_set(self.fncs_list[2])

    def test_set_symmetric_difference_empty(self):
        """intbitset - set symmetric difference, empty set"""
        self._helper_test_empty_set(self.fncs_list[2])

    def test_set_symmetric_difference_infinite(self):
        """intbitset - set symmetric difference, infinite set"""
        self._helper_test_inifinite_set(self.fncs_list[2])

    def test_set_symmetric_difference_infinite_empty(self):
        """intbitset - set symmetric difference, infinite vs empty"""
        self._helper_test_infinite_vs_empty(self.fncs_list[2])

    def test_set_difference(self):
        """intbitset - set difference, normal set"""
        self._helper_test_normal_set(self.fncs_list[3])

    def test_set_difference_empty(self):
        """intbitset - set difference, empty set"""
        self._helper_test_empty_set(self.fncs_list[3])

    def test_set_difference_infinite(self):
        """intbitset - set difference, infinite set"""
        self._helper_test_inifinite_set(self.fncs_list[3])

    def test_set_difference_infinite_empty(self):
        """intbitset - set difference, infinite vs empty"""
        self._helper_test_infinite_vs_empty(self.fncs_list[3])

    def test_set_intersection_in_place(self):
        """intbitset - set intersection, normal set in place"""
        self._helper_test_normal_set(self.fncs_list[4])

    def test_set_intersection_empty_in_place(self):
        """intbitset - set intersection, empty set in place"""
        self._helper_test_empty_set(self.fncs_list[4])

    def test_set_intersection_infinite_in_place(self):
        """intbitset - set intersection, infinite set in place"""
        self._helper_test_inifinite_set(self.fncs_list[4])

    def test_set_intersection_infinite_empty_in_place(self):
        """intbitset - set intersection, infinite vs empty in place"""
        self._helper_test_infinite_vs_empty(self.fncs_list[4])

    def test_set_union_in_place(self):
        """intbitset - set union, normal set in place"""
        self._helper_test_normal_set(self.fncs_list[5])

    def test_set_union_empty_in_place(self):
        """intbitset - set union, empty set in place"""
        self._helper_test_empty_set(self.fncs_list[5])

    def test_set_union_infinite_in_place(self):
        """intbitset - set union, infinite set in place"""
        self._helper_test_inifinite_set(self.fncs_list[5])

    def test_set_union_infinite_empty_in_place(self):
        """intbitset - set union, infinite vs empty in place"""
        self._helper_test_infinite_vs_empty(self.fncs_list[5])

    def test_set_symmetric_difference_in_place(self):
        """intbitset - set symmetric difference, normal set in place"""
        self._helper_test_normal_set(self.fncs_list[6])

    def test_set_symmetric_difference_empty_in_place(self):
        """intbitset - set symmetric difference, empty set in place"""
        self._helper_test_empty_set(self.fncs_list[6])

    def test_set_symmetric_difference_infinite_in_place(self):
        """intbitset - set symmetric difference, infinite set in place"""
        self._helper_test_inifinite_set(self.fncs_list[6])

    def test_set_symmetric_difference_infinite_empty_in_place(self):
        """intbitset - set symmetric difference, infinite vs empty in place"""
        self._helper_test_infinite_vs_empty(self.fncs_list[6])

    def test_set_difference_in_place(self):
        """intbitset - set difference, normal set in place"""
        self._helper_test_normal_set(self.fncs_list[7])

    def test_set_difference_empty_in_place(self):
        """intbitset - set difference, empty set in place"""
        self._helper_test_empty_set(self.fncs_list[7])

    def test_set_difference_infinite_in_place(self):
        """intbitset - set difference, infinite set in place"""
        self._helper_test_inifinite_set(self.fncs_list[7])

    def test_set_difference_infinite_empty_in_place(self):
        """intbitset - set difference, infinite vs empty in place"""
        self._helper_test_infinite_vs_empty(self.fncs_list[7])

    def test_list_dump(self):
        """intbitset - list dump"""
        for set1 in self.sets + [[]]:
            self.assertEqual(list(intbitset(set1)), set1)

    def test_ascii_bit_dump(self):
        """intbitset - ascii bit dump"""
        for set1 in self.sets + [[]]:
            tot = 0
            count = 0
            for bit in intbitset(set1).strbits():
                if bit == '0':
                    self.failIf(count in set1)
                elif bit == '1':
                    self.failIf(count not in set1)
                    tot += 1
                else:
                    self.fail()
                count += 1
            self.assertEqual(tot, len(set1))

    def test_tuple_of_tuples(self):
        """intbitset - support tuple of tuples"""
        for set1 in self.sets + [[]]:
            tmp_tuple = tuple([(elem, ) for elem in set1])
            self.assertEqual(list(intbitset(set1)), list(intbitset(tmp_tuple)))
        for set1 in self.sets + [[]]:
            tmp_tuple = tuple([(elem, ) for elem in set1])
            self.assertEqual(intbitset(set1, trailing_bits=True), intbitset(tmp_tuple, trailing_bits=True))

    def test_marshalling(self):
        """intbitset - marshalling"""
        for set1 in self.sets + [[]]:
            self.assertEqual(intbitset(set1), intbitset().fastload((intbitset(set1).fastdump())))
        for set1 in self.sets + [[]]:
            self.assertEqual(intbitset(set1, trailing_bits=True), intbitset().fastload(intbitset(set1, trailing_bits=True).fastdump()))

    def test_pickling(self):
        """intbitset - pickling"""
        import cPickle
        for set1 in self.sets + [[]]:
            self.assertEqual(intbitset(set1), cPickle.loads(cPickle.dumps(intbitset(set1), -1)))
        for set1 in self.sets + [[]]:
            self.assertEqual(intbitset(set1, trailing_bits=True), cPickle.loads(cPickle.dumps(intbitset(set1, trailing_bits=True), -1)))

    def test_set_emptiness(self):
        """intbitset - tests for emptiness"""
        for set1 in self.sets + [[]]:
            self.assertEqual(not set(set1), not intbitset(set1))

    def test_set_clear(self):
        """intbitset - clearing"""
        for set1 in self.sets + [[]]:
            intbitset1 = intbitset(set1)
            intbitset1.clear()
            self.assertEqual(list(intbitset1), [])
            intbitset1 = intbitset(set1, trailing_bits=True)
            intbitset1.clear()
            self.assertEqual(list(intbitset1), [])

    def test_set_repr(self):
        """intbitset - Pythonic representation"""
        if CFG_ENOUGH_RAM:
            big_examples = self.big_examples
        else:
            big_examples = []
        for set1 in self.sets + [[]] + big_examples:
            intbitset1 = intbitset(set1)
            self.assertEqual(intbitset1, eval(repr(intbitset1)))
        for set1 in self.sets + [[]] + big_examples:
            intbitset1 = intbitset(set1, trailing_bits=True)
            self.assertEqual(intbitset1, eval(repr(intbitset1)))

    def test_set_cmp(self):
        """intbitset - (non infinite) set comparison"""
        for set1 in self.sets + [[]]:
            for set2 in self.sets + [[]]:
                for op in self.cmp_list:
                    self.assertEqual(op[0](intbitset(set1), intbitset(set2)), op[1](set(set1), set(set2)), "Error in comparing %s %s with comparing function %s" % (set1, set2, op[0].__name__))

    def test_set_update_with_signs(self):
        """intbitset - set update with signs"""
        dict1 = {10 : -1, 20 : 1, 23 : -1, 27 : 1, 33 : -1, 56 : 1, 70 : -1, 74 : 1}
        for set1 in self.sets + [[]]:
            intbitset1 = intbitset(set1)
            intbitset1.update_with_signs(dict1)
            up_to = max(dict1.keys() + set1)
            for i in xrange(up_to + 1):
                if dict1.get(i, i in set1 and 1 or -1) == 1:
                    self.failUnless(i in intbitset1, "%s was not correctly updated from %s by %s" % (repr(intbitset1), repr(set1), repr(dict1)))
                else:
                    self.failIf(i in intbitset1, "%s was not correctly updated from %s by %s" % (repr(intbitset1), repr(set1), repr(dict1)))

    def test_set_cloning(self):
        """intbitset - set cloning"""
        import copy
        for set1 in self.sets + [[]]:
            intbitset1 = intbitset(set1)
            intbitset2 = intbitset(intbitset1)
            intbitset3 = copy.deepcopy(intbitset2)
            self._helper_sanity_test(intbitset1)
            self._helper_sanity_test(intbitset2)
            self._helper_sanity_test(intbitset3)
            self.assertEqual(intbitset1, intbitset2)
            self.assertEqual(intbitset1, intbitset3)

        for set1 in self.sets + [[]]:
            intbitset1 = intbitset(set1, trailing_bits=True)
            intbitset2 = intbitset(intbitset1)
            intbitset3 = copy.deepcopy(intbitset2)
            self._helper_sanity_test(intbitset1)
            self._helper_sanity_test(intbitset2)
            self._helper_sanity_test(intbitset3)
            self.assertEqual(intbitset1, intbitset2)
            self.assertEqual(intbitset1, intbitset3)

    def test_set_pop(self):
        """intbitset - set pop"""
        for set1 in self.sets + [[]]:
            intbitset1 = intbitset(set1)
            pythonlist1 = list(set1)
            while True:
                try:
                    res1 = pythonlist1.pop()
                except IndexError:
                    self.assertRaises(KeyError, intbitset1.pop)
                    self._helper_sanity_test(intbitset1)
                    break
                res2 = intbitset1.pop()
                self._helper_sanity_test(intbitset1)
                self.assertEqual(res1, res2)

    def test_set_getitem(self):
        """intbitset - __getitem__"""
        for set1 in self.sets + [[]]:
            intbitset1 = intbitset(set1)
            pythonlist1 = list(set1)
            for i in xrange(-2 * len(set1) - 2, 2 * len(set1) + 2):
                try:
                    res1 = pythonlist1[i]
                except IndexError:
                    self.assertRaises(IndexError, intbitset1.__getitem__, i)
                    continue
                res2 = intbitset1[i]
                self.assertEqual(res1, res2)

        for set1 in self.sets + [[]]:
            intbitset1 = intbitset(set1)
            pythonlist1 = list(set1)
            for start in xrange(-2 * len(set1) - 2, 2 * len(set1) + 2):
                for stop in xrange(-2 * len(set1) - 2, 2 * len(set1) + 2):
                    for step in xrange(1, 3):
                        res1 = pythonlist1[start:stop:step]
                        res2 = intbitset1[start:stop:step]
                        self.assertEqual(res1, list(res2), "Failure with set %s, start %s, stop %s, step %s, found %s, expected %s, indices: %s" % (set1, start, stop, step, list(res2), res1, slice(start, stop, step).indices(len(pythonlist1))))


    def test_set_iterator(self):
        """intbitset - set iterator"""
        for set1 in self.sets + [[]]:
            intbitset1 = intbitset(set1)
            self._helper_sanity_test(intbitset1)
            tmp_set1 = []
            for recid in intbitset1:
                self._helper_sanity_test(intbitset1)
                tmp_set1.append(recid)
            self._helper_sanity_test(intbitset1)
            self.assertEqual(set1, tmp_set1)

        for set1 in self.sets + [[]]:
            tmp_set1 = []
            for recid in intbitset(set1):
                tmp_set1.append(recid)
            self.assertEqual(set1, tmp_set1)

    def test_set_corruption(self):
        """intbitset - set corruption"""
        set1 = intbitset()
        for strdump in self.corrupted_strdumps:
            ## These should fail because they are not compressed
            self.assertRaises(ValueError, intbitset, strdump)
            self.assertRaises(ValueError, set1.fastload, strdump)
            strdump = zlib.compress(strdump)
            ## These should fail because they are not of the good
            ## length
            self.assertRaises(ValueError, intbitset, strdump)
            self.assertRaises(ValueError, set1.fastload, strdump)

    def test_set_consistence(self):
        """intbitset - set consistence"""
        tests = (
            (
                (20, 30, 1000, 40),
                'x\x9cc`\x10p``d\x18\x18\x80d/\x00*\xb6\x00S',
                'x\x9cc`\x10p`\x18(\xf0\x1f\x01\x00k\xe6\x0bF'
            ),
            (
                (20, 30, 1000, 41),
                'x\x9cc`\x10p``b\x18\x18\xc0\x88`\x02\x00+9\x00T',
                'x\x9cc`\x10p`\x18(\xf0\x1f\x01\x00k\xe6\x0bF'
            ),
            (
                (20, 30, 1001, 41),
                'x\x9cc`\x10p``b\x18\x18\x80d/\x00+D\x00U',
                'x\x9cc`\x10p`\x18(\xf0\xef?\x1c\x00\x00k\xdb\x0bE'
            )
        )
        for original, dumped, dumped_trails in tests:
            intbitset1 = intbitset(original)
            intbitset2 = intbitset(original, trailing_bits=True)
            intbitset3 = intbitset(dumped)
            intbitset4 = intbitset(dumped_trails)
            self._helper_sanity_test(intbitset1)
            self._helper_sanity_test(intbitset2)
            self._helper_sanity_test(intbitset3)
            self._helper_sanity_test(intbitset4)
            self.assertEqual(intbitset1.fastdump(), dumped)
            self.assertEqual(intbitset1, intbitset3)
            self.assertEqual(intbitset2.fastdump(), dumped_trails)
            self.assertEqual(intbitset2, intbitset4)

TEST_SUITE = make_test_suite(IntBitSetTest,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

