# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014 CERN.
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
# pylint: disable=E1102

"""WebSearch module regression tests."""

__revision__ = "$Id$"

from invenio.testutils import InvenioTestCase, InvenioXmlTestCase
import re
import urlparse, cgi
import sys
import cStringIO

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

from mechanize import Browser, LinkNotFoundError

from invenio.config import (CFG_SITE_URL,
                            CFG_SITE_NAME,
                            CFG_SITE_LANG,
                            CFG_SITE_RECORD,
                            CFG_SITE_LANGS,
                            CFG_SITE_SECURE_URL,
                            CFG_WEBSEARCH_SPIRES_SYNTAX,
                            CFG_BASE_URL)
from invenio.testutils import (make_test_suite,
                               run_test_suite,
                               nottest,
                               make_url,
                               make_surl,
                               make_rurl,
                               test_web_page_content,
                               merge_error_messages,
                               InvenioXmlTestCase)
from invenio.urlutils import same_urls_p
from invenio.dbquery import run_sql
from invenio.webinterface_handler_wsgi import SimulatedModPythonRequest
from invenio.search_engine import perform_request_search, \
    guess_primary_collection_of_a_record, guess_collection_of_a_record, \
    collection_restricted_p, get_permitted_restricted_collections, \
    search_pattern, search_unit, search_unit_in_bibrec, \
    wash_colls, record_public_p
from invenio import search_engine_summarizer
from invenio.search_engine_utils import get_fieldvalues
from invenio.intbitset import intbitset
from invenio.search_engine import intersect_results_with_collrecs
from invenio.bibrank_bridge_utils import get_external_word_similarity_ranker
from invenio.search_engine_query_parser_unit_tests import DATEUTIL_AVAILABLE
from invenio.bibindex_engine_utils import get_index_tags
from invenio.bibindex_engine_config import CFG_BIBINDEX_INDEX_TABLE_TYPE

if 'fr' in CFG_SITE_LANGS:
    lang_french_configured = True
else:
    lang_french_configured = False


def parse_url(url):
    parts = urlparse.urlparse(url)
    query = cgi.parse_qs(parts[4], True)

    return parts[2].split('/')[1:], query

def string_combinations(str_list):
    """Returns all the possible combinations of the strings in the list.
    Example: for the list ['A','B','Cd'], it will return
    [['Cd', 'B', 'A'], ['B', 'A'], ['Cd', 'A'], ['A'], ['Cd', 'B'], ['B'], ['Cd'], []]
    It adds "B", "H", "F" and "S" values to the results so different
    combinations of them are also checked.
    """
    out_list = []
    for i in range(len(str_list) + 1):
        out_list += list(combinations(str_list, i))
    for i in range(len(out_list)):
        out_list[i] = (list(out_list[i]) + {
            0: lambda: ["B", "H", "S"],
            1: lambda: ["B", "H", "F"],
            2: lambda: ["B", "F", "S"],
            3: lambda: ["B", "F"],
            4: lambda: ["B", "S"],
            5: lambda: ["B", "H"],
            6: lambda: ["B"]
        }[i % 7]())
    return out_list

def combinations(iterable, r):
    """Return r length subsequences of elements from the input iterable."""
    # combinations('ABCD', 2) --> AB AC AD BC BD CD
    # combinations(range(4), 3) --> 012 013 023 123
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = range(r)
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] += 1
        for j in range(i+1, r):
            indices[j] = indices[j-1] + 1
        yield tuple(pool[i] for i in indices)

class WebSearchWebPagesAvailabilityTest(InvenioTestCase):
    """Check WebSearch web pages whether they are up or not."""

    def test_search_interface_pages_availability(self):
        """websearch - availability of search interface pages"""

        baseurl = CFG_SITE_URL + '/'

        _exports = ['', 'collection/Poetry', 'collection/Poetry?as=1']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_search_results_pages_availability(self):
        """websearch - availability of search results pages"""

        baseurl = CFG_SITE_URL + '/search'

        _exports = ['', '?c=Poetry', '?p=ellis', '/cache', '/log']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_search_detailed_record_pages_availability(self):
        """websearch - availability of search detailed record pages"""

        baseurl = CFG_SITE_URL + '/'+ CFG_SITE_RECORD +'/'

        _exports = ['', '1', '1/', '1/files', '1/files/']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_browse_results_pages_availability(self):
        """websearch - availability of browse results pages"""

        baseurl = CFG_SITE_URL + '/search'

        _exports = ['?p=ellis&f=author&action_browse=Browse']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_help_page_availability(self):
        """websearch - availability of Help Central page"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/help',
                                               expected_text="Help Central"))

    if lang_french_configured:
        def test_help_page_availability_fr(self):
            """websearch - availability of Help Central page in french"""
            self.assertEqual([],
                             test_web_page_content(CFG_SITE_URL + '/help/?ln=fr',
                                                   expected_text="Centre d'aide"))

    def test_search_tips_page_availability(self):
        """websearch - availability of Search Tips"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/help/search-tips',
                                               expected_text="Search Tips"))

    if lang_french_configured:
        def test_search_tips_page_availability_fr(self):
            """websearch - availability of Search Tips in french"""
            self.assertEqual([],
                             test_web_page_content(CFG_SITE_URL + '/help/search-tips?ln=fr',
                                                   expected_text="Conseils de recherche"))

    def test_search_guide_page_availability(self):
        """websearch - availability of Search Guide"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/help/search-guide',
                                               expected_text="Search Guide"))

    if lang_french_configured:
        def test_search_guide_page_availability_fr(self):
            """websearch - availability of Search Guide in french"""
            self.assertEqual([],
                             test_web_page_content(CFG_SITE_URL + '/help/search-guide?ln=fr',
                                                   expected_text="Guide de recherche"))

class WebSearchTestLegacyURLs(InvenioTestCase):

    """ Check that the application still responds to legacy URLs for
    navigating, searching and browsing."""

    def test_legacy_collections(self):
        """ websearch - collections handle legacy urls """

        browser = Browser()

        def check(legacy, new, browser=browser):
            browser.open(legacy)
            got = browser.geturl()

            self.failUnless(same_urls_p(got, new), got)

        # Use the root URL unless we need more
        check(make_url('/', c=CFG_SITE_NAME),
              make_url('/', ln=CFG_SITE_LANG))

        # Other collections are redirected in the /collection area
        check(make_url('/', c='Poetry'),
              make_url('/collection/Poetry', ln=CFG_SITE_LANG))

        # Drop unnecessary arguments, like ln and as (when they are
        # the default value)
        args = {'as': 0}
        check(make_url('/', c='Poetry', **args),
              make_url('/collection/Poetry', ln=CFG_SITE_LANG))

        # Otherwise, keep them
        args = {'as': 1, 'ln': CFG_SITE_LANG}
        check(make_url('/', c='Poetry', **args),
              make_url('/collection/Poetry', **args))

        # Support the /index.py addressing too
        check(make_url('/index.py', c='Poetry'),
              make_url('/collection/Poetry', ln=CFG_SITE_LANG))


    def test_legacy_search(self):
        """ websearch - search queries handle legacy urls """

        browser = Browser()

        def check(legacy, new, browser=browser):
            browser.open(legacy)
            got = browser.geturl()

            self.failUnless(same_urls_p(got, new), got)

        # /search.py is redirected on /search
        # Note that `as' is a reserved word in Python 2.5
        check(make_url('/search.py', p='nuclear', ln='en') + 'as=1',
              make_url('/search', p='nuclear', ln='en') + 'as=1')

    if lang_french_configured:
        def test_legacy_search_fr(self):
            """ websearch - search queries handle legacy urls """

            browser = Browser()

            def check(legacy, new, browser=browser):
                browser.open(legacy)
                got = browser.geturl()

                self.failUnless(same_urls_p(got, new), got)

            # direct recid searches are redirected to /CFG_SITE_RECORD
            check(make_url('/search.py', recid=1, ln='fr'),
                  make_url('/%s/1' % CFG_SITE_RECORD, ln='fr'))

    def test_legacy_search_help_link(self):
        """websearch - legacy Search Help page link"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/help/search/index.en.html',
                                               expected_text="Help Central"))

    if lang_french_configured:
        def test_legacy_search_tips_link(self):
            """websearch - legacy Search Tips page link"""
            self.assertEqual([],
                             test_web_page_content(CFG_SITE_URL + '/help/search/tips.fr.html',
                                                   expected_text="Conseils de recherche"))

    def test_legacy_search_guide_link(self):
        """websearch - legacy Search Guide page link"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/help/search/guide.en.html',
                                               expected_text="Search Guide"))

class WebSearchTestRecord(InvenioTestCase):
    """ Check the interface of the /CFG_SITE_RECORD results """

    def test_format_links(self):
        """ websearch - check format links for records """

        browser = Browser()

        # We open the record in all known HTML formats
        for hformat in ('hd', 'hx', 'hm'):
            browser.open(make_url('/%s/1' % CFG_SITE_RECORD, of=hformat))

            if hformat == 'hd':
                # hd format should have a link to the following
                # formats
                for oformat in ('hx', 'hm', 'xm', 'xd'):
                    target = '%s/%s/1/export/%s?ln=en' % \
                             (CFG_BASE_URL, CFG_SITE_RECORD, oformat)
                    try:
                        browser.find_link(url=target)
                    except LinkNotFoundError:
                        self.fail('link %r should be in page' % target)
            else:
                # non-hd HTML formats should have a link back to
                # the main detailed record
                target = '%s/%s/1' % (CFG_BASE_URL, CFG_SITE_RECORD)
                try:
                    browser.find_link(url=target)
                except LinkNotFoundError:
                    self.fail('link %r should be in page' % target)

        return

    def test_exported_formats(self):
        """ websearch - check formats exported through /CFG_SITE_RECORD/1/export/ URLs"""

        self.assertEqual([],
                         test_web_page_content(make_url('/%s/1/export/hm' % CFG_SITE_RECORD),
                                               expected_text='245__ $$aALEPH experiment'))
        self.assertEqual([],
                         test_web_page_content(make_url('/%s/1/export/hd' % CFG_SITE_RECORD),
                                               expected_text='<strong>ALEPH experiment'))
        self.assertEqual([],
                         test_web_page_content(make_url('/%s/1/export/xm' % CFG_SITE_RECORD),
                                               expected_text='<subfield code="a">ALEPH experiment'))
        self.assertEqual([],
                         test_web_page_content(make_url('/%s/1/export/xd' % CFG_SITE_RECORD),
                                               expected_text='<dc:title>ALEPH experiment'))
        self.assertEqual([],
                         test_web_page_content(make_url('/%s/1/export/hs' % CFG_SITE_RECORD),
                                               expected_text='<a href="/%s/1?ln=%s">ALEPH experiment' % \
                                               (CFG_SITE_RECORD, CFG_SITE_LANG)))
        self.assertEqual([],
                         test_web_page_content(make_url('/%s/1/export/hx' % CFG_SITE_RECORD),
                                               expected_text='title         = "{ALEPH experiment'))
        self.assertEqual([],
                         test_web_page_content(make_url('/%s/1/export/t?ot=245' % CFG_SITE_RECORD),
                                               expected_text='245__ $$aALEPH experiment'))
        self.assertNotEqual([],
                         test_web_page_content(make_url('/%s/1/export/t?ot=245' % CFG_SITE_RECORD),
                                               expected_text='001__'))
        self.assertEqual([],
                         test_web_page_content(make_url('/%s/1/export/h?ot=245' % CFG_SITE_RECORD),
                                               expected_text='245__ $$aALEPH experiment'))
        self.assertNotEqual([],
                         test_web_page_content(make_url('/%s/1/export/h?ot=245' % CFG_SITE_RECORD),
                                               expected_text='001__'))
        return

    def test_plots_tab(self):
        """ websearch - test to ensure the plots tab is working """
        self.assertEqual([],
                         test_web_page_content(make_url('/%s/8/plots' % CFG_SITE_RECORD),
                                               expected_text='div id="clip"',
                                               unexpected_text='Abstract'))
    def test_meta_header(self):
        """ websearch - test that metadata embedded in header of hd
        relies on hdm format and Default_HTML_meta bft, but hook is in
        websearch to display the format
        """

        self.assertEqual([],
                         test_web_page_content(make_url('/record/1'),
                                               expected_text='<meta content="ALEPH experiment: Candidate of Higgs boson production" name="citation_title" />'))
        return


class WebSearchTestCollections(InvenioTestCase):

    def test_traversal_links(self):
        """ websearch - traverse all the publications of a collection """

        browser = Browser()

        try:
            for aas in (0, 1):
                args = {'as': aas}
                browser.open(make_url('/collection/Preprints', **args))

                for jrec in (11, 21, 11, 27):
                    args = {'jrec': jrec, 'cc': 'Preprints'}
                    if aas:
                        args['as'] = aas

                    url = make_rurl('/search', **args)
                    try:
                        browser.follow_link(url=url)
                    except LinkNotFoundError:
                        args['ln'] = CFG_SITE_LANG
                        url = make_rurl('/search', **args)
                        browser.follow_link(url=url)

        except LinkNotFoundError:
            self.fail('no link %r in %r' % (url, browser.geturl()))

    def test_collections_links(self):
        """ websearch - enter in collections and subcollections """

        browser = Browser()

        def tryfollow(url):
            cur = browser.geturl()
            body = browser.response().read()
            try:
                browser.follow_link(url=url)
            except LinkNotFoundError:
                print body
                self.fail("in %r: could not find %r" % (
                    cur, url))
            return

        for aas in (0, 1):
            if aas:
                kargs = {'as': 1}
            else:
                kargs = {}

            kargs['ln'] = CFG_SITE_LANG

            # We navigate from immediate son to immediate son...
            browser.open(make_url('/', **kargs))
            tryfollow(make_rurl('/collection/Articles%20%26%20Preprints',
                                **kargs))
            tryfollow(make_rurl('/collection/Articles', **kargs))

            # But we can also jump to a grandson immediately
            browser.back()
            browser.back()
            tryfollow(make_rurl('/collection/ALEPH', **kargs))

        return

    def test_records_links(self):
        """ websearch - check the links toward records in leaf collections """

        browser = Browser()
        browser.open(make_url('/collection/Preprints'))

        def harvest():

            """ Parse all the links in the page, and check that for
            each link to a detailed record, we also have the
            corresponding link to the similar records."""

            records = set()
            similar = set()

            for link in browser.links():
                path, q = parse_url(link.url)

                if not path:
                    continue

                if path[0] == CFG_SITE_RECORD:
                    records.add(int(path[1]))
                    continue

                if path[0] == 'search':
                    if not q.get('rm') == ['wrd']:
                        continue

                    recid = q['p'][0].split(':')[1]
                    similar.add(int(recid))

            self.failUnlessEqual(records, similar)

            return records

        # We must have 10 links to the corresponding /CFG_SITE_RECORD
        found = harvest()
        self.failUnlessEqual(len(found), 10)

        # When clicking on the "Search" button, we must also have
        # these 10 links on the records.
        browser.select_form(name="search")
        browser.submit()

        found = harvest()
        self.failUnlessEqual(len(found), 10)
        return

    def test_em_parameter(self):
        """ websearch - check different values of em return different parts of the collection page"""
        for combi in string_combinations(["L", "P", "Prt"]):
            url = '/collection/Articles?em=%s' % ','.join(combi)
            expected_text = ["<strong>Development of photon beam diagnostics for VUV radiation from a SASE FEL</strong>"]
            unexpected_text = []
            if "H" in combi:
                expected_text.append(">Atlantis Institute of Fictive Science</a>")
            else:
                unexpected_text.append(">Atlantis Institute of Fictive Science</a>")
            if "F" in combi:
                expected_text.append("This site is also available in the following languages:")
            else:
                unexpected_text.append("This site is also available in the following languages:")
            if "S" in combi:
                expected_text.append('value="Search"')
            else:
                unexpected_text.append('value="Search"')
            if "L" in combi:
                expected_text.append('Search also:')
            else:
                unexpected_text.append('Search also:')
            if "Prt" in combi or "P" in combi:
                expected_text.append('<div class="portalboxheader">ABOUT ARTICLES</div>')
            else:
                unexpected_text.append('<div class="portalboxheader">ABOUT ARTICLES</div>')
            self.assertEqual([], test_web_page_content(make_url(url),
                                           expected_text=expected_text,
                                           unexpected_text=unexpected_text))

    def test_canonical_and_alternate_urls_quoting(self):
        """ websearch - check that canonical and alternate URL in collection page header are properly quoted"""
        url = CFG_SITE_URL + '/collection/Experimental%20Physics%20%28EP%29?ln=en'
        expected_text = ['<link rel="alternate" hreflang="en" href="' + CFG_SITE_URL + '/collection/Experimental%20Physics%20%28EP%29?ln=en" />',
                         '<link rel="canonical" href="' + CFG_SITE_URL + '/collection/Experimental%20Physics%20%28EP%29" />']
        unexpected_text = ['<link rel="alternate" hreflang="en" href="' + CFG_SITE_URL + '/collection/Experimental Physics (EP)?ln=en" />',
                           '<link rel="canonical" href="' + CFG_SITE_URL + '/collection/Experimental Physics (EP)" />']

        self.assertEqual([], test_web_page_content(url,
                                                   expected_text=expected_text,
                                                   unexpected_text=unexpected_text))

class WebSearchTestBrowse(InvenioTestCase):

    def test_browse_field(self):
        """ websearch - check that browsing works """

        browser = Browser()
        browser.open(make_url('/', ln="en"))

        browser.select_form(name='search')
        browser['f'] = ['title']
        browser.submit(name='action_browse')

        def collect():
            # We'll get a few links to search for the actual hits, plus a
            # link to the following results.
            res = []
            for link in browser.links():
                if not link.url.startswith("%s/search" % (CFG_BASE_URL,)):
                    continue

                if "as=1" in link.url or "action=browse" in link.url:
                    continue

                for attr in link.attrs:
                    if "class" in attr:
                        break
                else:
                    dummy, q = parse_url(link.url)
                    res.append((link, q))
            return res

        # Here we should have 4 links to different records
        batch_1 = collect()
        self.assertEqual(4, len(batch_1))

        # if we follow the next link, we should get another
        # batch of 4. There is an overlap of one item.
        next_link = [l for l in browser.links() if l.text == "next"][0]
        browser.follow_link(link=next_link)
        batch_2 = collect()
        self.assertEqual(8, len(batch_2))

        # FIXME: we cannot compare the whole query, as the collection
        # set is not equal
        # Expecting "A naturalist\'s voyage around the world"
        # Last link in batch_1 should equal the 4th link in batch_2
        self.failUnlessEqual(batch_1[-1][1]['p'], batch_2[3][1]['p'])

    def test_browse_restricted_record_as_unauthorized_user(self):
        """websearch - browse for a record that belongs to a restricted collection as an unauthorized user."""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?p=CERN-THESIS-99-074&f=088__a&action_browse=Browse&ln=en',
                                               username = 'guest',
                                               expected_text = ['Hits', '088__a'],
                                               unexpected_text = ['>CERN-THESIS-99-074</a>'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_browse_restricted_record_as_unauthorized_user_in_restricted_collection(self):
        """websearch - browse for a record that belongs to a restricted collection as an unauthorized user."""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?p=CERN-THESIS-99-074&f=088__a&action_browse=Browse&c=ALEPH+Theses&ln=en',
                                               username='guest',
                                               expected_text= ['This collection is restricted'],
                                               unexpected_text= ['Hits', '>CERN-THESIS-99-074</a>'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_browse_restricted_record_as_authorized_user(self):
        """websearch - browse for a record that belongs to a restricted collection as an authorized user."""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?p=CERN-THESIS-99-074&f=088__a&action_browse=Browse&ln=en',
                                               username='admin',
                                               password='',
                                               expected_text= ['Hits', '088__a'],
                                               unexpected_text = ['>CERN-THESIS-99-074</a>'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_browse_restricted_record_as_authorized_user_in_restricted_collection(self):
        """websearch - browse for a record that belongs to a restricted collection as an authorized user."""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?p=CERN-THESIS-99-074&f=088__a&action_browse=Browse&c=ALEPH+Theses&ln=en',
                                               username='admin',
                                               password='',
                                               expected_text= ['Hits', '>CERN-THESIS-99-074</a>'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_browse_exact_author_help_link(self):
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=Dasse%2C+Michel&f=author&action_browse=Browse',
                                               username = 'guest',
                                               expected_text = ['Did you mean to browse in', 'index?'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=Dasse%2C+Michel&f=firstauthor&action_browse=Browse',
                                               username = 'guest',
                                               expected_text = ['Did you mean to browse in', 'index?'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&as=1&m1=a&p1=Dasse%2C+Michel&f1=author&op1=a&m2=a&p2=&f2=firstauthor&op2=a&m3=a&p3=&f3=&action_browse=Browse',
                                               username = 'guest',
                                               expected_text = ['Did you mean to browse in', 'index?'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))


class WebSearchTestOpenURL(InvenioTestCase):

    def test_isbn_01(self):
        """ websearch - isbn query via OpenURL 0.1"""

        browser = Browser()

        # We do a precise search in an isolated collection
        browser.open(make_url('/openurl', isbn='0387940758'))

        dummy, current_q = parse_url(browser.geturl())

        self.failUnlessEqual(current_q, {
            'sc' : ['1'],
            'p' : ['isbn:"0387940758"'],
            'of' : ['hd']
        })

    def test_isbn_10_rft_id(self):
        """ websearch - isbn query via OpenURL 1.0 - rft_id"""

        browser = Browser()

        # We do a precise search in an isolated collection
        browser.open(make_url('/openurl', rft_id='urn:ISBN:0387940758'))

        dummy, current_q = parse_url(browser.geturl())

        self.failUnlessEqual(current_q, {
            'sc' : ['1'],
            'p' : ['isbn:"0387940758"'],
            'of' : ['hd']
        })

    def test_isbn_10(self):
        """ websearch - isbn query via OpenURL 1.0"""

        browser = Browser()

        # We do a precise search in an isolated collection
        browser.open(make_url('/openurl?rft.isbn=0387940758'))

        dummy, current_q = parse_url(browser.geturl())

        self.failUnlessEqual(current_q, {
            'sc' : ['1'],
            'p' : ['isbn:"0387940758"'],
            'of' : ['hd']
        })


class WebSearchTestSearch(InvenioTestCase):

    def test_hits_in_other_collection(self):
        """ websearch - check extension of a query to the home collection """

        browser = Browser()

        # We do a precise search in an isolated collection
        browser.open(make_url('/collection/ISOLDE', ln='en'))

        browser.select_form(name='search')
        browser['f'] = ['author']
        browser['p'] = 'matsubara'
        browser.submit()

        dummy, current_q = parse_url(browser.geturl())

        link = browser.find_link(text_regex=re.compile('.*hit', re.I))
        dummy, target_q = parse_url(link.url)

        # the target query should be the current query without any c
        # or cc specified.
        for f in ('cc', 'c', 'action_search'):
            if f in current_q:
                del current_q[f]

        self.failUnlessEqual(current_q, target_q)

    def test_nearest_terms(self):
        """ websearch - provide a list of nearest terms """

        browser = Browser()
        browser.open(make_url(''))

        # Search something weird
        browser.select_form(name='search')
        browser['p'] = 'gronf'
        browser.submit()

        dummy, original = parse_url(browser.geturl())

        for to_drop in ('cc', 'action_search', 'f'):
            if to_drop in original:
                del original[to_drop]

        if 'ln' not in original:
            original['ln'] = [CFG_SITE_LANG]

        # we should get a few searches back, which are identical
        # except for the p field being substituted (and the cc field
        # being dropped).
        if 'cc' in original:
            del original['cc']

        for link in browser.links(url_regex=re.compile(CFG_SITE_URL + r'/search\?')):
            if link.text == 'Advanced Search':
                continue

            dummy, target = parse_url(link.url)

            if 'ln' not in target:
                target['ln'] = [CFG_SITE_LANG]

            original['p'] = [link.text]
            self.failUnlessEqual(original, target)

        return

    def test_switch_to_simple_search(self):
        """ websearch - switch to simple search """

        browser = Browser()
        args = {'as': 1}
        browser.open(make_url('/collection/ISOLDE', **args))

        browser.select_form(name='search')
        browser['p1'] = 'tandem'
        browser['f1'] = ['title']
        browser.submit()

        browser.follow_link(text='Simple Search')

        dummy, q = parse_url(browser.geturl())

        self.failUnlessEqual(q, {'cc': ['ISOLDE'],
                                 'p': ['tandem'],
                                 'f': ['title'],
                                 'ln': ['en']})

    def test_switch_to_advanced_search(self):
        """ websearch - switch to advanced search """

        browser = Browser()
        browser.open(make_url('/collection/ISOLDE'))

        browser.select_form(name='search')
        browser['p'] = 'tandem'
        browser['f'] = ['title']
        browser.submit()

        browser.follow_link(text='Advanced Search')

        dummy, q = parse_url(browser.geturl())

        self.failUnlessEqual(q, {'cc': ['ISOLDE'],
                                 'p1': ['tandem'],
                                 'f1': ['title'],
                                 'as': ['1'],
                                 'ln' : ['en']})

    def test_no_boolean_hits(self):
        """ websearch - check the 'no boolean hits' proposed links """

        browser = Browser()
        browser.open(make_url(''))

        browser.select_form(name='search')
        browser['p'] = 'quasinormal muon'
        browser.submit()

        dummy, q = parse_url(browser.geturl())

        for to_drop in ('cc', 'action_search', 'f'):
            if to_drop in q:
                del q[to_drop]

        for bsu in ('quasinormal', 'muon'):
            l = browser.find_link(text=bsu)
            q['p'] = bsu

            if not same_urls_p(l.url, make_rurl('/search', **q)):
                self.fail(repr((l.url, make_rurl('/search', **q))))

    def test_similar_authors(self):
        """ websearch - test similar authors box """

        browser = Browser()
        browser.open(make_url(''))

        browser.select_form(name='search')
        browser['p'] = 'Ellis, R K'
        browser['f'] = ['author']
        browser.submit()

        l = browser.find_link(text="Ellis, R S")
        urlargs = dict(p="Ellis, R S", f='author', ln='en')
        self.failUnless(same_urls_p(l.url, make_rurl('/search', **urlargs)))

    def test_em_parameter(self):
        """ websearch - check different values of em return different parts of the search page"""
        for combi in string_combinations(["K", "A", "I", "O"]):
            url = '/search?ln=en&cc=Articles+%%26+Preprints&sc=1&c=Articles&c=Preprints&em=%s' % ','.join(combi)
            expected_text = ["<strong>Development of photon beam diagnostics for VUV radiation from a SASE FEL</strong>"]
            unexpected_text = []
            if "H" in combi:
                expected_text.append(">Atlantis Institute of Fictive Science</a>")
            else:
                unexpected_text.append(">Atlantis Institute of Fictive Science</a>")
            if "F" in combi:
                expected_text.append("This site is also available in the following languages:")
            else:
                unexpected_text.append("This site is also available in the following languages:")
            if "S" in combi:
                expected_text.append('value="Search"')
            else:
                unexpected_text.append('value="Search"')
            if "K" in combi:
                expected_text.append('value="Add to basket"')
            else:
                unexpected_text.append('value="Add to basket"')
            if "A" in combi:
                expected_text.append('Interested in being notified about new results for this query?')
            else:
                unexpected_text.append('Interested in being notified about new results for this query?')
            if "I" in combi:
                expected_text.append('jump to record:')
            else:
                unexpected_text.append('jump to record:')
            if "O" in combi:
                expected_text.append('<th class="searchresultsboxheader"><strong>Results overview:</strong> Found <strong>')
            else:
                unexpected_text.append('<th class="searchresultsboxheader"><strong>Results overview:</strong> Found <strong>')
            self.assertEqual([], test_web_page_content(make_url(url),
                                           expected_text=expected_text,
                                           unexpected_text=unexpected_text))
        return


class WebSearchCJKTokenizedSearchTest(InvenioTestCase):
    """
        Reindexes record 104 (the one with chinese poetry) with use of BibIndexCJKTokenizer.
        After tests it reindexes record 104 back with BibIndexDefaultTokenizer.
        Checks if one can find record 104 specifying only one or two CJK characters.
    """

    test_counter = 0
    reindexed = False
    index_name = 'title'

    @classmethod
    def setUp(self):
        if not self.reindexed:
            from invenio.bibindex_engine import WordTable, AbstractIndexTable
            query = """SELECT last_updated FROM idxINDEX WHERE name='%s'""" % self.index_name
            self.last_updated = run_sql(query)[0][0]
            query = """UPDATE idxINDEX SET tokenizer='BibIndexCJKTokenizer', last_updated='0000-00-00 00:00:00'
                       WHERE name='%s'""" % self.index_name
            run_sql(query)
            self.reindexed = True
            wordTable = WordTable(index_name=self.index_name,
                                  table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"])
            wordTable.turn_off_virtual_indexes()
            wordTable.add_recIDs([[104, 104]], 10000)

    @classmethod
    def tearDown(self):
        self.test_counter += 1
        if self.test_counter == 2:
            from invenio.bibindex_engine import WordTable, AbstractIndexTable
            query = """UPDATE idxINDEX SET tokenizer='BibIndexDefaultTokenizer', last_updated='%s'
                       WHERE name='%s'""" % (self.last_updated, self.index_name)
            run_sql(query)
            wordTable = WordTable(index_name=self.index_name,
                                  table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"])
            wordTable.turn_off_virtual_indexes()
            wordTable.add_recIDs([[104, 104]], 10000)

    def test_title_cjk_tokenized_two_characters(self):
        """CJKTokenizer - test for finding chinese poetry with two CJK characters"""
        self.assertEqual([], test_web_page_content(CFG_SITE_URL + '/search?ln=en&sc=1&p=title%3A敬亭&f=&of=id',
                                                   expected_text='[104]'))

    def test_title_cjk_tokenized_single_character(self):
        """CJKTokenizer - test for finding chinese poetry with one CJK character"""
        self.assertEqual([], test_web_page_content(CFG_SITE_URL + '/search?ln=en&sc=1&p=title%3A亭&f=&of=id',
                                                   expected_text='[104]'))


class WebSearchTestWildcardLimit(InvenioTestCase):
    """Checks if the wildcard limit is correctly passed and that
    users without autorization can not exploit it"""

    def test_wildcard_limit_correctly_passed_when_not_set(self):
        """websearch - wildcard limit is correctly passed when default"""
        self.assertEqual(search_pattern(p='e*', f='author'),
                         search_pattern(p='e*', f='author', wl=1000))

    def test_wildcard_limit_correctly_passed_when_set(self):
        """websearch - wildcard limit is correctly passed when set"""
        self.assertEqual([],
            test_web_page_content(CFG_SITE_URL + '/search?p=e*&f=author&of=id&wl=5&rg=100',
                                  expected_text=[],
                                  unexpected_text="[96, 92, 88, 81, 74, 72, 71, 67, 55, 54, 53, 52, 51, 50, 48, 47, 46, 44, 18, 17, 16, 14, 13, 12, 11, 10, 9, 8]"))

    def test_wildcard_limit_correctly_not_active(self):
        """websearch - wildcard limit is not active when there is no wildcard query"""
        self.assertEqual(search_pattern(p='ellis', f='author'),
                         search_pattern(p='ellis', f='author', wl=1))

    def test_wildcard_limit_increased_by_authorized_users(self):
        """websearch - wildcard limit increased by authorized user"""

        browser = Browser()

        #try a search query, with no wildcard limit set by the user
        browser.open(make_url('/search?p=a*&of=id'))
        recid_list_guest_no_limit = browser.response().read() # so the limit is CGF_WEBSEARCH_WILDCARD_LIMIT

        #try a search query, with a wildcard limit imposed by the user
        #wl=1000000 - a very high limit,higher then what the CFG_WEBSEARCH_WILDCARD_LIMIT might be
        browser.open(make_url('/search?p=a*&of=id&wl=1000000'))
        recid_list_guest_with_limit = browser.response().read()

        #same results should be returned for a search without the wildcard limit set by the user
        #and for a search with a large limit set by the user
        #in this way we know that nomatter how large the limit is, the wildcard query will be
        #limitted by CFG_WEBSEARCH_WILDCARD_LIMIT (for a guest user)
        self.failIf(len(recid_list_guest_no_limit.split(',')) != len(recid_list_guest_with_limit.split(',')))

        ##login as admin
        browser.open(make_surl('/youraccount/login'))
        browser.select_form(nr=0)
        browser['p_un'] = 'admin'
        browser['p_pw'] = ''
        browser.submit()

        #try a search query, with a wildcard limit imposed by an authorized user
        #wl = 10000 a very high limit, higher then what the CFG_WEBSEARCH_WILDCARD_LIMIT might be
        browser.open(make_surl('/search?p=a*&of=id&wl=10000'))
        recid_list_authuser_with_limit = browser.response().read()

        #the authorized user can set whatever limit he might wish
        #so, the results returned for the auth. users should exceed the results returned for unauth. users
        self.failUnless(len(recid_list_guest_no_limit.split(',')) <= len(recid_list_authuser_with_limit.split(',')))

        #logout
        browser.open(make_surl('/youraccount/logout'))
        browser.response().read()
        browser.close()

class WebSearchNearestTermsTest(InvenioTestCase):
    """Check various alternatives of searches leading to the nearest
    terms box."""

    def test_nearest_terms_box_in_okay_query(self):
        """ websearch - no nearest terms box for a successful query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis',
                                               expected_text="jump to record"))

    def test_nearest_terms_box_in_unsuccessful_simple_query(self):
        """ websearch - nearest terms box for unsuccessful simple query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellisz',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=embed",
                                               expected_link_label='embed'))

    def test_nearest_terms_box_in_unsuccessful_simple_accented_query(self):
        """ websearch - nearest terms box for unsuccessful accented query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=elliszà',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=embed",
                                               expected_link_label='embed'))

    def test_nearest_terms_box_in_unsuccessful_structured_query(self):
        """ websearch - nearest terms box for unsuccessful structured query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellisz&f=author',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=eisenhandler&f=author",
                                               expected_link_label='eisenhandler'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=author%3Aellisz',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=author%3Aeisenhandler",
                                               expected_link_label='eisenhandler'))


    def test_nearest_terms_box_in_query_with_invalid_index(self):
        """ websearch - nearest terms box for queries with invalid indexes specified """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=bednarz%3Aellis',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=bednarz",
                                               expected_link_label='bednarz'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=1%3Aellis',
                                               expected_text="no index 1.",
                                               expected_link_target=CFG_BASE_URL+"/record/47?ln=en",
                                               expected_link_label="Detailed record"))

    def test_nearest_terms_box_in_unsuccessful_phrase_query(self):
        """ websearch - nearest terms box for unsuccessful phrase query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=author%3A%22Ellis%2C+Z%22',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=author%3A%22Enqvist%2C+K%22",
                                               expected_link_label='Enqvist, K'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%22ellisz%22&f=author',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=%22Enqvist%2C+K%22&f=author",
                                               expected_link_label='Enqvist, K'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%22elliszà%22&f=author',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=%22Enqvist%2C+K%22&f=author",
                                               expected_link_label='Enqvist, K'))

    def test_nearest_terms_box_in_unsuccessful_partial_phrase_query(self):
        """ websearch - nearest terms box for unsuccessful partial phrase query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=author%3A%27Ellis%2C+Z%27',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=author%3A%27Enqvist%2C+K%27",
                                               expected_link_label='Enqvist, K'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%27ellisz%27&f=author',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=%27Enqvist%2C+K%27&f=author",
                                               expected_link_label='Enqvist, K'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%27elliszà%27&f=author',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=%27Enqvist%2C+K%27&f=author",
                                               expected_link_label='Enqvist, K'))

    def test_nearest_terms_box_in_unsuccessful_partial_phrase_advanced_query(self):
        """ websearch - nearest terms box for unsuccessful partial phrase advanced search query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p1=aaa&f1=title&m1=p&as=1',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&f1=title&as=1&p1=A+simple+functional+form+for+proton-nucleus+total+reaction+cross+sections&m1=p",
                                               expected_link_label='A simple functional form for proton-nucleus total reaction cross sections'))

    def test_nearest_terms_box_in_unsuccessful_exact_phrase_advanced_query(self):
        """ websearch - nearest terms box for unsuccessful exact phrase advanced search query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p1=aaa&f1=title&m1=e&as=1',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&f1=title&as=1&p1=A+simple+functional+form+for+proton-nucleus+total+reaction+cross+sections&m1=e",
                                               expected_link_label='A simple functional form for proton-nucleus total reaction cross sections'))

    def test_nearest_terms_box_in_unsuccessful_boolean_query(self):
        """ websearch - nearest terms box for unsuccessful boolean query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=title%3Aellisz+author%3Aellisz',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=title%3Aenergi+author%3Aellisz",
                                               expected_link_label='energi'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=title%3Aenergi+author%3Aenergie',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=title%3Aenergi+author%3Aenqvist",
                                               expected_link_label='enqvist'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=title%3Aellisz+author%3Aellisz&f=keyword',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=title%3Aenergi+author%3Aellisz&f=keyword",
                                               expected_link_label='energi'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=title%3Aenergi+author%3Aenergie&f=keyword',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=title%3Aenergi+author%3Aenqvist&f=keyword",
                                               expected_link_label='enqvist'))

    def test_nearest_terms_box_in_unsuccessful_uppercase_query(self):
        """ websearch - nearest terms box for unsuccessful uppercase query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=fOo%3Atest',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=food",
                                               expected_link_label='food'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=arXiv%3A1007.5048',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=artist",
                                               expected_link_label='artist'))

    def test_nearest_terms_box_in_unsuccessful_spires_query(self):
        """ websearch - nearest terms box for unsuccessful spires query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=find+a+foobar',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=find+a+finch",
                                               expected_link_label='finch'))


class WebSearchBooleanQueryTest(InvenioTestCase):
    """Check various boolean queries."""

    def test_successful_boolean_query(self):
        """ websearch - successful boolean query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis+muon',
                                               expected_text="records found",
                                               expected_link_label="Detailed record"))

    def test_unsuccessful_boolean_query_where_all_individual_terms_match(self):
        """ websearch - unsuccessful boolean query where all individual terms match """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis+muon+letter',
                                               expected_text="Boolean query returned no hits. Please combine your search terms differently."))

    def test_unsuccessful_boolean_query_in_advanced_search_where_all_individual_terms_match(self):
        """ websearch - unsuccessful boolean query in advanced search where all individual terms match """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?m1=a&p1=ellis&op1=a&m2=a&p2=muon&op2=a&p3=letter',
                                               expected_text="Boolean query returned no hits. Please combine your search terms differently."))


class WebSearchAuthorQueryTest(InvenioTestCase):
    """Check various author-related queries."""

    def test_propose_similar_author_names_box(self):
        """ websearch - propose similar author names box """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=Ellis%2C+R&f=author',
                                               expected_text="See also: similar author names",
                                               expected_link_target=CFG_BASE_URL+"/search?ln=en&p=Ellis%2C+R+K&f=author",
                                               expected_link_label="Ellis, R K"))

    def test_do_not_propose_similar_author_names_box(self):
        """ websearch - do not propose similar author names box """
        errmsgs = test_web_page_content(CFG_SITE_URL + '/search?p=author%3A%22Ellis%2C+R%22',
                                        expected_link_target=CFG_BASE_URL+"/search?ln=en&p=Ellis%2C+R+K&f=author",
                                        expected_link_label="Ellis, R K")
        if errmsgs[0].find("does not contain link to") > -1:
            pass
        else:
            self.fail("Should not propose similar author names box.")
        return

class WebSearchSearchEnginePythonAPITest(InvenioXmlTestCase):
    """Check typical search engine Python API calls on the demo data."""

    def test_search_engine_python_api_for_failed_query(self):
        """websearch - search engine Python API for failed query"""
        self.assertEqual([],
                         perform_request_search(p='aoeuidhtns'))

    def test_search_engine_python_api_for_successful_query(self):
        """websearch - search engine Python API for successful query"""
        self.assertEqual([8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 47],
                         perform_request_search(p='ellis'))

    def test_search_engine_python_api_for_successful_query_format_intbitset(self):
        """websearch - search engine Python API for successful query, output format intbitset"""
        self.assertEqual(intbitset([8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 47]),
                         perform_request_search(p='ellis', of='intbitset'))

    def test_search_engine_web_api_jrec_parameter(self):
        """websearch - search engine Python API for successful query, ignore paging parameters"""
        self.assertEqual([11, 12, 13, 14, 15, 16, 17, 18, 47],
                         perform_request_search(p='ellis', jrec=3))

    def test_search_engine_web_api_paging_parameters(self):
        """websearch - search engine Python API for successful query, ignore paging parameters"""
        self.assertEqual([11, 12, 13, 14, 15],
                         perform_request_search(p='ellis', rg=5, jrec=3))

    def test_search_engine_python_api_respect_sorting_parameter(self):
        """websearch - search engine Python API for successful query, respect sorting parameters"""
        self.assertEqual([77, 84, 85],
                         perform_request_search(p='klebanov'))
        self.assertEqual([77, 85, 84],
                         perform_request_search(p='klebanov', sf='909C4v'))

    def test_search_engine_python_api_respect_ranking_parameter(self):
        """websearch - search engine Python API for successful query, respect ranking parameters"""
        self.assertEqual([77, 84, 85],
                         perform_request_search(p='klebanov'))
        self.assertEqual([85, 77, 84],
                         perform_request_search(p='klebanov', rm='citation'))

    def test_search_engine_python_api_for_existing_record(self):
        """websearch - search engine Python API for existing record"""
        self.assertEqual([8],
                         perform_request_search(recid=8))

    def test_search_engine_python_api_for_existing_record_format_intbitset(self):
        """websearch - search engine Python API for existing record, output format intbitset"""
        self.assertEqual(intbitset([8]),
                         perform_request_search(recid=8, of='intbitset'))

    def test_search_engine_python_api_for_nonexisting_record(self):
        """websearch - search engine Python API for non-existing record"""
        self.assertEqual([],
                         perform_request_search(recid=12345678))

    def test_search_engine_python_api_for_nonexisting_record_format_intbitset(self):
        """websearch - search engine Python API for non-existing record, output format intbitset"""
        self.assertEqual(intbitset(),
                         perform_request_search(recid=16777215, of='intbitset'))

    def test_search_engine_python_api_for_nonexisting_collection(self):
        """websearch - search engine Python API for non-existing collection"""
        self.assertEqual([],
                         perform_request_search(c='Foo'))

    def test_search_engine_python_api_for_range_of_records(self):
        """websearch - search engine Python API for range of records"""
        self.assertEqual([1, 2, 3, 4, 5, 6, 7, 8, 9],
                         perform_request_search(recid=1, recidb=10))

    def test_search_engine_python_api_old_style_ranked_by_citation(self):
        """websearch - search engine Python API old style citation ranking"""
        self.assertEqual([86, 77],
                perform_request_search(p='recid:95', rm='citation'))

    def test_search_engine_python_api_textmarc_full(self):
        """websearch - search engine Python API for Text MARC output, full"""
        req = make_fake_request()
        perform_request_search(req=req, p='higgs', of='tm', so='d')
        out = req.test_output_buffer.getvalue()
        self.assertMultiLineEqual(out, """\
000000107 001__ 107
000000107 003__ SzGeCERN
000000107 005__ %(rec_107_rev)s
000000107 035__ $$9SPIRES$$a4066995
000000107 037__ $$aCERN-EP-99-060
000000107 041__ $$aeng
000000107 084__ $$2CERN Library$$aEP-1999-060
000000107 088__ $$9SCAN-9910048
000000107 088__ $$aCERN-L3-175
000000107 110__ $$aCERN. Geneva
000000107 245__ $$aLimits on Higgs boson masses from combining the data of the four LEP experiments at $\sqrt{s} \leq 183 GeV$
000000107 260__ $$c1999
000000107 269__ $$aGeneva$$bCERN$$c26 Apr 1999
000000107 300__ $$a18 p
000000107 490__ $$aALEPH Papers
000000107 500__ $$aPreprint not submitted to publication
000000107 65017 $$2SzGeCERN$$aParticle Physics - Experiment
000000107 690C_ $$aCERN
000000107 690C_ $$aPREPRINT
000000107 693__ $$aCERN LEP$$eALEPH
000000107 693__ $$aCERN LEP$$eDELPHI
000000107 693__ $$aCERN LEP$$eL3
000000107 693__ $$aCERN LEP$$eOPAL
000000107 695__ $$9MEDLINE$$asearches Higgs bosons
000000107 697C_ $$aLexiHiggs
000000107 710__ $$5EP
000000107 710__ $$gALEPH Collaboration
000000107 710__ $$gDELPHI Collaboration
000000107 710__ $$gL3 Collaboration
000000107 710__ $$gLEP Working Group for Higgs Boson Searches
000000107 710__ $$gOPAL Collaboration
000000107 901__ $$uCERN
000000107 916__ $$sh$$w199941
000000107 960__ $$a11
000000107 963__ $$aPUBLIC
000000107 970__ $$a000330309CER
000000107 980__ $$aARTICLE
000000085 001__ 85
000000085 003__ SzGeCERN
000000085 005__ %(rec_85_rev)s
000000085 035__ $$a2356302CERCER
000000085 035__ $$9SLAC$$a5423422
000000085 037__ $$ahep-th/0212181
000000085 041__ $$aeng
000000085 100__ $$aGirardello, L$$uINFN$$uUniversita di Milano-Bicocca
000000085 245__ $$a3-D Interacting CFTs and Generalized Higgs Phenomenon in Higher Spin Theories on AdS
000000085 260__ $$c2003
000000085 269__ $$c16 Dec 2002
000000085 300__ $$a8 p
000000085 520__ $$aWe study a duality, recently conjectured by Klebanov and Polyakov, between higher-spin theories on AdS_4 and O(N) vector models in 3-d. These theories are free in the UV and interacting in the IR. At the UV fixed point, the O(N) model has an infinite number of higher-spin conserved currents. In the IR, these currents are no longer conserved for spin s>2. In this paper, we show that the dual interpretation of this fact is that all fields of spin s>2 in AdS_4 become massive by a Higgs mechanism, that leaves the spin-2 field massless. We identify the Higgs field and show how it relates to the RG flow connecting the two CFTs, which is induced by a double trace deformation.
000000085 65017 $$2SzGeCERN$$aParticle Physics - Theory
000000085 690C_ $$aARTICLE
000000085 695__ $$9LANL EDS$$aHigh Energy Physics - Theory
000000085 700__ $$aPorrati, Massimo
000000085 700__ $$aZaffaroni, A
000000085 8564_ $$s112828$$u%(siteurl)s/record/85/files/0212181.ps.gz
000000085 8564_ $$s151257$$u%(siteurl)s/record/85/files/0212181.pdf
000000085 859__ $$falberto.zaffaroni@mib.infn.it
000000085 909C4 $$c289-293$$pPhys. Lett. B$$v561$$y2003
000000085 916__ $$sn$$w200251
000000085 960__ $$a13
000000085 961__ $$c20060823$$h0007$$lCER01$$x20021217
000000085 963__ $$aPUBLIC
000000085 970__ $$a002356302CER
000000085 980__ $$aARTICLE
000000085 999C5 $$mD. Francia and A. Sagnotti,$$o[1]$$rhep-th/0207002$$sPhys. Lett. B 543 (2002) 303
000000085 999C5 $$mP. Haggi-Mani and B. Sundborg,$$o[1]$$rhep-th/0002189$$sJ. High Energy Phys. 0004 (2000) 031
000000085 999C5 $$mB. Sundborg,$$o[1]$$rhep-th/0103247$$sNucl. Phys. B, Proc. Suppl. 102 (2001) 113
000000085 999C5 $$mE. Sezgin and P. Sundell,$$o[1]$$rhep-th/0105001$$sJ. High Energy Phys. 0109 (2001) 036
000000085 999C5 $$mA. Mikhailov,$$o[1]$$rhep-th/0201019
000000085 999C5 $$mE. Sezgin and P. Sundell,$$o[1]$$rhep-th/0205131$$sNucl. Phys. B 644 (2002) 303
000000085 999C5 $$mE. Sezgin and P. Sundell,$$o[1]$$rhep-th/0205132$$sJ. High Energy Phys. 0207 (2002) 055
000000085 999C5 $$mJ. Engquist, E. Sezgin and P. Sundell,$$o[1]$$rhep-th/0207101$$sClass. Quantum Gravity 19 (2002) 6175
000000085 999C5 $$mM. A. Vasiliev,$$o[1]$$rhep-th/9611024$$sInt. J. Mod. Phys. D 5 (1996) 763
000000085 999C5 $$mD. Anselmi,$$o[1]$$rhep-th/9808004$$sNucl. Phys. B 541 (1999) 323
000000085 999C5 $$mD. Anselmi,$$o[1]$$rhep-th/9906167$$sClass. Quantum Gravity 17 (2000) 1383
000000085 999C5 $$mE. S. Fradkin and M. A. Vasiliev,$$o[2]$$sNucl. Phys. B 291 (1987) 141
000000085 999C5 $$mE. S. Fradkin and M. A. Vasiliev,$$o[2]$$sPhys. Lett. B 189 (1987) 89
000000085 999C5 $$mI. R. Klebanov and A. M. Polyakov,$$o[3]$$rhep-th/0210114$$sPhys. Lett. B 550 (2002) 213
000000085 999C5 $$mM. A. Vasiliev,$$o[4]$$rhep-th/9910096
000000085 999C5 $$mT. Leonhardt, A. Meziane and W. Ruhl,$$o[5]$$rhep-th/0211092
000000085 999C5 $$mO. Aharony, M. Berkooz and E. Silverstein,$$o[6]$$rhep-th/0105309$$sJ. High Energy Phys. 0108 (2001) 006
000000085 999C5 $$mE. Witten,$$o[7]$$rhep-th/0112258
000000085 999C5 $$mM. Berkooz, A. Sever and A. Shomer$$o[8]$$rhep-th/0112264$$sJ. High Energy Phys. 0205 (2002) 034
000000085 999C5 $$mS. S. Gubser and I. Mitra,$$o[9]$$rhep-th/0210093
000000085 999C5 $$mS. S. Gubser and I. R. Klebanov,$$o[10]$$rhep-th/0212138
000000085 999C5 $$mM. Porrati,$$o[11]$$rhep-th/0112166$$sJ. High Energy Phys. 0204 (2002) 058
000000085 999C5 $$mK. G. Wilson and J. B. Kogut,$$o[12]$$sPhys. Rep. 12 (1974) 75
000000085 999C5 $$mI. R. Klebanov and E. Witten,$$o[13]$$rhep-th/9905104$$sNucl. Phys. B 556 (1999) 89
000000085 999C5 $$mW. Heidenreich,$$o[14]$$sJ. Math. Phys. 22 (1981) 1566
000000085 999C5 $$mD. Anselmi,$$o[15]$$rhep-th/0210123
000000001 001__ 1
000000001 005__ %(rec_1_rev)s
000000001 037__ $$aCERN-EX-0106015
000000001 100__ $$aPhotolab
000000001 245__ $$aALEPH experiment: Candidate of Higgs boson production
000000001 246_1 $$aExpérience ALEPH: Candidat de la production d'un boson Higgs
000000001 260__ $$c14 06 2000
000000001 340__ $$aFILM
000000001 520__ $$aCandidate for the associated production of the Higgs boson and Z boson. Both, the Higgs and Z boson decay into 2 jets each. The green and the yellow jets belong to the Higgs boson. They represent the fragmentation of a bottom andanti-bottom quark. The red and the blue jets stem from the decay of the Z boson into a quark anti-quark pair. Left: View of the event along the beam axis. Bottom right: Zoom around the interaction point at the centre showing detailsof the fragmentation of the bottom and anti-bottom quarks. As expected for b quarks, in each jet the decay of a long-lived B meson is visible. Top right: "World map" showing the spatial distribution of the jets in the event.
000000001 65017 $$2SzGeCERN$$aExperiments and Tracks
000000001 6531_ $$aLEP
000000001 8560_ $$fneil.calder@cern.ch
000000001 8564_ $$s1585244$$u%(siteurl)s/record/1/files/0106015_01.jpg
000000001 8564_ $$s20954$$u%(siteurl)s/record/1/files/0106015_01.gif?subformat=icon$$xicon
000000001 909C0 $$o0003717PHOPHO
000000001 909C0 $$y2000
000000001 909C0 $$b81
000000001 909C1 $$c2001-06-14$$l50$$m2001-08-27$$oCM
000000001 909CP $$pBldg. 2
000000001 909CP $$rCalder, N
000000001 909CS $$sn$$w200231
000000001 980__ $$aPICTURE
""" % {'siteurl': CFG_SITE_URL,
       'rec_1_rev': get_fieldvalues(1, '005__')[0],
       'rec_85_rev': get_fieldvalues(85, '005__')[0],
       'rec_107_rev': get_fieldvalues(107, '005__')[0]})

    def test_search_engine_python_api_ranked_by_citation_asc(self):
        """websearch - search engine Python API for citation ranking asc"""
        self.assertEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
                          16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
                          30, 31, 32, 33, 34, 43, 44, 45, 46, 47, 48, 49, 50,
                          51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63,
                          64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 75, 76, 80,
                          82, 83, 85, 86, 87, 88, 89, 90, 92, 93, 96, 97, 98,
                          99, 100, 101, 102, 103, 104, 107, 108, 109, 113, 127,
                          128, 18, 74, 79, 91, 94, 77, 78, 95, 84, 81],
                perform_request_search(p='', rm='citation', so='a'))

    def test_search_engine_python_api_ranked_by_citation_desc(self):
        """websearch - search engine Python API for citation ranking desc"""
        self.assertEqual(list(reversed(
                         [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
                          16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
                          30, 31, 32, 33, 34, 43, 44, 45, 46, 47, 48, 49, 50,
                          51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63,
                          64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 75, 76, 80,
                          82, 83, 85, 86, 87, 88, 89, 90, 92, 93, 96, 97, 98,
                          99, 100, 101, 102, 103, 104, 107, 108, 109, 113, 127,
                          128, 18, 74, 79, 91, 94, 77, 78, 95, 84, 81])),
                perform_request_search(p='', rm='citation', so='d'))

    def test_search_engine_python_api_textmarc_field_filtered(self):
        """websearch - search engine Python API for Text MARC output, field-filtered"""
        req = make_fake_request()
        perform_request_search(req=req, p='higgs', of='tm', ot=['100', '700'])
        out = req.test_output_buffer.getvalue()
        self.assertEqual(out, """\
000000001 100__ $$aPhotolab
000000085 100__ $$aGirardello, L$$uINFN$$uUniversita di Milano-Bicocca
000000085 700__ $$aPorrati, Massimo
000000085 700__ $$aZaffaroni, A
""")

    def test_search_engine_python_api_for_intersect_results_with_one_collrec(self):
        """websearch - search engine Python API for intersect results with one collrec"""
        self.assertEqual({'Books & Reports': intbitset([19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34])},
                         intersect_results_with_collrecs(None, intbitset(range(0,110)), ['Books & Reports'], 'id', 0, 'en', False))

    def test_search_engine_python_api_for_intersect_results_with_several_collrecs(self):
        """websearch - search engine Python API for intersect results with several collrecs"""
        self.assertEqual({'Books': intbitset([21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34]),
                          'Reports': intbitset([19, 20]),
                          'Theses': intbitset([35, 36, 37, 38, 39, 40, 41, 42, 105])},
                         intersect_results_with_collrecs(None, intbitset(range(0,110)), ['Books', 'Theses', 'Reports'], 'id', 0, 'en', False))

    def test_search_engine_python_api_textmarc_field_filtered_hidden_guest(self):
        """websearch - search engine Python API for Text MARC output, field-filtered, hidden field, no guest access"""
        req = make_fake_request()
        perform_request_search(req=req, p='higgs', of='tm', ot=['100', '595'])
        out = req.test_output_buffer.getvalue()
        self.assertEqual(out, """\
000000001 100__ $$aPhotolab
000000085 100__ $$aGirardello, L$$uINFN$$uUniversita di Milano-Bicocca
""")

    def test_search_engine_python_api_xmlmarc_full(self):
        """websearch - search engine Python API for XMLMARC output, full"""
        req = make_fake_request(admin_user=False)
        perform_request_search(req=req, p='higgs', of='xm', so='d')
        out = req.test_output_buffer.getvalue()
        # print out
        self.assertXmlEqual(out, """<?xml version="1.0" encoding="UTF-8"?>
<!-- Search-Engine-Total-Number-Of-Results: 3 -->
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record>
  <controlfield tag="001">107</controlfield>
  <controlfield tag="003">SzGeCERN</controlfield>
  <controlfield tag="005">%(rec_107_rev)s</controlfield>
  <datafield tag="035" ind1=" " ind2=" ">
    <subfield code="9">SPIRES</subfield>
    <subfield code="a">4066995</subfield>
  </datafield>
  <datafield tag="037" ind1=" " ind2=" ">
    <subfield code="a">CERN-EP-99-060</subfield>
  </datafield>
  <datafield tag="041" ind1=" " ind2=" ">
    <subfield code="a">eng</subfield>
  </datafield>
  <datafield tag="084" ind1=" " ind2=" ">
    <subfield code="2">CERN Library</subfield>
    <subfield code="a">EP-1999-060</subfield>
  </datafield>
  <datafield tag="088" ind1=" " ind2=" ">
    <subfield code="9">SCAN-9910048</subfield>
  </datafield>
  <datafield tag="088" ind1=" " ind2=" ">
    <subfield code="a">CERN-L3-175</subfield>
  </datafield>
  <datafield tag="110" ind1=" " ind2=" ">
    <subfield code="a">CERN. Geneva</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">Limits on Higgs boson masses from combining the data of the four LEP experiments at $\sqrt{s} \leq 183 GeV$</subfield>
  </datafield>
  <datafield tag="260" ind1=" " ind2=" ">
    <subfield code="c">1999</subfield>
  </datafield>
  <datafield tag="269" ind1=" " ind2=" ">
    <subfield code="a">Geneva</subfield>
    <subfield code="b">CERN</subfield>
    <subfield code="c">26 Apr 1999</subfield>
  </datafield>
  <datafield tag="300" ind1=" " ind2=" ">
    <subfield code="a">18 p</subfield>
  </datafield>
  <datafield tag="490" ind1=" " ind2=" ">
    <subfield code="a">ALEPH Papers</subfield>
  </datafield>
  <datafield tag="500" ind1=" " ind2=" ">
    <subfield code="a">Preprint not submitted to publication</subfield>
  </datafield>
  <datafield tag="650" ind1="1" ind2="7">
    <subfield code="2">SzGeCERN</subfield>
    <subfield code="a">Particle Physics - Experiment</subfield>
  </datafield>
  <datafield tag="690" ind1="C" ind2=" ">
    <subfield code="a">CERN</subfield>
  </datafield>
  <datafield tag="690" ind1="C" ind2=" ">
    <subfield code="a">PREPRINT</subfield>
  </datafield>
  <datafield tag="693" ind1=" " ind2=" ">
    <subfield code="a">CERN LEP</subfield>
    <subfield code="e">ALEPH</subfield>
  </datafield>
  <datafield tag="693" ind1=" " ind2=" ">
    <subfield code="a">CERN LEP</subfield>
    <subfield code="e">DELPHI</subfield>
  </datafield>
  <datafield tag="693" ind1=" " ind2=" ">
    <subfield code="a">CERN LEP</subfield>
    <subfield code="e">L3</subfield>
  </datafield>
  <datafield tag="693" ind1=" " ind2=" ">
    <subfield code="a">CERN LEP</subfield>
    <subfield code="e">OPAL</subfield>
  </datafield>
  <datafield tag="695" ind1=" " ind2=" ">
    <subfield code="9">MEDLINE</subfield>
    <subfield code="a">searches Higgs bosons</subfield>
  </datafield>
  <datafield tag="697" ind1="C" ind2=" ">
    <subfield code="a">LexiHiggs</subfield>
  </datafield>
  <datafield tag="710" ind1=" " ind2=" ">
    <subfield code="5">EP</subfield>
  </datafield>
  <datafield tag="710" ind1=" " ind2=" ">
    <subfield code="g">ALEPH Collaboration</subfield>
  </datafield>
  <datafield tag="710" ind1=" " ind2=" ">
    <subfield code="g">DELPHI Collaboration</subfield>
  </datafield>
  <datafield tag="710" ind1=" " ind2=" ">
    <subfield code="g">L3 Collaboration</subfield>
  </datafield>
  <datafield tag="710" ind1=" " ind2=" ">
    <subfield code="g">LEP Working Group for Higgs Boson Searches</subfield>
  </datafield>
  <datafield tag="710" ind1=" " ind2=" ">
    <subfield code="g">OPAL Collaboration</subfield>
  </datafield>
  <datafield tag="901" ind1=" " ind2=" ">
    <subfield code="u">CERN</subfield>
  </datafield>
  <datafield tag="916" ind1=" " ind2=" ">
    <subfield code="s">h</subfield>
    <subfield code="w">199941</subfield>
  </datafield>
  <datafield tag="960" ind1=" " ind2=" ">
    <subfield code="a">11</subfield>
  </datafield>
  <datafield tag="963" ind1=" " ind2=" ">
    <subfield code="a">PUBLIC</subfield>
  </datafield>
  <datafield tag="970" ind1=" " ind2=" ">
    <subfield code="a">000330309CER</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">ARTICLE</subfield>
  </datafield>
</record>
<record>
  <controlfield tag="001">85</controlfield>
  <controlfield tag="003">SzGeCERN</controlfield>
  <controlfield tag="005">%(rec_85_rev)s</controlfield>
  <datafield tag="035" ind1=" " ind2=" ">
    <subfield code="a">2356302CERCER</subfield>
  </datafield>
  <datafield tag="035" ind1=" " ind2=" ">
    <subfield code="9">SLAC</subfield>
    <subfield code="a">5423422</subfield>
  </datafield>
  <datafield tag="037" ind1=" " ind2=" ">
    <subfield code="a">hep-th/0212181</subfield>
  </datafield>
  <datafield tag="041" ind1=" " ind2=" ">
    <subfield code="a">eng</subfield>
  </datafield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Girardello, L</subfield>
    <subfield code="u">INFN</subfield>
    <subfield code="u">Universita di Milano-Bicocca</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">3-D Interacting CFTs and Generalized Higgs Phenomenon in Higher Spin Theories on AdS</subfield>
  </datafield>
  <datafield tag="260" ind1=" " ind2=" ">
    <subfield code="c">2003</subfield>
  </datafield>
  <datafield tag="269" ind1=" " ind2=" ">
    <subfield code="c">16 Dec 2002</subfield>
  </datafield>
  <datafield tag="300" ind1=" " ind2=" ">
    <subfield code="a">8 p</subfield>
  </datafield>
  <datafield tag="520" ind1=" " ind2=" ">
    <subfield code="a">We study a duality, recently conjectured by Klebanov and Polyakov, between higher-spin theories on AdS_4 and O(N) vector models in 3-d. These theories are free in the UV and interacting in the IR. At the UV fixed point, the O(N) model has an infinite number of higher-spin conserved currents. In the IR, these currents are no longer conserved for spin s>2. In this paper, we show that the dual interpretation of this fact is that all fields of spin s>2 in AdS_4 become massive by a Higgs mechanism, that leaves the spin-2 field massless. We identify the Higgs field and show how it relates to the RG flow connecting the two CFTs, which is induced by a double trace deformation.</subfield>
  </datafield>
  <datafield tag="650" ind1="1" ind2="7">
    <subfield code="2">SzGeCERN</subfield>
    <subfield code="a">Particle Physics - Theory</subfield>
  </datafield>
  <datafield tag="690" ind1="C" ind2=" ">
    <subfield code="a">ARTICLE</subfield>
  </datafield>
  <datafield tag="695" ind1=" " ind2=" ">
    <subfield code="9">LANL EDS</subfield>
    <subfield code="a">High Energy Physics - Theory</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Porrati, Massimo</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Zaffaroni, A</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="s">112828</subfield>
    <subfield code="u">%(siteurl)s/record/85/files/0212181.ps.gz</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="s">151257</subfield>
    <subfield code="u">%(siteurl)s/record/85/files/0212181.pdf</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="4">
    <subfield code="c">289-293</subfield>
    <subfield code="p">Phys. Lett. B</subfield>
    <subfield code="v">561</subfield>
    <subfield code="y">2003</subfield>
  </datafield>
  <datafield tag="859" ind1=" " ind2=" ">
    <subfield code="f">alberto.zaffaroni@mib.infn.it</subfield>
  </datafield>
  <datafield tag="916" ind1=" " ind2=" ">
    <subfield code="s">n</subfield>
    <subfield code="w">200251</subfield>
  </datafield>
  <datafield tag="960" ind1=" " ind2=" ">
    <subfield code="a">13</subfield>
  </datafield>
  <datafield tag="961" ind1=" " ind2=" ">
    <subfield code="c">20060823</subfield>
    <subfield code="h">0007</subfield>
    <subfield code="l">CER01</subfield>
    <subfield code="x">20021217</subfield>
  </datafield>
  <datafield tag="963" ind1=" " ind2=" ">
    <subfield code="a">PUBLIC</subfield>
  </datafield>
  <datafield tag="970" ind1=" " ind2=" ">
    <subfield code="a">002356302CER</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">ARTICLE</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">D. Francia and A. Sagnotti,</subfield>
    <subfield code="s">Phys. Lett. B 543 (2002) 303</subfield>
    <subfield code="r">hep-th/0207002</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">P. Haggi-Mani and B. Sundborg,</subfield>
    <subfield code="s">J. High Energy Phys. 0004 (2000) 031</subfield>
    <subfield code="r">hep-th/0002189</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">B. Sundborg,</subfield>
    <subfield code="s">Nucl. Phys. B, Proc. Suppl. 102 (2001) 113</subfield>
    <subfield code="r">hep-th/0103247</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">E. Sezgin and P. Sundell,</subfield>
    <subfield code="s">J. High Energy Phys. 0109 (2001) 036</subfield>
    <subfield code="r">hep-th/0105001</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">A. Mikhailov,</subfield>
    <subfield code="r">hep-th/0201019</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">E. Sezgin and P. Sundell,</subfield>
    <subfield code="s">Nucl. Phys. B 644 (2002) 303</subfield>
    <subfield code="r">hep-th/0205131</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">E. Sezgin and P. Sundell,</subfield>
    <subfield code="s">J. High Energy Phys. 0207 (2002) 055</subfield>
    <subfield code="r">hep-th/0205132</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">J. Engquist, E. Sezgin and P. Sundell,</subfield>
    <subfield code="s">Class. Quantum Gravity 19 (2002) 6175</subfield>
    <subfield code="r">hep-th/0207101</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">M. A. Vasiliev,</subfield>
    <subfield code="s">Int. J. Mod. Phys. D 5 (1996) 763</subfield>
    <subfield code="r">hep-th/9611024</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">D. Anselmi,</subfield>
    <subfield code="s">Nucl. Phys. B 541 (1999) 323</subfield>
    <subfield code="r">hep-th/9808004</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">D. Anselmi,</subfield>
    <subfield code="s">Class. Quantum Gravity 17 (2000) 1383</subfield>
    <subfield code="r">hep-th/9906167</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[2]</subfield>
    <subfield code="m">E. S. Fradkin and M. A. Vasiliev,</subfield>
    <subfield code="s">Nucl. Phys. B 291 (1987) 141</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[2]</subfield>
    <subfield code="m">E. S. Fradkin and M. A. Vasiliev,</subfield>
    <subfield code="s">Phys. Lett. B 189 (1987) 89</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[3]</subfield>
    <subfield code="m">I. R. Klebanov and A. M. Polyakov,</subfield>
    <subfield code="s">Phys. Lett. B 550 (2002) 213</subfield>
    <subfield code="r">hep-th/0210114</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[4]</subfield>
    <subfield code="m">M. A. Vasiliev,</subfield>
    <subfield code="r">hep-th/9910096</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[5]</subfield>
    <subfield code="m">T. Leonhardt, A. Meziane and W. Ruhl,</subfield>
    <subfield code="r">hep-th/0211092</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[6]</subfield>
    <subfield code="m">O. Aharony, M. Berkooz and E. Silverstein,</subfield>
    <subfield code="s">J. High Energy Phys. 0108 (2001) 006</subfield>
    <subfield code="r">hep-th/0105309</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[7]</subfield>
    <subfield code="m">E. Witten,</subfield>
    <subfield code="r">hep-th/0112258</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[8]</subfield>
    <subfield code="m">M. Berkooz, A. Sever and A. Shomer</subfield>
    <subfield code="s">J. High Energy Phys. 0205 (2002) 034</subfield>
    <subfield code="r">hep-th/0112264</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[9]</subfield>
    <subfield code="m">S. S. Gubser and I. Mitra,</subfield>
    <subfield code="r">hep-th/0210093</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[10]</subfield>
    <subfield code="m">S. S. Gubser and I. R. Klebanov,</subfield>
    <subfield code="r">hep-th/0212138</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[11]</subfield>
    <subfield code="m">M. Porrati,</subfield>
    <subfield code="s">J. High Energy Phys. 0204 (2002) 058</subfield>
    <subfield code="r">hep-th/0112166</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[12]</subfield>
    <subfield code="m">K. G. Wilson and J. B. Kogut,</subfield>
    <subfield code="s">Phys. Rep. 12 (1974) 75</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[13]</subfield>
    <subfield code="m">I. R. Klebanov and E. Witten,</subfield>
    <subfield code="s">Nucl. Phys. B 556 (1999) 89</subfield>
    <subfield code="r">hep-th/9905104</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[14]</subfield>
    <subfield code="m">W. Heidenreich,</subfield>
    <subfield code="s">J. Math. Phys. 22 (1981) 1566</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[15]</subfield>
    <subfield code="m">D. Anselmi,</subfield>
    <subfield code="r">hep-th/0210123</subfield>
  </datafield>
</record>
<record>
  <controlfield tag="001">1</controlfield>
  <controlfield tag="005">%(rec_1_rev)s</controlfield>
  <datafield tag="037" ind1=" " ind2=" ">
    <subfield code="a">CERN-EX-0106015</subfield>
  </datafield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Photolab</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">ALEPH experiment: Candidate of Higgs boson production</subfield>
  </datafield>
  <datafield tag="246" ind1=" " ind2="1">
    <subfield code="a">Expérience ALEPH: Candidat de la production d'un boson Higgs</subfield>
  </datafield>
  <datafield tag="260" ind1=" " ind2=" ">
    <subfield code="c">14 06 2000</subfield>
  </datafield>
  <datafield tag="340" ind1=" " ind2=" ">
    <subfield code="a">FILM</subfield>
  </datafield>
  <datafield tag="520" ind1=" " ind2=" ">
    <subfield code="a">Candidate for the associated production of the Higgs boson and Z boson. Both, the Higgs and Z boson decay into 2 jets each. The green and the yellow jets belong to the Higgs boson. They represent the fragmentation of a bottom andanti-bottom quark. The red and the blue jets stem from the decay of the Z boson into a quark anti-quark pair. Left: View of the event along the beam axis. Bottom right: Zoom around the interaction point at the centre showing detailsof the fragmentation of the bottom and anti-bottom quarks. As expected for b quarks, in each jet the decay of a long-lived B meson is visible. Top right: "World map" showing the spatial distribution of the jets in the event.</subfield>
  </datafield>
  <datafield tag="650" ind1="1" ind2="7">
    <subfield code="2">SzGeCERN</subfield>
    <subfield code="a">Experiments and Tracks</subfield>
  </datafield>
  <datafield tag="653" ind1="1" ind2=" ">
    <subfield code="a">LEP</subfield>
  </datafield>
  <datafield tag="856" ind1="0" ind2=" ">
    <subfield code="f">neil.calder@cern.ch</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="s">1585244</subfield>
    <subfield code="u">%(siteurl)s/record/1/files/0106015_01.jpg</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="s">20954</subfield>
    <subfield code="u">%(siteurl)s/record/1/files/0106015_01.gif?subformat=icon</subfield>
    <subfield code="x">icon</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="0">
    <subfield code="o">0003717PHOPHO</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="0">
    <subfield code="y">2000</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="0">
    <subfield code="b">81</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="1">
    <subfield code="c">2001-06-14</subfield>
    <subfield code="l">50</subfield>
    <subfield code="m">2001-08-27</subfield>
    <subfield code="o">CM</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="P">
    <subfield code="p">Bldg. 2</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="P">
    <subfield code="r">Calder, N</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="S">
    <subfield code="s">n</subfield>
    <subfield code="w">200231</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">PICTURE</subfield>
  </datafield>
</record>
</collection>""" % {'siteurl': CFG_SITE_URL,
                    'rec_1_rev': get_fieldvalues(1, '005__')[0],
                    'rec_85_rev': get_fieldvalues(85, '005__')[0],
                    'rec_107_rev': get_fieldvalues(107, '005__')[0]})

    def test_search_engine_python_api_xmlmarc_field_filtered(self):
        """websearch - search engine Python API for XMLMARC output, field-filtered"""
        # we are testing example from /help/hacking/search-engine-api
        req = make_fake_request()
        perform_request_search(req=req, p='higgs', of='xm', ot=['100', '700'], so='d')
        out = req.test_output_buffer.getvalue()
        self.assertXmlEqual(out, """<?xml version="1.0" encoding="UTF-8"?>
<!-- Search-Engine-Total-Number-Of-Results: 3 -->
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record>
  <controlfield tag="001">107</controlfield>
</record>
<record>
  <controlfield tag="001">85</controlfield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Girardello, L</subfield>
    <subfield code="u">INFN</subfield>
    <subfield code="u">Universita di Milano-Bicocca</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Porrati, Massimo</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Zaffaroni, A</subfield>
  </datafield>
</record>
<record>
  <controlfield tag="001">1</controlfield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Photolab</subfield>
  </datafield>
</record>

</collection>""")

    def test_search_engine_python_api_xmlmarc_field_filtered_hidden_guest(self):
        """websearch - search engine Python API for XMLMARC output, field-filtered, hidden field, no guest access"""
        # we are testing example from /help/hacking/search-engine-api
        req = make_fake_request()
        perform_request_search(req=req, p='higgs', of='xm', ot=['100', '595'], so='d')
        out = req.test_output_buffer.getvalue()
        self.assertXmlEqual(out, """<?xml version="1.0" encoding="UTF-8"?>
<!-- Search-Engine-Total-Number-Of-Results: 3 -->
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record>
  <controlfield tag="001">107</controlfield>
</record>
<record>
  <controlfield tag="001">85</controlfield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Girardello, L</subfield>
    <subfield code="u">INFN</subfield>
    <subfield code="u">Universita di Milano-Bicocca</subfield>
  </datafield>
</record>
<record>
  <controlfield tag="001">1</controlfield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Photolab</subfield>
  </datafield>
</record>

</collection>""")

    def test_search_engine_python_api_long_author_with_quotes(self):
        """websearch - search engine Python API for p=author:"Abbot, R B"'""" \
        """this test was written along with a bug report, needs fixing."""
        self.assertEqual([16], perform_request_search(p='author:"Abbott, R B"'))

class WebSearchSearchEngineWebAPITest(InvenioTestCase):
    """Check typical search engine Web API calls on the demo data."""

    def test_search_engine_python_api_search_refersto_year_2000(self):
        """websearch - search engine Python API for failed query"""
        self.assertEqual([92], perform_request_search(p='refersto:year:2000'))

    def test_search_engine_web_api_for_failed_query(self):
        """websearch - search engine Web API for failed query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=aoeuidhtns&of=id',
                                               expected_text="[]"))

    def test_search_engine_web_api_for_failed_query_format_intbitset(self):
        """websearch - search engine Web API for failed query, output format intbitset"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=aoeuidhtns&of=intbitset',
                                               expected_text=intbitset().fastdump()))

    def test_search_engine_web_api_for_successful_query(self):
        """websearch - search engine Web API for successful query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis&of=id&rg=0',
                                               expected_text="[47, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8]"))

    def test_search_engine_web_api_no_paging_parameter(self):
        """websearch - search engine Web API for successful query, ignore paging parameters"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis&of=id&rg=0',
                                               expected_text="[47, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8]"))

    def test_search_engine_web_api_jrec_parameter(self):
        """websearch - search engine Web API for successful query, ignore paging parameters"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis&of=id&rg=0&jrec=3',
                                               expected_text="[16, 15, 14, 13, 12, 11, 10, 9, 8]"))

    def test_search_engine_web_api_paging_parameters(self):
        """websearch - search engine Web API for successful query, ignore paging parameters"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis&of=id&rg=5&jrec=3',
                                               expected_text="[16, 15, 14, 13, 12]"))

    def test_search_engine_web_api_respect_sorting_parameter(self):
        """websearch - search engine Web API for successful query, respect sorting parameters"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=klebanov&of=id',
                                               expected_text="[85, 84]"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=klebanov&of=id',
                                               username="admin",
                                               expected_text="[85, 84, 77]"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=klebanov&of=id&sf=909C4v',
                                               expected_text="[84, 85]"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=klebanov&of=id&sf=909C4v',
                                               username="admin",
                                               expected_text="[84, 85, 77]"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=klebanov&of=intbitset&sf=909C4v',
                                               username="admin",
                                               expected_text=intbitset([77, 84, 85]).fastdump()))

    def test_search_engine_web_api_respect_ranking_parameter(self):
        """websearch - search engine Web API for successful query, respect ranking parameters"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=klebanov&of=id',
                                               expected_text="[85, 84]"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=klebanov&of=id',
                                               username="admin",
                                               expected_text="[85, 84, 77]"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=klebanov&of=id&rm=citation',
                                               expected_text="[84, 85]"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=klebanov&of=id&rm=citation',
                                               username="admin",
                                               expected_text="[84, 77, 85]"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=klebanov&of=intbitset&rm=citation',
                                               username="admin",
                                               expected_text=intbitset([77, 84, 85]).fastdump()))

    def test_search_engine_web_api_for_existing_record(self):
        """websearch - search engine Web API for existing record"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?recid=8&of=id',
                                               expected_text="[8]"))

    def test_search_engine_web_api_for_nonexisting_record(self):
        """websearch - search engine Web API for non-existing record"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?recid=12345678&of=id',
                                               expected_text="[]"))

    def test_search_engine_web_api_for_nonexisting_collection(self):
        """websearch - search engine Web API for non-existing collection"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?c=Foo&of=id',
                                               expected_text="[]"))

    def test_search_engine_web_api_for_range_of_records(self):
        """websearch - search engine Web API for range of records"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?recid=1&recidb=10&of=id',
                                               expected_text="[1, 2, 3, 4, 5, 6, 7, 8, 9]"))

    def test_search_engine_web_api_ranked_by_citation(self):
        """websearch - search engine Web API for citation ranking"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=recid%3A81&rm=citation&of=id',
                                               expected_text="[82, 83, 87, 89]"))

    def test_search_engine_web_api_textmarc_full(self):
        """websearch - search engine Web API for Text MARC output, full"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=higgs&of=tm',
                                               expected_text="""\
000000107 001__ 107
000000107 003__ SzGeCERN
000000107 005__ %(rec_107_rev)s
000000107 035__ $$9SPIRES$$a4066995
000000107 037__ $$aCERN-EP-99-060
000000107 041__ $$aeng
000000107 084__ $$2CERN Library$$aEP-1999-060
000000107 088__ $$9SCAN-9910048
000000107 088__ $$aCERN-L3-175
000000107 110__ $$aCERN. Geneva
000000107 245__ $$aLimits on Higgs boson masses from combining the data of the four LEP experiments at $\sqrt{s} \leq 183 GeV$
000000107 260__ $$c1999
000000107 269__ $$aGeneva$$bCERN$$c26 Apr 1999
000000107 300__ $$a18 p
000000107 490__ $$aALEPH Papers
000000107 500__ $$aPreprint not submitted to publication
000000107 65017 $$2SzGeCERN$$aParticle Physics - Experiment
000000107 690C_ $$aCERN
000000107 690C_ $$aPREPRINT
000000107 693__ $$aCERN LEP$$eALEPH
000000107 693__ $$aCERN LEP$$eDELPHI
000000107 693__ $$aCERN LEP$$eL3
000000107 693__ $$aCERN LEP$$eOPAL
000000107 695__ $$9MEDLINE$$asearches Higgs bosons
000000107 697C_ $$aLexiHiggs
000000107 710__ $$5EP
000000107 710__ $$gALEPH Collaboration
000000107 710__ $$gDELPHI Collaboration
000000107 710__ $$gL3 Collaboration
000000107 710__ $$gLEP Working Group for Higgs Boson Searches
000000107 710__ $$gOPAL Collaboration
000000107 901__ $$uCERN
000000107 916__ $$sh$$w199941
000000107 960__ $$a11
000000107 963__ $$aPUBLIC
000000107 970__ $$a000330309CER
000000107 980__ $$aARTICLE
000000085 001__ 85
000000085 003__ SzGeCERN
000000085 005__ %(rec_85_rev)s
000000085 035__ $$a2356302CERCER
000000085 035__ $$9SLAC$$a5423422
000000085 037__ $$ahep-th/0212181
000000085 041__ $$aeng
000000085 100__ $$aGirardello, L$$uINFN$$uUniversita di Milano-Bicocca
000000085 245__ $$a3-D Interacting CFTs and Generalized Higgs Phenomenon in Higher Spin Theories on AdS
000000085 260__ $$c2003
000000085 269__ $$c16 Dec 2002
000000085 300__ $$a8 p
000000085 520__ $$aWe study a duality, recently conjectured by Klebanov and Polyakov, between higher-spin theories on AdS_4 and O(N) vector models in 3-d. These theories are free in the UV and interacting in the IR. At the UV fixed point, the O(N) model has an infinite number of higher-spin conserved currents. In the IR, these currents are no longer conserved for spin s>2. In this paper, we show that the dual interpretation of this fact is that all fields of spin s>2 in AdS_4 become massive by a Higgs mechanism, that leaves the spin-2 field massless. We identify the Higgs field and show how it relates to the RG flow connecting the two CFTs, which is induced by a double trace deformation.
000000085 65017 $$2SzGeCERN$$aParticle Physics - Theory
000000085 690C_ $$aARTICLE
000000085 695__ $$9LANL EDS$$aHigh Energy Physics - Theory
000000085 700__ $$aPorrati, Massimo
000000085 700__ $$aZaffaroni, A
000000085 8564_ $$s112828$$u%(siteurl)s/record/85/files/0212181.ps.gz
000000085 8564_ $$s151257$$u%(siteurl)s/record/85/files/0212181.pdf
000000085 859__ $$falberto.zaffaroni@mib.infn.it
000000085 909C4 $$c289-293$$pPhys. Lett. B$$v561$$y2003
000000085 916__ $$sn$$w200251
000000085 960__ $$a13
000000085 961__ $$c20060823$$h0007$$lCER01$$x20021217
000000085 963__ $$aPUBLIC
000000085 970__ $$a002356302CER
000000085 980__ $$aARTICLE
000000085 999C5 $$mD. Francia and A. Sagnotti,$$o[1]$$rhep-th/0207002$$sPhys. Lett. B 543 (2002) 303
000000085 999C5 $$mP. Haggi-Mani and B. Sundborg,$$o[1]$$rhep-th/0002189$$sJ. High Energy Phys. 0004 (2000) 031
000000085 999C5 $$mB. Sundborg,$$o[1]$$rhep-th/0103247$$sNucl. Phys. B, Proc. Suppl. 102 (2001) 113
000000085 999C5 $$mE. Sezgin and P. Sundell,$$o[1]$$rhep-th/0105001$$sJ. High Energy Phys. 0109 (2001) 036
000000085 999C5 $$mA. Mikhailov,$$o[1]$$rhep-th/0201019
000000085 999C5 $$mE. Sezgin and P. Sundell,$$o[1]$$rhep-th/0205131$$sNucl. Phys. B 644 (2002) 303
000000085 999C5 $$mE. Sezgin and P. Sundell,$$o[1]$$rhep-th/0205132$$sJ. High Energy Phys. 0207 (2002) 055
000000085 999C5 $$mJ. Engquist, E. Sezgin and P. Sundell,$$o[1]$$rhep-th/0207101$$sClass. Quantum Gravity 19 (2002) 6175
000000085 999C5 $$mM. A. Vasiliev,$$o[1]$$rhep-th/9611024$$sInt. J. Mod. Phys. D 5 (1996) 763
000000085 999C5 $$mD. Anselmi,$$o[1]$$rhep-th/9808004$$sNucl. Phys. B 541 (1999) 323
000000085 999C5 $$mD. Anselmi,$$o[1]$$rhep-th/9906167$$sClass. Quantum Gravity 17 (2000) 1383
000000085 999C5 $$mE. S. Fradkin and M. A. Vasiliev,$$o[2]$$sNucl. Phys. B 291 (1987) 141
000000085 999C5 $$mE. S. Fradkin and M. A. Vasiliev,$$o[2]$$sPhys. Lett. B 189 (1987) 89
000000085 999C5 $$mI. R. Klebanov and A. M. Polyakov,$$o[3]$$rhep-th/0210114$$sPhys. Lett. B 550 (2002) 213
000000085 999C5 $$mM. A. Vasiliev,$$o[4]$$rhep-th/9910096
000000085 999C5 $$mT. Leonhardt, A. Meziane and W. Ruhl,$$o[5]$$rhep-th/0211092
000000085 999C5 $$mO. Aharony, M. Berkooz and E. Silverstein,$$o[6]$$rhep-th/0105309$$sJ. High Energy Phys. 0108 (2001) 006
000000085 999C5 $$mE. Witten,$$o[7]$$rhep-th/0112258
000000085 999C5 $$mM. Berkooz, A. Sever and A. Shomer$$o[8]$$rhep-th/0112264$$sJ. High Energy Phys. 0205 (2002) 034
000000085 999C5 $$mS. S. Gubser and I. Mitra,$$o[9]$$rhep-th/0210093
000000085 999C5 $$mS. S. Gubser and I. R. Klebanov,$$o[10]$$rhep-th/0212138
000000085 999C5 $$mM. Porrati,$$o[11]$$rhep-th/0112166$$sJ. High Energy Phys. 0204 (2002) 058
000000085 999C5 $$mK. G. Wilson and J. B. Kogut,$$o[12]$$sPhys. Rep. 12 (1974) 75
000000085 999C5 $$mI. R. Klebanov and E. Witten,$$o[13]$$rhep-th/9905104$$sNucl. Phys. B 556 (1999) 89
000000085 999C5 $$mW. Heidenreich,$$o[14]$$sJ. Math. Phys. 22 (1981) 1566
000000085 999C5 $$mD. Anselmi,$$o[15]$$rhep-th/0210123
000000001 001__ 1
000000001 005__ %(rec_1_rev)s
000000001 037__ $$aCERN-EX-0106015
000000001 100__ $$aPhotolab
000000001 245__ $$aALEPH experiment: Candidate of Higgs boson production
000000001 246_1 $$aExpérience ALEPH: Candidat de la production d'un boson Higgs
000000001 260__ $$c14 06 2000
000000001 340__ $$aFILM
000000001 520__ $$aCandidate for the associated production of the Higgs boson and Z boson. Both, the Higgs and Z boson decay into 2 jets each. The green and the yellow jets belong to the Higgs boson. They represent the fragmentation of a bottom andanti-bottom quark. The red and the blue jets stem from the decay of the Z boson into a quark anti-quark pair. Left: View of the event along the beam axis. Bottom right: Zoom around the interaction point at the centre showing detailsof the fragmentation of the bottom and anti-bottom quarks. As expected for b quarks, in each jet the decay of a long-lived B meson is visible. Top right: "World map" showing the spatial distribution of the jets in the event.
000000001 65017 $$2SzGeCERN$$aExperiments and Tracks
000000001 6531_ $$aLEP
000000001 8560_ $$fneil.calder@cern.ch
000000001 8564_ $$s1585244$$u%(siteurl)s/record/1/files/0106015_01.jpg
000000001 8564_ $$s20954$$u%(siteurl)s/record/1/files/0106015_01.gif?subformat=icon$$xicon
000000001 909C0 $$o0003717PHOPHO
000000001 909C0 $$y2000
000000001 909C0 $$b81
000000001 909C1 $$c2001-06-14$$l50$$m2001-08-27$$oCM
000000001 909CP $$pBldg. 2
000000001 909CP $$rCalder, N
000000001 909CS $$sn$$w200231
000000001 980__ $$aPICTURE
""" % {'siteurl': CFG_SITE_URL,
       'rec_1_rev': get_fieldvalues(1, '005__')[0],
       'rec_85_rev': get_fieldvalues(85, '005__')[0],
       'rec_107_rev': get_fieldvalues(107, '005__')[0]}))

    def test_search_engine_web_api_textmarc_field_filtered(self):
        """websearch - search engine Web API for Text MARC output, field-filtered"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=higgs&of=tm&ot=100,700',
                                               expected_text="""\
000000085 100__ $$aGirardello, L$$uINFN$$uUniversita di Milano-Bicocca
000000085 700__ $$aPorrati, Massimo
000000085 700__ $$aZaffaroni, A
000000001 100__ $$aPhotolab
"""))

    def test_search_engine_web_api_textmarc_field_filtered_hidden_guest(self):
        """websearch - search engine Web API for Text MARC output, field-filtered, hidden field, no guest access"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=higgs&of=tm&ot=100,595',
                                               expected_text="""\
000000085 100__ $$aGirardello, L$$uINFN$$uUniversita di Milano-Bicocca
000000001 100__ $$aPhotolab
"""))

    def test_search_engine_web_api_textmarc_field_filtered_hidden_admin(self):
        """websearch - search engine Web API for Text MARC output, field-filtered, hidden field, admin access"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=higgs&of=tm&ot=100,595',
                                               username='admin',
                                               expected_text="""\
000000107 595__ $$aNo authors
000000107 595__ $$aCERN-EP
000000107 595__ $$aOA
000000107 595__ $$aSIS:200740 PR/LKR not found (from SLAC, INSPEC)
000000085 100__ $$aGirardello, L$$uINFN$$uUniversita di Milano-Bicocca
000000085 595__ $$aLANL EDS
000000085 595__ $$aSIS LANLPUBL2004
000000085 595__ $$aSIS:2004 PR/LKR added
000000001 100__ $$aPhotolab
000000001 595__ $$aPress
"""))

    def test_search_engine_web_api_textmarc_subfield_values(self):
        """websearch - search engine Web API for Text MARC output, subfield values"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=higgs&of=tm&ot=700__a',
                                               expected_text="""\
Porrati, Massimo
Zaffaroni, A
"""))

    def test_search_engine_web_api_xmlmarc_full(self):
        """websearch - search engine Web API for XMLMARC output, full"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=higgs&of=xm',
                                               expected_text="""\
<?xml version="1.0" encoding="UTF-8"?>
<!-- Search-Engine-Total-Number-Of-Results: 3 -->
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record>
  <controlfield tag="001">107</controlfield>
  <controlfield tag="003">SzGeCERN</controlfield>
  <controlfield tag="005">%(rec_107_rev)s</controlfield>
  <datafield tag="035" ind1=" " ind2=" ">
    <subfield code="9">SPIRES</subfield>
    <subfield code="a">4066995</subfield>
  </datafield>
  <datafield tag="037" ind1=" " ind2=" ">
    <subfield code="a">CERN-EP-99-060</subfield>
  </datafield>
  <datafield tag="041" ind1=" " ind2=" ">
    <subfield code="a">eng</subfield>
  </datafield>
  <datafield tag="084" ind1=" " ind2=" ">
    <subfield code="2">CERN Library</subfield>
    <subfield code="a">EP-1999-060</subfield>
  </datafield>
  <datafield tag="088" ind1=" " ind2=" ">
    <subfield code="9">SCAN-9910048</subfield>
  </datafield>
  <datafield tag="088" ind1=" " ind2=" ">
    <subfield code="a">CERN-L3-175</subfield>
  </datafield>
  <datafield tag="110" ind1=" " ind2=" ">
    <subfield code="a">CERN. Geneva</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">Limits on Higgs boson masses from combining the data of the four LEP experiments at $\sqrt{s} \leq 183 GeV$</subfield>
  </datafield>
  <datafield tag="260" ind1=" " ind2=" ">
    <subfield code="c">1999</subfield>
  </datafield>
  <datafield tag="269" ind1=" " ind2=" ">
    <subfield code="a">Geneva</subfield>
    <subfield code="b">CERN</subfield>
    <subfield code="c">26 Apr 1999</subfield>
  </datafield>
  <datafield tag="300" ind1=" " ind2=" ">
    <subfield code="a">18 p</subfield>
  </datafield>
  <datafield tag="490" ind1=" " ind2=" ">
    <subfield code="a">ALEPH Papers</subfield>
  </datafield>
  <datafield tag="500" ind1=" " ind2=" ">
    <subfield code="a">Preprint not submitted to publication</subfield>
  </datafield>
  <datafield tag="650" ind1="1" ind2="7">
    <subfield code="2">SzGeCERN</subfield>
    <subfield code="a">Particle Physics - Experiment</subfield>
  </datafield>
  <datafield tag="690" ind1="C" ind2=" ">
    <subfield code="a">CERN</subfield>
  </datafield>
  <datafield tag="690" ind1="C" ind2=" ">
    <subfield code="a">PREPRINT</subfield>
  </datafield>
  <datafield tag="693" ind1=" " ind2=" ">
    <subfield code="a">CERN LEP</subfield>
    <subfield code="e">ALEPH</subfield>
  </datafield>
  <datafield tag="693" ind1=" " ind2=" ">
    <subfield code="a">CERN LEP</subfield>
    <subfield code="e">DELPHI</subfield>
  </datafield>
  <datafield tag="693" ind1=" " ind2=" ">
    <subfield code="a">CERN LEP</subfield>
    <subfield code="e">L3</subfield>
  </datafield>
  <datafield tag="693" ind1=" " ind2=" ">
    <subfield code="a">CERN LEP</subfield>
    <subfield code="e">OPAL</subfield>
  </datafield>
  <datafield tag="695" ind1=" " ind2=" ">
    <subfield code="9">MEDLINE</subfield>
    <subfield code="a">searches Higgs bosons</subfield>
  </datafield>
  <datafield tag="697" ind1="C" ind2=" ">
    <subfield code="a">LexiHiggs</subfield>
  </datafield>
  <datafield tag="710" ind1=" " ind2=" ">
    <subfield code="5">EP</subfield>
  </datafield>
  <datafield tag="710" ind1=" " ind2=" ">
    <subfield code="g">ALEPH Collaboration</subfield>
  </datafield>
  <datafield tag="710" ind1=" " ind2=" ">
    <subfield code="g">DELPHI Collaboration</subfield>
  </datafield>
  <datafield tag="710" ind1=" " ind2=" ">
    <subfield code="g">L3 Collaboration</subfield>
  </datafield>
  <datafield tag="710" ind1=" " ind2=" ">
    <subfield code="g">LEP Working Group for Higgs Boson Searches</subfield>
  </datafield>
  <datafield tag="710" ind1=" " ind2=" ">
    <subfield code="g">OPAL Collaboration</subfield>
  </datafield>
  <datafield tag="901" ind1=" " ind2=" ">
    <subfield code="u">CERN</subfield>
  </datafield>
  <datafield tag="916" ind1=" " ind2=" ">
    <subfield code="s">h</subfield>
    <subfield code="w">199941</subfield>
  </datafield>
  <datafield tag="960" ind1=" " ind2=" ">
    <subfield code="a">11</subfield>
  </datafield>
  <datafield tag="963" ind1=" " ind2=" ">
    <subfield code="a">PUBLIC</subfield>
  </datafield>
  <datafield tag="970" ind1=" " ind2=" ">
    <subfield code="a">000330309CER</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">ARTICLE</subfield>
  </datafield>
</record>
<record>
  <controlfield tag="001">85</controlfield>
  <controlfield tag="003">SzGeCERN</controlfield>
  <controlfield tag="005">%(rec_85_rev)s</controlfield>
  <datafield tag="035" ind1=" " ind2=" ">
    <subfield code="a">2356302CERCER</subfield>
  </datafield>
  <datafield tag="035" ind1=" " ind2=" ">
    <subfield code="9">SLAC</subfield>
    <subfield code="a">5423422</subfield>
  </datafield>
  <datafield tag="037" ind1=" " ind2=" ">
    <subfield code="a">hep-th/0212181</subfield>
  </datafield>
  <datafield tag="041" ind1=" " ind2=" ">
    <subfield code="a">eng</subfield>
  </datafield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Girardello, L</subfield>
    <subfield code="u">INFN</subfield>
    <subfield code="u">Universita di Milano-Bicocca</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">3-D Interacting CFTs and Generalized Higgs Phenomenon in Higher Spin Theories on AdS</subfield>
  </datafield>
  <datafield tag="260" ind1=" " ind2=" ">
    <subfield code="c">2003</subfield>
  </datafield>
  <datafield tag="269" ind1=" " ind2=" ">
    <subfield code="c">16 Dec 2002</subfield>
  </datafield>
  <datafield tag="300" ind1=" " ind2=" ">
    <subfield code="a">8 p</subfield>
  </datafield>
  <datafield tag="520" ind1=" " ind2=" ">
    <subfield code="a">We study a duality, recently conjectured by Klebanov and Polyakov, between higher-spin theories on AdS_4 and O(N) vector models in 3-d. These theories are free in the UV and interacting in the IR. At the UV fixed point, the O(N) model has an infinite number of higher-spin conserved currents. In the IR, these currents are no longer conserved for spin s>2. In this paper, we show that the dual interpretation of this fact is that all fields of spin s>2 in AdS_4 become massive by a Higgs mechanism, that leaves the spin-2 field massless. We identify the Higgs field and show how it relates to the RG flow connecting the two CFTs, which is induced by a double trace deformation.</subfield>
  </datafield>
  <datafield tag="650" ind1="1" ind2="7">
    <subfield code="2">SzGeCERN</subfield>
    <subfield code="a">Particle Physics - Theory</subfield>
  </datafield>
  <datafield tag="690" ind1="C" ind2=" ">
    <subfield code="a">ARTICLE</subfield>
  </datafield>
  <datafield tag="695" ind1=" " ind2=" ">
    <subfield code="9">LANL EDS</subfield>
    <subfield code="a">High Energy Physics - Theory</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Porrati, Massimo</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Zaffaroni, A</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="s">112828</subfield>
    <subfield code="u">%(siteurl)s/record/85/files/0212181.ps.gz</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="s">151257</subfield>
    <subfield code="u">%(siteurl)s/record/85/files/0212181.pdf</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="4">
    <subfield code="c">289-293</subfield>
    <subfield code="p">Phys. Lett. B</subfield>
    <subfield code="v">561</subfield>
    <subfield code="y">2003</subfield>
  </datafield>
  <datafield tag="859" ind1=" " ind2=" ">
    <subfield code="f">alberto.zaffaroni@mib.infn.it</subfield>
  </datafield>
  <datafield tag="916" ind1=" " ind2=" ">
    <subfield code="s">n</subfield>
    <subfield code="w">200251</subfield>
  </datafield>
  <datafield tag="960" ind1=" " ind2=" ">
    <subfield code="a">13</subfield>
  </datafield>
  <datafield tag="961" ind1=" " ind2=" ">
    <subfield code="c">20060823</subfield>
    <subfield code="h">0007</subfield>
    <subfield code="l">CER01</subfield>
    <subfield code="x">20021217</subfield>
  </datafield>
  <datafield tag="963" ind1=" " ind2=" ">
    <subfield code="a">PUBLIC</subfield>
  </datafield>
  <datafield tag="970" ind1=" " ind2=" ">
    <subfield code="a">002356302CER</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">ARTICLE</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">D. Francia and A. Sagnotti,</subfield>
    <subfield code="s">Phys. Lett. B 543 (2002) 303</subfield>
    <subfield code="r">hep-th/0207002</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">P. Haggi-Mani and B. Sundborg,</subfield>
    <subfield code="s">J. High Energy Phys. 0004 (2000) 031</subfield>
    <subfield code="r">hep-th/0002189</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">B. Sundborg,</subfield>
    <subfield code="s">Nucl. Phys. B, Proc. Suppl. 102 (2001) 113</subfield>
    <subfield code="r">hep-th/0103247</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">E. Sezgin and P. Sundell,</subfield>
    <subfield code="s">J. High Energy Phys. 0109 (2001) 036</subfield>
    <subfield code="r">hep-th/0105001</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">A. Mikhailov,</subfield>
    <subfield code="r">hep-th/0201019</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">E. Sezgin and P. Sundell,</subfield>
    <subfield code="s">Nucl. Phys. B 644 (2002) 303</subfield>
    <subfield code="r">hep-th/0205131</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">E. Sezgin and P. Sundell,</subfield>
    <subfield code="s">J. High Energy Phys. 0207 (2002) 055</subfield>
    <subfield code="r">hep-th/0205132</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">J. Engquist, E. Sezgin and P. Sundell,</subfield>
    <subfield code="s">Class. Quantum Gravity 19 (2002) 6175</subfield>
    <subfield code="r">hep-th/0207101</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">M. A. Vasiliev,</subfield>
    <subfield code="s">Int. J. Mod. Phys. D 5 (1996) 763</subfield>
    <subfield code="r">hep-th/9611024</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">D. Anselmi,</subfield>
    <subfield code="s">Nucl. Phys. B 541 (1999) 323</subfield>
    <subfield code="r">hep-th/9808004</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">D. Anselmi,</subfield>
    <subfield code="s">Class. Quantum Gravity 17 (2000) 1383</subfield>
    <subfield code="r">hep-th/9906167</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[2]</subfield>
    <subfield code="m">E. S. Fradkin and M. A. Vasiliev,</subfield>
    <subfield code="s">Nucl. Phys. B 291 (1987) 141</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[2]</subfield>
    <subfield code="m">E. S. Fradkin and M. A. Vasiliev,</subfield>
    <subfield code="s">Phys. Lett. B 189 (1987) 89</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[3]</subfield>
    <subfield code="m">I. R. Klebanov and A. M. Polyakov,</subfield>
    <subfield code="s">Phys. Lett. B 550 (2002) 213</subfield>
    <subfield code="r">hep-th/0210114</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[4]</subfield>
    <subfield code="m">M. A. Vasiliev,</subfield>
    <subfield code="r">hep-th/9910096</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[5]</subfield>
    <subfield code="m">T. Leonhardt, A. Meziane and W. Ruhl,</subfield>
    <subfield code="r">hep-th/0211092</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[6]</subfield>
    <subfield code="m">O. Aharony, M. Berkooz and E. Silverstein,</subfield>
    <subfield code="s">J. High Energy Phys. 0108 (2001) 006</subfield>
    <subfield code="r">hep-th/0105309</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[7]</subfield>
    <subfield code="m">E. Witten,</subfield>
    <subfield code="r">hep-th/0112258</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[8]</subfield>
    <subfield code="m">M. Berkooz, A. Sever and A. Shomer</subfield>
    <subfield code="s">J. High Energy Phys. 0205 (2002) 034</subfield>
    <subfield code="r">hep-th/0112264</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[9]</subfield>
    <subfield code="m">S. S. Gubser and I. Mitra,</subfield>
    <subfield code="r">hep-th/0210093</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[10]</subfield>
    <subfield code="m">S. S. Gubser and I. R. Klebanov,</subfield>
    <subfield code="r">hep-th/0212138</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[11]</subfield>
    <subfield code="m">M. Porrati,</subfield>
    <subfield code="s">J. High Energy Phys. 0204 (2002) 058</subfield>
    <subfield code="r">hep-th/0112166</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[12]</subfield>
    <subfield code="m">K. G. Wilson and J. B. Kogut,</subfield>
    <subfield code="s">Phys. Rep. 12 (1974) 75</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[13]</subfield>
    <subfield code="m">I. R. Klebanov and E. Witten,</subfield>
    <subfield code="s">Nucl. Phys. B 556 (1999) 89</subfield>
    <subfield code="r">hep-th/9905104</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[14]</subfield>
    <subfield code="m">W. Heidenreich,</subfield>
    <subfield code="s">J. Math. Phys. 22 (1981) 1566</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[15]</subfield>
    <subfield code="m">D. Anselmi,</subfield>
    <subfield code="r">hep-th/0210123</subfield>
  </datafield>
</record>
<record>
  <controlfield tag="001">1</controlfield>
  <controlfield tag="005">%(rec_1_rev)s</controlfield>
  <datafield tag="037" ind1=" " ind2=" ">
    <subfield code="a">CERN-EX-0106015</subfield>
  </datafield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Photolab</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">ALEPH experiment: Candidate of Higgs boson production</subfield>
  </datafield>
  <datafield tag="246" ind1=" " ind2="1">
    <subfield code="a">Expérience ALEPH: Candidat de la production d'un boson Higgs</subfield>
  </datafield>
  <datafield tag="260" ind1=" " ind2=" ">
    <subfield code="c">14 06 2000</subfield>
  </datafield>
  <datafield tag="340" ind1=" " ind2=" ">
    <subfield code="a">FILM</subfield>
  </datafield>
  <datafield tag="520" ind1=" " ind2=" ">
    <subfield code="a">Candidate for the associated production of the Higgs boson and Z boson. Both, the Higgs and Z boson decay into 2 jets each. The green and the yellow jets belong to the Higgs boson. They represent the fragmentation of a bottom andanti-bottom quark. The red and the blue jets stem from the decay of the Z boson into a quark anti-quark pair. Left: View of the event along the beam axis. Bottom right: Zoom around the interaction point at the centre showing detailsof the fragmentation of the bottom and anti-bottom quarks. As expected for b quarks, in each jet the decay of a long-lived B meson is visible. Top right: "World map" showing the spatial distribution of the jets in the event.</subfield>
  </datafield>
  <datafield tag="650" ind1="1" ind2="7">
    <subfield code="2">SzGeCERN</subfield>
    <subfield code="a">Experiments and Tracks</subfield>
  </datafield>
  <datafield tag="653" ind1="1" ind2=" ">
    <subfield code="a">LEP</subfield>
  </datafield>
  <datafield tag="856" ind1="0" ind2=" ">
    <subfield code="f">neil.calder@cern.ch</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="s">1585244</subfield>
    <subfield code="u">%(siteurl)s/record/1/files/0106015_01.jpg</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="s">20954</subfield>
    <subfield code="u">%(siteurl)s/record/1/files/0106015_01.gif?subformat=icon</subfield>
    <subfield code="x">icon</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="0">
    <subfield code="o">0003717PHOPHO</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="0">
    <subfield code="y">2000</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="0">
    <subfield code="b">81</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="1">
    <subfield code="c">2001-06-14</subfield>
    <subfield code="l">50</subfield>
    <subfield code="m">2001-08-27</subfield>
    <subfield code="o">CM</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="P">
    <subfield code="p">Bldg. 2</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="P">
    <subfield code="r">Calder, N</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="S">
    <subfield code="s">n</subfield>
    <subfield code="w">200231</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">PICTURE</subfield>
  </datafield>
</record>
</collection>""" % {'siteurl': CFG_SITE_URL,
                    'rec_1_rev': get_fieldvalues(1, '005__')[0],
                    'rec_85_rev': get_fieldvalues(85, '005__')[0],
                    'rec_107_rev': get_fieldvalues(107, '005__')[0]}))

    def test_search_engine_web_api_xmlmarc_field_filtered(self):
        """websearch - search engine Web API for XMLMARC output, field-filtered"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=higgs&of=xm&ot=100,700',
                                               expected_text="""\
<?xml version="1.0" encoding="UTF-8"?>
<!-- Search-Engine-Total-Number-Of-Results: 3 -->
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record>
  <controlfield tag="001">107</controlfield>
</record>
<record>
  <controlfield tag="001">85</controlfield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Girardello, L</subfield>
    <subfield code="u">INFN</subfield>
    <subfield code="u">Universita di Milano-Bicocca</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Porrati, Massimo</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Zaffaroni, A</subfield>
  </datafield>
</record>
<record>
  <controlfield tag="001">1</controlfield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Photolab</subfield>
  </datafield>
</record>

</collection>"""))

    def test_search_engine_web_api_xmlmarc_field_filtered_hidden_guest(self):
        """websearch - search engine Web API for XMLMARC output, field-filtered, hidden field, no guest access"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=higgs&of=xm&ot=100,595',
                                               expected_text="""\
<?xml version="1.0" encoding="UTF-8"?>
<!-- Search-Engine-Total-Number-Of-Results: 3 -->
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record>
  <controlfield tag="001">107</controlfield>
</record>
<record>
  <controlfield tag="001">85</controlfield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Girardello, L</subfield>
    <subfield code="u">INFN</subfield>
    <subfield code="u">Universita di Milano-Bicocca</subfield>
  </datafield>
</record>
<record>
  <controlfield tag="001">1</controlfield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Photolab</subfield>
  </datafield>
</record>

</collection>"""))

    def test_search_engine_web_api_xmlmarc_field_filtered_hidden_admin(self):
        """websearch - search engine Web API for XMLMARC output, field-filtered, hidden field, admin access"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=higgs&of=xm&ot=100,595',
                                               username='admin',
                                               expected_text="""\
<?xml version="1.0" encoding="UTF-8"?>
<!-- Search-Engine-Total-Number-Of-Results: 3 -->
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record>
  <controlfield tag="001">107</controlfield>
  <datafield tag="595" ind1=" " ind2=" ">
    <subfield code="a">No authors</subfield>
  </datafield>
  <datafield tag="595" ind1=" " ind2=" ">
    <subfield code="a">CERN-EP</subfield>
  </datafield>
  <datafield tag="595" ind1=" " ind2=" ">
    <subfield code="a">OA</subfield>
  </datafield>
  <datafield tag="595" ind1=" " ind2=" ">
    <subfield code="a">SIS:200740 PR/LKR not found (from SLAC, INSPEC)</subfield>
  </datafield>
</record>
<record>
  <controlfield tag="001">85</controlfield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Girardello, L</subfield>
    <subfield code="u">INFN</subfield>
    <subfield code="u">Universita di Milano-Bicocca</subfield>
  </datafield>
  <datafield tag="595" ind1=" " ind2=" ">
    <subfield code="a">LANL EDS</subfield>
  </datafield>
  <datafield tag="595" ind1=" " ind2=" ">
    <subfield code="a">SIS LANLPUBL2004</subfield>
  </datafield>
  <datafield tag="595" ind1=" " ind2=" ">
    <subfield code="a">SIS:2004 PR/LKR added</subfield>
  </datafield>
</record>
<record>
  <controlfield tag="001">1</controlfield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Photolab</subfield>
  </datafield>
  <datafield tag="595" ind1=" " ind2=" ">
    <subfield code="a">Press</subfield>
  </datafield>
</record>

</collection>"""))


class WebSearchSearchEngineJSONAPITest(InvenioTestCase):
    """Check typical search engine JSON API calls on the demo data."""

    def test_search_engine_json_api_for_failed_query(self):
        """websearch - search engine JSON API for failed query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=aoeuidhtns&of=recjson',
                                               expected_text=""))

    def test_search_engine_json_api_for_ellis_query(self):
        """websearch - search engine JSON API for Ellis"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis&of=recjson&ot=recid',
                                               expected_text='[{"recid": 47},{"recid": 18},{"recid": 17},{"recid": 16},{"recid": 15},{"recid": 14},{"recid": 13},{"recid": 12},{"recid": 11},{"recid": 10}]'))

    def test_search_engine_json_api_for_ellis_query_paginated(self):
        """websearch - search engine JSON API for Ellis, output fields and pagination"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis&of=recjson&ot=recid,title&jrec=4&rg=2',
                                               expected_text='[{"recid": 16, "title": {"title": "Cosmological perturbations in Kaluza-Klein models"}},{"recid": 15, "title": {"title": "Cosmic equation of state, Gravitational Lensing Statistics and Merging of Galaxies"}}]'))


class WebSearchRecordWebAPITest(InvenioTestCase):
    """Check typical /record Web API calls on the demo data."""

    def test_record_web_api_textmarc_full(self):
        """websearch - /record Web API for TextMARC output, full"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/record/85?of=tm',
                                               expected_text="""\
000000085 001__ 85
000000085 003__ SzGeCERN
000000085 005__ %(rec_85_rev)s
000000085 035__ $$a2356302CERCER
000000085 035__ $$9SLAC$$a5423422
000000085 037__ $$ahep-th/0212181
000000085 041__ $$aeng
000000085 100__ $$aGirardello, L$$uINFN$$uUniversita di Milano-Bicocca
000000085 245__ $$a3-D Interacting CFTs and Generalized Higgs Phenomenon in Higher Spin Theories on AdS
000000085 260__ $$c2003
000000085 269__ $$c16 Dec 2002
000000085 300__ $$a8 p
000000085 520__ $$aWe study a duality, recently conjectured by Klebanov and Polyakov, between higher-spin theories on AdS_4 and O(N) vector models in 3-d. These theories are free in the UV and interacting in the IR. At the UV fixed point, the O(N) model has an infinite number of higher-spin conserved currents. In the IR, these currents are no longer conserved for spin s>2. In this paper, we show that the dual interpretation of this fact is that all fields of spin s>2 in AdS_4 become massive by a Higgs mechanism, that leaves the spin-2 field massless. We identify the Higgs field and show how it relates to the RG flow connecting the two CFTs, which is induced by a double trace deformation.
000000085 65017 $$2SzGeCERN$$aParticle Physics - Theory
000000085 690C_ $$aARTICLE
000000085 695__ $$9LANL EDS$$aHigh Energy Physics - Theory
000000085 700__ $$aPorrati, Massimo
000000085 700__ $$aZaffaroni, A
000000085 8564_ $$s112828$$u%(siteurl)s/record/85/files/0212181.ps.gz
000000085 8564_ $$s151257$$u%(siteurl)s/record/85/files/0212181.pdf
000000085 859__ $$falberto.zaffaroni@mib.infn.it
000000085 909C4 $$c289-293$$pPhys. Lett. B$$v561$$y2003
000000085 916__ $$sn$$w200251
000000085 960__ $$a13
000000085 961__ $$c20060823$$h0007$$lCER01$$x20021217
000000085 963__ $$aPUBLIC
000000085 970__ $$a002356302CER
000000085 980__ $$aARTICLE
000000085 999C5 $$mD. Francia and A. Sagnotti,$$o[1]$$rhep-th/0207002$$sPhys. Lett. B 543 (2002) 303
000000085 999C5 $$mP. Haggi-Mani and B. Sundborg,$$o[1]$$rhep-th/0002189$$sJ. High Energy Phys. 0004 (2000) 031
000000085 999C5 $$mB. Sundborg,$$o[1]$$rhep-th/0103247$$sNucl. Phys. B, Proc. Suppl. 102 (2001) 113
000000085 999C5 $$mE. Sezgin and P. Sundell,$$o[1]$$rhep-th/0105001$$sJ. High Energy Phys. 0109 (2001) 036
000000085 999C5 $$mA. Mikhailov,$$o[1]$$rhep-th/0201019
000000085 999C5 $$mE. Sezgin and P. Sundell,$$o[1]$$rhep-th/0205131$$sNucl. Phys. B 644 (2002) 303
000000085 999C5 $$mE. Sezgin and P. Sundell,$$o[1]$$rhep-th/0205132$$sJ. High Energy Phys. 0207 (2002) 055
000000085 999C5 $$mJ. Engquist, E. Sezgin and P. Sundell,$$o[1]$$rhep-th/0207101$$sClass. Quantum Gravity 19 (2002) 6175
000000085 999C5 $$mM. A. Vasiliev,$$o[1]$$rhep-th/9611024$$sInt. J. Mod. Phys. D 5 (1996) 763
000000085 999C5 $$mD. Anselmi,$$o[1]$$rhep-th/9808004$$sNucl. Phys. B 541 (1999) 323
000000085 999C5 $$mD. Anselmi,$$o[1]$$rhep-th/9906167$$sClass. Quantum Gravity 17 (2000) 1383
000000085 999C5 $$mE. S. Fradkin and M. A. Vasiliev,$$o[2]$$sNucl. Phys. B 291 (1987) 141
000000085 999C5 $$mE. S. Fradkin and M. A. Vasiliev,$$o[2]$$sPhys. Lett. B 189 (1987) 89
000000085 999C5 $$mI. R. Klebanov and A. M. Polyakov,$$o[3]$$rhep-th/0210114$$sPhys. Lett. B 550 (2002) 213
000000085 999C5 $$mM. A. Vasiliev,$$o[4]$$rhep-th/9910096
000000085 999C5 $$mT. Leonhardt, A. Meziane and W. Ruhl,$$o[5]$$rhep-th/0211092
000000085 999C5 $$mO. Aharony, M. Berkooz and E. Silverstein,$$o[6]$$rhep-th/0105309$$sJ. High Energy Phys. 0108 (2001) 006
000000085 999C5 $$mE. Witten,$$o[7]$$rhep-th/0112258
000000085 999C5 $$mM. Berkooz, A. Sever and A. Shomer$$o[8]$$rhep-th/0112264$$sJ. High Energy Phys. 0205 (2002) 034
000000085 999C5 $$mS. S. Gubser and I. Mitra,$$o[9]$$rhep-th/0210093
000000085 999C5 $$mS. S. Gubser and I. R. Klebanov,$$o[10]$$rhep-th/0212138
000000085 999C5 $$mM. Porrati,$$o[11]$$rhep-th/0112166$$sJ. High Energy Phys. 0204 (2002) 058
000000085 999C5 $$mK. G. Wilson and J. B. Kogut,$$o[12]$$sPhys. Rep. 12 (1974) 75
000000085 999C5 $$mI. R. Klebanov and E. Witten,$$o[13]$$rhep-th/9905104$$sNucl. Phys. B 556 (1999) 89
000000085 999C5 $$mW. Heidenreich,$$o[14]$$sJ. Math. Phys. 22 (1981) 1566
000000085 999C5 $$mD. Anselmi,$$o[15]$$rhep-th/0210123
""" % {'siteurl': CFG_SITE_URL,
       'rec_85_rev': get_fieldvalues(85, '005__')[0]}))

    def test_record_web_api_xmlmarc_full(self):
        """websearch - /record Web API for XMLMARC output, full"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/record/85?of=xm',
                                               expected_text="""\
<?xml version="1.0" encoding="UTF-8"?>
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record>
  <controlfield tag="001">85</controlfield>
  <controlfield tag="003">SzGeCERN</controlfield>
  <controlfield tag="005">%(rec_85_rev)s</controlfield>
  <datafield tag="035" ind1=" " ind2=" ">
    <subfield code="a">2356302CERCER</subfield>
  </datafield>
  <datafield tag="035" ind1=" " ind2=" ">
    <subfield code="9">SLAC</subfield>
    <subfield code="a">5423422</subfield>
  </datafield>
  <datafield tag="037" ind1=" " ind2=" ">
    <subfield code="a">hep-th/0212181</subfield>
  </datafield>
  <datafield tag="041" ind1=" " ind2=" ">
    <subfield code="a">eng</subfield>
  </datafield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Girardello, L</subfield>
    <subfield code="u">INFN</subfield>
    <subfield code="u">Universita di Milano-Bicocca</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">3-D Interacting CFTs and Generalized Higgs Phenomenon in Higher Spin Theories on AdS</subfield>
  </datafield>
  <datafield tag="260" ind1=" " ind2=" ">
    <subfield code="c">2003</subfield>
  </datafield>
  <datafield tag="269" ind1=" " ind2=" ">
    <subfield code="c">16 Dec 2002</subfield>
  </datafield>
  <datafield tag="300" ind1=" " ind2=" ">
    <subfield code="a">8 p</subfield>
  </datafield>
  <datafield tag="520" ind1=" " ind2=" ">
    <subfield code="a">We study a duality, recently conjectured by Klebanov and Polyakov, between higher-spin theories on AdS_4 and O(N) vector models in 3-d. These theories are free in the UV and interacting in the IR. At the UV fixed point, the O(N) model has an infinite number of higher-spin conserved currents. In the IR, these currents are no longer conserved for spin s>2. In this paper, we show that the dual interpretation of this fact is that all fields of spin s>2 in AdS_4 become massive by a Higgs mechanism, that leaves the spin-2 field massless. We identify the Higgs field and show how it relates to the RG flow connecting the two CFTs, which is induced by a double trace deformation.</subfield>
  </datafield>
  <datafield tag="650" ind1="1" ind2="7">
    <subfield code="2">SzGeCERN</subfield>
    <subfield code="a">Particle Physics - Theory</subfield>
  </datafield>
  <datafield tag="690" ind1="C" ind2=" ">
    <subfield code="a">ARTICLE</subfield>
  </datafield>
  <datafield tag="695" ind1=" " ind2=" ">
    <subfield code="9">LANL EDS</subfield>
    <subfield code="a">High Energy Physics - Theory</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Porrati, Massimo</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Zaffaroni, A</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="s">112828</subfield>
    <subfield code="u">%(siteurl)s/record/85/files/0212181.ps.gz</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="s">151257</subfield>
    <subfield code="u">%(siteurl)s/record/85/files/0212181.pdf</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="4">
    <subfield code="c">289-293</subfield>
    <subfield code="p">Phys. Lett. B</subfield>
    <subfield code="v">561</subfield>
    <subfield code="y">2003</subfield>
  </datafield>
  <datafield tag="859" ind1=" " ind2=" ">
    <subfield code="f">alberto.zaffaroni@mib.infn.it</subfield>
  </datafield>
  <datafield tag="916" ind1=" " ind2=" ">
    <subfield code="s">n</subfield>
    <subfield code="w">200251</subfield>
  </datafield>
  <datafield tag="960" ind1=" " ind2=" ">
    <subfield code="a">13</subfield>
  </datafield>
  <datafield tag="961" ind1=" " ind2=" ">
    <subfield code="c">20060823</subfield>
    <subfield code="h">0007</subfield>
    <subfield code="l">CER01</subfield>
    <subfield code="x">20021217</subfield>
  </datafield>
  <datafield tag="963" ind1=" " ind2=" ">
    <subfield code="a">PUBLIC</subfield>
  </datafield>
  <datafield tag="970" ind1=" " ind2=" ">
    <subfield code="a">002356302CER</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">ARTICLE</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">D. Francia and A. Sagnotti,</subfield>
    <subfield code="s">Phys. Lett. B 543 (2002) 303</subfield>
    <subfield code="r">hep-th/0207002</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">P. Haggi-Mani and B. Sundborg,</subfield>
    <subfield code="s">J. High Energy Phys. 0004 (2000) 031</subfield>
    <subfield code="r">hep-th/0002189</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">B. Sundborg,</subfield>
    <subfield code="s">Nucl. Phys. B, Proc. Suppl. 102 (2001) 113</subfield>
    <subfield code="r">hep-th/0103247</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">E. Sezgin and P. Sundell,</subfield>
    <subfield code="s">J. High Energy Phys. 0109 (2001) 036</subfield>
    <subfield code="r">hep-th/0105001</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">A. Mikhailov,</subfield>
    <subfield code="r">hep-th/0201019</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">E. Sezgin and P. Sundell,</subfield>
    <subfield code="s">Nucl. Phys. B 644 (2002) 303</subfield>
    <subfield code="r">hep-th/0205131</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">E. Sezgin and P. Sundell,</subfield>
    <subfield code="s">J. High Energy Phys. 0207 (2002) 055</subfield>
    <subfield code="r">hep-th/0205132</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">J. Engquist, E. Sezgin and P. Sundell,</subfield>
    <subfield code="s">Class. Quantum Gravity 19 (2002) 6175</subfield>
    <subfield code="r">hep-th/0207101</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">M. A. Vasiliev,</subfield>
    <subfield code="s">Int. J. Mod. Phys. D 5 (1996) 763</subfield>
    <subfield code="r">hep-th/9611024</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">D. Anselmi,</subfield>
    <subfield code="s">Nucl. Phys. B 541 (1999) 323</subfield>
    <subfield code="r">hep-th/9808004</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">D. Anselmi,</subfield>
    <subfield code="s">Class. Quantum Gravity 17 (2000) 1383</subfield>
    <subfield code="r">hep-th/9906167</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[2]</subfield>
    <subfield code="m">E. S. Fradkin and M. A. Vasiliev,</subfield>
    <subfield code="s">Nucl. Phys. B 291 (1987) 141</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[2]</subfield>
    <subfield code="m">E. S. Fradkin and M. A. Vasiliev,</subfield>
    <subfield code="s">Phys. Lett. B 189 (1987) 89</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[3]</subfield>
    <subfield code="m">I. R. Klebanov and A. M. Polyakov,</subfield>
    <subfield code="s">Phys. Lett. B 550 (2002) 213</subfield>
    <subfield code="r">hep-th/0210114</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[4]</subfield>
    <subfield code="m">M. A. Vasiliev,</subfield>
    <subfield code="r">hep-th/9910096</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[5]</subfield>
    <subfield code="m">T. Leonhardt, A. Meziane and W. Ruhl,</subfield>
    <subfield code="r">hep-th/0211092</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[6]</subfield>
    <subfield code="m">O. Aharony, M. Berkooz and E. Silverstein,</subfield>
    <subfield code="s">J. High Energy Phys. 0108 (2001) 006</subfield>
    <subfield code="r">hep-th/0105309</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[7]</subfield>
    <subfield code="m">E. Witten,</subfield>
    <subfield code="r">hep-th/0112258</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[8]</subfield>
    <subfield code="m">M. Berkooz, A. Sever and A. Shomer</subfield>
    <subfield code="s">J. High Energy Phys. 0205 (2002) 034</subfield>
    <subfield code="r">hep-th/0112264</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[9]</subfield>
    <subfield code="m">S. S. Gubser and I. Mitra,</subfield>
    <subfield code="r">hep-th/0210093</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[10]</subfield>
    <subfield code="m">S. S. Gubser and I. R. Klebanov,</subfield>
    <subfield code="r">hep-th/0212138</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[11]</subfield>
    <subfield code="m">M. Porrati,</subfield>
    <subfield code="s">J. High Energy Phys. 0204 (2002) 058</subfield>
    <subfield code="r">hep-th/0112166</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[12]</subfield>
    <subfield code="m">K. G. Wilson and J. B. Kogut,</subfield>
    <subfield code="s">Phys. Rep. 12 (1974) 75</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[13]</subfield>
    <subfield code="m">I. R. Klebanov and E. Witten,</subfield>
    <subfield code="s">Nucl. Phys. B 556 (1999) 89</subfield>
    <subfield code="r">hep-th/9905104</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[14]</subfield>
    <subfield code="m">W. Heidenreich,</subfield>
    <subfield code="s">J. Math. Phys. 22 (1981) 1566</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[15]</subfield>
    <subfield code="m">D. Anselmi,</subfield>
    <subfield code="r">hep-th/0210123</subfield>
  </datafield>
</record>
</collection>""" % {'siteurl': CFG_SITE_URL,
                    'rec_85_rev': get_fieldvalues(85, '005__')[0]}))

    def test_record_web_api_textmarc_field_filtered(self):
        """websearch - /record Web API for TextMARC output, field-filtered"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/record/85?of=tm&ot=100,700',
                                               expected_text="""\
000000085 100__ $$aGirardello, L$$uINFN$$uUniversita di Milano-Bicocca
000000085 700__ $$aPorrati, Massimo
000000085 700__ $$aZaffaroni, A
"""))

    def test_record_web_api_textmarc_field_filtered_hidden_guest(self):
        """websearch - /record Web API for TextMARC output, field-filtered, hidden field, no guest access"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/record/85?of=tm&ot=100,595',
                                               expected_text="""\
000000085 100__ $$aGirardello, L$$uINFN$$uUniversita di Milano-Bicocca
"""))

    def test_record_web_api_textmarc_field_filtered_hidden_admin(self):
        """websearch - /record Web API for TextMARC output, field-filtered, hidden field, admin access"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/record/85?of=tm&ot=100,595',
                                               username='admin',
                                               expected_text="""\
000000085 100__ $$aGirardello, L$$uINFN$$uUniversita di Milano-Bicocca
000000085 595__ $$aLANL EDS
000000085 595__ $$aSIS LANLPUBL2004
000000085 595__ $$aSIS:2004 PR/LKR added
"""))

    def test_record_web_api_xmlmarc_field_filtered(self):
        """websearch - /record Web API for XMLMARC output, field-filtered"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/record/85?of=xm&ot=100,700',
                                               expected_text="""\
<?xml version="1.0" encoding="UTF-8"?>
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record>
  <controlfield tag="001">85</controlfield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Girardello, L</subfield>
    <subfield code="u">INFN</subfield>
    <subfield code="u">Universita di Milano-Bicocca</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Porrati, Massimo</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Zaffaroni, A</subfield>
  </datafield>
</record>

</collection>"""))

    def test_record_web_api_xmlmarc_field_filtered_hidden_guest(self):
        """websearch - /record Web API for XMLMARC output, field-filtered, hidden field, no guest access"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/record/85?of=xm&ot=100,595',
                                               expected_text="""\
<?xml version="1.0" encoding="UTF-8"?>
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record>
  <controlfield tag="001">85</controlfield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Girardello, L</subfield>
    <subfield code="u">INFN</subfield>
    <subfield code="u">Universita di Milano-Bicocca</subfield>
  </datafield>
</record>

</collection>"""))

    def test_record_web_api_xmlmarc_field_filtered_hidden_admin(self):
        """websearch - /record Web API for XMLMARC output, field-filtered, hidden field, admin access"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/record/85?of=xm&ot=100,595',
                                               username='admin',
                                               expected_text="""\
<?xml version="1.0" encoding="UTF-8"?>
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record>
  <controlfield tag="001">85</controlfield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Girardello, L</subfield>
    <subfield code="u">INFN</subfield>
    <subfield code="u">Universita di Milano-Bicocca</subfield>
  </datafield>
  <datafield tag="595" ind1=" " ind2=" ">
    <subfield code="a">LANL EDS</subfield>
  </datafield>
  <datafield tag="595" ind1=" " ind2=" ">
    <subfield code="a">SIS LANLPUBL2004</subfield>
  </datafield>
  <datafield tag="595" ind1=" " ind2=" ">
    <subfield code="a">SIS:2004 PR/LKR added</subfield>
  </datafield>
</record>

</collection>"""))

    def test_record_web_api_textmarc_subfield_values(self):
        """websearch - /record Web API for TextMARC output, subfield values"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/record/85?of=tm&ot=700__a',
                                               expected_text="""\
Porrati, Massimo
Zaffaroni, A
"""))


class WebSearchRecordJSONAPITest(InvenioTestCase):
    """Check typical /record JSON API calls on the demo data."""

    def test_record_json_api_for_failed_field(self):
        """websearch - search engine JSON API for failed field"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/record/81?of=recjson&ot=aoeuidhtns',
                                               expected_text='[{"aoeuidhtns": null}]'))

    def test_record_json_api_for_field(self):
        """websearch - search engine JSON API for existing field"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/record/81?of=recjson&ot=authors',
                                               expected_text='[{"authors": [{"affiliation": "Stanford University", "first_name": "A", "last_name": "Adams", "full_name": "Adams, A"}, {"first_name": "J", "last_name": "McGreevy", "full_name": "McGreevy, J"}, {"first_name": "E", "last_name": "Silverstein", "full_name": "Silverstein, E"}]}]'))

    def test_record_json_api_for_field_subfield(self):
        """websearch - search engine JSON API for existing field.subfield"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/record/81?of=recjson&ot=authors.last_name',
                                               expected_text='[{"authors": {"last_name": ["Adams", "McGreevy", "Silverstein"]}}]'))

    def test_record_json_api_for_derived_field(self):
        """websearch - search engine JSON API for derived field"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/record/81?of=recjson&ot=number_of_authors',
                                               expected_text='[{"number_of_authors": 3}]'))

    def test_record_json_api_for_virtual_field(self):
        """websearch - search engine JSON API for virtual field"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/record/81?of=recjson&ot=recid,number_of_citations',
                                               expected_text='[{"recid": 81, "number_of_citations": 4}]'))


class WebSearchRestrictedCollectionTest(InvenioTestCase):
    """Test of the restricted collections behaviour."""

    def test_restricted_collection_interface_page(self):
        """websearch - restricted collection interface page body"""
        # there should be no Latest additions box for restricted collections
        self.assertNotEqual([],
                            test_web_page_content(CFG_SITE_URL + '/collection/Theses',
                                                  expected_text="Latest additions"))

    def test_restricted_search_as_anonymous_guest(self):
        """websearch - restricted collection not searchable by anonymous guest"""
        browser = Browser()
        browser.open(CFG_SITE_URL + '/search?c=Theses')
        response = browser.response().read()
        if response.find("If you think you have right to access it, please authenticate yourself.") > -1:
            pass
        else:
            self.fail("Oops, searching restricted collection without password should have redirected to login dialog.")
        return

    def test_restricted_search_as_authorized_person(self):
        """websearch - restricted collection searchable by authorized person"""
        browser = Browser()
        browser.open(CFG_SITE_URL + '/search?c=Theses')
        browser.select_form(nr=0)
        browser['p_un'] = 'jekyll'
        browser['p_pw'] = 'j123ekyll'
        browser.submit()
        if browser.response().read().find("records found") > -1:
            pass
        else:
            self.fail("Oops, Dr. Jekyll should be able to search Theses collection.")

    def test_restricted_search_as_unauthorized_person(self):
        """websearch - restricted collection not searchable by unauthorized person"""
        browser = Browser()
        browser.open(CFG_SITE_URL + '/search?c=Theses')
        browser.select_form(nr=0)
        browser['p_un'] = 'hyde'
        browser['p_pw'] = 'h123yde'
        browser.submit()
        # Mr. Hyde should not be able to connect:
        if browser.response().read().find("Authorization failure") <= -1:
            # if we got here, things are broken:
            self.fail("Oops, Mr.Hyde should not be able to search Theses collection.")

    def test_restricted_detailed_record_page_as_anonymous_guest(self):
        """websearch - restricted detailed record page not accessible to guests"""
        browser = Browser()
        browser.open(CFG_SITE_URL + '/%s/35' % CFG_SITE_RECORD)
        if browser.response().read().find("You can use your nickname or your email address to login.") > -1:
            pass
        else:
            self.fail("Oops, searching restricted collection without password should have redirected to login dialog.")
        return

    def test_restricted_detailed_record_page_as_authorized_person(self):
        """websearch - restricted detailed record page accessible to authorized person"""
        browser = Browser()
        browser.open(CFG_SITE_URL + '/youraccount/login')
        browser.select_form(nr=0)
        browser['p_un'] = 'jekyll'
        browser['p_pw'] = 'j123ekyll'
        browser.submit()
        browser.open(CFG_SITE_URL + '/%s/35' % CFG_SITE_RECORD)
        # Dr. Jekyll should be able to connect
        # (add the pw to the whole CFG_SITE_URL because we shall be
        # redirected to '/reordrestricted/'):
        if browser.response().read().find("A High-performance Video Browsing System") > -1:
            pass
        else:
            self.fail("Oops, Dr. Jekyll should be able to access restricted detailed record page.")

    def test_restricted_detailed_record_page_as_unauthorized_person(self):
        """websearch - restricted detailed record page not accessible to unauthorized person"""
        browser = Browser()
        browser.open(CFG_SITE_URL + '/youraccount/login')
        browser.select_form(nr=0)
        browser['p_un'] = 'hyde'
        browser['p_pw'] = 'h123yde'
        browser.submit()
        browser.open(CFG_SITE_URL + '/%s/35' % CFG_SITE_RECORD)
        # Mr. Hyde should not be able to connect:
        if browser.response().read().find('You are not authorized') <= -1:
            # if we got here, things are broken:
            self.fail("Oops, Mr.Hyde should not be able to access restricted detailed record page.")

    def test_collection_restricted_p(self):
        """websearch - collection_restricted_p"""
        self.failUnless(collection_restricted_p('Theses'), True)
        self.failIf(collection_restricted_p('Books & Reports'))

    def test_get_permitted_restricted_collections(self):
        """websearch - get_permitted_restricted_collections"""
        from invenio.webuser import get_uid_from_email, collect_user_info
        self.assertEqual(get_permitted_restricted_collections(collect_user_info(get_uid_from_email('jekyll@cds.cern.ch'))), ['Theses', 'Drafts'])
        self.assertEqual(get_permitted_restricted_collections(collect_user_info(get_uid_from_email('hyde@cds.cern.ch'))), [])
        self.assertEqual(get_permitted_restricted_collections(collect_user_info(get_uid_from_email('balthasar.montague@cds.cern.ch'))), ['ALEPH Theses', 'ALEPH Internal Notes', 'Atlantis Times Drafts'])
        self.assertEqual(get_permitted_restricted_collections(collect_user_info(get_uid_from_email('dorian.gray@cds.cern.ch'))), ['ISOLDE Internal Notes'])

    def test_restricted_record_has_restriction_flag(self):
        """websearch - restricted record displays a restriction flag"""
        browser = Browser()
        browser.open(CFG_SITE_URL + '/%s/42/files/' % CFG_SITE_RECORD)
        browser.select_form(nr=0)
        browser['p_un'] = 'jekyll'
        browser['p_pw'] = 'j123ekyll'
        browser.submit()
        if browser.response().read().find("Restricted") > -1:
            pass
        else:
            self.fail("Oops, a 'Restricted' flag should appear on restricted records.")

        browser.open(CFG_SITE_URL + '/%s/42/files/comments' % CFG_SITE_RECORD)
        if browser.response().read().find("Restricted") > -1:
            pass
        else:
            self.fail("Oops, a 'Restricted' flag should appear on restricted records.")

        # Flag also appear on records that exist both in a public and
        # restricted collection:
        error_messages = test_web_page_content(CFG_SITE_URL + '/%s/109' % CFG_SITE_RECORD,
                                               username='admin',
                                               password='',
                                               expected_text=['Restricted'])
        if error_messages:
            self.fail("Oops, a 'Restricted' flag should appear on restricted records.")


class WebSearchRestrictedCollectionHandlingTest(InvenioTestCase):
    """
    Check how the restricted or restricted and "hidden" collection
    handling works: (i)user has or not rights to access to specific
    records or collections, (ii)public and restricted results are displayed
    in the right position in the collection tree, (iii)display the right
    warning depending on the case.

    Changes in the collection tree used for testing (are showed the records used for testing as well):

                  Articles & Preprints                                           Books & Reports
              _____________|________________                               ____________|_____________
              |        |          |        |                               |           |            |
          Articles   Drafts(r)  Notes   Preprints                         Books      Theses(r)    Reports
            69        77         109      10                                           105
            77        98                  98
           108       105

                                                      CERN Experiments
                                    _________________________|___________________________
                                    |                                                   |
                                  ALEPH                                              ISOLDE
                   _________________|_________________                      ____________|_____________
                   |                |                |                      |                        |
                 ALEPH            ALEPH            ALEPH                   ISOLDE                  ISOLDE
                Papers       Internal Notes(r)    Theses(r)                Papers               Internal Notes(r&h)
                  10               109              105                      69                       110
                 108                                106

    Authorized users:
        jekyll -> Drafts, Theses
        balthasar -> ALEPH Internal Notes, ALEPH Theses
        dorian -> ISOLDE Internal Notes
    """

    def test_show_public_colls_in_warning_as_unauthorizad_user(self):
        """websearch - show public daugther collections in warning to unauthorized user"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&cc=Articles+%26+Preprints&sc=1&p=recid:20',
                                               username='hyde',
                                               password='h123yde',
                                               expected_text=['No match found in collection <em>Articles, Preprints, Notes</em>.'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))


    def test_show_public_and_restricted_colls_in_warning_as_authorized_user(self):
        """websearch - show public and restricted daugther collections in warning to authorized user"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&cc=Articles+%26+Preprints&sc=1&p=recid:20',
                                               username='jekyll',
                                               password='j123ekyll',
                                               expected_text=['No match found in collection <em>Articles, Preprints, Notes, Drafts</em>.'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_restricted_record_in_different_colls_as_unauthorized_user(self):
        """websearch - record belongs to different restricted collections with different rights, user not has rights"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?p=105&f=recid',
                                               username='hyde',
                                               password='h123yde',
                                               expected_text=['No public collection matched your query.'],
                                               unexpected_text=['records found'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_restricted_record_in_different_colls_as_authorized_user_of_one_coll(self):
        """websearch - record belongs to different restricted collections with different rights, balthasar has rights to one of them"""
        from invenio.config import CFG_WEBSEARCH_VIEWRESTRCOLL_POLICY
        policy = CFG_WEBSEARCH_VIEWRESTRCOLL_POLICY.strip().upper()
        if policy == 'ANY':
            error_messages = test_web_page_content(CFG_SITE_URL + '/search?&sc=1&p=recid:105&c=Articles+%26+Preprints&c=Books+%26+Reports&c=Multimedia+%26+Arts',
                                                   username='balthasar',
                                                   password='b123althasar',
                                                   expected_text=['[CERN-THESIS-99-074]'],
                                                   unexpected_text=['No public collection matched your query.'])
        else:
            error_messages = test_web_page_content(CFG_SITE_URL + '/search?&sc=1&p=recid:105&c=Articles+%26+Preprints&c=Books+%26+Reports&c=Multimedia+%26+Arts',
                                                   username='balthasar',
                                                   password='b123althasar',
                                                   expected_text=['No public collection matched your query.'],
                                                   unexpected_text=['[CERN-THESIS-99-074]'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))


    def test_restricted_record_in_different_colls_as_authorized_user_of_two_colls(self):
        """websearch - record belongs to different restricted collections with different rights, jekyll has rights to two of them"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?&sc=1&p=recid:105&c=Articles+%26+Preprints&c=Books+%26+Reports&c=Multimedia+%26+Arts',
                                               username='jekyll',
                                               password='j123ekyll',
                                               expected_text=['Articles &amp; Preprints', 'Books &amp; Reports'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_restricted_record_in_different_colls_as_authorized_user_of_all_colls(self):
        """websearch - record belongs to different restricted collections with different rights, admin has rights to all of them"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?&sc=1&p=recid:105&c=Articles+%26+Preprints&c=Books+%26+Reports&c=Multimedia+%26+Arts',
                                               username='admin',
                                               expected_text=['Articles &amp; Preprints', 'Books &amp; Reports', 'ALEPH Theses'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_search_restricted_record_from_not_dad_coll(self):
        """websearch - record belongs to different restricted collections with different rights, search from a not dad collection"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&cc=Multimedia+%26+Arts&sc=1&p=recid%3A105&f=&action_search=Search&c=Pictures&c=Poetry&c=Atlantis+Times',
                                               username='admin',
                                               expected_text='No match found in collection',
                                               expected_link_label='1 hits')
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_public_and_restricted_record_as_unauthorized_user(self):
        """websearch - record belongs to different public and restricted collections, user not has rights"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?&sc=1&p=geometry&c=Articles+%26+Preprints&c=Books+%26+Reports&c=Multimedia+%26+Arts&of=id&so=a',
                                               username='guest',
                                               expected_text='[80, 86]',
                                               unexpected_text='[40, 80, 86]')
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_public_and_restricted_record_as_authorized_user(self):
        """websearch - record belongs to different public and restricted collections, admin has rights"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?&sc=1&p=geometry&c=Articles+%26+Preprints&c=Books+%26+Reports&c=Multimedia+%26+Arts&of=id&so=a',
                                               username='admin',
                                               password='',
                                               expected_text='[40, 80, 86]')
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_public_and_restricted_record_of_focus_as_unauthorized_user(self):
        """websearch - record belongs to both a public and a restricted collection of "focus on", user not has rights"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&cc=Articles+%26+Preprints&sc=1&p=109&f=recid',
                                               username='hyde',
                                               password='h123yde',
                                               expected_text=['No public collection matched your query'],
                                               unexpected_text=['LEP Center-of-Mass Energies in Presence of Opposite'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_public_and_restricted_record_of_focus_as_authorized_user(self):
        """websearch - record belongs to both a public and a restricted collection of "focus on", user has rights"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?&sc=1&p=109&f=recid&c=Articles+%26+Preprints&c=Books+%26+Reports&c=Multimedia+%26+Arts',
                                               username='balthasar',
                                               password='b123althasar',
                                               expected_text=['Articles &amp; Preprints', 'ALEPH Internal Notes', 'LEP Center-of-Mass Energies in Presence of Opposite'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_search_public_and_restricted_record_from_not_dad_coll_as_authorized_user(self):
        """websearch - record belongs to both a public and a restricted collection, search from a not dad collection, admin has rights"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&cc=Books+%26+Reports&sc=1&p=recid%3A98&f=&action_search=Search&c=Books&c=Reports',
                                               username='admin',
                                               password='',
                                               expected_text='No match found in collection <em>Books, Theses, Reports</em>',
                                               expected_link_label='1 hits')
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_search_public_and_restricted_record_from_not_dad_coll_as_unauthorized_user(self):
        """websearch - record belongs to both a public and a restricted collection, search from a not dad collection, hyde not has rights"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&cc=Books+%26+Reports&sc=1&p=recid%3A98&f=&action_search=Search&c=Books&c=Reports',
                                               username='hyde',
                                               password='h123yde',
                                               expected_text='No public collection matched your query',
                                               unexpected_text='No match found in collection')
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_restricted_record_of_focus_as_authorized_user(self):
        """websearch - record belongs to a restricted collection of "focus on", balthasar has rights"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?&sc=1&p=106&f=recid&c=Articles+%26+Preprints&c=Books+%26+Reports&c=Multimedia+%26+Arts&of=id',
                                               username='balthasar',
                                               password='b123althasar',
                                               expected_text='[106]',
                                               unexpected_text='[]')
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_display_dad_coll_of_restricted_coll_as_unauthorized_user(self):
        """websearch - unauthorized user displays a collection that contains a restricted collection"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&cc=Articles+%26+Preprints&sc=1&p=&f=&action_search=Search&c=Articles&c=Drafts&c=Preprints',
                                               username='guest',
                                               expected_text=['This collection is restricted.'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_display_dad_coll_of_restricted_coll_as_authorized_user(self):
        """websearch - authorized user displays a collection that contains a restricted collection"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&cc=Articles+%26+Preprints&sc=1&p=&f=&action_search=Search&c=Articles&c=Drafts&c=Notes&c=Preprints',
                                               username='jekyll',
                                               password='j123ekyll',
                                               expected_text=['Articles', 'Drafts', 'Notes', 'Preprints'],
                                               unexpected_text=['This collection is restricted.'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_search_restricted_record_from_coll_of_focus_as_unauthorized_user(self):
        """websearch - search for a record that belongs to a restricted collection from a collection of "focus on" , jekyll not has rights"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&cc=CERN+Divisions&sc=1&p=recid%3A106&f=&action_search=Search&c=Experimental+Physics+(EP)&c=Theoretical+Physics+(TH)',
                                               username='jekyll',
                                               password='j123ekyll',
                                               expected_text=['No public collection matched your query.'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_search_restricted_record_from_coll_of_focus_as_authorized_user(self):
        """websearch - search for a record that belongs to a restricted collection from a collection of "focus on" , admin has rights"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&cc=CERN+Divisions&sc=1&p=recid%3A106&f=&action_search=Search&c=Experimental+Physics+(EP)&c=Theoretical+Physics+(TH)',
                                               username='admin',
                                               password='',
                                               expected_text='No match found in collection <em>Experimental Physics (EP), Theoretical Physics (TH)</em>.',
                                               expected_link_label='1 hits')
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_search_restricted_record_from_not_direct_dad_coll_and_display_in_right_position_in_tree(self):
        """websearch - search for a restricted record from not direct dad collection and display it on its right position in the tree"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&sc=1&p=recid%3A40&f=&action_search=Search&c=Articles+%26+Preprints&c=Books+%26+Reports&c=Multimedia+%26+Arts',
                                               username='admin',
                                               password='',
                                               expected_text=['Books &amp; Reports','[LBL-22304]'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_search_restricted_record_from_direct_dad_coll_and_display_in_right_position_in_tree(self):
        """websearch - search for a restricted record from the direct dad collection and display it on its right position in the tree"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&cc=Books+%26+Reports&sc=1&p=recid%3A40&f=&action_search=Search&c=Books&c=Reports',
                                               username='admin',
                                               password='',
                                               expected_text=['Theses',  '[LBL-22304]'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_restricted_and_hidden_record_as_unauthorized_user(self):
        """websearch - search for a "hidden" record, user not has rights"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&sc=1&p=recid%3A110&f=&action_search=Search&c=Articles+%26+Preprints&c=Books+%26+Reports&c=Multimedia+%26+Arts',
                                               username='guest',
                                               expected_text=['If you were looking for a non-public document'],
                                               unexpected_text=['If you were looking for a hidden document'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_restricted_and_hidden_record_as_authorized_user(self):
        """websearch - search for a "hidden" record, admin has rights"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&sc=1&p=recid%3A110&f=&action_search=Search&c=Articles+%26+Preprints&c=Books+%26+Reports&c=Multimedia+%26+Arts',
                                               username='admin',
                                               password='',
                                               expected_text=['If you were looking for a hidden document, please type the correct URL for this record.'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_enter_url_of_restricted_and_hidden_coll_as_unauthorized_user(self):
        """websearch - unauthorized user types the concret URL of a "hidden" collection"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&cc=ISOLDE+Internal+Notes&sc=1&p=&f=&action_search=Search',
                                               username='guest',
                                               expected_text=['This collection is restricted.'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_enter_url_of_restricted_and_hidden_coll_as_authorized_user(self):
        """websearch - authorized user types the concret URL of a "hidden" collection"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&cc=ISOLDE+Internal+Notes&sc=1&p=&f=&action_search=Search',
                                               username='dorian',
                                               password='d123orian',
                                               expected_text=['ISOLDE Internal Notes', '[CERN-PS-PA-Note-93-04]'],
                                               unexpected_text=['This collection is restricted.'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_search_for_pattern_from_the_top_as_unauthorized_user(self):
        """websearch - unauthorized user searches for a pattern from the top"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&sc=1&p=of&f=&action_search=Search&c=Articles+%26+Preprints&c=Books+%26+Reports&c=Multimedia+%26+Arts',
                                               username='guest',
                                               expected_text=['Articles &amp; Preprints', '61', 'records found',
                                                              'Books &amp; Reports', '2', 'records found',
                                                              'Multimedia &amp; Arts', '14', 'records found'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_search_for_pattern_from_the_top_as_authorized_user(self):
        """websearch - authorized user searches for a pattern from the top"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&sc=1&p=of&f=&action_search=Search&c=Articles+%26+Preprints&c=Books+%26+Reports&c=Multimedia+%26+Arts',
                                               username='admin',
                                               password='',
                                               expected_text=['Articles &amp; Preprints', '61', 'records found',
                                                              'Books &amp; Reports', '6', 'records found',
                                                              'Multimedia &amp; Arts', '14', 'records found',
                                                              'ALEPH Theses', '1', 'records found',
                                                              'ALEPH Internal Notes', '1', 'records found'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_search_for_pattern_from_an_specific_coll_as_unauthorized_user(self):
        """websearch - unauthorized user searches for a pattern from one specific collection"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&cc=Books+%26+Reports&sc=1&p=of&f=&action_search=Search&c=Books&c=Reports',
                                               username='guest',
                                               expected_text=['Books', '1', 'records found',
                                                              'Reports', '1', 'records found'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_search_for_pattern_from_an_specific_coll_as_authorized_user(self):
        """websearch - authorized user searches for a pattern from one specific collection"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/search?ln=en&cc=Books+%26+Reports&sc=1&p=of&f=&action_search=Search&c=Books&c=Reports',
                                               username='admin',
                                               password='',
                                               expected_text=['Books', '1', 'records found',
                                                              'Reports', '1', 'records found',
                                                              'Theses', '4', 'records found'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))


class WebSearchRestrictedPicturesTest(InvenioTestCase):
    """
    Check whether restricted pictures on the demo site can be accessed
    well by people who have rights to access them.
    """

    def test_restricted_pictures_guest(self):
        """websearch - restricted pictures not available to guest"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/%s/1/files/0106015_01.jpg' % CFG_SITE_RECORD,
                                               expected_text=['This file is restricted.  If you think you have right to access it, please authenticate yourself.'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_restricted_pictures_romeo(self):
        """websearch - restricted pictures available to Romeo"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/%s/1/files/0106015_01.jpg' % CFG_SITE_RECORD,
                                               username='romeo',
                                               password='r123omeo',
                                               expected_text=[],
                                               unexpected_text=['This file is restricted',
                                                                'You are not authorized'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_restricted_pictures_hyde(self):
        """websearch - restricted pictures not available to Mr. Hyde"""

        error_messages = test_web_page_content(CFG_SITE_URL + '/%s/1/files/0106015_01.jpg' % CFG_SITE_RECORD,
                                               username='hyde',
                                               password='h123yde',
                                               expected_text=['This file is restricted',
                                                              'You are not authorized'])
        if error_messages:
            self.failUnless("HTTP Error 401: Unauthorized" in merge_error_messages(error_messages))

class WebSearchRestrictedWebJournalFilesTest(InvenioTestCase):
    """
    Check whether files attached to a WebJournal article are well
    accessible when the article is published
    """
    def test_restricted_files_guest(self):
        """websearch - files of unreleased articles are not available to guest"""

        # Record is not public...
        self.assertEqual(record_public_p(112), False)

        # ... and guest cannot access attached files
        error_messages = test_web_page_content(CFG_SITE_URL + '/%s/112/files/journal_galapagos_archipelago.jpg' % CFG_SITE_RECORD,
                                               expected_text=['This file is restricted.  If you think you have right to access it, please authenticate yourself.'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_restricted_files_editor(self):
        """websearch - files of unreleased articles are available to editor"""

        # Record is not public...
        self.assertEqual(record_public_p(112), False)

        # ... but editor can access attached files
        error_messages = test_web_page_content(CFG_SITE_URL + '/%s/112/files/journal_galapagos_archipelago.jpg' % CFG_SITE_RECORD,
                                               username='balthasar',
                                               password='b123althasar',
                                               expected_text=[],
                                               unexpected_text=['This file is restricted',
                                                                'You are not authorized'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_public_files_guest(self):
        """websearch - files of released articles are available to guest"""

        # Record is not public...
        self.assertEqual(record_public_p(111), False)

        # ... but user can access attached files, as article is released
        error_messages = test_web_page_content(CFG_SITE_URL + '/%s/111/files/journal_scissor_beak.jpg' % CFG_SITE_RECORD,
                                               expected_text=[],
                                                unexpected_text=['This file is restricted',
                                                                 'You are not authorized'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_really_restricted_files_guest(self):
        """websearch - restricted files of released articles are not available to guest"""

        # Record is not public...
        self.assertEqual(record_public_p(111), False)

        # ... and user cannot access restricted attachements, even if
        # article is released
        error_messages = test_web_page_content(CFG_SITE_URL + '/%s/111/files/restricted-journal_scissor_beak.jpg' % CFG_SITE_RECORD,
                                               expected_text=['This file is restricted.  If you think you have right to access it, please authenticate yourself.'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_restricted_picture_has_restriction_flag(self):
        """websearch - restricted files displays a restriction flag"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/%s/1/files/' % CFG_SITE_RECORD,
                                                  expected_text="Restricted")
        if error_messages:
            self.fail(merge_error_messages(error_messages))

class WebSearchRSSFeedServiceTest(InvenioTestCase):
    """Test of the RSS feed service."""

    def test_rss_feed_service(self):
        """websearch - RSS feed service"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/rss',
                                               expected_text='<rss version="2.0"'))

class WebSearchXSSVulnerabilityTest(InvenioTestCase):
    """Test possible XSS vulnerabilities of the search engine."""

    def test_xss_in_collection_interface_page(self):
        """websearch - no XSS vulnerability in collection interface pages"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/?c=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E',
                                               expected_text='Collection &amp;lt;SCRIPT&amp;gt;alert("XSS");&amp;lt;/SCRIPT&amp;gt; Not Found'))

    def test_xss_in_collection_search_page(self):
        """websearch - no XSS vulnerability in collection search pages"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?c=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E',
                                               expected_text='Collection &lt;SCRIPT&gt;alert("XSS");&lt;/SCRIPT&gt; Not Found'))

    def test_xss_in_simple_search(self):
        """websearch - no XSS vulnerability in simple search"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E',
                                               expected_text='Search term <em>&lt;SCRIPT&gt;alert("XSS");&lt;/SCRIPT&gt;</em> did not match any record.'))

    def test_xss_in_structured_search(self):
        """websearch - no XSS vulnerability in structured search"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E&f=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E',
                                               expected_text='No word index is available for <em>&lt;script&gt;alert("xss");&lt;/script&gt;</em>.'))

    def test_xss_in_advanced_search(self):
        """websearch - no XSS vulnerability in advanced search"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?as=1&p1=ellis&f1=author&op1=a&p2=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E&f2=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E&m2=e',
                                               expected_text='Search term <em>&lt;SCRIPT&gt;alert("XSS");&lt;/SCRIPT&gt;</em> inside index <em>&lt;script&gt;alert("xss");&lt;/script&gt;</em> did not match any record.'))

    def test_xss_in_browse(self):
        """websearch - no XSS vulnerability in browse"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E&f=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E&action_browse=Browse',
                                               expected_text='&lt;SCRIPT&gt;alert("XSS");&lt;/SCRIPT&gt;'))

class WebSearchResultsOverview(InvenioTestCase):
    """Test of the search results page's Results overview box and links."""

    def test_results_overview_split_off(self):
        """websearch - results overview box when split by collection is off"""
        browser = Browser()
        browser.open(CFG_SITE_URL + '/search?p=of&sc=0')
        body = browser.response().read()
        if body.find("Results overview") > -1:
            self.fail("Oops, when split by collection is off, "
                      "results overview should not be present.")
        if body.find('<a name="1"></a>') == -1:
            self.fail("Oops, when split by collection is off, "
                      "Atlantis collection should be found.")
        if body.find('<a name="15"></a>') > -1:
            self.fail("Oops, when split by collection is off, "
                      "Multimedia & Arts should not be found.")
        try:
            browser.find_link(url='#15')
            self.fail("Oops, when split by collection is off, "
                      "a link to Multimedia & Arts should not be found.")
        except LinkNotFoundError:
            pass

    def test_results_overview_split_on(self):
        """websearch - results overview box when split by collection is on"""
        browser = Browser()
        browser.open(CFG_SITE_URL + '/search?p=of&sc=1')
        body = browser.response().read()
        if body.find("Results overview") == -1:
            self.fail("Oops, when split by collection is on, "
                      "results overview should be present.")
        if body.find('<a name="Atlantis%20Institute%20of%20Fictive%20Science"></a>') > -1:
            self.fail("Oops, when split by collection is on, "
                      "Atlantis collection should not be found.")
        if body.find('<a name="15"></a>') == -1:
            self.fail("Oops, when split by collection is on, "
                      "Multimedia & Arts should be found.")
        try:
            browser.find_link(url='#15')
        except LinkNotFoundError:
            self.fail("Oops, when split by collection is on, "
                      "a link to Multimedia & Arts should be found.")

class WebSearchSortResultsTest(InvenioTestCase):
    """Test of the search results page's sorting capability."""

    def test_sort_results_default(self):
        """websearch - search results sorting, default method"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=of&f=title&rg=3',
                                               expected_text="CMS animation of the high-energy collisions"))

    def test_sort_results_ascending(self):
        """websearch - search results sorting, ascending field"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=of&f=title&rg=2&sf=reportnumber&so=a',
                                               expected_text="[astro-ph/0104076]"))

    def test_sort_results_descending(self):
        """websearch - search results sorting, descending field"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=of&f=title&rg=1&sf=reportnumber&so=d',
                                               expected_text=" [TESLA-FEL-99-07]"))

    def test_sort_results_sort_pattern(self):
        """websearch - search results sorting, preferential sort pattern"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=of&f=title&rg=1&sf=reportnumber&so=d&sp=cern',
                                               expected_text="[CERN-TH-2002-069]"))

class WebSearchSearchResultsXML(InvenioTestCase):
    """Test search results in various output"""

    def test_search_results_xm_output_split_on(self):
        """ websearch - check document element of search results in xm output (split by collection on)"""
        browser = Browser()
        browser.open(CFG_SITE_URL + '/search?sc=1&of=xm')
        body = browser.response().read()

        num_doc_element = body.count("<collection "
                                     "xmlns=\"http://www.loc.gov/MARC21/slim\">")
        if num_doc_element == 0:
            self.fail("Oops, no document element <collection "
                      "xmlns=\"http://www.loc.gov/MARC21/slim\">"
                      "found in search results.")
        elif num_doc_element > 1:
            self.fail("Oops, multiple document elements <collection> "
                      "found in search results.")

        num_doc_element = body.count("</collection>")
        if num_doc_element == 0:
            self.fail("Oops, no document element </collection> "
                      "found in search results.")
        elif num_doc_element > 1:
            self.fail("Oops, multiple document elements </collection> "
                      "found in search results.")


    def test_search_results_xm_output_split_off(self):
        """ websearch - check document element of search results in xm output (split by collection off)"""
        browser = Browser()
        browser.open(CFG_SITE_URL + '/search?sc=0&of=xm')
        body = browser.response().read()

        num_doc_element = body.count("<collection "
                                     "xmlns=\"http://www.loc.gov/MARC21/slim\">")
        if num_doc_element == 0:
            self.fail("Oops, no document element <collection "
                      "xmlns=\"http://www.loc.gov/MARC21/slim\">"
                      "found in search results.")
        elif num_doc_element > 1:
            self.fail("Oops, multiple document elements <collection> "
                      "found in search results.")

        num_doc_element = body.count("</collection>")
        if num_doc_element == 0:
            self.fail("Oops, no document element </collection> "
                      "found in search results.")
        elif num_doc_element > 1:
            self.fail("Oops, multiple document elements </collection> "
                      "found in search results.")

    def test_search_results_xd_output_split_on(self):
        """ websearch - check document element of search results in xd output (split by collection on)"""
        browser = Browser()
        browser.open(CFG_SITE_URL + '/search?sc=1&of=xd')
        body = browser.response().read()

        num_doc_element = body.count("<collection")
        if num_doc_element == 0:
            self.fail("Oops, no document element <collection "
                      "xmlns=\"http://www.loc.gov/MARC21/slim\">"
                      "found in search results.")
        elif num_doc_element > 1:
            self.fail("Oops, multiple document elements <collection> "
                      "found in search results.")

        num_doc_element = body.count("</collection>")
        if num_doc_element == 0:
            self.fail("Oops, no document element </collection> "
                      "found in search results.")
        elif num_doc_element > 1:
            self.fail("Oops, multiple document elements </collection> "
                      "found in search results.")


    def test_search_results_xd_output_split_off(self):
        """ websearch - check document element of search results in xd output (split by collection off)"""
        browser = Browser()
        browser.open(CFG_SITE_URL + '/search?sc=0&of=xd')
        body = browser.response().read()

        num_doc_element = body.count("<collection>")
        if num_doc_element == 0:
            self.fail("Oops, no document element <collection "
                      "xmlns=\"http://www.loc.gov/MARC21/slim\">"
                      "found in search results.")
        elif num_doc_element > 1:
            self.fail("Oops, multiple document elements <collection> "
                      "found in search results.")

        num_doc_element = body.count("</collection>")
        if num_doc_element == 0:
            self.fail("Oops, no document element </collection> "
                      "found in search results.")
        elif num_doc_element > 1:
            self.fail("Oops, multiple document elements </collection> "
                      "found in search results.")

class WebSearchUnicodeQueryTest(InvenioTestCase):
    """Test of the search results for queries containing Unicode characters."""

    def test_unicode_word_query(self):
        """websearch - Unicode word query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=title%3A%CE%99%CE%B8%CE%AC%CE%BA%CE%B7',
                                               expected_text="[76]"))

    def test_unicode_word_query_not_found_term(self):
        """websearch - Unicode word query, not found term"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=title%3A%CE%99%CE%B8',
                                               expected_text="ιθάκη"))

    def test_unicode_exact_phrase_query(self):
        """websearch - Unicode exact phrase query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=title%3A%22%CE%99%CE%B8%CE%AC%CE%BA%CE%B7%22',
                                               expected_text="[76]"))

    def test_unicode_partial_phrase_query(self):
        """websearch - Unicode partial phrase query"""
        # no hit here for example title partial phrase query due to
        # removed difference between double-quoted and single-quoted
        # search:
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=title%3A%27%CE%B7%27',
                                               expected_text="[]"))

    def test_unicode_regexp_query(self):
        """websearch - Unicode regexp query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=title%3A%2F%CE%B7%2F',
                                               expected_text="[76]"))

class WebSearchMARCQueryTest(InvenioTestCase):
    """Test of the search results for queries containing physical MARC tags."""

    def test_single_marc_tag_exact_phrase_query(self):
        """websearch - single MARC tag, exact phrase query (100__a)"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=100__a%3A%22Ellis%2C+J%22&so=a',
                                               expected_text="[9, 14, 18]"))

    def test_single_marc_tag_partial_phrase_query(self):
        """websearch - single MARC tag, partial phrase query (245__b)"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=245__b%3A%27and%27',
                                               expected_text="[28]"))

    def test_many_marc_tags_partial_phrase_query(self):
        """websearch - many MARC tags, partial phrase query (245)"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=245%3A%27and%27&rg=100&so=a',
                                               expected_text="[1, 8, 9, 14, 15, 20, 22, 24, 28, 33, 47, 48, 49, 51, 53, 64, 69, 71, 79, 82, 83, 85, 91, 96, 108]"))

    def test_single_marc_tag_regexp_query(self):
        """websearch - single MARC tag, regexp query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=245%3A%2Fand%2F&rg=100&so=a',
                                               expected_text="[1, 8, 9, 14, 15, 20, 22, 24, 28, 33, 47, 48, 49, 51, 53, 64, 69, 71, 79, 82, 83, 85, 91, 96, 108]"))

class WebSearchExtSysnoQueryTest(InvenioTestCase):
    """Test of queries using external system numbers."""

    def test_existing_sysno_html_output(self):
        """websearch - external sysno query, existing sysno, HTML output"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?sysno=000289446CER',
                                               expected_text="The wall of the cave"))

    def test_existing_sysno_id_output(self):
        """websearch - external sysno query, existing sysno, ID output"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?sysno=000289446CER&of=id',
                                               expected_text="[95]"))

    def test_nonexisting_sysno_html_output(self):
        """websearch - external sysno query, non-existing sysno, HTML output"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?sysno=000289446CERRRR',
                                               expected_text="Requested record does not seem to exist."))

    def test_nonexisting_sysno_id_output(self):
        """websearch - external sysno query, non-existing sysno, ID output"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?sysno=000289446CERRRR&of=id',
                                               expected_text="[]"))

class WebSearchResultsRecordGroupingTest(InvenioTestCase):
    """Test search results page record grouping (rg)."""

    def test_search_results_rg_guest(self):
        """websearch - search results, records in groups of, guest"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?rg=17',
                                               expected_text="1 - 17"))

    def test_search_results_rg_nonguest(self):
        """websearch - search results, records in groups of, non-guest"""
        # This test used to fail due to saved user preference fetching
        # not overridden by URL rg argument.
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?rg=17',
                                               username='admin',
                                               expected_text="1 - 17"))

class WebSearchSpecialTermsQueryTest(InvenioTestCase):
    """Test of the search results for queries containing special terms."""

    def test_special_terms_u1(self):
        """websearch - query for special terms, U(1)"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=U%281%29',
                                               expected_text="[88, 80, 79, 57]"))

    def test_special_terms_u1_and_sl(self):
        """websearch - query for special terms, U(1) SL(2,Z)"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=U%281%29+SL%282%2CZ%29',
                                               expected_text="[88]"))

    def test_special_terms_u1_and_sl_or(self):
        """websearch - query for special terms, U(1) OR SL(2,Z)"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=U%281%29+OR+SL%282%2CZ%29',
                                               expected_text="[88, 80, 79, 57]"))

    @nottest
    def FIXME_TICKET_453_test_special_terms_u1_and_sl_or_parens(self):
        """websearch - query for special terms, (U(1) OR SL(2,Z))"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=%28U%281%29+OR+SL%282%2CZ%29%29',
                                               expected_text="[57, 79, 80, 88]"))

    def test_special_terms_u1_and_sl_in_quotes(self):
        """websearch - query for special terms, ('SL(2,Z)' OR 'U(1)')"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + "/search?of=id&p=%28%27SL%282%2CZ%29%27+OR+%27U%281%29%27%29",
                                               expected_text="[96, 88, 80, 79, 57]"))


class WebSearchJournalQueryTest(InvenioTestCase):
    """Test of the search results for journal pubinfo queries."""

    def test_query_journal_title_only(self):
        """websearch - journal publication info query, title only"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&f=journal&p=Phys.+Lett.+B&so=a',
                                               expected_text="[78, 85, 87]"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&f=journal&p=Phys.+Lett.+B&so=a',
                                               username='admin',
                                               expected_text="[77, 78, 85, 87]"))

    def test_query_journal_full_pubinfo(self):
        """websearch - journal publication info query, full reference"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&f=journal&p=Phys.+Lett.+B+531+%282002%29+301',
                                               expected_text="[78]"))

class WebSearchStemmedIndexQueryTest(InvenioTestCase):
    """Test of the search results for queries using stemmed indexes."""

    def test_query_stemmed_lowercase(self):
        """websearch - stemmed index query, lowercase"""
        # note that dasse/Dasse is stemmed into dass/Dass, as expected
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=dasse',
                                               expected_text="[26, 25]"))

    def test_query_stemmed_uppercase(self):
        """websearch - stemmed index query, uppercase"""
        # ... but note also that DASSE is stemmed into DASSE(!); so
        # the test would fail if the search engine would not lower the
        # query term.  (Something that is not necessary for
        # non-stemmed indexes.)
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=DASSE',
                                               expected_text="[26, 25]"))

class WebSearchSummarizerTest(InvenioTestCase):
    """Test of the search results summarizer functions."""

    def test_most_popular_field_values_singletag(self):
        """websearch - most popular field values, simple tag"""
        from invenio.search_engine import get_most_popular_field_values
        self.assertEqual([('PREPRINT', 37), ('ARTICLE', 28), ('BOOK', 14), ('THESIS', 8), ('PICTURE', 7),
                         ('DRAFT', 2), ('POETRY', 2), ('REPORT', 2), ('ALEPHPAPER', 1), ('ATLANTISTIMESNEWS', 1),
                         ('ISOLDEPAPER', 1)],
                         get_most_popular_field_values(range(0,100), '980__a'))

    def test_most_popular_field_values_singletag_multiexclusion(self):
        """websearch - most popular field values, simple tag, multiple exclusions"""
        from invenio.search_engine import get_most_popular_field_values
        self.assertEqual([('PREPRINT', 37), ('ARTICLE', 28), ('BOOK', 14), ('DRAFT', 2), ('REPORT', 2),
                          ('ALEPHPAPER', 1), ('ATLANTISTIMESNEWS', 1), ('ISOLDEPAPER', 1)],
                         get_most_popular_field_values(range(0,100), '980__a', ('THESIS', 'PICTURE', 'POETRY')))

    def test_most_popular_field_values_multitag(self):
        """websearch - most popular field values, multiple tags"""
        from invenio.search_engine import get_most_popular_field_values
        self.assertEqual([('Ellis, J', 3), ('Enqvist, K', 1), ('Ibanez, L E', 1), ('Nanopoulos, D V', 1), ('Ross, G G', 1)],
                         get_most_popular_field_values((9, 14, 18), ('100__a', '700__a')))

    def test_most_popular_field_values_multitag_singleexclusion(self):
        """websearch - most popular field values, multiple tags, single exclusion"""
        from invenio.search_engine import get_most_popular_field_values
        self.assertEqual([('Enqvist, K', 1), ('Ibanez, L E', 1), ('Nanopoulos, D V', 1), ('Ross, G G', 1)],
                         get_most_popular_field_values((9, 14, 18), ('100__a', '700__a'), ('Ellis, J')))

    def test_most_popular_field_values_multitag_countrepetitive(self):
        """websearch - most popular field values, multiple tags, counting repetitive occurrences"""
        from invenio.search_engine import get_most_popular_field_values
        self.assertEqual([('THESIS', 2), ('REPORT', 1)],
                         get_most_popular_field_values((41,), ('690C_a', '980__a'), count_repetitive_values=True))
        self.assertEqual([('REPORT', 1), ('THESIS', 1)],
                         get_most_popular_field_values((41,), ('690C_a', '980__a'), count_repetitive_values=False))

    def test_ellis_citation_summary(self):
        """websearch - query ellis, citation summary output format"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis&of=hcs',
                                               expected_text="Less known papers (1-9)",
                                               expected_link_target=CFG_BASE_URL+"/search?p=ellis%20AND%20cited%3A1-%3E9",
                                               expected_link_label='1'))

    def test_ellis_not_quark_citation_summary_advanced(self):
        """websearch - ellis and not quark, citation summary format advanced"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?ln=en&as=1&m1=a&p1=ellis&f1=author&op1=n&m2=a&p2=quark&f2=&op2=a&m3=a&p3=&f3=&action_search=Search&sf=&so=a&rm=&rg=10&sc=1&of=hcs',
                                               expected_text="Less known papers (1-9)",
                                               expected_link_target=CFG_BASE_URL+'/search?p=author%3Aellis%20and%20not%20quark%20AND%20cited%3A1-%3E9',
                                               expected_link_label='1'))

    def test_ellis_not_quark_citation_summary_regular(self):
        """websearch - ellis and not quark, citation summary format advanced"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=author%3Aellis+and+not+quark&f=&action_search=Search&sf=&so=d&rm=&rg=10&sc=0&of=hcs',
                                               expected_text="Less known papers (1-9)",
                                               expected_link_target=CFG_BASE_URL+'/search?p=author%3Aellis%20and%20not%20quark%20AND%20cited%3A1-%3E9',
                                               expected_link_label='1'))


class WebSearchRecordCollectionGuessTest(InvenioTestCase):
    """Primary collection guessing tests."""

    def test_guess_primary_collection_of_a_record(self):
        """websearch - guess_primary_collection_of_a_record"""
        self.assertEqual(guess_primary_collection_of_a_record(96), 'Articles')

    def test_guess_collection_of_a_record(self):
        """websearch - guess_collection_of_a_record"""
        self.assertEqual(guess_collection_of_a_record(96), 'Articles')
        self.assertEqual(guess_collection_of_a_record(96, '%s/collection/Theoretical Physics (TH)?ln=en' % CFG_SITE_URL), 'Articles')
        self.assertEqual(guess_collection_of_a_record(12, '%s/collection/Theoretical Physics (TH)?ln=en' % CFG_SITE_URL), 'Theoretical Physics (TH)')
        self.assertEqual(guess_collection_of_a_record(12, '%s/collection/Theoretical%%20Physics%%20%%28TH%%29?ln=en' % CFG_SITE_URL), 'Theoretical Physics (TH)')

class WebSearchGetFieldValuesTest(InvenioTestCase):
    """Testing get_fieldvalues() function."""

    def test_get_fieldvalues_001(self):
        """websearch - get_fieldvalues() for bibxxx-agnostic tags"""
        self.assertEqual(get_fieldvalues(10, '001___'), ['10'])

    def test_get_fieldvalues_980(self):
        """websearch - get_fieldvalues() for bibxxx-powered tags"""
        self.assertEqual(get_fieldvalues(18, '700__a'), ['Enqvist, K', 'Nanopoulos, D V'])
        self.assertEqual(get_fieldvalues(18, '909C1u'), ['CERN'])

    def test_get_fieldvalues_wildcard(self):
        """websearch - get_fieldvalues() for tag wildcards"""
        self.assertEqual(get_fieldvalues(18, '%'), [])
        self.assertEqual(get_fieldvalues(18, '7%'), [])
        self.assertEqual(get_fieldvalues(18, '700%'), ['Enqvist, K', 'Nanopoulos, D V'])
        self.assertEqual(get_fieldvalues(18, '909C0%'), ['1985', '13','TH'])

    def test_get_fieldvalues_recIDs(self):
        """websearch - get_fieldvalues() for list of recIDs"""
        self.assertEqual(get_fieldvalues([], '001___'), [])
        self.assertEqual(get_fieldvalues([], '700__a'), [])
        self.assertEqual(get_fieldvalues([10, 13], '001___'), ['10', '13'])
        self.assertEqual(get_fieldvalues([18, 13], '700__a'),
                         ['Dawson, S', 'Ellis, R K', 'Enqvist, K', 'Nanopoulos, D V'])

    def test_get_fieldvalues_repetitive(self):
        """websearch - get_fieldvalues() for repetitive values"""
        self.assertEqual(get_fieldvalues([17, 18], '909C1u'),
                         ['CERN', 'CERN'])
        self.assertEqual(get_fieldvalues([17, 18], '909C1u', repetitive_values=True),
                         ['CERN', 'CERN'])
        self.assertEqual(get_fieldvalues([17, 18], '909C1u', repetitive_values=False),
                         ['CERN'])

class WebSearchAddToBasketTest(InvenioTestCase):
    """Test of the add-to-basket presence depending on user rights."""

    def test_add_to_basket_guest(self):
        """websearch - add-to-basket facility allowed for guests"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=recid%3A10',
                                               expected_text='Add to basket'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=recid%3A10',
                                               expected_text='<input name="recid" type="checkbox" value="10" />'))

    def test_add_to_basket_jekyll(self):
        """websearch - add-to-basket facility allowed for Dr. Jekyll"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=recid%3A10',
                                               expected_text='Add to basket',
                                               username='jekyll',
                                               password='j123ekyll'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=recid%3A10',
                                               expected_text='<input name="recid" type="checkbox" value="10" />',
                                               username='jekyll',
                                               password='j123ekyll'))

    def test_add_to_basket_hyde(self):
        """websearch - add-to-basket facility denied to Mr. Hyde"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=recid%3A10',
                                               unexpected_text='Add to basket',
                                               username='hyde',
                                               password='h123yde'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=recid%3A10',
                                               unexpected_text='<input name="recid" type="checkbox" value="10" />',
                                               username='hyde',
                                               password='h123yde'))

class WebSearchAlertTeaserTest(InvenioTestCase):
    """Test of the alert teaser presence depending on user rights."""

    def test_alert_teaser_guest(self):
        """websearch - alert teaser allowed for guests"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis',
                                               expected_link_label='email alert'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis',
                                               expected_text='RSS feed'))

    def test_alert_teaser_jekyll(self):
        """websearch - alert teaser allowed for Dr. Jekyll"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis',
                                               expected_text='email alert',
                                               username='jekyll',
                                               password='j123ekyll'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis',
                                               expected_text='RSS feed',
                                               username='jekyll',
                                               password='j123ekyll'))

    def test_alert_teaser_hyde(self):
        """websearch - alert teaser allowed for Mr. Hyde"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis',
                                               expected_text='email alert',
                                               username='hyde',
                                               password='h123yde'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis',
                                               expected_text='RSS feed',
                                               username='hyde',
                                               password='h123yde'))


class WebSearchSpanQueryTest(InvenioTestCase):
    """Test of span queries."""

    def test_span_in_word_index(self):
        """websearch - span query in a word index"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=year%3A1992-%3E1996&of=id&ap=0',
                                               expected_text='[71, 69, 66, 17]'))

    def test_span_in_phrase_index(self):
        """websearch - span query in a phrase index"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=year%3A%221992%22-%3E%221996%22&of=id&ap=0',
                                               expected_text='[71, 69, 66, 17]'))

    def test_span_in_bibxxx(self):
        """websearch - span query in MARC tables"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=909C0y%3A%221992%22-%3E%221996%22&of=id&ap=0',
                                               expected_text='[71, 69, 66, 17]'))

    def test_span_with_spaces(self):
        """websearch - no span query when a space is around"""
        # useful for reaction search
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=title%3A%27mu%20--%3E%20e%27&of=id&ap=0',
                                               expected_text='[67]'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=245%3A%27mu%20--%3E%20e%27&of=id&ap=0',
                                               expected_text='[67]'))

    def test_span_in_author(self):
        """websearch - span query in special author index"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=author%3A%22Ellis,%20K%22-%3E%22Ellis,%20RZ%22&of=id&ap=0',
                                               expected_text='[47, 18, 17, 14, 13, 12, 11, 9, 8]'))


class WebSearchReferstoCitedbyTest(InvenioTestCase):
    """Test of refersto/citedby search operators."""

    def test_refersto_recid(self):
        'websearch - refersto:recid:84'
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=refersto%3Arecid%3A84&of=id&ap=0&so=a',
                                               expected_text='[85, 88, 91]'))

    def test_refersto_repno(self):
        'websearch - refersto:reportnumber:hep-th/0205061'
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=refersto%3Areportnumber%3Ahep-th/0205061&of=id&ap=0',
                                               expected_text='[91]'))

    def test_refersto_author_word(self):
        'websearch - refersto:author:klebanov'
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=refersto%3Aauthor%3Aklebanov&of=id&ap=0&so=a',
                                               expected_text='[85, 86, 88, 91]'))

    def test_refersto_author_phrase(self):
        'websearch - refersto:author:"Klebanov, I"'
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=refersto%3Aauthor%3A%22Klebanov,%20I%22&of=id&ap=0&so=a',
                                               expected_text='[85, 86, 88, 91]'))

    def test_citedby_recid(self):
        'websearch - citedby:recid:92'
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=citedby%3Arecid%3A92&of=id&ap=0&so=a',
                                               expected_text='[74, 91]'))

    def test_citedby_repno(self):
        'websearch - citedby:reportnumber:hep-th/0205061'
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=citedby%3Areportnumber%3Ahep-th/0205061&of=id&ap=0',
                                               expected_text='[78]'))

    def test_citedby_author_word(self):
        'websearch - citedby:author:klebanov'
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=citedby%3Aauthor%3Aklebanov&of=id&ap=0',
                                               expected_text='[95]'))

    def test_citedby_author_phrase(self):
        'websearch - citedby:author:"Klebanov, I"'
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=citedby%3Aauthor%3A%22Klebanov,%20I%22&of=id&ap=0',
                                               expected_text='[95]'))

    def test_refersto_bad_query(self):
        'websearch - refersto:title:'
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=refersto%3Atitle%3A',
                                               expected_text='There are no records referring to title:.'))

    def test_citedby_bad_query(self):
        'websearch - citedby:title:'
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=citedby%3Atitle%3A',
                                               expected_text='There are no records cited by title:.'))


class WebSearchSPIRESSyntaxTest(InvenioTestCase):
    """Test of SPIRES syntax issues"""

    if CFG_WEBSEARCH_SPIRES_SYNTAX > 0:
        def test_and_not_parens(self):
            'websearch - find a ellis, j and not a enqvist'
            self.assertEqual([],
                             test_web_page_content(CFG_SITE_URL +'/search?p=find+a+ellis%2C+j+and+not+a+enqvist&of=id&ap=0&so=a',
                                                   expected_text='[9, 12, 14, 47]'))

    if DATEUTIL_AVAILABLE:
        def test_dadd_search(self):
            'websearch - find da > today - 3650'
            # XXX: assumes we've reinstalled our site in the last 10 years
            # should return every document in the system
            self.assertEqual([],
                             test_web_page_content(CFG_SITE_URL +'/search?ln=en&p=find+da+%3E+today+-+3650&f=&of=id&so=a&rg=0',
                                                  expected_text='[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 99, 100, 101, 102, 103, 104, 107, 108, 113, 127, 128]'))


class WebSearchDateQueryTest(InvenioTestCase):
    """Test various date queries."""

    def setUp(self):
        """Establish variables we plan to re-use"""
        self.empty = intbitset()

    def test_search_unit_hits_for_datecreated_previous_millenia(self):
        """websearch - search_unit with datecreated returns >0 hits for docs in the last 1000 years"""
        self.assertNotEqual(self.empty, search_unit('1000-01-01->9999-12-31', 'datecreated'))

    def test_search_unit_hits_for_datemodified_previous_millenia(self):
        """websearch - search_unit with datemodified returns >0 hits for docs in the last 1000 years"""
        self.assertNotEqual(self.empty, search_unit('1000-01-01->9999-12-31', 'datemodified'))

    def test_search_unit_in_bibrec_for_datecreated_previous_millenia(self):
        """websearch - search_unit_in_bibrec with creationdate gets >0 hits for past 1000 years"""
        self.assertNotEqual(self.empty, search_unit_in_bibrec("1000-01-01", "9999-12-31", 'creationdate'))

    def test_search_unit_in_bibrec_for_datecreated_next_millenia(self):
        """websearch - search_unit_in_bibrec with creationdate gets 0 hits for after year 3000"""
        self.assertEqual(self.empty, search_unit_in_bibrec("3000-01-01", "9999-12-31", 'creationdate'))


class WebSearchSynonymQueryTest(InvenioTestCase):
    """Test of queries using synonyms."""

    def test_journal_phrvd(self):
        """websearch - search-time synonym search, journal title"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=PHRVD&f=journal&of=id',
                                               expected_text="[72, 66]"))

    def test_journal_phrvd_54_1996_4234(self):
        """websearch - search-time synonym search, journal article"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=PHRVD%2054%20%281996%29%204234&f=journal&of=id',
                                               expected_text="[66]"))

    def test_journal_beta_decay_title(self):
        """websearch - index-time synonym search, beta decay in title"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=beta+decay&f=title&of=id',
                                               expected_text="[59]"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%CE%B2+decay&f=title&of=id',
                                               expected_text="[59]"))

    def test_journal_beta_decay_global(self):
        """websearch - index-time synonym search, beta decay in any field"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=beta+decay&of=id',
                                               expected_text="[59, 52]"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%CE%B2+decay&of=id',
                                               expected_text="[59]"))

    def test_journal_beta_title(self):
        """websearch - index-time synonym search, beta in title"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=beta&f=title&of=id',
                                               expected_text="[59]"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%CE%B2&f=title&of=id',
                                               expected_text="[59]"))

    def test_journal_beta_global(self):
        """websearch - index-time synonym search, beta in any field"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=beta&of=id',
                                               expected_text="[59, 52]"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%CE%B2&of=id',
                                               expected_text="[59]"))

class WebSearchWashCollectionsTest(InvenioTestCase):
    """Test if the collection argument is washed correctly"""

    def test_wash_coll_when_coll_restricted(self):
        """websearch - washing of restricted daughter collections"""
        self.assertEqual(
            sorted(wash_colls(cc='', c=['Books & Reports', 'Theses'])[1]),
            ['Books & Reports', 'Theses'])
        self.assertEqual(
            sorted(wash_colls(cc='', c=['Books & Reports', 'Theses'])[2]),
            ['Books & Reports', 'Theses'])


class WebSearchAuthorCountQueryTest(InvenioTestCase):
    """Test of queries using authorcount fields."""

    def test_journal_authorcount_word(self):
        """websearch - author count, word query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=4&f=authorcount&of=id&so=a',
                                               expected_text="[51, 54, 59, 66, 92, 96]"))

    def test_journal_authorcount_phrase(self):
        """websearch - author count, phrase query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%224%22&f=authorcount&of=id&so=a',
                                               expected_text="[51, 54, 59, 66, 92, 96]"))

    def test_journal_authorcount_span(self):
        """websearch - author count, span query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=authorcount%3A9-%3E16&of=id&so=a',
                                               expected_text="[69, 71, 127]"))

    def test_journal_authorcount_plus(self):
        """websearch - author count, plus query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=50%2B&f=authorcount&of=id&so=a',
                                               expected_text="[10, 17]"))


class WebSearchItemCountQueryTest(InvenioTestCase):
    """Test of queries using itemcount field/index"""

    def test_itemcount_plus(self):
        """websearch - item count, search for more than one item, using 'plus'"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=2%2B&f=itemcount&of=id&so=a',
                                               expected_text="[31, 32, 34]"))

    def test_itemcount_span(self):
        """websearch - item count, search for more than one item, using 'span'"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=2->10&f=itemcount&of=id&so=a',
                                               expected_text="[31, 32, 34]"))

    def test_itemcount_phrase(self):
        """websearch - item count, search for records with exactly two items, phrase"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%222%22&f=itemcount&of=id&so=a',
                                               expected_text="[31, 34]"))

    def test_itemcount_records_with_two_items(self):
        """websearch - item count, search for records with exactly two items"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=2&f=itemcount&of=id&so=a',
                                               expected_text="[31, 34]"))


class WebSearchFiletypeQueryTest(InvenioTestCase):
    """Test of queries using filetype fields."""

    def test_mpg_filetype(self):
        """websearch - file type, query for tif extension"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=mpg&f=filetype&of=id',
                                               expected_text="[113]"))

    def test_tif_filetype_and_word_study(self):
        """websearch - file type, query for tif extension and word 'study'"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=study+filetype%3Atif&of=id',
                                               expected_text="[71]"))

    def test_pdf_filetype_and_phrase(self):
        """websearch - file type, query for pdf extension and phrase 'parameter test'"""
        self.assertEqual([],
                  test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=filetype%3Apdf+parameter+test&of=id&so=a',
                                        expected_text="[50, 93]"))


class WebSearchFilenameQueryTest(InvenioTestCase):
    """Test of queries using filename fields."""

    def test_search_for_main_file_name(self):
        """websearch - file name, query for name without extension"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=0402130&f=filename&of=id',
                                               expected_text="[89]"))

    def test_search_for_file_name_with_extension(self):
        """websearch - file name, query for name with extension"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=0210075.ps.gz&f=filename&of=id',
                                               expected_text="[83]"))

    def test_search_for_file_name_with_part_of_extension(self):
        """websearch - file name, query for name and part of extension"""
        self.assertEqual([],
                  test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=filename:0212138.ps&of=id&so=a',
                                        expected_text="[84]"))

    def test_search_for_file_name_with_wildcard(self):
        """websearch - file name, query with wildcard"""
        self.assertEqual([],
                  test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=filename:convert*&of=id&so=a',
                                        expected_text="[66, 71, 97]"))

    def test_search_for_file_name_with_span(self):
        """websearch - file name, query with span"""
        self.assertEqual([],
                  test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=filename:6->7&of=id&so=a',
                                        expected_text="[3, 6]"))


def make_fake_request(admin_user=True):
    environ = {'wsgi.errors': cStringIO.StringIO(),
               'QUERY_STRING': '',
               'PATH_INFO': ''}
    if admin_user:
        user_info = {'uid': 1, 'guest': '0', 'email': '', 'nickname': ''}
    else:
        user_info = {'uid': 2, 'guest': '1', 'email': '', 'nickname': ''}
    user_info['precached_permitted_restricted_collections'] = get_permitted_restricted_collections(user_info)
    buf = cStringIO.StringIO()

    def start_response(status, response_headers, exc_info=None):
        return buf.write

    req = SimulatedModPythonRequest(environ, start_response)
    req._user_info = user_info
    req.test_output_buffer = buf
    return req


class WebSearchPerformRequestSearchRefactoringTest(InvenioTestCase):
    """Tests the perform request search API after refactoring."""

    def _run_test(self, test_args, expected_results):
        params = {}
        params.update(map(lambda y: (y[0], ',' in y[1] and ', ' not in y[1] and y[1].split(',') or y[1]), map(lambda x: x.split('=', 1), test_args.split(';'))))

        if isinstance(expected_results, str):
            req = make_fake_request()
            params['req'] = req

        recs = perform_request_search(**params)

        if isinstance(expected_results, str):
            recs = req.test_output_buffer.getvalue()

        # this is just used to generate the results from the seearch engine before refactoring
        #if recs != expected_results:
        #    print test_args
        #    print params
        #    print recs

        self.assertEqual(recs, expected_results, "Error, we expect: %s, and we received: %s" % (expected_results, recs))



    def test_queries(self):
        """websearch - testing p_r_s standard arguments and their combinations"""

        self._run_test('p=ellis;f=author;action=Search', [8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 47])

        self._run_test('p=ellis;f=author;sf=title;action=Search', [8, 16, 14, 9, 11, 17, 18, 12, 10, 47, 13])

        self._run_test('p=ellis;f=author;sf=title;wl=5;action=Search', [8, 16, 14, 9, 11, 17, 18, 12, 10, 47, 13])

        self._run_test('p=ellis;f=author;sf=title;wl=5;so=a', [8, 16, 14, 9, 11, 17, 18, 12, 10, 47, 13])

        self._run_test('p=ellis;f=author;sf=title;wl=5;so=d', [13, 47, 10, 12, 18, 17, 11, 9, 14, 16, 8])

        self._run_test('p=ell*;sf=title;wl=5', [8, 15, 16, 14, 9, 11, 17, 18, 12, 10, 47, 13])

        self._run_test('p=ell*;sf=title;wl=1', [10])

        self._run_test('p=ell*;sf=title;wl=100', [8, 15, 16, 14, 9, 11, 17, 18, 12, 10, 47, 13])

        self._run_test('p=muon OR kaon;f=author;sf=title;wl=5;action=Search', [])

        self._run_test('p=muon OR kaon;sf=title;wl=5;action=Search', [67, 12])

        self._run_test('p=muon OR kaon;sf=title;wl=5;c=Articles,Preprints', [67, 12])

        self._run_test('p=muon OR kaon;sf=title;wl=5;c=Articles', [67])

        self._run_test('p=muon OR kaon;sf=title;wl=5;c=Preprints', [12])

        self._run_test('p=el*;rm=citation;so=a', [2, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 23, 30, 32, 34, 47, 48, 51, 52, 54, 56, 58, 59, 92, 97, 100, 103, 109, 127, 128, 18, 74, 91, 94, 81])
        self._run_test('p=el*;rm=citation;so=d', list(reversed([2, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 23, 30, 32, 34, 47, 48, 51, 52, 54, 56, 58, 59, 92, 97, 100, 103, 109, 127, 128, 18, 74, 91, 94, 81])))

        if not get_external_word_similarity_ranker():
            self._run_test('p=el*;rm=wrd', [2, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 23, 30, 32, 34, 47, 48, 51, 52, 54, 56, 58, 59, 74, 81, 91, 92, 94, 97, 100, 103, 109, 127, 128])

        self._run_test('p=el*;sf=title', [100, 32, 8, 15, 16, 81, 97, 34, 23, 127, 58, 2, 14, 9, 128, 11, 30, 109, 52, 48, 94, 17, 56, 18, 91, 59, 12, 92, 74, 54, 103, 10, 51, 47, 13])

        self._run_test('p=boson;rm=citation', [1, 47, 50, 107, 108, 77, 95])

        if not get_external_word_similarity_ranker():
            self._run_test('p=boson;rm=wrd', [47, 50, 77, 95, 108, 1, 107])

        self._run_test('p1=ellis;f1=author;m1=a;op1=a;p2=john;f2=author;m2=a', [9, 12, 14, 18])

        self._run_test('p1=ellis;f1=author;m1=o;op1=a;p2=john;f2=author;m2=o', [9, 12, 14, 18])

        self._run_test('p1=ellis;f1=author;m1=e;op1=a;p2=john;f2=author;m2=e', [])

        self._run_test('p1=ellis;f1=author;m1=a;op1=o;p2=john;f2=author;m2=a', [8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 47])

        self._run_test('p1=ellis;f1=author;m1=o;op1=o;p2=john;f2=author;m2=o', [8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 47])

        self._run_test('p1=ellis;f1=author;m1=e;op1=o;p2=john;f2=author;m2=e', [])

        self._run_test('p1=ellis;f1=author;m1=a;op1=n;p2=john;f2=author;m2=a', [8, 10, 11, 13, 16, 17, 47])

        self._run_test('p1=ellis;f1=author;m1=o;op1=n;p2=john;f2=author;m2=o', [8, 10, 11, 13, 16, 17, 47])

        self._run_test('p1=ellis;f1=author;m1=e;op1=n;p2=john;f2=author;m2=e', [])

        self._run_test('p=Ellis, J;ap=1', [9, 10, 11, 12, 14, 17, 18, 47])

        self._run_test('p=Ellis, J;ap=0', [9, 10, 11, 12, 14, 17, 18, 47])

        self._run_test('p=recid:148x', [])

        self._run_test('p=recid:148x;of=xm;rg=200', "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<collection xmlns=\"http://www.loc.gov/MARC21/slim\">\n\n</collection>")


class WebSearchDOIQueryTest(InvenioTestCase):
    """Tests queries using doi field."""

    def test_span_doi_search(self):
        """websearch - doi, span query 1->9"""
        errors = test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=doi%3A1->9&of=id',
                                       expected_text="[128, 127, 96]")
        self.assertEqual(True, errors == [])

    def test_doi_wildcard(self):
        """websearch - doi, query for '10.1063%'"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=doi%3A10.1063%25&of=id',
                                               expected_text="[127]"))

    def test_doi_negative_search(self):
        """websearch - doi, query for 'VDB:88636' """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=VDB%3A88636&f=doi&of=id',
                                               expected_text="[]"))


class WebSearchGetRecordTests(InvenioTestCase):
    def setUp(self):
        self.recid = run_sql("INSERT INTO bibrec(creation_date, modification_date) VALUES(NOW(), NOW())")

    def tearDown(self):
        run_sql("DELETE FROM bibrec WHERE id=%s", (self.recid,))

    def test_get_record(self):
        """bibformat - test print_record and get_record of empty record"""
        from invenio.search_engine import print_record, get_record
        self.assertEqual(print_record(self.recid, 'xm'), '    <record>\n        <controlfield tag="001">%s</controlfield>\n    </record>\n\n    ' % self.recid)
        self.assertEqual(get_record(self.recid), {'001': [([], ' ', ' ', str(self.recid), 1)]})


class WebSearchExactTitleIndexTest(InvenioTestCase):
    """Checks if exact title index works correctly """

    def test_exacttitle_query_solves_problems(self):
        """websearch - check exacttitle query solves problems"""
        error_messages = []
        error_messages.extend(test_web_page_content(CFG_SITE_URL + "/search?ln=en&p=exacttitle%3A'solves+problems'&f=&action_search=Search",
                                                    expected_text = "Non-compact supergravity solves problems"))
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_exacttitle_query_solve_problems(self):
        """websearch - check exacttitle query solve problems"""
        error_messages = []
        error_messages.extend(test_web_page_content(CFG_SITE_URL + "/search?ln=en&p=exacttitle%3A'solve+problems'&f=&action_search=Search",
                                                    expected_text = ['Search term', 'solve problems', 'did not match']))
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_exacttitle_query_photon_beam(self):
        """websearch - check exacttitle search photon beam"""
        error_messages = []
        error_messages.extend(test_web_page_content(CFG_SITE_URL + "/search?ln=en&p=exacttitle%3A'photon+beam'&f=&action_search=Search",
                                                    expected_text = "Development of photon beam diagnostics"))
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_exacttitle_query_photons_beam(self):
        """websearch - check exacttitle search photons beam"""
        error_messages = []
        error_messages.extend(test_web_page_content(CFG_SITE_URL + "/search?ln=en&p=exacttitle%3A'photons+beam'&f=&action_search=Search",
                                                    expected_text = ['Search term', 'photons beam', 'did not match']))
        if error_messages:
            self.fail(merge_error_messages(error_messages))

class WebSearchCustomCollectionBoxesName(InvenioTestCase):
    """Test if the custom collection box labels are correctly displayed"""

    def test_custom_latest_additions_box_name(self):
        """websearch - test custom name for 'Latest additions' box in 'Videos' collection"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/collection/Videos?ln=en',
                                               expected_text='Latest videos:'))

        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/collection/Videos?ln=fr',
                                               expected_text='Dernières vidéos:'))

        # There is currently no translation for that box in Afrikaans:
        # we must fall back to CFG_SITE_LANG
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/collection/Videos?ln=af',
                                               expected_text='Latest videos:'))

    def test_custom_narrow_by_box_name(self):
        """websearch - test custom name for 'Narrow by' box in 'CERN Divisions' collection"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/collection/CERN%20Divisions?ln=en',
                                               expected_text='Browse by division:'))

        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/collection/CERN%20Divisions?ln=fr',
                                               expected_text='Naviguer par division:'))

        # There is currently no translation for that box in Afrikaans:
        # we must fall back to CFG_SITE_LANG
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/collection/CERN%20Divisions?ln=af',
                                               expected_text='Browse by division:'))

class WebSearchDetailedRecordTabsTest(InvenioTestCase):
    def test_detailed_record(self):
        """websearch - check detailed record main tab"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/record/81',
                                               expected_text='Decapitating Tadpoles',
                                               unexpected_text='The server encountered an error'))

    def test_detailed_record_references_tab(self):
        """websearch - check detailed record references tab"""
        expected_refs = [
            'References (37)',
            'W. Fischler and L. Susskind, "Dilaton Tadpoles, String Condensates And Scale In-variance,"',
            'A. Adams, O. Aharony, J. McGreevy, E. Silverstein,..., work in progress',
        ]
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/record/81/references',
                                               expected_text=expected_refs))

    def test_detailed_record_citations_tab(self):
        """websearch - check detailed record citations tab"""
        expected_cites = [
            'Filtering Gravity: Modification at Large Distances?',
        ]
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/record/81/citations',
                                               expected_text=expected_cites,
                                               unexpected_text='The server encountered an error'))

    def test_detailed_record_keywords_tab(self):
        """websearch - check detailed record keywords tab"""
        self.assertEqual([], test_web_page_content(CFG_SITE_URL + '/record/81/keywords',
                                                   expected_text='Keywords',
                                                   unexpected_text='The server encountered an error'))

    def test_detailed_record_comments_tab(self):
        """websearch - check detailed record comments tab"""
        self.assertEqual([], test_web_page_content(CFG_SITE_URL + '/record/81/comments',
                                                   expected_text='Comments',
                                                   unexpected_text='The server encountered an error'))

    def test_detailed_record_usage_tab(self):
        """websearch - check detailed record usage tab"""
        self.assertEqual([], test_web_page_content(CFG_SITE_URL + '/record/81/usage',
                                                   expected_text='Usage statistics',
                                                   unexpected_text='The server encountered an error'))

    def test_detailed_record_files_tab(self):
        """websearch - check detailed record files tab"""
        self.assertEqual([], test_web_page_content(CFG_SITE_URL + '/record/81/files',
                                                   expected_text='Files',
                                                   unexpected_text='The server encountered an error'))

    def test_detailed_record_plots_tab(self):
        """websearch - check detailed record plots tab"""
        self.assertEqual([], test_web_page_content(CFG_SITE_URL + '/record/81/linkbacks',
                                                   expected_text='Plots',
                                                   unexpected_text='The server encountered an error'))
    def test_detailed_record_holdings_tab(self):
        """websearch - check detailed record holdings tab"""
        self.assertEqual([], test_web_page_content(CFG_SITE_URL + '/record/81/linkbacks',
                                                   expected_text='Holdings',
                                                   unexpected_text='The server encountered an error'))
    def test_detailed_record_linkback_tab(self):
        """websearch - check detailed record linkback tab"""
        self.assertEqual([], test_web_page_content(CFG_SITE_URL + '/record/81/linkbacks',
                                                   expected_text='Linkbacks',
                                                   unexpected_text='The server encountered an error'))

class WebSearchResolveDOITest(InvenioTestCase):
    """Checks that we can resolve DOIs """

    def test_resolve_existing_doi(self):
        """websearch - check resolution of a DOI for an existing record"""
        error_messages = []
        error_messages.extend(test_web_page_content(CFG_SITE_URL + "/doi/10.4028/www.scientific.net/MSF.638-642.1098",
                                                    expected_text = ['Influence of processing parameters on the manufacturing of anode-supported solid oxide fuel cells by different wet chemical routes'],
                                                    unexpected_text = ['404 Not Found', 'could not be resolved']))

        error_messages.extend(test_web_page_content(CFG_SITE_URL + "/doi/10.1063/1.2737136",
                                                    expected_text = ['Epitaxially stabilized growth of orthorhombic LuScO3 thin films'],
                                                    unexpected_text = ['404 Not Found', 'could not be resolved']))
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_resolve_non_existing_doi(self):
        """websearch - check resolution of a non-existing DOI"""
        error_messages = []
        error_messages.extend(test_web_page_content(CFG_SITE_URL + "/doi/foobar",
                                                    expected_text = ['could not be resolved', 'foobar'],
                                                    unexpected_text = ['404 Not Found']))
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_resolve_non_doi(self):
        """websearch - check resolution of a non-DOI value living in 0247_a (without 0247__2:DOI)"""
        error_messages = []
        error_messages.extend(test_web_page_content(CFG_SITE_URL + "/doi/0255-5476",
                                                    expected_text = ['could not be resolved', '0255-5476'],
                                                    unexpected_text = ['404 Not Found']))
        if error_messages:
            self.fail(merge_error_messages(error_messages))

TEST_SUITE = make_test_suite(WebSearchWebPagesAvailabilityTest,
                             WebSearchTestSearch,
                             WebSearchTestBrowse,
                             WebSearchTestOpenURL,
                             WebSearchTestCollections,
                             WebSearchTestRecord,
                             WebSearchTestLegacyURLs,
                             WebSearchNearestTermsTest,
                             WebSearchBooleanQueryTest,
                             WebSearchAuthorQueryTest,
                             WebSearchSearchEnginePythonAPITest,
                             WebSearchSearchEngineWebAPITest,
                             WebSearchSearchEngineJSONAPITest,
                             WebSearchRecordWebAPITest,
                             WebSearchRecordJSONAPITest,
                             WebSearchRestrictedCollectionTest,
                             WebSearchRestrictedCollectionHandlingTest,
                             WebSearchRestrictedPicturesTest,
                             WebSearchRestrictedWebJournalFilesTest,
                             WebSearchRSSFeedServiceTest,
                             WebSearchXSSVulnerabilityTest,
                             WebSearchResultsOverview,
                             WebSearchSortResultsTest,
                             WebSearchSearchResultsXML,
                             WebSearchUnicodeQueryTest,
                             WebSearchMARCQueryTest,
                             WebSearchExtSysnoQueryTest,
                             WebSearchResultsRecordGroupingTest,
                             WebSearchSpecialTermsQueryTest,
                             WebSearchJournalQueryTest,
                             WebSearchStemmedIndexQueryTest,
                             WebSearchSummarizerTest,
                             WebSearchRecordCollectionGuessTest,
                             WebSearchGetFieldValuesTest,
                             WebSearchAddToBasketTest,
                             WebSearchAlertTeaserTest,
                             WebSearchSpanQueryTest,
                             WebSearchReferstoCitedbyTest,
                             WebSearchSPIRESSyntaxTest,
                             WebSearchDateQueryTest,
                             WebSearchTestWildcardLimit,
                             WebSearchSynonymQueryTest,
                             WebSearchWashCollectionsTest,
                             WebSearchAuthorCountQueryTest,
                             WebSearchFiletypeQueryTest,
                             WebSearchFilenameQueryTest,
                             WebSearchDOIQueryTest,
                             WebSearchPerformRequestSearchRefactoringTest,
                             WebSearchGetRecordTests,
                             WebSearchExactTitleIndexTest,
                             WebSearchCJKTokenizedSearchTest,
                             WebSearchItemCountQueryTest,
                             WebSearchCustomCollectionBoxesName,
                             WebSearchDetailedRecordTabsTest,
                             WebSearchResolveDOITest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
