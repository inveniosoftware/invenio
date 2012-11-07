# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

"""BibDocFile module web tests."""
import time
from invenio.config import CFG_SITE_SECURE_URL
from invenio.testutils import make_test_suite, \
                              run_test_suite, \
                              InvenioWebTestCase


class InvenioBibDocFileWebTest(InvenioWebTestCase):
    """BibDocFile web tests."""

    def test_add_new_file(self):
        """bibdocfile - web test add a new file"""

        self.browser.get(CFG_SITE_SECURE_URL + "/record/5?ln=en")
        # login as admin
        self.login(username="admin", password="")

        self.find_element_by_link_text_with_timeout("Manage Files of This Record")
        self.browser.find_element_by_link_text("Manage Files of This Record").click()
        self.find_element_by_xpath_with_timeout("//div[@id='uploadFileInterface']//input[@type='button' and @value='Add new file']")
        self.browser.find_element_by_xpath("//div[@id='uploadFileInterface']//input[@type='button' and @value='Add new file']").click()
        self.wait_element_displayed_with_timeout(self.browser.find_element_by_id("balloonReviseFileInput"))
        filename = "Tiger_" + time.strftime("%Y%m%d%H%M%S")
        self.fill_textbox(textbox_name="rename", text=filename)
        self.fill_textbox(textbox_id="balloonReviseFileInput", text="/opt/invenio/lib/webtest/invenio/test.pdf")
        self.find_element_by_id_with_timeout("bibdocfilemanagedocfileuploadbutton")
        self.browser.find_element_by_id("bibdocfilemanagedocfileuploadbutton").click()
        self.wait_element_hidden_with_timeout(self.browser.find_element_by_id("balloonReviseFileInput"))
        self.find_elements_by_class_name_with_timeout('reviseControlFileColumn')
        self.page_source_test(expected_text=filename)
        self.find_element_by_id_with_timeout("applyChanges")
        self.browser.find_element_by_id("applyChanges").click()
        self.page_source_test(expected_text='Your modifications to record #5 have been submitted')
        self.logout()

    def test_revise_file(self):
        """bibdocfile - web test revise a file"""

        self.browser.get(CFG_SITE_SECURE_URL + "/record/6?ln=en")
        # login as admin
        self.login(username="admin", password="")

        self.find_element_by_link_text_with_timeout("Manage Files of This Record")
        self.browser.find_element_by_link_text("Manage Files of This Record").click()
        self.find_element_by_link_text_with_timeout("revise")
        self.browser.find_element_by_link_text("revise").click()
        self.find_element_by_id_with_timeout("balloonReviseFileInput")
        self.wait_element_displayed_with_timeout(self.browser.find_element_by_id("balloonReviseFileInput"))
        self.fill_textbox(textbox_id="balloonReviseFileInput", text="/opt/invenio/lib/webtest/invenio/test.pdf")
        self.find_element_by_id_with_timeout("bibdocfilemanagedocfileuploadbutton")
        self.browser.find_element_by_id("bibdocfilemanagedocfileuploadbutton").click()
        self.wait_element_hidden_with_timeout(self.browser.find_element_by_id("balloonReviseFileInput"))
        self.find_element_by_id_with_timeout("applyChanges")
        self.browser.find_element_by_id("applyChanges").click()
        self.page_source_test(expected_text='Your modifications to record #6 have been submitted')
        self.logout()

    def test_delete_file(self):
        """bibdocfile - web test delete a file"""

        self.browser.get(CFG_SITE_SECURE_URL + "/record/8?ln=en")
        # login as admin
        self.login(username="admin", password="")

        self.find_element_by_link_text_with_timeout("Manage Files of This Record")
        self.browser.find_element_by_link_text("Manage Files of This Record").click()
        self.browser.find_element_by_xpath("(//div[@id='uploadFileInterface']//tr[@class='even']//a[text()='delete'])[1]").click()
        self.handle_popup_dialog()
        time.sleep(1)
        self.page_source_test(expected_text=['9812226', 'pdf', 'ps.gz'],
                              unexpected_text=['9812226.fig1.ps.gz'])
        self.find_element_by_name_with_timeout("cancel")
        self.browser.find_element_by_name("cancel").click()
        self.handle_popup_dialog()
        time.sleep(1)
        self.page_source_test(expected_text='Your modifications to record #8 have been cancelled')
        self.logout()


TEST_SUITE = make_test_suite(InvenioBibDocFileWebTest, )

if __name__ == '__main__':
    run_test_suite(TEST_SUITE, warn_user=True)
