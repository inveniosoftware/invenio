## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

"""WebSearch module regression tests."""

__revision__ = "$Id$"

import unittest
import re
import urlparse, cgi
from sets import Set

from mechanize import Browser, LinkNotFoundError, HTTPError

from invenio.config import weburl, cdsname, cdslang
from invenio.testutils import make_test_suite, \
                              warn_user_about_tests_and_run, \
                              make_url, test_web_page_content, \
                              merge_error_messages
from invenio.urlutils import same_urls_p
from invenio.search_engine import perform_request_search

def parse_url(url):
    parts = urlparse.urlparse(url)
    query = cgi.parse_qs(parts[4], True)

    return parts[2].split('/')[1:], query

class WebSearchWebPagesAvailabilityTest(unittest.TestCase):
    """Check WebSearch web pages whether they are up or not."""

    def test_search_interface_pages_availability(self):
        """websearch - availability of search interface pages"""

        baseurl = weburl + '/'

        _exports = ['', 'collection/Poetry', 'collection/Poetry?as=1']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_search_results_pages_availability(self):
        """websearch - availability of search results pages"""

        baseurl = weburl + '/search'

        _exports = ['', '?c=Poetry', '?p=ellis', '/cache', '/log']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_search_detailed_record_pages_availability(self):
        """websearch - availability of search detailed record pages"""

        baseurl = weburl + '/record/'

        _exports = ['', '1', '1/', '1/files', '1/files/']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_browse_results_pages_availability(self):
        """websearch - availability of browse results pages"""

        baseurl = weburl + '/search'

        _exports = ['?p=ellis&f=author&action_browse=Browse']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_search_user_help_pages_availability(self):
        """websearch - availability of search user help pages"""

        baseurl = weburl + '/help/search/'

        _exports = ['', 'index.fr.html', 'tips.fr.html', 'guide.fr.html']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

class WebSearchTestLegacyURLs(unittest.TestCase):

    """ Check that the application still responds to legacy URLs for
    navigating, searching and browsing."""

    def test_legacy_collections(self):
        """ websearch - collections handle legacy urls """

        browser = Browser()

        def check(legacy, new):
            browser.open(legacy)
            got = browser.geturl()

            self.failUnless(same_urls_p(got, new), got)

        # Use the root URL unless we need more
        check(make_url('/', c=cdsname),
              make_url('/'))

        # Other collections are redirected in the /collection area
        check(make_url('/', c='Poetry'),
              make_url('/collection/Poetry'))

        # Drop unnecessary arguments, like ln and as (when they are
        # the default value)
        check(make_url('/', c='Poetry', as=0, ln=cdslang),
              make_url('/collection/Poetry'))

        # Otherwise, keep them
        check(make_url('/', c='Poetry', as=1, ln=cdslang),
              make_url('/collection/Poetry', as=1))

        # Support the /index.py addressing too
        check(make_url('/index.py', c='Poetry'),
              make_url('/collection/Poetry'))


    def test_legacy_search(self):
        """ websearch - search queries handle legacy urls """

        browser = Browser()

        def check(legacy, new):
            browser.open(legacy)
            got = browser.geturl()

            self.failUnless(same_urls_p(got, new), got)

        # /search.py is redirected on /search
        check(make_url('/search.py', p='nuclear', as=1),
              make_url('/search', p='nuclear', as=1))

        # direct recid searches are redirected to /record
        check(make_url('/search.py', recid=1, ln='es'),
              make_url('/record/1', ln='es'))



class WebSearchTestRecord(unittest.TestCase):
    """ Check the interface of the /record results """

    def test_format_links(self):
        """ websearch - check format links for records """

        browser = Browser()

        # We open the record in all known HTML formats
        for hformat in ('hd', 'hx', 'hm'):
            browser.open(make_url('/record/1', of=hformat))

            # all except the selected links should be present in the
            # page.
            for oformat in ('hd', 'hx', 'hm', 'xm', 'xd'):
                target = make_url('/record/1', of=oformat)

                if oformat == hformat:
                    try:
                        browser.find_link(url=target)
                    except LinkNotFoundError:
                        continue

                    self.fail('link %r should not be in page' % target)
                else:
                    try:
                        browser.find_link(url=target)
                    except LinkNotFoundError:
                        self.fail('link %r should be in page' % target)

        return


class WebSearchTestCollections(unittest.TestCase):

    def test_traversal_links(self):
        """ websearch - traverse all the publications of a collection """

        # Ensure that it is possible to traverse a collection as
        # /collection/My_Collection?jrec=...

        browser = Browser()

        try:
            for as in (0, 1):
                browser.open(make_url('/collection/Preprints', as=as))

                for jrec in (11, 21, 11, 23):
                    args = {'jrec': jrec, 'cc': 'Preprints'}
                    if as:
                        args['as'] = as

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

        for as in (0, 1):
            if as:
                kargs = {'as': 1}
            else:
                kargs = {}

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

            records = Set()
            similar = Set()

            for link in browser.links():
                path, q = parse_url(link.url)

                if not path:
                    continue

                if path[0] == 'record':
                    records.add(int(path[1]))
                    continue

                if path[0] == 'search':
                    if not q.get('rm') == ['wrd']:
                        continue

                    recid = q['p'][0].split(':')[1]
                    similar.add(int(recid))

            self.failUnlessEqual(records, similar)

            return records

        # We must have 10 links to the corresponding /records
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
            for link in browser.links(url_regex=re.compile(weburl +
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
        for f in ('cc', 'c', 'action_search', 'ln'):
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

        # we should get a few searches back, which are identical
        # except for the p field being substituted (and the cc field
        # being dropped).
        if 'cc' in original:
            del original['cc']

        for link in browser.links(url_regex=re.compile(weburl + r'/search\?')):
            if link.text == 'Advanced Search':
                continue

            dummy, target = parse_url(link.url)

            original['p'] = [link.text]
            self.failUnlessEqual(original, target)

        return

    def test_switch_to_simple_search(self):
        """ websearch - switch to simple search """

        browser = Browser()
        browser.open(make_url('/collection/ISOLDE', as=1))

        browser.select_form(name='search')
        browser['p1'] = 'tandem'
        browser['f1'] = ['title']
        browser.submit()

        browser.follow_link(text='Simple Search')

        dummy, q = parse_url(browser.geturl())

        self.failUnlessEqual(q, {'cc': ['ISOLDE'],
                                 'p': ['tandem'],
                                 'f': ['title']})

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
                                 'as': ['1']})

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
                                                    f='author')))

# pylint: disable-msg=C0301

class WebSearchNearestTermsTest(unittest.TestCase):
    """Check various alternatives of searches leading to the nearest
    terms box."""

    def test_nearest_terms_box_in_okay_query(self):
        """ websearch - no nearest terms box for a successful query """
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=ellis',
                                               expected_text="jump to record"))

    def test_nearest_terms_box_in_unsuccessful_simple_query(self):
        """ websearch - nearest terms box for unsuccessful simple query """
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=ellisz',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=weburl+"/search?p=embed",
                                               expected_link_label='embed'))

    def test_nearest_terms_box_in_unsuccessful_structured_query(self):
        """ websearch - nearest terms box for unsuccessful structured query """
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=ellisz&f=author',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=weburl+"/search?p=fabbro&f=author",
                                               expected_link_label='fabbro'))
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=author%3Aellisz',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=weburl+"/search?p=author%3Afabbro",
                                               expected_link_label='fabbro'))

    def test_nearest_terms_box_in_unsuccessful_phrase_query(self):
        """ websearch - nearest terms box for unsuccessful phrase query """
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=author%3A%22Ellis%2C+Z%22',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=weburl+"/search?p=author%3A%22Enqvist%2C+K%22",
                                               expected_link_label='Enqvist, K'))
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=%22ellisz%22&f=author',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=weburl+"/search?p=%22Enqvist%2C+K%22&f=author",
                                               expected_link_label='Enqvist, K'))

    def test_nearest_terms_box_in_unsuccessful_boolean_query(self):
        """ websearch - nearest terms box for unsuccessful boolean query """
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=title%3Aellisz+author%3Aellisz',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=weburl+"/search?p=title%3Aenergie+author%3Aellisz",
                                               expected_link_label='energie'))
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=title%3Aenergie+author%3Aenergie',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=weburl+"/search?p=title%3Aenergie+author%3Aenqvist",
                                               expected_link_label='enqvist'))
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=title%3Aellisz+author%3Aellisz&f=keyword',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=weburl+"/search?p=title%3Aenergie+author%3Aellisz&f=keyword",
                                               expected_link_label='energie'))
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=title%3Aenergie+author%3Aenergie&f=keyword',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=weburl+"/search?p=title%3Aenergie+author%3Aenqvist&f=keyword",
                                               expected_link_label='enqvist'))

class WebSearchBooleanQueryTest(unittest.TestCase):
    """Check various boolean queries."""

    def test_successful_boolean_query(self):
        """ websearch - successful boolean query """
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=ellis+muon',
                                               expected_text="records found",
                                               expected_link_label="Detailed record"))

    def test_unsuccessful_boolean_query_where_all_individual_terms_match(self):
        """ websearch - unsuccessful boolean query where all individual terms match """
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=ellis+muon+letter',
                                               expected_text="Boolean query returned no hits. Please combine your search terms differently."))

class WebSearchAuthorQueryTest(unittest.TestCase):
    """Check various author-related queries."""

    def test_propose_similar_author_names_box(self):
        """ websearch - propose similar author names box """
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=Ellis%2C+R&f=author',
                                               expected_text="See also: similar author names",
                                               expected_link_target=weburl+"/search?p=Ellis%2C+R+K&f=author",
                                               expected_link_label="Ellis, R K"))

    def test_do_not_propose_similar_author_names_box(self):
        """ websearch - do not propose similar author names box """
        errmsgs = test_web_page_content(weburl + '/search?p=author%3A%22Ellis%2C+R%22',
                                        expected_link_target=weburl+"/search?p=Ellis%2C+R+K&f=author",
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
                         perform_request_search(p='ellis'))

    def test_search_engine_python_api_for_existing_record(self):
        """websearch - search engine Python API for existing record"""
        self.assertEqual([8],
                         perform_request_search(recid=8))

    def test_search_engine_python_api_for_nonexisting_record(self):
        """websearch - search engine Python API for non-existing record"""
        self.assertEqual([],
                         perform_request_search(recid=1234567809))

    def test_search_engine_python_api_for_nonexisting_collection(self):
        """websearch - search engine Python API for non-existing collection"""
        self.assertEqual([],
                         perform_request_search(c='Foo'))

    def test_search_engine_python_api_for_range_of_records(self):
        """websearch - search engine Python API for range of records"""
        self.assertEqual([1, 2, 3, 4, 5, 6, 7, 8, 9],
                         perform_request_search(recid=1, recidb=10))

class WebSearchSearchEngineWebAPITest(unittest.TestCase):
    """Check typical search engine Web API calls on the demo data."""

    def test_search_engine_web_api_for_failed_query(self):
        """websearch - search engine Web API for failed query"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=aoeuidhtns&of=id',
                                               expected_text="[]"))


    def test_search_engine_web_api_for_successful_query(self):
        """websearch - search engine Web API for successful query"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=ellis&of=id',
                                               expected_text="[8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 47]"))

    def test_search_engine_web_api_for_existing_record(self):
        """websearch - search engine Web API for existing record"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?recid=8&of=id',
                                               expected_text="[8]"))

    def test_search_engine_web_api_for_nonexisting_record(self):
        """websearch - search engine Web API for non-existing record"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?recid=123456789&of=id',
                                               expected_text="[]"))

    def test_search_engine_web_api_for_nonexisting_collection(self):
        """websearch - search engine Web API for non-existing collection"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?c=Foo&of=id',
                                               expected_text="[]"))

    def test_search_engine_web_api_for_range_of_records(self):
        """websearch - search engine Web API for range of records"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?recid=1&recidb=10&of=id',
                                               expected_text="[1, 2, 3, 4, 5, 6, 7, 8, 9]"))

class WebSearchRestrictedCollectionTest(unittest.TestCase):
    """Test of the restricted Theses collection behaviour."""

    def test_restricted_collection_interface_page(self):
        """websearch - restricted collection interface page body"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/collection/Theses',
                                               expected_text="The contents of this collection is restricted."))

    def test_restricted_search_as_anonymous_guest(self):
        """websearch - restricted collection not searchable by anonymous guest"""
        browser = Browser()
        browser.open(weburl + '/search?c=Theses')
        response = browser.response().read()
        if response.find("If you think you have right to access it, please authenticate yourself.") > -1:
            pass
        else:
            self.fail("Oops, searching restricted collection without password should have redirected to login dialog.")
        return

    def test_restricted_search_as_authorized_person(self):
        """websearch - restricted collection searchable by authorized person"""
        browser = Browser()
        browser.open(weburl + '/search?c=Theses')
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
        browser.open(weburl + '/search?c=Theses')
        browser.select_form(nr=0)
        browser['p_un'] = 'hyde'
        browser['p_pw'] = 'h123yde'
        browser.submit()
        # Mr. Hyde should not be able to connect:
        if browser.response().read().find("You are not authorized to access this resource.") <= -1:
            # if we got here, things are broken:
            self.fail("Oops, Mr.Hyde should not be able to search Theses collection.")

    def test_restricted_detailed_record_page_as_anonymous_guest(self):
        """websearch - restricted detailed record page not accessible to guests"""
        browser = Browser()
        browser.open(weburl + '/record/35')
        if browser.response().read().find("If you already have an account, please login using the form below") > -1:
            pass
        else:
            self.fail("Oops, searching restricted collection without password should have redirected to login dialog.")
        return

    def test_restricted_detailed_record_page_as_authorized_person(self):
        """websearch - restricted detailed record page accessible to authorized person"""
        browser = Browser()
        browser.open(weburl + '/youraccount/login')
        browser.select_form(nr=0)
        browser['p_un'] = 'jekyll'
        browser['p_pw'] = 'j123ekyll'
        browser.submit()
        browser.open(weburl + '/record/35')
        # Dr. Jekyll should be able to connect
        # (add the pw to the whole weburl because we shall be
        # redirected to '/reordrestricted/'):
        if browser.response().read().find("A High-performance Video Browsing System") > -1:
            pass
        else:
            self.fail("Oops, Dr. Jekyll should be able to access restricted detailed record page.")

    def test_restricted_detailed_record_page_as_unauthorized_person(self):
        """websearch - restricted detailed record page not accessible to unauthorized person"""
        browser = Browser()
        browser.open(weburl + '/youraccount/login')
        browser.select_form(nr=0)
        browser['p_un'] = 'hyde'
        browser['p_pw'] = 'h123yde'
        browser.submit()
        browser.open(weburl + '/record/35')
        # Mr. Hyde should not be able to connect:
        if browser.response().read().find('You are not authorized to access this resource.') <= -1:
            # if we got here, things are broken:
            self.fail("Oops, Mr.Hyde should not be able to access restricted detailed record page.")

class WebSearchRSSFeedServiceTest(unittest.TestCase):
    """Test of the RSS feed service."""

    def test_rss_feed_service(self):
        """websearch - RSS feed service"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/rss',
                                               expected_text='<rss version="2.0">'))

class WebSearchXSSVulnerabilityTest(unittest.TestCase):
    """Test possible XSS vulnerabilities of the search engine."""

    def test_xss_in_collection_interface_page(self):
        """websearch - no XSS vulnerability in collection interface pages"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/?c=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E',
                                               expected_text='Collection &lt;SCRIPT&gt;alert("XSS");&lt;/SCRIPT&gt; Not Found'))

    def test_xss_in_collection_search_page(self):
        """websearch - no XSS vulnerability in collection search pages"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?c=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E',
                                               expected_text='Collection &lt;SCRIPT&gt;alert("XSS");&lt;/SCRIPT&gt; Not Found'))

    def test_xss_in_simple_search(self):
        """websearch - no XSS vulnerability in simple search"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E',
                                               expected_text='Search term <em>&lt;SCRIPT&gt;alert("XSS");&lt;/SCRIPT&gt;</em> did not match any record.'))

    def test_xss_in_structured_search(self):
        """websearch - no XSS vulnerability in structured search"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E&f=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E',
                                               expected_text='Search term <em>&lt;SCRIPT&gt;alert("XSS");&lt;/SCRIPT&gt;</em> inside index <em>&lt;SCRIPT&gt;alert("XSS");&lt;/SCRIPT&gt;</em> did not match any record.'))


    def test_xss_in_advanced_search(self):
        """websearch - no XSS vulnerability in advanced search"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?as=1&p1=ellis&f1=author&op1=a&p2=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E&f2=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E',
                                               expected_text='Search term <em>&lt;SCRIPT&gt;alert("XSS");&lt;/SCRIPT&gt;</em> inside index <em>&lt;SCRIPT&gt;alert("XSS");&lt;/SCRIPT&gt;</em> did not match any record.'))



    def test_xss_in_browse(self):
        """websearch - no XSS vulnerability in browse"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E&f=%3CSCRIPT%3Ealert%28%22XSS%22%29%3B%3C%2FSCRIPT%3E&action_browse=Browse',
                                               expected_text='&lt;SCRIPT&gt;alert("XSS");&lt;/SCRIPT&gt;'))

class WebSearchResultsOverview(unittest.TestCase):
    """Test of the search results page's Results overview box and links."""

    def test_results_overview_split_off(self):
        """websearch - results overview box when split by collection is off"""
        browser = Browser()
        browser.open(weburl + '/search?p=of&sc=0')
        body = browser.response().read()
        if body.find("Results overview") > -1:
            self.fail("Oops, when split by collection is off, "
                      "results overview should not be present.")
        if body.find('<a name="Atlantis%20Institute%20of%20Fictive%20Science"></a>') == -1:
            self.fail("Oops, when split by collection is off, "
                      "Atlantis collection should be found.")
        if body.find('<a name="Multimedia%20%26%20Arts"></a>') > -1:
            self.fail("Oops, when split by collection is off, "
                      "Multimedia & Arts should not be found.")
        try:
            browser.find_link(url='#Multimedia%20%26%20Arts')
            self.fail("Oops, when split by collection is off, "
                      "a link to Multimedia & Arts should not be found.")
        except LinkNotFoundError:
            pass

    def test_results_overview_split_on(self):
        """websearch - results overview box when split by collection is on"""
        browser = Browser()
        browser.open(weburl + '/search?p=of&sc=1')
        body = browser.response().read()
        if body.find("Results overview") == -1:
            self.fail("Oops, when split by collection is on, "
                      "results overview should be present.")
        if body.find('<a name="Atlantis%20Institute%20of%20Fictive%20Science"></a>') > -1:
            self.fail("Oops, when split by collection is on, "
                      "Atlantis collection should not be found.")
        if body.find('<a name="Multimedia%20%26%20Arts"></a>') == -1:
            self.fail("Oops, when split by collection is on, "
                      "Multimedia & Arts should be found.")
        try:
            browser.find_link(url='#Multimedia%20%26%20Arts')
        except LinkNotFoundError:
            self.fail("Oops, when split by collection is on, "
                      "a link to Multimedia & Arts should be found.")

class WebSearchSortResultsTest(unittest.TestCase):
    """Test of the search results page's sorting capability."""

    def test_sort_results_default(self):
        """websearch - search results sorting, default method"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=cern&rg=1',
                                               expected_text="hep-th/0003295"))

    def test_sort_results_ascending(self):
        """websearch - search results sorting, ascending field"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=cern&rg=1&sf=reportnumber&so=a',
                                               expected_text="ISOLTRAP"))

    def test_sort_results_descending(self):
        """websearch - search results sorting, descending field"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=cern&rg=1&sf=reportnumber&so=d',
                                               expected_text="SCAN-9605071"))

    def test_sort_results_sort_pattern(self):
        """websearch - search results sorting, preferential sort pattern"""
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=cern&rg=1&sf=reportnumber&so=d&sp=cern',
                                               expected_text="CERN-TH-4036"))

class WebSearchSearchResultsXML(unittest.TestCase):
    """Test search results in various output"""

    def test_search_results_xm_output_split_on(self):
        """ websearch - check document element of search results in xm output (split by collection on)"""
        browser = Browser()
        browser.open(weburl + '/search?sc=1&of=xm')
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
        browser.open(weburl + '/search?sc=0&of=xm')
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
        browser.open(weburl + '/search?sc=1&of=xd')
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
        browser.open(weburl + '/search?sc=0&of=xd')
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

test_suite = make_test_suite(WebSearchWebPagesAvailabilityTest,
                             WebSearchTestSearch,
                             WebSearchTestBrowse,
                             WebSearchTestCollections,
                             WebSearchTestRecord,
                             WebSearchTestLegacyURLs,
                             WebSearchNearestTermsTest,
                             WebSearchBooleanQueryTest,
                             WebSearchAuthorQueryTest,
                             WebSearchSearchEnginePythonAPITest,
                             WebSearchSearchEngineWebAPITest,
                             WebSearchRestrictedCollectionTest,
                             WebSearchRSSFeedServiceTest,
                             WebSearchXSSVulnerabilityTest,
                             WebSearchResultsOverview,
                             WebSearchSortResultsTest,
                             WebSearchSearchResultsXML)

if __name__ == "__main__":
    warn_user_about_tests_and_run(test_suite)

