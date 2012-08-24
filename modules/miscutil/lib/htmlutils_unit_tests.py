# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""Unit tests for htmlutils library."""

__revision__ = "$Id$"

import unittest

from invenio.htmlutils import HTMLWasher, nmtoken_from_string, \
     remove_html_markup, create_html_select, \
     CFG_TIDY_INSTALLED, \
     CFG_BEAUTIFULSOUP_INSTALLED, tidy_html
from invenio.testutils import make_test_suite, run_test_suite

class XSSEscapingTest(unittest.TestCase):
    """Test functions related to the prevention of XSS attacks."""

    def __init__(self, methodName='test'):
        self.washer = HTMLWasher()
        unittest.TestCase.__init__(self, methodName)

    def test_forbidden_formatting_tags(self):
        """htmlutils - washing of tags altering formatting of a page (e.g. </html>)"""
        test_str = """</html></body></pre>"""
        self.assertEqual(self.washer.wash(html_buffer=test_str),
                         '')
        self.assertEqual(self.washer.wash(html_buffer=test_str,
                                          render_unallowed_tags=True),
                         '&lt;/html&gt;&lt;/body&gt;&lt;/pre&gt;')

    def test_forbidden_script_tags(self):
        """htmlutils - washing of tags defining scripts (e.g. <script>)"""
        test_str = """<script>malicious_function();</script>"""
        self.assertEqual(self.washer.wash(html_buffer=test_str),
                         '')
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

class CharactersEscapingTest(unittest.TestCase):
    """Test functions related to escaping reserved or forbidden characters """

    def test_convert_string_to_nmtoken(self):
        """htmlutils - converting string to Nmtoken"""

        # TODO: possibly extend this test to include 'extenders' and
        # 'combining characters' as defined in
        # http://www.w3.org/TR/2000/REC-xml-20001006#NT-Nmtoken

        ascii_str = "".join([chr(i) for i in range(0, 256)])
        nmtoken = nmtoken_from_string(ascii_str)
        for char in nmtoken:
            self.assert_(char in ['.', '-', '_', ':'] or char.isalnum())

class HTMLWashingTest(unittest.TestCase):
    """Test functions related to general washing of HTML source"""

    def __init__(self, methodName='test'):
        self.washer = HTMLWasher()
        unittest.TestCase.__init__(self, methodName)

    def test_wash_html(self):
        """htmlutils - washing HTML tags"""

        # Simple test case
        test_str = 'Spam and <b><blink>eggs</blink></b>'
        self.assertEqual(self.washer.wash(html_buffer=test_str),
                         'Spam and <b>eggs</b>')

        # Show 'escaped' tags
        test_str = 'Spam and <b><blink>eggs</blink></b>'
        self.assertEqual(self.washer.wash(html_buffer=test_str,
                                          render_unallowed_tags=True),
                         'Spam and <b>&lt;blink&gt;eggs&lt;/blink&gt;</b>')

        # Keep entity and character references
        test_str = '<b> a &lt; b &gt; c </b> &#247;'
        self.assertEqual(self.washer.wash(html_buffer=test_str),
                         '<b> a &lt; b &gt; c </b> &#247;')

        # Remove content of <script> tags
        test_str = '<script type="text/javacript">alert("foo")</script>bar'
        self.assertEqual(self.washer.wash(html_buffer=test_str),
                         'bar')
        test_str = '<script type="text/javacript"><!--alert("foo")--></script>bar'
        self.assertEqual(self.washer.wash(html_buffer=test_str),
                         'bar')

        # Remove content of <style> tags
        test_str = '<style>.myclass {color:#f00}</style><span class="myclass">styled text</span>'
        self.assertEqual(self.washer.wash(html_buffer=test_str),
                         'styled text')
        test_str = '<style><!-- .myclass {color:#f00} --></style><span class="myclass">styled text</span>'
        self.assertEqual(self.washer.wash(html_buffer=test_str),
                         'styled text')

class HTMLTidyingTest(unittest.TestCase):
    """Test functions related to tidying up HTML source"""

    html_buffer_1 = 'test</blockquote >'
    html_buffer_2 = '<blockquote >test </div><div>test2'
    html_buffer_3 = '''<UL>
<LI>
<UL>
<LI><A HREF="rememberwhenb.html">Next</A>
<LI><A HREF="daysofourlives.html">Back</A>
<LI><A HREF="newstuff.html">New Stuff</A>
</UL>
</UL>

<UL>
<LI>Merge adjacent lists
</UL>

<UL>

<UL>
<LI><A HREF="one.html">One</A>
<LI><A HREF="two.html">Two</A>
<LI><A HREF="three.html">Three</A>
</UL>''' # Input test 427841 from Tidy

    if CFG_TIDY_INSTALLED:
        def test_tidy_html_with_utidylib(self):
            """htmlutils - Tidying up HTML with µTidylib """
            res1 = tidy_html(self.html_buffer_1, 'utidylib')
            res2 = tidy_html(self.html_buffer_2, 'utidylib')
            res3 = tidy_html(self.html_buffer_3, 'utidylib')
            self.assertEqual(res1.replace('\n', '').replace(' ', ''),
                            'test')
            self.assertEqual(res2.replace('\n', '').replace(' ', ''),
                            '<blockquote>test<div>test2</div></blockquote>')
            self.assertEqual(res3.replace('\n', '').replace(' ', ''),
                            '<ul><li><ul><li><ahref="rememberwhenb.html">Next</a></li><li><ahref="daysofourlives.html">Back</a></li><li><ahref="newstuff.html">NewStuff</a></li></ul></li></ul><ul><li>Mergeadjacentlists</li></ul><divstyle="margin-left:2em"><ul><li><ahref="one.html">One</a></li><li><ahref="two.html">Two</a></li><li><ahref="three.html">Three</a></li></ul></div>')

    if CFG_BEAUTIFULSOUP_INSTALLED:
        def test_tidy_html_with_beautifulsoup(self):
            """htmlutils - Tidying up HTML with BeautifulSoup"""
            res1 = tidy_html(self.html_buffer_1, 'beautifulsoup')
            res2 = tidy_html(self.html_buffer_2, 'beautifulsoup')
            res3 = tidy_html(self.html_buffer_3, 'beautifulsoup')
            self.assertEqual(res1.replace('\n', '').replace(' ', ''),
                            'test')
            self.assertEqual(res2.replace('\n', '').replace(' ', ''),
                            '<blockquote>test<div>test2</div></blockquote>')
            self.assertEqual(res3.replace('\n', '').replace(' ', ''),
                            '<ul><li><ul><li><ahref="rememberwhenb.html">Next</a></li><li><ahref="daysofourlives.html">Back</a></li><li><ahref="newstuff.html">NewStuff</a></li></ul></li></ul><ul><li>Mergeadjacentlists</li></ul><ul><ul><li><ahref="one.html">One</a></li><li><ahref="two.html">Two</a></li><li><ahref="three.html">Three</a></li></ul></ul>')

    def test_tidy_html_with_unknown_lib(self):
        """htmlutils - Tidying up HTML with non existing library"""
        res = tidy_html(self.html_buffer_1, 'foo')
        self.assertEqual(res.replace('\n', '').replace(' ', ''),
                         self.html_buffer_1.replace('\n', '').replace(' ', ''))

class HTMLMarkupRemovalTest(unittest.TestCase):
    """Test functions related to removing HTML markup."""

    def test_remove_html_markup_empty(self):
        """htmlutils - remove HTML markup, empty replacement"""
        test_input = 'This is <a href="test">test</a>.'
        test_expected = 'This is test.'
        self.assertEqual(remove_html_markup(test_input, ''),
                         test_expected)

    def test_remove_html_markup_replacement(self):
        """htmlutils - remove HTML markup, some replacement"""
        test_input = 'This is <a href="test">test</a>.'
        test_expected = 'This is XtestX.'
        self.assertEqual(remove_html_markup(test_input, 'X'),
                         test_expected)

class HTMLAutomaticLinksTransformation(unittest.TestCase):
    """Test functions related to transforming links into HTML context"""

    def __init__(self, methodName='test'):
        self.washer = HTMLWasher()
        unittest.TestCase.__init__(self, methodName)

    def test_transform_link(self):
        """htmlutils - transforming a link"""
        body_input = 'https://cdsweb.cern.ch/collection/Multimedia%20%26%20Outreach?ln=es'
        body_expected = '<a href="https://cdsweb.cern.ch/collection/Multimedia%20%26%20Outreach?ln=es">https://cdsweb.cern.ch/collection/Multimedia%20%26%20Outreach?ln=es</a>'
        self.assertEqual(self.washer.wash(html_buffer=body_input,
                                          automatic_link_transformation=True),
                         body_expected)

    def test_transform_several_links(self):
        """htmlutils - transforming several links"""
        body_input = 'some text https://cdsweb.cern.ch/collection/Videos?ln=es more text https://cdsweb.cern.ch/search?p=%27CERN+News'
        body_expected = 'some text <a href="https://cdsweb.cern.ch/collection/Videos?ln=es">https://cdsweb.cern.ch/collection/Videos?ln=es</a> more text <a href="https://cdsweb.cern.ch/search?p=%27CERN">https://cdsweb.cern.ch/search?p=%27CERN</a>+News'
        self.assertEqual(self.washer.wash(html_buffer=body_input,
                                          automatic_link_transformation=True),
                         body_expected)

    def test_transform_just_valid_links(self):
        """htmlutils - transforming just valid links"""
        body_input = body_input = 'some text https://cdsweb.cern.ch/collection/Videos?ln=es more text https://cdsweb..cern/search?p=%27CERN+News'
        body_expected = 'some text <a href="https://cdsweb.cern.ch/collection/Videos?ln=es">https://cdsweb.cern.ch/collection/Videos?ln=es</a> more text https://cdsweb..cern/search?p=%27CERN+News'
        self.assertEqual(self.washer.wash(html_buffer=body_input,
                                          automatic_link_transformation=True),
                         body_expected)

    def test_not_transform_link(self):
        """htmlutils - not transforming a link"""
        body_input = '<a href="https://cdsweb.cern.ch/collection/Multimedia%20%26%20Outreach?ln=es">Multimedia</a>'
        body_expected = '<a href="https://cdsweb.cern.ch/collection/Multimedia%20%26%20Outreach?ln=es">Multimedia</a>'
        self.assertEqual(self.washer.wash(html_buffer=body_input,
                                          automatic_link_transformation=True),
                         body_expected)

class HTMLCreation(unittest.TestCase):
    """Test functions related to creation of HTML markup."""

    def test_create_html_select(self):
        """htmlutils - create HTML <select> list """
        self.assertEqual(create_html_select(["foo", "bar"], selected="bar", name="baz"),
                         '<select name="baz"><option value="foo">foo</option>\n<option selected="selected" value="bar">bar</option></select>')


TEST_SUITE = make_test_suite(XSSEscapingTest,
                             CharactersEscapingTest,
                             HTMLWashingTest,
                             HTMLMarkupRemovalTest,
                             HTMLTidyingTest,
                             HTMLAutomaticLinksTransformation,
                             HTMLCreation)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
