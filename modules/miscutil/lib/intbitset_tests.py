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
        set1 = intbitset([30,10,20])
        self.assertEqual(list(set1), [10,20,30])

    def test_set_intersection(self):
        """intbitset - set intersection"""
        lst1 = [10,20,30]
        lst2 = [20,30,40,50,70]
        set1 = intbitset(lst1)
        set2 = intbitset(lst2)
        setx = set1 & set2
        self.assertEqual(list(set1), lst1)
        self.assertEqual(list(set2), lst2)
        self.assertEqual(list(setx), [20,30])

    def test_set_union(self):
        """intbitset - set union"""
        lst1 = [10,20,30]
        lst2 = [20,30,40,50,70]
        set1 = intbitset(lst1)
        set2 = intbitset(lst2)
        setx = set1 | set2
        self.assertEqual(list(set1), lst1)
        self.assertEqual(list(set2), lst2)
        self.assertEqual(list(setx), [10,20,30,40,50,70])

    def test_set_difference(self):
        """intbitset - set difference"""
        lst1 = [10,20,30]
        lst2 = [20,30,40,50,70]
        set1 = intbitset(lst1)
        set2 = intbitset(lst2)
        setx = set1 - set2
        self.assertEqual(list(set1), lst1)
        self.assertEqual(list(set2), lst2)
        self.assertEqual(list(setx), [10])

def create_test_suite():
    """Return test suite for the intbitset data structure."""
    return unittest.TestSuite((
        unittest.makeSuite(IntBitSetTest,'test'),
        ))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())

