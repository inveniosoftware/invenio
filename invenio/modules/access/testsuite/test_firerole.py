# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011, 2013 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Unit tests for the access_control_firerole library."""

__revision__ = "$Id$"


from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

acc_firerole_check_user = lazy_import('invenio.modules.access.firerole:acc_firerole_check_user')
compile_role_definition = lazy_import('invenio.modules.access.firerole:compile_role_definition')
deserialize = lazy_import('invenio.modules.access.firerole:deserialize')
serialize = lazy_import('invenio.modules.access.firerole:serialize')
collect_user_info = lazy_import('invenio.legacy.webuser:collect_user_info')


class AccessControlFireRoleTest(InvenioTestCase):
    """Test functions related to the firewall like role definitions."""

    def setUp(self):
        """setting up helper variables for tests"""
        self.user_info = {'email' : 'foo.bar@cern.ch', 'uid': 1000,
            'group' : ['patata', 'cetriolo'], 'remote_ip' : '127.0.0.1',
            'guest' : '0'}
        self.guest = collect_user_info(None)

    def test_compile_role_definition_empty(self):
        """firerole - compiling empty role definitions"""
        from invenio.modules.access.local_config import CFG_ACC_EMPTY_ROLE_DEFINITION_SER
        self.assertEqual(compile_role_definition(None),
                         deserialize(CFG_ACC_EMPTY_ROLE_DEFINITION_SER))

    def test_compile_role_definition_allow_any(self):
        """firerole - compiling allow any role definitions"""
        self.failUnless(serialize(compile_role_definition("allow any")))

    def test_compile_role_definition_deny_any(self):
        """firerole - compiling deny any role definitions"""
        self.failIf(serialize(compile_role_definition("deny any")))

    def test_compile_role_definition_literal_field(self):
        """firerole - compiling literal field role definitions"""
        self.failUnless(serialize(compile_role_definition(
            "allow email 'info@invenio-software.org'")))

    def test_compile_role_definition_not(self):
        """firerole - compiling not role definitions"""
        self.failUnless(serialize(compile_role_definition(
            "allow not email 'info@invenio-software.org'")))

    def test_compile_role_definition_group_field(self):
        """firerole - compiling group field role definitions"""
        self.failUnless(serialize(compile_role_definition(
            "allow groups 'patata'")))

    def test_compile_role_definition_regexp_field(self):
        """firerole - compiling regexp field role definitions"""
        self.failUnless(serialize(compile_role_definition(
            "allow email /.*@cern.ch/")))

    def test_compile_role_definition_literal_list(self):
        """firerole - compiling literal list role definitions"""
        self.failUnless(serialize(compile_role_definition(
            "allow email 'info@invenio-software.org', 'foo.bar@cern.ch'")))

    def test_compile_role_definition_more_rows(self):
        """firerole - compiling more rows role definitions"""
        self.failUnless(serialize(compile_role_definition(
            "allow email /.*@cern.ch/\nallow groups 'patata' "
            "# a comment\ndeny any")))

    def test_compile_role_definition_guest_field(self):
        """firerole - compiling guest field role definitions"""
        self.failUnless(serialize(compile_role_definition(
            "allow guest '1'")))

    def test_compile_role_definition_complex(self):
        """firerole - compiling complex role definitions"""
        self.failUnless(serialize(compile_role_definition(
            "allow email /.*@cern.ch/\nallow groups 'patata' "
            "# a comment\ndeny remote_ip '127.0.0.0/24'\ndeny any")))

    def test_compile_role_definition_with_date(self):
        """firerole - compiling date based role definitions"""
        from invenio.modules.access.errors import InvenioWebAccessFireroleError

        self.failUnless(serialize(compile_role_definition(
            "allow from '2010-11-11'")))
        self.failUnless(serialize(compile_role_definition(
            "allow until '2010-11-11'")))
        self.assertRaises(InvenioWebAccessFireroleError,
            compile_role_definition, "allow from '2010-11-11','2010-11-23'")
        self.assertRaises(InvenioWebAccessFireroleError,
            compile_role_definition, "allow from '2010-11'")

    def test_compile_role_definition_wrong(self):
        """firerole - compiling wrong role definitions"""
        from invenio.modules.access.errors import InvenioWebAccessFireroleError

        self.assertRaises(InvenioWebAccessFireroleError,
            compile_role_definition, "allow al")
        self.assertRaises(InvenioWebAccessFireroleError,
            compile_role_definition, "fgdfglk  g fgk")

    def test_deserialize(self):
        """firerole - deserializing"""
        self.assertEqual(compile_role_definition("allow any"),
            (True, ()))

    def test_firerole_literal_email(self):
        """firerole - firerole core testing literal email matching"""
        self.failUnless(acc_firerole_check_user(self.user_info,
            compile_role_definition("allow email 'info@invenio-software.org',"
                "'foo.bar@cern.ch'\ndeny any")))

    def test_firerole_regexp_email(self):
        """firerole - firerole core testing regexp email matching"""
        self.failUnless(acc_firerole_check_user(self.user_info,
            compile_role_definition("allow email /.*@cern.ch/\ndeny any")))

    def test_firerole_literal_group(self):
        """firerole - firerole core testing literal group matching"""
        self.failUnless(acc_firerole_check_user(self.user_info,
            compile_role_definition("allow groups 'patata'\ndeny any")))

    def test_firerole_ip_mask(self):
        """firerole - firerole core testing ip mask matching"""
        self.failUnless(acc_firerole_check_user(self.user_info,
            compile_role_definition("allow remote_ip '127.0.0.0/24'"
                "\ndeny any")))
        self.failIf(acc_firerole_check_user(self.guest,
            compile_role_definition("allow remote_ip '127.0.0.0/24'"
                "\ndeny any")))

    def test_firerole_non_existant_group(self):
        """firerole - firerole core testing non existant group matching"""
        self.failIf(acc_firerole_check_user(self.user_info,
            compile_role_definition("allow groups 'patat'\ndeny any")))

    def test_firerole_with_future_date(self):
        """firerole - firerole core testing with future date"""
        import time
        future_date = time.strftime('%Y-%m-%d', time.gmtime(time.time() + 24 * 3600 * 2))
        self.failUnless(acc_firerole_check_user(self.user_info,
            compile_role_definition("allow until '%s'\nallow any" % future_date)))
        self.failIf(acc_firerole_check_user(self.user_info,
            compile_role_definition("allow from '%s'\nallow any" % future_date)))

    def test_firerole_with_past_date(self):
        """firerole - firerole core testing with past date"""
        import time
        past_date = time.strftime('%Y-%m-%d', time.gmtime(time.time() - 24 * 3600 * 2))
        self.failIf(acc_firerole_check_user(self.user_info,
            compile_role_definition("allow until '%s'\nallow any" % past_date)))
        self.failUnless(acc_firerole_check_user(self.user_info,
            compile_role_definition("allow from '%s'\nallow any" % past_date)))

    def test_firerole_empty(self):
        """firerole - firerole core testing empty matching"""
        self.assertEqual(False, acc_firerole_check_user(self.user_info,
            compile_role_definition(None)))

    def test_firerole_uid(self):
        """firerole - firerole core testing with integer uid"""
        self.assertEqual(False, acc_firerole_check_user(self.guest,
            compile_role_definition("deny uid '-1', '0'\nallow all")))
        self.assertEqual(True, acc_firerole_check_user(self.user_info,
            compile_role_definition("deny uid '-1', '0'\nallow all")))

    def test_firerole_guest(self):
        """firerole - firerole core testing with guest"""
        self.assertEqual(False, acc_firerole_check_user(self.guest,
            compile_role_definition("deny guest '1'\nallow all")))
        self.assertEqual(True, acc_firerole_check_user(self.guest,
            compile_role_definition("deny guest '0'\nallow all")))

        self.assertEqual(True, acc_firerole_check_user(self.user_info,
            compile_role_definition("deny guest '1'\nallow all")))
        self.assertEqual(False, acc_firerole_check_user(self.user_info,
            compile_role_definition("deny guest '0'\nallow all")))

        self.assertEqual(False, acc_firerole_check_user(self.user_info,
            compile_role_definition("deny guest '1'\ndeny all")))
        self.assertEqual(False, acc_firerole_check_user(self.user_info,
            compile_role_definition("deny guest '0'\ndeny all")))

TEST_SUITE = make_test_suite(AccessControlFireRoleTest,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
