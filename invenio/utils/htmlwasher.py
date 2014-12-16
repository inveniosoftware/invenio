# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012, 2013 CERN.
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

from invenio.utils.html import HTMLWasher
from six.moves import html_entities
import cgi
import re

RE_HTML_FIRST_NON_QUOTATION_CHAR_ON_LINE = re.compile('[^>]')


class EmailWasher(HTMLWasher):
    """
    Wash comments before being sent by email
    """

    line_quotation = ''

    def handle_starttag(self, tag, attrs):
        """Function called for new opening tags"""
        if tag.lower() in self.allowed_tag_whitelist:
            if tag.lower() == 'ol':
                # we need a list to store the last
                # number used  in the previous ordered lists
                self.previous_nbs.append(self.nb)
                self.nb = 0
                # we need to know which is the tag list
                self.previous_type_lists.append(tag.lower())
                # we must remove any non-relevant spacing and end of
                # line before
                self.result = self.result.rstrip()
            elif tag.lower() == 'ul':
                self.previous_type_lists.append(tag.lower())
                # we must remove any non-relevant spacing and end of
                # line before
                self.result = self.result.rstrip()
            elif tag.lower() == 'li':
                # we must remove any non-relevant spacing and end of
                # line before
                self.result = self.result.rstrip()
                if self.previous_type_lists[-1] == 'ol':
                    self.nb += 1
                    self.result += '\n' + self.line_quotation + \
                                   '  ' * len(self.previous_type_lists) + str(self.nb) + '. '
                else:
                    self.result += '\n' + self.line_quotation + \
                                   '  ' * len(self.previous_type_lists) + '* '
            elif tag.lower() == 'a':
                #self.previous_type_lists.append(tag.lower())
                for (attr, value) in attrs:
                    if attr.lower() == 'href':
                        self.url = value
                        self.result += '<' + value + '>'

    def handle_data(self, data):
        """Function called for text nodes"""
        if not self.silent:
            if self.url:
                if self.url == data:
                    data = ''
                else:
                    data = '(' + data + ')'
            self.url = ''
            self.result += cgi.escape(data, True)
        lines = data.splitlines()
        if len(lines) > 1:
            match_obj = RE_HTML_FIRST_NON_QUOTATION_CHAR_ON_LINE.search(lines[-1])
            if match_obj:
                self.line_quotation = '&gt;' * match_obj.start()
            else:
                self.line_quotation = ''

    def handle_endtag(self, tag):
        """Function called for ending of tags"""
        if tag.lower() in self.allowed_tag_whitelist:
            if tag.lower() in ['ul', 'ol']:
                self.previous_type_lists = self.previous_type_lists[:-1]
                if tag.lower() == 'ol':
                    self.nb = self.previous_nbs[-1]
                    self.previous_nbs = self.previous_nbs[:-1]
                # we must remove any non-relevant spacing and end of
                # line before
                self.result = self.result.rstrip()
                self.result += '\n' + self.line_quotation

    def handle_startendtag(self, tag, attrs):
        """Function called for empty tags (e.g. <br />)"""
        self.result += ""

    def handle_charref(self, name):
        """Process character references of the form "&#ref;". Transform to text whenever possible."""
        try:
            self.result += unichr(int(name)).encode("utf-8")
        except:
            return

    def handle_entityref(self, name):
        """Process a general entity reference of the form "&name;".
        Transform to text whenever possible."""
        char_code = html_entities.name2codepoint.get(name, None)
        if char_code is not None:
            try:
                self.result += unichr(char_code).encode("utf-8")
            except:
                return
