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

"""Unit tests for the WebAlert engine."""

__revision__ = \
    "$Id$"

import unittest
from invenio.config import CFG_SITE_URL
from invenio.testutils import make_test_suite, run_test_suite
from invenio.htmlparser import RecordHTMLParser

class TestWashHTMLtoText(unittest.TestCase):
    """Test HTML to text conversion."""

    def test_wash_html_to_text(self):
        """webalert - stripping HTML markup for alert emails"""
        htparser = RecordHTMLParser()
        htparser.feed('''<style type="text/css">
                    <!--
                       div.thumbMosaic {display:inline;}
                       div.thumbMosaic span{display:none;}
                       div.thumbMosaic:hover span{display:inline;position:absolute;}
                     -->
                     </style><!--START_NOT_FOR_TEXT--><strong>Abracadabra!</strong><!--END_NOT_FOR_TEXT--><br/><a class="moreinfo" href="%(CFG_SITE_URL)s">Detailed Record</a>''' % {'CFG_SITE_URL': CFG_SITE_URL})

        self.assertEqual('\nDetailed record : <%s>' % CFG_SITE_URL, htparser.result)

TEST_SUITE = make_test_suite(TestWashHTMLtoText)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

