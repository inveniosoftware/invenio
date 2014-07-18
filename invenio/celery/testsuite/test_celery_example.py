# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

from __future__ import absolute_import

from invenio.testsuite import make_test_suite, run_test_suite
from invenio.celery.testsuite.helpers import CeleryTestCase


class CeleryExampleTest(CeleryTestCase):
    def setUp(self):
        super(CeleryExampleTest, self).setUp()
        self.called = 0

        # Register celery test task
        @self.celery_app.task(ignore_result=True)
        def test_task():
            # Increment call counter on each call
            self.called += 1

        self.task = test_task

    def test_async_call(self):
        # Due to CELERY_ALWAYS_EAGER task will actually be called
        # synchronously.
        assert self.called == 0
        self.task.delay()
        assert self.called == 1

    def test_sync_call(self):
        # Normally tasks can also just be called as a normal function.
        assert self.called == 0
        self.task()
        assert self.called == 1


TEST_SUITE = make_test_suite(CeleryExampleTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
