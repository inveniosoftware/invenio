# -*- coding: utf-8 -*-
## $Id$

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

"""Testing function for the external collections search.
"""

__lastupdated__ = """$Date$"""

__version__ = "$Id$"

__revision__ = "0.0.1"

import unittest

from invenio.websearch_external_collections_searcher import external_collections_dictionary
from invenio.websearch_external_collections_page_getter import HTTPAsyncPageGetter, async_download

def async_download_test():
    """Test varius cases for the async_download function:
    - test 2 workings pages : google, kernel.org
    - test 1 unresolvable name : rjfreijoiregjreoijgoirg.fr
    - test 1 bad ip : 1.2.3.4
    Return True if the test is succefull."""

    urls = ['http://www.google.com/', 'http://rjfreijoiregjreoijgoirg.fr', 'http://1.2.3.4/', 'http://www.kernel.org']
    checks = [  ['<title>Google</title>', False], 
                [None, False],
                [None, False],
                ['<title>The Linux Kernel Archives</title>', False] ]

    def finished(pagegetter, data, current_time):
        """Function called when a page is received."""
        check = data[0]
        is_ok = pagegetter.status != None
       
        if check and is_ok:
            is_ok = pagegetter.data.find(check) > 0
 
        result = is_ok == (check != None)
        if result:
            print "Test Ok (%f): " % current_time + pagegetter.uri
        else:
            print "Test failed (%f): " % current_time + pagegetter.uri

        data[1] = result

    pagegetters = [HTTPAsyncPageGetter(url) for url in urls]
    finished_list = async_download(pagegetters, finished, checks, 20)

    for (finished, check, pagegetter) in zip(finished_list, checks, pagegetters):
        if not finished:
            if check[0] == None:
                print "Test Ok: " + pagegetter.uri
                check[1] = True

    errors = [check for check in checks if check == False]
    print errors
    return len(errors) == 0

def download_and_parse():
    """Try to make a query that always return results on all search engines. 
    Check that a page is well returned and that the result can be parsed."""
    test = [['+', 'ieee', '', 'w']]
    errors = []

    external_collections = external_collections_dictionary.values()
    urls = [engine.build_search_url(test)for engine in external_collections]
    pagegetters = [HTTPAsyncPageGetter(url) for url in urls]
    finished_list = async_download(pagegetters, None, None, 30)
    print urls
    print finished_list

    for (page, engine, url) in zip(pagegetters, external_collections, urls):
        print engine.name + " - " + str(len(page.data)) + " - " + url
        if not url:
            errors.append("Unable to build url for : " + engine.name)
            continue
        if len(page.data) == 0:
            errors.append("Zero sized page with : " + engine.name)
            continue
        if engine.parser:
            results = engine.parser.parse_and_get_results(page.data)
            num_results = engine.parser.parse_num_results()
            print "  parser : " + str(len(results)) + " on " + str(num_results)
            if len(results) == 0:
                errors.append("Unable to parse results for : " + engine.name)
                continue
            if not num_results:
                errors.append("Unable to parse (None returned) number of results for : " + engine.name)
            try:
                num_results = int(num_results)
            except:
                errors.append("Unable to parse (not a number) number of results for : " + engine.name)

    return errors

def build_search_urls_test():
    """Build some classical urls from basic_search_units."""
    print "Testing external_search_engines build_search_url functions."
    tests = [ [['+', 'ellis', 'author', 'w'], ['+', 'unification', 'title', 'w'],
            ['-', 'Ross', 'author', 'w'], ['+', 'large', '', 'w'], ['-', 'helloworld', '', 'w']],
        [['+', 'ellis', 'author', 'w'], ['+', 'unification', 'title', 'w']],
        [['+', 'ellis', 'author', 'w']],
        [['-', 'Ross', 'author', 'w']] ]
    for engine in external_collections_dictionary.values():
        print engine.name
        for test in tests:
            url = engine.build_search_url(test)
            print "    Url: " + str(url)

def _test():
    """Make small test on the module."""
    async_download_test()
    build_search_urls_test()
    for error in download_and_parse():
        print error

class TestSuite(unittest.TestCase):
    """Test suite for websearch_external_collections_*"""

    def test_async_download(self):
        """test of async_download function."""
        self.assertEqual(True, async_download_test())

    def test_download_and_parse(self):
        """Download page on all know search engines and check if the result is parsable."""
        self.assertEqual([], download_and_parse())

def create_test_suite():
    """Return test suite for the external collection tests."""
    return unittest.TestSuite((unittest.makeSuite(TestSuite, 'test')))

if __name__ == "__main__":
	_test()

