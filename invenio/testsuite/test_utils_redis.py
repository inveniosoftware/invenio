# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2010, 2011, 2013, 2014 CERN.
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
"""Redis utils Regression Test Suite."""

import time

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class RedisUtilsTest(InvenioTestCase):

    def setUp(self):
        from invenio.utils.redis import get_redis
        self.db = get_redis()

    def test_set(self):
        from invenio.config import CFG_REDIS_HOSTS
        self.db.set('hello_test', 'a')
        if CFG_REDIS_HOSTS:
            self.assertEqual(self.db.get('hello_test'), 'a')
        else:
            self.assertEqual(self.db.get('hello_test'), None)
        self.db.delete('hello_test')

    def test_expire(self):
        self.db.set('hello', 'a', 1)
        time.sleep(2)
        self.assertEqual(self.db.get('hello'), None)


TEST_SUITE = make_test_suite(RedisUtilsTest)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
