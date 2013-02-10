# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2013 CERN.
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

"""Testing functions for the external collections search.

   More tests of the page getter module can be done with
       websearch_external_collections_getter_tests.py
"""

__revision__ = "$Id$"

import unittest

from invenio.websearch_external_collections_searcher import external_collections_dictionary
from invenio.websearch_external_collections_getter import HTTPAsyncPageGetter, async_download
from invenio.testutils import make_test_suite, run_test_suite, nottest

def download_and_parse():
    """Try to make a query that always return results on all search engines.
    Check that a page is well returned and that the result can be parsed.

    This test is not included in the general test suite.

    This test give false positive if any of the external server is non working or too slow.
    """
    test = [['+', 'ieee', '', 'w']]
    errors = []

    external_collections = external_collections_dictionary.values()
    urls = [engine.build_search_url(test) for engine in external_collections]
    pagegetters = [HTTPAsyncPageGetter(url) for url in urls]
    dummy = async_download(pagegetters, None, None, 30)

    for (page, engine, url) in zip(pagegetters, external_collections, urls):
        if not url:
            errors.append("Unable to build url for : " + engine.name)
            continue
        if len(page.data) == 0:
            errors.append("Zero sized page with : " + engine.name)
            continue
        if engine.parser:
            results = engine.parser.parse_and_get_results(page.data)
            num_results = engine.parser.parse_num_results()
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

@nottest
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

class ExtCollTests(unittest.TestCase):
    """Test cases for websearch_external_collections_*"""

    @nottest
    def test_download_and_parse(self):
        """websearch_external_collections - download_and_parse (not reliable, see docstring)"""
        self.assertEqual([], download_and_parse())

# FIXME: the above tests not plugged into global unit test suite
TEST_SUITE = make_test_suite() #ExtCollTests,)

if __name__ == "__main__":
    build_search_urls_test()
    run_test_suite(TEST_SUITE)
