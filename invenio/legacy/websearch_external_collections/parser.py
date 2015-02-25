# -*- coding: utf-8 -*-

# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""
This is a collection of parsers for external search engines.

Each parser try to extract results from a web page returned by an external search
engine.
"""

__revision__ = "$Id$"

import re
from six import iteritems

#from .config import CFG_EXTERNAL_COLLECTION_MAXRESULTS
from invenio.config import CFG_WEBSEARCH_EXTERNAL_COLLECTION_SEARCH_MAXRESULTS
CFG_EXTERNAL_COLLECTION_MAXRESULTS = CFG_WEBSEARCH_EXTERNAL_COLLECTION_SEARCH_MAXRESULTS

try:
    from BeautifulSoup import BeautifulSoup
    CFG_BEAUTIFULSOUP_INSTALLED = True
except ImportError:
    CFG_BEAUTIFULSOUP_INSTALLED = False

from invenio.modules.formatter import format_record
from .getter import fetch_url_content
import cgi

xml_parser_type = 0
try:
    from lxml import etree
    xml_parser_type = 1
except ImportError:
    try:
        import libxml2
        xml_parser_type = 2
    except ImportError:
        pass

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
    nbrecs_regex = None
    nbrecs_url = None

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

    def parse(self, of=None, req=None, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Parse the buffer. Set an optional output format."""
        pass

    def add_html_result(self, html, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Add a new html code as result. The urls in the html code will be corrected."""

        if not html:
            return

        if len(self.results) >= limit:
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

    def parse_nbrecs(self, timeout):
        """Fetch and parse the contents of the nbrecs url with the nbrecs_regex to extract the total
        number of records. This will be returned as a formated string."""

        if self.nbrecs_regex is None:
            return None
        html = fetch_url_content([self.nbrecs_url], timeout)
        try:
            if len(html) == 1:
                matches = self.nbrecs_regex.search(html[0])
                return int(matches.group(1).replace(',', ''))
            else: return None
            # This last else should never occur. It means the list html has more (or less) than 1 elements,
            # which is impossible since the fetch_url_content(url) function always returns a list with as many
            # elements as the list's it was fed with
        except AttributeError:
            # This means that the pattern did not match anything, therefore the matches.group(1) raised the exception
            return -1
        except TypeError:
            # This means that the pattern was ran on None instead of string or buffer, therefore the
            # self.nbrecs_regex.search(html[0]) raised the exception, as html = [None]
            return -2

    def parse_and_get_results(self, data, of=None, req=None, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS, feedonly=False, parseonly=False):
        """Parse given data and return results."""

        # parseonly = True just in case we only want to parse the data and return the results
        # ex. the bufffer has already been fed
        if not parseonly:
            self.clean()
            self.feed(data)
        # feedonly = True just in case we just want to feed the buffer with the new data
        # ex. the data will be used only to calculate the number of results
        if not feedonly:
            self.parse(of, req, limit)
            return self.results

    def buffer_decode_from(self, charset):
        """Convert the buffer to UTF-8 from the specified charset. Ignore errors."""
        try:
            self.buffer = self.buffer.decode(charset, 'ignore').encode('utf-8', 'ignore')
        except:
            pass

class CDSIndicoCollectionResutsParser(ExternalCollectionResultsParser):
    """Parser for Indico"""

    num_results_regex = re.compile(r'<h3 style="float:right">Hits: ([0-9]+?)</h3>')

    def __init__(self, host="", path=""):
        super(CDSIndicoCollectionResutsParser, self).__init__(host, path)

    def parse(self, of=None, req=None, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Parse buffer to extract records."""

        if CFG_BEAUTIFULSOUP_INSTALLED:
            soup = BeautifulSoup(self.buffer)

            # Remove "more" links that include Indico Javascript
            more_links = soup.findAll('a', { "class" : "searchResultLink", "href": "#"})
            [more_link.extract() for more_link in more_links]

            # Events
            event_results = soup.findAll('li', {"class" : "searchResultEvent"})
            event_index = 1
            for result in event_results:
                self.add_html_result((event_index == 1 and '<b>Events:</b><br/>' or '') + \
                                     str(result)  + '<br />', limit)
                event_index += 1
            # Contributions
            contribution_results = soup.findAll('li', {"class" : "searchResultContribution"})
            contribution_index = 1
            for result in contribution_results:
                self.add_html_result((contribution_index == 1 and '<b>Contributions:</b><br/>' or '') + \
                                     str(result)  + '<br />', limit)
                contribution_index += 1
        else:
            # Markup is complex. Do whatever we can...
            # Events
            split_around_events = self.buffer.split('<li class="searchResultEvent">')
            if len(split_around_events) > 1:
                event_index = 1
                for html_chunk in split_around_events[1:]:
                    output = '<li class="searchResultEvent">'
                    if event_index == len(split_around_events) -1:
                        split_around_link = html_chunk.split('searchResultLink')
                        split_around_ul = 'searchResultLink'.join(split_around_link[1:]).split('</ul>')
                        output += split_around_link[0] + 'searchResultLink' + \
                                  split_around_ul[0] + '</ul>' + split_around_ul[1]
                    else:
                        output += html_chunk
                    self.add_html_result((event_index == 1 and '<b>Events:</b><br/>' or '') + \
                                     output  + '<br />', limit)
                    event_index += 1
            # Contributions
            split_around_contributions = self.buffer.split('<li class="searchResultContribution">')
            if len(split_around_contributions) > 1:
                contribution_index = 1
                for html_chunk in split_around_contributions[1:]:
                    output = '<li class="searchResultContribution">'
                    if contribution_index == len(split_around_contributions) -1:
                        split_around_link = html_chunk.split('searchResultLink')
                        split_around_ul = 'searchResultLink'.join(split_around_link[1:]).split('</ul>')
                        output += split_around_link[0] + 'searchResultLink' + \
                                  split_around_ul[0] + '</ul>' + split_around_ul[1]
                    else:
                        output += html_chunk
                    self.add_html_result((contribution_index == 1 and '<b>Contributions:</b><br/>' or '') + \
                                     output  + '<br />', limit)
                    contribution_index += 1

class KISSExternalCollectionResultsParser(ExternalCollectionResultsParser):
    """Parser for Kiss."""

    num_results_regex = re.compile(r'<pre><b> ([0-9]+?) records matched</b></pre>')

    def __init__(self, host="www-lib.kek.jp", path="cgi-bin/"):
        super(KISSExternalCollectionResultsParser, self).__init__(host, path)

    def parse(self, of=None, req=None, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
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
            self.add_html_result(element + '<br /><br />', limit)

class KISSBooksExternalCollectionResultsParser(ExternalCollectionResultsParser):
    """Parser for Kiss books."""
    line = re.compile(r'<TR>(.*?)</TR>')
    title = re.compile(r'<TR>[ ]+<TD valign="top">([0-9]+)\)</TD>[ ]+<TD><A HREF="?(.*)"?>[ ]*(.*?)[ ]*</A></TD>[ ]+</TR>')
    info_line = re.compile(r'[ ]*<TR>[ ]*<TD></TD>[ ]*<TD>(.*?)</TD>.*</TR>')
    num_results_regex = re.compile(r'<B> (?:Books|Journals) ([0-9]+?) </B>')

    def __init__(self, host="www-lib.kek.jp", path="cgi-bin/"):
        super(KISSBooksExternalCollectionResultsParser, self).__init__(host, path)

    def parse(self, of=None, req=None, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
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
                self.add_html_result(html, limit)

                num = title_match.group(1)
                url = title_match.group(2)
                title = title_match.group(3)

                html = num + ') <a href=http://' + self.host + url + ">" + title + "</a><br />"
            else:
                info_line_match = self.info_line.match(data)
                if info_line_match:
                    info = info_line_match.group(1)
                    html += info + '<br />'

        self.add_html_result(html, limit)

class GoogleExternalCollectionResultsParser(ExternalCollectionResultsParser):
    """Parser for Google"""

    num_results_regex = re.compile(r'of about <b>([0-9,]+?)</b>')

    def __init__(self, host = "www.google.com", path=""):
        super(GoogleExternalCollectionResultsParser, self).__init__(host, path)

    def parse(self, of=None, req=None, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Parse buffer to extract records."""
        elements = self.buffer.split("<div class=g>")
        if len(elements) <= 1:
            return

        for element in elements[1:]:
            end_index = element.find('</table>')
            if end_index != -1:
                element = element[:end_index + 8]
            self.add_html_result(element, limit)

class GoogleScholarExternalCollectionResultsParser(GoogleExternalCollectionResultsParser):
    """Parser for Google Scholar."""

    def __init__(self, host = "scholar.google.com", path=""):
        super(GoogleScholarExternalCollectionResultsParser, self).__init__(host, path)

    def parse(self, of=None, req=None, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Parse buffer to extract records."""
        elements = self.buffer.split("<p class=g>")
        if len(elements) <= 1:
            return

        for element in elements[1:-1]:
            end_index = element.find('</table>')
            if end_index != -1:
                element = element[:end_index + 8]
            self.add_html_result(element + '<br />', limit)

class GoogleBooksExternalCollectionResultsParser(GoogleExternalCollectionResultsParser):
    """Parser for Google Books."""

    num_results_regex = re.compile(r' with <b>([0-9]+?)</b> pages on ')

    def __init__(self, host = "books.google.com", path=""):
        super(GoogleBooksExternalCollectionResultsParser, self).__init__(host, path)

    def parse(self, of=None, req=None, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Parse buffer to extract records."""
        elements = self.buffer.split('<table class=rsi><tr><td class="covertd">')
        if len(elements) <= 1:
            return

        for element in elements[1:-1]:
            self.add_html_result(element, limit)

class SPIRESExternalCollectionResultsParser(ExternalCollectionResultsParser):
    """Parser for SPIRES."""

    num_results_regex = re.compile(r'Paper <b>[0-9]+</b> to <b>[0-9]+</b> of <b>([0-9]+)</b>')

    def __init__(self, host="www.slac.stanford.edu", path="spires/find/hep/"):
        super(SPIRESExternalCollectionResultsParser, self).__init__(host, path)

    def parse(self, of=None, req=None, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Parse buffer to extract records."""
        elements = self.buffer.split('<p>')

        if len(elements) <= 2:
            return

        for element in elements[1:-1]:
            self.add_html_result(element, limit)

class SCIRUSExternalCollectionResultsParser(ExternalCollectionResultsParser):
    """Parser for SCIRUS."""

    num_results_regex = re.compile(r'<b>([0-9,]+) total</b> ')
    result_separator = re.compile(r'<td width="100%" valign="top" colspan="2">[ ]*(.*?)</td>[ ]*</tr>[ ]*</table>')
    result_decode = re.compile('[ ]*(.*?)[ ]*<font class="filesize">.*?<br />[ ]*(.*?)[ ]*<br />[ ]*(.*?)[ ]*</td>.*?<br />[ ]*(.*)[ ]*')

    cleaning = re.compile('(<img .*?>|</td>|</tr>|<td .*?>|<tr.*?>)')

    def __init__(self, host='www.scirus.com', path='srsapp/'):
        super(SCIRUSExternalCollectionResultsParser, self).__init__(host, path)

    def parse(self, of=None, req=None, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
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
            self.add_html_result(html, limit)

class CiteSeerExternalCollectionResultsParser(ExternalCollectionResultsParser):
    """Parser for CiteSeer."""

    num_results_regex = re.compile(r'<br />(?:More than |)([0-9]+)(?: documents found.| results)')
    result_separator = re.compile(r'<!--RIS-->.*?<!--RIE-->', re.DOTALL)

    def __init__(self, host='', path=''):
        super(CiteSeerExternalCollectionResultsParser, self).__init__(host, path)

    def parse(self, of=None, req=None, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Parse buffer to extract records."""
        for element in self.result_separator.finditer(self.buffer):
            self.add_html_result(element.group() + '<br />', limit)

class InvenioHTMLExternalCollectionResultsParser(ExternalCollectionResultsParser):
    """HTML brief (hb) Parser for Invenio"""

    def __init__(self, params):
        self.buffer = ""
        self.results = []
        self.clean()
        self.num_results_regex_str = None
        self.nbrecs_regex_str = None
        for (name, value) in iteritems(params):
            setattr(self, name, value)
        if self.num_results_regex_str:
            self.num_results_regex = re.compile(self.num_results_regex_str)
        if self.nbrecs_regex_str:
            self.nbrecs_regex = re.compile(self.nbrecs_regex_str, re.IGNORECASE)

    def parse(self, of=None, req=None, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Parse buffer to extract records."""

        # the patterns :
        # level_a : select only the results
        level_a_pat = re.compile(r'<form[^>]*basket[^>]*?>.*?<table>(.*?)</table>.*?</form>', re.DOTALL + re.MULTILINE + re.IGNORECASE)
        # level_b : purge html from the basket input fields
        level_b_pat = re.compile(r'<input[^>]*?/>', re.DOTALL + re.MULTILINE + re.IGNORECASE)
        # level_c : separate the results from one another
        level_c_pat = re.compile(r'(<tr>.*?</tr>)', re.DOTALL + re.MULTILINE + re.IGNORECASE)

        # the long way :
        #level_a_res = level_a_pat.search(self.buffer)
        #level_ab_res = level_a_res.group(1)
        #level_b_res = level_b_pat.sub('', level_ab_res)
        #level_c_res = level_c_pat.finditer(level_b_res)

        # the short way :
        try:
            results = level_c_pat.finditer(level_b_pat.sub('', level_a_pat.search(self.buffer).group(1)))
            for result in results:
               # each result is placed in each own table since it already has its rows and cells defined
                self.add_html_result('<table>' + result.group(1) + '</table>', limit)
        except AttributeError:
            # in case there were no results found an Attribute error is raised
            pass

class InvenioXMLExternalCollectionResultsParser(ExternalCollectionResultsParser):
    """XML (xm) parser for Invenio"""

    def __init__(self, params):
        self.buffer = ""
        self.results = []
        self.clean()
        self.num_results_regex_str = None
        self.nbrecs_regex_str = None
        for (name, value) in iteritems(params):
            setattr(self, name, value)
        if self.num_results_regex_str:
            self.num_results_regex = re.compile(self.num_results_regex_str)
        if self.nbrecs_regex_str:
            self.nbrecs_regex = re.compile(self.nbrecs_regex_str, re.IGNORECASE)

    def parse(self, of='hb', req=None, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Parse buffer to extract records. Format the records using the selected output format."""

        (recids, records) = self.parse_and_extract_records(of)
        if req and 'jrec' in cgi.parse_qs(req.args):
            counter = int(cgi.parse_qs(req.args)['jrec'][0]) - 1
        else:
            counter = 0
        for recid in recids:
            counter += 1
            if of in ['hb', None]:
                html = """
                        <tr><td valign="top" align="right" style="white-space: nowrap;">
                        <input name="recid" type="checkbox" value="%(recid)s" />

                        %(counter)s.

                        </td><td valign="top">%(record)s</td></tr>
                        """ % {'recid': recid,
                               'counter': counter,
                               'record': records[recid]}
            elif of == 'hd':
                # HTML detailed (hd) is not supported yet
                # TODO: either disable the hd output format or print it out correctly
                html = """"""
            elif of == 'xm':
                html = records[recid]
            else:
                html = None
            if html:
                self.add_html_result(html, limit)

    def parse_and_extract_records(self, of='hb'):
        """Parse the buffer and return a list of the recids and a
        dictionary with key:value pairs like the following
        recid:formated record with the selected output format"""

        # the patterns :
        # separate the records from one another
        record_pat = re.compile(r'(<record.*?>.*?</record>)', re.DOTALL + re.MULTILINE + re.IGNORECASE)
        # extract the recid
        recid_pat = re.compile(r'<controlfield tag="001">([0-9]+?)</controlfield>', re.DOTALL + re.MULTILINE + re.IGNORECASE)

        if not of:
            of='hb'

        try:
            results = record_pat.finditer(self.buffer)
            records = {}
            recids = []
            for result in results:
                xml_record = result.group(1)
                recid = recid_pat.search(xml_record).group(1)
                recids.append(recid)
                if of != 'xm':
                    records[recid] = format_record(None, of, xml_record=xml_record)
                elif of == 'xm':
                    records[recid] = xml_record
            return (recids, records)
        except AttributeError:
            # in case there were no results found an Attribute error is raised
            return ([], {})

class ScienceCinemaXMLExternalCollectionResultsParser(ExternalCollectionResultsParser):
    """XML parser for ScienceCinema"""

    def parse_num_results(self):
        """Returns the number of results"""
        return self.buffer.split('</audio>')[0].count('<record>')

    def parse(self, of='hb', req=None, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Parse buffer to extract records. Format the records using the selected output format."""

        def process_audio_record(record_node):
            """Return HTML formatted version of an audio record_node"""
            ostiId = ''
            title = ''
            description = ''
            link = ''
            image = ''
            snippets = ''
            if xml_parser_type == 1:
                # lxml
                subnodes = record_node.iterchildren()
                for subnode in subnodes:
                    if subnode.tag == 'ostiId':
                        ostiId = str(subnode.text)
                    elif subnode.tag == 'title':
                        title = str(subnode.text)
                    elif subnode.tag == 'description':
                        description = str(subnode.text)
                    elif subnode.tag == 'link':
                        link = str(subnode.text)
                    elif subnode.tag == 'image':
                        image = str(subnode.text)
                    elif subnode.tag == 'snippets':
                        snippets = str(subnode.text)
            elif xml_parser_type == 2:
                # libxml2
                subnode = record_node.children
                while subnode is not None:
                    if subnode.name == 'ostiId':
                        ostiId = str(subnode.content)
                    elif subnode.name == 'title':
                        title = str(subnode.content)
                    elif subnode.name == 'description':
                        description = str(subnode.content)
                    elif subnode.name == 'link':
                        link = str(subnode.content)
                    elif subnode.name == 'image':
                        image = str(subnode.content)
                    elif subnode.name == 'snippets':
                        snippets = str(subnode.content)
                    subnode = subnode.next
            return """<table><tr><td><img style="max-width:180px" src="%(image)s"/></td><td valign="top"><b>%(title)s</b><br/>
%(description)s<br/>
<a href="%(link)s">%(link)s</a></td></tr></table>
            """ % \
        {'title': title,
         'ostiId': ostiId,
         'description': description,
         'link': link,
         'image': image,
         'snippets': snippets}

        def process_metadata_record(record_node):
            """Return HTML formatted version of a metadata record_node"""
            return process_audio_record(record_node)

        if xml_parser_type == 1:
            # lxml
            document = etree.XML(self.buffer)
            nodes = document.iterchildren()
            for node in nodes:
                current_nodename = node.tag
                if current_nodename in ['audio']:
                    results = node.iterchildren()
                    for result in results:
                        if result.tag == 'record':
                            if current_nodename == 'audio':
                                self.add_html_result(process_audio_record(result))
                            elif current_nodename == 'metadata':
                                self.add_html_result(process_metadata_record(result))
            del document

        elif xml_parser_type == 2:
            # libxml2
            document = libxml2.parseDoc(self.buffer)
            node = document.getRootElement().children
            while node is not None:
                current_nodename = node.name
                if current_nodename in ['audio']: # Currently ignore 'metadata' nodes
                    result = node.children
                    while result is not None:
                        if result.name == 'record':
                            if current_nodename == 'audio':
                                self.add_html_result(process_audio_record(result))
                            elif current_nodename == 'metadata':
                                self.add_html_result(process_metadata_record(result))
                        result = result.next
                node = node.next
            document.freeDoc()

        else:
            # no xml parser found
            return
