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

"""Unit tests for the user handling library."""

__revision__ = "$Id$"

import unittest

from invenio import external_authentication_cern as cern

class ExternalAuthenticationCernTest(unittest.TestCase):
    """Test functions related to the CERN authentication."""

    def setUp(self):
        # pylint: disable-msg=C0103
        """setting up helper variables for tests"""
        self.username, self.userpwd, self.useremail = \
                open('demopwd.cfg', 'r').read().split(':', 2)
        self.cern = cern.ExternalAuthCern()

    def test_auth_user_ok(self):
        """external CERN - authorizing user through CERN system: should pass"""
        self.assertEqual(self.cern.auth_user(self.username, self.userpwd), \
                self.useremail)

    def test_auth_user_fail(self):
        """external CERN - authorizing user through CERN system: should fail"""
        self.assertEqual(self.cern.auth_user('patata', 'patata'), None)

    def test_fetch_user_groups_membership(self):
        """external CERN - fetching user group membership at CERN"""
        self.assertNotEqual(self.cern.fetch_user_groups_membership(self.useremail), 0)
        self.assertEqual(self.cern.fetch_user_groups_membership('patata'), {})

    def test_fetch_user_preferences(self):
        """external CERN - fetching user setting from CERN"""
        self.assertEqual(self.cern.fetch_user_preferences(self.username, self.userpwd)['email'], self.useremail)
        #self.assertRaises(KeyError, self.cern.fetch_user_preferences('patata', 'patata')['email'])

def create_test_suite():
    """Return test suite for the user handling."""
    return unittest.TestSuite((unittest.makeSuite(
        ExternalAuthenticationCernTest,'test'),))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())


