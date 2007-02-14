# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

"""Unit tests for the user handling library."""

__revision__ = "$Id$"

import unittest

class WebGroupTests(unittest.TestCase):
    """Test functions related to the WebGroup usage."""

    def setUp(self):
        """Nothing yet."""
        pass

    def test_set(self):
        """webgroup - test fancy usage of set (differences among Python versions)"""
        # These should succeed:
        self.failUnless(set([1,2,3]))
        self.assertEqual(set([1,2,3]) - set([3,4,5]), set([1,2]))
        self.assertEqual(set([1,2,3,3]), set([1,2,3]))
        self.assertEqual(set([1,2,3]), set([3,2,1]))
        self.assertEqual(set([1,2,3]) & set([2,3,4]), set([2,3]))
        self.assertEqual(set([1,2,3]) | set([2,3,4]), set([1,2,3,4]))
        self.assertEqual(set([1,2,3]), set([3,2,1]))

def create_test_suite():
    """Return test suite for the user handling."""
    return unittest.TestSuite((unittest.makeSuite(
        WebGroupTests,'test'),
                               ))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())
