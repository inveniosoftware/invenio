# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013, 2014 CERN.
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
import time
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
        self.fill_textbox(textbox_name="DEMOART_REP", text="Test-Ref-001\nTest-Ref-002")
        self.fill_textbox(textbox_name="DEMOART_TITLE", text="Test article document title")
        self.fill_textbox(textbox_name="DEMOART_AU", text="Author1, Firstname1\nAuthor2, Firstname2")
        self.fill_textbox(textbox_name="DEMOART_ABS", text="This is a test abstract.\nIt has some more lines.\n\n...and some empty lines.\n\nAnd it finishes here.")
        self.fill_textbox(textbox_name="DEMOART_NUMP", text="1234")
        self.choose_selectbox_option_by_label(selectbox_name="DEMOART_LANG", label="French")
        self.fill_textbox(textbox_name="DEMOART_DATE", text="11/01/2001")
        self.fill_textbox(textbox_name="DEMOART_KW", text="test keyword1\ntest keyword2\ntest keyword3")
        self.fill_textbox(textbox_name="DEMOART_NOTE", text="I don't think I have any additional comments.\nBut maybe I'll input some quotes here: \" ' ` and the rest.")
        self.find_element_by_xpath_with_timeout("//div[@id='uploadFileInterface']//input[@type='button' and @value='Add new file']")
        self.browser.find_element_by_xpath("//div[@id='uploadFileInterface']//input[@type='button' and @value='Add new file']").click()
        self.wait_element_displayed_with_timeout(self.browser.find_element_by_id("balloonReviseFileInput"))
        self.fill_textbox(textbox_id="balloonReviseFileInput", text="/opt/invenio/lib/webtest/invenio/test.pdf")
        self.find_element_by_id_with_timeout("bibdocfilemanagedocfileuploadbutton")
        self.browser.find_element_by_id("bibdocfilemanagedocfileuploadbutton").click()
        self.wait_element_hidden_with_timeout(self.browser.find_element_by_id("balloonReviseFileInput"))
        self.find_elements_by_class_name_with_timeout('reviseControlFileColumn')
        self.page_source_test(expected_text=['revise', 'tree_branch.gif'])
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
        self.fill_textbox(textbox_name="DEMOBOO_REP", text="test-bk-ref-1\ntest-bk-ref-2")
        self.fill_textbox(textbox_name="DEMOBOO_TITLE", text="Test book title")
        self.fill_textbox(textbox_name="DEMOBOO_AU", text="Doe, John")
        self.fill_textbox(textbox_name="DEMOBOO_ABS", text="This is a test abstract of this test book record.")
        self.fill_textbox(textbox_name="DEMOBOO_NUMP", text="20")
        self.choose_selectbox_option_by_label(selectbox_name="DEMOBOO_LANG", label="English")
        self.fill_textbox(textbox_name="DEMOBOO_DATE", text="10/01/2001")
        self.fill_textbox(textbox_name="DEMOBOO_KW", text="test keyword 1\ntest keyword 2")
        self.fill_textbox(textbox_name="DEMOBOO_NOTE", text="No additional notes.")
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
        self.page_source_test(unexpected_text='Arts')
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
        self.choose_selectbox_option_by_label(selectbox_name="DEMOJRN_TYPE", label="Offline")
        self.fill_textbox(textbox_name="DEMOJRN_ORDER1", text="1")
        self.fill_textbox(textbox_name="DEMOJRN_ORDER2", text="1")
        self.fill_textbox(textbox_name="DEMOJRN_AU", text="Author1, Firstname1\nAuthor2, Firstname2")
        self.fill_textbox(textbox_name="DEMOJRN_TITLEE", text="This is a test title")
        self.fill_textbox(textbox_name="DEMOJRN_TITLEF", text="Ceci est un titre test")
        self.find_element_by_name_with_timeout("endS")
        self.browser.find_element_by_name("endS").click()
        self.page_source_test(expected_text=['Submission Complete!', \
                                             'Your document has the following reference(s): <b>BUL-ARTS-'])
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
        self.fill_textbox(textbox_name="DEMOPOE_TITLE", text="A test poem")
        self.fill_textbox(textbox_name="DEMOPOE_AU", text="Doe, John")
        self.choose_selectbox_option_by_label(selectbox_name="DEMOPOE_LANG", label="Slovak")
        self.fill_textbox(textbox_name="DEMOPOE_YEAR", text="1234")
        self.find_element_by_xpath_with_timeout("//strong/font")
        self.browser.find_element_by_xpath("//strong/font").click()
        self.fill_textbox(textbox_name="DEMOPOE_ABS", text=u"This is a test poem<br>\na test poem indeed<br>\nwith some accented characters<br>\n<br>\nΕλληνικά<br> \n日本語<br>\nEspañol")
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
        self.fill_textbox(textbox_name="DEMOART_REP", text="Test-Ref-001\nTest-Ref-002")
        self.fill_textbox(textbox_name="DEMOART_TITLE", text="Test article tar gz document title")
        self.fill_textbox(textbox_name="DEMOART_AU", text="Author1, Firstname1\nAuthor2, Firstname2")
        self.fill_textbox(textbox_name="DEMOART_ABS", text="This is a test abstract.\nIt has some more lines.\n\n...and some empty lines.\n\nAnd it finishes here.")
        self.fill_textbox(textbox_name="DEMOART_NUMP", text="1234")
        self.choose_selectbox_option_by_label(selectbox_name="DEMOART_LANG", label="French")
        self.fill_textbox(textbox_name="DEMOART_DATE", text="11/01/2001")
        self.fill_textbox(textbox_name="DEMOART_KW", text="test keyword1\ntest keyword2\ntest keyword3")
        self.fill_textbox(textbox_name="DEMOART_NOTE", text="I don't think I have any additional comments.\nBut maybe I'll input some quotes here: \" ' ` and the rest.")
        self.find_element_by_xpath_with_timeout("//div[@id='uploadFileInterface']//input[@type='button' and @value='Add new file']")
        self.browser.find_element_by_xpath("//div[@id='uploadFileInterface']//input[@type='button' and @value='Add new file']").click()
        self.wait_element_displayed_with_timeout(self.browser.find_element_by_id("balloonReviseFileInput"))
        self.fill_textbox(textbox_id="balloonReviseFileInput", text="/opt/invenio/lib/webtest/invenio/test.pdf")
        self.find_element_by_id_with_timeout("bibdocfilemanagedocfileuploadbutton")
        self.browser.find_element_by_id("bibdocfilemanagedocfileuploadbutton").click()
        self.wait_element_hidden_with_timeout(self.browser.find_element_by_id("balloonReviseFileInput"))
        self.find_elements_by_class_name_with_timeout('reviseControlFileColumn')
        self.page_source_test(expected_text=['revise', 'tree_branch.gif'])
        self.find_element_by_name_with_timeout("endS")
        self.browser.find_element_by_name("endS").click()
        self.page_source_test(expected_text=['Submission Complete!', \
                                             'Your document has the following reference(s): <b>DEMO-ARTICLE-'])
        self.logout()

    def test_submit_article_guest(self):
        """websubmit - web test submit an article as a guest"""
        self.browser.get(CFG_SITE_SECURE_URL)
        self.find_element_by_link_text_with_timeout("Submit")
        self.browser.find_element_by_link_text("Submit").click()
        self.find_element_by_link_text_with_timeout("Demo Article Submission")
        self.browser.find_element_by_link_text("Demo Article Submission").click()
        self.find_element_by_xpath_with_timeout("//input[@value='Submit New Record']")
        self.browser.find_element_by_xpath("//input[@value='Submit New Record']").click()
        self.fill_textbox(textbox_name="DEMOART_REP", text="Test-Ref-001\nTest-Ref-002")
        self.fill_textbox(textbox_name="DEMOART_TITLE", text="Test article document title")
        self.fill_textbox(textbox_name="DEMOART_AU", text="Author1, Firstname1\nAuthor2, Firstname2")
        self.fill_textbox(textbox_name="DEMOART_ABS", text="This is a test abstract.\nIt has some more lines.\n\n...and some empty lines.\n\nAnd it finishes here.")
        self.fill_textbox(textbox_name="DEMOART_NUMP", text="1234")
        self.choose_selectbox_option_by_label(selectbox_name="DEMOART_LANG", label="French")
        self.fill_textbox(textbox_name="DEMOART_DATE", text="11/01/2001")
        self.fill_textbox(textbox_name="DEMOART_KW", text="test keyword1\ntest keyword2\ntest keyword3")
        self.fill_textbox(textbox_name="DEMOART_NOTE", text="I don't think I have any additional comments.\nBut maybe I'll input some quotes here: \" ' ` and the rest.")
        self.find_element_by_xpath_with_timeout("//div[@id='uploadFileInterface']//input[@type='button' and @value='Add new file']")
        self.browser.find_element_by_xpath("//div[@id='uploadFileInterface']//input[@type='button' and @value='Add new file']").click()
        self.fill_textbox(textbox_id="balloonReviseFileInput", text="/opt/invenio/lib/webtest/invenio/test.pdf")
        self.find_element_by_id_with_timeout("bibdocfilemanagedocfileuploadbutton")
        self.browser.find_element_by_id("bibdocfilemanagedocfileuploadbutton").click()
        self.find_elements_by_class_name_with_timeout('reviseControlFileColumn')
        self.page_source_test(expected_text=['revise', 'tree_branch.gif'])
        self.find_element_by_name_with_timeout("endS")
        self.browser.find_element_by_name("endS").click()
        self.page_source_test(expected_text=['Submission Complete!', \
                                             'Your document has the following reference(s): <b>DEMO-ARTICLE-'])

    def test_access_restricted_submission_as_guest(self):
        """websubmit - web test guest must login to access restricted submission"""
        self.browser.get(CFG_SITE_SECURE_URL + '/submit?ln=en&doctype=DEMOTHE')
        self.page_source_test(expected_text=['Password', 'Lost your password?'],
                              unexpected_text=['Submit New Record', \
                                               'Demo Thesis Submission'])
        self.login(username="jekyll", password="j123ekyll", go_to_login_page=False)
        self.page_source_test(expected_text=['Submit New Record', \
                                             'Demo Thesis Submission'])
    def test_revise_picture_admin(self):
        """websubmit - web test submit and revise picture as admin"""
        self.browser.get(CFG_SITE_SECURE_URL + '?ln=en')
        # login as admin
        self.login( username="admin", password="")
        self.find_element_by_link_text_with_timeout("Submit")
        self.browser.find_element_by_link_text("Submit").click()
        self.find_element_by_link_text_with_timeout("Demo Picture Submission")
        self.browser.find_element_by_link_text("Demo Picture Submission").click()
        self.find_element_by_id_with_timeout("comboEXP")
        self.browser.find_element_by_id("comboEXP").click()
        self.find_element_by_xpath_with_timeout("//input[@value='Submit New File']")
        self.browser.find_element_by_xpath("//input[@value='Submit New File']").click()
        self.find_element_by_name_with_timeout("DEMOPIC_RN")
        self.browser.find_element_by_name("DEMOPIC_RN").clear()
        self.fill_textbox(textbox_name="DEMOPIC_RN", text="CERN-GE-9806033")
        self.find_element_by_name_with_timeout("endS")
        self.browser.find_element_by_name("endS").click()
        time.sleep(2)
        self.handle_popup_dialog()
        time.sleep(2)
        self.find_element_by_link_text_with_timeout("revise")
        self.browser.find_element_by_link_text("revise").click()
        self.find_element_by_id_with_timeout("balloonReviseFileInput")
        self.wait_element_displayed_with_timeout(self.browser.find_element_by_id("balloonReviseFileInput"))
        self.fill_textbox(textbox_id="balloonReviseFileInput", text="/opt/invenio/lib/webtest/invenio/test.png")
        self.find_element_by_id_with_timeout("bibdocfilemanagedocfileuploadbutton")
        self.browser.find_element_by_id("bibdocfilemanagedocfileuploadbutton").click()
        time.sleep(1)
        self.wait_element_hidden_with_timeout(self.browser.find_element_by_id("balloonReviseFileInput"))
        self.find_element_by_xpath_with_timeout("//div[@id='uploadFileInterface']//input[@type='button' and @value='Add new file']")
        self.browser.find_element_by_xpath("//div[@id='uploadFileInterface']//input[@type='button' and @value='Add new file']").click()
        self.choose_selectbox_option_by_value(selectbox_id='fileDoctype', value='Additional')
        self.fill_textbox(textbox_name="rename", text="Tiger")
        self.fill_textbox(textbox_id="balloonReviseFileInput", text="/opt/invenio/lib/webtest/invenio/test.pdf")
        self.find_element_by_id_with_timeout("bibdocfilemanagedocfileuploadbutton")
        self.browser.find_element_by_id("bibdocfilemanagedocfileuploadbutton").click()
        time.sleep(1)
        self.wait_element_hidden_with_timeout(self.browser.find_element_by_id("balloonReviseFileInput"))
        self.page_source_test(expected_text='Tiger')
        self.browser.find_element_by_xpath("//div[@id='uploadFileInterface']//tr[@class='even']//a[text()='delete']").click()
        self.handle_popup_dialog()
        time.sleep(1)
        self.find_element_by_name_with_timeout("Submit")
        self.browser.find_element_by_name("Submit").click()
        self.handle_popup_dialog()
        time.sleep(2)
        self.page_source_test(expected_text=['Submission Complete!', \
                                             'Your document has the following reference(s): <b>CERN-GE-9806033'])

    def test_autocompletion_authors(self):
        """"""
        from time import sleep
        from random import randint,choice
        from string import ascii_uppercase, digits
        def random_string(N=None):
            if N == None:
                N = randint(10, 25)
            return "".join(choice(ascii_uppercase + digits) for _ in range(N))
        test_authors = 10
        self.browser.get(CFG_SITE_SECURE_URL)
        self.login(username="admin", password="")
        self.browser.get(CFG_SITE_SECURE_URL+"/submit?ln=en&doctype=DEMOTHE")
        self.find_element_by_xpath_with_timeout("//input[@value='Submit New Record']")
        self.browser.find_element_by_xpath("//input[@value='Submit New Record']").click()
        self.find_element_by_name_with_timeout("DEMOTHE_TITLE")
        self.fill_textbox(textbox_name="DEMOTHE_TITLE", text=random_string())
        title = self.browser.find_element_by_name("DEMOTHE_TITLE")
        self.find_element_by_id_with_timeout("author_textbox")
        author_names = {}
        authors_to_input = ["Ellis", "Dickinson", "Bach"]
        for i in range(0,2):
            self.browser.find_element_by_id("author_textbox").send_keys(authors_to_input[i])
            self.find_element_by_id_with_timeout("autocomplete_element_"+str(i+1))
            self.browser.find_element_by_id("autocomplete_element_"+str(i+1)).click()
            author_names[i] = self.browser.find_elements_by_class_name("author-row-header-name")[i].text

        self.fill_textbox(textbox_name="DEMOTHE_ABS", text=random_string())
        abstract = self.browser.find_element_by_name("DEMOTHE_ABS").text
        self.choose_selectbox_option_by_label("DEMOTHE_LANG", label="English")
        self.fill_textbox(textbox_name="DEMOTHE_PUBL", text="CERN")
        self.fill_textbox("DEMOTHE_PLDEF", text="Geneva")
        self.choose_selectbox_option_by_label(selectbox_name="DEMOTHE_DIPL", label="MSc")
        self.fill_textbox(textbox_name="DEMOTHE_DATE", text="11/11/1991")
        self.fill_textbox(textbox_name="DEMOTHE_UNIV", text="AUTH")
        self.fill_textbox(textbox_name="DEMOTHE_PLACE", text="Thessaloniki")
        self.fill_textbox(textbox_name="DEMOTHE_FILE", text="/opt/invenio/lib/webtest/invenio/test.pdf")
        author_contributions = {}
        for i in range(0, 2):
            self.browser.find_elements_by_class_name("author-row-body-extra-contribution")[i].send_keys(random_string())
        for i in range(0, 2):
            author_contributions[i] = self.browser.find_elements_by_class_name("author-row-body-extra-contribution")[i].get_attribute("value")
        self.find_element_by_name_with_timeout("endS")
        self.browser.find_element_by_name("endS").click()
        self.find_element_by_xpath_with_timeout("html/body/div[2]/div[3]/form/center/table/tbody/tr[2]/td/small/b[2]")
        doc_ref = self.browser.find_element_by_xpath("html/body/div[2]/div[3]/form/center/table/tbody/tr[2]/td/small/b[2]").text
        self.browser.get(CFG_SITE_SECURE_URL + "/submit?ln=en&doctype=DEMOTHE")
        self.find_element_by_xpath_with_timeout("//input[@value='Modify Record']")
        self.browser.find_element_by_xpath("//input[@value='Modify Record']").click()
        self.browser.find_element_by_name("DEMOTHE_RN").clear()
        self.fill_textbox(textbox_name="DEMOTHE_RN", text=doc_ref)
        self.choose_selectbox_option_by_label(selectbox_name="DEMOTHE_CHANGE[]", label="Title")
        self.choose_selectbox_option_by_label(selectbox_name="DEMOTHE_CHANGE[]", label="Author(s)")
        self.choose_selectbox_option_by_label(selectbox_name="DEMOTHE_CHANGE[]", label="Abstract")
        sleep(5)
        self.find_element_by_name_with_timeout("endS")
        self.browser.find_element_by_name("endS").click()
        for i in range(0, 2):
            self.find_elements_by_class_name_with_timeout("author-row-header-name")
            self.assertEqual(self.browser.find_elements_by_class_name("author-row-header-name")[i].text, author_names[i], "Authors must stay the same")
            self.assertEqual(
                self.browser.find_elements_by_class_name("author-row-body-extra-contribution")[i].get_attribute("value"),
                author_contributions[i],
                "Contributions should stay in the same authors"
            )

TEST_SUITE = make_test_suite(InvenioWebSubmitWebTest,)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE, warn_user=True)
