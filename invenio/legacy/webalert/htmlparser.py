# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""HTML parser for records."""

__revision__ = "$Id$"

import re
from HTMLParser import HTMLParser
import textwrap
from six.moves import html_entities

from invenio.config import \
     CFG_WEBALERT_MAX_NUM_OF_CHARS_PER_LINE_IN_ALERT_EMAIL, \
     CFG_SITE_LANG
from invenio.modules.formatter import format_record
from invenio.utils.html import remove_html_markup
from invenio.base.i18n import gettext_set_language

whitespaces_pattern = re.compile(r'[ \t]+')

def wrap(text):
    """Limits the number of characters per line in given text.
    The function does not preserve new lines.
    """
    lines = textwrap.wrap(text, CFG_WEBALERT_MAX_NUM_OF_CHARS_PER_LINE_IN_ALERT_EMAIL)
    r = ''
    for l in lines:
        r += l + '\n'
    return r

def wrap_records(text):
    """Limits the number of characters per line in given text.
    The function preserves new lines.
    """
    lines = text.split('\n')
    result_lines = []
    for l in lines:
        newlines = textwrap.wrap(l, CFG_WEBALERT_MAX_NUM_OF_CHARS_PER_LINE_IN_ALERT_EMAIL)
        for ll in newlines:
            result_lines.append(ll)
    return '\n'.join(result_lines)

class RecordHTMLParser(HTMLParser):
    """A parser for the HTML returned by invenio.legacy.search_engine.print_record.

    The parser provides methods to transform the HTML returned by
    invenio.legacy.search_engine.print_record into plain text, with some
    minor formatting.
    """

    silent = False
    new_line = True # Are we at the beginning of a new line? (after
                    # <br/>, </p> or at the beginning of the text)

    def __init__(self):
        HTMLParser.__init__(self)
        self.result = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'strong':
            # self.result += '*'
            pass
        elif tag == 'a':
            self.printURL = 0
            self.unclosedBracket = 0
            for f in attrs:
                #if f[1] == 'note':
                #    self.result += 'Fulltext : <'
                #    self.unclosedBracket = 1
                if f[1] == 'moreinfo':
                    self.result += 'Detailed record : '
                    self.printURL = 1
                if (self.printURL == 1) and (f[0] == 'href'):
                    self.result += '<' + f[1] + '>'
        elif tag == 'br':
            self.result += '\n'
        elif tag == 'style' or tag == 'script':
            self.silent = True
        elif tag == 'p':
            if not self.new_line:
                self.result += '\n'
                self.new_line = True

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            self.result += '\n'
            self.new_line = True

    def handle_endtag(self, tag):
        if tag == 'strong':
            # self.result += '\n'
            pass
        elif tag == 'a':
            if self.unclosedBracket == 1:
                self.result += '>'
                self.unclosedBracket = 0
        elif tag == 'style' or tag == 'script':
            self.silent = False
        elif tag == 'p':
            self.result += '\n'
            self.new_line = True

    def handle_data(self, data):
        if data.lower() in  ['detailed record', 'similar record', 'cited by']:
            pass
        elif self.silent == False:
            if self.new_line:
                # Remove unnecessary trailing whitespace at the
                # beginning of a line
                data = data.lstrip()
            # Merge all consecutive whitespaces into a single one
            self.result += data
            self.new_line = False

    def handle_comment(self, data):
        if 'START_NOT_FOR_TEXT' == data.upper().strip():
            self.silent = True
        elif 'END_NOT_FOR_TEXT' == data.upper().strip():
            self.silent = False

    def handle_charref(self, name):
        """Process character references of the form "&#ref;". Transform to text whenever possible."""
        try:
            self.result += unichr(int(name)).encode("utf-8")
        except:
            return

    def handle_entityref(self, name):
        """Process a general entity reference of the form "&name;".
        Transform to text whenever possible."""
        if name == 'nbsp':
            # Keep them for the moment. Will be processed at the end.
            # It is needed to consider them separately, as all
            # consecutive whitespaces will be merged into a single one
            # at the end. It should not be the case of non breakable
            # space.  Note that because of this trick, input
            # &amp;nbsp; will be considered as a &nbsp;
            self.result += '&nbsp;'
            return
        char_code = html_entities.name2codepoint.get(name, None)
        if char_code is not None:
            try:
                self.result += unichr(char_code).encode("utf-8")
            except:
                return

def get_as_text(record_id=0, xml_record=None, ln=CFG_SITE_LANG):
    """Return the record in a textual format"""
    _ = gettext_set_language(ln)
    out = ""
    if record_id != 0:
        rec_in_hb = format_record(record_id, of="hb")
    elif xml_record:
        rec_in_hb = format_record(0, of="hb", xml_record=xml_record)
    rec_in_hb = rec_in_hb.replace('\n', ' ')
    htparser = RecordHTMLParser()
    try:
        htparser.feed(rec_in_hb)
        htparser.close()
        out = htparser.result
    except:
        out = remove_html_markup(rec_in_hb)

    # Remove trailing whitespace and linefeeds
    out = out.strip('\n').strip()
    # Merge consecutive whitespaces. Must be done here, once all HTML
    # tags have been removed
    out = whitespaces_pattern.sub(' ', out)
    # Now consider non-breakable spaces
    out = out.replace('&nbsp;', ' ')
    out = re.sub(r"[\-:]?\s*%s\s*[\-:]?" % _("Detailed record"), "", out)
    out = re.sub(r"[\-:]?\s*%s\s*[\-:]?" % _("Similar records"), "", out)
    out = re.sub(r"[\-:]?\s*%s\s*[\-:]?" % _("Cited by"), "", out)
    return out.strip()
