# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

"""WebAuthorProfile functional/regression test suite."""

from invenio.config import CFG_SITE_URL
from invenio.testutils import make_test_suite, run_test_suite, \
    test_web_page_content, InvenioTestCase


class WebAuthorProfilePageTest(InvenioTestCase):
    """Check /author profile pages."""

    def test_author_page_klebanov(self):
        """webauthorprofile - /author/profile/Klebanov,%20Igor%20R"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/author/profile/Klebanov,%20Igor%20R',
                                           expected_text=['Klebanov, Igor R']))


TEST_SUITE = make_test_suite(WebAuthorProfilePageTest,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
