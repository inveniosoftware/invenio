# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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

"""Unit tests for the user handling library."""

__revision__ = "$Id$"

import unittest

from invenio import webuser
from invenio.testutils import make_test_suite, run_test_suite
from invenio.dbquery import run_sql

class IsUserSuperAdminTests(unittest.TestCase):
    """Test functions related to the isUserSuperAdmin function."""
    def setUp(self):
        self.id_admin = run_sql('SELECT id FROM user WHERE nickname="admin"')[0][0]
        self.id_hyde = run_sql('SELECT id FROM user WHERE nickname="hyde"')[0][0]

    def test_isUserSuperAdmin_admin(self):
        """webuser - isUserSuperAdmin with admin"""
        self.failUnless(webuser.isUserSuperAdmin(webuser.collect_user_info(self.id_admin)))

    def test_isUserSuperAdmin_hyde(self):
        """webuser - isUserSuperAdmin with hyde"""
        self.failIf(webuser.isUserSuperAdmin(webuser.collect_user_info(self.id_hyde)))

TEST_SUITE = make_test_suite(IsUserSuperAdminTests)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)


