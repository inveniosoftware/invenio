# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

__revision__ = "$Id$"

from invenio.testutils import InvenioTestCase

from invenio.webcomment import calculate_start_date
from invenio.testutils import make_test_suite, run_test_suite

class TestCalculateStartDate(InvenioTestCase):
    """Test for calculating previous date."""

    def test_previous_year(self):
        """webcomment - calculate_start_date, values bigger than one year"""
        self.assert_(int(calculate_start_date('1y')[:4]) > 2007)
        self.assert_(int(calculate_start_date('13m')[:4]) > 2007)
        self.assert_(int(calculate_start_date('55w')[:4]) > 2007)
        self.assert_(int(calculate_start_date('370d')[:4]) > 2007)

    def test_with_random_values(self):
        """webcomment - calculate_start_date, various random values"""
        self.assert_(calculate_start_date('1d') > '2009-07-08 14:39:39')
        self.assert_(calculate_start_date('2w') > '2009-07-08 14:39:39')
        self.assert_(calculate_start_date('2w') > '2009-06-25 14:46:31')
        self.assert_(calculate_start_date('2y') > '2007-07-09 14:50:43')
        self.assert_(calculate_start_date('6m') > '2009-01-09 14:51:10')
        self.assert_(calculate_start_date('77d') > '2009-04-23 14:51:31')
        self.assert_(calculate_start_date('20d') > '2009-06-19 14:51:55')

class TestCommentFormats(InvenioTestCase):

    def test_conversions(self):
        from invenio.webcomment_templates import Template
        from invenio.webcomment_config import CFG_WEBCOMMENT_BODY_FORMATS, CFG_WEBCOMMENT_OUTPUT_FORMATS
        t = Template()


        test_body = """<div>\n\n\n<script>alert("xss");</script><h1>heading1\n\n\n</h1><div>\n\n\n<strong>strong</strong></div><plaintext>test</plaintext></div>"""

        ## BODY_FORMAT = HTML

        expected_output = """<div>\n\n\n<script>alert("xss");</script><h1>heading1\n\n\n</h1><div>\n\n\n<strong>strong</strong></div><plaintext>test</plaintext></div>"""
        output = t.tmpl_prepare_comment_body(test_body, CFG_WEBCOMMENT_BODY_FORMATS['HTML'], CFG_WEBCOMMENT_OUTPUT_FORMATS['HTML']['WEB'])
        assert expected_output == output

        expected_output = """<div>\n\n\n<script>alert("xss");</script><h1>heading1\n\n\n</h1><div>\n\n\n<strong>strong</strong></div><plaintext>test</plaintext></div>"""
        output = t.tmpl_prepare_comment_body(test_body, CFG_WEBCOMMENT_BODY_FORMATS['HTML'], CFG_WEBCOMMENT_OUTPUT_FORMATS['HTML']['EMAIL'])
        assert expected_output == output

        expected_output = """&lt;div&gt;\n\n\n&lt;script&gt;alert("xss");&lt;/script&gt;&lt;h1&gt;heading1\n\n\n&lt;/h1&gt;&lt;div&gt;\n\n\n&lt;strong&gt;strong&lt;/strong&gt;&lt;/div&gt;&lt;plaintext&gt;test&lt;/plaintext&gt;&lt;/div&gt;"""
        output = t.tmpl_prepare_comment_body(test_body, CFG_WEBCOMMENT_BODY_FORMATS['HTML'], CFG_WEBCOMMENT_OUTPUT_FORMATS['HTML']['CKEDITOR'])
        assert expected_output == output

        expected_output = """# heading1\n\n**strong**\n\ntest"""
        output = t.tmpl_prepare_comment_body(test_body, CFG_WEBCOMMENT_BODY_FORMATS['HTML'], CFG_WEBCOMMENT_OUTPUT_FORMATS['TEXT']['TEXTAREA'])
        assert expected_output == output

        expected_output = """# heading1\n\n**strong**\n\ntest"""
        output = t.tmpl_prepare_comment_body(test_body, CFG_WEBCOMMENT_BODY_FORMATS['HTML'], CFG_WEBCOMMENT_OUTPUT_FORMATS['TEXT']['EMAIL'])
        assert expected_output == output


        ## BODY_FORMAT = TEXT
        test_body = """Hello, <div>\n\n\n<script>alert("xss");</script><h1>heading1\n\n\n</h1><div>\n\n\n<strong>strong</strong></div><plaintext>test</plaintext></div>\n\n    testtest"""

        expected_output = """Hello, <div>\n\n\n<script>alert("xss");</script><h1>heading1\n\n\n</h1><div>\n\n\n<strong>strong</strong></div><plaintext>test</plaintext></div>\n\n    testtest"""
        output = t.tmpl_prepare_comment_body(test_body, CFG_WEBCOMMENT_BODY_FORMATS['TEXT'], CFG_WEBCOMMENT_OUTPUT_FORMATS['TEXT']['TEXTAREA'])
        assert expected_output == output

        expected_output = """Hello, <div>\n\n\n<script>alert("xss");</script><h1>heading1\n\n\n</h1><div>\n\n\n<strong>strong</strong></div><plaintext>test</plaintext></div>\n\n    testtest"""
        output = t.tmpl_prepare_comment_body(test_body, CFG_WEBCOMMENT_BODY_FORMATS['TEXT'], CFG_WEBCOMMENT_OUTPUT_FORMATS['TEXT']['EMAIL'])
        assert expected_output == output

        expected_output = """Hello, &lt;div&gt;<br/>\n<br/>\n<br/>\n&lt;script&gt;alert("xss");&lt;/script&gt;&lt;h1&gt;heading1<br/>\n<br/>\n<br/>\n&lt;/h1&gt;&lt;div&gt;<br/>\n<br/>\n<br/>\n&lt;strong&gt;strong&lt;/strong&gt;&lt;/div&gt;&lt;plaintext&gt;test&lt;/plaintext&gt;&lt;/div&gt;<br/>\n<br/>\n    testtest<br/>\n"""
        output = t.tmpl_prepare_comment_body(test_body, CFG_WEBCOMMENT_BODY_FORMATS['TEXT'], CFG_WEBCOMMENT_OUTPUT_FORMATS['HTML']['WEB'])
        assert expected_output == output

        expected_output = """Hello, &lt;div&gt;<br/>\n<br/>\n<br/>\n&lt;script&gt;alert("xss");&lt;/script&gt;&lt;h1&gt;heading1<br/>\n<br/>\n<br/>\n&lt;/h1&gt;&lt;div&gt;<br/>\n<br/>\n<br/>\n&lt;strong&gt;strong&lt;/strong&gt;&lt;/div&gt;&lt;plaintext&gt;test&lt;/plaintext&gt;&lt;/div&gt;<br/>\n<br/>\n    testtest<br/>\n"""
        output = t.tmpl_prepare_comment_body(test_body, CFG_WEBCOMMENT_BODY_FORMATS['TEXT'], CFG_WEBCOMMENT_OUTPUT_FORMATS['HTML']['EMAIL'])
        assert expected_output == output

        expected_output = """Hello, &amp;lt;div&amp;gt;&lt;br/&gt;\n&lt;br/&gt;\n&lt;br/&gt;\n&amp;lt;script&amp;gt;alert("xss");&amp;lt;/script&amp;gt;&amp;lt;h1&amp;gt;heading1&lt;br/&gt;\n&lt;br/&gt;\n&lt;br/&gt;\n&amp;lt;/h1&amp;gt;&amp;lt;div&amp;gt;&lt;br/&gt;\n&lt;br/&gt;\n&lt;br/&gt;\n&amp;lt;strong&amp;gt;strong&amp;lt;/strong&amp;gt;&amp;lt;/div&amp;gt;&amp;lt;plaintext&amp;gt;test&amp;lt;/plaintext&amp;gt;&amp;lt;/div&amp;gt;&lt;br/&gt;\n&lt;br/&gt;\n    testtest&lt;br/&gt;\n"""
        output = t.tmpl_prepare_comment_body(test_body, CFG_WEBCOMMENT_BODY_FORMATS['TEXT'], CFG_WEBCOMMENT_OUTPUT_FORMATS['HTML']['CKEDITOR'])
        assert expected_output == output

        ## BODY_FORMAT = MARKDOWN
        test_body = """An h2 header\n------------\n\nHere's a numbered list:\n\n 1. first item\n 2. second item\n 3. third item"""

        expected_output = """<h2>An h2 header</h2>\n\n<p>Here's a numbered list:</p>\n\n<ol>\n<li>first item</li>\n<li>second item</li>\n<li>third item</li>\n</ol>\n"""
        output = t.tmpl_prepare_comment_body(test_body, CFG_WEBCOMMENT_BODY_FORMATS['MARKDOWN'], CFG_WEBCOMMENT_OUTPUT_FORMATS['HTML']['WEB'])
        assert expected_output == output

        expected_output = """<h2>An h2 header</h2>\n\n<p>Here's a numbered list:</p>\n\n<ol>\n<li>first item</li>\n<li>second item</li>\n<li>third item</li>\n</ol>\n"""
        output = t.tmpl_prepare_comment_body(test_body, CFG_WEBCOMMENT_BODY_FORMATS['MARKDOWN'], CFG_WEBCOMMENT_OUTPUT_FORMATS['HTML']['EMAIL'])
        assert expected_output == output

        expected_output = """&lt;h2&gt;An h2 header&lt;/h2&gt;\n\n&lt;p&gt;Here\'s a numbered list:&lt;/p&gt;\n\n&lt;ol&gt;\n&lt;li&gt;first item&lt;/li&gt;\n&lt;li&gt;second item&lt;/li&gt;\n&lt;li&gt;third item&lt;/li&gt;\n&lt;/ol&gt;\n"""
        output = t.tmpl_prepare_comment_body(test_body, CFG_WEBCOMMENT_BODY_FORMATS['MARKDOWN'], CFG_WEBCOMMENT_OUTPUT_FORMATS['HTML']['CKEDITOR'])
        assert expected_output == output

        expected_output ="""An h2 header\n------------\n\nHere's a numbered list:\n\n 1. first item\n 2. second item\n 3. third item"""
        output = t.tmpl_prepare_comment_body(test_body, CFG_WEBCOMMENT_BODY_FORMATS['MARKDOWN'], CFG_WEBCOMMENT_OUTPUT_FORMATS['TEXT']['TEXTAREA'])
        assert expected_output == output

        expected_output ="""An h2 header\n------------\n\nHere's a numbered list:\n\n 1. first item\n 2. second item\n 3. third item"""
        output = t.tmpl_prepare_comment_body(test_body, CFG_WEBCOMMENT_BODY_FORMATS['MARKDOWN'], CFG_WEBCOMMENT_OUTPUT_FORMATS['TEXT']['EMAIL'])
        assert expected_output == output

        return output


TEST_SUITE = make_test_suite(TestCalculateStartDate, TestCommentFormats)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
