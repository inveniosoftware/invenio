# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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

"""
Unit tests for the memoize facility.
"""

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class MemoizeTest(InvenioTestCase):
    """Unit test cases for Memoize."""

    def test_memoize_fib(self):
        """memoizeutils - test fib() memoisation"""
        from invenio.utils.memoize import Memoize
        from invenio.legacy.bibsched.bibtaskex import fib
        fib_memoized = Memoize(fib)
        self.assertEqual(fib(17), fib_memoized(17))

    def test_instance_method_memoize(self):
        """memoizeutils - test memoising instance method."""
        from invenio.utils.memoize import InstanceMethodMemoize

        class FooMemoize(object):

            """Class for MemoizeTest purposes."""

            def __init__(self, b):
                self.foo_b = b

            @InstanceMethodMemoize(instance_variables_names=['foo_b'],
                                   cache_limit=4)
            def add(self):

                """Method wrapped in Memoize."""

                return 9 + self.foo_b

        foo_instance = FooMemoize(2)

        self.assertEqual(9 + foo_instance.foo_b, foo_instance.add())

TEST_SUITE = make_test_suite(MemoizeTest, )

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
