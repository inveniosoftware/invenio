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

"""WebAlert Regression Test Suite."""

__revision__ = "$Id$"

import unittest

from invenio.config import CFG_SITE_URL
from invenio.testutils import make_test_suite, run_test_suite, \
                              test_web_page_content, merge_error_messages
from invenio.htmlparser import get_as_text

class WebAlertWebPagesAvailabilityTest(unittest.TestCase):
    """Check WebAlert web pages whether they are up or not."""

    def test_your_alerts_pages_availability(self):
        """webalert - availability of Your Alerts pages"""

        baseurl = CFG_SITE_URL + '/youralerts/'

        _exports = ['', 'display', 'input', 'modify', 'list', 'add',
                    'update', 'remove']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

class WebAlertHTMLToTextTest(unittest.TestCase):
    """Check that HTML is properly converted to text."""

    def test_your_alerts_pages_availability(self):
        """webalert - HTML to text conversion"""

        self.assertEqual("High energy cosmic rays striking atoms at the top of the atmosphere give the rise to showers of particles striking the Earth's surface \nDes rayons cosmiques de haute energie heurtent des atomes dans la haute atmosphere et donnent ainsi naissance a des gerbes de particules projetees sur la surface terrestre \n10 May 1999 \nPicture number: CERN-DI-9905005", get_as_text(5))

        self.assertEqual("Quasinormal modes of Reissner-Nordstrom Anti-de Sitter Black Holes / Wang, B ; Lin, C Y ; Abdalla, E [hep-th/0003295] \nComplex frequencies associated with quasinormal modes for large Reissner-Nordstr$\\ddot{o}$m Anti-de Sitter black holes have been computed. [...] \nPublished in Phys. Lett., B :481 2000 79-88", get_as_text(74))


TEST_SUITE = make_test_suite(WebAlertWebPagesAvailabilityTest,
                             WebAlertHTMLToTextTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
