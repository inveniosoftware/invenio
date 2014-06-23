# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013 CERN.
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

# TODO fix those tests - export formats looks different now

import time
import os
import re
from invenio.config import CFG_SITE_SECURE_URL
from invenio.legacy.dbquery import run_sql
from invenio.testutils import make_test_suite, \
    run_test_suite, \
    InvenioWebTestCase

try:
    from selenium import webdriver
    from selenium.common.exceptions import NoSuchElementException
except ImportError:
    # web tests will not be available, but unit and regression tests will:
    pass

# some predefined keys
ENTER_KEY = webdriver.common.keys.Keys.ENTER
TMP_FOLDER = '/tmp/'


class InvenioWebTestAlertException(Exception):
    """This exception is raised when there is an alert popup on the page"""

    def __init__(self, message):
        """Initialisation."""
        self.message = "There is an error on the page:\n" + message

    def __str__(self):
        """String representation."""
        return str(self.message)


class InvenioWebTestTimeoutException(Exception):
    """This exception is raised when something takes too much time than expected"""

    def __init__(self):
        """Initialisation."""
        pass

    def __str__(self):
        """Showing an error message"""
        return "Timeout exception"


class InvenioWebAuthorlistWebTest(InvenioWebTestCase):
    """WebAuthorlist web tests."""

    def setUp(self):
        """Initialization before tests."""

        ## Let's default to English locale
        profile = webdriver.FirefoxProfile()
        profile.set_preference('intl.accept_languages', 'en-us, en')
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference('browser.download.dir', TMP_FOLDER)
        profile.set_preference("browser.download.manager.showWhenStarting", False)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk",
                               "application/x-tex, text/plain, application/octet-stream, text/html, text/xml, application/xml")
        profile.update_preferences()

        # the instance of Firefox WebDriver is created
        self.browser = webdriver.Firefox(profile)

        # list of errors
        self.errors = []
        # Make sure that the appropriate tables are empty
        run_sql("TRUNCATE aulPAPERS")
        run_sql("TRUNCATE aulAUTHORS")
        run_sql("TRUNCATE aulAFFILIATIONS")
        run_sql("TRUNCATE aulAUTHOR_AFFILIATIONS")

        # Add some example records to the database
        timestamp = time.time()
        run_sql("""INSERT INTO aulPAPERS (id, id_user, title, collaboration,
                    experiment_number, last_modified) VALUES
                    (1,2, 'test_paper', 'test_collaboration',
                    'text_experiment_number',%(time)s),
                    (2,2, 'test_paper2', 'test_collaboration2',
                    'text_experiment_number2',%(time)s)"""
                % {'time': timestamp})
        # Add example authors
        run_sql("""INSERT INTO aulAUTHORS (item, family_name, given_name, name_on_paper,
                    alive, inspire_id, paper_id) VALUES
                    (0, 'John', 'Banana', 'Banana, J.', 1, '', 1),
                    (1, 'Mark', 'Apple', 'Apple, M.', 1, '', 1),
                    (0,'John', 'Banana', 'Banana, J.', 1, '', 2)""")
        # Add example affiliations
        run_sql("""INSERT INTO aulAFFILIATIONS (item, acronym, umbrella, name_and_address,
                domain, member, spires_id, paper_id) VALUES
                (0, 'example', '', 'example 100', '', 1, '', 1),
                (0, 'example', '', 'example 100', '', 1, '', 2)""")
        # Add example author_affiliations
        run_sql("""INSERT INTO aulAUTHOR_AFFILIATIONS (item, affiliation_acronym,
                affiliation_status, author_item, paper_id) VALUES
                (0, 'example', 'Affiliate with', 0, 1),
                (0, 'example', 'Affiliate with', 1, 1),
                (0, 'example', 'Affiliate with', 0, 2)""")

    def tearDown(self):
        super(InvenioWebAuthorlistWebTest, self).tearDown()
        # Cleanup the database
        run_sql("TRUNCATE aulPAPERS")
        run_sql("TRUNCATE aulAUTHORS")
        run_sql("TRUNCATE aulAFFILIATIONS")
        run_sql("TRUNCATE aulAUTHOR_AFFILIATIONS")

# <-------- Helper functions ---------->

    def fill_datatable_cell(self, cell, text):
        """Helper for filling DataTable cell"""
        cell.click()
        cell.send_keys(text)

    def get_downloaded_file(self, filename, interval=0.5, repetitions=10):
        """Waits until file is downloaded.
        Returns handler to the file or throws an exception"""

        for _ in range(repetitions):
            try:
                f = open(TMP_FOLDER + filename)
                return f
            except IOError:
                # maybe file is still not downloaded ? Let's wait a while
                time.sleep(interval)
        # file was not downloaded in a given period of time, let's raise an exception
        raise InvenioWebTestTimeoutException

    def login_and_download_file(self, filename, button_class):
        """Logs into the authorlist manager area and downloads specific file from example record.
        Returns handler to the file"""

        self.browser.get(CFG_SITE_SECURE_URL)
        # login as jekyll
        self.login(username="jekyll", password="j123ekyll")
        self.browser.get(CFG_SITE_SECURE_URL + "/authorlist")
        # open record
        self.find_element_by_link_text_with_timeout('test_paper')
        self.browser.find_element_by_link_text('test_paper').click()
        # before downloading, make sure we don't have a file with the same name in TMP_FOLDER
        self.clear_download_folder(filename)
        self.find_element_by_class_name_with_timeout(button_class)
        self.browser.find_element_by_class_name(button_class).click()
        # get the downloaded file
        f = self.get_downloaded_file(filename)
        return f

    def save_and_quit(self):
        """Saves new record, makes sure that there are no errors (no popups with errors),
        goes back to main Authorlist Manager page and cehck if the new record was added"""
        # save record
        self.find_element_by_class_name_with_timeout('AuthorlistSave')
        self.browser.find_element_by_class_name('AuthorlistSave').click()
        # check if there are any errors
        try:
            alert = self.browser.find_element_by_class_name('AuthorlistDialog')
            alert_message = alert.find_element_by_class_name('ui-state-error').text
            raise InvenioWebTestAlertException(alert_message)
        except NoSuchElementException:
            # no errors - yay !
            pass

        # go back to all papers
        self.find_element_by_class_name_with_timeout('AuthorlistBack')
        self.browser.find_element_by_class_name('AuthorlistBack').click()
        # make sure that now we have 3 lists of papers
        self.find_elements_by_class_name_with_timeout('AuthorlistIndexPaper')
        papers = self.browser.find_elements_by_class_name('AuthorlistIndexPaper')
        self.assertEqual(len(papers), 3)

    def clear_download_folder(self, filename):
        try:
            os.remove(TMP_FOLDER + filename)
        except OSError:
            # no such file, but it's ok
            pass

# <-------- Test functions ---------->

    def test_add_record(self):
        """WebAuthorlist - web test add new record and save it"""

        self.browser.get(CFG_SITE_SECURE_URL)
        # login as jekyll
        self.login(username="jekyll", password="j123ekyll")
        self.browser.get(CFG_SITE_SECURE_URL + "/authorlist")
        # open new record
        self.find_element_by_class_name_with_timeout('AuthorlistIndexNew')
        self.browser.find_element_by_class_name('AuthorlistIndexNew').click()
        # fill all the fields
        self.find_element_by_id_with_timeout("PaperTitle(*)")
        self.fill_textbox(textbox_id="PaperTitle(*)", text="Paper name")
        self.find_element_by_id_with_timeout("Collaboration(*)")
        self.fill_textbox(textbox_id="Collaboration(*)", text="Collaboration example")
        self.find_element_by_id_with_timeout("ExperimentNumber")
        self.fill_textbox(textbox_id="ExperimentNumber", text="123")
        self.find_element_by_id_with_timeout("AuthorlistReference0")
        self.fill_textbox(textbox_id="AuthorlistReference0", text="Reference123")
        self.find_element_by_class_name_with_timeout('AuthorlistAdd')
        self.browser.find_element_by_class_name('AuthorlistAdd').click()
        self.find_element_by_id_with_timeout("AuthorlistReference1")
        self.fill_textbox(textbox_id="AuthorlistReference1", text="Reference456")
        self.find_elements_by_class_name_with_timeout("Readonly")
        cells = self.browser.find_elements_by_class_name("Readonly")
        self.fill_datatable_cell(cells[0], 'Banana')
        self.fill_datatable_cell(cells[1], 'John')
        self.fill_datatable_cell(cells[2], 'Banana, J.')
        self.fill_datatable_cell(cells[3], 'Main university')
        self.fill_datatable_cell(cells[4], '123123')
        self.fill_datatable_cell(cells[5], 'Main university')
        self.fill_datatable_cell(cells[7], 'Example 111')
        self.fill_datatable_cell(cells[8], 'Domain_example')
        self.fill_datatable_cell(cells[9], '123Spires')
        self.save_and_quit()

        self.logout()

    def test_xml_save(self):
        """WebAuthorlist - web test save xml file of example record and check if it's correct"""

        # Log in and download authors.xml file
        fopen = self.login_and_download_file('authors.xml', 'AuthorlistExportXML')
        downloaded = fopen.read()
        # remove timestamp
        downloaded = re.sub("\n    <cal:creationDate>[^<].*</cal:creationDate>", '', downloaded)
        valid = """<?xml version="1.0" encoding="utf-8"?>
<collaborationauthorlist xmlns:cal="http://www.slac.stanford.edu/spires/hepnames/authors_xml/" xmlns:foaf="http://xmlns.com/foaf/0.1/">
    <cal:experimentNumber>text_experiment_number</cal:experimentNumber>
    <cal:organizations>
        <foaf:Organization id="o0">
            <foaf:name>example 100</foaf:name>
            <cal:orgAddress>example 100</cal:orgAddress>
            <cal:orgStatus>member</cal:orgStatus>
        </foaf:Organization>
    </cal:organizations>
    <cal:authors>
        <foaf:Person>
            <cal:authorNamePaper>Banana, J.</cal:authorNamePaper>
            <foaf:givenName>Banana</foaf:givenName>
            <foaf:familyName>John</foaf:familyName>
            <cal:authorCollaboration collaborationid="c1"/>
            <cal:authorAffiliations>
                <cal:authorAffiliation connection="Affiliated with" organizationid="o0"/>
            </cal:authorAffiliations>
        </foaf:Person>
        <foaf:Person>
            <cal:authorNamePaper>Apple, M.</cal:authorNamePaper>
            <foaf:givenName>Apple</foaf:givenName>
            <foaf:familyName>Mark</foaf:familyName>
            <cal:authorCollaboration collaborationid="c1"/>
            <cal:authorAffiliations>
                <cal:authorAffiliation connection="Affiliated with" organizationid="o0"/>
            </cal:authorAffiliations>
        </foaf:Person>
    </cal:authors>
</collaborationauthorlist>
"""
        # compare both files
        self.assertEqual(downloaded, valid)
        #FIXME: if this test will begin to fail, check if the indentations or escaping are correct in valid
        #       or use parsing function to get rid of whitespaces
        self.logout()

    def test_elsevier_save(self):
        """WebAuthorlist - web test save elsevier format file of example record and check if it's correct"""

        # Log in and download elsarticle.tex file
        fopen = self.login_and_download_file('elsarticle.tex', 'AuthorlistExportElsevier')
        downloaded = fopen.read()
        valid = """\documentclass[a4paper,12pt]{article}
\\begin{document}
\\begin{center}
{\Large Collaboration}\\\\
\\vspace{2mm}
%
 Banana~John,
 Apple~Mark \\\\
{\em \small example 100} \\\\[0.2cm]
%
\end{center}
\setcounter{footnote}{0}
\end{document}
"""
        # compare both files
        self.assertEqual(downloaded, valid)
        self.logout()

    def test_APS_save(self):
        """WebAuthorlist - web test save APSpaper format file of example record and check if it's correct"""

        # Log in and download APSpaper.tex file
        fopen = self.login_and_download_file('APSpaper.tex', 'AuthorlistExportAPS')
        downloaded = fopen.read()
        valid = """<?xml version="1.0"?>

\\author{Banana, J.$^{o0}$}  
\\author{Apple, M.$^{o0}$}  
\\affiliation{$^{o0}$ example 100}

"""
        # compare both files
        self.assertEqual(downloaded, valid)
        self.logout()

    def test_import_record(self):
        """WebAuthorlist - web test imports data from a record"""

        self.browser.get(CFG_SITE_SECURE_URL)
        # login as jekyll
        self.login(username="jekyll", password="j123ekyll")
        self.browser.get(CFG_SITE_SECURE_URL + "/authorlist")
        # open new record
        self.find_element_by_class_name_with_timeout('AuthorlistIndexNew')
        self.browser.find_element_by_class_name('AuthorlistIndexNew').click()
        # import data from record with ID 15
        self.find_element_by_class_name_with_timeout('AuthorlistImport')
        self.browser.find_element_by_class_name('AuthorlistImport').click()
        self.find_element_by_class_name_with_timeout('AuthorlistDialog')
        dialog = self.browser.find_element_by_class_name('AuthorlistDialog')
        textbox = dialog.find_element_by_tag_name('input')
        textbox.send_keys('9')
        # click "Import"
        dialog.find_element_by_class_name('ui-button').click()
        # count the cells in tables
        # we should have now 8 cols x 4 rows = 32 cells in the first tables
        # and 8 cols x 3 rows = 24 cells in the second table
        self.find_elements_by_class_name_with_timeout("Clickable")
        cells = self.browser.find_elements_by_class_name("Clickable")
        if len(cells) < 56:
            #maybe not all tables rows were loaded yet ? Give it another chance
            time.sleep(0.5)
            cells = self.browser.find_elements_by_class_name("Clickable")
        self.assertEqual(len(cells), 56)
        # fill the remaining fields
        self.find_element_by_id_with_timeout("PaperTitle(*)")
        self.fill_textbox(textbox_id="PaperTitle(*)", text="Paper name")
        self.find_element_by_id_with_timeout("Collaboration(*)")
        self.fill_textbox(textbox_id="Collaboration(*)", text="Collaboration example")
        self.save_and_quit()

        self.logout()


TEST_SUITE = make_test_suite(InvenioWebAuthorlistWebTest, )

if __name__ == '__main__':
    run_test_suite(TEST_SUITE, warn_user=True)
