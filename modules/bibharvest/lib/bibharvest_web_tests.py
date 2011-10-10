# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

"""BibHarvest module web tests."""

from invenio.config import CFG_SITE_SECURE_URL
from invenio.testutils import make_test_suite, \
                              run_test_suite, \
                              InvenioWebTestCase


class InvenioBibHarvestWebTest(InvenioWebTestCase):
    """BibHarvest web tests."""

    def test_insert_oai_sourse(self):
        """bibharvest - web test insert oai source"""

        self.browser.get(CFG_SITE_SECURE_URL)
        # login as admin
        self.login(username="admin", password="")   
        
        self.find_element_by_link_text_with_timeout("Administration")
        self.browser.find_element_by_link_text("Administration").click()
        self.find_element_by_link_text_with_timeout("Configure OAI Harvest")
        self.browser.find_element_by_link_text("Configure OAI Harvest").click()
        self.find_element_by_link_text_with_timeout("add new OAI source")
        self.browser.find_element_by_link_text("add new OAI source").click()
        self.fill_textbox("oai_src_baseurl", "invenio-demo.cern.ch/oai2d")
        self.find_element_by_xpath_with_timeout("//input[@value='Validate']")
        self.browser.find_element_by_xpath("//input[@value='Validate']").click()
        self.fill_textbox("oai_src_name", "AtlantisOAI")
        self.choose_selectbox_option_by_label("oai_src_prefix", "marcxml")
        self.find_element_by_id_with_timeout("cern:theory1")
        self.browser.find_element_by_id("cern:theory1").click()
        self.choose_selectbox_option_by_label("oai_src_frequency", "never")
        self.choose_selectbox_option_by_label("oai_src_lastrun", "from beginning")
        self.find_element_by_xpath_with_timeout("//label[text()='convert (c)']")
        self.browser.find_element_by_xpath("//label[text()='convert (c)']").click()
        self.find_element_by_xpath_with_timeout("//input[@value='Add OAI Source']", timeout=60)
        self.browser.find_element_by_xpath("//input[@value='Add OAI Source']").click()
        self.page_source_test(expected_text='Please enter a valid name of or a full path to a BibConvert config file or change postprocess mode.')
        self.fill_textbox("oai_src_config", "oaimarc2marcxml.xsl")
        self.find_element_by_xpath_with_timeout("//input[@value='Add OAI Source']")
        self.browser.find_element_by_xpath("//input[@value='Add OAI Source']").click()
        self.find_element_by_link_text_with_timeout("Go back to the OAI sources overview")
        self.browser.find_element_by_link_text("Go back to the OAI sources overview").click()
        self.page_source_test(expected_text='AtlantisOAI')
        self.logout()

TEST_SUITE = make_test_suite(InvenioBibHarvestWebTest, )

if __name__ == '__main__':
    run_test_suite(TEST_SUITE, warn_user=True)
