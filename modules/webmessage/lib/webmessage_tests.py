# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

"""Unit tests for WebMessage."""

__revision__ = \
    "$Id$"

import unittest

from invenio import webmessage_mailutils
from invenio.testutils import make_test_suite, run_test_suite

class TestQuotingMessage(unittest.TestCase):
    """Test for quoting messages."""

    def test_simple_quoting(self):
        """webmessage - test quoting simple message"""
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

    def test_quoting_message(self):
        """webmessage - test quoting message"""
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
