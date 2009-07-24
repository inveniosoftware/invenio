# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

__revision__ = "$Id$"

import unittest

from invenio.webcomment import calculate_start_date
from invenio.testutils import make_test_suite, run_test_suite

class TestCalculateStartDate(unittest.TestCase):
    """Test for calculating previous date."""

    def test_previous_year(self):
        """webcomment - calculate_start_date, values bigger than one year"""
        self.assert_(int(calculate_start_date('1y')[:4]) > 2007)
        self.assert_(int(calculate_start_date('13m')[:4]) > 2007)
        self.assert_(int(calculate_start_date('55w')[:4]) > 2007)
        self.assert_(int(calculate_start_date('370d')[:4]) > 2007)

    def test_with_random_values(self):
        """webcomment - calculate_start_date, various random values"""
        self.assert_(calculate_start_date('1d') > '2009-07-08 14:39:39')
        self.assert_(calculate_start_date('2w') > '2009-07-08 14:39:39')
        self.assert_(calculate_start_date('2w') > '2009-06-25 14:46:31')
        self.assert_(calculate_start_date('2y') > '2007-07-09 14:50:43')
        self.assert_(calculate_start_date('6m') > '2009-01-09 14:51:10')
        self.assert_(calculate_start_date('77d') > '2009-04-23 14:51:31')
        self.assert_(calculate_start_date('20d') > '2009-06-19 14:51:55')

TEST_SUITE = make_test_suite(TestCalculateStartDate)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
