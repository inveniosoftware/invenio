# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013 CERN.
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

"""Unit tests for the search engine query parsers."""


try:
    from mock import patch
    HAS_MOCK = True
except ImportError:
    HAS_MOCK = False

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


def get_author_tags_mock():
    return {'collaboration_name': '1'}


def get_fieldvalues_mock(dummy_recID, tag):
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


def get_person_bibrecs_mock(personID):
    graph = {
        1: (1, 2),
        2: (2, 3),
        3: (4,),
        4: (5,),
    }
    return graph[personID]


def get_authors_from_record_mock(recID, dummy_tags):
    return get_personids_from_bibrec_mock(recID)


def get_collaborations_from_record_mock(dummy_recID):
    return ()


def get_cited_by_mock(*args):
    def f(dummy):
        return args
    return f


def get_record_coauthors_mock(recID, dummy_tags):
    coauthors = set()
    for personid in get_personids_from_bibrec_mock(recID):
        recs = get_person_bibrecs_mock(personid)
        for recid in recs:
            coauthors.update(get_personids_from_bibrec_mock(recid))
    return coauthors


# Document Graph
# Docid -> Authorid
# 1 -> 1
# 2 -> 1,2
# 3 -> 2
# 4 -> 3
# 5 -> 4


class SelfCitesOtherTests(InvenioTestCase):
    if HAS_MOCK:
        @patch('invenio.legacy.bibrank.selfcites_indexer.get_fieldvalues',
            get_fieldvalues_mock)
        def get_collaborations_from_record(self):
            """
            Check that it's fetching collaborations
            """
            from invenio.legacy.bibrank.selfcites_indexer import get_collaborations_from_record

            tags = get_author_tags_mock()
            collaborations = get_collaborations_from_record(2, tags)
            self.assertEqual(collaborations, ['1'])

        @patch('invenio.legacy.bibrank.selfcites_indexer.get_collaborations_from_record',
            get_collaborations_from_record_mock)
        @patch('invenio.legacy.bibrank.selfcites_indexer.get_authors_from_record',
            get_authors_from_record_mock)
        @patch('invenio.legacy.bibrank.selfcites_indexer.get_cited_by',
            get_cited_by_mock(4, 5))
        def test_compute_self_citations_no_self_citations(self):
            """
            Check self citations count matches when no self citations
            are present

            see document graph up in this file
            """
            from invenio.legacy.bibrank.selfcites_indexer import compute_self_citations
            tags = get_author_tags_mock()
            self_citations = compute_self_citations(1, tags, get_record_coauthors_mock)
            self.assertEqual(self_citations, set())

        @patch('invenio.legacy.bibrank.selfcites_indexer.get_collaborations_from_record',
            get_collaborations_from_record_mock)
        @patch('invenio.legacy.bibrank.selfcites_indexer.get_authors_from_record',
            get_authors_from_record_mock)
        @patch('invenio.legacy.bibrank.selfcites_indexer.get_cited_by',
            get_cited_by_mock(3, 4))
        def test_compute_self_citations(self):
            """Check self citations count matches in a typical case

            1 has a self-citation
            see document graph up in this file
            """
            from invenio.legacy.bibrank.selfcites_indexer import compute_self_citations

            tags = get_author_tags_mock()
            self_citations = compute_self_citations(1, tags, get_record_coauthors_mock)
            self.assertEqual(self_citations, set([3]))

        @patch('invenio.legacy.bibrank.selfcites_indexer.get_collaborations_from_record',
            get_collaborations_from_record_mock)
        @patch('invenio.legacy.bibrank.selfcites_indexer.get_authors_from_record',
            get_authors_from_record_mock)
        @patch('invenio.legacy.bibrank.selfcites_indexer.get_cited_by',
            get_cited_by_mock(1, 2, 3))
        def test_compute_self_citations_all_self_citations(self):
            """
            Check self citations count matches when all citations
            are self citations

            see document graph up in this file
            """
            from invenio.legacy.bibrank.selfcites_indexer import compute_self_citations
            tags = get_author_tags_mock()
            total_citations = compute_self_citations(1, tags, get_record_coauthors_mock)
            self.assertEqual(total_citations, set([1, 2, 3]))


TEST_SUITE = make_test_suite(SelfCitesOtherTests)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
