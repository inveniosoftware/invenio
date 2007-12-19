# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

"""BibConvert Regression Test Suite."""

__revision__ = "$Id$"

import unittest

from invenio.config import weburl
from invenio.testutils import make_test_suite, warn_user_about_tests_and_run, \
                              test_web_page_content, merge_error_messages, \
                              test_web_page_existence

class BibConvertWebPagesAvailabilityTest(unittest.TestCase):
    """Check BibConvert web pages whether they are up or not."""

    def test_availability_bibconvert_admin_guide(self):
        """bibconvert - availability of BibConvert Admin Guide page"""
	self.assertEqual([],
                         test_web_page_content(weburl + '/help/admin/bibconvert-admin-guide',
                                               expected_text="BibConvert Admin Guide"))
        return

    def test_availability_bibconvert_admin_guide_parts(self):
        """bibconvert - availability of BibConvert Admin Guide parts"""
        test_web_page_existence(weburl + '/admin/bibconvert/bibtex.cfg')
        test_web_page_existence(weburl + '/admin/bibconvert/dcq.cfg')
        test_web_page_existence(weburl + '/admin/bibconvert/dcq.dat')
        test_web_page_existence(weburl + '/admin/bibconvert/dcxml-to-marcxml.cfg')
        test_web_page_existence(weburl + '/admin/bibconvert/example_oaimarc2xm.xsl')
        test_web_page_existence(weburl + '/admin/bibconvert/example_oaimarc2xm_collID.kb')
        test_web_page_existence(weburl + '/admin/bibconvert/sample.cfg')
        test_web_page_existence(weburl + '/admin/bibconvert/sample.dat')
        test_web_page_existence(weburl + '/admin/bibconvert/sample.kb')

    def test_availability_bibconvert_hacking_pages(self):
        """bibconvert - availability of BibConvert Hacking Guide pages"""
	self.assertEqual([],
                         test_web_page_content(weburl + '/help/hacking/bibconvert-internals',
                                               expected_text="BibConvert Internals"))
	self.assertEqual([],
                         test_web_page_content(weburl + '/help/hacking/bibconvert-api',
                                               expected_text="BibConvert API"))
        return

test_suite = make_test_suite(BibConvertWebPagesAvailabilityTest)

if __name__ == "__main__":
    warn_user_about_tests_and_run(test_suite)
