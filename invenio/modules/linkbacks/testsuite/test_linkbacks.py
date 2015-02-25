# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2013 CERN.
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

"""WebLinkback - Unit Test Suite"""


import datetime

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

split_in_days = lazy_import('invenio.legacy.weblinkback.api:split_in_days')

from invenio.legacy.weblinkback.config import CFG_WEBLINKBACK_TYPE, CFG_WEBLINKBACK_STATUS


class TestSplitLinkbacksInInsertionDayGroups(InvenioTestCase):
    """Test for splitting linkbacks in insertion day groups"""

    def setUp(self):
        # [(linkback_id, origin_url, recid, additional_properties, linkback_type, linkback_status, insert_time)]
        self.test_data = ((23L, 'URL', 42, None, CFG_WEBLINKBACK_TYPE['TRACKBACK'], CFG_WEBLINKBACK_STATUS['APPROVED'], datetime.datetime(2011, 10, 21, 0, 1, 40)),
                          (22L, 'URL', 41, None, CFG_WEBLINKBACK_TYPE['TRACKBACK'], CFG_WEBLINKBACK_STATUS['APPROVED'], datetime.datetime(2011, 10, 20, 0, 0, 51)),
                          (21L, 'URL', 42, None, CFG_WEBLINKBACK_TYPE['TRACKBACK'], CFG_WEBLINKBACK_STATUS['APPROVED'], datetime.datetime(2011, 10, 20, 0, 0, 42)),
                          (18L, 'URL', 42, None, CFG_WEBLINKBACK_TYPE['TRACKBACK'], CFG_WEBLINKBACK_STATUS['APPROVED'], datetime.datetime(2011, 10, 20, 0, 0, 41)),
                          (16L, 'URL', 41, None, CFG_WEBLINKBACK_TYPE['TRACKBACK'], CFG_WEBLINKBACK_STATUS['APPROVED'], datetime.datetime(2011, 10, 16, 22, 44, 41)),
                          (15L, 'URL', 41, None, CFG_WEBLINKBACK_TYPE['TRACKBACK'], CFG_WEBLINKBACK_STATUS['APPROVED'], datetime.datetime(2011, 10, 16, 22, 43, 19)),
                          (14L, 'URL', 42, None, CFG_WEBLINKBACK_TYPE['TRACKBACK'], CFG_WEBLINKBACK_STATUS['APPROVED'], datetime.datetime(2011, 10, 14, 22, 43, 18)),
                          (12L, 'URL', 41, None, CFG_WEBLINKBACK_TYPE['TRACKBACK'], CFG_WEBLINKBACK_STATUS['APPROVED'], datetime.datetime(2011, 10, 13, 22, 43, 14)),
                          (11L, 'URL', 42, None, CFG_WEBLINKBACK_TYPE['TRACKBACK'], CFG_WEBLINKBACK_STATUS['APPROVED'], datetime.datetime(2011, 10, 13, 22, 32, 43)),
                          (10L, 'URL', 41, None, CFG_WEBLINKBACK_TYPE['TRACKBACK'], CFG_WEBLINKBACK_STATUS['APPROVED'], datetime.datetime(2011, 10, 10, 21, 28, 48)))

    def test_no_linkbacks(self):
        """weblinkback - no linkbacks (edge case test)"""
        result = split_in_days(())
        self.assertEqual(0, len(result))

    def test_one_linkback(self):
        """weblinkback - one linkback (edge case test)"""
        test_data = self.test_data[0:1]
        result = split_in_days(test_data)
        self.assertEqual(1, len(result))
        self.assertEqual(1, len(result[0]))
        self.assertEqual(self.test_data[0], result[0][0])

    def test_all_same_day(self):
        """weblinkback - all linkbacks of the same day (edge case test)"""
        test_data = self.test_data[1:4]
        result = split_in_days(test_data)
        self.assertEqual(1, len(result))
        self.assertEqual(3, len(result[0]))
        self.assertEqual(self.test_data[1], result[0][0])
        self.assertEqual(self.test_data[2], result[0][1])
        self.assertEqual(self.test_data[3], result[0][2])

    def test_multiple_days(self):
        """weblinkback - linkbacks of different days"""
        test_data = self.test_data[0:11]
        result = split_in_days(test_data)

        # Group count
        self.assertEqual(6, len(result))

        # First group
        self.assertEqual(1, len(result[0]))
        self.assertEqual(self.test_data[0], result[0][0])

        # Second group
        self.assertEqual(3, len(result[1]))
        self.assertEqual(self.test_data[1], result[1][0])
        self.assertEqual(self.test_data[2], result[1][1])
        self.assertEqual(self.test_data[3], result[1][2])

        # Third group
        self.assertEqual(2, len(result[2]))
        self.assertEqual(self.test_data[4], result[2][0])
        self.assertEqual(self.test_data[5], result[2][1])

        # Fourth group
        self.assertEqual(1, len(result[3]))
        self.assertEqual(self.test_data[6], result[3][0])

        # Fifth group
        self.assertEqual(2, len(result[4]))
        self.assertEqual(self.test_data[7], result[4][0])
        self.assertEqual(self.test_data[8], result[4][1])

        # Sixth group
        self.assertEqual(1, len(result[5]))
        self.assertEqual(self.test_data[9], result[5][0])

    def test_multiple_days_reversed(self):
        """weblinkback - linkbacks of different days in reversed order"""
        # Reverse test data
        test_data = list(self.test_data[0:11])
        test_data.reverse()
        test_data_reversed = tuple(test_data)

        result = split_in_days(test_data_reversed)

        # Group count
        self.assertEqual(6, len(result))

        # First group
        self.assertEqual(1, len(result[0]))
        self.assertEqual(self.test_data[9], result[0][0])

        # Second group
        self.assertEqual(2, len(result[1]))
        self.assertEqual(self.test_data[8], result[1][0])
        self.assertEqual(self.test_data[7], result[1][1])

        # Third group
        self.assertEqual(1, len(result[2]))
        self.assertEqual(self.test_data[6], result[2][0])

        # Fourth group
        self.assertEqual(2, len(result[3]))
        self.assertEqual(self.test_data[5], result[3][0])
        self.assertEqual(self.test_data[4], result[3][1])

        # Fifth group
        self.assertEqual(3, len(result[4]))
        self.assertEqual(self.test_data[3], result[4][0])
        self.assertEqual(self.test_data[2], result[4][1])
        self.assertEqual(self.test_data[1], result[4][2])

        # Sixth group
        self.assertEqual(1, len(result[5]))
        self.assertEqual(self.test_data[0], result[5][0])

TEST_SUITE = make_test_suite(TestSplitLinkbacksInInsertionDayGroups)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
