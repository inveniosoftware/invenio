# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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
    return {'collaboration_name': '1'}


def get_fieldvalues_mock(recID, tag):
    return [tag]


def get_personids_from_bibrec_mock(recID):
    graph = {
        1: (1,),
        2: (1, 2),
        3: (2,),
        4: (3,),
        5: (4,),
    }
    return graph[recID]


def get_person_bibrecs_mock(recID):
    graph = {
        1: (1, 2),
        2: (2, 3),
        3: (4,),
        4: (5,),
    }
    return graph[recID]


def get_collaborations_from_record_mock(recID):
    return ()

# Document Graph
# Docid -> Authorid
# 1 -> 1
# 2 -> 1,2
# 3 -> 2
# 4 -> 3
# 5 -> 4


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
        def get_collaborations_from_record(self):
            """
            Check that it's fetching collaborations
            """
            tags = get_author_tags_mock()
            authors = \
                search_engine_summarizer.get_collaborations_from_record(2, tags)
            self.assertEqual(authors, set([1, 2]))

        @patch('invenio.search_engine_summarizer.get_personids_from_bibrec',
            get_personids_from_bibrec_mock)
        @patch('invenio.search_engine_summarizer.get_person_bibrecs',
            get_person_bibrecs_mock)
        def test_get_coauthors(self):
            """
            Check that it's fetching coauthors
            """
            tags = get_author_tags_mock()
            cache = {}
            author_id = 2 # real use case: 'S.Alexander.1'
            coauthors = search_engine_summarizer.get_coauthors(author_id,
                                                               tags,
                                                               cache)
            self.assertEqual(coauthors, set([1, 2]))
            self.assertEqual(cache,  {author_id: coauthors})

        @patch('invenio.search_engine_summarizer.get_collaborations_from_record',
            get_collaborations_from_record_mock)
        @patch('invenio.search_engine_summarizer.get_personids_from_bibrec',
            get_personids_from_bibrec_mock)
        @patch('invenio.search_engine_summarizer.get_person_bibrecs',
            get_person_bibrecs_mock)
        def test_compute_self_citations_no_self_citations(self):
            """
            Check self citations count matches when no self citations
            are present

            see document graph up in this file
            """
            tags = get_author_tags_mock()
            total_citations = search_engine_summarizer.compute_self_citations(
                1, (4, 5), {}, tags)
            self.assertEqual(total_citations, 2)

        @patch('invenio.search_engine_summarizer.get_collaborations_from_record',
            get_collaborations_from_record_mock)
        @patch('invenio.search_engine_summarizer.get_personids_from_bibrec',
            get_personids_from_bibrec_mock)
        @patch('invenio.search_engine_summarizer.get_person_bibrecs',
            get_person_bibrecs_mock)
        def test_compute_self_citations(self):
            """Check self citations count matches in a typical case

            1 has a self-citation
            see document graph up in this file
            """
            tags = get_author_tags_mock()
            total_citations = search_engine_summarizer.compute_self_citations(
                1, (3, 4), {}, tags)
            self.assertEqual(total_citations, 1)

        @patch('invenio.search_engine_summarizer.get_collaborations_from_record',
            get_collaborations_from_record_mock)
        @patch('invenio.search_engine_summarizer.get_personids_from_bibrec',
            get_personids_from_bibrec_mock)
        @patch('invenio.search_engine_summarizer.get_person_bibrecs',
            get_person_bibrecs_mock)
        def test_compute_self_citations_all_self_citations(self):
            """
            Check self citations count matches when all citations
            are self citations

            see document graph up in this file
            """
            tags = get_author_tags_mock()
            total_citations = search_engine_summarizer.compute_self_citations(
                1, (1, 2, 3), {}, tags)
            self.assertEqual(total_citations, 0)

TEST_SUITE = make_test_suite(WebSearchSummarizerTests)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
