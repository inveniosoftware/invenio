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

def create_test_suite():
    """Return test suite for the intbitset data structure."""
    return unittest.TestSuite((
        unittest.makeSuite(IntBitSetTest, 'test'),
        ))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())

