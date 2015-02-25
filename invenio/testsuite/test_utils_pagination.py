# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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

"""
Test unit for the miscutil/paginationutils module.
"""

from invenio.utils.pagination import Pagination
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class TestPaginationUtils(InvenioTestCase):
    """
    PaginationUtils TestSuite.
    """

    def test_first_page(self):
        page = 1
        per_page = 10
        total_count = 98
        pagination = Pagination(page, per_page, total_count)
        self.assertFalse(pagination.has_prev)
        self.assertTrue(pagination.has_next)
        self.assertEqual(list(pagination.iter_pages()), [1, 2, 3, None, 10])

    def test_last_page(self):
        page = 10
        per_page = 10
        total_count = 98
        pagination = Pagination(page, per_page, total_count)
        self.assertTrue(pagination.has_prev)
        self.assertFalse(pagination.has_next)
        self.assertEqual(list(pagination.iter_pages()), [1, None, 9, 10])

    def test_middle_page(self):
        page = 5
        per_page = 10
        total_count = 98
        pagination = Pagination(page, per_page, total_count)
        self.assertTrue(pagination.has_prev)
        self.assertTrue(pagination.has_next)
        self.assertEqual(list(pagination.iter_pages()),
                         [1, None, 4, 5, 6, 7, None, 10])


TEST_SUITE = make_test_suite(TestPaginationUtils,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
