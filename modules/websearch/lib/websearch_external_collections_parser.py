# -*- coding: utf-8 -*-

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

"""
This is a collection of parsers for external search engines.

Each parser try to extract results from a web page returned by an external search
engine.
"""

__revision__ = "$Id$"

import re
from invenio.websearch_external_collections_config import CFG_EXTERNAL_COLLECTION_MAXRESULTS

re_href = re.compile(r'<a[^>]*href="?([^">]*)"?[^>]*>', re.IGNORECASE)
re_img = re.compile(r'<img[^>]*src="?([^">]*)"?[^>]*>', re.IGNORECASE)

def correct_url(htmlcode, host, path):
    """This function is used to correct urls in html code.

    >>> correct_url('<a href="hello.html">', 'www.google.com', 'search/')
    '<a href="http://www.google.com/search/hello.html">'
    """
    htmlcode = correct_url_with_regex(htmlcode, host, path, re_href)
    htmlcode = correct_url_with_regex(htmlcode, host, path, re_img)
    return htmlcode

def correct_url_with_regex(htmlcode, host, path, regex):
    """Correct urls in html code. The url is found using the regex given."""
    url_starts = []
    results = regex.finditer(htmlcode)
    for result in results:
        url = result.group(1)
        if not url.startswith('http://'):
            url_starts.append(result.start(1))
    url_starts.reverse()
    for url_start in url_starts:
        if htmlcode[url_start] == '/':
            htmlcode = htmlcode[:url_start] + "http://" + host + htmlcode[url_start:]
        else:
            htmlcode = htmlcode[:url_start] + "http://" + host + "/" + path + htmlcode[url_start:]
    return htmlcode

class ExternalCollectionHit:
    """Hold a result."""

    def __init__(self, html=None):
        self.html = html

class ExternalCollectionResultsParser(object):
    """Mother class for parsers."""

    num_results_regex = None

    def __init__(self, host='', path=''):
        self.buffer = ""
        self.results = []
        self.host = host
        self.path = path
        self.clean()

    def clean(self):
        """Clean buffer and results to be able to parse a new web page."""
        self.buffer = ""
        self.results = []

    def feed(self, data):
        """Feed buffer with data that will be parse later."""
        self.buffer += data

    def parse(self):
        """Parse the buffer."""
        pass

    def add_html_result(self, html):
        """Add a new html code as result. The urls in the html code will be corrected."""

        if not html:
            return

        if len(self.results) >= CFG_EXTERNAL_COLLECTION_MAXRESULTS:
            return

        html = correct_url(html, self.host, self.path) + '\n'
        result = ExternalCollectionHit(html)
        self.results.append(result)

    def parse_num_results(self):
        """Parse the buffer with the num_results_regex to extract the number of records found.
        This will be returned as a formated string."""
        if self.num_results_regex is None:
            return None
        list_matchs = self.num_results_regex.finditer(self.buffer)
        for match in list_matchs:
            return int(match.group(1).replace(',', ''))
        return None

    def parse_and_get_results(self, data):
        """Parse given data and return results.
        """
        self.clean()
        self.feed(data)
        self.parse()
        return self.results

    def buffer_decode_from(self, charset):
        """Convert the buffer to UTF-8 from the specified charset. Ignore errors."""
        try:
            self.buffer = self.buffer.decode(charset, 'ignore').encode('utf-8', 'ignore')
        except:
            pass

class CDSIndicoCollectionResutsParser(ExternalCollectionResultsParser):
    """Parser for CDS Indico"""

    num_results_regex = re.compile(r'<strong>([0-9]+?)</strong> records found')
    result_regex = re.compile(r'<tr><td valign="top" align="right" style="white-space: nowrap;">\s*<input name="recid" type="checkbox" value="[0-9]+" \/>\s*([0-9]+\.)\s*</td><td valign="top">(.*?)<div class="moreinfo">.*?</div></td></tr>', re.MULTILINE + re.DOTALL)

    def __init__(self, host="", path=""):
        super(CDSIndicoCollectionResutsParser, self).__init__(host, path)

    def parse(self):
        """Parse buffer to extract records."""

        results = self.result_regex.finditer(self.buffer)
        for result in results:
            num = result.group(1)
            html = result.group(2)

            self.add_html_result(num + ' ' + html  + '<br />')

class KISSExternalCollectionResultsParser(ExternalCollectionResultsParser):
    """Parser for Kiss."""

    num_results_regex = re.compile(r'<pre><b> ([0-9]+?) records matched</b></pre>')

    def __init__(self, host="www-lib.kek.jp", path="cgi-bin/"):
        super(KISSExternalCollectionResultsParser, self).__init__(host, path)

    def parse(self):
        """Parse buffer to extract records."""

        self.buffer_decode_from('Shift_JIS')

        elements = self.buffer.split("<DL>")
        if len(elements) <= 1:
            return

        for element in elements[1:]:
            if len(self.results) >= CFG_EXTERNAL_COLLECTION_MAXRESULTS:
                return
            end_index = element.find('</DL>')
            if end_index != -1:
                element = element[:end_index + 4]
            self.add_html_result(element + '<br /><br />')

class KISSBooksExternalCollectionResultsParser(ExternalCollectionResultsParser):
    """Parser for Kiss books."""
    line = re.compile(r'<TR>(.*?)</TR>')
    title = re.compile(r'<TR>[ ]+<TD valign="top">([0-9]+)\)</TD>[ ]+<TD><A HREF="?(.*)"?>[ ]*(.*?)[ ]*</A></TD>[ ]+</TR>')
    info_line = re.compile(r'[ ]*<TR>[ ]*<TD></TD>[ ]*<TD>(.*?)</TD>.*</TR>')
    num_results_regex = re.compile(r'<B> (?:Books|Journals) ([0-9]+?) </B>')

    def __init__(self, host="www-lib.kek.jp", path="cgi-bin/"):
        super(KISSBooksExternalCollectionResultsParser, self).__init__(host, path)

    def parse(self):
        """Parse buffer to extract records."""

        self.buffer_decode_from('Shift_JIS')
        self.buffer = self.buffer.replace('\n', ' ')

        html = ""
        results_to_parse = self.line.finditer(self.buffer)
        for result in results_to_parse:
            if len(self.results) >= CFG_EXTERNAL_COLLECTION_MAXRESULTS:
                return
            data = result.group()

            title_match = self.title.match(data)
            if title_match:
                self.add_html_result(html)

                num = title_match.group(1)
                url = title_match.group(2)
                title = title_match.group(3)

                html = num + ') <a href=http://' + self.host + url + ">" + title + "</a><br />"
            else:
                info_line_match = self.info_line.match(data)
                if info_line_match:
                    info = info_line_match.group(1)
                    html += info + '<br />'

        self.add_html_result(html)

class GoogleExternalCollectionResultsParser(ExternalCollectionResultsParser):
    """Parser for Google"""

    num_results_regex = re.compile(r'of about <b>([0-9,]+?)</b>')

    def __init__(self, host = "www.google.com", path=""):
        super(GoogleExternalCollectionResultsParser, self).__init__(host, path)

    def parse(self):
        """Parse buffer to extract records."""
        elements = self.buffer.split("<div class=g>")
        if len(elements) <= 1:
            return

        for element in elements[1:]:
            end_index = element.find('</table>')
            if end_index != -1:
                element = element[:end_index + 8]
            self.add_html_result(element)

class GoogleScholarExternalCollectionResultsParser(GoogleExternalCollectionResultsParser):
    """Parser for Google Scholar."""

    def __init__(self, host = "scholar.google.com", path=""):
        super(GoogleScholarExternalCollectionResultsParser, self).__init__(host, path)

    def parse(self):
        """Parse buffer to extract records."""
        elements = self.buffer.split("<p class=g>")
        if len(elements) <= 1:
            return

        for element in elements[1:-1]:
            end_index = element.find('</table>')
            if end_index != -1:
                element = element[:end_index + 8]
            self.add_html_result(element + '<br />')

class GoogleBooksExternalCollectionResultsParser(GoogleExternalCollectionResultsParser):
    """Parser for Google Books."""

    num_results_regex = re.compile(r' with <b>([0-9]+?)</b> pages on ')

    def __init__(self, host = "books.google.com", path=""):
        super(GoogleBooksExternalCollectionResultsParser, self).__init__(host, path)

    def parse(self):
        """Parse buffer to extract records."""
        elements = self.buffer.split('<table class=rsi><tr><td class="covertd">')
        if len(elements) <= 1:
            return

        for element in elements[1:-1]:
            self.add_html_result(element)

class SPIRESExternalCollectionResultsParser(ExternalCollectionResultsParser):
    """Parser for SPIRES."""

    num_results_regex = re.compile(r'Paper <b>[0-9]+</b> to <b>[0-9]+</b> of <b>([0-9]+)</b>')

    def __init__(self, host="www.slac.stanford.edu", path="spires/find/hep/"):
        super(SPIRESExternalCollectionResultsParser, self).__init__(host, path)

    def parse(self):
        """Parse buffer to extract records."""
        elements = self.buffer.split('<p>')

        if len(elements) <= 2:
            return

        for element in elements[1:-1]:
            self.add_html_result(element)

class SCIRUSExternalCollectionResultsParser(ExternalCollectionResultsParser):
    """Parser for SCIRUS."""

    num_results_regex = re.compile(r'<b>([0-9,]+) total</b> ')
    result_separator = re.compile(r'<td width="100%" valign="top" colspan="2">[ ]*(.*?)</td>[ ]*</tr>[ ]*</table>')
    result_decode = re.compile('[ ]*(.*?)[ ]*<font class="filesize">.*?<br />[ ]*(.*?)[ ]*<br />[ ]*(.*?)[ ]*</td>.*?<br />[ ]*(.*)[ ]*')

    cleaning = re.compile('(<img .*?>|</td>|</tr>|<td .*?>|<tr.*?>)')

    def __init__(self, host='www.scirus.com', path='srsapp/'):
        super(SCIRUSExternalCollectionResultsParser, self).__init__(host, path)

    def parse(self):
        """Parse buffer to extract records."""
        data = self.buffer.replace('\n', ' ')

        for element in self.result_separator.finditer(data):
            data = element.group(1)
            parsed_line = self.result_decode.match(data)
            if parsed_line is not None:
                link = parsed_line.group(1)
                date = parsed_line.group(2)
                comments = parsed_line.group(3)
                similar = parsed_line.group(4)
                html = "%(link)s - %(date)s <br /> %(comments)s <br /> %(similar)s <br />" % {'link' : link,
                    'date' : date, 'comments' : comments, 'similar' : similar}
            else:
                html = self.cleaning.sub("", data) + '<br />'
            self.add_html_result(html)

class CiteSeerExternalCollectionResultsParser(ExternalCollectionResultsParser):
    """Parser for CiteSeer."""

    num_results_regex = re.compile(r'<br />(?:More than |)([0-9]+)(?: documents found.| results)')
    result_separator = re.compile(r'<!--RIS-->.*?<!--RIE-->', re.DOTALL)

    def __init__(self, host='', path=''):
        super(CiteSeerExternalCollectionResultsParser, self).__init__(host, path)

    def parse(self):
        """Parse buffer to extract records."""
        for element in self.result_separator.finditer(self.buffer):
            self.add_html_result(element.group() + '<br />')

