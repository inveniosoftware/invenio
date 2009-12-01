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

"""Unit tests for the urlutils module."""

__revision__ = "$Id$"

import unittest

from invenio import urlutils
from invenio.testutils import make_test_suite, run_test_suite

class TestWashUrlArgument(unittest.TestCase):
    def test_wash_url_argument(self):
        """urlutils - washing of URL arguments"""
        self.assertEqual(1,
                         urlutils.wash_url_argument(['1'], 'int'))
        self.assertEqual("1",
                         urlutils.wash_url_argument(['1'], 'str'))
        self.assertEqual(['1'],
                         urlutils.wash_url_argument(['1'], 'list'))
        self.assertEqual(0,
                         urlutils.wash_url_argument('ellis', 'int'))
        self.assertEqual("ellis",
                         urlutils.wash_url_argument('ellis', 'str'))
        self.assertEqual(["ellis"],
                         urlutils.wash_url_argument('ellis', 'list'))
        self.assertEqual(0,
                         urlutils.wash_url_argument(['ellis'], 'int'))
        self.assertEqual("ellis",
                         urlutils.wash_url_argument(['ellis'], 'str'))
        self.assertEqual(["ellis"],
                         urlutils.wash_url_argument(['ellis'], 'list'))

TEST_SUITE = make_test_suite(TestWashUrlArgument)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
