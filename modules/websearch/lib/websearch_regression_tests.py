## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

import unittest
import re
import urlparse, cgi
from sets import Set

from mechanize import Browser, LinkNotFoundError

from invenio.config import weburl, cdsname, cdslang
from invenio.testutils import make_test_suite, warn_user_about_tests_and_run, \
                              make_url, test_web_page_content, merge_error_messages
from invenio.urlutils import same_urls_p

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

        b = Browser()

        def check(legacy, new):
            b.open(legacy)
            got = b.geturl()
            
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

        b = Browser()

        def check(legacy, new):
            b.open(legacy)
            got = b.geturl()
            
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

        b = Browser()

        # We open the record in all known HTML formats
        for hformat in ('hd', 'hx', 'hm'):
            b.open(make_url('/record/1', of=hformat))

            # all except the selected links should be present in the
            # page.
            for oformat in ('hd', 'hx', 'hm', 'xm', 'xd'):
                target = make_url('/record/1', of=oformat)
                
                if oformat == hformat:
                    try:
                        b.find_link(url=target)
                    except LinkNotFoundError:
                        continue

                    self.fail('link %r should not be in page' % target)
                else:
                    try:
                        b.find_link(url=target)
                    except LinkNotFoundError:
                        self.fail('link %r should be in page' % target)
                    
        return


class WebSearchTestCollections(unittest.TestCase):
    
    def test_traversal_links(self):
        """ websearch - traverse all the publications of a collection """

        # Ensure that it is possible to traverse a collection as
        # /collection/My_Collection?jrec=...

        b = Browser()

        try:
            for as in (0, 1):
                b.open(make_url('/collection/Preprints', as=as))

                for jrec in (11, 21, 11, 23):
                    args = {'jrec': jrec, 'cc': 'Preprints'}
                    if as:
                        args['as'] = as
                        
                    url = make_url('/search', **args)
                    b.follow_link(url=url)
                    
        except LinkNotFoundError:
            self.fail('no link %r in %r' % (url, b.geturl()))
            
    def test_collections_links(self):
        """ websearch - enter in collections and subcollections """

        b = Browser()

        def tryfollow(url):
            cur = b.geturl()
            body = b.response().read()
            try:
                b.follow_link(url=url)
            except LinkNotFoundError:
                print body
                self.fail("in %r: could not find %r" % (
                    cur, url))
            return

        for as in (0, 1):
            if as: kargs = {'as': 1}
            else:  kargs = {}
                
            # We navigate from immediate son to immediate son...
            b.open(make_url('/', **kargs))
            tryfollow(make_url('/collection/Articles%20%26%20Preprints', **kargs))
            tryfollow(make_url('/collection/Articles', **kargs))

            # But we can also jump to a grandson immediately
            b.back()
            b.back()
            tryfollow(make_url('/collection/ALEPH', **kargs))

        return

    def test_records_links(self):
        """ websearch - check the links toward records in leaf collections """
        
        b = Browser()
        b.open(make_url('/collection/Preprints'))

        def harvest():

            """ Parse all the links in the page, and check that for
            each link to a detailed record, we also have the
            corresponding link to the similar records."""
            
            records = Set()
            similar = Set()
            
            for link in b.links():
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
        b.select_form(name="search")
        b.submit()

        found = harvest()
        self.failUnlessEqual(len(found), 10)
        return


class WebSearchTestBrowse(unittest.TestCase):

    def test_browse_field(self):
        """ websearch - check that browsing works """

        b = Browser()
        b.open(make_url('/'))

        b.select_form(name='search')
        b['f'] = ['title']
        b.submit(name='action_browse')

        def collect():
            # We'll get a few links to search for the actual hits, plus a
            # link to the following results.
            res = []
            for link in b.links(url_regex=re.compile(weburl + r'/search\?')):
                if link.text == 'Advanced Search':
                    continue
            
                path, q = parse_url(link.url)
                res.append((link, q))

            return res
        
        # if we follow the last link, we should get another
        # batch. There is an overlap of one item.
        batch_1 = collect()

        b.follow_link(link=batch_1[-1][0])

        batch_2 = collect()

        # FIXME: we cannot compare the whole query, as the collection
        # set is not equal
        self.failUnlessEqual(batch_1[-2][1]['p'], batch_2[0][1]['p'])
        

class WebSearchTestSearch(unittest.TestCase):

    def test_hits_in_other_collection(self):
        """ websearch - check extension of a query to the home collection """

        b = Browser()
        
        # We do a precise search in an isolated collection
        b.open(make_url('/collection/ISOLDE', ln='en'))
        
        b.select_form(name='search')
        b['f'] = ['author']
        b['p'] = 'matsubara'
        b.submit()

        path, current_q = parse_url(b.geturl())
        
        link = b.find_link(text_regex=re.compile('.*hit', re.I))
        path, target_q = parse_url(link.url)

        # the target query should be the current query without any c
        # or cc specified.
        for f in ('cc', 'c', 'action_search', 'ln'):
            if f in current_q:
                del current_q[f]

        self.failUnlessEqual(current_q, target_q)

    def test_nearest_terms(self):
        """ websearch - provide a list of nearest terms """
        
        b = Browser()
        b.open(make_url(''))

        # Search something weird
        b.select_form(name='search')
        b['p'] = 'gronf'
        b.submit()

        path, original = parse_url(b.geturl())
        
        for to_drop in ('cc', 'action_search', 'f'):
            if to_drop in original:
                del original[to_drop]
        
        # we should get a few searches back, which are identical
        # except for the p field being substituted (and the cc field
        # being dropped).
        if 'cc' in original:
            del original['cc']
        
        for link in b.links(url_regex=re.compile(weburl + r'/search\?')):
            if link.text == 'Advanced Search':
                continue
            
            path, target = parse_url(link.url)

            original['p'] = [link.text]
            self.failUnlessEqual(original, target)

        return

    def test_switch_to_simple_search(self):
        """ websearch - switch to simple search """
        
        b = Browser()
        b.open(make_url('/collection/ISOLDE', as=1))

        b.select_form(name='search')
        b['p1'] = 'tandem'
        b['f1'] = ['title']
        b.submit()

        b.follow_link(text='Simple Search')

        path, q = parse_url(b.geturl())

        self.failUnlessEqual(q, {'cc': ['ISOLDE'], 'p': ['tandem'], 'f': ['title']})

        
    def test_switch_to_advanced_search(self):
        """ websearch - switch to advanced search """
        
        b = Browser()
        b.open(make_url('/collection/ISOLDE'))

        b.select_form(name='search')
        b['p'] = 'tandem'
        b['f'] = ['title']
        b.submit()

        b.follow_link(text='Advanced Search')

        path, q = parse_url(b.geturl())

        self.failUnlessEqual(q, {'cc': ['ISOLDE'], 'p1': ['tandem'], 'f1': ['title'], 'as': ['1']})
        
    def test_no_boolean_hits(self):
        """ websearch - check the 'no boolean hits' proposed links """
        
        b = Browser()
        b.open(make_url(''))

        b.select_form(name='search')
        b['p'] = 'quasinormal muon'
        b.submit()

        path, q = parse_url(b.geturl())

        for to_drop in ('cc', 'action_search', 'f'):
            if to_drop in q:
                del q[to_drop]
        
        for bsu in ('quasinormal', 'muon'):
            l = b.find_link(text=bsu)
            q['p'] = bsu

            if not same_urls_p(l.url, make_url('/search', **q)):
                self.fail(repr((l.url, make_url('/search', **q))))

    def test_similar_authors(self):
        """ websearch - test similar authors box """

        b = Browser()
        b.open(make_url(''))

        b.select_form(name='search')
        b['p'] = 'Ellis, R K'
        b['f'] = ['author']
        b.submit()

        l = b.find_link(text="Ellis, R S")
        self.failUnless(same_urls_p(l.url, make_url('/search', p="Ellis, R S", f='author')))

class WebSearchNearestTermsTest(unittest.TestCase):
    """Check various alternatives of searches leading to the nearest
    terms box."""

    def test_nearest_terms_box_in_okay_query(self):
        """ websearch - no nearest terms box for an okay query """
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=ellis',
                                               expected_text="jump to record"))
        
    def test_nearest_terms_box_in_failed_simple_query(self):
        """ websearch - nearest terms box for failed simple query """
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=ellisz',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=weburl+"/search?p=embed",
                                               expected_link_label='embed'))

    def test_nearest_terms_box_in_failed_structured_query(self):
        """ websearch - nearest terms box for failed structured query """
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

    def test_nearest_terms_box_in_failed_phrase_query(self):
        """ websearch - nearest terms box for failed phrase query """
        self.assertEqual([],
                         test_web_page_content(weburl + '/search?p=%22ellisz%22&f=author',
                                               expected_text="Nearest terms in any collection are",
                                               expected_link_target=weburl+"/search?p=%22Enqvist%2C+K%22&f=author",
                                               expected_link_label='Enqvist, K'))

    def test_nearest_terms_box_in_failed_boolean_query(self):
        """ websearch - nearest terms box for failed boolean query """
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

test_suite = make_test_suite(WebSearchWebPagesAvailabilityTest,
                             WebSearchTestSearch,
                             WebSearchTestBrowse,
                             WebSearchTestCollections,
                             WebSearchTestRecord,
                             WebSearchTestLegacyURLs,
                             WebSearchNearestTermsTest)

if __name__ == "__main__":
    warn_user_about_tests_and_run(test_suite)
    
