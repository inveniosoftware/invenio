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

"""WebSubmit module web tests."""

from invenio.config import CFG_SITE_SECURE_URL
from invenio.testutils import make_test_suite, \
                              run_test_suite, \
                              InvenioWebTestCase


class InvenioWebSubmitWebTest(InvenioWebTestCase):
    """WebSubmit web tests."""

    def test_submit_article(self):
        """websubmit - web test submit an article"""

        self.browser.get(CFG_SITE_SECURE_URL)
        # login as jekyll
        self.login(username="jekyll", password="j123ekyll")

        self.find_element_by_link_text_with_timeout("Submit")
        self.browser.find_element_by_link_text("Submit").click()
        self.find_element_by_link_text_with_timeout("Demo Article Submission")
        self.browser.find_element_by_link_text("Demo Article Submission").click()
        self.find_element_by_id_with_timeout("comboARTICLE")
        self.browser.find_element_by_id("comboARTICLE").click()
        self.find_element_by_xpath_with_timeout("//input[@value='Submit New Record']")
        self.browser.find_element_by_xpath("//input[@value='Submit New Record']").click()
        self.fill_textbox("DEMOART_REP", "Test-Ref-001\nTest-Ref-002")
        self.fill_textbox("DEMOART_TITLE", "Test article document title")
        self.fill_textbox("DEMOART_AU", "Author1, Firstname1\nAuthor2, Firstname2")
        self.fill_textbox("DEMOART_ABS", "This is a test abstract.\nIt has some more lines.\n\n...and some empty lines.\n\nAnd it finishes here.")
        self.fill_textbox("DEMOART_NUMP", "1234")
        self.choose_selectbox_option_by_label("DEMOART_LANG", "French")
        self.fill_textbox("DEMOART_DATE", "11/01/2001")
        self.fill_textbox("DEMOART_KW", "test keyword1\ntest keyword2\ntest keyword3")
        self.fill_textbox("DEMOART_NOTE", "I don't think I have any additional comments.\nBut maybe I'll input some quotes here: \" ' ` and the rest.")
        self.fill_textbox("DEMOART_FILE", "/opt/invenio/lib/webtest/invenio/test.pdf")
        self.find_element_by_name_with_timeout("endS")
        self.browser.find_element_by_name("endS").click()
        self.page_source_test(expected_text=['Submission Complete!', \
                                             'Your document has the following reference(s): <b>DEMO-ARTICLE-'])
        self.logout()

    def test_submit_book(self):
        """websubmit - web test submit a book"""
        
        self.browser.get(CFG_SITE_SECURE_URL)
        # login as jekyll
        self.login( username="jekyll", password="j123ekyll")
        self.find_element_by_link_text_with_timeout("Submit")
        self.browser.find_element_by_link_text("Submit").click()
        self.find_element_by_link_text_with_timeout("Demo Book Submission (Refereed)")
        self.browser.find_element_by_link_text("Demo Book Submission (Refereed)").click()
        self.find_element_by_xpath_with_timeout("//input[@value='Submit New Record']")
        self.browser.find_element_by_xpath("//input[@value='Submit New Record']").click()
        self.fill_textbox("DEMOBOO_REP", "test-bk-ref-1\ntest-bk-ref-2")
        self.fill_textbox("DEMOBOO_TITLE", "Test book title")
        self.fill_textbox("DEMOBOO_AU", "Doe, John")
        self.fill_textbox("DEMOBOO_ABS", "This is a test abstract of this test book record.")
        self.fill_textbox("DEMOBOO_NUMP", "20")
        self.choose_selectbox_option_by_label("DEMOBOO_LANG", "English")
        self.fill_textbox("DEMOBOO_DATE", "10/01/2001")
        self.fill_textbox("DEMOBOO_KW", "test keyword 1\ntest keyword 2")
        self.fill_textbox("DEMOBOO_NOTE", "No additional notes.")
        self.find_element_by_name_with_timeout("endS")
        self.browser.find_element_by_name("endS").click()
        self.page_source_test(expected_text=['Submission Complete!', \
                                             'Your document has the following reference(s): <b>DEMO-BOOK-', \
                                             'An email has been sent to the referee.'])
        self.logout()

    def test_submit_book_approval(self):
        """websubmit - web test submit a book approval"""

        import time
        year = time.localtime().tm_year
        self.browser.get(CFG_SITE_SECURE_URL)
        # login as hyde
        self.login(username="hyde", password="h123yde")
        self.browser.get(CFG_SITE_SECURE_URL + "/yourapprovals.py")
        self.page_source_test(expected_text='You are not authorized to use approval system.')
        self.browser.get(CFG_SITE_SECURE_URL + "/publiline.py?doctype=DEMOBOO")
        self.browser.find_element_by_link_text("DEMO-BOOK-%s-001" % str(year)).click()
        self.page_source_test(unexpected_text='As a referee for this document, you may click this button to approve or reject it')
        self.logout()
        # login as dorian
        self.login(username="dorian", password="d123orian")
        self.find_element_by_link_text_with_timeout("your approvals")
        self.browser.find_element_by_link_text("your approvals").click()
        self.page_source_test(expected_text='You are a general referee')
        self.find_element_by_link_text_with_timeout("You are a general referee")
        self.browser.find_element_by_link_text("You are a general referee").click()
        self.page_source_test(expected_text='DEMO-BOOK-')
        self.browser.find_element_by_link_text("DEMO-BOOK-%s-001" % str(year)).click()
        self.page_source_test(expected_text=['Approval and Refereeing Workflow', \
                                             'The record you are trying to access', \
                                             'It is currently restricted for security reasons'])
        self.logout()

    def test_submit_journal(self):
        """websubmit - web test submit a journal"""

        self.browser.get(CFG_SITE_SECURE_URL + "/submit?doctype=DEMOJRN")
        # login as jekyll
        self.login(username="jekyll", password="j123ekyll")
        self.browser.get(CFG_SITE_SECURE_URL + "/submit?doctype=DEMOJRN")
        self.find_element_by_id_with_timeout("comboARTS")
        self.browser.find_element_by_id("comboARTS").click()
        self.find_element_by_xpath_with_timeout("//input[@value='Submit New Record']")
        self.browser.find_element_by_xpath("//input[@value='Submit New Record']").click()
        self.page_source_test(expected_text='You are not authorized to perform this action')
        self.browser.get(CFG_SITE_SECURE_URL)
        self.find_element_by_link_text_with_timeout("Submit")
        self.browser.find_element_by_link_text("Submit").click()
        self.page_source_test(unexpected_text='Demo Journal Submission')
        self.logout()
        # login as romeo
        self.login(username="romeo", password="r123omeo")
        self.find_element_by_link_text_with_timeout("Submit")
        self.browser.find_element_by_link_text("Submit").click()
        self.find_element_by_link_text_with_timeout("Demo Journal Submission")
        self.browser.find_element_by_link_text("Demo Journal Submission").click()
        self.find_element_by_id_with_timeout("comboARTS")
        self.browser.find_element_by_id("comboARTS").click()
        self.find_element_by_xpath_with_timeout("//input[@value='Submit New Record']")
        self.browser.find_element_by_xpath("//input[@value='Submit New Record']").click()
        self.choose_selectbox_option_by_label("DEMOJRN_TYPE", "Offline")
        self.fill_textbox("DEMOJRN_ORDER1", "1")
        self.fill_textbox("DEMOJRN_ORDER2", "1")
        self.fill_textbox("DEMOJRN_AU", "Author1, Firstname1\nAuthor2, Firstname2")
        self.fill_textbox("DEMOJRN_TITLEE", "This is a test title")
        self.fill_textbox("DEMOJRN_TITLEF", "Ceci est un titre test")
        self.find_element_by_name_with_timeout("endS")
        self.browser.find_element_by_name("endS").click()
        self.logout()

    def test_submit_poetry(self):
        """websubmit - web test submit a poem"""

        self.browser.get(CFG_SITE_SECURE_URL)
        # login as jekyll
        self.login(username="jekyll", password="j123ekyll")
        self.find_element_by_link_text_with_timeout("Submit")
        self.browser.find_element_by_link_text("Submit").click()
        self.find_element_by_link_text_with_timeout("Demo Poetry Submission")
        self.browser.find_element_by_link_text("Demo Poetry Submission").click()
        self.find_element_by_xpath_with_timeout("//input[@value='Submit New Record']")
        self.browser.find_element_by_xpath("//input[@value='Submit New Record']").click()
        self.fill_textbox("DEMOPOE_TITLE", "A test poem")
        self.fill_textbox("DEMOPOE_AU", "Doe, John")
        self.choose_selectbox_option_by_label("DEMOPOE_LANG", "Slovak")
        self.fill_textbox("DEMOPOE_YEAR", "1234")
        self.find_element_by_xpath_with_timeout("//strong/font")
        self.browser.find_element_by_xpath("//strong/font").click()
        self.fill_textbox("DEMOPOE_ABS", u"This is a test poem<br>\na test poem indeed<br>\nwith some accented characters<br>\n<br>\nΕλληνικά<br> \n日本語<br>\nEspañol")
        self.find_element_by_name_with_timeout("endS")
        self.browser.find_element_by_name("endS").click()
        self.page_source_test(expected_text=['Submission Complete!', \
                                             'Your document has the following reference(s): <b>DEMO-POETRY-'])
        self.logout()

    def test_submit_tar_gz(self):
        """websubmit - web test submit an article with a tar.gz file """

        self.browser.get(CFG_SITE_SECURE_URL)
        # login as jekyll
        self.login(username="jekyll", password="j123ekyll")
        self.find_element_by_link_text_with_timeout("Submit")
        self.browser.find_element_by_link_text("Submit").click()
        self.find_element_by_link_text_with_timeout("Demo Article Submission")
        self.browser.find_element_by_link_text("Demo Article Submission").click()
        self.find_element_by_id_with_timeout("comboARTICLE")
        self.browser.find_element_by_id("comboARTICLE").click()
        self.find_element_by_xpath_with_timeout("//input[@value='Submit New Record']")
        self.browser.find_element_by_xpath("//input[@value='Submit New Record']").click()
        self.fill_textbox("DEMOART_REP", "Test-Ref-001\nTest-Ref-002")
        self.fill_textbox("DEMOART_TITLE", "Test article tar gz document title")
        self.fill_textbox("DEMOART_AU", "Author1, Firstname1\nAuthor2, Firstname2")
        self.fill_textbox("DEMOART_ABS", "This is a test abstract.\nIt has some more lines.\n\n...and some empty lines.\n\nAnd it finishes here.")
        self.fill_textbox("DEMOART_NUMP", "1234")
        self.choose_selectbox_option_by_label("DEMOART_LANG", "French")
        self.fill_textbox("DEMOART_DATE", "11/01/2001")
        self.fill_textbox("DEMOART_KW", "test keyword1\ntest keyword2\ntest keyword3")
        self.fill_textbox("DEMOART_NOTE", "I don't think I have any additional comments.\nBut maybe I'll input some quotes here: \" ' ` and the rest.")
        self.fill_textbox("DEMOART_FILE", "/opt/invenio/lib/webtest/invenio/test.tar.gz")
        self.find_element_by_name_with_timeout("endS")
        self.browser.find_element_by_name("endS").click()
        self.page_source_test(expected_text=['Submission Complete!', \
                                             'Your document has the following reference(s): <b>DEMO-ARTICLE-'])
        self.logout()

TEST_SUITE = make_test_suite(InvenioWebSubmitWebTest, )

if __name__ == '__main__':
    run_test_suite(TEST_SUITE, warn_user=True)
