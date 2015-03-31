# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Unit tests for the indexing engine washer."""

from invenio.base.wrappers import lazy_import
from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite

engine_washer = lazy_import('invenio.legacy.bibindex.engine_washer')


class TestWashers(InvenioTestCase):

    """Test for washer operations."""

    def test_lower_term_washer(self):
        """Bibindex engine washer - lower term."""
        self.assertEqual(
            engine_washer.lower_index_term("test"),
            u"test"
        )
        self.assertEqual(
            engine_washer.lower_index_term("Test"),
            u"test"
        )

    def test_lower_term_washer_encoding(self):
        """Bibindex engine washer - lower term encoding."""
        self.assertEqual(
            engine_washer.lower_index_term(u"test"),
            u"test"
        )
        self.assertEqual(
            engine_washer.lower_index_term("Über"),
            u"über"
        )
        self.assertEqual(
            engine_washer.lower_index_term(u"Über"),
            u"über"
        )

TEST_SUITE = make_test_suite(TestWashers)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
