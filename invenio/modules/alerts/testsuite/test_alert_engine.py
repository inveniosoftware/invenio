# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2010, 2011, 2013 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Unit tests for the WebAlert engine."""

__revision__ = \
    "$Id$"


from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

RecordHTMLParser = lazy_import('invenio.legacy.webalert.htmlparser:RecordHTMLParser')


class TestWashHTMLtoText(InvenioTestCase):
    """Test HTML to text conversion."""

    def test_wash_html_to_text(self):
        """webalert - stripping HTML markup for alert emails"""
        from invenio.config import CFG_SITE_URL
        htparser = RecordHTMLParser()
        htparser.feed('''<style type="text/css">
                    <!--
                       div.thumbMosaic {display:inline;}
                       div.thumbMosaic span{display:none;}
                       div.thumbMosaic:hover span{display:inline;position:absolute;}
                     -->
                     </style><!--START_NOT_FOR_TEXT--><strong>Abracadabra!</strong><!--END_NOT_FOR_TEXT--><br/><a class="moreinfo" href="%(CFG_SITE_URL)s">Detailed Record</a>''' % {'CFG_SITE_URL': CFG_SITE_URL})

        self.assertEqual('\nDetailed record : <%s>' % CFG_SITE_URL, htparser.result)

    def test_entity_ref_conversion(self):
        """webalert - convert entity reference to text (Eg: '&lt;' -> '<')"""
        htparser = RecordHTMLParser()
        htparser.feed('<strong>a &lt; b &gt; c</strong> &copy;CERN')
        self.assertEqual('a < b > c ©CERN', htparser.result)

    def test_character_ref_conversion(self):
        """webalert - convert character reference to text (Eg: '&#97;' -> 'a')"""
        htparser = RecordHTMLParser()
        htparser.feed('&#80;ython is co&#111;l')
        self.assertEqual('Python is cool', htparser.result)

TEST_SUITE = make_test_suite(TestWashHTMLtoText)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
