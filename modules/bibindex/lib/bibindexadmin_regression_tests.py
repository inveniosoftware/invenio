# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2010, 2011 CERN.
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

"""BibIndex Admin Regression Test Suite."""

__revision__ = "$Id$"

import unittest
import re

from invenio.config import CFG_SITE_URL
from invenio.testutils import make_test_suite, run_test_suite, \
                              test_web_page_content, merge_error_messages, \
                              get_authenticated_mechanize_browser, make_url


class BibIndexAdminWebPagesAvailabilityTest(unittest.TestCase):
    """Check BibIndex Admin web pages whether they are up or not."""

    def test_bibindex_admin_interface_pages_availability(self):
        """bibindexadmin - availability of BibIndex Admin interface pages"""

        baseurl = CFG_SITE_URL + '/admin/bibindex/bibindexadmin.py/'

        _exports = ['',
                    'index',
                    'index?mtype=perform_showindexoverview',
                    'index?mtype=perform_editindexes',
                    'index?mtype=perform_addindex',
                    'field',
                    'field?mtype=perform_showfieldoverview',
                    'field?mtype=perform_editfields',
                    'field?mtype=perform_addfield',
                    'editindex?idxID=8&ln=en&mtype=perform_modifysynonymkb',
                    ]

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

    def test_bibindex_admin_guide_availability(self):
        """bibindexadmin - availability of BibIndex Admin guide pages"""

        url = CFG_SITE_URL + '/help/admin/bibindex-admin-guide'
        error_messages = test_web_page_content(url,
                                               expected_text="BibIndex Admin Guide")
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return


class BibIndexAdminSynonymKnowledgeBaseTest(unittest.TestCase):
    """Tests BibIndexAdmin's ability to change knowledge base details for indexes"""

    def setUp(self):
        self.re_operation_successfull = re.compile(r"Operation successfully completed")

    def test_change_title_index_knowledge_base(self):
        """tests if information about title index's knowledge base can be changed properly"""

        base = "/admin/bibindex/bibindexadmin.py/editindex"
        parameters = {'idxID':'8', 'ln':'en', 'mtype':'perform_modifysynonymkb'}
        url = make_url(base,**parameters)

        browser = get_authenticated_mechanize_browser("admin","")
        browser.open(url)
        browser.select_form(nr=0)
        form = browser.form
        form["idxKB"] = ["INDEX-SYNONYM-TITLE"]
        form["idxMATCH"] = ["leading_to_comma"]
        resp = browser.submit()
        #second page - confirmation
        browser.select_form(nr=1)
        resp = browser.submit()
        success = self.re_operation_successfull.search(resp.read())
        if not success:
            error_messages = """There is no "Operation successfully completed" in html response."""
            self.fail(merge_error_messages(error_messages))

    def test_change_title_index_knowledge_base_back(self):
        """tests if information about title index's knowledge base can be changed back"""

        base = "/admin/bibindex/bibindexadmin.py/editindex"
        parameters = {'idxID':'8', 'ln':'en', 'mtype':'perform_modifysynonymkb'}
        url = make_url(base,**parameters)

        browser = get_authenticated_mechanize_browser("admin","")
        browser.open(url)
        browser.select_form(nr=0)
        form = browser.form
        form["idxKB"] = ["INDEX-SYNONYM-TITLE"]
        form["idxMATCH"] = ["exact"]
        resp = browser.submit()
        #second page - confirmation
        browser.select_form(nr=1)
        resp = browser.submit()
        success = self.re_operation_successfull.search(resp.read())
        if not success:
            error_messages = """There is no "Operation successfully completed." in html response."""
            self.fail(merge_error_messages(error_messages))

TEST_SUITE = make_test_suite(BibIndexAdminWebPagesAvailabilityTest,
                             BibIndexAdminSynonymKnowledgeBaseTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
