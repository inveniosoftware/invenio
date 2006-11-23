# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

"""Unit tests for htmlutils library."""

__revision__ = "$Id$"

import unittest

from invenio import dbquery
from invenio.htmlutils import HTMLWasher

class XSSEscapingTest(unittest.TestCase):
    """Test functions related to the prevention of XSS attacks."""
    
    def __init__(self, methodName='test'):
        self.washer = HTMLWasher()
        unittest.TestCase.__init__(self, methodName)
    
    def test_forbidden_formatting_tags(self):
        """htmlutils - washing of tags altering formatting of a page (e.g. </html>"""
        test_str = """</html></body></div></pre>"""
        self.assertEqual(self.washer.wash(html_buffer=test_str),
                         '')
        self.assertEqual(self.washer.wash(html_buffer=test_str,
                                          render_unallowed_tags=True),
                         '&lt;/html&gt;&lt;/body&gt;&lt;/div&gt;&lt;/pre&gt;')
                         
    def test_forbidden_script_tags(self):
        """htmlutils - washing of tags defining scripts (e.g. <script>)"""
        test_str = """<script>malicious_function();</script>"""
        self.assertEqual(self.washer.wash(html_buffer=test_str),
                         'malicious_function();')
        self.assertEqual(self.washer.wash(html_buffer=test_str,
                                          render_unallowed_tags=True),
                         '&lt;script&gt;malicious_function();&lt;/script&gt;')
    
    def test_forbidden_attributes(self):
        """htmlutils - washing of forbidden attributes in allowed tags (e.g. onLoad)"""
        # onload
        test_str = """<p onload="javascript:malicious_functtion();">"""
        self.assertEqual(self.washer.wash(html_buffer=test_str), '<p>') 
        # tricky: css calling a javascript
        test_str = """<p style="background: url('http://malicious_site.com/malicious_script.js');">"""
        self.assertEqual(self.washer.wash(html_buffer=test_str), '<p>')

    def test_fake_url(self):
        """htmlutils - washing of fake URLs which execute scripts"""
        test_str = """<a href="javascript:malicious_function();">link</a>"""
        self.assertEqual(self.washer.wash(html_buffer=test_str),
                         '<a href="">link</a>')
        # Pirates could encode ascii values, or use uppercase letters...
        test_str = """<a href="&#106;a&#118;asCRi&#112;t:malicious_function();">link</a>"""
        self.assertEqual(self.washer.wash(html_buffer=test_str),
                         '<a href="">link</a>')
        # MSIE treats 'java\ns\ncript:' the same way as 'javascript:'
        # Here we test with:
        # j
        #     avas
        #   crIPt :
        test_str = """<a href="&#106;\n    a&#118;as\n  crI&#80;t :malicious_function();">link</a>"""
        self.assertEqual(self.washer.wash(html_buffer=test_str),
                         '<a href="">link</a>')
                                 
def create_test_suite():
    """Return test suite for the user handling."""
    return unittest.TestSuite((
        unittest.makeSuite(XSSEscapingTest,'test'),
        ))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())


