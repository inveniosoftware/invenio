# -*- coding: utf-8 -*-
##
## $Id$
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

"""Unit tests for the user handling library."""

__revision__ = "$Id$"

import unittest

from invenio import webuser
from invenio.testutils import make_test_suite, run_test_suite
from invenio.dbquery import run_sql

class ApacheAuthenticationTests(unittest.TestCase):
    """Test functions related to the Apache authentication."""

    def test_auth_apache_user_p(self):
        """webuser - apache user password checking"""
        # These should succeed:
        self.assertEqual(True,
                         webuser.auth_apache_user_p('jekyll', 'j123ekyll'))
        self.assertEqual(True,
                         webuser.auth_apache_user_p('hyde', 'h123yde'))
        # Note: the following one should succeed even though the real
        # password is different, because crypt() looks at first 8
        # chars only:
        self.assertEqual(True,
                         webuser.auth_apache_user_p('jekyll', 'j123ekylx'))
        # Now some attempts that should fail:
        self.assertEqual(False,
                         webuser.auth_apache_user_p('jekyll', ''))
        self.assertEqual(False,
                         webuser.auth_apache_user_p('jekyll', 'h123yde'))
        self.assertEqual(False,
                         webuser.auth_apache_user_p('jekyll', 'aoeuidhtns'))
        self.assertEqual(False,
                         webuser.auth_apache_user_p('aoeui', ''))
        self.assertEqual(False,
                         webuser.auth_apache_user_p('aoeui', 'h123yde'))
        self.assertEqual(False,
                         webuser.auth_apache_user_p('aoeui', 'dhtns'))

    def test_auth_apache_user_in_groups(self):
        """webuser - apache user group membership checking"""
        self.assertEqual(['theses'],
          webuser.auth_apache_user_in_groups('jekyll'))
        self.assertEqual([],
          webuser.auth_apache_user_in_groups('hyde'))
        self.assertEqual([],
          webuser.auth_apache_user_in_groups('aoeui'))

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

TEST_SUITE = make_test_suite(ApacheAuthenticationTests, IsUserSuperAdminTests)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)


