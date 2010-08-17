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

"""WebAccess Regression Test Suite."""

__revision__ = "$Id$"

import unittest

from invenio.access_control_admin import acc_add_role, acc_delete_role, \
    acc_get_role_definition
from invenio.access_control_firerole import compile_role_definition, \
    serialize, deserialize
from invenio.config import CFG_SITE_URL, CFG_SITE_SECURE_URL
from invenio.testutils import make_test_suite, run_test_suite, \
                              test_web_page_content, merge_error_messages

class WebAccessWebPagesAvailabilityTest(unittest.TestCase):
    """Check WebAccess web pages whether they are up or not."""

    def test_webaccess_admin_interface_availability(self):
        """webaccess - availability of WebAccess Admin interface pages"""

        baseurl = CFG_SITE_URL + '/admin/webaccess/webaccessadmin.py/'

        _exports = ['', 'delegate_startarea', 'manageaccounts']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            # first try as guest:
            error_messages.extend(test_web_page_content(url,
                                                        username='guest',
                                                        expected_text=
                                                        'Authorization failure'))
            # then try as admin:
            error_messages.extend(test_web_page_content(url,
                                                        username='admin'))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_webaccess_admin_guide_availability(self):
        """webaccess - availability of WebAccess Admin guide pages"""

        url = CFG_SITE_URL + '/help/admin/webaccess-admin-guide'
        error_messages = test_web_page_content(url,
                                               expected_text="WebAccess Admin Guide")
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

class WebAccessFireRoleTest(unittest.TestCase):
    """Check WebAccess behaviour WRT FireRole."""

    def setUp(self):
        """Create a fake role."""
        self.role_name = 'test'
        self.role_description = 'test role'
        self.role_definition = 'allow email /.*@cern.ch/'
        self.role_id, dummy, dummy, dummy = acc_add_role(self.role_name,
            self.role_description,
            serialize(compile_role_definition(self.role_definition)),
            self.role_definition)

    def tearDown(self):
        """Drop the fake role."""
        acc_delete_role(self.role_id)

    def test_webaccess_firerole_serialization(self):
        """webaccess - firerole role definition correctly serialized"""
        def_ser = compile_role_definition(self.role_definition)
        tmp_def_ser = acc_get_role_definition(self.role_id)
        self.assertEqual(def_ser, deserialize(tmp_def_ser))

class WebAccessUseBasketsTest(unittest.TestCase):
    """
    Check WebAccess behaviour WRT enabling/disabling web modules such
    as baskets.
    """

    def test_precached_area_authorization(self):
        """webaccess - login-time precached authorizations for usebaskets"""
        error_messages = test_web_page_content(CFG_SITE_SECURE_URL + '/youraccount/display?ln=en', username='jekyll', password='j123ekyll', expected_text='Your Baskets')
        error_messages.extend(test_web_page_content(CFG_SITE_SECURE_URL + '/youraccount/display?ln=en', username='hyde', password='h123yde', unexpected_text='Your Baskets'))

        if error_messages:
            self.fail(merge_error_messages(error_messages))


TEST_SUITE = make_test_suite(WebAccessWebPagesAvailabilityTest,
                             WebAccessFireRoleTest,
                             WebAccessUseBasketsTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
