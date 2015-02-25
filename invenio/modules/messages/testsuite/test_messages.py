# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2013 CERN.
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

"""Unit tests for WebMessage."""

__revision__ = \
    "$Id$"


from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase
webmessage_mailutils = lazy_import('invenio.utils.mail')


class TestQuotingMessage(InvenioTestCase):
    """Test for quoting messages."""

    def test_simple_quoting_per_block(self):
        """webmessage - test quoting simple message (HTML, per block)"""
        text = """Dear romeo
I received your mail
>>Would you like to come with me to the restaurant?
Of course!
>>>>When could we get together?
Reply to my question please.
    see you..."""
        expected_text = """Dear romeo<br/>
I received your mail<br/>
<div class="commentbox">
\tWould you like to come with me to the restaurant?<br/>
</div>
Of course!<br/>
<div class="commentbox">
\t<div class="commentbox">
\t\tWhen could we get together?<br/>
\t</div>
</div>
Reply to my question please.<br/>
    see you...<br/>
"""
        res =  webmessage_mailutils.email_quoted_txt2html(text,
                                                          tabs_before=0,
                                                          indent_txt='>>',
                                                          linebreak_txt="\n",
                                                          indent_html=('<div class="commentbox">', "</div>"),
                                                          linebreak_html='<br/>')
        self.assertEqual(res, expected_text)

    def test_simple_quoting_per_line(self):
        """webmessage - test quoting simple message (HTML, per line)"""
        text = """Dear romeo
I received your mail
>>Would you like to come with me to the restaurant?
>>I discovered a really nice one.
Of course!
>>>>When could we get together?
Reply to my question please.
    see you..."""
        expected_text = """Dear romeo&nbsp;<br/>
I received your mail&nbsp;<br/>
<blockquote><div>Would you like to come with me to the restaurant?&nbsp;</div></blockquote>&nbsp;<br/>
<blockquote><div>I discovered a really nice one.&nbsp;</div></blockquote>&nbsp;<br/>
Of course!&nbsp;<br/>
<blockquote><div><blockquote><div>When could we get together?&nbsp;</div></blockquote>&nbsp;</div></blockquote>&nbsp;<br/>
Reply to my question please.&nbsp;<br/>
    see you...&nbsp;<br/>
"""
        res =  webmessage_mailutils.email_quoted_txt2html(text,
                                                          tabs_before=0,
                                                          indent_txt='>>',
                                                          linebreak_txt="\n",
                                                          indent_html=('<blockquote><div>', '&nbsp;</div></blockquote>'),
                                                          linebreak_html="&nbsp;<br/>",
                                                          indent_block=False)
        self.assertEqual(res, expected_text)


    def test_quoting_message(self):
        """webmessage - test quoting message (text)"""
        text = """C'est un lapin, lapin de bois.
>>Quoi?
Un cadeau.
>>What?
A present.
>>Oh, un cadeau"""

        expected_text = """>>C'est un lapin, lapin de bois.
>>>>Quoi?
>>Un cadeau.
>>>>What?
>>A present.
>>>>Oh, un cadeau
"""

        res = webmessage_mailutils.email_quote_txt(text,
                                                   indent_txt='>>',
                                                   linebreak_input="\n",
                                                   linebreak_output="\n")
        self.assertEqual(res, expected_text)

    def test_indenting_rule_message(self):
        """webmessage - return email-like indenting rule"""
        text = """>>Brave Sir Robin ran away...
<img src="malicious_script"/>*No!*
>>bravely ran away away...
I didn't!*<script>malicious code</script>
>>When danger reared its ugly head, he bravely turned his tail and fled.
<form onload="malicious"></form>*I never did!*
"""
        expected_text = """>>Brave Sir Robin ran away...
&lt;img src="malicious_script" /&gt;*No!*
>>bravely ran away away...
I didn't!*&lt;script&gt;malicious code&lt;/script&gt;
>>When danger reared its ugly head, he bravely turned his tail and fled.
&lt;form onload="malicious"&gt;&lt;/form&gt;*I never did!*
"""

        res = webmessage_mailutils.escape_email_quoted_text(text,
                                                            indent_txt='>>',
                                                            linebreak_txt='\n')
        self.assertEqual(res, expected_text)


TEST_SUITE = make_test_suite(TestQuotingMessage)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
