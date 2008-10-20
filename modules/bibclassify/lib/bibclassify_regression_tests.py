# -*- coding: utf-8 -*-
##
## $Id$
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

"""BibClassify Regression Test Suite."""

import unittest

from invenio.config import CFG_SITE_URL
from invenio.testutils import make_test_suite, run_test_suite, \
                              test_web_page_content, merge_error_messages, \
                              test_web_page_existence

class BibClassifyWebPagesAvailabilityTest(unittest.TestCase):
    """Check BibClassify web pages whether they are up or not."""

    def test_availability_bibclassify_admin_guide(self):
        """bibclassify - availability of BibClassify Admin Guide page"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/help/admin/bibclassify-admin-guide',
                                               expected_text="BibClassify Admin Guide"))
        return

    def test_availability_bibclassify_admin_guide_images(self):
        """bibclassify - availability of BibClassify Admin Guide images"""
        test_web_page_existence(CFG_SITE_URL + '/img/admin/bibclassify-admin-guide-cloud.jpeg')

    def test_availability_bibclassify_hacking_pages(self):
        """bibclassify - availability of BibClassify Hacking Guide pages"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/help/hacking/bibclassify-internals',
                                               expected_text="BibClassify Internals"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/help/hacking/bibclassify-hep-taxonomy',
                                               expected_text="The HEP taxonomy: rationale and extensions"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/help/hacking/bibclassify-extraction-algorithm',
                                               expected_text="The code behind BibClassify: the extraction algorithm"))
        return

TEST_SUITE = make_test_suite(BibClassifyWebPagesAvailabilityTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
