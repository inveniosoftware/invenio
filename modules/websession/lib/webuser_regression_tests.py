# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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

# pylint: disable=E1102

"""WebSession Regression Test Suite."""

__revision__ = \
    "$Id$"

from invenio.testutils import InvenioTestCase

from mechanize import Browser

from invenio.dbquery import run_sql
from invenio.config import CFG_SITE_SECURE_URL
from invenio.testutils import make_test_suite, run_test_suite
from invenio import webuser

class IsUserSuperAdminTests(InvenioTestCase):
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

class WebSessionYourSettingsTests(InvenioTestCase):
    """Check WebSession web pages whether they are up or not."""

    def tearDown(self):
        run_sql('DELETE FROM user WHERE email="foo@cds.cern.ch"')
        run_sql('DELETE FROM user WHERE email="FOO@cds.cern.ch"')

    def test_password_setting(self):
        """webuser - check password settings"""
        browser = Browser()
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/login")
        browser.select_form(nr=0)
        browser['p_un'] = 'admin'
        browser['p_pw'] = ''
        browser.submit()

        expected_response = "You are logged in as <strong>admin</strong>."
        login_response_body = browser.response().read()
        try:
            login_response_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                      (expected_response, login_response_body))

        # Going to set new password from "" to "123"
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/edit")
        browser.select_form(name="edit_password")
        browser['old_password'] = ""
        browser['password'] = "123"
        browser['password2'] = "123"
        browser.submit()
        expected_response = "Password successfully edited"
        change_password_body = browser.response().read()
        try:
            change_password_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                    (expected_response, change_password_body))

        # Going to set a wrong old password
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/edit")
        browser.select_form(name="edit_password")
        browser['old_password'] = "321"
        browser['password'] = "123"
        browser['password2'] = "123"
        browser.submit()
        expected_response = "Wrong old password inserted"
        change_password_body = browser.response().read()
        try:
            change_password_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                    (expected_response, change_password_body))

        # Going to put different new passwords
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/edit")
        browser.select_form(name="edit_password")
        browser['old_password'] = "123"
        browser['password'] = "123"
        browser['password2'] = "321"
        browser.submit()
        expected_response = "Both passwords must match"
        change_password_body = browser.response().read()
        try:
            change_password_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                    (expected_response, change_password_body))

        # Reset the situation
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/edit")
        browser.select_form(name="edit_password")
        browser['old_password'] = "123"
        browser['password'] = ""
        browser['password2'] = ""
        browser.submit()
        expected_response = "Password successfully edited"
        change_password_body = browser.response().read()
        try:
            change_password_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                    (expected_response, change_password_body))

    def test_email_caseless(self):
        """webuser - check email caseless"""
        browser = Browser()
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/register")
        browser.select_form(nr=0)
        browser['p_email'] = 'foo@cds.cern.ch'
        browser['p_nickname'] = 'foobar'
        browser['p_pw'] = ''
        browser['p_pw2'] = ''
        browser.submit()

        expected_response = "Account created"
        login_response_body = browser.response().read()
        try:
            login_response_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                      (expected_response, login_response_body))


        browser = Browser()
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/register")
        browser.select_form(nr=0)
        browser['p_email'] = 'foo@cds.cern.ch'
        browser['p_nickname'] = 'foobar2'
        browser['p_pw'] = ''
        browser['p_pw2'] = ''
        browser.submit()

        expected_response = "Registration failure"
        login_response_body = browser.response().read()
        try:
            login_response_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                      (expected_response, login_response_body))

        browser = Browser()
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/register")
        browser.select_form(nr=0)
        browser['p_email'] = 'FOO@cds.cern.ch'
        browser['p_nickname'] = 'foobar2'
        browser['p_pw'] = ''
        browser['p_pw2'] = ''
        browser.submit()

        expected_response = "Registration failure"
        login_response_body = browser.response().read()
        try:
            login_response_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                      (expected_response, login_response_body))

    def test_select_records_per_group(self):
        """webuser - test of user preferences setting"""

        # logging in as admin
        browser = Browser()
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/login")
        browser.select_form(nr=0)
        browser['p_un'] = 'admin'
        browser['p_pw'] = ''
        browser.submit()

        expected_response = "You are logged in as <strong>admin</strong>."
        login_response_body = browser.response().read()
        try:
            login_response_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                      (expected_response, login_response_body))

        # Going to edit page and setting records per group to 20
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/edit")
        browser.select_form(name="edit_websearch_settings")
        browser['group_records'] = ["25"]
        browser.submit()

        expected_response = "User settings saved correctly"
        changed_settings_body = browser.response().read()
        try:
            changed_settings_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                      (expected_response, changed_settings_body))

        # Going to the search page, making an empty search
        browser.open(CFG_SITE_SECURE_URL)
        browser.select_form(nr=0)
        browser.submit()
        expected_response = "1 - 25"
        records_found_body = browser.response().read()
        try:
            records_found_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                      (expected_response, records_found_body))

        # Going again to edit and setting records per group back to 10
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/edit")
        browser.select_form(name="edit_websearch_settings")
        browser['group_records'] = ["10"]
        browser.submit()

        expected_response = "User settings saved correctly"
        changed_settings_body = browser.response().read()
        try:
            changed_settings_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                      (expected_response, changed_settings_body))

        # Logging out!
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/logout")
        expected_response = "You are no longer recognized"
        logout_response_body = browser.response().read()
        try:
            logout_response_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                      (expected_response, logout_response_body))

        # Logging in again
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/login")
        browser.select_form(nr=0)
        browser['p_un'] = 'admin'
        browser['p_pw'] = ''
        browser.submit()

        expected_response = "You are logged in as <strong>admin</strong>."
        login_response_body = browser.response().read()
        try:
            login_response_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                      (expected_response, login_response_body))

        # Let's go to search and check that the setting is still there
        browser.open(CFG_SITE_SECURE_URL)
        browser.select_form(nr=0)
        browser.submit()
        expected_response = "1 - 10"
        records_found_body = browser.response().read()
        try:
            records_found_body.index(expected_response)
        except ValueError:
            self.fail("Expected to see %s, got %s." % \
                      (expected_response, records_found_body))

        return



TEST_SUITE = make_test_suite(WebSessionYourSettingsTests, IsUserSuperAdminTests)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
