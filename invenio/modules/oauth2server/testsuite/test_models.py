# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

from __future__ import absolute_import, print_function

from invenio.testsuite import InvenioTestCase, make_test_suite, \
    run_test_suite
from invenio.ext.sqlalchemy import db


class OAuth2ModelsTestCase(InvenioTestCase):
    def setUp(self):
        from ..models import Scope
        from invenio.modules.accounts.models import User
        from ..registry import scopes as scopes_registry

        # Register a test scope
        scopes_registry.register(Scope('test:scope1'))
        scopes_registry.register(Scope('test:scope2', internal=True))

        self.base_url = self.app.config.get('CFG_SITE_SECURE_URL')

        # Create needed objects
        u = User(
            email='info@invenio-software.org', nickname='tester'
        )
        u.password = "tester"

        db.session.add(u)
        db.session.commit()

        self.objects = [u]

    def test_empty_redirect_uri_and_scope(self):
        from ..models import Client
        from ..errors import ScopeDoesNotExists

        c = Client(
            client_id='dev',
            client_secret='dev',
            name='dev',
            description='',
            is_confidential=False,
            user=self.objects[0],
            _redirect_uris='',
            _default_scopes=""
        )
        self.assertIsNone(c.default_redirect_uri)
        self.assertEqual(c.redirect_uris, [])
        self.assertEqual(c.default_scopes, [])

        c.default_scopes = ['test:scope1', 'test:scope2', 'test:scope2', ]

        self.assertEqual(c.default_scopes, ['test:scope1', 'test:scope2'])
        self.assertRaises(ScopeDoesNotExists,
                          c.__setattr__, 'default_scopes', ['invalid', ])

    def test_token_scopes(self):
        from ..models import Client, Token
        from ..errors import ScopeDoesNotExists

        c = Client(
            client_id='dev',
            client_secret='dev',
            name='dev',
            description='',
            is_confidential=False,
            user=self.objects[0],
            _redirect_uris='',
            _default_scopes=""
        )
        t = Token(
            client=c,
            user=self.objects[0],
            token_type='bearer',
            access_token='dev_access',
            refresh_token='dev_refresh',
            expires=None,
            is_personal=False,
            is_internal=False,
            _scopes='',
        )
        t.scopes = ['test:scope1', 'test:scope2', 'test:scope2']
        self.assertEqual(t.scopes, ['test:scope1', 'test:scope2'])
        self.assertRaises(ScopeDoesNotExists,
                          t.__setattr__, 'scopes', ['invalid'])
        self.assertEqual(t.get_visible_scopes(),
                         ['test:scope1'])

    def test_registering_invalid_scope(self):
        from ..registry import scopes as registry
        from flask_registry import RegistryError

        self.assertRaises(RegistryError, registry.register, 'test:scope')

    def tearDown(self):
        for o in self.objects:
            db.session.delete(o)
        db.session.commit()


TEST_SUITE = make_test_suite(OAuth2ModelsTestCase)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
