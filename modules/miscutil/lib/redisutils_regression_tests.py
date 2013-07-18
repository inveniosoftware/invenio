# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2010, 2011, 2013 CERN.
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
"""Redis utils Regression Test Suite."""

import time

from invenio.testutils import InvenioTestCase
from invenio.testutils import make_test_suite, run_test_suite
from invenio.config import CFG_REDIS_HOSTS
from invenio.redisutils import get_redis

class RedisUtilsTest(InvenioTestCase):
    if CFG_REDIS_HOSTS:
        def test_simple(self):
            db = get_redis()
            db.set('hello_test', 'a')
            self.assertEqual(db.get('hello_test'), 'a')
            db.delete('hello_test')
    else:
        def test_dummy(self):
            db = get_redis()
            db.set('hello', 'a')
            self.assertEqual(db.get('hello'), None)
            db.delete('hello')

    def test_expire(self):
        db = get_redis()
        db.set('hello', 'a', 1)
        time.sleep(2)
        self.assertEqual(db.get('hello'), None)


TEST_SUITE = make_test_suite(RedisUtilsTest)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
