# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014 CERN.
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

# pylint: disable=C0301

__revision__ = "$Id$"

import time
import cgi
import string
import re
import locale
from urllib import quote, urlencode
from xml.sax.saxutils import escape as xml_escape

from invenio.config import \
     CFG_WEBSEARCH_LIGHTSEARCH_PATTERN_BOX_WIDTH, \
     CFG_WEBSEARCH_SIMPLESEARCH_PATTERN_BOX_WIDTH, \
     CFG_WEBSEARCH_ADVANCEDSEARCH_PATTERN_BOX_WIDTH, \
     CFG_WEBSEARCH_AUTHOR_ET_AL_THRESHOLD, \
     CFG_WEBSEARCH_USE_ALEPH_SYSNOS, \
     CFG_WEBSEARCH_SPLIT_BY_COLLECTION, \
     CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS, \
     CFG_BIBRANK_SHOW_READING_STATS, \
     CFG_BIBRANK_SHOW_DOWNLOAD_STATS, \
     CFG_BIBRANK_SHOW_DOWNLOAD_GRAPHS, \
     CFG_BIBRANK_SHOW_CITATION_LINKS, \
     CFG_BIBRANK_SHOW_CITATION_STATS, \
     CFG_BIBRANK_SHOW_CITATION_GRAPHS, \
     CFG_WEBSEARCH_RSS_TTL, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_SITE_NAME_INTL, \
     CFG_VERSION, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_SITE_ADMIN_EMAIL, \
     CFG_CERN_SITE, \
     CFG_INSPIRE_SITE, \
     CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE, \
     CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES, \
     CFG_WEBSEARCH_MAX_RECORDS_IN_GROUPS, \
     CFG_BIBINDEX_CHARS_PUNCTUATION, \
     CFG_WEBCOMMENT_ALLOW_COMMENTS, \
     CFG_WEBCOMMENT_ALLOW_REVIEWS, \
     CFG_WEBSEARCH_WILDCARD_LIMIT, \
     CFG_WEBSEARCH_SHOW_COMMENT_COUNT, \
     CFG_WEBSEARCH_SHOW_REVIEW_COUNT, \
     CFG_SITE_RECORD, \
     CFG_WEBSEARCH_PREV_NEXT_HIT_LIMIT, \
     CFG_HEPDATA_URL, \
     CFG_HEPDATA_PLOTSIZE, \
     CFG_BASE_URL, \
     CFG_SITE_URL, \
     CFG_WEBSEARCH_PREV_NEXT_HIT_FOR_GUESTS

from invenio.search_engine_config import CFG_WEBSEARCH_RESULTS_OVERVIEW_MAX_COLLS_TO_PRINT
from invenio.websearch_services import \
     CFG_WEBSEARCH_MAX_SEARCH_COLL_RESULTS_TO_PRINT
from invenio.bibformat import format_record

from invenio.dbquery import run_sql
from invenio.messages import gettext_set_language
from invenio.urlutils import make_canonical_urlargd, drop_default_urlargd, create_html_link, create_url
from invenio.htmlutils import nmtoken_from_string
from invenio.webinterface_handler import wash_urlargd
from invenio.bibrank_citation_searcher import get_cited_by_count
from invenio.webuser import session_param_get

from invenio.intbitset import intbitset

from invenio.websearch_external_collections import external_collection_get_state, get_external_collection_engine
from invenio.websearch_external_collections_utils import get_collection_id
from invenio.websearch_external_collections_config import CFG_EXTERNAL_COLLECTION_MAXRESULTS
from invenio.search_engine_utils import get_fieldvalues
from invenio.bibformat import format_record
from invenio.search_engine_utils import record_exists

from invenio import hepdatadisplayutils

_RE_PUNCTUATION = re.compile(CFG_BIBINDEX_CHARS_PUNCTUATION)
_RE_SPACES = re.compile(r"\s+")


def tmpl_citesummary_get_link(search_pattern_for_coll, searchfield, colldef):
    link_url = CFG_BASE_URL + '/search?p='
    if search_pattern_for_coll:
        p = search_pattern_for_coll
        if searchfield:
            if " " in p:
                p = searchfield + ':"' + p + '"'
            else:
                p = searchfield + ':' + p
        link_url += quote(p)
    if colldef:
        link_url += '%20AND%20' + quote(colldef)

    return link_url

def tmpl_citesummary_get_link_for_rep_breakdown(search_pattern_for_coll, searchfield, colldef, keyword, low, high):
    link_url = CFG_BASE_URL + '/search?p='
    if search_pattern_for_coll:
        p = search_pattern_for_coll
        if searchfield:
            if " " in p:
                p = searchfield + ':"' + p + '"'
            else:
                p = searchfield + ':' + p
        link_url += quote(p) + '%20AND%20'
    if colldef:
        link_url += quote(colldef) + '%20AND%20'
    if low == 0 and high == 0:
        link_url += quote('%s:0' % keyword)
    else:
        link_url += quote('%s:%i->%i' % (keyword, low, high))
    return link_url

class Template:

    # This dictionary maps Invenio language code to locale codes (ISO 639)
    tmpl_localemap = {
        'bg': 'bg_BG',
        'ar': 'ar_AR',
        'ca': 'ca_ES',
        'de': 'de_DE',
        'el': 'el_GR',
        'en': 'en_US',
        'es': 'es_ES',
        'pt': 'pt_BR',
        'fa': 'fa_IR',
        'fr': 'fr_FR',
        'it': 'it_IT',
        'ka': 'ka_GE',
        'lt': 'lt_LT',
        'ro': 'ro_RO',
        'ru': 'ru_RU',
        'rw': 'rw_RW',
        'sk': 'sk_SK',
        'cs': 'cs_CZ',
        'no': 'no_NO',
        'sv': 'sv_SE',
        'uk': 'uk_UA',
        'ja': 'ja_JA',
        'pl': 'pl_PL',
        'hr': 'hr_HR',
        'zh_CN': 'zh_CN',
        'zh_TW': 'zh_TW',
        'hu': 'hu_HU',
        'af': 'af_ZA',
        'gl': 'gl_ES'
        }
    tmpl_default_locale = "en_US" # which locale to use by default, useful in case of failure

    # Type of the allowed parameters for the web interface for search results
    search_results_default_urlargd = {
        'cc': (str, CFG_SITE_NAME),
        'c': (list, []),
        'p': (str, ""), 'f': (str, ""),
        'rg': (int, CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS),
        'sf': (str, ""),
        'so': (str, "d"),
        'sp': (str, ""),
        'rm': (str, ""),
        'of': (str, "hb"),
        'ot': (list, []),
        'em': (str,""),
        'aas': (int, CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE),
        'as': (int, CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE),
        'p1': (str, ""), 'f1': (str, ""), 'm1': (str, ""), 'op1':(str, ""),
        'p2': (str, ""), 'f2': (str, ""), 'm2': (str, ""), 'op2':(str, ""),
        'p3': (str, ""), 'f3': (str, ""), 'm3': (str, ""),
        'sc': (int, 0),
        'jrec': (int, 0),
        'recid': (int, -1), 'recidb': (int, -1), 'sysno': (str, ""),
        'id': (int, -1), 'idb': (int, -1), 'sysnb': (str, ""),
        'action': (str, "search"),
        'action_search': (str, ""),
        'action_browse': (str, ""),
        'd1': (str, ""),
        'd1y': (int, 0), 'd1m': (int, 0), 'd1d': (int, 0),
        'd2': (str, ""),
        'd2y': (int, 0), 'd2m': (int, 0), 'd2d': (int, 0),
        'dt': (str, ""),
        'ap': (int, 1),
        'verbose': (int, 0),
        'ec': (list, []),
        'wl': (int, CFG_WEBSEARCH_WILDCARD_LIMIT),
        }

    # ...and for search interfaces
    search_interface_default_urlargd = {
        'aas': (int, CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE),
        'as': (int, CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE),
        'verbose': (int, 0),
        'em' : (str, "")}

    # ...and for RSS feeds
    rss_default_urlargd = {'c'  : (list, []),
                           'cc' : (str, ""),
                           'p'  : (str, ""),
                           'f'  : (str, ""),
                           'p1' : (str, ""),
                           'f1' : (str, ""),
                           'm1' : (str, ""),
                           'op1': (str, ""),
                           'p2' : (str, ""),
                           'f2' : (str, ""),
                           'm2' : (str, ""),
                           'op2': (str, ""),
                           'p3' : (str, ""),
                           'f3' : (str, ""),
                           'm3' : (str, ""),
                           'wl' : (int, CFG_WEBSEARCH_WILDCARD_LIMIT)}

    tmpl_openurl_accepted_args = {
            'id' : (list, []),
            'genre' : (str, ''),
            'aulast' : (str, ''),
            'aufirst' : (str, ''),
            'auinit' : (str, ''),
            'auinit1' : (str, ''),
            'auinitm' : (str, ''),
            'issn' : (str, ''),
            'eissn' : (str, ''),
            'coden' : (str, ''),
            'isbn' : (str, ''),
            'sici' : (str, ''),
            'bici' : (str, ''),
            'title' : (str, ''),
            'stitle' : (str, ''),
            'atitle' : (str, ''),
            'volume' : (str, ''),
            'part' : (str, ''),
            'issue' : (str, ''),
            'spage' : (str, ''),
            'epage' : (str, ''),
            'pages' : (str, ''),
            'artnum' : (str, ''),
            'date' : (str, ''),
            'ssn' : (str, ''),
            'quarter' : (str, ''),
            'url_ver' : (str, ''),
            'ctx_ver' : (str, ''),
            'rft_val_fmt' : (str, ''),
            'rft_id' : (list, []),
            'rft.atitle' : (str, ''),
            'rft.title' : (str, ''),
            'rft.jtitle' : (str, ''),
            'rft.stitle' : (str, ''),
            'rft.date' : (str, ''),
            'rft.volume' : (str, ''),
            'rft.issue' : (str, ''),
            'rft.spage' : (str, ''),
            'rft.epage' : (str, ''),
            'rft.pages' : (str, ''),
            'rft.artnumber' : (str, ''),
            'rft.issn' : (str, ''),
            'rft.eissn' : (str, ''),
            'rft.aulast' : (str, ''),
            'rft.aufirst' : (str, ''),
            'rft.auinit' : (str, ''),
            'rft.auinit1' : (str, ''),
            'rft.auinitm' : (str, ''),
            'rft.ausuffix' : (str, ''),
            'rft.au' : (list, []),
            'rft.aucorp' : (str, ''),
            'rft.isbn' : (str, ''),
            'rft.coden' : (str, ''),
            'rft.sici' : (str, ''),
            'rft.genre' : (str, 'unknown'),
            'rft.chron' : (str, ''),
            'rft.ssn' : (str, ''),
            'rft.quarter' : (int, ''),
            'rft.part' : (str, ''),
            'rft.btitle' : (str, ''),
            'rft.isbn' : (str, ''),
            'rft.atitle' : (str, ''),
            'rft.place' : (str, ''),
            'rft.pub' : (str, ''),
            'rft.edition' : (str, ''),
            'rft.tpages' : (str, ''),
            'rft.series' : (str, ''),
    }

    tmpl_opensearch_rss_url_syntax = "%(CFG_BASE_URL)s/rss?p={searchTerms}&amp;jrec={startIndex}&amp;rg={count}&amp;ln={language}" % {'CFG_BASE_URL': CFG_BASE_URL}
    tmpl_opensearch_html_url_syntax = "%(CFG_BASE_URL)s/search?p={searchTerms}&amp;jrec={startIndex}&amp;rg={count}&amp;ln={language}" % {'CFG_BASE_URL': CFG_BASE_URL}

    def tmpl_openurl2invenio(self, openurl_data):
        """ Return an Invenio url corresponding to a search with the data
        included in the openurl form map.
        """
        def isbn_to_isbn13_isbn10(isbn):
            isbn = isbn.replace(' ', '').replace('-', '')
            if len(isbn) == 10 and isbn.isdigit():
                ## We already have isbn10
                return ('', isbn)
            if len(isbn) != 13 and isbn.isdigit():
                return ('', '')
            isbn13, isbn10 = isbn, isbn[3:-1]
            checksum = 0
            weight = 10
            for char in isbn10:
                checksum += int(char) * weight
                weight -= 1
            checksum = 11 - (checksum % 11)
            if checksum == 10:
                isbn10 += 'X'
            if checksum == 11:
                isbn10 += '0'
            else:
                isbn10 += str(checksum)
            return (isbn13, isbn10)

        from invenio.search_engine import perform_request_search
        doi = ''
        pmid = ''
        bibcode = ''
        oai = ''
        issn = ''
        isbn = ''
        for elem in openurl_data['id']:
            if elem.startswith('doi:'):
                doi = elem[len('doi:'):]
            elif elem.startswith('pmid:'):
                pmid = elem[len('pmid:'):]
            elif elem.startswith('bibcode:'):
                bibcode = elem[len('bibcode:'):]
            elif elem.startswith('oai:'):
                oai = elem[len('oai:'):]
        for elem in openurl_data['rft_id']:
            if elem.startswith('info:doi/'):
                doi = elem[len('info:doi/'):]
            elif elem.startswith('info:pmid/'):
                pmid = elem[len('info:pmid/'):]
            elif elem.startswith('info:bibcode/'):
                bibcode = elem[len('info:bibcode/'):]
            elif elem.startswith('info:oai/'):
                oai = elem[len('info:oai/')]
            elif elem.startswith('urn:ISBN:'):
                isbn = elem[len('urn:ISBN:'):]
            elif elem.startswith('urn:ISSN:'):
                issn = elem[len('urn:ISSN:'):]

        ## Building author query
        aulast = openurl_data['rft.aulast'] or openurl_data['aulast']
        aufirst = openurl_data['rft.aufirst'] or openurl_data['aufirst']
        auinit = openurl_data['rft.auinit'] or \
                 openurl_data['auinit'] or \
                 openurl_data['rft.auinit1'] + ' ' + openurl_data['rft.auinitm'] or \
                 openurl_data['auinit1'] + ' ' + openurl_data['auinitm'] or  aufirst[:1]
        auinit = auinit.upper()
        if aulast and aufirst:
            author_query = 'author:"%s, %s" or author:"%s, %s"' % (aulast, aufirst, aulast, auinit)
        elif aulast and auinit:
            author_query = 'author:"%s, %s"' % (aulast, auinit)
        else:
            author_query = ''

        ## Building title query
        title = openurl_data['rft.atitle'] or \
                openurl_data['atitle'] or \
                openurl_data['rft.btitle'] or \
                openurl_data['rft.title'] or \
                openurl_data['title']
        if title:
            title_query = 'title:"%s"' % title
            title_query_cleaned = 'title:"%s"' % _RE_SPACES.sub(' ', _RE_PUNCTUATION.sub(' ', title))
        else:
            title_query = ''

        ## Building journal query
        jtitle = openurl_data['rft.stitle'] or \
                 openurl_data['stitle'] or \
                 openurl_data['rft.jtitle'] or \
                 openurl_data['title']
        if jtitle:
            journal_query = 'journal:"%s"' % jtitle
        else:
            journal_query = ''

        ## Building isbn query
        isbn = isbn or openurl_data['rft.isbn'] or \
               openurl_data['isbn']
        isbn13, isbn10 = isbn_to_isbn13_isbn10(isbn)
        if isbn13:
            isbn_query = 'isbn:"%s" or isbn:"%s"' % (isbn13, isbn10)
        elif isbn10:
            isbn_query = 'isbn:"%s"' % isbn10
        else:
            isbn_query = ''

        ## Building issn query
        issn = issn or openurl_data['rft.eissn'] or \
               openurl_data['eissn'] or \
               openurl_data['rft.issn'] or \
               openurl_data['issn']
        if issn:
            issn_query = 'issn:"%s"' % issn
        else:
            issn_query = ''

        ## Building coden query
        coden = openurl_data['rft.coden'] or openurl_data['coden']
        if coden:
            coden_query = 'coden:"%s"' % coden
        else:
            coden_query = ''

        ## Building doi query
        if False: #doi: #FIXME Temporaly disabled until doi field is properly setup
            doi_query = 'doi:"%s"' % doi
        else:
            doi_query = ''

        ## Trying possible searches
        if doi_query:
            if perform_request_search(p=doi_query):
                return '%s/search?%s' % (CFG_BASE_URL, urlencode({
                    'p' : doi_query,
                    'sc' : CFG_WEBSEARCH_SPLIT_BY_COLLECTION,
                    'of' : 'hd'}))
        if isbn_query:
            if perform_request_search(p=isbn_query):
                return '%s/search?%s' % (CFG_BASE_URL, urlencode({
                    'p' : isbn_query,
                    'sc' : CFG_WEBSEARCH_SPLIT_BY_COLLECTION,
                    'of' : 'hd'}))
        if coden_query:
            if perform_request_search(p=coden_query):
                return '%s/search?%s' % (CFG_BASE_URL, urlencode({
                    'p' : coden_query,
                    'sc' : CFG_WEBSEARCH_SPLIT_BY_COLLECTION,
                    'of' : 'hd'}))
        if author_query and title_query:
            if perform_request_search(p='%s and %s' % (title_query, author_query)):
                return '%s/search?%s' % (CFG_BASE_URL, urlencode({
                    'p' : '%s and %s' % (title_query, author_query),
                    'sc' : CFG_WEBSEARCH_SPLIT_BY_COLLECTION,
                    'of' : 'hd'}))
        if title_query:
            result = len(perform_request_search(p=title_query))
            if result == 1:
                return '%s/search?%s' % (CFG_BASE_URL, urlencode({
                    'p' : title_query,
                    'sc' : CFG_WEBSEARCH_SPLIT_BY_COLLECTION,
                    'of' : 'hd'}))
            elif result > 1:
                return '%s/search?%s' % (CFG_BASE_URL, urlencode({
                    'p' : title_query,
                    'sc' : CFG_WEBSEARCH_SPLIT_BY_COLLECTION,
                    'of' : 'hb'}))

        ## Nothing worked, let's return a search that the user can improve
        if author_query and title_query:
            return '%s/search%s' % (CFG_BASE_URL, make_canonical_urlargd({
                'p' : '%s and %s' % (title_query_cleaned, author_query),
                'sc' : CFG_WEBSEARCH_SPLIT_BY_COLLECTION,
                'of' : 'hb'}, {}))
        elif title_query:
            return '%s/search%s' % (CFG_BASE_URL, make_canonical_urlargd({
                'p' : title_query_cleaned,
                'sc' : CFG_WEBSEARCH_SPLIT_BY_COLLECTION,
                'of' : 'hb'}, {}))
        else:
            ## Mmh. Too few information provided.
            return '%s/search%s' % (CFG_BASE_URL, make_canonical_urlargd({
                        'p' : 'recid:-1',
                        'sc' : CFG_WEBSEARCH_SPLIT_BY_COLLECTION,
                        'of' : 'hb'}, {}))

    def tmpl_opensearch_description(self, ln):
        """ Returns the OpenSearch description file of this site.
        """
        _ = gettext_set_language(ln)
        return """<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/"
                       xmlns:moz="http://www.mozilla.org/2006/browser/search/">
<ShortName>%(short_name)s</ShortName>
<LongName>%(long_name)s</LongName>
<Description>%(description)s</Description>
<InputEncoding>UTF-8</InputEncoding>
<OutputEncoding>UTF-8</OutputEncoding>
<Language>*</Language>
<Contact>%(CFG_SITE_ADMIN_EMAIL)s</Contact>
<Query role="example" searchTerms="a" />
<Developer>Powered by Invenio</Developer>
<Url type="text/html" indexOffset="1" rel="results" template="%(html_search_syntax)s" />
<Url type="application/rss+xml" indexOffset="1" rel="results" template="%(rss_search_syntax)s" />
<Url type="application/opensearchdescription+xml" rel="self" template="%(CFG_BASE_URL)s/opensearchdescription" />
<moz:SearchForm>%(CFG_BASE_URL)s</moz:SearchForm>
</OpenSearchDescription>""" % \
  {'CFG_BASE_URL': CFG_BASE_URL,
   'short_name': CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME)[:16],
   'long_name': CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME),
   'description': (_("Search on %(x_CFG_SITE_NAME_INTL)s") % \
   {'x_CFG_SITE_NAME_INTL': CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME)})[:1024],
   'CFG_SITE_ADMIN_EMAIL': CFG_SITE_ADMIN_EMAIL,
   'rss_search_syntax': self.tmpl_opensearch_rss_url_syntax,
   'html_search_syntax': self.tmpl_opensearch_html_url_syntax
   }

    def build_search_url(self, known_parameters={}, **kargs):
        """ Helper for generating a canonical search
        url. 'known_parameters' is the list of query parameters you
        inherit from your current query. You can then pass keyword
        arguments to modify this query.

           build_search_url(known_parameters, of="xm")

        The generated URL is absolute.
        """

        parameters = {}
        parameters.update(known_parameters)
        parameters.update(kargs)

        # Now, we only have the arguments which have _not_ their default value
        parameters = drop_default_urlargd(parameters, self.search_results_default_urlargd)

        # Treat `as' argument specially:
        if parameters.has_key('aas'):
            parameters['as'] = parameters['aas']
            del parameters['aas']

        # Asking for a recid? Return a /CFG_SITE_RECORD/<recid> URL
        if 'recid' in parameters:
            target = "%s/%s/%s" % (CFG_BASE_URL, CFG_SITE_RECORD, parameters['recid'])
            del parameters['recid']
            target += make_canonical_urlargd(parameters, self.search_results_default_urlargd)
            return target

        return "%s/search%s" % (CFG_BASE_URL, make_canonical_urlargd(parameters, self.search_results_default_urlargd))

    def build_search_interface_url(self, known_parameters={}, **kargs):
        """ Helper for generating a canonical search interface URL."""

        parameters = {}
        parameters.update(known_parameters)
        parameters.update(kargs)

        c = parameters['c']
        del parameters['c']

        # Now, we only have the arguments which have _not_ their default value
        parameters = drop_default_urlargd(parameters, self.search_results_default_urlargd)

        # Treat `as' argument specially:
        if parameters.has_key('aas'):
            parameters['as'] = parameters['aas']
            del parameters['aas']

        if c and c != CFG_SITE_NAME:
            base = CFG_BASE_URL + '/collection/' + quote(c)
        else:
            base = CFG_BASE_URL
        return create_url(base, parameters)

    def build_rss_url(self, known_parameters, **kargs):
        """Helper for generating a canonical RSS URL"""

        parameters = {}
        parameters.update(known_parameters)
        parameters.update(kargs)

        # Keep only interesting parameters
        argd = wash_urlargd(parameters, self.rss_default_urlargd)

        if argd:
            # Handle 'c' differently since it is a list
            c = argd.get('c', [])
            del argd['c']
            # Create query, and drop empty params
            args = make_canonical_urlargd(argd, self.rss_default_urlargd)
            if c != []:
                # Add collections
                c = [quote(coll) for coll in c]
                if args == '':
                    args += '?'
                else:
                    args += '&amp;'
                args += 'c=' + '&amp;c='.join(c)

        return CFG_BASE_URL + '/rss' + args

    def tmpl_record_page_header_content(self, req, recid, ln):
        """
        Provide extra information in the header of /CFG_SITE_RECORD pages

        Return (title, description, keywords), not escaped for HTML
        """

        _ = gettext_set_language(ln)

        title = get_fieldvalues(recid, "245__a") or \
                get_fieldvalues(recid, "111__a")

        if title:
            title = title[0]
        else:
            title = _("Record") + ' #%d' % recid

        keywords = ', '.join(get_fieldvalues(recid, "6531_a"))
        description = ' '.join(get_fieldvalues(recid, "520__a"))
        description += "\n"
        description += '; '.join(get_fieldvalues(recid, "100__a") + get_fieldvalues(recid, "700__a"))

        return (title, description, keywords)


    def tmpl_exact_author_browse_help_link(self, p, p1, p2, p3, f, f1, f2, f3, rm, cc, ln, jrec, rg, aas, action, link_name):
        """
        Creates the 'exact author' help link for browsing.

        """
        _ = gettext_set_language(ln)
        url = create_html_link(self.build_search_url(p=p,
                                                     p1=p1,
                                                     p2=p2,
                                                     p3=p3,
                                                     f=f,
                                                     f1=f1,
                                                     f2=f2,
                                                     f3=f3,
                                                     rm=rm,
                                                     cc=cc,
                                                     ln=ln,
                                                     jrec=jrec,
                                                     rg=rg,
                                                     aas=aas,
                                                     action=action),
                               {}, _(link_name), {'class': 'nearestterms'})
        return "Did you mean to browse in %s index?" % url


    def tmpl_navtrail_links(self, aas, ln, dads):
        """
        Creates the navigation bar at top of each search page (*Home > Root collection > subcollection > ...*)

        Parameters:

          - 'aas' *int* - Should we display an advanced search box?

          - 'ln' *string* - The language to display

          - 'separator' *string* - The separator between two consecutive collections

          - 'dads' *list* - A list of parent links, eachone being a dictionary of ('name', 'longname')
        """
        out = []
        for url, name in dads:
            args = {'c': url, 'as': aas, 'ln': ln}
            out.append(create_html_link(self.build_search_interface_url(**args), {}, cgi.escape(name), {'class': 'navtrail'}))

        return ' &gt; '.join(out)

    def tmpl_webcoll_body(self, ln, collection, te_portalbox,
                          searchfor, np_portalbox, narrowsearch,
                          focuson, instantbrowse, ne_portalbox, show_body=True):

        """ Creates the body of the main search page.

        Parameters:

          - 'ln' *string* - language of the page being generated

          - 'collection' - collection id of the page being generated

          - 'te_portalbox' *string* - The HTML code for the portalbox on top of search

          - 'searchfor' *string* - The HTML code for the search for box

          - 'np_portalbox' *string* - The HTML code for the portalbox on bottom of search

          - 'narrowsearch' *string* - The HTML code for the search categories (left bottom of page)

          - 'focuson' *string* - The HTML code for the "focuson" categories (right bottom of page)

          - 'ne_portalbox' *string* - The HTML code for the bottom of the page
        """

        if not narrowsearch:
            narrowsearch = instantbrowse

        body = '''
               <form name="search" action="%(siteurl)s/search" method="get">
               %(searchfor)s
               %(np_portalbox)s
               ''' % {
                   'siteurl': CFG_BASE_URL,
                   'searchfor': searchfor,
                   'np_portalbox': np_portalbox
               }
        if show_body:
            body += '''
                    <table cellspacing="0" cellpadding="0" border="0" class="narrowandfocusonsearchbox">
                      <tr>
                        <td valign="top">%(narrowsearch)s</td>
                   ''' % { 'narrowsearch' : narrowsearch }
            if focuson:
                body += """<td valign="top">""" + focuson + """</td>"""
            body += """</tr></table>"""
        elif focuson:
            body += focuson
        body += """%(ne_portalbox)s
               </form>""" % {'ne_portalbox' : ne_portalbox}
        return body

    def tmpl_portalbox(self, title, body):
        """Creates portalboxes based on the parameters
        Parameters:

          - 'title' *string* - The title of the box

          - 'body' *string* - The HTML code for the body of the box

        """
        out = """<div class="portalbox">
                    <div class="portalboxheader">%(title)s</div>
                    <div class="portalboxbody">%(body)s</div>
                 </div>""" % {'title' : cgi.escape(title), 'body' : body}

        return out

    def tmpl_searchfor_light(self, ln, collection_id, collection_name, record_count,
                             example_search_queries): # EXPERIMENTAL
        """Produces light *Search for* box for the current collection.

        Parameters:

          - 'ln' *string* - *str* The language to display

          - 'collection_id' - *str* The collection id

          - 'collection_name' - *str* The collection name in current language

          - 'example_search_queries' - *list* List of search queries given as example for this collection
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = '''
        <!--create_searchfor_light()-->
        '''

        argd = drop_default_urlargd({'ln': ln, 'sc': CFG_WEBSEARCH_SPLIT_BY_COLLECTION},
                                    self.search_results_default_urlargd)

        # Only add non-default hidden values
        for field, value in argd.items():
            out += self.tmpl_input_hidden(field, value)


        header = _("Search %s records for:") % \
                 self.tmpl_nbrecs_info(record_count, "", "")
        asearchurl = self.build_search_interface_url(c=collection_id,
                                                     aas=max(CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES),
                                                     ln=ln)

        # Build example of queries for this collection
        example_search_queries_links = [create_html_link(self.build_search_url(p=example_query,
                                                                               ln=ln,
                                                                               aas= -1,
                                                                               c=collection_id),
                                                         {},
                                                         cgi.escape(example_query),
                                                         {'class': 'examplequery'}) \
                                        for example_query in example_search_queries]
        example_query_html = ''
        if len(example_search_queries) > 0:
            example_query_link = example_search_queries_links[0]

            # offers more examples if possible
            more = ''
            if len(example_search_queries_links) > 1:
                more = '''
                <script type="text/javascript">
                function toggle_more_example_queries_visibility(){
                    var more = document.getElementById('more_example_queries');
                    var link = document.getElementById('link_example_queries');
                    var sep = document.getElementById('more_example_sep');
                    if (more.style.display=='none'){
                        more.style.display = '';
                        link.innerHTML = "%(show_less)s"
                        link.style.color = "rgb(204,0,0)";
                        sep.style.display = 'none';
                    } else {
                        more.style.display = 'none';
                        link.innerHTML = "%(show_more)s"
                        link.style.color = "rgb(0,0,204)";
                        sep.style.display = '';
                    }
                    return false;
                }
                </script>
                <span id="more_example_queries" style="display:none;text-align:right"><br/>%(more_example_queries)s<br/></span>
                <a id="link_example_queries" href="#" onclick="toggle_more_example_queries_visibility()" style="display:none"></a>
                <script type="text/javascript">
                    var link = document.getElementById('link_example_queries');
                    var sep = document.getElementById('more_example_sep');
                    link.style.display = '';
                    link.innerHTML = "%(show_more)s";
                    sep.style.display = '';
                </script>
                ''' % {'more_example_queries': '<br/>'.join(example_search_queries_links[1:]),
                       'show_less':_("less"),
                       'show_more':_("more")}

            example_query_html += '''<p style="text-align:right;margin:0px;">
            %(example)s<span id="more_example_sep" style="display:none;">&nbsp;&nbsp;::&nbsp;</span>%(more)s
            </p>
            ''' % {'example': _("Example: %(x_sample_search_query)s") % \
                   {'x_sample_search_query': example_query_link},
                   'more': more}

        # display options to search in current collection or everywhere
        search_in = ''
        if collection_name != CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME):
            search_in += '''
           <input type="radio" name="cc" value="%(collection_id)s" id="searchCollection" checked="checked"/>
           <label for="searchCollection">%(search_in_collection_name)s</label>
           <input type="radio" name="cc" value="%(root_collection_name)s" id="searchEverywhere" />
           <label for="searchEverywhere">%(search_everywhere)s</label>
           ''' % {'search_in_collection_name': _("Search in %(x_collection_name)s") % \
                  {'x_collection_name': collection_name},
                  'collection_id': collection_id,
                  'root_collection_name': CFG_SITE_NAME,
                  'search_everywhere': _("Search everywhere")}

        # print commentary start:
        out += '''
        <table class="searchbox lightsearch">
         <tbody>
          <tr valign="baseline">
           <td class="searchboxbody" align="right"><input type="text" name="p" size="%(sizepattern)d" value="" class="lightsearchfield"/><br/>
             <small><small>%(example_query_html)s</small></small>
           </td>
           <td class="searchboxbody" align="left">
             <input class="formbutton" type="submit" name="action_search" value="%(msg_search)s" />
           </td>
           <td class="searchboxbody" align="left" rowspan="2" valign="top">
             <small><small>
             <a href="%(siteurl)s/help/search-tips%(langlink)s">%(msg_search_tips)s</a><br/>
             %(asearch)s
             </small></small>
           </td>
          </tr></table>
          <!--<tr valign="baseline">
           <td class="searchboxbody" colspan="2" align="left">
             <small>
               --><small>%(search_in)s</small><!--
             </small>
           </td>
          </tr>
         </tbody>
        </table>-->
        <!--/create_searchfor_light()-->
        ''' % {'ln' : ln,
               'sizepattern' : CFG_WEBSEARCH_LIGHTSEARCH_PATTERN_BOX_WIDTH,
               'langlink': '?ln=' + ln,
               'siteurl' : CFG_BASE_URL,
               'asearch' : create_html_link(asearchurl, {}, _('Advanced Search')),
               'header' : header,
               'msg_search' : _('Search'),
               'msg_browse' : _('Browse'),
               'msg_search_tips' : _('Search Tips'),
               'search_in': search_in,
               'example_query_html': example_query_html}

        return out

    def tmpl_searchfor_simple(self, ln, collection_id, collection_name, record_count, middle_option):
        """Produces simple *Search for* box for the current collection.

        Parameters:

          - 'ln' *string* - *str* The language to display

          - 'collection_id' - *str* The collection id

          - 'collection_name' - *str* The collection name in current language

          - 'record_count' - *str* Number of records in this collection

          - 'middle_option' *string* - HTML code for the options (any field, specific fields ...)
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = '''
        <!--create_searchfor_simple()-->
        '''

        argd = drop_default_urlargd({'ln': ln, 'cc': collection_id, 'sc': CFG_WEBSEARCH_SPLIT_BY_COLLECTION},
                                    self.search_results_default_urlargd)

        # Only add non-default hidden values
        for field, value in argd.items():
            out += self.tmpl_input_hidden(field, value)


        header = _("Search %s records for:") % \
                 self.tmpl_nbrecs_info(record_count, "", "")
        asearchurl = self.build_search_interface_url(c=collection_id,
                                                     aas=max(CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES),
                                                     ln=ln)
        # print commentary start:
        out += '''
        <table class="searchbox simplesearch">
         <thead>
          <tr align="left">
           <th colspan="3" class="searchboxheader">%(header)s</th>
          </tr>
         </thead>
         <tbody>
          <tr valign="baseline">
           <td class="searchboxbody" align="left"><input type="text" name="p" size="%(sizepattern)d" value="" class="simplesearchfield"/></td>
           <td class="searchboxbody" align="left">%(middle_option)s</td>
           <td class="searchboxbody" align="left">
             <input class="formbutton" type="submit" name="action_search" value="%(msg_search)s" />
             <input class="formbutton" type="submit" name="action_browse" value="%(msg_browse)s" /></td>
          </tr>
          <tr valign="baseline">
           <td class="searchboxbody" colspan="3" align="right">
             <small>
               <a href="%(siteurl)s/help/search-tips%(langlink)s">%(msg_search_tips)s</a> ::
               %(asearch)s
             </small>
           </td>
          </tr>
         </tbody>
        </table>
        <!--/create_searchfor_simple()-->
        ''' % {'ln' : ln,
               'sizepattern' : CFG_WEBSEARCH_SIMPLESEARCH_PATTERN_BOX_WIDTH,
               'langlink': '?ln=' + ln,
               'siteurl' : CFG_BASE_URL,
               'asearch' : create_html_link(asearchurl, {}, _('Advanced Search')),
               'header' : header,
               'middle_option' : middle_option,
               'msg_search' : _('Search'),
               'msg_browse' : _('Browse'),
               'msg_search_tips' : _('Search Tips')}

        return out

    def tmpl_searchfor_advanced(self,
                                ln, # current language
                                collection_id,
                                collection_name,
                                record_count,
                                middle_option_1, middle_option_2, middle_option_3,
                                searchoptions,
                                sortoptions,
                                rankoptions,
                                displayoptions,
                                formatoptions
                                ):
        """
          Produces advanced *Search for* box for the current collection.

          Parameters:

            - 'ln' *string* - The language to display

            - 'middle_option_1' *string* - HTML code for the first row of options (any field, specific fields ...)

            - 'middle_option_2' *string* - HTML code for the second row of options (any field, specific fields ...)

            - 'middle_option_3' *string* - HTML code for the third row of options (any field, specific fields ...)

            - 'searchoptions' *string* - HTML code for the search options

            - 'sortoptions' *string* - HTML code for the sort options

            - 'rankoptions' *string* - HTML code for the rank options

            - 'displayoptions' *string* - HTML code for the display options

            - 'formatoptions' *string* - HTML code for the format options

        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = '''
        <!--create_searchfor_advanced()-->
        '''

        argd = drop_default_urlargd({'ln': ln, 'aas': 1, 'cc': collection_id, 'sc': CFG_WEBSEARCH_SPLIT_BY_COLLECTION},
                                    self.search_results_default_urlargd)

        # Only add non-default hidden values
        for field, value in argd.items():
            out += self.tmpl_input_hidden(field, value)


        header = _("Search %s records for") % \
                 self.tmpl_nbrecs_info(record_count, "", "")
        header += ':'
        ssearchurl = self.build_search_interface_url(c=collection_id, aas=min(CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES), ln=ln)

        out += '''
        <table class="searchbox advancedsearch">
         <thead>
          <tr>
           <th class="searchboxheader" colspan="3">%(header)s</th>
          </tr>
         </thead>
         <tbody>
          <tr valign="bottom">
            <td class="searchboxbody" style="white-space: nowrap;">
                %(matchbox_m1)s<input type="text" name="p1" size="%(sizepattern)d" value="" class="advancedsearchfield"/>
            </td>
            <td class="searchboxbody" style="white-space: nowrap;">%(middle_option_1)s</td>
            <td class="searchboxbody">%(andornot_op1)s</td>
          </tr>
          <tr valign="bottom">
            <td class="searchboxbody" style="white-space: nowrap;">
                %(matchbox_m2)s<input type="text" name="p2" size="%(sizepattern)d" value="" class="advancedsearchfield"/>
            </td>
            <td class="searchboxbody">%(middle_option_2)s</td>
            <td class="searchboxbody">%(andornot_op2)s</td>
          </tr>
          <tr valign="bottom">
            <td class="searchboxbody" style="white-space: nowrap;">
                %(matchbox_m3)s<input type="text" name="p3" size="%(sizepattern)d" value="" class="advancedsearchfield"/>
            </td>
            <td class="searchboxbody">%(middle_option_3)s</td>
            <td class="searchboxbody" style="white-space: nowrap;">
              <input class="formbutton" type="submit" name="action_search" value="%(msg_search)s" />
              <input class="formbutton" type="submit" name="action_browse" value="%(msg_browse)s" /></td>
          </tr>
          <tr valign="bottom">
            <td colspan="3" class="searchboxbody" align="right">
              <small>
                <a href="%(siteurl)s/help/search-tips%(langlink)s">%(msg_search_tips)s</a> ::
                %(ssearch)s
              </small>
            </td>
          </tr>
         </tbody>
        </table>
        <!-- @todo - more imports -->
        ''' % {'ln' : ln,
               'sizepattern' : CFG_WEBSEARCH_ADVANCEDSEARCH_PATTERN_BOX_WIDTH,
               'langlink': '?ln=' + ln,
               'siteurl' : CFG_BASE_URL,
               'ssearch' : create_html_link(ssearchurl, {}, _("Simple Search")),
               'header' : header,

               'matchbox_m1' : self.tmpl_matchtype_box('m1', ln=ln),
               'middle_option_1' : middle_option_1,
               'andornot_op1' : self.tmpl_andornot_box('op1', ln=ln),

               'matchbox_m2' : self.tmpl_matchtype_box('m2', ln=ln),
               'middle_option_2' : middle_option_2,
               'andornot_op2' : self.tmpl_andornot_box('op2', ln=ln),

               'matchbox_m3' : self.tmpl_matchtype_box('m3', ln=ln),
               'middle_option_3' : middle_option_3,

               'msg_search' : _("Search"),
               'msg_browse' : _("Browse"),
               'msg_search_tips' : _("Search Tips")}

        if (searchoptions):
            out += """<table class="searchbox">
                      <thead>
                       <tr>
                         <th class="searchboxheader">
                           %(searchheader)s
                         </th>
                       </tr>
                      </thead>
                      <tbody>
                       <tr valign="bottom">
                        <td class="searchboxbody">%(searchoptions)s</td>
                       </tr>
                      </tbody>
                     </table>""" % {
                       'searchheader' : _("Search options:"),
                       'searchoptions' : searchoptions
                     }

        out += """<table class="searchbox">
                   <thead>
                    <tr>
                      <th class="searchboxheader">
                        %(added)s
                      </th>
                      <th class="searchboxheader">
                        %(until)s
                      </th>
                    </tr>
                   </thead>
                   <tbody>
                    <tr valign="bottom">
                      <td class="searchboxbody">%(added_or_modified)s %(date_added)s</td>
                      <td class="searchboxbody">%(date_until)s</td>
                    </tr>
                   </tbody>
                  </table>
                  <table class="searchbox">
                   <thead>
                    <tr>
                      <th class="searchboxheader">
                        %(msg_sort)s
                      </th>
                      <th class="searchboxheader">
                        %(msg_display)s
                      </th>
                      <th class="searchboxheader">
                        %(msg_format)s
                      </th>
                    </tr>
                   </thead>
                   <tbody>
                    <tr valign="bottom">
                      <td class="searchboxbody">%(sortoptions)s %(rankoptions)s</td>
                      <td class="searchboxbody">%(displayoptions)s</td>
                      <td class="searchboxbody">%(formatoptions)s</td>
                    </tr>
                   </tbody>
                  </table>
                  <!--/create_searchfor_advanced()-->
              """ % {

                    'added' : _("Added/modified since:"),
                    'until' : _("until:"),
                    'added_or_modified': self.tmpl_inputdatetype(ln=ln),
                    'date_added' : self.tmpl_inputdate("d1", ln=ln),
                    'date_until' : self.tmpl_inputdate("d2", ln=ln),

                    'msg_sort' : _("Sort by:"),
                    'msg_display' : _("Display results:"),
                    'msg_format' : _("Output format:"),
                    'sortoptions' : sortoptions,
                    'rankoptions' : rankoptions,
                    'displayoptions' : displayoptions,
                    'formatoptions' : formatoptions
                  }
        return out

    def tmpl_matchtype_box(self, name='m', value='', ln='en'):
        """Returns HTML code for the 'match type' selection box.

          Parameters:

            - 'name' *string* - The name of the produced select

            - 'value' *string* - The selected value (if any value is already selected)

            - 'ln' *string* - the language to display
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
        <select name="%(name)s">
        <option value="a"%(sela)s>%(opta)s</option>
        <option value="o"%(selo)s>%(opto)s</option>
        <option value="e"%(sele)s>%(opte)s</option>
        <option value="p"%(selp)s>%(optp)s</option>
        <option value="r"%(selr)s>%(optr)s</option>
        </select>
        """ % {'name' : name,
               'sela' : self.tmpl_is_selected('a', value),
                                                           'opta' : _("All of the words:"),
               'selo' : self.tmpl_is_selected('o', value),
                                                           'opto' : _("Any of the words:"),
               'sele' : self.tmpl_is_selected('e', value),
                                                           'opte' : _("Exact phrase:"),
               'selp' : self.tmpl_is_selected('p', value),
                                                           'optp' : _("Partial phrase:"),
               'selr' : self.tmpl_is_selected('r', value),
                                                           'optr' : _("Regular expression:")
              }
        return out

    def tmpl_is_selected(self, var, fld):
        """
          Checks if *var* and *fld* are equal, and if yes, returns ' selected="selected"'.  Useful for select boxes.

          Parameters:

          - 'var' *string* - First value to compare

          - 'fld' *string* - Second value to compare
        """
        if var == fld:
            return ' selected="selected"'
        else:
            return ""

    def tmpl_andornot_box(self, name='op', value='', ln='en'):
        """
          Returns HTML code for the AND/OR/NOT selection box.

          Parameters:

            - 'name' *string* - The name of the produced select

            - 'value' *string* - The selected value (if any value is already selected)

            - 'ln' *string* - the language to display
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
        <select name="%(name)s">
        <option value="a"%(sela)s>%(opta)s</option>
        <option value="o"%(selo)s>%(opto)s</option>
        <option value="n"%(seln)s>%(optn)s</option>
        </select>
        """ % {'name' : name,
               'sela' : self.tmpl_is_selected('a', value), 'opta' : _("AND"),
               'selo' : self.tmpl_is_selected('o', value), 'opto' : _("OR"),
               'seln' : self.tmpl_is_selected('n', value), 'optn' : _("AND NOT")
              }
        return out

    def tmpl_inputdate(self, name, ln, sy=0, sm=0, sd=0):
        """
          Produces *From Date*, *Until Date* kind of selection box. Suitable for search options.

          Parameters:

            - 'name' *string* - The base name of the produced selects

            - 'ln' *string* - the language to display
        """
        # load the right message language
        _ = gettext_set_language(ln)

        box = """
               <select name="%(name)sd">
                 <option value=""%(sel)s>%(any)s</option>
              """ % {
                'name' : name,
                'any' : _("any day"),
                'sel' : self.tmpl_is_selected(sd, 0)
              }
        for day in range(1, 32):
            box += """<option value="%02d"%s>%02d</option>""" % (day, self.tmpl_is_selected(sd, day), day)
        box += """</select>"""
        # month
        box += """
                <select name="%(name)sm">
                  <option value=""%(sel)s>%(any)s</option>
               """ % {
                 'name' : name,
                 'any' : _("any month"),
                 'sel' : self.tmpl_is_selected(sm, 0)
               }
        # trailing space in May distinguishes short/long form of the month name
        for mm, month in [(1, _("January")), (2, _("February")), (3, _("March")), (4, _("April")), \
                          (5, _("May ")), (6, _("June")), (7, _("July")), (8, _("August")), \
                          (9, _("September")), (10, _("October")), (11, _("November")), (12, _("December"))]:
            box += """<option value="%02d"%s>%s</option>""" % (mm, self.tmpl_is_selected(sm, mm), month.strip())
        box += """</select>"""
        # year
        box += """
                <select name="%(name)sy">
                  <option value=""%(sel)s>%(any)s</option>
               """ % {
                 'name' : name,
                 'any' : _("any year"),
                 'sel' : self.tmpl_is_selected(sy, 0)
               }
        this_year = int(time.strftime("%Y", time.localtime()))
        for year in range(this_year - 20, this_year + 1):
            box += """<option value="%d"%s>%d</option>""" % (year, self.tmpl_is_selected(sy, year), year)
        box += """</select>"""
        return box

    def tmpl_inputdatetype(self, dt='', ln=CFG_SITE_LANG):
        """
          Produces input date type selection box to choose
          added-or-modified date search option.

          Parameters:

            - 'dt' *string - date type (c=created, m=modified)

            - 'ln' *string* - the language to display
        """
        # load the right message language
        _ = gettext_set_language(ln)

        box = """<select name="dt">
                  <option value="">%(added)s </option>
                  <option value="m"%(sel)s>%(modified)s </option>
                 </select>
              """ % { 'added': _("Added since:"),
                      'modified': _("Modified since:"),
                      'sel': self.tmpl_is_selected(dt, 'm'),
                    }
        return box

    def tmpl_narrowsearch(self, aas, ln, type, father,
                          has_grandchildren, sons, display_grandsons,
                          grandsons):

        """
        Creates list of collection descendants of type *type* under title *title*.
        If aas==1, then links to Advanced Search interfaces; otherwise Simple Search.
        Suitable for 'Narrow search' and 'Focus on' boxes.

        Parameters:

          - 'aas' *bool* - Should we display an advanced search box?

          - 'ln' *string* - The language to display

          - 'type' *string* - The type of the produced box (virtual collections or normal collections)

          - 'father' *collection* - The current collection

          - 'has_grandchildren' *bool* - If the current collection has grand children

          - 'sons' *list* - The list of the sub-collections (first level)

          - 'display_grandsons' *bool* - If the grand children collections should be displayed (2 level deep display)

          - 'grandsons' *list* - The list of sub-collections (second level)
        """

        # load the right message language
        _ = gettext_set_language(ln)

        title = father.get_collectionbox_name(ln, type)

        if has_grandchildren:
            style_class = 'collection-first-level collection-father-has-grandchildren'
        else:
            style_class = 'collection-first-level'

        out = """<table class="%(narrowsearchbox)s">
                   <thead>
                    <tr>
                     <th colspan="2" align="left" class="%(narrowsearchbox)sheader">
                      %(title)s
                     </th>
                    </tr>
                   </thead>
                   <tbody>""" % {'title' : title,
                                 'narrowsearchbox': {'r': 'narrowsearchbox',
                                                     'v': 'focusonsearchbox'}[type]}
        # iterate through sons:
        i = 0
        for son in sons:
            out += """<tr><td class="%(narrowsearchbox)sbody" valign="top">""" % \
                   { 'narrowsearchbox': {'r': 'narrowsearchbox',
                                         'v': 'focusonsearchbox'}[type]}

            if type == 'r':
                if son.restricted_p() and son.restricted_p() != father.restricted_p():
                    out += """<input type="checkbox" name="c" value="%(name)s" /></td>""" % {'name' : cgi.escape(son.name) }
                # hosted collections are checked by default only when configured so
                elif str(son.dbquery).startswith("hostedcollection:"):
                    external_collection_engine = get_external_collection_engine(str(son.name))
                    if external_collection_engine and external_collection_engine.selected_by_default:
                        out += """<input type="checkbox" name="c" value="%(name)s" checked="checked" /></td>""" % {'name' : cgi.escape(son.name) }
                    elif external_collection_engine and not external_collection_engine.selected_by_default:
                        out += """<input type="checkbox" name="c" value="%(name)s" /></td>""" % {'name' : cgi.escape(son.name) }
                    else:
                        # strangely, the external collection engine was never found. In that case,
                        # why was the hosted collection here in the first place?
                        out += """<input type="checkbox" name="c" value="%(name)s" /></td>""" % {'name' : cgi.escape(son.name) }
                else:
                    out += """<input type="checkbox" name="c" value="%(name)s" checked="checked" /></td>""" % {'name' : cgi.escape(son.name) }
            else:
                out += '</td>'
            out += """<td valign="top"><span class="%(style_class)s">%(link)s%(recs)s</span> """ % {
                'link': create_html_link(self.build_search_interface_url(c=son.name, ln=ln, aas=aas),
                                         {}, cgi.escape(son.get_name(ln))),
                'recs' : self.tmpl_nbrecs_info(son.nbrecs, ln=ln),
                'style_class': style_class}

            # the following prints the "external collection" arrow just after the name and
            # number of records of the hosted collection
            # 1) we might want to make the arrow work as an anchor to the hosted collection as well.
            # That would probably require a new separate function under invenio.urlutils
            # 2) we might want to place the arrow between the name and the number of records of the hosted collection
            # That would require to edit/separate the above out += ...
            if type == 'r':
                if str(son.dbquery).startswith("hostedcollection:"):
                    out += """<img src="%(siteurl)s/img/external-icon-light-8x8.gif" border="0" alt="%(name)s"/>""" % \
                           { 'siteurl' : CFG_BASE_URL, 'name' : cgi.escape(son.name), }

            if son.restricted_p():
                out += """ <small class="warning">[%(msg)s]</small> """ % { 'msg' : _("restricted") }
            if display_grandsons and len(grandsons[i]):
                # iterate trough grandsons:
                out += """<ul class="collection-second-level">"""
                for grandson in grandsons[i]:
                    out += """ <li>%(link)s%(nbrec)s</li> """ % {
                        'link': create_html_link(self.build_search_interface_url(c=grandson.name, ln=ln, aas=aas),
                                                 {},
                                                 cgi.escape(grandson.get_name(ln))),
                        'nbrec' : self.tmpl_nbrecs_info(grandson.nbrecs, ln=ln)}
                    # the following prints the "external collection" arrow just after the name and
                    # number of records of the hosted collection
                    # Some relatives comments have been made just above
                    if type == 'r':
                        if str(grandson.dbquery).startswith("hostedcollection:"):
                            out += """<img src="%(siteurl)s/img/external-icon-light-8x8.gif" border="0" alt="%(name)s"/>""" % \
                                    { 'siteurl' : CFG_BASE_URL, 'name' : cgi.escape(grandson.name), }
                out += """</ul>"""

            out += """</td></tr>"""
            i += 1
        out += "</tbody></table>"

        return out

    def tmpl_searchalso(self, ln, engines_list, collection_id):
        _ = gettext_set_language(ln)

        box_name = _("Search also:")

        html = """<table cellspacing="0" cellpadding="0" border="0">
            <tr><td valign="top"><table class="searchalsosearchbox">
            <thead><tr><th colspan="2" align="left" class="searchalsosearchboxheader">%(box_name)s
            </th></tr></thead><tbody>
        """ % locals()

        for engine in engines_list:
            internal_name = engine.name
            name = _(internal_name)
            base_url = engine.base_url
            if external_collection_get_state(engine, collection_id) == 3:
                checked = ' checked="checked"'
            else:
                checked = ''

            html += """<tr><td class="searchalsosearchboxbody" valign="top">
                <input type="checkbox" name="ec" id="%(id)s" value="%(internal_name)s" %(checked)s /></td>
                <td valign="top" class="searchalsosearchboxbody">
                <div style="white-space: nowrap"><label for="%(id)s">%(name)s</label>
                <a href="%(base_url)s">
                <img src="%(siteurl)s/img/external-icon-light-8x8.gif" border="0" alt="%(name)s"/></a>
                </div></td></tr>""" % \
                                 { 'checked': checked,
                                   'base_url': base_url,
                                   'internal_name': internal_name,
                                   'name': cgi.escape(name),
                                   'id': "extSearch" + nmtoken_from_string(name),
                                   'siteurl': CFG_BASE_URL, }

        html += """</tbody></table></td></tr></table>"""
        return html

    def tmpl_nbrecs_info(self, number, prolog=None, epilog=None, ln=CFG_SITE_LANG):
        """
        Return information on the number of records.

        Parameters:

        - 'number' *string* - The number of records

        - 'prolog' *string* (optional) - An HTML code to prefix the number (if **None**, will be
        '<small class="nbdoccoll">(')

        - 'epilog' *string* (optional) - An HTML code to append to the number (if **None**, will be
        ')</small>')
        """

        if number is None:
            number = 0
        if prolog is None:
            prolog = '''&nbsp;<small class="nbdoccoll">('''
        if epilog is None:
            epilog = ''')</small>'''

        return prolog + self.tmpl_nice_number(number, ln) + epilog

    def tmpl_box_restricted_content(self, ln):
        """
          Displays a box containing a *restricted content* message

        Parameters:

          - 'ln' *string* - The language to display

        """

        # load the right message language
        _ = gettext_set_language(ln)

        return _("This collection is restricted.  If you are authorized to access it, please click on the Search button.")

    def tmpl_box_hosted_collection(self, ln):
        """
          Displays a box containing a *hosted collection* message

        Parameters:

          - 'ln' *string* - The language to display

        """

        # load the right message language
        _ = gettext_set_language(ln)

        return _("This is a hosted external collection. Please click on the Search button to see its content.")

    def tmpl_box_no_records(self, ln):
        """
          Displays a box containing a *no content* message

        Parameters:

          - 'ln' *string* - The language to display

        """

        # load the right message language
        _ = gettext_set_language(ln)

        return _("This collection does not contain any document yet.")


    def tmpl_instant_browse(self, aas, ln, recids, more_link=None, grid_layout=False, father=None):
        """
          Formats a list of records (given in the recids list) from the database.

        Parameters:

          - 'aas' *int* - Advanced Search interface or not (0 or 1)

          - 'ln' *string* - The language to display

          - 'recids' *list* - the list of records from the database

          - 'more_link' *string* - the "More..." link for the record. If not given, will not be displayed

          - 'father' *collection* - The current collection
        """

        # load the right message language
        _ = gettext_set_language(ln)

        body = '''<table class="latestadditionsbox">'''
        if grid_layout:
            body += '<tr><td><div>'
        for recid in recids:
            if grid_layout:
                body += '''
                <abbr class="unapi-id" title="%(recid)s"></abbr>
                %(body)s
            ''' % {
                'recid': recid['id'],
                'body': recid['body']}
            else:
                body += '''
                <tr>
                  <td class="latestadditionsboxtimebody">%(date)s</td>
                  <td class="latestadditionsboxrecordbody">
                    <abbr class="unapi-id" title="%(recid)s"></abbr>
                    %(body)s
                  </td>
                </tr>''' % {
                        'recid': recid['id'],
                        'date': recid['date'],
                        'body': recid['body']
                      }
        if grid_layout:
            body += '''<div style="clear:both"></div>'''
            body += '''</div></td></tr>'''
        body += "</table>"
        if more_link:
            body += '<div align="right"><small>' + \
                    create_html_link(more_link, {}, '[&gt;&gt; %s]' % _("more")) + \
                    '</small></div>'

        return '''
        <table class="narrowsearchbox">
          <thead>
            <tr>
              <th class="narrowsearchboxheader">%(header)s</th>
            </tr>
          </thead>
          <tbody>
            <tr>
            <td class="narrowsearchboxbody">%(body)s</td>
            </tr>
          </tbody>
        </table>''' % {'header' : father.get_collectionbox_name(ln, 'l') ,
                       'body' : body,
                       }


    def tmpl_searchwithin_select(self, ln, fieldname, selected, values):
        """
          Produces 'search within' selection box for the current collection.

        Parameters:

          - 'ln' *string* - The language to display

          - 'fieldname' *string* - the name of the select box produced

          - 'selected' *string* - which of the values is selected

          - 'values' *list* - the list of values in the select
        """

        out = '<select name="%(fieldname)s">' % {'fieldname': fieldname}

        if values:
            for pair in values:
                out += """<option value="%(value)s"%(selected)s>%(text)s</option>""" % {
                         'value'    : cgi.escape(pair['value']),
                         'selected' : self.tmpl_is_selected(pair['value'], selected),
                         'text'     : cgi.escape(pair['text'])
                       }
        out += """</select>"""
        return out

    def tmpl_select(self, fieldname, values, selected=None, css_class=''):
        """
          Produces a generic select box

        Parameters:

          - 'css_class' *string* - optional, a css class to display this select with

          - 'fieldname' *list* - the name of the select box produced

          - 'selected' *string* - which of the values is selected

          - 'values' *list* - the list of values in the select
        """
        if css_class != '':
            class_field = ' class="%s"' % css_class
        else:
            class_field = ''
        out = '<select name="%(fieldname)s"%(class)s>' % {
            'fieldname' : fieldname,
            'class' : class_field
            }

        for pair in values:
            if pair.get('selected', False) or pair['value'] == selected:
                flag = ' selected="selected"'
            else:
                flag = ''

            out += '<option value="%(value)s"%(selected)s>%(text)s</option>' % {
                     'value'    : cgi.escape(str(pair['value'])),
                     'selected' : flag,
                     'text'     : cgi.escape(pair['text'])
                   }

        out += """</select>"""
        return out

    def tmpl_record_links(self, recid, ln, sf='', so='d', sp='', rm=''):
        """
          Displays the *More info* and *Find similar* links for a record

        Parameters:

          - 'ln' *string* - The language to display

          - 'recid' *string* - the id of the displayed record
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = '''<br /><span class="moreinfo">%(detailed)s - %(similar)s</span>''' % {
            'detailed': create_html_link(self.build_search_url(recid=recid, ln=ln),
                                         {},
                                         _("Detailed record"), {'class': "moreinfo"}),
            'similar': create_html_link(self.build_search_url(p="recid:%d" % recid, rm='wrd', ln=ln),
                                        {},
                                        _("Similar records"),
                                        {'class': "moreinfo"})}

        if CFG_BIBRANK_SHOW_CITATION_LINKS:
            num_timescited = get_cited_by_count(recid)
            if num_timescited:
                out += '''<span class="moreinfo"> - %s </span>''' % \
                       create_html_link(self.build_search_url(p='refersto:recid:%d' % recid,
                                                              sf=sf,
                                                              so=so,
                                                              sp=sp,
                                                              rm=rm,
                                                              ln=ln),
                                        {}, _("Cited by %i records") % num_timescited, {'class': "moreinfo"})

        return out

    def tmpl_record_body(self, titles, authors, dates, rns, abstracts, urls_u, urls_z, ln):
        """
          Displays the "HTML basic" format of a record

        Parameters:

          - 'authors' *list* - the authors (as strings)

          - 'dates' *list* - the dates of publication

          - 'rns' *list* - the quicknotes for the record

          - 'abstracts' *list* - the abstracts for the record

          - 'urls_u' *list* - URLs to the original versions of the record

          - 'urls_z' *list* - Not used
        """
        out = ""
        for title in titles:
            out += "<strong>%(title)s</strong> " % {
                     'title' : cgi.escape(title)
                   }
        if authors:
            out += " / "
            for author in authors[:CFG_WEBSEARCH_AUTHOR_ET_AL_THRESHOLD]:
                out += '%s ' % \
                       create_html_link(self.build_search_url(p=author, f='author', ln=ln),
                                        {}, cgi.escape(author))

            if len(authors) > CFG_WEBSEARCH_AUTHOR_ET_AL_THRESHOLD:
                out += "<em>et al</em>"
        for date in dates:
            out += " %s." % cgi.escape(date)
        for rn in rns:
            out += """ <small class="quicknote">[%(rn)s]</small>""" % {'rn' : cgi.escape(rn)}
        for abstract in abstracts:
            out += "<br /><small>%(abstract)s [...]</small>" % {'abstract' : cgi.escape(abstract[:1 + string.find(abstract, '.')]) }
        for idx in range(0, len(urls_u)):
            out += """<br /><small class="note"><a class="note" href="%(url)s">%(name)s</a></small>""" % {
                     'url' : urls_u[idx],
                     'name' : urls_u[idx]
                   }
        return out

    def tmpl_search_in_bibwords(self, p, f, ln, nearest_box):
        """
          Displays the *Words like current ones* links for a search

        Parameters:

          - 'p' *string* - Current search words

          - 'f' *string* - the fields in which the search was done

          - 'nearest_box' *string* - the HTML code for the "nearest_terms" box - most probably from a create_nearest_terms_box call
        """

        # load the right message language
        _ = gettext_set_language(ln)
        out = '<p>'
        if f:
            out += _("Words nearest to %(x_word)s inside %(x_field)s in any collection are:") % {'x_word': '<em>' + cgi.escape(p) + '</em>',
                                                                                                 'x_field': '<em>' + cgi.escape(f) + '</em>'}
        else:
            out += _("Words nearest to %(x_word)s in any collection are:") % {'x_word': '<em>' + cgi.escape(p) + '</em>'}
        out += '<br />' + nearest_box + '</p>'
        return out

    def tmpl_nearest_term_box(self, p, ln, f, terminfo, intro):
        """
          Displays the *Nearest search terms* box

        Parameters:

          - 'p' *string* - Current search words

          - 'f' *string* - a collection description (if the search has been completed in a collection)

          - 'ln' *string* - The language to display

          - 'terminfo': tuple (term, hits, argd) for each near term

          - 'intro' *string* - the intro HTML to prefix the box with
        """

        out = '''<table class="nearesttermsbox" cellpadding="0" cellspacing="0" border="0">'''

        for term, hits, argd in terminfo:

            if hits:
                hitsinfo = str(hits)
            else:
                hitsinfo = '-'

            term = cgi.escape(term)

            if term == p: # print search word for orientation:
                nearesttermsboxbody_class = "nearesttermsboxbodyselected"
                if hits > 0:
                    term = create_html_link(self.build_search_url(argd), {},
                                            term, {'class': "nearesttermsselected"})
            else:
                nearesttermsboxbody_class = "nearesttermsboxbody"
                term = create_html_link(self.build_search_url(argd), {},
                                        term, {'class': "nearestterms"})

            out += '''\
            <tr>
              <td class="%(nearesttermsboxbody_class)s" align="right">%(hits)s</td>
              <td class="%(nearesttermsboxbody_class)s" width="15">&nbsp;</td>
              <td class="%(nearesttermsboxbody_class)s" align="left">%(term)s</td>
            </tr>
            ''' % {'hits': hitsinfo,
                   'nearesttermsboxbody_class': nearesttermsboxbody_class,
                   'term': term}

        out += "</table>"
        return intro + "<blockquote>" + out + "</blockquote>"

    def tmpl_browse_pattern(self, f, fn, ln, browsed_phrases_in_colls, colls, rg):
        """
          Displays the *Nearest search terms* box

        Parameters:

          - 'f' *string* - field (*not* i18nized)

          - 'fn' *string* - field name (i18nized)

          - 'ln' *string* - The language to display

          - 'browsed_phrases_in_colls' *array* - the phrases to display

          - 'colls' *array* - the list of collection parameters of the search (c's)

          - 'rg' *int* - the number of records
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """<table class="searchresultsbox">
              <thead>
               <tr>
                <th class="searchresultsboxheader" style="text-align: right;" width="15">
                  %(hits)s
                </th>
                <th class="searchresultsboxheader" width="15">
                  &nbsp;
                </th>
                <th class="searchresultsboxheader" style="text-align: left;">
                  %(fn)s
                </th>
               </tr>
              </thead>
              <tbody>""" % {
                'hits' : _("Hits"),
                'fn' : cgi.escape(fn)
              }

        if len(browsed_phrases_in_colls) == 1:
            # one hit only found:
            phrase, nbhits = browsed_phrases_in_colls[0][0], browsed_phrases_in_colls[0][1]

            query = {'c': colls,
                     'ln': ln,
                     'p': '"%s"' % phrase.replace('"', '\\"'),
                     'f': f,
                     'rg' : rg}

            out += """<tr>
                       <td class="searchresultsboxbody" style="text-align: right;">
                        %(nbhits)s
                       </td>
                       <td class="searchresultsboxbody" width="15">
                        &nbsp;
                       </td>
                       <td class="searchresultsboxbody" style="text-align: left;">
                        %(link)s
                       </td>
                      </tr>""" % {'nbhits': nbhits,
                                  'link': create_html_link(self.build_search_url(query),
                                                           {}, cgi.escape(phrase))}

        elif len(browsed_phrases_in_colls) > 1:
            # first display what was found but the last one:
            for phrase, nbhits in browsed_phrases_in_colls[:-1]:
                query = {'c': colls,
                         'ln': ln,
                         'p': '"%s"' % phrase.replace('"', '\\"'),
                         'f': f,
                         'rg' : rg}

                out += """<tr>
                           <td class="searchresultsboxbody" style="text-align: right;">
                            %(nbhits)s
                           </td>
                           <td class="searchresultsboxbody" width="15">
                            &nbsp;
                           </td>
                           <td class="searchresultsboxbody" style="text-align: left;">
                            %(link)s
                           </td>
                          </tr>""" % {'nbhits' : nbhits,
                                      'link': create_html_link(self.build_search_url(query),
                                                               {},
                                                               cgi.escape(phrase))}

            # now display last hit as "previous term":
            phrase, nbhits = browsed_phrases_in_colls[0]
            query_previous = {'c': colls,
                     'ln': ln,
                     'p': '"%s"' % phrase.replace('"', '\\"'),
                     'f': f,
                     'rg' : rg}

            # now display last hit as "next term":
            phrase, nbhits = browsed_phrases_in_colls[-1]
            query_next = {'c': colls,
                     'ln': ln,
                     'p': '"%s"' % phrase.replace('"', '\\"'),
                     'f': f,
                     'rg' : rg}

            out += """<tr><td colspan="2" class="normal">
                            &nbsp;
                          </td>
                          <td class="normal">
                            %(link_previous)s
                            <img src="%(siteurl)s/img/sp.gif" alt="" border="0" />
                            <img src="%(siteurl)s/img/sn.gif" alt="" border="0" />
                            %(link_next)s
                          </td>
                      </tr>""" % {'link_previous': create_html_link(self.build_search_url(query_previous, action='browse'), {}, _("Previous")),
                      'link_next': create_html_link(self.build_search_url(query_next, action='browse'),
                                                           {}, _("next")),
                                  'siteurl' : CFG_BASE_URL}
        out += """</tbody>
            </table>"""
        return out

    def tmpl_search_box(self, ln, aas, cc, cc_intl, ot, sp,
                        action, fieldslist, f1, f2, f3, m1, m2, m3,
                        p1, p2, p3, op1, op2, rm, p, f, coll_selects,
                        d1y, d2y, d1m, d2m, d1d, d2d, dt, sort_fields,
                        sf, so, ranks, sc, rg, formats, of, pl, jrec, ec,
                        show_colls=True, show_title=True):

        """
          Displays the *Nearest search terms* box

        Parameters:

          - 'ln' *string* - The language to display

          - 'aas' *bool* - Should we display an advanced search box? -1 -> 1, from simpler to more advanced

          - 'cc_intl' *string* - the i18nized current collection name, used for display

          - 'cc' *string* - the internal current collection name

          - 'ot', 'sp' *string* - hidden values

          - 'action' *string* - the action demanded by the user

          - 'fieldslist' *list* - the list of all fields available, for use in select within boxes in advanced search

          - 'p, f, f1, f2, f3, m1, m2, m3, p1, p2, p3, op1, op2, op3, rm' *strings* - the search parameters

          - 'coll_selects' *array* - a list of lists, each containing the collections selects to display

          - 'd1y, d2y, d1m, d2m, d1d, d2d' *int* - the search between dates

          - 'dt' *string* - the dates' types (creation dates, modification dates)

          - 'sort_fields' *array* - the select information for the sort fields

          - 'sf' *string* - the currently selected sort field

          - 'so' *string* - the currently selected sort order ("a" or "d")

          - 'ranks' *array* - ranking methods

          - 'rm' *string* - selected ranking method

          - 'sc' *string* - split by collection or not

          - 'rg' *string* - selected results/page

          - 'formats' *array* - available output formats

          - 'of' *string* - the selected output format

          - 'pl' *string* - `limit to' search pattern

          - show_colls *bool* - propose coll selection box?

          - show_title *bool* show cc_intl in page title?
        """

        # load the right message language
        _ = gettext_set_language(ln)


        # These are hidden fields the user does not manipulate
        # directly
        if aas == -1:
            argd = drop_default_urlargd({
                'ln': ln, 'aas': aas,
                'ot': ot, 'sp': sp, 'ec': ec,
                }, self.search_results_default_urlargd)
        else:
            argd = drop_default_urlargd({
                'cc': cc, 'ln': ln, 'aas': aas,
                'ot': ot, 'sp': sp, 'ec': ec,
                }, self.search_results_default_urlargd)

        out = ""
        if show_title:
            # display cc name if asked for
            out += '''
            <h1 class="headline">%(ccname)s</h1>''' % {'ccname' : cgi.escape(cc_intl), }

        out += '''
        <form name="search" action="%(siteurl)s/search" method="get">
        ''' % {'siteurl' : CFG_BASE_URL}

        # Only add non-default hidden values
        for field, value in argd.items():
            out += self.tmpl_input_hidden(field, value)

        leadingtext = _("Search")

        if action == 'browse':
            leadingtext = _("Browse")

        if aas == 1:
            # print Advanced Search form:

            # define search box elements:
            out += '''
            <table class="searchbox advancedsearch">
             <thead>
              <tr>
               <th colspan="3" class="searchboxheader">
                %(leading)s:
               </th>
              </tr>
             </thead>
             <tbody>
              <tr valign="top" style="white-space:nowrap;">
                <td class="searchboxbody">%(matchbox1)s
                  <input type="text" name="p1" size="%(sizepattern)d" value="%(p1)s" class="advancedsearchfield"/>
                </td>
                <td class="searchboxbody">%(searchwithin1)s</td>
                <td class="searchboxbody">%(andornot1)s</td>
              </tr>
              <tr valign="top">
                <td class="searchboxbody">%(matchbox2)s
                  <input type="text" name="p2" size="%(sizepattern)d" value="%(p2)s" class="advancedsearchfield"/>
                </td>
                <td class="searchboxbody">%(searchwithin2)s</td>
                <td class="searchboxbody">%(andornot2)s</td>
              </tr>
              <tr valign="top">
                <td class="searchboxbody">%(matchbox3)s
                  <input type="text" name="p3" size="%(sizepattern)d" value="%(p3)s" class="advancedsearchfield"/>
                </td>
                <td class="searchboxbody">%(searchwithin3)s</td>
                <td class="searchboxbody"  style="white-space:nowrap;">
                  <input class="formbutton" type="submit" name="action_search" value="%(search)s" />
                  <input class="formbutton" type="submit" name="action_browse" value="%(browse)s" />&nbsp;
                </td>
              </tr>
              <tr valign="bottom">
                <td colspan="3" align="right" class="searchboxbody">
                  <small>
                    <a href="%(siteurl)s/help/search-tips%(langlink)s">%(search_tips)s</a> ::
                    %(simple_search)s
                  </small>
                </td>
              </tr>
             </tbody>
            </table>
            ''' % {
                'simple_search': create_html_link(self.build_search_url(p=p1, f=f1, rm=rm, cc=cc, ln=ln, jrec=jrec, rg=rg),
                                                  {}, _("Simple Search")),

                'leading' : leadingtext,
                'sizepattern' : CFG_WEBSEARCH_ADVANCEDSEARCH_PATTERN_BOX_WIDTH,
                'matchbox1' : self.tmpl_matchtype_box('m1', m1, ln=ln),
                'p1' : cgi.escape(p1, 1),
                'searchwithin1' : self.tmpl_searchwithin_select(
                                  ln=ln,
                                  fieldname='f1',
                                  selected=f1,
                                  values=self._add_mark_to_field(value=f1, fields=fieldslist, ln=ln)
                                ),
              'andornot1' : self.tmpl_andornot_box(
                                  name='op1',
                                  value=op1,
                                  ln=ln
                                ),
              'matchbox2' : self.tmpl_matchtype_box('m2', m2, ln=ln),
              'p2' : cgi.escape(p2, 1),
              'searchwithin2' : self.tmpl_searchwithin_select(
                                  ln=ln,
                                  fieldname='f2',
                                  selected=f2,
                                  values=self._add_mark_to_field(value=f2, fields=fieldslist, ln=ln)
                                ),
              'andornot2' : self.tmpl_andornot_box(
                                  name='op2',
                                  value=op2,
                                  ln=ln
                                ),
              'matchbox3' : self.tmpl_matchtype_box('m3', m3, ln=ln),
              'p3' : cgi.escape(p3, 1),
              'searchwithin3' : self.tmpl_searchwithin_select(
                                  ln=ln,
                                  fieldname='f3',
                                  selected=f3,
                                  values=self._add_mark_to_field(value=f3, fields=fieldslist, ln=ln)
                                ),
              'search' : _("Search"),
              'browse' : _("Browse"),
              'siteurl' : CFG_BASE_URL,
              'ln' : ln,
              'langlink': '?ln=' + ln,
              'search_tips': _("Search Tips")
            }
        elif aas == 0:
            # print Simple Search form:
            out += '''
            <table class="searchbox simplesearch">
             <thead>
              <tr>
               <th colspan="3" class="searchboxheader">
                %(leading)s:
               </th>
              </tr>
             </thead>
             <tbody>
              <tr valign="top">
                <td class="searchboxbody"><input type="text" name="p" size="%(sizepattern)d" value="%(p)s" class="simplesearchfield"/></td>
                <td class="searchboxbody">%(searchwithin)s</td>
                <td class="searchboxbody">
                  <input class="formbutton" type="submit" name="action_search" value="%(search)s" />
                  <input class="formbutton" type="submit" name="action_browse" value="%(browse)s" />&nbsp;
                </td>
              </tr>
              <tr valign="bottom">
                <td colspan="3" align="right" class="searchboxbody">
                  <small>
                    <a href="%(siteurl)s/help/search-tips%(langlink)s">%(search_tips)s</a> ::
                    %(advanced_search)s
                  </small>
                </td>
              </tr>
             </tbody>
            </table>
            ''' % {
              'advanced_search': create_html_link(self.build_search_url(p1=p,
                                                                        f1=f,
                                                                        rm=rm,
                                                                        aas=max(CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES),
                                                                        cc=cc,
                                                                        jrec=jrec,
                                                                        ln=ln,
                                                                        rg=rg),
                                                  {}, _("Advanced Search")),

              'leading' : leadingtext,
              'sizepattern' : CFG_WEBSEARCH_SIMPLESEARCH_PATTERN_BOX_WIDTH,
              'p' : cgi.escape(p, 1),
              'searchwithin' : self.tmpl_searchwithin_select(
                                  ln=ln,
                                  fieldname='f',
                                  selected=f,
                                  values=self._add_mark_to_field(value=f, fields=fieldslist, ln=ln)
                                ),
              'search' : _("Search"),
              'browse' : _("Browse"),
              'siteurl' : CFG_BASE_URL,
              'ln' : ln,
              'langlink': '?ln=' + ln,
              'search_tips': _("Search Tips")
            }
        else:
            # EXPERIMENTAL
            # print light search form:
            search_in = ''
            if cc_intl != CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME):
                search_in = '''
            <input type="radio" name="cc" value="%(collection_id)s" id="searchCollection" checked="checked"/>
            <label for="searchCollection">%(search_in_collection_name)s</label>
            <input type="radio" name="cc" value="%(root_collection_name)s" id="searchEverywhere" />
            <label for="searchEverywhere">%(search_everywhere)s</label>
            ''' % {'search_in_collection_name': _("Search in %(x_collection_name)s") % \
                  {'x_collection_name': cgi.escape(cc_intl)},
                  'collection_id': cc,
                  'root_collection_name': CFG_SITE_NAME,
                  'search_everywhere': _("Search everywhere")}
            out += '''
            <table class="searchbox lightsearch">
              <tr valign="top">
                <td class="searchboxbody"><input type="text" name="p" size="%(sizepattern)d" value="%(p)s" class="lightsearchfield"/></td>
                <td class="searchboxbody">
                  <input class="formbutton" type="submit" name="action_search" value="%(search)s" />
                </td>
                <td class="searchboxbody" align="left" rowspan="2" valign="top">
                  <small><small>
                  <a href="%(siteurl)s/help/search-tips%(langlink)s">%(search_tips)s</a><br/>
                  %(advanced_search)s
                </td>
              </tr>
            </table>
            <small>%(search_in)s</small>
            ''' % {
              'sizepattern' : CFG_WEBSEARCH_LIGHTSEARCH_PATTERN_BOX_WIDTH,
              'advanced_search': create_html_link(self.build_search_url(p1=p,
                                                                        f1=f,
                                                                        rm=rm,
                                                                        aas=max(CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES),
                                                                        cc=cc,
                                                                        jrec=jrec,
                                                                        ln=ln,
                                                                        rg=rg),
                                                  {}, _("Advanced Search")),

              'leading' : leadingtext,
              'p' : cgi.escape(p, 1),
              'searchwithin' : self.tmpl_searchwithin_select(
                                  ln=ln,
                                  fieldname='f',
                                  selected=f,
                                  values=self._add_mark_to_field(value=f, fields=fieldslist, ln=ln)
                                ),
              'search' : _("Search"),
              'browse' : _("Browse"),
              'siteurl' : CFG_BASE_URL,
              'ln' : ln,
              'langlink': '?ln=' + ln,
              'search_tips': _("Search Tips"),
              'search_in': search_in
            }
        ## secondly, print Collection(s) box:

        if show_colls and aas > -1:
            # display collections only if there is more than one
            selects = ''
            for sel in coll_selects:
                selects += self.tmpl_select(fieldname='c', values=sel)

            out += """
                <table class="searchbox">
                 <thead>
                  <tr>
                   <th colspan="3" class="searchboxheader">
                    %(leading)s %(msg_coll)s:
                   </th>
                  </tr>
                 </thead>
                 <tbody>
                  <tr valign="bottom">
                   <td valign="top" class="searchboxbody">
                     %(colls)s
                   </td>
                  </tr>
                 </tbody>
                </table>
                 """ % {
                   'leading' : leadingtext,
                   'msg_coll' : _("collections"),
                   'colls' : selects,
                 }

        ## thirdly, print search limits, if applicable:
        if action != _("Browse") and pl:
            out += """<table class="searchbox">
                       <thead>
                        <tr>
                          <th class="searchboxheader">
                            %(limitto)s
                          </th>
                        </tr>
                       </thead>
                       <tbody>
                        <tr valign="bottom">
                          <td class="searchboxbody">
                           <input type="text" name="pl" size="%(sizepattern)d" value="%(pl)s" />
                          </td>
                        </tr>
                       </tbody>
                      </table>""" % {
                        'limitto' : _("Limit to:"),
                        'sizepattern' : CFG_WEBSEARCH_ADVANCEDSEARCH_PATTERN_BOX_WIDTH,
                        'pl' : cgi.escape(pl, 1),
                      }

        ## fourthly, print from/until date boxen, if applicable:
        if action == _("Browse") or (d1y == 0 and d1m == 0 and d1d == 0 and d2y == 0 and d2m == 0 and d2d == 0):
            pass # do not need it
        else:
            cell_6_a = self.tmpl_inputdatetype(dt, ln) + self.tmpl_inputdate("d1", ln, d1y, d1m, d1d)
            cell_6_b = self.tmpl_inputdate("d2", ln, d2y, d2m, d2d)
            out += """<table class="searchbox">
                       <thead>
                        <tr>
                          <th class="searchboxheader">
                            %(added)s
                          </th>
                          <th class="searchboxheader">
                            %(until)s
                          </th>
                        </tr>
                       </thead>
                       <tbody>
                        <tr valign="bottom">
                          <td class="searchboxbody">%(added_or_modified)s %(date1)s</td>
                          <td class="searchboxbody">%(date2)s</td>
                        </tr>
                       </tbody>
                      </table>""" % {
                        'added' : _("Added/modified since:"),
                        'until' : _("until:"),
                        'added_or_modified': self.tmpl_inputdatetype(dt, ln),
                        'date1' : self.tmpl_inputdate("d1", ln, d1y, d1m, d1d),
                        'date2' : self.tmpl_inputdate("d2", ln, d2y, d2m, d2d),
                      }

        ## fifthly, print Display results box, including sort/rank, formats, etc:
        if action != _("Browse") and aas > -1:

            rgs = []
            for i in [10, 25, 50, 100, 250, 500]:
                if i <= CFG_WEBSEARCH_MAX_RECORDS_IN_GROUPS:
                    rgs.append({ 'value' : i, 'text' : "%d %s" % (i, _("results"))})
            # enrich sort fields list if we are sorting by some MARC tag:
            sort_fields = self._add_mark_to_field(value=sf, fields=sort_fields, ln=ln)
            # create sort by HTML box:
            out += """<table class="searchbox">
                 <thead>
                  <tr>
                   <th class="searchboxheader">
                    %(sort_by)s
                   </th>
                   <th class="searchboxheader">
                    %(display_res)s
                   </th>
                   <th class="searchboxheader">
                    %(out_format)s
                   </th>
                  </tr>
                 </thead>
                 <tbody>
                  <tr valign="bottom">
                   <td class="searchboxbody">
                     %(select_sf)s %(select_so)s %(select_rm)s
                   </td>
                   <td class="searchboxbody">
                     %(select_rg)s %(select_sc)s
                   </td>
                   <td class="searchboxbody">%(select_of)s</td>
                  </tr>
                 </tbody>
                </table>""" % {
                  'sort_by' : _("Sort by:"),
                  'display_res' : _("Display results:"),
                  'out_format' : _("Output format:"),
                  'select_sf' : self.tmpl_select(fieldname='sf', values=sort_fields, selected=sf, css_class='address'),
                  'select_so' : self.tmpl_select(fieldname='so', values=[{
                                    'value' : 'a',
                                    'text' : _("asc.")
                                  }, {
                                    'value' : 'd',
                                    'text' : _("desc.")
                                  }], selected=so, css_class='address'),
                  'select_rm' : self.tmpl_select(fieldname='rm', values=ranks, selected=rm, css_class='address'),
                  'select_rg' : self.tmpl_select(fieldname='rg', values=rgs, selected=rg, css_class='address'),
                  'select_sc' : self.tmpl_select(fieldname='sc', values=[{
                                    'value' : 0,
                                    'text' : _("single list")
                                  }, {
                                    'value' : 1,
                                    'text' : _("split by collection")
                                  }], selected=sc, css_class='address'),
                  'select_of' : self.tmpl_select(
                                  fieldname='of',
                                  selected=of,
                                  values=self._add_mark_to_field(value=of, fields=formats, chars=3, ln=ln),
                                  css_class='address'),
                }

        ## last but not least, print end of search box:
        out += """</form>"""
        return out

    def tmpl_input_hidden(self, name, value):
        "Produces the HTML code for a hidden field "
        if isinstance(value, list):
            list_input = [self.tmpl_input_hidden(name, val) for val in value]
            return "\n".join(list_input)

        # # Treat `as', `aas' arguments specially:
        if name == 'aas':
            name = 'as'

        return """<input type="hidden" name="%(name)s" value="%(value)s" />""" % {
                 'name' : cgi.escape(str(name), 1),
                 'value' : cgi.escape(str(value), 1),
               }

    def _add_mark_to_field(self, value, fields, ln, chars=1):
        """Adds the current value as a MARC tag in the fields array
        Useful for advanced search"""

        # load the right message language
        _ = gettext_set_language(ln)

        out = fields
        if value and str(value[0:chars]).isdigit():
            out.append({'value' : value,
                        'text' : str(value) + " " + _("MARC tag")
                        })
        return out

    def tmpl_search_pagestart(self, ln) :
        "page start for search page. Will display after the page header"
        return """<div class="pagebody"><div class="pagebodystripemiddle">"""

    def tmpl_search_pageend(self, ln) :
        "page end for search page. Will display just before the page footer"
        return """</div></div>"""

    def tmpl_print_search_info(self, ln, middle_only,
                               collection, collection_name, collection_id,
                               aas, sf, so, rm, rg, nb_found, of, ot, p, f, f1,
                               f2, f3, m1, m2, m3, op1, op2, p1, p2,
                               p3, d1y, d1m, d1d, d2y, d2m, d2d, dt,
                               all_fieldcodes, cpu_time, pl_in_url,
                               jrec, sc, sp):

        """Prints stripe with the information on 'collection' and 'nb_found' results and CPU time.
           Also, prints navigation links (beg/next/prev/end) inside the results set.
           If middle_only is set to 1, it will only print the middle box information (beg/netx/prev/end/etc) links.
           This is suitable for displaying navigation links at the bottom of the search results page.

        Parameters:

          - 'ln' *string* - The language to display

          - 'middle_only' *bool* - Only display parts of the interface

          - 'collection' *string* - the collection name

          - 'collection_name' *string* - the i18nized current collection name

          - 'aas' *bool* - if we display the advanced search interface

          - 'sf' *string* - the currently selected sort format

          - 'so' *string* - the currently selected sort order ("a" or "d")

          - 'rm' *string* - selected ranking method

          - 'rg' *int* - selected results/page

          - 'nb_found' *int* - number of results found

          - 'of' *string* - the selected output format

          - 'ot' *string* - hidden values

          - 'p' *string* - Current search words

          - 'f' *string* - the fields in which the search was done

          - 'f1, f2, f3, m1, m2, m3, p1, p2, p3, op1, op2' *strings* - the search parameters

          - 'jrec' *int* - number of first record on this page

          - 'd1y, d2y, d1m, d2m, d1d, d2d' *int* - the search between dates

          - 'dt' *string* the dates' type (creation date, modification date)

          - 'all_fieldcodes' *array* - all the available fields

          - 'cpu_time' *float* - the time of the query in seconds

        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        # left table cells: print collection name
        if not middle_only:
            out += '''
                  <a name="%(collection_id)s"></a>
                  <form action="%(siteurl)s/search" method="get">
                  <table class="searchresultsbox"><tr><td class="searchresultsboxheader" align="left">
                  <strong><big>%(collection_link)s</big></strong></td>
                  ''' % {
                    'collection_id': collection_id,
                    'siteurl' : CFG_BASE_URL,
                    'collection_link': create_html_link(self.build_search_interface_url(c=collection, aas=aas, ln=ln),
                                                        {}, cgi.escape(collection_name))
                  }
        else:
            out += """
                  <div style="clear:both"></div>
                  <form action="%(siteurl)s/search" method="get"><div align="center">
                  """ % { 'siteurl' : CFG_BASE_URL }

        # middle table cell: print beg/next/prev/end arrows:
        if not middle_only:
            out += """<td class="searchresultsboxheader" align="center">
                      %(recs_found)s &nbsp;""" % {
                     'recs_found' : _("%s records found") % ('<strong>' + self.tmpl_nice_number(nb_found, ln) + '</strong>')
                   }
        else:
            out += "<small>"
            if nb_found > rg:
                out += "" + cgi.escape(collection_name) + " : " + _("%s records found") % ('<strong>' + self.tmpl_nice_number(nb_found, ln) + '</strong>') + " &nbsp; "

        if nb_found > rg: # navig.arrows are needed, since we have many hits

            query = {'p': p, 'f': f,
                     'cc': collection,
                     'sf': sf, 'so': so,
                     'sp': sp, 'rm': rm,
                     'of': of, 'ot': ot,
                     'aas': aas, 'ln': ln,
                     'p1': p1, 'p2': p2, 'p3': p3,
                     'f1': f1, 'f2': f2, 'f3': f3,
                     'm1': m1, 'm2': m2, 'm3': m3,
                     'op1': op1, 'op2': op2,
                     'sc': 0,
                     'd1y': d1y, 'd1m': d1m, 'd1d': d1d,
                     'd2y': d2y, 'd2m': d2m, 'd2d': d2d,
                     'dt': dt,
                }

            # @todo here
            def img(gif, txt):
                return '<img src="%(siteurl)s/img/%(gif)s.gif" alt="%(txt)s" border="0" />' % {
                    'txt': txt, 'gif': gif, 'siteurl': CFG_BASE_URL}

            if jrec - rg > 1:
                out += create_html_link(self.build_search_url(query, jrec=1, rg=rg),
                                        {}, img('sb', _("begin")),
                                        {'class': 'img'})

            if jrec > 1:
                out += create_html_link(self.build_search_url(query, jrec=max(jrec - rg, 1), rg=rg),
                                        {}, img('sp', _("previous")),
                                        {'class': 'img'})

            if jrec + rg - 1 < nb_found:
                out += "%d - %d" % (jrec, jrec + rg - 1)
            else:
                out += "%d - %d" % (jrec, nb_found)

            if nb_found >= jrec + rg:
                out += create_html_link(self.build_search_url(query,
                                                              jrec=jrec + rg,
                                                              rg=rg),
                                        {}, img('sn', _("next")),
                                        {'class':'img'})

            if nb_found >= jrec + rg + rg:
                out += create_html_link(self.build_search_url(query,
                                                            jrec=nb_found - rg + 1,
                                                            rg=rg),
                                        {}, img('se', _("end")),
                                        {'class': 'img'})


            # still in the navigation part
            cc = collection
            sc = 0
            for var in ['p', 'cc', 'f', 'sf', 'so', 'of', 'rg', 'aas', 'ln', 'p1', 'p2', 'p3', 'f1', 'f2', 'f3', 'm1', 'm2', 'm3', 'op1', 'op2', 'sc', 'd1y', 'd1m', 'd1d', 'd2y', 'd2m', 'd2d', 'dt']:
                out += self.tmpl_input_hidden(name=var, value=vars()[var])
            for var in ['ot', 'sp', 'rm']:
                if vars()[var]:
                    out += self.tmpl_input_hidden(name=var, value=vars()[var])
            if pl_in_url:
                fieldargs = cgi.parse_qs(pl_in_url)
                for fieldcode in all_fieldcodes:
                    # get_fieldcodes():
                    if fieldargs.has_key(fieldcode):
                        for val in fieldargs[fieldcode]:
                            out += self.tmpl_input_hidden(name=fieldcode, value=val)
            out += """&nbsp; %(jump)s <input type="text" name="jrec" size="4" value="%(jrec)d" />""" % {
                     'jump' : _("jump to record:"),
                     'jrec' : jrec,
                   }

        if not middle_only:
            out += "</td>"
        else:
            out += "</small>"

        # right table cell: cpu time info
        if not middle_only:
            if cpu_time > -1:
                out += """<td class="searchresultsboxheader" align="right"><small>%(time)s</small>&nbsp;</td>""" % {
                         'time' : _("Search took %s seconds.") % ('%.2f' % cpu_time),
                       }
            out += "</tr></table>"
        else:
            out += "</div>"
        out += "</form>"
        return out

    def tmpl_print_hosted_search_info(self, ln, middle_only,
                               collection, collection_name, collection_id,
                               aas, sf, so, rm, rg, nb_found, of, ot, p, f, f1,
                               f2, f3, m1, m2, m3, op1, op2, p1, p2,
                               p3, d1y, d1m, d1d, d2y, d2m, d2d, dt,
                               all_fieldcodes, cpu_time, pl_in_url,
                               jrec, sc, sp):

        """Prints stripe with the information on 'collection' and 'nb_found' results and CPU time.
           Also, prints navigation links (beg/next/prev/end) inside the results set.
           If middle_only is set to 1, it will only print the middle box information (beg/netx/prev/end/etc) links.
           This is suitable for displaying navigation links at the bottom of the search results page.

        Parameters:

          - 'ln' *string* - The language to display

          - 'middle_only' *bool* - Only display parts of the interface

          - 'collection' *string* - the collection name

          - 'collection_name' *string* - the i18nized current collection name

          - 'aas' *bool* - if we display the advanced search interface

          - 'sf' *string* - the currently selected sort format

          - 'so' *string* - the currently selected sort order ("a" or "d")

          - 'rm' *string* - selected ranking method

          - 'rg' *int* - selected results/page

          - 'nb_found' *int* - number of results found

          - 'of' *string* - the selected output format

          - 'ot' *string* - hidden values

          - 'p' *string* - Current search words

          - 'f' *string* - the fields in which the search was done

          - 'f1, f2, f3, m1, m2, m3, p1, p2, p3, op1, op2' *strings* - the search parameters

          - 'jrec' *int* - number of first record on this page

          - 'd1y, d2y, d1m, d2m, d1d, d2d' *int* - the search between dates

          - 'dt' *string* the dates' type (creation date, modification date)

          - 'all_fieldcodes' *array* - all the available fields

          - 'cpu_time' *float* - the time of the query in seconds

        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        # left table cells: print collection name
        if not middle_only:
            out += '''
                  <a name="%(collection_id)s"></a>
                  <form action="%(siteurl)s/search" method="get">
                  <table class="searchresultsbox"><tr><td class="searchresultsboxheader" align="left">
                  <strong><big>%(collection_link)s</big></strong></td>
                  ''' % {
                    'collection_id': collection_id,
                    'siteurl' : CFG_BASE_URL,
                    'collection_link': create_html_link(self.build_search_interface_url(c=collection, aas=aas, ln=ln),
                                                        {}, cgi.escape(collection_name))
                  }

        else:
            out += """
                  <form action="%(siteurl)s/search" method="get"><div align="center">
                  """ % { 'siteurl' : CFG_BASE_URL }

        # middle table cell: print beg/next/prev/end arrows:
        if not middle_only:
            # in case we have a hosted collection that timed out do not print its number of records, as it is yet unknown
            if nb_found != -963:
                out += """<td class="searchresultsboxheader" align="center">
                          %(recs_found)s &nbsp;""" % {
                         'recs_found' : _("%s records found") % ('<strong>' + self.tmpl_nice_number(nb_found, ln) + '</strong>')
                       }
            #elif nb_found = -963:
            #    out += """<td class="searchresultsboxheader" align="center">
            #              %(recs_found)s &nbsp;""" % {
            #             'recs_found' : _("%s records found") % ('<strong>' + self.tmpl_nice_number(nb_found, ln) + '</strong>')
            #           }
        else:
            out += "<small>"
            # we do not care about timed out hosted collections here, because the bumber of records found will never be bigger
            # than rg anyway, since it's negative
            if nb_found > rg:
                out += "" + cgi.escape(collection_name) + " : " + _("%s records found") % ('<strong>' + self.tmpl_nice_number(nb_found, ln) + '</strong>') + " &nbsp; "

        if nb_found > rg: # navig.arrows are needed, since we have many hits

            query = {'p': p, 'f': f,
                     'cc': collection,
                     'sf': sf, 'so': so,
                     'sp': sp, 'rm': rm,
                     'of': of, 'ot': ot,
                     'aas': aas, 'ln': ln,
                     'p1': p1, 'p2': p2, 'p3': p3,
                     'f1': f1, 'f2': f2, 'f3': f3,
                     'm1': m1, 'm2': m2, 'm3': m3,
                     'op1': op1, 'op2': op2,
                     'sc': 0,
                     'd1y': d1y, 'd1m': d1m, 'd1d': d1d,
                     'd2y': d2y, 'd2m': d2m, 'd2d': d2d,
                     'dt': dt,
                }

            # @todo here
            def img(gif, txt):
                return '<img src="%(siteurl)s/img/%(gif)s.gif" alt="%(txt)s" border="0" />' % {
                    'txt': txt, 'gif': gif, 'siteurl': CFG_BASE_URL}

            if jrec - rg > 1:
                out += create_html_link(self.build_search_url(query, jrec=1, rg=rg),
                                        {}, img('sb', _("begin")),
                                        {'class': 'img'})

            if jrec > 1:
                out += create_html_link(self.build_search_url(query, jrec=max(jrec - rg, 1), rg=rg),
                                        {}, img('sp', _("previous")),
                                        {'class': 'img'})

            if jrec + rg - 1 < nb_found:
                out += "%d - %d" % (jrec, jrec + rg - 1)
            else:
                out += "%d - %d" % (jrec, nb_found)

            if nb_found >= jrec + rg:
                out += create_html_link(self.build_search_url(query,
                                                              jrec=jrec + rg,
                                                              rg=rg),
                                        {}, img('sn', _("next")),
                                        {'class':'img'})

            if nb_found >= jrec + rg + rg:
                out += create_html_link(self.build_search_url(query,
                                                            jrec=nb_found - rg + 1,
                                                            rg=rg),
                                        {}, img('se', _("end")),
                                        {'class': 'img'})


            # still in the navigation part
            cc = collection
            sc = 0
            for var in ['p', 'cc', 'f', 'sf', 'so', 'of', 'rg', 'aas', 'ln', 'p1', 'p2', 'p3', 'f1', 'f2', 'f3', 'm1', 'm2', 'm3', 'op1', 'op2', 'sc', 'd1y', 'd1m', 'd1d', 'd2y', 'd2m', 'd2d', 'dt']:
                out += self.tmpl_input_hidden(name=var, value=vars()[var])
            for var in ['ot', 'sp', 'rm']:
                if vars()[var]:
                    out += self.tmpl_input_hidden(name=var, value=vars()[var])
            if pl_in_url:
                fieldargs = cgi.parse_qs(pl_in_url)
                for fieldcode in all_fieldcodes:
                    # get_fieldcodes():
                    if fieldargs.has_key(fieldcode):
                        for val in fieldargs[fieldcode]:
                            out += self.tmpl_input_hidden(name=fieldcode, value=val)
            out += """&nbsp; %(jump)s <input type="text" name="jrec" size="4" value="%(jrec)d" />""" % {
                     'jump' : _("jump to record:"),
                     'jrec' : jrec,
                   }

        if not middle_only:
            out += "</td>"
        else:
            out += "</small>"

        # right table cell: cpu time info
        if not middle_only:
            if cpu_time > -1:
                out += """<td class="searchresultsboxheader" align="right"><small>%(time)s</small>&nbsp;</td>""" % {
                         'time' : _("Search took %s seconds.") % ('%.2f' % cpu_time),
                       }
            out += "</tr></table>"
        else:
            out += "</div>"
        out += "</form>"
        return out

    def tmpl_nice_number(self, number, ln=CFG_SITE_LANG, thousands_separator=',', max_ndigits_after_dot=None):
        """
        Return nicely printed number NUMBER in language LN using
        given THOUSANDS_SEPARATOR character.
        If max_ndigits_after_dot is specified and the number is float, the
        number is rounded by taking in consideration up to max_ndigits_after_dot
        digit after the dot.

        This version does not pay attention to locale.  See
        tmpl_nice_number_via_locale().
        """
        if type(number) is float:
            if max_ndigits_after_dot is not None:
                number = round(number, max_ndigits_after_dot)
            int_part, frac_part = str(number).split('.')
            return '%s.%s' % (self.tmpl_nice_number(int(int_part), ln, thousands_separator), frac_part)
        else:
            chars_in = list(str(number))
            number = len(chars_in)
            chars_out = []
            for i in range(0, number):
                if i % 3 == 0 and i != 0:
                    chars_out.append(thousands_separator)
                chars_out.append(chars_in[number - i - 1])
            chars_out.reverse()
            return ''.join(chars_out)

    def tmpl_nice_number_via_locale(self, number, ln=CFG_SITE_LANG):
        """
        Return nicely printed number NUM in language LN using the locale.
        See also version tmpl_nice_number().
        """
        if number is None:
            return None
        # Temporarily switch the numeric locale to the requested one, and format the number
        # In case the system has no locale definition, use the vanilla form
        ol = locale.getlocale(locale.LC_NUMERIC)
        try:
            locale.setlocale(locale.LC_NUMERIC, self.tmpl_localemap.get(ln, self.tmpl_default_locale))
        except locale.Error:
            return str(number)
        try:
            number = locale.format('%d', number, True)
        except TypeError:
            return str(number)
        locale.setlocale(locale.LC_NUMERIC, ol)
        return number

    def tmpl_record_format_htmlbrief_header(self, ln):
        """Returns the header of the search results list when output
        is html brief. Note that this function is called for each collection
        results when 'split by collection' is enabled.

        See also: tmpl_record_format_htmlbrief_footer,
                  tmpl_record_format_htmlbrief_body

        Parameters:

          - 'ln' *string* - The language to display

        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
              <form action="%(siteurl)s/yourbaskets/add" method="post">
              <table>
              """ % {
                'siteurl' : CFG_BASE_URL,
              }

        return out

    def tmpl_record_format_htmlbrief_footer(self, ln, display_add_to_basket=True):
        """Returns the footer of the search results list when output
        is html brief. Note that this function is called for each collection
        results when 'split by collection' is enabled.

        See also: tmpl_record_format_htmlbrief_header(..),
                  tmpl_record_format_htmlbrief_body(..)

        Parameters:

          - 'ln' *string* - The language to display
          - 'display_add_to_basket' *bool* - whether to display Add-to-basket button
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """</table>
               <br />
               <input type="hidden" name="colid" value="0" />
               %(add_to_basket)s
               </form>""" % {
               'add_to_basket': display_add_to_basket and """<input class="formbutton" type="submit" name="action" value="%s" />""" % _("Add to basket") or "",
                 }

        return out

    def tmpl_record_format_htmlbrief_body(self, ln, recid,
                                          row_number, relevance,
                                          record, relevances_prologue,
                                          relevances_epilogue,
                                          display_add_to_basket=True):
        """Returns the html brief format of one record. Used in the
        search results list for each record.

        See also: tmpl_record_format_htmlbrief_header(..),
                  tmpl_record_format_htmlbrief_footer(..)

        Parameters:

          - 'ln' *string* - The language to display

          - 'row_number' *int* - The position of this record in the list

          - 'recid' *int* - The recID

          - 'relevance' *string* - The relevance of the record

          - 'record' *string* - The formatted record

          - 'relevances_prologue' *string* - HTML code to prepend the relevance indicator

          - 'relevances_epilogue' *string* - HTML code to append to the relevance indicator (used mostly for formatting)

        """

        # load the right message language
        _ = gettext_set_language(ln)

        checkbox_for_baskets = """<input name="recid" type="checkbox" value="%(recid)s" />""" % \
                               {'recid': recid, }
        if not display_add_to_basket:
            checkbox_for_baskets = ''
        out = """
                <tr><td valign="top" align="right" style="white-space: nowrap;">
                    %(checkbox_for_baskets)s
                    <abbr class="unapi-id" title="%(recid)s"></abbr>

                %(number)s.
               """ % {'recid': recid,
                      'number': row_number,
                      'checkbox_for_baskets': checkbox_for_baskets}
        if relevance:
            out += """<br /><div class="rankscoreinfo"><a title="rank score">%(prologue)s%(relevance)s%(epilogue)s</a></div>""" % {
                'prologue' : relevances_prologue,
                'epilogue' : relevances_epilogue,
                'relevance' : relevance
                }
        out += """</td><td valign="top">%s</td></tr>""" % record

        return out

    def tmpl_print_results_overview(self, ln, results_final_nb_total, cpu_time, results_final_nb, colls, ec, hosted_colls_potential_results_p=False):
        """Prints results overview box with links to particular collections below.

        Parameters:

          - 'ln' *string* - The language to display

          - 'results_final_nb_total' *int* - The total number of hits for the query

          - 'colls' *array* - The collections with hits, in the format:

          - 'coll[code]' *string* - The code of the collection (canonical name)

          - 'coll[name]' *string* - The display name of the collection

          - 'results_final_nb' *array* - The number of hits, indexed by the collection codes:

          - 'cpu_time' *string* - The time the query took

          - 'url_args' *string* - The rest of the search query

          - 'ec' *array* - selected external collections

          - 'hosted_colls_potential_results_p' *boolean* - check if there are any hosted collections searches
                                                    that timed out during the pre-search
        """

        if len(colls) == 1 and not ec:
            # if one collection only and no external collections, print nothing:
            return ""

        # load the right message language
        _ = gettext_set_language(ln)

        # first find total number of hits:
        # if there were no hosted collections that timed out during the pre-search print out the exact number of records found
        if not hosted_colls_potential_results_p:
            out = """<table class="searchresultsbox">
                    <thead><tr><th class="searchresultsboxheader">%(founds)s</th></tr></thead>
                    <tbody><tr><td class="searchresultsboxbody"> """ % {
                    'founds' : _("%(x_fmt_open)sResults overview:%(x_fmt_close)s Found %(x_nb_records)s records in %(x_nb_seconds)s seconds.") % \
                    {'x_fmt_open': '<strong>',
                     'x_fmt_close': '</strong>',
                     'x_nb_records': '<strong>' + self.tmpl_nice_number(results_final_nb_total, ln) + '</strong>',
                     'x_nb_seconds': '%.2f' % cpu_time}
                  }
        # if there were (only) hosted_collections that timed out during the pre-search print out a fuzzier message
        else:
            if results_final_nb_total == 0:
                out = """<table class="searchresultsbox">
                        <thead><tr><th class="searchresultsboxheader">%(founds)s</th></tr></thead>
                        <tbody><tr><td class="searchresultsboxbody"> """ % {
                        'founds' : _("%(x_fmt_open)sResults overview%(x_fmt_close)s") % \
                        {'x_fmt_open': '<strong>',
                         'x_fmt_close': '</strong>'}
                      }
            elif results_final_nb_total > 0:
                out = """<table class="searchresultsbox">
                        <thead><tr><th class="searchresultsboxheader">%(founds)s</th></tr></thead>
                        <tbody><tr><td class="searchresultsboxbody"> """ % {
                        'founds' : _("%(x_fmt_open)sResults overview:%(x_fmt_close)s Found at least %(x_nb_records)s records in %(x_nb_seconds)s seconds.") % \
                        {'x_fmt_open': '<strong>',
                         'x_fmt_close': '</strong>',
                         'x_nb_records': '<strong>' + self.tmpl_nice_number(results_final_nb_total, ln) + '</strong>',
                         'x_nb_seconds': '%.2f' % cpu_time}
                      }
        # then print hits per collection:
        out += """<script type="text/javascript">
            $(document).ready(function() {
                $('a.morecolls').click(function() {
                    $('.morecollslist').show();
                    $(this).hide();
                    $('.lesscolls').show();
                    return false;
                });
                $('a.lesscolls').click(function() {
                    $('.morecollslist').hide();
                    $(this).hide();
                    $('.morecolls').show();
                    return false;
                });
            });
            </script>"""
        count = 0
        for coll in colls:
            if results_final_nb.has_key(coll['code']) and results_final_nb[coll['code']] > 0:
                count += 1
                out += """
                      <span %(collclass)s><strong><a href="#%(coll)s">%(coll_name)s</a></strong>, <a href="#%(coll)s">%(number)s</a><br /></span>""" % \
                                      {'collclass' : count > CFG_WEBSEARCH_RESULTS_OVERVIEW_MAX_COLLS_TO_PRINT and 'class="morecollslist" style="display:none"' or '',
                                       'coll' : coll['id'],
                                       'coll_name' : cgi.escape(coll['name']),
                                       'number' : _("%s records found") % \
                                       ('<strong>' + self.tmpl_nice_number(results_final_nb[coll['code']], ln) + '</strong>')}
            # the following is used for hosted collections that have timed out,
            # i.e. for which we don't know the exact number of results yet.
            elif results_final_nb.has_key(coll['code']) and results_final_nb[coll['code']] == -963:
                count += 1
                out += """
                      <span %(collclass)s><strong><a href="#%(coll)s">%(coll_name)s</a></strong><br /></span>""" % \
                                      {'collclass' : count > CFG_WEBSEARCH_RESULTS_OVERVIEW_MAX_COLLS_TO_PRINT and 'class="morecollslist" style="display:none"' or '',
                                       'coll' : coll['id'],
                                       'coll_name' : cgi.escape(coll['name']),
                                       'number' : _("%s records found") % \
                                       ('<strong>' + self.tmpl_nice_number(results_final_nb[coll['code']], ln) + '</strong>')}
        if count > CFG_WEBSEARCH_RESULTS_OVERVIEW_MAX_COLLS_TO_PRINT:
            out += """<a class="lesscolls" style="display:none; color:red; font-size:small" href="#"><i>%s</i></a>""" % _("Show less collections")
            out += """<a class="morecolls" style="color:red; font-size:small" href="#"><i>%s</i></a>""" % _("Show all collections")

        out += "</td></tr></tbody></table>"
        return out

    def tmpl_print_hosted_results(self, url_and_engine, ln, of=None, req=None, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS, display_body=True, display_add_to_basket = True):
        """Print results of a given search engine.
        """

        if display_body:
            _ = gettext_set_language(ln)
            #url = url_and_engine[0]
            engine = url_and_engine[1]
            #name = _(engine.name)
            db_id = get_collection_id(engine.name)
            #base_url = engine.base_url

            out = ""

            results = engine.parser.parse_and_get_results(None, of=of, req=req, limit=limit, parseonly=True)

            if len(results) != 0:
                if of == 'hb':
                    out += """
                          <form action="%(siteurl)s/yourbaskets/add" method="post">
                          <input type="hidden" name="colid" value="%(col_db_id)s" />
                          <table>
                          """ % {
                            'siteurl' : CFG_BASE_URL,
                            'col_db_id' : db_id,
                          }
            else:
                if of == 'hb':
                    out += """
                          <table>
                          """

            for result in results:
                out += result.html.replace('>Detailed record<', '>External record<').replace('>Similar records<', '>Similar external records<')

            if len(results) != 0:
                if of == 'hb':
                    out += """</table>
                           <br />"""
                    if display_add_to_basket:
                        out += """<input class="formbutton" type="submit" name="action" value="%(basket)s" />
                    """ % {'basket' : _("Add to basket")}
                    out += """</form>"""
            else:
                if of == 'hb':
                    out += """
                          </table>
                          """

            # we have already checked if there are results or no, maybe the following if should be removed?
            if not results:
                if of.startswith("h"):
                    out = _('No results found...') + '<br />'

            return out
        else:
            return ""

    def tmpl_print_service_list_links(self, label, labels_and_urls, ln=CFG_SITE_URL):
        """
        Prints service results as list

        @param label: the label to display before the list of links
        @type label: string
        @param labels_and_urls: list of tuples (label, url), already translated, not escaped
        @type labels_and_urls: list(string, string)
        @param ln: language
        """
        # load the right message language
        _ = gettext_set_language(ln)


        out = '''
        <span class="searchservicelabel">%s</span> ''' % cgi.escape(label)

        out += """<script type="text/javascript">
            $(document).ready(function() {
                $('a.moreserviceitemslink').click(function() {
                    $('.moreserviceitemslist', $(this).parent()).show();
                    $(this).hide();
                    $('.lessserviceitemslink', $(this).parent()).show();
                    return false;
                });
                $('a.lessserviceitemslink').click(function() {
                    $('.moreserviceitemslist', $(this).parent()).hide();
                    $(this).hide();
                    $('.moreserviceitemslink', $(this).parent()).show();
                    return false;
                });
            });
            </script>"""
        count = 0
        for link_label, link_url in labels_and_urls:
            count += 1
            out += """<span %(itemclass)s>%(separator)s <a class="searchserviceitem" href="%(url)s">%(link_label)s</a></span>""" % \
                   {'itemclass' : count > CFG_WEBSEARCH_MAX_SEARCH_COLL_RESULTS_TO_PRINT and 'class="moreserviceitemslist" style="display:none"' or '',
                    'separator': count > 1 and ', ' or '',
                    'url' : link_url,
                    'link_label' : cgi.escape(link_label)}

        if count > CFG_WEBSEARCH_MAX_SEARCH_COLL_RESULTS_TO_PRINT:
            out += """ <a class="lessserviceitemslink" style="display:none;" href="#">%s</a>""" % _("Less suggestions")
            out += """ <a class="moreserviceitemslink" style="" href="#">%s</a>""" % _("More suggestions")

        return out

    def tmpl_print_searchresultbox(self, header, body):
        """print a nicely formatted box for search results """
        #_ = gettext_set_language(ln)

        # first find total number of hits:
        out = '<table class="searchresultsbox"><thead><tr><th class="searchresultsboxheader">' + header + '</th></tr></thead><tbody><tr><td class="searchresultsboxbody">' + body + '</td></tr></tbody></table>'
        return out


    def tmpl_search_no_boolean_hits(self, ln, nearestterms):
        """No hits found, proposes alternative boolean queries

        Parameters:

          - 'ln' *string* - The language to display

          - 'nearestterms' *array* - Parts of the interface to display, in the format:

          - 'nearestterms[nbhits]' *int* - The resulting number of hits

          - 'nearestterms[url_args]' *string* - The search parameters

          - 'nearestterms[p]' *string* - The search terms

        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = _("Boolean query returned no hits. Please combine your search terms differently.")

        out += '''<blockquote><table class="nearesttermsbox" cellpadding="0" cellspacing="0" border="0">'''
        for term, hits, argd in nearestterms:
            out += '''\
            <tr>
              <td class="nearesttermsboxbody" align="right">%(hits)s</td>
              <td class="nearesttermsboxbody" width="15">&nbsp;</td>
              <td class="nearesttermsboxbody" align="left">
                %(link)s
              </td>
            </tr>''' % {'hits' : hits,
                        'link': create_html_link(self.build_search_url(argd),
                                                 {}, cgi.escape(term),
                                                 {'class': "nearestterms"})}
        out += """</table></blockquote>"""
        return out

    def tmpl_similar_author_names(self, authors, ln):
        """No hits found, proposes alternative boolean queries

        Parameters:

          - 'authors': a list of (name, hits) tuples
          - 'ln' *string* - The language to display
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = '''<a name="googlebox"></a>
                 <table class="googlebox"><tr><th colspan="2" class="googleboxheader">%(similar)s</th></tr>''' % {
                'similar' : _("See also: similar author names")
              }
        for author, hits in authors:
            out += '''\
            <tr>
              <td class="googleboxbody">%(nb)d</td>
              <td class="googleboxbody">%(link)s</td>
            </tr>''' % {'link': create_html_link(
                                    self.build_search_url(p=author,
                                                          f='author',
                                                          ln=ln),
                                    {}, cgi.escape(author), {'class':"google"}),
                        'nb' : hits}

        out += """</table>"""

        return out

    def tmpl_print_record_detailed(self, recID, ln):
        """Displays a detailed on-the-fly record

        Parameters:

          - 'ln' *string* - The language to display

          - 'recID' *int* - The record id
        """
        # okay, need to construct a simple "Detailed record" format of our own:
        out = "<p>&nbsp;"
        # secondly, title:
        titles = get_fieldvalues(recID, "245__a") or \
                 get_fieldvalues(recID, "111__a")
        for title in titles:
            out += "<p><center><big><strong>%s</strong></big></center></p>" % cgi.escape(title)
        # thirdly, authors:
        authors = get_fieldvalues(recID, "100__a") + get_fieldvalues(recID, "700__a")
        if authors:
            out += "<p><center>"
            for author in authors:
                out += '%s; ' % create_html_link(self.build_search_url(
                                                                ln=ln,
                                                                p=author,
                                                                f='author'),
                                                 {}, cgi.escape(author))
            out += "</center></p>"
        # fourthly, date of creation:
        dates = get_fieldvalues(recID, "260__c")
        for date in dates:
            out += "<p><center><small>%s</small></center></p>" % date
        # fifthly, abstract:
        abstracts = get_fieldvalues(recID, "520__a")
        for abstract in abstracts:
            out += """<p style="margin-left: 15%%; width: 70%%">
                     <small><strong>Abstract:</strong> %s</small></p>""" % abstract
        # fifthly bis, keywords:
        keywords = get_fieldvalues(recID, "6531_a")
        if len(keywords):
            out += """<p style="margin-left: 15%%; width: 70%%">
                     <small><strong>Keyword(s):</strong>"""
            for keyword in keywords:
                out += '%s; ' % create_html_link(
                                    self.build_search_url(ln=ln,
                                                          p=keyword,
                                                          f='keyword'),
                                    {}, cgi.escape(keyword))

            out += '</small></p>'
        # fifthly bis bis, published in:
        prs_p = get_fieldvalues(recID, "909C4p")
        prs_v = get_fieldvalues(recID, "909C4v")
        prs_y = get_fieldvalues(recID, "909C4y")
        prs_n = get_fieldvalues(recID, "909C4n")
        prs_c = get_fieldvalues(recID, "909C4c")
        for idx in range(0, len(prs_p)):
            out += """<p style="margin-left: 15%%; width: 70%%">
                     <small><strong>Publ. in:</strong> %s""" % prs_p[idx]
            if prs_v and prs_v[idx]:
                out += """<strong>%s</strong>""" % prs_v[idx]
            if prs_y and prs_y[idx]:
                out += """(%s)""" % prs_y[idx]
            if prs_n and prs_n[idx]:
                out += """, no.%s""" % prs_n[idx]
            if prs_c and prs_c[idx]:
                out += """, p.%s""" % prs_c[idx]
            out += """.</small></p>"""
        # sixthly, fulltext link:
        urls_z = get_fieldvalues(recID, "8564_z")
        urls_u = get_fieldvalues(recID, "8564_u")
        # we separate the fulltext links and image links
        for url_u in urls_u:
            if url_u.endswith('.png'):
                continue
            else:
                link_text = "URL"
                try:
                    if urls_z[idx]:
                        link_text = urls_z[idx]
                except IndexError:
                    pass
                out += """<p style="margin-left: 15%%; width: 70%%">
                <small><strong>%s:</strong> <a href="%s">%s</a></small></p>""" % (link_text, urls_u[idx], urls_u[idx])

        # print some white space at the end:
        out += "<br /><br />"
        return out

    def tmpl_print_record_list_for_similarity_boxen(self, title, recID_score_list, ln=CFG_SITE_LANG):
        """Print list of records in the "hs" (HTML Similarity) format for similarity boxes.
           RECID_SCORE_LIST is a list of (recID1, score1), (recID2, score2), etc.
        """

        from invenio.search_engine import print_record, record_public_p

        recID_score_list_to_be_printed = []

        # firstly find 5 first public records to print:
        nb_records_to_be_printed = 0
        nb_records_seen = 0
        while nb_records_to_be_printed < 5 and nb_records_seen < len(recID_score_list) and nb_records_seen < 50:
            # looking through first 50 records only, picking first 5 public ones
            (recID, score) = recID_score_list[nb_records_seen]
            nb_records_seen += 1
            if record_public_p(recID):
                nb_records_to_be_printed += 1
                recID_score_list_to_be_printed.append([recID, score])

        # secondly print them:
        out = '''
        <table><tr>
         <td>
          <table><tr><td class="blocknote">%(title)s</td></tr></table>
         </td>
         </tr>
         <tr>
          <td><table>
        ''' % { 'title': cgi.escape(title) }
        for recid, score in recID_score_list_to_be_printed:
            out += '''
            <tr><td><font class="rankscoreinfo"><a>(%(score)s)&nbsp;</a></font><small>&nbsp;%(info)s</small></td></tr>''' % {
                'score': score,
                'info' : print_record(recid, format="hs", ln=ln),
                }

        out += """</table></td></tr></table> """
        return out

    def tmpl_print_record_brief(self, ln, recID):
        """Displays a brief record on-the-fly

        Parameters:

          - 'ln' *string* - The language to display

          - 'recID' *int* - The record id
        """
        out = ""

        # record 'recID' does not exist in format 'format', so print some default format:
        # firstly, title:
        titles = get_fieldvalues(recID, "245__a") or \
                 get_fieldvalues(recID, "111__a")
        # secondly, authors:
        authors = get_fieldvalues(recID, "100__a") + get_fieldvalues(recID, "700__a")
        # thirdly, date of creation:
        dates = get_fieldvalues(recID, "260__c")
        # thirdly bis, report numbers:
        rns = get_fieldvalues(recID, "037__a")
        rns = get_fieldvalues(recID, "088__a")
        # fourthly, beginning of abstract:
        abstracts = get_fieldvalues(recID, "520__a")
        # fifthly, fulltext link:
        urls_z = get_fieldvalues(recID, "8564_z")
        urls_u = get_fieldvalues(recID, "8564_u")
        # get rid of images
        images = []
        non_image_urls_u = []
        for url_u in urls_u:
            if url_u.endswith('.png'):
                images.append(url_u)
            else:
                non_image_urls_u.append(url_u)

        ## unAPI identifier
        out = '<abbr class="unapi-id" title="%s"></abbr>\n' % recID
        out += self.tmpl_record_body(
                 titles=titles,
                 authors=authors,
                 dates=dates,
                 rns=rns,
                 abstracts=abstracts,
                 urls_u=non_image_urls_u,
                 urls_z=urls_z,
                 ln=ln)

        return out

    def tmpl_print_record_brief_links(self, ln, recID, sf='', so='d', sp='', rm='', display_claim_link=False, display_edit_link=False):
        """Displays links for brief record on-the-fly

        Parameters:

          - 'ln' *string* - The language to display

          - 'recID' *int* - The record id
        """
        from invenio.webcommentadminlib import get_nb_reviews, get_nb_comments

        # load the right message language
        _ = gettext_set_language(ln)

        out = '<div class="moreinfo">'
        if CFG_WEBSEARCH_USE_ALEPH_SYSNOS:
            alephsysnos = get_fieldvalues(recID, "970__a")
            if len(alephsysnos) > 0:
                alephsysno = alephsysnos[0]
                out += '<span class="moreinfo">%s</span>' % \
                    create_html_link(self.build_search_url(recid=alephsysno,
                                                           ln=ln),
                                     {}, _("Detailed record"),
                                     {'class': "moreinfo"})
            else:
                out += '<span class="moreinfo">%s</span>' % \
                    create_html_link(self.build_search_url(recid=recID, ln=ln),
                                     {},
                                     _("Detailed record"),
                                     {'class': "moreinfo"})
        else:
            out += '<span class="moreinfo">%s</span>' % \
                   create_html_link(self.build_search_url(recid=recID, ln=ln),
                                    {}, _("Detailed record"),
                                    {'class': "moreinfo"})

            out += '<span class="moreinfo"> - %s</span>' % \
                   create_html_link(self.build_search_url(p="recid:%d" % recID,
                                                     rm="wrd",
                                                     ln=ln),
                                    {}, _("Similar records"),
                                    {'class': "moreinfo"})

        if CFG_BIBRANK_SHOW_CITATION_LINKS:
            num_timescited = get_cited_by_count(recID)
            if num_timescited:
                out += '<span class="moreinfo"> - %s</span>' % \
                       create_html_link(self.build_search_url(p="refersto:recid:%d" % recID,
                                                              sf=sf,
                                                              so=so,
                                                              sp=sp,
                                                              rm=rm,
                                                              ln=ln),
                                        {}, num_timescited > 1 and _("Cited by %i records") % num_timescited
                                        or _("Cited by 1 record"),
                                        {'class': "moreinfo"})
            else:
                out += "<!--not showing citations links-->"
        if display_claim_link: #Maybe we want not to show the link to who cannot use id?
            out += '<span class="moreinfo"> - %s</span>' % \
                create_html_link(CFG_SITE_URL + '/author/claim/action', {'assign':'True', 'selection':str(recID)},
                                                                        'Attribute this paper',
                                                                        {'class': "moreinfo"})

        if CFG_WEBCOMMENT_ALLOW_COMMENTS and CFG_WEBSEARCH_SHOW_COMMENT_COUNT:
            num_comments = get_nb_comments(recID, count_deleted=False)
            if num_comments:
                out += '<span class="moreinfo"> - %s</span>' % \
                        create_html_link(CFG_BASE_URL + '/' + CFG_SITE_RECORD + '/' + str(recID)
                        + '/comments?ln=%s' % ln, {}, num_comments > 1 and _("%i comments")
                        % (num_comments) or _("1 comment"),
                        {'class': "moreinfo"})
            else:
                out += "<!--not showing reviews links-->"

        if CFG_WEBCOMMENT_ALLOW_REVIEWS and CFG_WEBSEARCH_SHOW_REVIEW_COUNT:
            num_reviews = get_nb_reviews(recID, count_deleted=False)
            if num_reviews:
                out += '<span class="moreinfo"> - %s</span>' % \
                        create_html_link(CFG_BASE_URL + '/' + CFG_SITE_RECORD + '/' + str(recID)
                        + '/reviews?ln=%s' % ln, {}, num_reviews > 1 and _("%i reviews")
                        % (num_reviews) or _("1 review"), {'class': "moreinfo"})
            else:
                out += "<!--not showing reviews links-->"

        if display_edit_link:
            out += '<span class="moreinfo"> - %s</span>' % \
                    create_html_link('%s/%s/edit/?ln=%s#state=edit&recid=%s' % \
                                     (CFG_SITE_URL, CFG_SITE_RECORD, ln, str(recID)),
                                     {},
                                     link_label=_("Edit record"),
                                     linkattrd={'class': "moreinfo"})
        out += '</div>'
        return out

    def tmpl_xml_rss_prologue(self, current_url=None,
                              previous_url=None, next_url=None,
                              first_url=None, last_url=None,
                              nb_found=None, jrec=None, rg=None, cc=None):
        """Creates XML RSS 2.0 prologue."""
        title = CFG_SITE_NAME
        description = '%s latest documents' % CFG_SITE_NAME
        if cc and cc != CFG_SITE_NAME:
            title += ': ' + cgi.escape(cc)
            description += ' in ' + cgi.escape(cc)

        out = """<rss version="2.0"
        xmlns:media="http://search.yahoo.com/mrss/"
        xmlns:atom="http://www.w3.org/2005/Atom"
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:dcterms="http://purl.org/dc/terms/"
        xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
      <channel>
        <title>%(rss_title)s</title>
        <link>%(siteurl)s</link>
        <description>%(rss_description)s</description>
        <language>%(sitelang)s</language>
        <pubDate>%(timestamp)s</pubDate>
        <category></category>
        <generator>Invenio %(version)s</generator>
        <webMaster>%(sitesupportemail)s</webMaster>
        <ttl>%(timetolive)s</ttl>%(previous_link)s%(next_link)s%(current_link)s%(total_results)s%(start_index)s%(items_per_page)s
        <image>
            <url>%(siteurl)s/img/site_logo_rss.png</url>
            <title>%(sitename)s</title>
            <link>%(siteurl)s</link>
        </image>
         <atom:link rel="search" href="%(siteurl)s/opensearchdescription" type="application/opensearchdescription+xml" title="Content Search" />

        <textInput>
          <title>Search </title>
          <description>Search this site:</description>
          <name>p</name>
          <link>%(siteurl)s/search</link>
        </textInput>
        """ % {'sitename': CFG_SITE_NAME,
               'siteurl': CFG_SITE_URL,
               'sitelang': CFG_SITE_LANG,
               'search_syntax': self.tmpl_opensearch_rss_url_syntax,
               'timestamp': time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()),
               'version': CFG_VERSION,
               'sitesupportemail': CFG_SITE_SUPPORT_EMAIL,
               'timetolive': CFG_WEBSEARCH_RSS_TTL,
               'current_link': (current_url and \
                                 '\n<atom:link rel="self" href="%s" />\n' % current_url) or '',
               'previous_link': (previous_url and \
                                 '\n<atom:link rel="previous" href="%s" />' % previous_url) or '',
               'next_link': (next_url and \
                             '\n<atom:link rel="next" href="%s" />' % next_url) or '',
               'first_link': (first_url and \
                             '\n<atom:link rel="first" href="%s" />' % first_url) or '',
               'last_link': (last_url and \
                             '\n<atom:link rel="last" href="%s" />' % last_url) or '',
               'total_results': (nb_found and \
                             '\n<opensearch:totalResults>%i</opensearch:totalResults>' % nb_found) or '',
               'start_index': (jrec and \
                             '\n<opensearch:startIndex>%i</opensearch:startIndex>' % jrec) or '',
               'items_per_page': (rg and \
                             '\n<opensearch:itemsPerPage>%i</opensearch:itemsPerPage>' % rg) or '',
               'rss_title': title,
               'rss_description': description
        }
        return out

    def tmpl_xml_rss_epilogue(self):
        """Creates XML RSS 2.0 epilogue."""
        out = """\
      </channel>
</rss>\n"""
        return out

    def tmpl_xml_podcast_prologue(self, current_url=None,
                                  previous_url=None, next_url=None,
                                  first_url=None, last_url=None,
                                  nb_found=None, jrec=None, rg=None, cc=None):
        """Creates XML podcast prologue."""
        title = CFG_SITE_NAME
        description = '%s latest documents' % CFG_SITE_NAME
        if CFG_CERN_SITE:
            title = 'CERN'
            description = 'CERN latest documents'
        if cc and cc != CFG_SITE_NAME:
            title += ': ' + cgi.escape(cc)
            description += ' in ' + cgi.escape(cc)

        out = """<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" version="2.0">
        <channel>
        <title>%(podcast_title)s</title>
    	<link>%(siteurl)s</link>
        <description>%(podcast_description)s</description>
        <language>%(sitelang)s</language>
        <pubDate>%(timestamp)s</pubDate>
        <category></category>
	    <generator>Invenio %(version)s</generator>
        <webMaster>%(siteadminemail)s</webMaster>
        <ttl>%(timetolive)s</ttl>%(previous_link)s%(next_link)s%(current_link)s
        <image>
            <url>%(siteurl)s/img/site_logo_rss.png</url>
            <title>%(sitename)s</title>
            <link>%(siteurl)s</link>
        </image>
        <itunes:owner>
        <itunes:email>%(siteadminemail)s</itunes:email>
        </itunes:owner>
        """ % {'sitename': CFG_SITE_NAME,
               'siteurl': CFG_SITE_URL,
               'sitelang': CFG_SITE_LANG,
               'siteadminemail': CFG_SITE_ADMIN_EMAIL,
               'timestamp': time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()),
               'version': CFG_VERSION,
               'sitesupportemail': CFG_SITE_SUPPORT_EMAIL,
               'timetolive': CFG_WEBSEARCH_RSS_TTL,
               'current_link': (current_url and \
                                 '\n<atom:link rel="self" href="%s" />\n' % current_url) or '',
               'previous_link': (previous_url and \
                                 '\n<atom:link rel="previous" href="%s" />' % previous_url) or '',
               'next_link': (next_url and \
                             '\n<atom:link rel="next" href="%s" />' % next_url) or '',
               'first_link': (first_url and \
                             '\n<atom:link rel="first" href="%s" />' % first_url) or '',
               'last_link': (last_url and \
                             '\n<atom:link rel="last" href="%s" />' % last_url) or '',
                'podcast_title': title,
                'podcast_description': description
               }
        return out

    def tmpl_xml_podcast_epilogue(self):
        """Creates XML podcast epilogue."""
        out = """\n</channel>
</rss>\n"""
        return out

    def tmpl_xml_nlm_prologue(self):
        """Creates XML NLM prologue."""
        out = """<articles>\n"""
        return out

    def tmpl_xml_nlm_epilogue(self):
        """Creates XML NLM epilogue."""
        out = """\n</articles>"""
        return out

    def tmpl_xml_refworks_prologue(self):
        """Creates XML RefWorks prologue."""
        out = """<references>\n"""
        return out

    def tmpl_xml_refworks_epilogue(self):
        """Creates XML RefWorks epilogue."""
        out = """\n</references>"""
        return out

    def tmpl_xml_endnote_prologue(self):
        """Creates XML EndNote prologue."""
        out = """<xml>\n<records>\n"""
        return out

    def tmpl_xml_endnote_8x_prologue(self):
        """Creates XML EndNote prologue."""
        out = """<records>\n"""
        return out

    def tmpl_xml_endnote_epilogue(self):
        """Creates XML EndNote epilogue."""
        out = """\n</records>\n</xml>"""
        return out

    def tmpl_xml_endnote_8x_epilogue(self):
        """Creates XML EndNote epilogue."""
        out = """\n</records>"""
        return out

    def tmpl_xml_marc_prologue(self):
        """Creates XML MARC prologue."""
        out = """<collection xmlns="http://www.loc.gov/MARC21/slim">\n"""
        return out

    def tmpl_xml_marc_epilogue(self):
        """Creates XML MARC epilogue."""
        out = """\n</collection>"""
        return out

    def tmpl_xml_mods_prologue(self):
        """Creates XML MODS prologue."""
        out = """<modsCollection xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n
                   xsi:schemaLocation="http://www.loc.gov/mods/v3\n
                                       http://www.loc.gov/standards/mods/v3/mods-3-3.xsd">\n"""
        return out

    def tmpl_xml_mods_epilogue(self):
        """Creates XML MODS epilogue."""
        out = """\n</modsCollection>"""
        return out

    def tmpl_xml_default_prologue(self):
        """Creates XML default format prologue. (Sanity calls only.)"""
        out = """<collection>\n"""
        return out

    def tmpl_xml_default_epilogue(self):
        """Creates XML default format epilogue. (Sanity calls only.)"""
        out = """\n</collection>"""
        return out

    def tmpl_collection_not_found_page_title(self, colname, ln=CFG_SITE_LANG):
        """
        Create page title for cases when unexisting collection was asked for.
        """
        _ = gettext_set_language(ln)
        out = _("Collection %s Not Found") % cgi.escape(colname)
        return out

    def tmpl_collection_not_found_page_body(self, colname, ln=CFG_SITE_LANG):
        """
        Create page body for cases when unexisting collection was asked for.
        """
        _ = gettext_set_language(ln)
        out = """<h1>%(title)s</h1>
                 <p>%(sorry)s</p>
                 <p>%(you_may_want)s</p>
              """ % { 'title': self.tmpl_collection_not_found_page_title(colname, ln),
                      'sorry': _("Sorry, collection %s does not seem to exist.") % \
                                ('<strong>' + cgi.escape(colname) + '</strong>'),
                      'you_may_want': _("You may want to start browsing from %s.") % \
                                 ('<a href="' + CFG_BASE_URL + '/?ln=' + ln + '">' + \
                                        cgi.escape(CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME)) + '</a>')}
        return out

    def tmpl_alert_rss_teaser_box_for_query(self, id_query, ln, display_email_alert_part=True):
        """Propose teaser for setting up this query as alert or RSS feed.

        Parameters:
          - 'id_query' *int* - ID of the query we make teaser for
          - 'ln' *string* - The language to display
          - 'display_email_alert_part' *bool* - whether to display email alert part
        """

        # load the right message language
        _ = gettext_set_language(ln)

        # get query arguments:
        res = run_sql("SELECT urlargs FROM query WHERE id=%s", (id_query,))
        argd = {}
        if res:
            argd = cgi.parse_qs(res[0][0])

        rssurl = self.build_rss_url(argd)
        alerturl = CFG_BASE_URL + '/youralerts/input?ln=%s&amp;idq=%s' % (ln, id_query)

        if display_email_alert_part:
            msg_alert = _("""Set up a personal %(x_url1_open)semail alert%(x_url1_close)s
                                  or subscribe to the %(x_url2_open)sRSS feed%(x_url2_close)s.""") % \
                        {'x_url1_open': '<a href="%s"><img src="%s/img/mail-icon-12x8.gif" border="0" alt="" /></a> ' % (alerturl, CFG_BASE_URL) + ' <a class="google" href="%s">' % (alerturl),
                         'x_url1_close': '</a>',
                         'x_url2_open': '<a href="%s"><img src="%s/img/feed-icon-12x12.gif" border="0" alt="" /></a> ' % (rssurl, CFG_BASE_URL) + ' <a class="google" href="%s">' % rssurl,
                         'x_url2_close': '</a>', }
        else:
            msg_alert = _("""Subscribe to the %(x_url2_open)sRSS feed%(x_url2_close)s.""") % \
                        {'x_url2_open': '<a href="%s"><img src="%s/img/feed-icon-12x12.gif" border="0" alt="" /></a> ' % (rssurl, CFG_BASE_URL) + ' <a class="google" href="%s">' % rssurl,
                         'x_url2_close': '</a>', }

        out = '''<a name="googlebox"></a>
                 <table class="googlebox"><tr><th class="googleboxheader">%(similar)s</th></tr>
                 <tr><td class="googleboxbody">%(msg_alert)s</td></tr>
                 </table>
                 ''' % {
                'similar' : _("Interested in being notified about new results for this query?"),
                'msg_alert': msg_alert, }
        return out

    def tmpl_detailed_record_metadata(self, recID, ln, format,
                                      content,
                                      creationdate=None,
                                      modificationdate=None):
        """Returns the main detailed page of a record

        Parameters:

          - 'recID' *int* - The ID of the printed record

          - 'ln' *string* - The language to display

          - 'format' *string* - The format in used to print the record

          - 'content' *string* - The main content of the page

          - 'creationdate' *string* - The creation date of the printed record

          - 'modificationdate' *string* - The last modification date of the printed record
        """
        _ = gettext_set_language(ln)

        ## unAPI identifier
        out = '<abbr class="unapi-id" title="%s"></abbr>\n' % recID
        out += content
        return out

    def tmpl_display_back_to_search(self, req, recID, ln):
        """
        Displays next-hit/previous-hit/back-to-search links
        on the detailed record pages in order to be able to quickly
        flip between detailed record pages
        @param req: Apache request object
        @type req: Apache request object
        @param recID: detailed record ID
        @type recID: int
        @param ln: language of the page
        @type ln: string
        @return: html output
        @rtype: html
        """

        _ = gettext_set_language(ln)

        # this variable is set to zero and then, nothing is displayed
        if not CFG_WEBSEARCH_PREV_NEXT_HIT_LIMIT:
            return ''

        # this variable is set to zero and then nothing is saved in the previous session
        if not CFG_WEBSEARCH_PREV_NEXT_HIT_FOR_GUESTS:
            return ''

        # search for a specific record having not done any search before
        wlq = session_param_get(req, 'websearch-last-query', '')
        wlqh = session_param_get(req, 'websearch-last-query-hits')

        out = '''<br/><br/><div align="right">'''
        # excedeed limit CFG_WEBSEARCH_PREV_NEXT_HIT_LIMIT,
        # then will be displayed only the back to search link
        if wlqh is None:
            out += '''<div style="padding-bottom:2px;padding-top:30px;"><span class="moreinfo" style="margin-right:10px;">
                        %(back)s </span></div></div>''' % \
                        {'back': create_html_link(wlq, {}, _("Back to search"), {'class': "moreinfo"})}
            return out

        # let's look for the recID's collection
        record_found = False
        for coll in wlqh:
            if recID in coll:
                record_found = True
                coll_recID = coll
                break

        # let's calculate lenght of recID's collection
        if record_found:
            recIDs = coll_recID[::-1]
            totalrec = len(recIDs)
        # search for a specific record having not done any search before
        else:
            return ''

        # if there is only one hit,
        # to show only the "back to search" link
        if totalrec == 1:
            # to go back to the last search results page
            out += '''<div style="padding-bottom:2px;padding-top:30px;"><span class="moreinfo" style="margin-right:10px;">
                        %(back)s </span></div></div>''' % \
                        {'back': create_html_link(wlq, {}, _("Back to search"), {'class': "moreinfo"})}
        elif totalrec > 1:
            pos = recIDs.index(recID)
            numrec = pos + 1
            if pos == 0:
                recIDnext = recIDs[pos + 1]
                recIDlast = recIDs[totalrec - 1]
                # to display only next and last links
                out += '''<div><span class="moreinfo" style="margin-right:10px;">
                                    %(numrec)s %(totalrec)s %(next)s %(last)s </span></div> ''' % {
                                'numrec': _("%s of") % ('<strong>' + self.tmpl_nice_number(numrec, ln) + '</strong>'),
                                'totalrec': ("%s") % ('<strong>' + self.tmpl_nice_number(totalrec, ln) + '</strong>'),
                                'next': create_html_link(self.build_search_url(recid=recIDnext, ln=ln),
                                        {}, ('<font size="4">&rsaquo;</font>'), {'class': "moreinfo"}),
                                'last': create_html_link(self.build_search_url(recid=recIDlast, ln=ln),
                                        {}, ('<font size="4">&raquo;</font>'), {'class': "moreinfo"})}
            elif pos == totalrec - 1:
                recIDfirst = recIDs[0]
                recIDprev = recIDs[pos - 1]
                # to display only first and previous links
                out += '''<div style="padding-top:30px;"><span class="moreinfo" style="margin-right:10px;">
                                    %(first)s %(previous)s %(numrec)s %(totalrec)s</span></div>''' % {
                                'first': create_html_link(self.build_search_url(recid=recIDfirst, ln=ln),
                                            {}, ('<font size="4">&laquo;</font>'), {'class': "moreinfo"}),
                                'previous': create_html_link(self.build_search_url(recid=recIDprev, ln=ln),
                                            {}, ('<font size="4">&lsaquo;</font>'), {'class': "moreinfo"}),
                                'numrec': _("%s of") % ('<strong>' + self.tmpl_nice_number(numrec, ln) + '</strong>'),
                                'totalrec': ("%s") % ('<strong>' + self.tmpl_nice_number(totalrec, ln) + '</strong>')}
            else:
                # to display all links
                recIDfirst = recIDs[0]
                recIDprev = recIDs[pos - 1]
                recIDnext = recIDs[pos + 1]
                recIDlast = recIDs[len(recIDs) - 1]
                out += '''<div style="padding-top:30px;"><span class="moreinfo" style="margin-right:10px;">
                                    %(first)s %(previous)s
                                    %(numrec)s %(totalrec)s %(next)s %(last)s </span></div>''' % {
                                'first': create_html_link(self.build_search_url(recid=recIDfirst, ln=ln),
                                            {}, ('<font size="4">&laquo;</font>'),
                                            {'class': "moreinfo"}),
                                'previous': create_html_link(self.build_search_url(recid=recIDprev, ln=ln),
                                            {}, ('<font size="4">&lsaquo;</font>'), {'class': "moreinfo"}),
                                'numrec': _("%s of") % ('<strong>' + self.tmpl_nice_number(numrec, ln) + '</strong>'),
                                'totalrec': ("%s") % ('<strong>' + self.tmpl_nice_number(totalrec, ln) + '</strong>'),
                                'next': create_html_link(self.build_search_url(recid=recIDnext, ln=ln),
                                            {}, ('<font size="4">&rsaquo;</font>'), {'class': "moreinfo"}),
                                'last': create_html_link(self.build_search_url(recid=recIDlast, ln=ln),
                                            {}, ('<font size="4">&raquo;</font>'), {'class': "moreinfo"})}
            out += '''<div style="padding-bottom:2px;"><span class="moreinfo" style="margin-right:10px;">
                        %(back)s </span></div></div>''' % {
                    'back': create_html_link(wlq, {}, _("Back to search"), {'class': "moreinfo"})}
        return out

    def tmpl_record_hepdata(self, data, recid, isLong=True):
        """ Generate a page for HepData records
        """
        from invenio import hepdatautils
        from invenio.search_engine import get_fieldvalues

        c = []
        c.append("<div style=\"background-color: #ececec;\">")

        flag_hepdata = 0
        flag_dataverse = 0
        for dataset in data.datasets:
            try:
                publisher = get_fieldvalues(dataset.recid, '520__9')[0]
            except IndexError:
                from invenio.hepdatautils import create_hepdata_ticket
                create_hepdata_ticket(dataset.recid, 'Data missing in 520__9')
                continue
            if publisher == "HEPDATA" and flag_hepdata == 0:
                flag_hepdata = 1
            elif publisher == "Dataverse":
                flag_dataverse = 1

        if flag_hepdata == 1 or flag_dataverse == 1:
            c.append("<h3> This data comes from ")
            if flag_hepdata == 1:
                c.append('<a href="http://hepdata.cedar.ac.uk/view/ins%s" target="_blank"> Durham HepData project </a>' % (recid))
            if flag_hepdata == 1 and flag_dataverse == 1:
                c.append(' and ')
            if flag_dataverse == 1:
                c.append('<a href="http://thedata.harvard.edu/"> Dataverse </a>')
            c.append('</h3>')

        c.append("<div style=\"background-color: #ececec;\">")
        if data.comment:
            c.append("<h3> Summary:</h3>")
            c.append("""<div class="hepdataSummary">%s</div>""" % (data.comment, ))

        if data.systematics and data.systematics.strip() != "":
            c.append("<h3>Systematic data: </h3>")
            c.append(data.systematics)
            c.append("</div>")

        if data.additional_data_links:
            c.append("<h3>Additional data:</h3>")
            for link in data.additional_data_links:
                if "href" in link and "description" in link:
                    c.append("<a href=\"%s/%s\">%s</a><br>" % (CFG_HEPDATA_URL, link["href"], link["description"]))

        c.append("<h3> Datasets:</h3>")

        seq = 0

        for dataset in data.datasets:
            seq += 1
            try:
                publisher = get_fieldvalues(dataset.recid, '520__9')[0]
            except IndexError:
                from invenio.hepdatautils import create_hepdata_ticket
                create_hepdata_ticket(dataset.recid, 'Data missing in 520__9')
                continue
            if publisher == "HEPDATA":
                c.append(hepdatadisplayutils.render_hepdata_dataset_html(dataset, recid, seq))
            elif publisher == "Dataverse":
                c.append(hepdatadisplayutils.render_dataverse_dataset_html(dataset.recid))
            elif publisher == "INSPIRE":
                c.append(hepdatadisplayutils.render_inspire_dataset_html(dataset.recid))
            else:
                c.append(hepdatadisplayutils.render_other_dataset_html(dataset.recid))

        c.append("</div>")

        return "\n".join(c)

    def tmpl_record_no_hepdata(self):
        return "This record does not have HEP data associated"

    def tmpl_record_plots(self, recID, ln):
        """
          Displays little tables containing the images and captions contained in the specified document.

        Parameters:

          - 'recID' *int* - The ID of the printed record

          - 'ln' *string* - The language to display
        """
        from invenio.search_engine import get_record
        from invenio.bibrecord import field_get_subfield_values
        from invenio.bibrecord import record_get_field_instances
        _ = gettext_set_language(ln)

        out = ''

        rec = get_record(recID)
        flds = record_get_field_instances(rec, '856', '4')

        images = []

        for fld in flds:
            image = field_get_subfield_values(fld, 'u')
            caption = field_get_subfield_values(fld, 'y')
            data_urls = field_get_subfield_values(fld, 'z')
            if type(data_urls) == list and len(data_urls) > 0:
                data_urls = str(data_urls[0])
                if data_urls.startswith("HEPDATA:"):
                    data_urls = data_urls[8:].split(";")
                else:
                    data_urls = []

            if type(image) == list and len(image) > 0:
                image = image[0]
            else:
                continue
            if type(caption) == list and len(caption) > 0:
                caption = caption[0]
            else:
                continue

            if not image.endswith('.png'):
                # huh?
                continue

            if len(caption) >= 5:
                images.append((int(caption[:5]), image, caption[5:], data_urls))
            else:
                # we don't have any idea of the order... just put it on
                images.append(99999, image, caption, data_urls)

        images = sorted(images, key=lambda x: x[0])

        for (index, image, caption, data_urls) in images:
            # let's put everything in nice little subtables with the image
            # next to the caption
            data_string_list = []
            seq_num = 1

            for data_url in data_urls:
                val = ""
                if len(data_urls) > 1:
                    val = " %i" % seq_num
                data_string_list.append("<br><a href=\"%s\">Data%s</a>" % (str(data_url), val))
                seq_num += 1

            data_string = "".join(data_string_list)
            out = out + '<table width="95%" style="display: inline;">' + \
                 '<tr><td width="66%"><a name="' + str(index) + '" ' + \
                 'href="' + image + '">' + \
                 '<img src="' + image + '" width="95%"/></a></td>' + \
                 '<td width="33%">' + caption +  data_string + '</td></tr>' + \
                 '</table>'

        out = out + '<br /><br />'

        return out


    def tmpl_detailed_record_statistics(self, recID, ln,
                                        downloadsimilarity,
                                        downloadhistory, viewsimilarity):
        """Returns the statistics page of a record

        Parameters:

          - 'recID' *int* - The ID of the printed record

          - 'ln' *string* - The language to display

          - downloadsimilarity *string* - downloadsimilarity box

          - downloadhistory *string* - downloadhistory box

          - viewsimilarity *string* - viewsimilarity box

        """
        # load the right message language
        _ = gettext_set_language(ln)

        out = ''

        if CFG_BIBRANK_SHOW_DOWNLOAD_STATS and downloadsimilarity is not None:
            similar = self.tmpl_print_record_list_for_similarity_boxen (
                _("People who downloaded this document also downloaded:"), downloadsimilarity, ln)

            out = '<table>'
            out += '''
                    <tr><td>%(graph)s</td></tr>
                    <tr><td>%(similar)s</td></tr>
                    ''' % { 'siteurl': CFG_BASE_URL, 'recid': recID, 'ln': ln,
                             'similar': similar, 'more': _("more"),
                             'graph': downloadsimilarity
                             }

            out += '</table>'
            out += '<br />'

        if CFG_BIBRANK_SHOW_READING_STATS and viewsimilarity is not None:
            out += self.tmpl_print_record_list_for_similarity_boxen (
                _("People who viewed this page also viewed:"), viewsimilarity, ln)

        if CFG_BIBRANK_SHOW_DOWNLOAD_GRAPHS and downloadhistory is not None:
            out += downloadhistory + '<br />'

        return out

    def tmpl_detailed_record_citations_prologue(self, recID, ln):
        """Returns the prologue of the citations page of a record

        Parameters:

          - 'recID' *int* - The ID of the printed record

          - 'ln' *string* - The language to display

        """

        return '<table>'

    def tmpl_detailed_record_citations_epilogue(self, recID, ln):
        """Returns the epilogue of the citations page of a record

        Parameters:

          - 'recID' *int* - The ID of the printed record

          - 'ln' *string* - The language to display

        """

        return '</table>'

    def tmpl_detailed_record_citations_citing_list(self, recID, ln,
                                                   citinglist,
                                                   sf='', so='d', sp='', rm=''):
        """Returns the list of record citing this one

        Parameters:

          - 'recID' *int* - The ID of the printed record

          - 'ln' *string* - The language to display

          - citinglist *list* - a list of tuples [(x1,y1),(x2,y2),..] where x is doc id and y is number of citations

        """
        # load the right message language
        _ = gettext_set_language(ln)

        out = ''

        if CFG_BIBRANK_SHOW_CITATION_STATS and citinglist is not None:
            similar = self.tmpl_print_record_list_for_similarity_boxen(
                _("Cited by: %s records") % len (citinglist), citinglist, ln)

            out += '''
                    <tr><td>
                      %(similar)s&nbsp;%(more)s
                      <br /><br />
                    </td></tr>''' % {
                'more': create_html_link(
                self.build_search_url(p='refersto:recid:%d' % recID, #XXXX
                                      sf=sf,
                                      so=so,
                                      sp=sp,
                                      rm=rm,
                                      ln=ln),
                                      {}, _("more")),
                'similar': similar}
        return out

    def tmpl_detailed_record_citations_citation_history(self, ln,
                                                              citationhistory):
        """Returns the citations history graph of this record

        Parameters:

          - 'recID' *int* - The ID of the printed record

          - 'ln' *string* - The language to display

          - citationhistory *string* - citationhistory box

        """
        # load the right message language
        _ = gettext_set_language(ln)

        out = ''

        if CFG_BIBRANK_SHOW_CITATION_GRAPHS and citationhistory is not None:
            out = '<!--citation history--><tr><td>%s</td></tr>' % citationhistory
        else:
            out = "<!--not showing citation history. CFG_BIBRANK_SHOW_CITATION_GRAPHS:"
            out += str(CFG_BIBRANK_SHOW_CITATION_GRAPHS) + " citationhistory "
            if citationhistory:
                out += str(len(citationhistory)) + "-->"
            else:
                out += "no citationhistory -->"
        return out

    def tmpl_detailed_record_citations_citation_log(self, ln, log_entries):
        """Returns the citations history graph of this record

        Parameters:

          - 'recID' *int* - The ID of the printed record

          - 'ln' *string* - The language to display

          - citationhistory *string* - citationhistory box

        """
        # load the right message language
        _ = gettext_set_language(ln)

        out = []
        if log_entries:
            out.append('<style>td.citationlogdate { width: 5.4em; }</style>')
            out.append('<table><tr><td class="blocknote">Citation Log: </td></tr><tr><td><a id="citationlogshow" class="moreinfo" style="text-decoration: underline; " onclick="$(\'#citationlog\').show(); $(\'#citationlogshow\').hide();">show</a></td></tr></table>')
            out.append('<table id="citationlog" style="display: none;">')
            for recid, action_type, action_date in log_entries:
                if record_exists(recid) == 1:
                    record_str = format_record(recid, 'HS2')
                else:
                    record_str = 'The record with id %s was deleted' % recid
                out.append("""<tr>
  <td>%s</td>
  <td class="citationlogdate">%s</td>
  <td>%s</td>
</tr>""" % (action_type, action_date.strftime('%Y-%m-%d'), record_str))
            out.append('</table>')

        return '\n'.join(out)

    def tmpl_detailed_record_citations_co_citing(self, recID, ln,
                                                 cociting):
        """Returns the list of cocited records

        Parameters:

          - 'recID' *int* - The ID of the printed record

          - 'ln' *string* - The language to display

          - cociting *string* - cociting box

        """
        # load the right message language
        _ = gettext_set_language(ln)

        out = ''

        if CFG_BIBRANK_SHOW_CITATION_STATS and cociting is not None:
            similar = self.tmpl_print_record_list_for_similarity_boxen (
                _("Co-cited with: %s records") % len (cociting), cociting, ln)

            out = '''
                    <tr><td>
                      %(similar)s&nbsp;%(more)s
                      <br />
                    </td></tr>''' % { 'more': create_html_link(self.build_search_url(p='cocitedwith:%d' % recID, ln=ln),
                                                                {}, _("more")),
                                      'similar': similar }
        return out


    def tmpl_detailed_record_citations_self_cited(self, recID, ln,
                                                  selfcited, citinglist):
        """Returns the list of self-citations for this record

        Parameters:

          - 'recID' *int* - The ID of the printed record

          - 'ln' *string* - The language to display

          - selfcited list - a list of self-citations for recID

        """
        # load the right message language
        _ = gettext_set_language(ln)

        out = ''

        if CFG_BIBRANK_SHOW_CITATION_GRAPHS and selfcited is not None:
            sc_scorelist = [] #a score list for print..
            for s in selfcited:
                #copy weight from citations
                weight = 0
                for c in citinglist:
                    (crec, score) = c
                    if crec == s:
                        weight = score
                tmp = [s, weight]
                sc_scorelist.append(tmp)
            scite = self.tmpl_print_record_list_for_similarity_boxen (
                _(".. of which self-citations: %s records") % len (selfcited), sc_scorelist, ln)
            out = '<tr><td>' + scite + '</td></tr>'
        return out

    def tmpl_author_information(self, req, pubs, authorname, num_downloads,
                                aff_pubdict, citedbylist, kwtuples, authors,
                                vtuples, names_dict, person_link,
                                bibauthorid_data, ln, return_html=False):
        """Prints stuff about the author given as authorname.
           1. Author name + his/her institutes. Each institute I has a link
              to papers where the auhtor has I as institute.
           2. Publications, number: link to search by author.
           3. Keywords
           4. Author collabs
           5. Publication venues like journals
           The parameters are data structures needed to produce 1-6, as follows:
           req - request
           pubs - list of recids, probably the records that have the author as an author
           authorname - evident
           num_downloads - evident
           aff_pubdict - a dictionary where keys are inst names and values lists of recordids
           citedbylist - list of recs that cite pubs
           kwtuples - keyword tuples like ('HIGGS BOSON',[3,4]) where 3 and 4 are recids
           authors - a list of authors that have collaborated with authorname
           names_dict - a dict of {name: frequency}
        """
        from invenio.search_engine import perform_request_search
        from operator import itemgetter
        _ = gettext_set_language(ln)
        ib_pubs = intbitset(pubs)
        html = []

        # construct an extended search as an interim solution for author id
        # searches. Will build "(exactauthor:v1 OR exactauthor:v2)" strings
#        extended_author_search_str = ""

#        if bibauthorid_data["is_baid"]:
#            if len(names_dict.keys()) > 1:
#                extended_author_search_str = '('
#
#            for name_index, name_query in enumerate(names_dict.keys()):
#                if name_index > 0:
#                    extended_author_search_str += " OR "
#
#                extended_author_search_str += 'exactauthor:"' + name_query + '"'
#
#            if len(names_dict.keys()) > 1:
#                extended_author_search_str += ')'
#     rec_query = 'exactauthor:"' + authorname + '"'
#
#        if bibauthorid_data["is_baid"] and extended_author_search_str:
#            rec_query = extended_author_search_str


        baid_query = ""
        extended_author_search_str = ""

        if 'is_baid' in bibauthorid_data and bibauthorid_data['is_baid']:
            if bibauthorid_data["cid"]:
                baid_query = 'author:%s' % bibauthorid_data["cid"]
            elif bibauthorid_data["pid"] > -1:
                baid_query = 'author:%s' % bibauthorid_data["pid"]
            ## todo: figure out if the author index is filled with pids/cids.
            ## if not: fall back to exactauthor search.
            # if not index:
            #    baid_query = ""

        if not baid_query:
            baid_query = 'exactauthor:"' + authorname + '"'

            if bibauthorid_data['is_baid']:
                if len(names_dict.keys()) > 1:
                    extended_author_search_str = '('

                for name_index, name_query in enumerate(names_dict.keys()):
                    if name_index > 0:
                        extended_author_search_str += " OR "

                    extended_author_search_str += 'exactauthor:"' + name_query + '"'

                if len(names_dict.keys()) > 1:
                    extended_author_search_str += ')'

            if bibauthorid_data['is_baid'] and extended_author_search_str:
                baid_query = extended_author_search_str

        baid_query = baid_query + " "
        sorted_names_list = sorted(names_dict.iteritems(), key=itemgetter(1),
                                   reverse=True)

        # Prepare data for display
        # construct names box
        header = "<strong>" + _("Name variants") + "</strong>"
        content = []

        for name, frequency in sorted_names_list:
            prquery = baid_query + ' exactauthor:"' + name + '"'
            name_lnk = create_html_link(self.build_search_url(p=prquery),
                                                              {},
                                                              str(frequency),)
            content.append("%s (%s)" % (name, name_lnk))

        if not content:
            content = [_("No Name Variants")]

        names_box = self.tmpl_print_searchresultbox(header, "<br />\n".join(content))

        # construct papers box
        rec_query = baid_query
        searchstr = create_html_link(self.build_search_url(p=rec_query),
                                     {}, "<strong>" + "All papers (" + str(len(pubs)) + ")" + "</strong>",)
        line1 = "<strong>" + _("Papers") + "</strong>"
        line2 = searchstr

        if CFG_BIBRANK_SHOW_DOWNLOAD_STATS and num_downloads:
            line2 += " (" + _("downloaded") + " "
            line2 += str(num_downloads) + " " + _("times") + ")"

        if CFG_INSPIRE_SITE:
            CFG_COLLS = ['Book',
                         'Conference',
                         'Introductory',
                         'Lectures',
                         'Preprint',
                         'Published',
                         'Review',
                         'Thesis']
        else:
            CFG_COLLS = ['Article',
                         'Book',
                         'Preprint', ]
        collsd = {}
        for coll in CFG_COLLS:
            coll_papers = list(ib_pubs & intbitset(perform_request_search(f="collection", p=coll)))
            if coll_papers:
                collsd[coll] = coll_papers
        colls = collsd.keys()
        colls.sort(lambda x, y: cmp(len(collsd[y]), len(collsd[x]))) # sort by number of papers
        for coll in colls:
            rec_query = baid_query + 'collection:' + coll
            line2 += "<br />" + create_html_link(self.build_search_url(p=rec_query),
                                                                       {}, coll + " (" + str(len(collsd[coll])) + ")",)

        if not pubs:
            line2 = _("No Papers")

        papers_box = self.tmpl_print_searchresultbox(line1, line2)

        #make a authoraff string that looks like CERN (1), Caltech (2) etc
        authoraff = ""
        aff_pubdict_keys = aff_pubdict.keys()
        aff_pubdict_keys.sort(lambda x, y: cmp(len(aff_pubdict[y]), len(aff_pubdict[x])))

        if aff_pubdict_keys:
            for a in aff_pubdict_keys:
                print_a = a
                if (print_a == ' '):
                    print_a = _("unknown affiliation")
                if authoraff:
                    authoraff += '<br>'
                authoraff += create_html_link(self.build_search_url(p=' or '.join(["%s" % x for x in aff_pubdict[a]]),
                                                                       f='recid'),
                                                                       {}, print_a + ' (' + str(len(aff_pubdict[a])) + ')',)
        else:
            authoraff = _("No Affiliations")

        line1 = "<strong>" + _("Affiliations") + "</strong>"
        line2 = authoraff
        affiliations_box = self.tmpl_print_searchresultbox(line1, line2)

        # print frequent keywords:
        keywstr = ""
        if (kwtuples):
            for (kw, freq) in kwtuples:
                if keywstr:
                    keywstr += '<br>'
                rec_query = baid_query + 'keyword:"' + kw + '"'
                searchstr = create_html_link(self.build_search_url(p=rec_query),
                                                                   {}, kw + " (" + str(freq) + ")",)
                keywstr = keywstr + " " + searchstr

        else:
            keywstr += _('No Keywords')


        line1 = "<strong>" + _("Frequent keywords") + "</strong>"
        line2 = keywstr
        keyword_box = self.tmpl_print_searchresultbox(line1, line2)


        header = "<strong>" + _("Frequent co-authors") + "</strong>"
        content = []
        sorted_coauthors = sorted(sorted(authors.iteritems(), key=itemgetter(0)),
                                  key=itemgetter(1), reverse=True)

        for name, frequency in sorted_coauthors:
            rec_query = baid_query + 'exactauthor:"' + name + '"'
            lnk = create_html_link(self.build_search_url(p=rec_query), {}, "%s (%s)" % (name, frequency),)
            content.append("%s" % lnk)

        if not content:
            content = [_("No Frequent Co-authors")]

        coauthor_box = self.tmpl_print_searchresultbox(header, "<br />\n".join(content))

        pubs_to_papers_link = create_html_link(self.build_search_url(p=baid_query), {}, str(len(pubs)))
        display_name = ""

        try:
            display_name = sorted_names_list[0][0]
        except IndexError:
            display_name = "&nbsp;"

        headertext = ('<h1>%s <span style="font-size:50%%;">(%s papers)</span></h1>'
                      % (display_name, pubs_to_papers_link))

        if return_html:
            html.append(headertext)
        else:
            req.write(headertext)
            #req.write("<h1>%s</h1>" % (authorname))

        if person_link:
            cmp_link = ('<div><a href="%s/author/claim/claimstub?person=%s">%s</a></div>'
                      % (CFG_SITE_URL, person_link,
                         _("This is me.  Verify my publication list.")))
            if return_html:
                html.append(cmp_link)
            else:
                req.write(cmp_link)

        if return_html:
            html.append("<table width=80%><tr valign=top><td>")
            html.append(names_box)
            html.append("<br />")
            html.append(papers_box)
            html.append("<br />")
            html.append(keyword_box)
            html.append("</td>")
            html.append("<td>&nbsp;</td>")
            html.append("<td>")
            html.append(affiliations_box)
            html.append("<br />")
            html.append(coauthor_box)
            html.append("</td></tr></table>")
        else:
            req.write("<table width=80%><tr valign=top><td>")
            req.write(names_box)
            req.write("<br />")
            req.write(papers_box)
            req.write("<br />")
            req.write(keyword_box)
            req.write("</td>")
            req.write("<td>&nbsp;</td>")
            req.write("<td>")
            req.write(affiliations_box)
            req.write("<br />")
            req.write(coauthor_box)
            req.write("</td></tr></table>")

        # print citations:
        rec_query = baid_query

        if len(citedbylist):
            line1 = "<strong>" + _("Citations:") + "</strong>"
            line2 = ""

            if not pubs:
                line2 = _("No Citation Information available")

            sr_box = self.tmpl_print_searchresultbox(line1, line2)

            if return_html:
                html.append(sr_box)
            else:
                req.write(sr_box)

        if return_html:
            return "\n".join(html)

        # print frequent co-authors:
#        collabstr = ""
#        if (authors):
#            for c in authors:
#                c = c.strip()
#                if collabstr:
#                    collabstr += '<br>'
#                #do not add this person him/herself in the list
#                cUP = c.upper()
#                authornameUP = authorname.upper()
#                if not cUP == authornameUP:
#                    commpubs = intbitset(pubs) & intbitset(perform_request_search(p="exactauthor:\"%s\" exactauthor:\"%s\"" % (authorname, c)))
#                    collabstr = collabstr + create_html_link(self.build_search_url(p='exactauthor:"' + authorname + '" exactauthor:"' + c + '"'),
#                                                              {}, c + " (" + str(len(commpubs)) + ")",)
#        else: collabstr += 'None'
#        banner = self.tmpl_print_searchresultbox("<strong>" + _("Frequent co-authors:") + "</strong>", collabstr)


        # print frequently publishes in journals:
        #if (vtuples):
        #    pubinfo = ""
        #    for t in vtuples:
        #        (journal, num) = t
        #        pubinfo += create_html_link(self.build_search_url(p='exactauthor:"' + authorname + '" ' + \
        #                                                          'journal:"' + journal + '"'),
        #                                           {}, journal + " ("+str(num)+")<br/>")
        #    banner = self.tmpl_print_searchresultbox("<strong>" + _("Frequently publishes in:") + "<strong>", pubinfo)
        #    req.write(banner)


    def tmpl_detailed_record_references(self, recID, ln, content):
        """Returns the discussion page of a record

        Parameters:

          - 'recID' *int* - The ID of the printed record

          - 'ln' *string* - The language to display

          - 'content' *string* - The main content of the page
        """
        # load the right message language
        out = ''
        if content is not None:
            out += content

        return out

    def tmpl_citesummary_title(self, ln=CFG_SITE_LANG):
        """HTML citesummary title and breadcrumbs

        A part of HCS format suite."""
        return ''

    def tmpl_citesummary2_title(self, searchpattern, ln=CFG_SITE_LANG):
        """HTML citesummary title and breadcrumbs

        A part of HCS2 format suite."""
        return ''

    def tmpl_citesummary_back_link(self, searchpattern, ln=CFG_SITE_LANG):
        """HTML back to citesummary link

        A part of HCS2 format suite."""
        _ = gettext_set_language(ln)
        out = ''
        params = {'ln': 'en',
                  'p': quote(searchpattern),
                  'of': 'hcs'}
        msg = _('Back to citesummary')

        url = CFG_BASE_URL + '/search?' + \
                          '&'.join(['='.join(i) for i in params.iteritems()])
        out += '<p><a href="%(url)s">%(msg)s</a></p>' % {'url': url, 'msg': msg}

        return out

    def tmpl_citesummary_more_links(self, searchpattern, ln=CFG_SITE_LANG):
        _ = gettext_set_language(ln)
        out = ''
        msg = _('<p><a href="%(url)s">%(msg)s</a></p>')
        params = {'ln': ln,
                  'p': quote(searchpattern),
                  'of': 'hcs2'}
        url = CFG_BASE_URL + '/search?' + \
                       '&amp;'.join(['='.join(i) for i in params.iteritems()])
        out += msg % {'url': url,
                      'msg': _('Exclude self-citations')}

        return out

    def tmpl_citesummary_prologue(self, coll_recids, collections, search_patterns,
                                  searchfield, citable_recids, total_count,
                                  ln=CFG_SITE_LANG):
        """HTML citesummary format, prologue. A part of HCS format suite."""
        _ = gettext_set_language(ln)
        out = """<table id="citesummary">
                  <tr>
                    <td>
                      <strong class="headline">%(msg_title)s</strong>
                    </td>""" % \
               {'msg_title': _("Citation summary results"), }
        for coll, dummy in collections:
            out += '<td align="right">%s</td>' % _(coll)
        out += '</tr>'
        out += """<tr><td><strong>%(msg_recs)s</strong></td>""" % \
               {'msg_recs': _("Total number of papers analyzed:"), }
        for coll, colldef in collections:
            link_url = tmpl_citesummary_get_link(search_patterns[coll], searchfield, colldef)
            link_text = self.tmpl_nice_number(len(coll_recids[coll]), ln)
            out += '<td align="right"><a href="%s">%s</a></td>' % (link_url,
                                                                   link_text)
        out += '</tr>'
        return out


    def tmpl_citesummary_overview(self, collections, d_total_cites,
                                  d_avg_cites, ln=CFG_SITE_LANG):
        """HTML citesummary format, overview. A part of HCS format suite."""
        _ = gettext_set_language(ln)
        out = """<tr><td><strong>%(msg_cites)s</strong></td>""" % \
              {'msg_cites': _("Total number of citations:"), }
        for coll, dummy in collections:
            total_cites = d_total_cites[coll]
            out += '<td align="right">%s</td>' % \
                                        self.tmpl_nice_number(total_cites, ln)
        out += '</tr>'
        out += """<tr><td><strong>%(msg_avgcit)s</strong></td>""" % \
               {'msg_avgcit': _("Average citations per paper:"), }
        for coll, dummy in collections:
            avg_cites = d_avg_cites[coll]
            out += '<td align="right">%.1f</td>' % avg_cites
        out += '</tr>'
        return out

    def tmpl_citesummary_minus_self_cites(self, d_total_cites, d_avg_cites,
                                          ln=CFG_SITE_LANG):
        """HTML citesummary format, overview. A part of HCS format suite."""
        _ = gettext_set_language(ln)
        msg = _("Total number of citations excluding self-citations")
        out = """<tr><td><strong>%(msg_cites)s</strong>""" % \
                                                           {'msg_cites': msg, }

        # use ? help linking in the style of oai_repository_admin.py
        msg = ' <small><small>[<a href="%s%s">?</a>]</small></small></td>'
        out += msg % (CFG_BASE_URL,
                      '/help/citation-metrics#citesummary_self-cites')

        for total_cites in d_total_cites.values():
            out += '<td align="right">%s</td>' % \
                                        self.tmpl_nice_number(total_cites, ln)
        out += '</tr>'
        msg = _("Average citations per paper excluding self-citations")
        out += """<tr><td><strong>%(msg_avgcit)s</strong>""" % \
                                                        {'msg_avgcit': msg, }
        # use ? help linking in the style of oai_repository_admin.py
        msg = ' <small><small>[<a href="%s%s">?</a>]</small></small></td>'
        out += msg % (CFG_BASE_URL,
                      '/help/citation-metrics#citesummary_self-cites')

        for avg_cites in d_avg_cites.itervalues():
            out += '<td align="right">%.1f</td>' % avg_cites
        out += '</tr>'
        return out

    def tmpl_citesummary_footer(self):
        return ''

    def tmpl_citesummary_breakdown_header(self, ln=CFG_SITE_LANG):
        _ = gettext_set_language(ln)
        return """<tr><td><strong>%(msg_breakdown)s</strong></td></tr>""" % \
               {'msg_breakdown': _("Breakdown of papers by citations:"), }

    def tmpl_citesummary_breakdown_by_fame(self, d_cites, low, high, fame,
                                           l_colls, searchpatterns,
                                           searchfield, ln=CFG_SITE_LANG):
        """HTML citesummary format, breakdown by fame.

        A part of HCS format suite."""
        _ = gettext_set_language(ln)
        out = """<tr><td>%(fame)s</td>""" % \
              {'fame': _(fame), }
        for coll, colldef in l_colls:
            if 'excluding self cites' in coll:
                keyword = 'citedexcludingselfcites'
            else:
                keyword = 'cited'

            link_url = tmpl_citesummary_get_link_for_rep_breakdown(searchpatterns.get(coll, None), searchfield, colldef, keyword, low, high)
            link_text = self.tmpl_nice_number(d_cites[coll], ln)
            out += '<td align="right"><a href="%s">%s</a></td>' % (link_url,
                                                                   link_text)
        out += '</tr>'
        return out

    def tmpl_citesummary_h_index(self, collections,
                                                d_h_factors, ln=CFG_SITE_LANG):
        """HTML citesummary format, h factor output. A part of the HCS suite."""
        _ = gettext_set_language(ln)
        out = "<tr><td></td></tr><tr><td><strong>%(msg_metrics)s</strong> <small><small>[<a href=\"%(help_url)s\">?</a>]</small></small></td></tr>" % \
              {'msg_metrics': _("Citation metrics"),
               'help_url': CFG_SITE_URL + '/help/citation-metrics', }
        out += '<tr><td>h-index'
        # use ? help linking in the style of oai_repository_admin.py
        msg = ' <small><small>[<a href="%s%s">?</a>]</small></small></td>'
        out += msg % (CFG_BASE_URL,
                      '/help/citation-metrics#citesummary_h-index')
        for coll, dummy in collections:
            h_factors = d_h_factors[coll]
            out += '<td align="right">%s</td>' % \
                                          self.tmpl_nice_number(h_factors, ln)
        out += '</tr>'
        return out

    def tmpl_citesummary_epilogue(self):
        """HTML citesummary format, epilogue. A part of HCS format suite."""
        out = "</table>"
        return out

    def tmpl_unapi(self, formats, identifier=None):
        """
        Provide a list of object format available from the unAPI service
        for the object identified by IDENTIFIER
        """
        out = '<?xml version="1.0" encoding="UTF-8" ?>\n'
        if identifier:
            out += '<formats id="%i">\n' % (identifier)
        else:
            out += "<formats>\n"
        for format_name, format_type in formats.iteritems():
            docs = ''
            if format_name == 'xn':
                docs = 'http://www.nlm.nih.gov/databases/dtd/'
                format_type = 'application/xml'
                format_name = 'nlm'
            elif format_name == 'xm':
                docs = 'http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd'
                format_type = 'application/xml'
                format_name = 'marcxml'
            elif format_name == 'xr':
                format_type = 'application/rss+xml'
                docs = 'http://www.rssboard.org/rss-2-0/'
            elif format_name == 'xw':
                format_type = 'application/xml'
                docs = 'http://www.refworks.com/RefWorks/help/RefWorks_Tagged_Format.htm'
            elif format_name == 'xoaidc':
                format_type = 'application/xml'
                docs = 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd'
            elif format_name == 'xe':
                format_type = 'application/xml'
                docs = 'http://www.endnote.com/support/'
                format_name = 'endnote'
            elif format_name == 'xd':
                format_type = 'application/xml'
                docs = 'http://dublincore.org/schemas/'
                format_name = 'dc'
            elif format_name == 'xo':
                format_type = 'application/xml'
                docs = 'http://www.loc.gov/standards/mods/v3/mods-3-3.xsd'
                format_name = 'mods'
            if docs:
                out += '<format name="%s" type="%s" docs="%s" />\n' % (xml_escape(format_name), xml_escape(format_type), xml_escape(docs))
            else:
                out += '<format name="%s" type="%s" />\n' % (xml_escape(format_name), xml_escape(format_type))
        out += "</formats>"
        return out

    def tmpl_multiple_dois_found_page(self, doi, recids, ln=CFG_SITE_LANG, verbose=0):
        """
        Page displayed when multiple records would match a DOIs

        @param doi: DOI that has multiple matching records
        @param recids: record IDs matched by given C{DOI}
        @param ln: language
        """
        _ = gettext_set_language(ln)
        out = ""
        out += _('For some unknown reason multiple records matching the specified DOI "%s" have been found.') % cgi.escape(doi)
        out += '<br/>' + _('The system administrators have been alerted.')
        out += '<br/>' + _('In the meantime you can pick one of the retrieved candidates:')
        out += '<br/><ul>' + '\n'.join(['<li>' + format_record(recid, of='hb', verbose=verbose) + '<br/>' + \
                                        create_html_link(CFG_SITE_URL + '/' + CFG_SITE_RECORD + '/' + str(recid), \
                                                         {}, _("Detailed record"), {'class': 'moreinfo'}) + \
                                     '</li>' \
                                     for recid in recids]) + \
                     '</ul>'
        return out
