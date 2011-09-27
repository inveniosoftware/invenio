# -*- coding: utf-8 -*-
##
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

"""WebSearch module web tests."""

import unittest
from selenium import webdriver

from invenio.config import CFG_SITE_URL
from invenio.testutils import make_test_suite, run_test_suite


class InvenioWebSearchWebTests(unittest.TestCase):
    """WebSearch web tests."""

    def setUp(self):
        """Set up for tests."""
        self.browser = webdriver.Firefox()

    def tearDown(self):
        """Clean after tests."""
        self.browser.quit()

    def test_search_ellis(self):
        """websearch - web test search for ellis"""
        self.browser.get(CFG_SITE_URL)
        p = self.browser.find_element_by_name("p")
        p.send_keys("ellis")
        p.submit()
        page_source = self.browser.page_source
        self.assertTrue('Thermal conductivity of dense quark matter ' \
                        'and cooling of stars' in page_source)


TEST_SUITE = make_test_suite(InvenioWebSearchWebTests, )

if __name__ == '__main__':
    run_test_suite(TEST_SUITE, warn_user=True)
