# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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

from invenio.config import CFG_SITE_URL
from invenio.testutils import make_test_suite, run_test_suite, \
                              test_web_page_content, merge_error_messages

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

TEST_SUITE = make_test_suite(BibIndexAdminWebPagesAvailabilityTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
