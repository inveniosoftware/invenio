# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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

# pylint: disable=E1102

"""
WebAuthorProfile unit tests
"""

from unittest import TestCase
from threading import Thread
from time import sleep
from invenio.testutils import make_test_suite, run_test_suite
from invenio.webauthorprofile_dbapi import expire_cache_element
from invenio.webauthorprofile_corefunctions import foo, _foo

class WebAuthorProfileTest(TestCase):
    """ Test functions to check the validator of WebAuthorProfile. """

    def test_caching(self):
        """ Test if the main corefuntions work correctly. """
        res1 = _foo(1,2,3,0)
        res2, status2, _ = foo(1,2,3,0)
        res3, status3, _ = foo(1,2,3,0)
        self.assertEqual(res1, res2)
        self.assertEqual(True, status2)
        self.assertEqual(res2, res3)
        self.assertEqual(status2, status3)

    def test_caching2(self):
        """ Test if precaching works """
        def handler(reslist, secs):
            reslist.append(foo(1,2,3,secs))

        def make_thread(secs):
            result = []
            thread = Thread(target=handler, args=(result, secs))
            return (thread, result)

        expire_cache_element('foo', 1)
        thread1, res1 = make_thread(1)
        thread2, res2 = make_thread(0)
        thread1.start()
        sleep(0.5)
        thread2.start()
        thread1.join()
        thread2.join()
        self.assertNotEqual(res1[0][0], res2[0][0])
        self.assertNotEqual(res1[0][1], res2[0][1])
        expire_cache_element('foo', 1)


TEST_SUITE = make_test_suite(WebAuthorProfileTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=False)
