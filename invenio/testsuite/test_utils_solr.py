# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2013 CERN.
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

"""Unit tests for the solrutils library."""

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

replace_invalid_solr_characters = lazy_import(
    'invenio.legacy.miscutil.solrutils_bibindex_indexer:'
    'replace_invalid_solr_characters')
get_collection_filter = lazy_import(
    'invenio.legacy.miscutil.solrutils_bibrank_searcher:'
    'get_collection_filter')


class TestReplaceInvalidCharacters(InvenioTestCase):
    """Test for removal of invalid Solr characters and control characters."""

    def test_no_replacement(self):
        """solrutils - no characters to replace"""
        utext_in = unicode('foo\nbar\tfab\n\r', 'utf-8')
        utext_out = unicode('foo\nbar\tfab\n\r', 'utf-8')
        self.assertEqual(utext_out, replace_invalid_solr_characters(utext_in))

    def test_replace_control_characters(self):
        """solrutils - replacement of control characters"""
        self.assertEqual(u'abc \nde', replace_invalid_solr_characters(u'abc\u0000\nde'))
        self.assertEqual(u'abc \nde', replace_invalid_solr_characters(u'abc\u0003\nde'))
        self.assertEqual(u'abc \nde', replace_invalid_solr_characters(u'abc\u0008\nde'))

        self.assertEqual(u'abc \nde', replace_invalid_solr_characters(u'abc\u000B\nde'))
        self.assertEqual(u'abc \nde', replace_invalid_solr_characters(u'abc\u000C\nde'))

        self.assertEqual(u'abc \nde', replace_invalid_solr_characters(u'abc\u000E\nde'))
        self.assertEqual(u'abc \nde', replace_invalid_solr_characters(u'abc\u0012\nde'))
        self.assertEqual(u'abc \nde', replace_invalid_solr_characters(u'abc\u001F\nde'))

    def test_replace_invalid_chars(self):
        """solrutils - replacement of invalid characters"""
        self.assertEqual(u'abc\nde', replace_invalid_solr_characters(u'abc\uD800\nde'))
        self.assertEqual(u'abc\nde', replace_invalid_solr_characters(u'abc\uDF12\nde'))
        self.assertEqual(u'abc\nde', replace_invalid_solr_characters(u'abc\uDFFF\nde'))

        self.assertEqual(u'abc\nde', replace_invalid_solr_characters(u'abc\uFFFE\nde'))
        self.assertEqual(u'abc\nde', replace_invalid_solr_characters(u'abc\uFFFF\nde'))


class TestSolrRankingHelpers(InvenioTestCase):
    """Test for Solr ranking helper functions."""
    def test_get_collection_filter(self):
        """solrutils - creation of collection filter"""
        import intbitset
        self.assertEqual('', get_collection_filter(intbitset.intbitset([]), 0))
        self.assertEqual('', get_collection_filter(intbitset.intbitset([]), 1))
        self.assertEqual('', get_collection_filter(intbitset.intbitset([1, 2, 3, 4, 5]), 0))
        self.assertEqual('id:(5)', get_collection_filter(intbitset.intbitset([1, 2, 3, 4, 5]), 1))
        self.assertEqual('id:(4 5)', get_collection_filter(intbitset.intbitset([1, 2, 3, 4, 5]), 2))
        self.assertEqual('id:(1 2 3 4 5)', get_collection_filter(intbitset.intbitset([1, 2, 3, 4, 5]), 5))
        self.assertEqual('id:(1 2 3 4 5)', get_collection_filter(intbitset.intbitset([1, 2, 3, 4, 5]), 6))


TEST_SUITE = make_test_suite(TestReplaceInvalidCharacters, TestSolrRankingHelpers)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
