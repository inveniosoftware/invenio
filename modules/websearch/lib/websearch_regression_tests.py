# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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

import unittest
import re
import urlparse, cgi
import sys

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

from mechanize import Browser, LinkNotFoundError

from invenio.config import CFG_SITE_URL, CFG_SITE_NAME, CFG_SITE_LANG, \
    CFG_SITE_RECORD, CFG_SITE_LANGS, CFG_WEBSEARCH_SPIRES_SYNTAX
from invenio.testutils import make_test_suite, \
                              run_test_suite, \
                              make_url, make_surl, test_web_page_content, \
                              merge_error_messages
from invenio.urlutils import same_urls_p
from invenio.dbquery import run_sql
from invenio.search_engine import perform_request_search, \
    guess_primary_collection_of_a_record, guess_collection_of_a_record, \
    collection_restricted_p, get_permitted_restricted_collections, \
    search_pattern, search_unit, search_unit_in_bibrec, \
    wash_colls, record_public_p
from invenio import search_engine_summarizer
from invenio.search_engine_utils import get_fieldvalues


if 'fr' in CFG_SITE_LANGS:
    lang_french_configured = True
else:
    lang_french_configured = False


def parse_url(url):
    parts = urlparse.urlparse(url)
    query = cgi.parse_qs(parts[4], True)

    return parts[2].split('/')[1:], query

class WebSearchWebPagesAvailabilityTest(unittest.TestCase):
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

class WebSearchTestLegacyURLs(unittest.TestCase):

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

class WebSearchTestRecord(unittest.TestCase):
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
                    target = make_url('/%s/1/export/%s?ln=en' % (CFG_SITE_RECORD, oformat))
                    try:
                        browser.find_link(url=target)
                    except LinkNotFoundError:
                        self.fail('link %r should be in page' % target)
            else:
                # non-hd HTML formats should have a link back to
                # the main detailed record
                target = make_url('/%s/1' % CFG_SITE_RECORD)
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
                                               expected_text='title        = "ALEPH experiment'))
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

class WebSearchTestCollections(unittest.TestCase):

    def test_traversal_links(self):
        """ websearch - traverse all the publications of a collection """

        browser = Browser()

        try:
            for aas in (0, 1):
                args = {'as': aas}
                browser.open(make_url('/collection/Preprints', **args))

                for jrec in (11, 21, 11, 28):
                    args = {'jrec': jrec, 'cc': 'Preprints'}
                    if aas:
                        args['as'] = aas

                    url = make_url('/search', **args)
                    try:
                        browser.follow_link(url=url)
                    except LinkNotFoundError:
                        args['ln'] = CFG_SITE_LANG
                        url = make_url('/search', **args)
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
            tryfollow(make_url('/collection/Articles%20%26%20Preprints',
                               **kargs))
            tryfollow(make_url('/collection/Articles', **kargs))

            # But we can also jump to a grandson immediately
            browser.back()
            browser.back()
            tryfollow(make_url('/collection/ALEPH', **kargs))

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


class WebSearchTestBrowse(unittest.TestCase):

    def test_browse_field(self):
        """ websearch - check that browsing works """

        browser = Browser()
        browser.open(make_url('/'))

        browser.select_form(name='search')
        browser['f'] = ['title']
        browser.submit(name='action_browse')

        def collect():
            # We'll get a few links to search for the actual hits, plus a
            # link to the following results.
            res = []
            for link in browser.links(url_regex=re.compile(CFG_SITE_URL +
                                                           r'/search\?')):
                if link.text == 'Advanced Search':
                    continue

                dummy, q = parse_url(link.url)
                res.append((link, q))

            return res

        # if we follow the last link, we should get another
        # batch. There is an overlap of one item.
        batch_1 = collect()

        browser.follow_link(link=batch_1[-1][0])

        batch_2 = collect()

        # FIXME: we cannot compare the whole query, as the collection
        # set is not equal
        self.failUnlessEqual(batch_1[-2][1]['p'], batch_2[0][1]['p'])

class WebSearchTestOpenURL(unittest.TestCase):

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


class WebSearchTestSearch(unittest.TestCase):

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

            if not same_urls_p(l.url, make_url('/search', **q)):
                self.fail(repr((l.url, make_url('/search', **q))))

    def test_similar_authors(self):
        """ websearch - test similar authors box """

        browser = Browser()
        browser.open(make_url(''))

        browser.select_form(name='search')
        browser['p'] = 'Ellis, R K'
        browser['f'] = ['author']
        browser.submit()

        l = browser.find_link(text="Ellis, R S")
        self.failUnless(same_urls_p(l.url, make_url('/search',
                                                    p="Ellis, R S",
                                                    f='author',
                                                    ln='en')))

class WebSearchTestWildcardLimit(unittest.TestCase):
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
                                  expected_text="[9, 10, 11, 17, 46, 48, 50, 51, 52, 53, 54, 67, 72, 74, 81, 88, 92, 96]"))

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

class WebSearchNearestTermsTest(unittest.TestCase):
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
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=embed",
                                               expected_link_label='embed'))

    def test_nearest_terms_box_in_unsuccessful_simple_accented_query(self):
        """ websearch - nearest terms box for unsuccessful accented query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=elliszà',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=embed",
                                               expected_link_label='embed'))

    def test_nearest_terms_box_in_unsuccessful_structured_query(self):
        """ websearch - nearest terms box for unsuccessful structured query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellisz&f=author',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=fabbro&f=author",
                                               expected_link_label='fabbro'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=author%3Aellisz',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=author%3Afabbro",
                                               expected_link_label='fabbro'))

    def test_nearest_terms_box_in_query_with_invalid_index(self):
        """ websearch - nearest terms box for queries with invalid indexes specified """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=bednarz%3Aellis',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=bednarz",
                                               expected_link_label='bednarz'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=1%3Aellis',
                                               expected_text="no index 1.",
                                               expected_link_target=CFG_SITE_URL+"/record/47?ln=en",
                                               expected_link_label="Detailed record"))

    def test_nearest_terms_box_in_unsuccessful_phrase_query(self):
        """ websearch - nearest terms box for unsuccessful phrase query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=author%3A%22Ellis%2C+Z%22',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=author%3A%22Enqvist%2C+K%22",
                                               expected_link_label='Enqvist, K'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%22ellisz%22&f=author',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=%22Enqvist%2C+K%22&f=author",
                                               expected_link_label='Enqvist, K'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%22elliszà%22&f=author',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=%22Enqvist%2C+K%22&f=author",
                                               expected_link_label='Enqvist, K'))

    def test_nearest_terms_box_in_unsuccessful_partial_phrase_query(self):
        """ websearch - nearest terms box for unsuccessful partial phrase query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=author%3A%27Ellis%2C+Z%27',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=author%3A%27Enqvist%2C+K%27",
                                               expected_link_label='Enqvist, K'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%27ellisz%27&f=author',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=%27Enqvist%2C+K%27&f=author",
                                               expected_link_label='Enqvist, K'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%27elliszà%27&f=author',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=%27Enqvist%2C+K%27&f=author",
                                               expected_link_label='Enqvist, K'))

    def test_nearest_terms_box_in_unsuccessful_partial_phrase_advanced_query(self):
        """ websearch - nearest terms box for unsuccessful partial phrase advanced search query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p1=aaa&f1=title&m1=p&as=1',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&f1=title&as=1&p1=A+simple+functional+form+for+proton-nucleus+total+reaction+cross+sections&m1=p",
                                               expected_link_label='A simple functional form for proton-nucleus total reaction cross sections'))

    def test_nearest_terms_box_in_unsuccessful_exact_phrase_advanced_query(self):
        """ websearch - nearest terms box for unsuccessful exact phrase advanced search query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p1=aaa&f1=title&m1=e&as=1',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&f1=title&as=1&p1=A+simple+functional+form+for+proton-nucleus+total+reaction+cross+sections&m1=e",
                                               expected_link_label='A simple functional form for proton-nucleus total reaction cross sections'))

    def test_nearest_terms_box_in_unsuccessful_boolean_query(self):
        """ websearch - nearest terms box for unsuccessful boolean query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=title%3Aellisz+author%3Aellisz',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=title%3Aenergi+author%3Aellisz",
                                               expected_link_label='energi'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=title%3Aenergi+author%3Aenergie',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=title%3Aenergi+author%3Aenqvist",
                                               expected_link_label='enqvist'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=title%3Aellisz+author%3Aellisz&f=keyword',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=title%3Aenergi+author%3Aellisz&f=keyword",
                                               expected_link_label='energi'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=title%3Aenergi+author%3Aenergie&f=keyword',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=title%3Aenergi+author%3Aenqvist&f=keyword",
                                               expected_link_label='enqvist'))

    def test_nearest_terms_box_in_unsuccessful_uppercase_query(self):
        """ websearch - nearest terms box for unsuccessful uppercase query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=fOo%3Atest',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=food",
                                               expected_link_label='food'))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=arXiv%3A1007.5048',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=artist",
                                               expected_link_label='artist'))

    def test_nearest_terms_box_in_unsuccessful_spires_query(self):
        """ websearch - nearest terms box for unsuccessful spires query """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=find+a+foobar',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=find+a+finch",
                                               expected_link_label='finch'))


class WebSearchBooleanQueryTest(unittest.TestCase):
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

class WebSearchAuthorQueryTest(unittest.TestCase):
    """Check various author-related queries."""

    def test_propose_similar_author_names_box(self):
        """ websearch - propose similar author names box """
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=Ellis%2C+R&f=author',
                                               expected_text="See also: similar author names",
                                               expected_link_target=CFG_SITE_URL+"/search?ln=en&p=Ellis%2C+R+K&f=author",
                                               expected_link_label="Ellis, R K"))

    def test_do_not_propose_similar_author_names_box(self):
        """ websearch - do not propose similar author names box """
        errmsgs = test_web_page_content(CFG_SITE_URL + '/search?p=author%3A%22Ellis%2C+R%22',
                                        expected_link_target=CFG_SITE_URL+"/search?ln=en&p=Ellis%2C+R+K&f=author",
                                        expected_link_label="Ellis, R K")
        if errmsgs[0].find("does not contain link to") > -1:
            pass
        else:
            self.fail("Should not propose similar author names box.")
        return

class WebSearchSearchEnginePythonAPITest(unittest.TestCase):
    """Check typical search engine Python API calls on the demo data."""

    def test_search_engine_python_api_for_failed_query(self):
        """websearch - search engine Python API for failed query"""
        self.assertEqual([],
                         perform_request_search(p='aoeuidhtns'))

    def test_search_engine_python_api_for_successful_query(self):
        """websearch - search engine Python API for successful query"""
        self.assertEqual([8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 47],
                         perform_request_search(p='ellis', rg=None))

    def test_search_engine_python_api_for_existing_record(self):
        """websearch - search engine Python API for existing record"""
        self.assertEqual([8],
                         perform_request_search(recid=8))

    def test_search_engine_python_api_for_nonexisting_record(self):
        """websearch - search engine Python API for non-existing record"""
        self.assertEqual([],
                         perform_request_search(recid=16777215))

    def test_search_engine_python_api_for_nonexisting_collection(self):
        """websearch - search engine Python API for non-existing collection"""
        self.assertEqual([],
                         perform_request_search(c='Foo'))

    def test_search_engine_python_api_for_range_of_records(self):
        """websearch - search engine Python API for range of records"""
        self.assertEqual([1, 2, 3, 4, 5, 6, 7, 8, 9],
                         perform_request_search(recid=1, recidb=10))

    def test_search_engine_python_api_ranked_by_citation(self):
        """websearch - search engine Python API for citation ranking"""
        self.assertEqual([82, 83, 87, 89],
                perform_request_search(p='recid:81', rm='citation'))

    def test_search_engine_python_api_textmarc(self):
        """websearch - search engine Python API for Text MARC output"""
        # we are testing example from /help/hacking/search-engine-api
        import cStringIO
        tmp = cStringIO.StringIO()
        perform_request_search(req=tmp, p='higgs', of='tm', ot=['100', '700'])
        out = tmp.getvalue()
        tmp.close()
        self.assertEqual(out, """\
000000085 100__ $$aGirardello, L$$uINFN$$uUniversita di Milano-Bicocca
000000085 700__ $$aPorrati, Massimo
000000085 700__ $$aZaffaroni, A
000000001 100__ $$aPhotolab
""")


class WebSearchSearchEngineWebAPITest(unittest.TestCase):
    """Check typical search engine Web API calls on the demo data."""

    def test_search_engine_web_api_for_failed_query(self):
        """websearch - search engine Web API for failed query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=aoeuidhtns&of=id',
                                               expected_text="[]"))


    def test_search_engine_web_api_for_successful_query(self):
        """websearch - search engine Web API for successful query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis&of=id&rg=100',
                                               expected_text="[8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 47]"))

    def test_search_engine_web_api_for_existing_record(self):
        """websearch - search engine Web API for existing record"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?recid=8&of=id',
                                               expected_text="[8]"))

    def test_search_engine_web_api_for_nonexisting_record(self):
        """websearch - search engine Web API for non-existing record"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?recid=123456789&of=id',
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

class WebSearchRestrictedCollectionTest(unittest.TestCase):
    """Test of the restricted Theses collection behaviour."""

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
        self.assertEqual(get_permitted_restricted_collections(collect_user_info(get_uid_from_email('jekyll@cds.cern.ch'))), ['Theses'])
        self.assertEqual(get_permitted_restricted_collections(collect_user_info(get_uid_from_email('hyde@cds.cern.ch'))), [])

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

class WebSearchRestrictedPicturesTest(unittest.TestCase):
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

class WebSearchRestrictedWebJournalFilesTest(unittest.TestCase):
    """
    Check whether files attached to a WebJournal article are well
    accessible when the article is published
    """
    def test_restricted_files_guest(self):
        """websearch - files of unreleased articles are not available to guest"""

        # Record is not public...
        self.assertEqual(record_public_p(106), False)

        # ... and guest cannot access attached files
        error_messages = test_web_page_content(CFG_SITE_URL + '/%s/106/files/journal_galapagos_archipelago.jpg' % CFG_SITE_RECORD,
                                               expected_text=['This file is restricted.  If you think you have right to access it, please authenticate yourself.'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_restricted_files_editor(self):
        """websearch - files of unreleased articles are available to editor"""

        # Record is not public...
        self.assertEqual(record_public_p(106), False)

        # ... but editor can access attached files
        error_messages = test_web_page_content(CFG_SITE_URL + '/%s/106/files/journal_galapagos_archipelago.jpg' % CFG_SITE_RECORD,
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
        self.assertEqual(record_public_p(105), False)

        # ... but user can access attached files, as article is released
        error_messages = test_web_page_content(CFG_SITE_URL + '/%s/105/files/journal_scissor_beak.jpg' % CFG_SITE_RECORD,
                                               expected_text=[],
                                                unexpected_text=['This file is restricted',
                                                                 'You are not authorized'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_really_restricted_files_guest(self):
        """websearch - restricted files of released articles are not available to guest"""

        # Record is not public...
        self.assertEqual(record_public_p(105), False)

        # ... and user cannot access restricted attachements, even if
        # article is released
        error_messages = test_web_page_content(CFG_SITE_URL + '/%s/105/files/restricted-journal_scissor_beak.jpg' % CFG_SITE_RECORD,
                                               expected_text=['This file is restricted.  If you think you have right to access it, please authenticate yourself.'])
        if error_messages:
            self.fail(merge_error_messages(error_messages))

    def test_restricted_picture_has_restriction_flag(self):
        """websearch - restricted files displays a restriction flag"""
        error_messages = test_web_page_content(CFG_SITE_URL + '/%s/1/files/' % CFG_SITE_RECORD,
                                                  expected_text="Restricted")
        if error_messages:
            self.fail(merge_error_messages(error_messages))

class WebSearchRSSFeedServiceTest(unittest.TestCase):
    """Test of the RSS feed service."""

    def test_rss_feed_service(self):
        """websearch - RSS feed service"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/rss',
                                               expected_text='<rss version="2.0"'))

class WebSearchXSSVulnerabilityTest(unittest.TestCase):
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

class WebSearchResultsOverview(unittest.TestCase):
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

class WebSearchSortResultsTest(unittest.TestCase):
    """Test of the search results page's sorting capability."""

    def test_sort_results_default(self):
        """websearch - search results sorting, default method"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=of&f=title&rg=1',
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

class WebSearchSearchResultsXML(unittest.TestCase):
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

class WebSearchUnicodeQueryTest(unittest.TestCase):
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
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=title%3A%27%CE%B7%27',
                                               expected_text="[76]"))

    def test_unicode_regexp_query(self):
        """websearch - Unicode regexp query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=title%3A%2F%CE%B7%2F',
                                               expected_text="[76]"))

class WebSearchMARCQueryTest(unittest.TestCase):
    """Test of the search results for queries containing physical MARC tags."""

    def test_single_marc_tag_exact_phrase_query(self):
        """websearch - single MARC tag, exact phrase query (100__a)"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=100__a%3A%22Ellis%2C+J%22',
                                               expected_text="[9, 14, 18]"))

    def test_single_marc_tag_partial_phrase_query(self):
        """websearch - single MARC tag, partial phrase query (245__b)"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=245__b%3A%27and%27',
                                               expected_text="[28]"))

    def test_many_marc_tags_partial_phrase_query(self):
        """websearch - many MARC tags, partial phrase query (245)"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=245%3A%27and%27&rg=100',
                                               expected_text="[1, 8, 9, 14, 15, 20, 22, 24, 28, 33, 47, 48, 49, 51, 53, 64, 69, 71, 79, 82, 83, 85, 91, 96]"))

    def test_single_marc_tag_regexp_query(self):
        """websearch - single MARC tag, regexp query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=245%3A%2Fand%2F&rg=100',
                                               expected_text="[1, 8, 9, 14, 15, 20, 22, 24, 28, 33, 47, 48, 49, 51, 53, 64, 69, 71, 79, 82, 83, 85, 91, 96]"))

class WebSearchExtSysnoQueryTest(unittest.TestCase):
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

class WebSearchResultsRecordGroupingTest(unittest.TestCase):
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

class WebSearchSpecialTermsQueryTest(unittest.TestCase):
    """Test of the search results for queries containing special terms."""

    def test_special_terms_u1(self):
        """websearch - query for special terms, U(1)"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=U%281%29',
                                               expected_text="[57, 79, 80, 88]"))

    def test_special_terms_u1_and_sl(self):
        """websearch - query for special terms, U(1) SL(2,Z)"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=U%281%29+SL%282%2CZ%29',
                                               expected_text="[88]"))

    def test_special_terms_u1_and_sl_or(self):
        """websearch - query for special terms, U(1) OR SL(2,Z)"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=U%281%29+OR+SL%282%2CZ%29',
                                               expected_text="[57, 79, 80, 88]"))

    def test_special_terms_u1_and_sl_or_parens(self):
        """websearch - query for special terms, (U(1) OR SL(2,Z))"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=%28U%281%29+OR+SL%282%2CZ%29%29',
                                               expected_text="[57, 79, 80, 88]"))

class WebSearchJournalQueryTest(unittest.TestCase):
    """Test of the search results for journal pubinfo queries."""

    def test_query_journal_title_only(self):
        """websearch - journal publication info query, title only"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&f=journal&p=Phys.+Lett.+B',
                                               expected_text="[77, 78, 85, 87]"))

    def test_query_journal_full_pubinfo(self):
        """websearch - journal publication info query, full reference"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&f=journal&p=Phys.+Lett.+B+531+%282002%29+301',
                                               expected_text="[78]"))

class WebSearchStemmedIndexQueryTest(unittest.TestCase):
    """Test of the search results for queries using stemmed indexes."""

    def test_query_stemmed_lowercase(self):
        """websearch - stemmed index query, lowercase"""
        # note that dasse/Dasse is stemmed into dass/Dass, as expected
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=dasse',
                                               expected_text="[25, 26]"))

    def test_query_stemmed_uppercase(self):
        """websearch - stemmed index query, uppercase"""
        # ... but note also that DASSE is stemmed into DASSE(!); so
        # the test would fail if the search engine would not lower the
        # query term.  (Something that is not necessary for
        # non-stemmed indexes.)
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?of=id&p=DASSE',
                                               expected_text="[25, 26]"))

class WebSearchSummarizerTest(unittest.TestCase):
    """Test of the search results summarizer functions."""

    def test_most_popular_field_values_singletag(self):
        """websearch - most popular field values, simple tag"""
        from invenio.search_engine import get_most_popular_field_values
        self.assertEqual((('PREPRINT', 37), ('ARTICLE', 28), ('BOOK', 14), ('THESIS', 8), ('PICTURE', 7), ('POETRY', 2), ('REPORT', 2),  ('ATLANTISTIMESNEWS', 1)),
                         get_most_popular_field_values(range(0,100), '980__a'))

    def test_most_popular_field_values_singletag_multiexclusion(self):
        """websearch - most popular field values, simple tag, multiple exclusions"""
        from invenio.search_engine import get_most_popular_field_values
        self.assertEqual((('PREPRINT', 37), ('ARTICLE', 28), ('BOOK', 14), ('REPORT', 2), ('ATLANTISTIMESNEWS', 1)),
                         get_most_popular_field_values(range(0,100), '980__a', ('THESIS', 'PICTURE', 'POETRY')))

    def test_most_popular_field_values_multitag(self):
        """websearch - most popular field values, multiple tags"""
        from invenio.search_engine import get_most_popular_field_values
        self.assertEqual((('Ellis, J', 3), ('Enqvist, K', 1), ('Ibanez, L E', 1), ('Nanopoulos, D V', 1), ('Ross, G G', 1)),
                         get_most_popular_field_values((9, 14, 18), ('100__a', '700__a')))

    def test_most_popular_field_values_multitag_singleexclusion(self):
        """websearch - most popular field values, multiple tags, single exclusion"""
        from invenio.search_engine import get_most_popular_field_values
        self.assertEqual((('Enqvist, K', 1), ('Ibanez, L E', 1), ('Nanopoulos, D V', 1), ('Ross, G G', 1)),
                         get_most_popular_field_values((9, 14, 18), ('100__a', '700__a'), ('Ellis, J')))

    def test_most_popular_field_values_multitag_countrepetitive(self):
        """websearch - most popular field values, multiple tags, counting repetitive occurrences"""
        from invenio.search_engine import get_most_popular_field_values
        self.assertEqual((('THESIS', 2), ('REPORT', 1)),
                         get_most_popular_field_values((41,), ('690C_a', '980__a'), count_repetitive_values=True))
        self.assertEqual((('REPORT', 1), ('THESIS', 1)),
                         get_most_popular_field_values((41,), ('690C_a', '980__a'), count_repetitive_values=False))

    def test_ellis_citation_summary(self):
        """websearch - query ellis, citation summary output format"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=ellis&of=hcs',
                                               expected_text="Less known papers (1-9)",
                                               expected_link_target=CFG_SITE_URL+"/search?p=ellis%20AND%20cited%3A1-%3E9&rm=citation",
                                               expected_link_label='1'))

    def test_ellis_not_quark_citation_summary_advanced(self):
        """websearch - ellis and not quark, citation summary format advanced"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?ln=en&as=1&m1=a&p1=ellis&f1=author&op1=n&m2=a&p2=quark&f2=&op2=a&m3=a&p3=&f3=&action_search=Search&sf=&so=a&rm=&rg=10&sc=1&of=hcs',
                                               expected_text="Less known papers (1-9)",
                                               expected_link_target=CFG_SITE_URL+'/search?p=author%3Aellis%20and%20not%20quark%20AND%20cited%3A1-%3E9&rm=citation',
                                               expected_link_label='1'))

    def test_ellis_not_quark_citation_summary_regular(self):
        """websearch - ellis and not quark, citation summary format advanced"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?ln=en&p=author%3Aellis+and+not+quark&f=&action_search=Search&sf=&so=d&rm=&rg=10&sc=0&of=hcs',
                                               expected_text="Less known papers (1-9)",
                                               expected_link_target=CFG_SITE_URL+'/search?p=author%3Aellis%20and%20not%20quark%20AND%20cited%3A1-%3E9&rm=citation',
                                               expected_link_label='1'))

    def test_compute_self_citations(self):
        """websearch - computing self-citations"""
        tags = search_engine_summarizer.get_authors_tags()
        recids = [row[0] for row in run_sql('select id from bibrec limit 300')]
        citers = search_engine_summarizer.get_cited_by_list(recids)
        authors_cache = {}
        total_citations = sum(len(lciters) for recid,lciters in citers)
        total_citations_minus_self_citations = 0
        for recid, lciters in citers:
            total_citations_minus_self_citations += \
                search_engine_summarizer.compute_self_citations(recid,
                                                                lciters,
                                                                authors_cache,
                                                                tags)
        self.assert_(total_citations_minus_self_citations < total_citations)


class WebSearchRecordCollectionGuessTest(unittest.TestCase):
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

class WebSearchGetFieldValuesTest(unittest.TestCase):
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

class WebSearchAddToBasketTest(unittest.TestCase):
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

class WebSearchAlertTeaserTest(unittest.TestCase):
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


class WebSearchSpanQueryTest(unittest.TestCase):
    """Test of span queries."""

    def test_span_in_word_index(self):
        """websearch - span query in a word index"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=year%3A1992-%3E1996&of=id&ap=0',
                                               expected_text='[17, 66, 69, 71]'))

    def test_span_in_phrase_index(self):
        """websearch - span query in a phrase index"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=year%3A%221992%22-%3E%221996%22&of=id&ap=0',
                                               expected_text='[17, 66, 69, 71]'))

    def test_span_in_bibxxx(self):
        """websearch - span query in MARC tables"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=909C0y%3A%221992%22-%3E%221996%22&of=id&ap=0',
                                               expected_text='[17, 66, 69, 71]'))

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
                                               expected_text='[8, 11, 13, 17, 47]'))


class WebSearchReferstoCitedbyTest(unittest.TestCase):
    """Test of refersto/citedby search operators."""

    def test_refersto_recid(self):
        'websearch - refersto:recid:84'
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=refersto%3Arecid%3A84&of=id&ap=0',
                                               expected_text='[85, 88, 91]'))

    def test_refersto_repno(self):
        'websearch - refersto:reportnumber:hep-th/0205061'
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=refersto%3Areportnumber%3Ahep-th/0205061&of=id&ap=0',
                                               expected_text='[91]'))

    def test_refersto_author_word(self):
        'websearch - refersto:author:klebanov'
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=refersto%3Aauthor%3Aklebanov&of=id&ap=0',
                                               expected_text='[85, 86, 88, 91]'))

    def test_refersto_author_phrase(self):
        'websearch - refersto:author:"Klebanov, I"'
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=refersto%3Aauthor%3A%22Klebanov,%20I%22&of=id&ap=0',
                                               expected_text='[85, 86, 88, 91]'))

    def test_citedby_recid(self):
        'websearch - citedby:recid:92'
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=citedby%3Arecid%3A92&of=id&ap=0',
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


class WebSearchSPIRESSyntaxTest(unittest.TestCase):
    """Test of SPIRES syntax issues"""

    if CFG_WEBSEARCH_SPIRES_SYNTAX > 0:
        def test_and_not_parens(self):
            'websearch - find a ellis, j and not a enqvist'
            self.assertEqual([],
                             test_web_page_content(CFG_SITE_URL +'/search?p=find+a+ellis%2C+j+and+not+a+enqvist&of=id&ap=0',
                                                   expected_text='[9, 12, 14, 47]'))

        def test_dadd_search(self):
            'websearch - find da > today - 3650'
            # XXX: assumes we've reinstalled our site in the last 10 years
            # should return every document in the system
            self.assertEqual([],
                             test_web_page_content(CFG_SITE_URL +'/search?ln=en&p=find+da+%3E+today+-+3650&f=&of=id',
                                                   expected_text='[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 107]'))


class WebSearchDateQueryTest(unittest.TestCase):
    """Test various date queries."""

    def setUp(self):
        """Establish variables we plan to re-use"""
        from invenio.intbitset import intbitset
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


class WebSearchSynonymQueryTest(unittest.TestCase):
    """Test of queries using synonyms."""

    def test_journal_phrvd(self):
        """websearch - search-time synonym search, journal title"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=PHRVD&f=journal&of=id',
                                               expected_text="[66, 72]"))

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
                                               expected_text="[52, 59]"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%CE%B2+decay&of=id',
                                               expected_text="[52, 59]"))

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
                                               expected_text="[52, 59]"))
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%CE%B2&of=id',
                                               expected_text="[52, 59]"))

class WebSearchWashCollectionsTest(unittest.TestCase):
    """Test if the collection argument is washed correctly"""

    def test_wash_coll_when_coll_restricted(self):
        """websearch - washing of restricted daughter collections"""
        self.assertEqual(
            sorted(wash_colls(cc='', c=['Books & Reports', 'Theses'])[1]),
            ['Books & Reports', 'Theses'])
        self.assertEqual(
            sorted(wash_colls(cc='', c=['Books & Reports', 'Theses'])[2]),
            ['Books & Reports', 'Theses'])


class WebSearchAuthorCountQueryTest(unittest.TestCase):
    """Test of queries using authorcount fields."""

    def test_journal_authorcount_word(self):
        """websearch - author count, word query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=4&f=authorcount&of=id',
                                               expected_text="[51, 54, 59, 66, 92, 96]"))

    def test_journal_authorcount_phrase(self):
        """websearch - author count, phrase query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=%224%22&f=authorcount&of=id',
                                               expected_text="[51, 54, 59, 66, 92, 96]"))

    def test_journal_authorcount_span(self):
        """websearch - author count, span query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=authorcount%3A9-%3E16&of=id',
                                               expected_text="[69, 71]"))

    def test_journal_authorcount_plus(self):
        """websearch - author count, plus query"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/search?p=50%2B&f=authorcount&of=id',
                                               expected_text="[10, 17]"))

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
                             WebSearchRestrictedCollectionTest,
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
                             WebSearchAuthorCountQueryTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
