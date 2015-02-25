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
Unit test for the hash functions.
"""

from invenio.utils.hash import md5, sha1
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class TestHashUtils(InvenioTestCase):
    """
    hashutils TestSuite.
    """
    def test_md5(self):
        self.assertEqual(md5('').hexdigest(),
                         'd41d8cd98f00b204e9800998ecf8427e')
        self.assertEqual(md5('test').hexdigest(),
                         '098f6bcd4621d373cade4e832627b4f6')

    def test_sha1(self):
        self.assertEqual(sha1('').hexdigest(),
                         'da39a3ee5e6b4b0d3255bfef95601890afd80709')
        self.assertEqual(sha1('test').hexdigest(),
                         'a94a8fe5ccb19ba61c4c0873d391e987982fbbd3')

TEST_SUITE = make_test_suite(TestHashUtils, )

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
