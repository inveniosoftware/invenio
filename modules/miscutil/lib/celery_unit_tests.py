# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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
Invenio Celery unit tests
"""

from __future__ import absolute_import

# Invenio runs tests as standalone modules, instead of from their package
# hierarchy. This means that this test module is executed as if you ran
# 'python celery_unit_tests.py'. This causes the directory of this file to be added
# to the sys.path. This causes the module invenio.celery to be importable
# as just 'celery' since modules/miscutil/lib is now in sys.path. Thus, the real
# celery package is no longer importable, causing an import error in
# invenio.celery. Solutions could be to rename invenio.celery, however then you
# cannot start celery workers with 'celeryd -A invenio' and must use something
# like 'celeryd -A invenio.<new name>.celery' instead.
#
# Below lines removes the directory of this file from the sys.path so modules
# are imported from their proper location.
import sys
import os
from distutils.sysconfig import get_python_lib
EXCLUDE = [
    '',
    os.path.dirname(os.path.abspath(__file__)),
    os.path.join(get_python_lib(), 'invenio'),
]
sys.path = filter(
    lambda x: x not in EXCLUDE,
    sys.path
)

import unittest
from invenio.testutils import make_test_suite, run_test_suite
from invenio.celery import celery


class CeleryTest(unittest.TestCase):
    def setUp(self):
        # Execute tasks synchronously
        celery.conf.CELERY_ALWAYS_EAGER = True
        # Set in-memory result backend
        celery.conf.CELERY_RESULT_BACKEND = 'cache'
        celery.conf.CELERY_CACHE_BACKEND = 'memory'
        # Don't silence exceptions in tasks.
        celery.conf.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
        # Trigger task registering (this is done by the worker, to register all tasks)
        celery.loader.import_default_modules()

    def test_loader(self):
        """ Test if *_tasks.py files are correctly registered. """
        self.assertTrue('invenio.celery_tasks.invenio_version' in celery.tasks)

    def test_task_invenio_version(self):
        """ Test calling of tasks """
        from invenio.config import CFG_VERSION
        from invenio.celery_tasks import invenio_version
        # Call task function without celery
        self.assertEqual(invenio_version(), CFG_VERSION)
        # Call task via Celery machinery
        self.assertEqual(invenio_version.delay().get(), CFG_VERSION)

    def test_task_invenio_db_test(self):
        """ Test Flask request context in tasks """
        from invenio.celery_tasks import invenio_db_test
        # Call task via Celery machinery
        self.assertEqual(invenio_db_test.delay(1).get(), 1)
        self.assertEqual(invenio_db_test.delay(2).get(), 2)
        self.assertEqual(invenio_db_test.delay(3).get(), 3)
        # Call task without Celery machinery.
        with celery.loader.flask_app.test_request_context():
            self.assertEqual(invenio_db_test(1), 1)


TEST_SUITE = make_test_suite(CeleryTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
