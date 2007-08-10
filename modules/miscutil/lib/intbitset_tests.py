# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

"""Unit tests for the intbitset data structure."""

__revision__ = "$Id$"

import unittest

from invenio.intbitset import intbitset

class IntBitSetTest(unittest.TestCase):
    """Test functions related to intbitset data structure."""

    def test_list_dump(self):
        """intbitset - list dump"""
        set1 = intbitset([30, 10, 20])
        self.assertEqual(list(set1), [10, 20, 30])

    def test_ascii_bit_dump(self):
        """intbitset - ascii bit dump"""
        set1 = intbitset([30, 10, 20])
        self.assertEqual(set1.strbits(), "0000000000100000000010000000001")

    def test_marshalling(self):
        """intbitset - marshalling"""
        # serialize an intbitset:
        set1 = intbitset([30, 10, 20])
        str1 = set1.fastdump()
        # load it back via constructor:
        set2 = intbitset(str1)
        # load it back via fastload:
        set3 = intbitset()
        set3.fastload(str1)
        # compare results:
        self.assertEqual(list(set1), [10, 20, 30])
        self.assertEqual(list(set2), [10, 20, 30])
        self.assertEqual(list(set3), [10, 20, 30])

    def test_set_intersection(self):
        """intbitset - set intersection"""
        lst1 = [10, 20, 30]
        lst2 = [20, 30, 40, 50, 70]
        set1 = intbitset(lst1)
        set2 = intbitset(lst2)
        setx = set1 & set2
        self.assertEqual(list(set1), lst1)
        self.assertEqual(list(set2), lst2)
        self.assertEqual(list(setx), [20, 30])

    def test_set_intersection_in_place(self):
        """intbitset - set intersection in place"""
        lst1 = [10, 20, 30]
        lst2 = [20, 30, 40, 50, 70]
        set1 = intbitset(lst1)
        set2 = intbitset(lst2)
        set1 &= set2
        self.assertEqual(list(set1), [20, 30])
        self.assertEqual(list(set2), lst2)

    def test_set_union(self):
        """intbitset - set union"""
        lst1 = [10, 20, 30]
        lst2 = [20, 30, 40, 50, 70]
        set1 = intbitset(lst1)
        set2 = intbitset(lst2)
        setx = set1 | set2
        self.assertEqual(list(set1), lst1)
        self.assertEqual(list(set2), lst2)
        self.assertEqual(list(setx), [10, 20, 30, 40, 50, 70])

    def test_set_union_in_place(self):
        """intbitset - set union in place"""
        lst1 = [10, 20, 30]
        lst2 = [20, 30, 40, 50, 70]
        set1 = intbitset(lst1)
        set2 = intbitset(lst2)
        set1 |= set2
        self.assertEqual(list(set1), [10, 20, 30, 40, 50, 70])
        self.assertEqual(list(set2), lst2)

    def test_set_difference(self):
        """intbitset - set difference"""
        lst1 = [10, 20, 30]
        lst2 = [20, 30, 40, 50, 70]
        set1 = intbitset(lst1)
        set2 = intbitset(lst2)
        setx = set1 - set2
        self.assertEqual(list(set1), lst1)
        self.assertEqual(list(set2), lst2)
        self.assertEqual(list(setx), [10])

    def test_set_difference_in_place(self):
        """intbitset - set difference in place"""
        lst1 = [10, 20, 30]
        lst2 = [20, 30, 40, 50, 70]
        set1 = intbitset(lst1)
        set2 = intbitset(lst2)
        set1 -= set2
        self.assertEqual(list(set1), [10])
        self.assertEqual(list(set2), lst2)

    def test_set_emptyness(self):
        """intbitset - set emptyness"""
        set1 = intbitset()
        set2 = intbitset(universe=True)
        set3 = intbitset([70])
        set4 = intbitset([70], universe=True)
        self.failUnless(not set1.__nonzero__())
        self.failUnless(set2.__nonzero__())
        self.failUnless(set3.__nonzero__())
        self.failUnless(set4.__nonzero__())

    def test_set_clear(self):
        """intbitset - clearing"""
        set1 = intbitset([10, 20, 30, 70])
        set1.clear()
        self.assertEqual(list(set1), [])
        self.failUnless(not set1.__nonzero__())

    def test_set_universe(self):
        """intbitset - universe"""
        set1 = intbitset(universe=True)
        set2 = intbitset([10, 20, 30], universe=True)
        self.failUnless(0 in set1)
        self.failUnless(100 in set1)
        self.failUnless(10000 in set1)
        self.failIf(0 in set2)
        self.failUnless(10 in set2)
        self.failIf(15 in set2)
        self.failUnless(30 in set2)
        self.failUnless(100 in set2)
        self.failUnless(10000 in set2)
        self.failUnless('...' in str(set1))
        self.failUnless('...' in str(set2))

    def test_set_repr(self):
        """intbitset - set representation"""
        set1 = intbitset()
        set2 = intbitset([10, 20, 30])
        set3 = intbitset([10, 20, 30], universe=True)
        self.assertEqual(set1, eval(repr(set1)))
        self.assertEqual(set2, eval(repr(set2)))
        self.assertEqual(set3, eval(repr(set3)))

    def test_set_cmp(self):
        """intbitset - set comparison"""
        set1 = intbitset([10, 20, 30, 70])
        set2 = intbitset([20, 30, 40, 70])
        set3 = intbitset(universe=True)
        self.failUnless(set1 != set2)
        self.failUnless(set1 != set3)
        self.failUnless(set2 != set3)
        self.failIf(set1 < set2)
        self.failIf(set1 > set2)
        self.failIf(set1 == set2)
        self.failUnless(set1 >= set1)
        self.failUnless(set1 >= (set1 & set2))
        self.failUnless(set1 <= (set1 | set2))
        self.failUnless(set1 <= set3)
        self.failUnless(set2 <= set3)
        self.failUnless(set1 < set3)
        self.failUnless(set2 < set3)

    def test_set_update_with_signs(self):
        """intbitset - set update with signs"""
        set1 = intbitset([10, 20, 30])
        dict1 = {20 : -1, 40 : 1}
        set1.update_with_signs(dict1)
        self.assertEqual(list(set1), [10, 30, 40])

def create_test_suite():
    """Return test suite for the intbitset data structure."""
    return unittest.TestSuite((
        unittest.makeSuite(IntBitSetTest, 'test'),
        ))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())

