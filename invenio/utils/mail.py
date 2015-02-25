# -*- coding: utf-8 -*-

# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

""" Library for quoting text, email style """

__revision__ = "$Id$"

import cgi
from .html import HTMLWasher
from HTMLParser import HTMLParseError


def email_quoted_txt2html(text,
                          tabs_before=0,
                          indent_txt='>>',
                          linebreak_txt="\n",
                          indent_html=('<div class="commentbox">', "</div>"),
                          linebreak_html='<br/>',
                          indent_block=True):
    """
    Takes a typical mail quoted text, e.g.::
        hello,
        you told me:
        >> Your mother was a hamster and your father smelt of elderberries
        I must tell you that I'm not convinced. Then in this discussion:
        >>>> Is there someone else up there we could talk to?
        >> No. Now, go away, or I shall taunt you a second time-a!
        I think we're not going to be friends!

    and return an html formatted output, e.g.::
        hello,<br/>
        you told me:<br/>
        <div>
          Your mother was a hamster and your father smelt of elderberries
        </div>
        I must tell you that I'm not convinced. Then in this discussion:
        <div>
          <div>
            Is there someone else up there we could talk to?
          </div>
          No. Now, go away, or I shall taunt you a second time-a!
        </div>
        I think we're not going to be friends!

    The behaviour is different when C{indent_block} is C{True} or C{False}.
    When C{True} the when C{indent_html} is only added at each change of
    level of indentation, while it is added for each line when C{False}.
    For eg::
        >> a
        >> b
        >>>> c

    would result in (if C{True})::
        <div class="commentbox">
            a<br/>
            b<br/>
            <div class="commentbox">
                c<br/>
            </div>
        </div>

    or would be (if C{False})::
        <div class="commentbox"> a</div><br/>
        <div class="commentbox"> b</div><br/>
        <div class="commentbox"><div class="commentbox"> c</div></div><br/>

    @param text: the text in quoted format
    @param tabs_before: number of tabulations before each line
    @param indent_txt: quote separator in email (default:'>>')
    @param linebreak_txt: line separator in email
    @param indent_html: tuple of (opening, closing) html tags.
                        default: ('<div class="commentbox">', "</div>")
    @param linebreak_html: line separator in html (default: '<br/>')
    @param indent_block: if indentation should be done per 'block'
                         i.e. only at changes of indentation level
                         (+1, -1) or at each line.
    @return: string containing html formatted output
    """
    washer = HTMLWasher()

    final_body = ""
    nb_indent = 0
    text = text.strip('\n')
    lines = text.split(linebreak_txt)
    for line in lines:
        new_nb_indent = 0
        while True:
            if line.startswith(indent_txt):
                new_nb_indent += 1
                line = line[len(indent_txt):]
            else:
                break
        if indent_block:
            if (new_nb_indent > nb_indent):
                for dummy in range(nb_indent, new_nb_indent):
                    final_body += tabs_before*"\t" + indent_html[0] + "\n"
                    tabs_before += 1
            elif (new_nb_indent < nb_indent):
                for dummy in range(new_nb_indent, nb_indent):
                    tabs_before -= 1
                    final_body += (tabs_before)*"\t" + indent_html[1] + "\n"
            else:
                final_body += (tabs_before)*"\t"
        else:
            final_body += tabs_before*"\t" + new_nb_indent * indent_html[0]
        try:
            line = washer.wash(line)
        except HTMLParseError:
            # Line contained something like "foo<bar"
            line = cgi.escape(line)
        if indent_block:
            final_body += tabs_before*"\t"
        final_body += line
        if not indent_block:
            final_body += new_nb_indent * indent_html[1]
        final_body += linebreak_html + "\n"
        nb_indent = new_nb_indent
    if indent_block:
        for dummy in range(0, nb_indent):
            tabs_before -= 1
            final_body += (tabs_before)*"\t" + "</div>\n"
    return final_body


def email_quote_txt(text,
                    indent_txt='>>',
                    linebreak_input="\n",
                    linebreak_output="\n"):
    """
    Takes a text and returns it in a typical mail quoted format, e.g.::
        C'est un lapin, lapin de bois.
        >>Quoi?
        Un cadeau.
        >>What?
        A present.
        >>Oh, un cadeau.

    will return::
        >>C'est un lapin, lapin de bois.
        >>>>Quoi?
        >>Un cadeau.
        >>>>What?
        >>A present.
        >>>>Oh, un cadeau.

    @param text: the string to quote
    @param indent_txt: the string used for quoting (default: '>>')
    @param linebreak_input: in the text param, string used for linebreaks
    @param linebreak_output: linebreak used for output
    @return: the text as a quoted string
    """
    if (text == ""):
        return ""
    lines = text.split(linebreak_input)
    text = ""
    for line in lines:
        text += indent_txt + line + linebreak_output
    return text


def escape_email_quoted_text(text, indent_txt='>>', linebreak_txt='\n'):
    """
    Escape text using an email-like indenting rule.
    As an example, this text::
        >>Brave Sir Robin ran away...
        <img src="malicious_script />*No!*
        >>bravely ran away away...
        I didn't!*<script>malicious code</script>
        >>When danger reared its ugly head, he bravely turned his tail and fled.
        <form onload="malicious"></form>*I never did!*

    will be escaped like this::
        >>Brave Sir Robin ran away...
        &lt;img src="malicious_script /&gt;*No!*
        >>bravely ran away away...
        I didn't!*&lt;script&gt;malicious code&lt;/script&gt;
        >>When danger reared its ugly head, he bravely turned his tail and fled.
        &lt;form onload="malicious"&gt;&lt;/form&gt;*I never did!*

    @param text: the string to escape
    @param indent_txt: the string used for quoting
    @param linebreak_txt: in the text param, string used for linebreaks
    """
    washer = HTMLWasher()
    lines = text.split(linebreak_txt)
    output = ''
    for line in lines:
        line = line.strip()
        nb_indent = 0
        while True:
            if line.startswith(indent_txt):
                nb_indent += 1
                line = line[len(indent_txt):]
            else:
                break
        output += (nb_indent * indent_txt) + washer.wash(line, render_unallowed_tags=True) + linebreak_txt
        nb_indent = 0
    return output[:-1]
