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

"""Unit tests for dateutils library."""

__revision__ = "$Id$"

import unittest
import dateutils

class ConvertDateCVSTest(unittest.TestCase):
    """
    Testing conversion of CVS dates.
    """
    
    def test_convert_good_cvsdate(self):
        """dateutils - conversion of good CVS dates"""
        # here we have to use '$' + 'Date...' here, otherwise the CVS
        # commit would erase this time format to put commit date:
        datecvs = "$" + "Date: 2006/09/21 10:07:22" + "$"
        datestruct_beginning_expected = (2006, 9, 21, 10, 7, 22)
        self.assertEqual(dateutils.convert_datecvs_to_datestruct(datecvs)[:6],
                         datestruct_beginning_expected)

    def test_convert_bad_cvsdate(self):
        """dateutils - conversion of bad CVS dates"""
        # here we have to use '$' + 'Date...' here, otherwise the CVS
        # commit would erase this time format to put commit date:
        datecvs = "$" + "Date: 2006/AA/21 10:07:22" + "$"
        datestruct_beginning_expected = (0, 0, 0, 0, 0, 0)
        self.assertEqual(dateutils.convert_datecvs_to_datestruct(datecvs)[:6],
                         datestruct_beginning_expected)

def create_test_suite():
    """
    Return test suite for the dateutils.
    """
    return unittest.TestSuite((unittest.makeSuite(\
        ConvertDateCVSTest, 'test'),
                               ))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())
