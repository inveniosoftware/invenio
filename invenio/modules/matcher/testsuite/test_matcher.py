# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2013, 2014 CERN.
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

# pylint: disable=E1102

"""Unit tests for bibmatch."""

__revision__ = "$Id$"

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

compare_fieldvalues_normal = lazy_import('invenio.legacy.bibmatch.validator:compare_fieldvalues_normal')
compare_fieldvalues_authorname = lazy_import('invenio.legacy.bibmatch.validator:compare_fieldvalues_authorname')
compare_fieldvalues_identifier = lazy_import('invenio.legacy.bibmatch.validator:compare_fieldvalues_identifier')
compare_fieldvalues_title = lazy_import('invenio.legacy.bibmatch.validator:compare_fieldvalues_title')
compare_fieldvalues_date = lazy_import('invenio.legacy.bibmatch.validator:compare_fieldvalues_date')
get_paired_comparisons = lazy_import('invenio.legacy.bibmatch.validator:get_paired_comparisons')
get_longest_words = lazy_import('invenio.legacy.bibmatch.engine:get_longest_words')


class BibMatchTest(InvenioTestCase):
    """Test functions of Bibmatch."""

    def test_get_longest_words(self):
        """ Testing get_longest_words function """
        string_to_check = "This is a string containing some long words"
        list_expected = ["containing", "string", "words"]
        self.assertEqual(list_expected,
                         get_longest_words(string_to_check, limit=3))

        string_to_check = 'This is a "string containing some quoted" long words'
        list_expected = ['"string containing some quoted"', "words"]
        self.assertEqual(list_expected,
                         get_longest_words(string_to_check, limit=2))


class BibMatchValidationTest(InvenioTestCase):
    """Test functions to check the validator of Bibmatch."""

    def test_validation_get_paired_comparisons(self):
        """bibmatch - validation: check generated paired comparisons """
        first_list = [1,2,3]
        second_list = [4,5]
        # Should return empty, as lists are not equal in length
        self.assertFalse(get_paired_comparisons(first_list, second_list, False))

        # Should return result, in un-ordered mode
        result = [((1, 4), (1, 5)), ((2, 4), (2, 5)), ((3, 4), (3, 5))]
        self.assertEqual(result, get_paired_comparisons(first_list, second_list))

    def test_validation_compare_authors(self):
        """BibMatch comparison: compare authors"""
        original_record_instances = ['Brodsky, Stanley J.']
        matched_record_instances = ['Brodsky, S.J.', 'Not, M E']
        comparisons = get_paired_comparisons(original_record_instances, matched_record_instances)
        threshold = 0.85
        matches_needed = 1
        result, dummy = compare_fieldvalues_authorname(comparisons, threshold, matches_needed)
        self.assertTrue(result)

        original_record_instances = ['Brodsky, J.']
        matched_record_instances = ['Brodsky, S.J.']
        comparisons = get_paired_comparisons(original_record_instances, matched_record_instances)
        result, dummy = compare_fieldvalues_authorname(comparisons, threshold, matches_needed)
        self.assertFalse(result)

    def test_validation_compare_strings(self):
        """BibMatch comparison: compare strings"""
        original_record_instances = ['This is some random text']
        matched_record_instances = ['I have some random text about nothing']
        comparisons = get_paired_comparisons(original_record_instances, matched_record_instances)
        threshold = 0.8
        matches_needed = 1
        result, dummy = compare_fieldvalues_normal(comparisons, threshold, matches_needed)
        self.assertFalse(result)

        original_record_instances = ['This is some random text']
        matched_record_instances = ['Is some random text']
        comparisons = get_paired_comparisons(original_record_instances, matched_record_instances)
        result, dummy = compare_fieldvalues_normal(comparisons, threshold, matches_needed)
        self.assertTrue(result)

    def test_validation_compare_identifiers(self):
        """BibMatch comparison: compare identifiers"""
        original_record_instances = ['REP-NO-02123']
        matched_record_instances = ['REPNO123']
        comparisons = get_paired_comparisons(original_record_instances, matched_record_instances)
        threshold = 1.0
        matches_needed = 1
        result, dummy = compare_fieldvalues_identifier(comparisons, threshold, matches_needed)
        self.assertFalse(result)

        original_record_instances = ['REP-NO-0123']
        matched_record_instances = ['REPNO123']
        comparisons = get_paired_comparisons(original_record_instances, matched_record_instances)
        result, dummy = compare_fieldvalues_identifier(comparisons, threshold, matches_needed)
        self.assertTrue(result)

    def test_validation_compare_date(self):
        """BibMatch comparison: compare date"""
        original_record_instances = ['2002-02']
        matched_record_instances = ['2001']
        comparisons = get_paired_comparisons(original_record_instances, matched_record_instances)
        threshold = 1.0
        matches_needed = 1
        result, dummy = compare_fieldvalues_date(comparisons, threshold, matches_needed)
        self.assertFalse(result)

        original_record_instances = ['2001-02']
        matched_record_instances = ['2001']
        comparisons = get_paired_comparisons(original_record_instances, matched_record_instances)
        result, dummy = compare_fieldvalues_date(comparisons, threshold, matches_needed)
        self.assertTrue(result)

    def test_validation_compare_title(self):
        """BibMatch comparison: compare title"""
        original_record_instances = ['Assault frequency and preformation probability']
        matched_record_instances = ['Assault frequency and preformation probability : The alpha emission process']
        comparisons = get_paired_comparisons(original_record_instances, matched_record_instances)
        threshold = 0.9
        matches_needed = 1
        # This should fail
        result, dummy = compare_fieldvalues_normal(comparisons, threshold, matches_needed)
        self.assertFalse(result)
        # Title search however, takes separators into account
        result, dummy = compare_fieldvalues_title(comparisons, threshold, matches_needed)
        self.assertTrue(result)

        # Check longer titles
        original_record_instances = ['Buffered Electropolishing \xe2\x80\x93 A New Way for ' \
                                     'Achieving Extremely Smooth Surface Finish on Nb SRF ' \
                                     'Cavities to be Used in Particle Accelerators']
        matched_record_instances = ['Buffered Electropolishing: A New Way for Achieving ' \
                                    'Extremely Smooth Surface Finish on Nb SRF Cavities ' \
                                    'To be Used in Particle Accelerators']
        comparisons = get_paired_comparisons(original_record_instances, matched_record_instances)
        result, dummy = compare_fieldvalues_title(comparisons, threshold, matches_needed)
        self.assertTrue(result)


TEST_SUITE = make_test_suite(BibMatchTest,
                             BibMatchValidationTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=False)
