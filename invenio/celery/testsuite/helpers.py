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
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA

"""
Celery unit tests helper
"""

from __future__ import absolute_import

from celery import Celery

from invenio.testsuite import InvenioTestCase
from invenio.celery import InvenioLoader


class CeleryTestCase(InvenioTestCase):
    def create_celery_app(self):
        # Execute tasks synchronously
        self.app.config['CELERY_ALWAYS_EAGER'] = True
        # Set in-memory result backend
        self.app.config['CELERY_RESULT_BACKEND'] = 'cache'
        self.app.config['CELERY_CACHE_BACKEND'] = 'memory'
        # Don't silence exceptions in tasks.
        self.app.config['CELERY_EAGER_PROPAGATES_EXCEPTIONS'] = True

        self.celery_app = Celery(
            'invenio-test',
            loader=InvenioLoader,
            flask_app=self.app,
        )
        self.celery_app.loader.import_default_modules()

    def destroy_celery_app(self):
        del self.celery_app

    def setUp(self):
        self.create_celery_app()

    def tearDown(self):
        self.destroy_celery_app()
