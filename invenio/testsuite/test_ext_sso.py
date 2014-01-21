# -*- coding: utf-8 -*-
##
## This file is part of Flask-SSO
## Copyright (C) 2014 CERN.
##
## Flask-SSO is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Flask-SSO is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Flask-SSO; if not, write to the Free Software Foundation,
## Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
##
## In applying this licence, CERN does not waive the privileges and immunities
## granted to it by virtue of its status as an Intergovernmental Organization
## or submit itself to any jurisdiction.

from __future__ import absolute_import

import unittest

from contextlib import contextmanager
from flask import request_started, request
from flask.ext.login import current_user
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

try:
    from invenio.ext.sso import setup_app
    has_sso = True
except ImportError:
    has_sso = False


class TestSSO(InvenioTestCase):
    """
    Tests of extension creation
    """

    @unittest.skipUnless(has_sso, 'Flask-SSO is not installed')
    def test_login_handler(self):
        self.app = setup_app(self.app)

        @contextmanager
        def request_environ_set(app, data):

            def handler(sender, **kwargs):
                for (k, v) in data.items():
                    request.environ[k] = v

            with request_started.connected_to(handler, app):
                yield

        def run(data, expected_data):
            with request_environ_set(self.app, data):
                with self.app.test_client() as c:
                    c.get(self.app.config['SSO_LOGIN_URL'])
                    current_user['email'] == expected_data['email']

        data = {
            'ADFS_GROUP': 'CERN Registered',
            'ADFS_LOGIN': 'admin',
            'ADFS_EMAIL': self.app.config['CFG_SITE_ADMIN_EMAIL'],
        }
        expected_data = {'email': self.app.config['CFG_SITE_ADMIN_EMAIL']}

        run(data, expected_data)

TEST_SUITE = make_test_suite(TestSSO)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
