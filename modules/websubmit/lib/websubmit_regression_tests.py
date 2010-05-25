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

"""WebSubmit Regression Test Suite."""

__revision__ = "$Id$"

import unittest
import os

from invenio.config import CFG_SITE_URL, CFG_PREFIX
from invenio.testutils import make_test_suite, run_test_suite, \
                              test_web_page_content, merge_error_messages
from invenio import websubmit_file_stamper

class WebSubmitWebPagesAvailabilityTest(unittest.TestCase):
    """Check WebSubmit web pages whether they are up or not."""

    def test_submission_pages_availability(self):
        """websubmit - availability of submission pages"""

        baseurl = CFG_SITE_URL + '/submit/'

        _exports = ['', 'direct']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_publiline_pages_availability(self):
        """websubmit - availability of approval pages"""

        baseurl = CFG_SITE_URL

        _exports = ['/approve.py', '/publiline.py',
                    '/yourapprovals.py']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_your_submissions_pages_availability(self):
        """websubmit - availability of Your Submissions pages"""

        baseurl = CFG_SITE_URL

        _exports = ['/yoursubmissions.py']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_help_page_availability(self):
        """websubmit - availability of WebSubmit help page"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/help/submit-guide',
                                               expected_text="Submit Guide"))

class WebSubmitTestLegacyURLs(unittest.TestCase):
    """ Check that the application still responds to legacy URLs"""

    def test_legacy_help_page_link(self):
        """websubmit - legacy Submit Guide page link"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/help/submit',
                                               expected_text="Submit Guide"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/help/submit/',
                                               expected_text="Submit Guide"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/help/submit/index.en.html',
                                              expected_text="Submit Guide"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/help/submit/access.en.html',
                                              expected_text="Submit Guide"))

class WebSubmitXSSVulnerabilityTest(unittest.TestCase):
    """Test possible XSS vulnerabilities of the submission engine."""

    def test_xss_in_submission_doctype(self):
        """websubmit - no XSS vulnerability in doctype parameter"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/submit?doctype=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E',
                                               expected_text='Unable to find document type: &lt;SCRIPT&gt;alert("XSS")', username="jekyll",
                          password="j123ekyll"))

    def test_xss_in_submission_act(self):
        """websubmit - no XSS vulnerability in act parameter"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/submit?doctype=DEMOTHE&access=1_1&act=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E',
                                               expected_text='Invalid doctype and act parameters', username="jekyll",
                          password="j123ekyll"))

    def test_xss_in_submission_page(self):
        """websubmit - no XSS vulnerability in access parameter"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL +
                          '/submit?doctype=DEMOTHE&access=/../../../etc/passwd&act=SBI&startPg=1&ln=en&ln=en',                                               expected_text='Invalid parameters', username="jekyll",
                          password="j123ekyll"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL +
                          '/submit?doctype=DEMOTHE&access=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E&act=SBI',                                               expected_text='Invalid parameters', username="jekyll",
                          password="j123ekyll"))


class WebSubmitStampingTest(unittest.TestCase):
    """Test WebSubmit file stamping tool"""

    def test_stamp_coverpage(self):
        """websubmit - creation of a PDF cover page stamp (APIs)"""
        file_stamper_options = { 'latex-template'      : "demo-stamp-left.tex",
                                 'latex-template-var'  : {'REPORTNUMBER':'TEST-2010','DATE':'10/10/2000'},
                                 'input-file'          : CFG_PREFIX + "/lib/webtest/invenio/test.pdf",
                                 'output-file'         : "test-stamp-coverpage.pdf",
                                 'stamp'               : "coverpage",
                                 'layer'               : "foreground",
                                 'verbosity'           : 0,
                                 }
        try:
            (stamped_file_path_only, stamped_file_name) = \
                    websubmit_file_stamper.stamp_file(file_stamper_options)
        except:
            self.fail("Stamping failed")

        # Test that file is now bigger...
        assert os.path.getsize(os.path.join(stamped_file_path_only,
                                            stamped_file_name)) > 12695

    def test_stamp_firstpage(self):
        """websubmit - stamping first page of a PDF (APIs)"""
        file_stamper_options = { 'latex-template'      : "demo-stamp-left.tex",
                                 'latex-template-var'  : {'REPORTNUMBER':'TEST-2010','DATE':'10/10/2000'},
                                 'input-file'          : CFG_PREFIX + "/lib/webtest/invenio/test.pdf",
                                 'output-file'         : "test-stamp-firstpage.pdf",
                                 'stamp'               : "first",
                                 'layer'               : "background",
                                 'verbosity'           : 0,
                                 }
        try:
            (stamped_file_path_only, stamped_file_name) = \
                    websubmit_file_stamper.stamp_file(file_stamper_options)
        except:
            self.fail("Stamping failed")

        # Test that file is now bigger...
        assert os.path.getsize(os.path.join(stamped_file_path_only,
                                            stamped_file_name)) > 12695

    def test_stamp_allpages(self):
        """websubmit - stamping all pages of a PDF (APIs)"""
        file_stamper_options = { 'latex-template'      : "demo-stamp-left.tex",
                                 'latex-template-var'  : {'REPORTNUMBER':'TEST-2010','DATE':'10/10/2000'},
                                 'input-file'          : CFG_PREFIX + "/lib/webtest/invenio/test.pdf",
                                 'output-file'         : "test-stamp-allpages.pdf",
                                 'stamp'               : "all",
                                 'layer'               : "foreground",
                                 'verbosity'           : 0,
                                 }
        try:
            (stamped_file_path_only, stamped_file_name) = \
                    websubmit_file_stamper.stamp_file(file_stamper_options)
        except:
            self.fail("Stamping failed")

        # Test that file is now bigger...
        assert os.path.getsize(os.path.join(stamped_file_path_only,
                                            stamped_file_name)) > 12695


TEST_SUITE = make_test_suite(WebSubmitWebPagesAvailabilityTest,
                             WebSubmitTestLegacyURLs,
                             WebSubmitXSSVulnerabilityTest,
                             WebSubmitStampingTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
