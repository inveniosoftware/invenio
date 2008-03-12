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

# pylint: disable-msg=E1102

"""Unit tests for the user handling library."""

__revision__ = "$Id$"

from mechanize import Browser
from invenio.config import CFG_SITE_SECURE_URL, CFG_SITE_ADMIN_EMAIL

from invenio.dbquery import run_sql
from invenio.webgroup import synchronize_external_groups, synchronize_all_external_groups
from invenio.webgroup_dblayer import get_external_groups, get_all_login_method_groups
from invenio.testutils import make_test_suite, warn_user_about_tests_and_run, \
                              test_web_page_content, merge_error_messages
import unittest

class WebGroupTest(unittest.TestCase):
    """Test functions related to the Apache authentication."""

    def setUp(self):
        # pylint: disable-msg=C0103
        """setting up helper variables for tests"""
        self.email = 'ciccio@pasticcio.it'
        self.pwd = '123'
        self.login_method = 'PATATA'
        self.uid = run_sql("""INSERT INTO user (email, password) VALUES (%s, AES_ENCRYPT(email,%s))""", (self.email, self.pwd, ))
        self.uid = int(self.uid)

        self.email2 = 'ghero@boll.ch'
        self.pwd2 = '1234'
        self.uid2 = run_sql("""INSERT INTO user (email, password) VALUES (%s, AES_ENCRYPT(email,%s))""", (self.email2, self.pwd2, ))
        self.uid2 = int(self.uid2)

        self.goodgroup = 'bla'
        self.badgroup = 'blo'
        self.goodid = run_sql("""INSERT INTO usergroup(name, description, join_policy, login_method)
            VALUES (%s, %s, 'VE', 'INTERNAL')""", (self.goodgroup, self.goodgroup))
        self.badid = run_sql("""INSERT INTO usergroup(name, description, join_policy, login_method)
            VALUES (%s, %s, 'VE', 'INTERNAL')""", (self.badgroup, self.badgroup))
        run_sql("""INSERT INTO user_usergroup(id_user, id_usergroup, user_status, user_status_date)
            VALUES (1, %s, 'M', NOW())""", (self.goodid, ))


    def test_synchronize_external_groups(self):
        """webgroup - synchronizing one user external groups"""
        synchronize_external_groups(self.uid, {'group1' : 'descr1', 'group2' : 'descr2'}, self.login_method)
        groups = get_external_groups(self.uid)
        groups_names = [name[1] for name in groups]
        self.failUnless('group1' in groups_names)
        self.failUnless('group2' in groups_names)
        synchronize_external_groups(self.uid, {'group1' : 'descr1', 'group2' : 'descr2'}, self.login_method)
        groups = get_external_groups(self.uid)
        groups_names = [name[1] for name in groups]
        self.failUnless('group1' in groups_names)
        self.failUnless('group2' in groups_names)
        self.failUnless(len(groups_names) == 2)
        synchronize_external_groups(self.uid, {'group1' : 'descr1', 'group3' : 'descr2'}, self.login_method)
        groups = get_external_groups(self.uid)
        groups_names = [name[1] for name in groups]
        self.failUnless('group1' in groups_names)
        self.failUnless('group3' in groups_names)
        self.failUnless(len(groups_names) == 2)
        synchronize_external_groups(self.uid, {}, self.login_method)
        groups = get_external_groups(self.uid)
        groups_names = [name[1] for name in groups]
        self.failUnless(len(groups_names) == 0)

    def test_synchronize_all_external_groups(self):
        """webgroup - synchronizing all external groups"""
        synchronize_all_external_groups({'group1' : ('descr1', [self.email, self.email2])}, self.login_method)
        groups = get_external_groups(self.uid2)
        self.assertEqual(len(groups), 1)
        synchronize_all_external_groups({'group2' : ('descr1', [self.email, self.email2])}, self.login_method)
        groups = get_external_groups(self.uid2)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0][1], 'group2')
        self.assertEqual(groups[0][2], 'descr1')
        synchronize_all_external_groups({'group2' : ('descr2', [self.email])}, self.login_method)
        groups = get_external_groups(self.uid)
        self.assertEqual(groups[0][2], 'descr2')
        groups = get_external_groups(self.uid)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0][1], 'group2')
        groups = get_external_groups(self.uid2)
        self.assertEqual(len(groups), 0)
        synchronize_all_external_groups({}, self.login_method)
        groups = get_external_groups(self.uid2)
        self.assertEqual(len(groups), 0)
        groups = get_all_login_method_groups(self.login_method)
        self.failIf(groups)

    def test_external_groups_visibility_groupspage(self):
        """webgroup - external group visibility in groups page"""
        browser = Browser()
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/login")
        browser.select_form(nr=0)
        browser['p_un'] = 'admin'
        browser['p_pw'] = ''
        browser.submit()

        expected_response = "You are logged in as admin"
        login_response_body = browser.response().read()
        try:
            login_response_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                      (expected_response, login_response_body))

        browser.open(CFG_SITE_SECURE_URL + "/yourgroups/display")
        expected_response = self.goodgroup
        groups_body = browser.response().read()
        try:
            groups_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                    (expected_response, groups_body))

        not_expected_response = self.badgroup
        try:
            groups_body.index(not_expected_response)
        except ValueError:
            pass
        else:
            self.fail("Not expected to see %s, got %s." % \
                    (not_expected_response, groups_body))

    def test_external_groups_visibility_messagespage(self):
        """webgroup - external group visibility in messages page"""
        browser = Browser()
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/login")
        browser.select_form(nr=0)
        browser['p_un'] = 'admin'
        browser['p_pw'] = ''
        browser.submit()

        expected_response = "You are logged in as admin"
        login_response_body = browser.response().read()
        try:
            login_response_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                      (expected_response, login_response_body))

        browser.open(CFG_SITE_SECURE_URL + "/yourmessages/write")
        browser.select_form(nr=0)
        browser['search_pattern'] = 'b'
        browser.submit(name='search_group')

        expected_response = self.goodgroup
        groups_body = browser.response().read()
        try:
            groups_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                    (expected_response, groups_body))

        not_expected_response = self.badgroup
        try:
            groups_body.index(not_expected_response)
        except ValueError:
            pass
        else:
            self.fail("Not expected to see %s, got %s." % \
                    (not_expected_response, groups_body))



    def tearDown(self):
        run_sql("""DELETE FROM user WHERE email=%s""", (self.email,))
        run_sql("""DELETE FROM user WHERE email=%s""", (self.email2,))
        run_sql("""DELETE FROM usergroup WHERE login_method=%s""", (self.login_method,))
        run_sql("""DELETE FROM user_usergroup WHERE id_user=%s""", (self.uid, ))
        run_sql("""DELETE FROM user_usergroup WHERE id_user=%s""", (self.uid2, ))
        run_sql("""DELETE FROM usergroup WHERE name=%s OR name=%s""", (self.goodgroup, self.badgroup,))
        run_sql("""DELETE FROM user_usergroup WHERE id_usergroup=%s OR id_usergroup=%s""", (self.goodid, self.badid,))

test_suite = make_test_suite(WebGroupTest)

if __name__ == "__main__":
    warn_user_about_tests_and_run(test_suite)
