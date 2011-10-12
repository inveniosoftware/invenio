# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

"""Unit tests for the search engine query parsers."""


import unittest
try:
    from mock import patch
    HAS_MOCK = True
except ImportError:
    HAS_MOCK = False

from invenio import search_engine_summarizer

from invenio.testutils import make_test_suite, run_test_suite


def get_author_tags_mock():
    return {
        'first_author': '1',
        'additional_author': '2',
        'alternative_author_name': '3',
    }


def get_fieldvalues_mock(recID, tag):
    return [tag]


def get_authors_from_record_mock(recID, tags):
    return set(['1', '2', '3'])


def search_pattern_mock(p, f):
    return ['a']


class WebSearchSummarizerTests(unittest.TestCase):
    """Test utility functions for the summarizer components"""

    def test_get_author_tags(self):
        """
        We don't care about the value since it's
        customizable but verify that it doesn't error
        """
        tags = search_engine_summarizer.get_authors_tags()
        self.assertEqual(len(tags), 4)

    if HAS_MOCK:
        @patch('invenio.search_engine_summarizer.get_fieldvalues',
            get_fieldvalues_mock)
        def test_get_authors_from_record(self):
            """
            Check that it's fetching authors
            """
            tags = get_author_tags_mock()
            authors = search_engine_summarizer.get_authors_from_record(1, tags)
            self.assertEqual(authors, set(['1', '2', '3']))

    if HAS_MOCK:
        @patch('invenio.search_engine_summarizer.get_authors_from_record',
            get_authors_from_record_mock)
        @patch('invenio.search_engine_summarizer.search_engine.search_pattern',
            search_pattern_mock)
        def test_get_coauthors(self):
            """
            Check that it's fetching coauthors
            """
            tags = get_author_tags_mock()
            cache = {}
            coauthors = search_engine_summarizer.get_coauthors('Alexander, S', tags, cache)
            self.assertEqual(coauthors, set(['1', '2', '3']))
            self.assertEqual(cache,  {'Alexander, S': coauthors})


TEST_SUITE = make_test_suite(WebSearchSummarizerTests)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
