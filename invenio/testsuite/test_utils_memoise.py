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
Unit tests for the memoise facility.
"""

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class MemoiseTest(InvenioTestCase):
    """Unit test cases for Memoise."""

    def test_memoise_fib(self):
        """memoiseutils - test fib() memoisation"""
        from invenio.utils.memoise import Memoise
        from invenio.legacy.bibsched.bibtaskex import fib
        fib_memoised = Memoise(fib)
        self.assertEqual(fib(17), fib_memoised(17))

TEST_SUITE = make_test_suite(MemoiseTest, )

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
