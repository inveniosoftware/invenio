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

from invenio import webuser

class ApacheAuthenticationTests(unittest.TestCase):
    """Test functions related to the Apache authentication."""

    def setUp(self):
        # pylint: disable-msg=C0103
        """setting up helper variables for tests"""
        self.apache_password_file = "demo-site-apache-user-passwords"
        self.apache_group_file = "demo-site-apache-user-groups"

    def test_auth_apache_user_p(self):
        """webuser - apache user password checking"""
        self.assertEqual(1,
                         webuser.auth_apache_user_p('jekyll', 'jekyll',
                                                    self.apache_password_file))
        self.assertEqual(1,
                         webuser.auth_apache_user_p('hyde', 'hyde',
                                                    self.apache_password_file))
        self.assertEqual(0,
                         webuser.auth_apache_user_p('jekyll', '',
                                                    self.apache_password_file))
        self.assertEqual(0,
                         webuser.auth_apache_user_p('jekyll', 'hyde',
                                                    self.apache_password_file))
        self.assertEqual(0,
                         webuser.auth_apache_user_p('aoeui', 'hyde',
                                                    self.apache_password_file))

    def test_auth_apache_user_in_groups(self):
        """webuser - apache user group membership checking""" 
        self.assertEqual(['theses'],
          webuser.auth_apache_user_in_groups('jekyll', self.apache_group_file))
        self.assertEqual([],
          webuser.auth_apache_user_in_groups('hyde', self.apache_group_file))
        self.assertEqual([],
          webuser.auth_apache_user_in_groups('aoeui', self.apache_group_file))
        
def create_test_suite():
    """Return test suite for the user handling."""
    return unittest.TestSuite((unittest.makeSuite(
        ApacheAuthenticationTests,'test'),
                               ))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())


