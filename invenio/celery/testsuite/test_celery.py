# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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
Invenio Celery unit tests
"""

from __future__ import absolute_import

from invenio.testsuite import make_test_suite, run_test_suite
from invenio.celery.testsuite.helpers import CeleryTestCase


class CeleryTest(CeleryTestCase):
    def test_loader(self):
        """ Test if `workers.py` files are correctly registered. """
        self.assertTrue('invenio.celery.tasks.invenio_version' in
                        self.celery_app.tasks)

    def test_task_invenio_version(self):
        """ Test calling of tasks """

        from invenio_base.globals import cfg
        from invenio.celery.tasks import invenio_version

        # Call task function without celery
        self.assertEqual(invenio_version(), cfg['CFG_VERSION'])
        # Call task via Celery machinery
        self.assertEqual(invenio_version.delay().get(), cfg['CFG_VERSION'])

    def test_task_invenio_db_test(self):
        """ Test Flask request context in tasks """
        from invenio.celery.tasks import invenio_db_test

        # Call task via Celery machinery
        self.assertEqual(invenio_db_test.delay(1).get(), 1)
        self.assertEqual(invenio_db_test.delay(2).get(), 2)
        self.assertEqual(invenio_db_test.delay(3).get(), 3)

        # Call task without Celery machinery.
        with self.celery_app.loader.flask_app.test_request_context():
            self.assertEqual(invenio_db_test(1), 1)


TEST_SUITE = make_test_suite(CeleryTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
