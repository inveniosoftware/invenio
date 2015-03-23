# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Unit tests for the Acl JSONAlchemy extension."""

from invenio.base.wrappers import lazy_import
from flask_registry import PkgResourcesDirDiscoveryRegistry, \
    ImportPathRegistry, RegistryProxy
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

Model_parser = lazy_import('invenio.modules.jsonalchemy.parser:ModelParser')

TEST_PACKAGE = 'invenio.modules.access.testsuite'

test_registry = RegistryProxy('testsuite', ImportPathRegistry,
                              initial=[TEST_PACKAGE])

model_definitions = lambda: PkgResourcesDirDiscoveryRegistry(
    'models', registry_namespace=test_registry)


class TestAclExtension(InvenioTestCase):

    @classmethod
    def setUpClass(cls):
        """Invalidate any previous field definition"""
        Model_parser._model_definitions = {}

    def setUp(self):
        self.app.extensions['registry']['testsuite.models'] = \
            model_definitions()

    def tearDown(self):
        del self.app.extensions['registry']['testsuite.models']

    def test_restriction(self):
        """JSONAlchemy - restriction"""
        from flask_login import login_user, logout_user
        from invenio.ext.login.legacy_user import UserInfo
        from invenio.modules.jsonalchemy.reader import Reader
        from invenio.modules.jsonalchemy.wrappers import SmartJson

        blob = {'_id': 1}

        json = Reader.translate(blob, SmartJson, model='test_access_base',
                                master_format='json', namespace='testsuite')
        self.assertIsNotNone(json)
        self.assertTrue('restriction' in json)
        self.assertTrue('email' in json['restriction'])
        self.assertTrue(hasattr(json, 'is_authorized'))
        self.assertEqual(json.is_authorized()[0], 0)
        self.assertEqual(json.is_authorized(user_info=UserInfo(1))[0], 0)

        json['restriction']['email'] = UserInfo(1)['email']
        self.assertEqual(json.is_authorized()[0], 1)
        self.assertEqual(json.is_authorized(user_info=UserInfo(1))[0], 0)

        login_user(UserInfo(1))
        self.assertEqual(json.is_authorized()[0], 0)

        logout_user()
        self.assertEqual(json.is_authorized()[0], 1)


TEST_SUITE = make_test_suite(TestAclExtension)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
