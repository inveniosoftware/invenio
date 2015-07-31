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

from __future__ import absolute_import, print_function

from invenio.ext.sqlalchemy import db
from invenio.testsuite import InvenioTestCase, make_test_suite, \
    run_test_suite


class OAuth2ModelsTestCase(InvenioTestCase):
    def setUp(self):
        from ..models import Scope
        from invenio_accounts.models import User
        from invenio.modules.oauth2server.models import Client, Token

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

        self.create_objects([u])

        # environment
        #
        # resource_owner -- client1 -- token_1
        #                     |
        #                     -------- token_2
        #                               |
        #       consumer ----------------

        # create resource_owner and consumer
        self.resource_owner = User(
            email='resource_owner@invenio-software.org',
            nickname='resource_owner', password='test')
        self.consumer = User(
            email='consumer@invenio-software.org', nickname='consumer',
            password='test')

        self.create_objects([self.resource_owner, self.consumer])

        # create resource_owner -> client_1
        self.u1c1 = Client(
            client_id='client_test_u1c1',
            client_secret='client_test_u1c1',
            name='client_test_u1c1',
            description='',
            is_confidential=False,
            user=self.resource_owner,
            _redirect_uris='',
            _default_scopes=""
        )

        self.create_objects([self.u1c1])

        # create resource_owner -> client_1 / resource_owner -> token_1
        self.u1c1u1t1 = Token(
            client=self.u1c1,
            user=self.resource_owner,
            token_type='u',
            access_token='dev_access_1',
            refresh_token='dev_refresh_1',
            expires=None,
            is_personal=False,
            is_internal=False,
            _scopes='',
        )
        # create consumer -> client_1 / resource_owner -> token_2
        self.u1c1u2t2 = Token(
            client=self.u1c1,
            user=self.consumer,
            token_type='u',
            access_token='dev_access_2',
            refresh_token='dev_refresh_2',
            expires=None,
            is_personal=False,
            is_internal=False,
            _scopes='',
        )

        # create objects
        self.create_objects([self.u1c1u1t1, self.u1c1u2t2])

        self.objects = [u,
                        self.resource_owner, self.consumer,
                        self.u1c1u1t1, self.u1c1u2t2]

    def tearDown(self):
        self.delete_objects(self.objects)

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
        self.create_objects([c])
        self.assertIsNone(c.default_redirect_uri)
        self.assertEqual(c.redirect_uris, [])
        self.assertEqual(c.default_scopes, [])

        c.default_scopes = ['test:scope1', 'test:scope2', 'test:scope2', ]

        self.assertEqual(c.default_scopes, ['test:scope1', 'test:scope2'])
        self.assertRaises(ScopeDoesNotExists,
                          c.__setattr__, 'default_scopes', ['invalid', ])
        self.delete_objects([c])

    def test_token_scopes(self):
        from ..models import Client, Token
        from ..errors import ScopeDoesNotExists

        c = Client(
            client_id='dev2',
            client_secret='dev2',
            name='dev2',
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
        self.create_objects([c, t])
        self.assertEqual(t.scopes, ['test:scope1', 'test:scope2'])
        self.assertRaises(ScopeDoesNotExists,
                          t.__setattr__, 'scopes', ['invalid'])
        self.assertEqual(t.get_visible_scopes(),
                         ['test:scope1'])
        self.delete_objects([c])

    def test_registering_invalid_scope(self):
        from ..registry import scopes as registry
        from flask_registry import RegistryError

        self.assertRaises(RegistryError, registry.register, 'test:scope')

    def test_deletion_of_consumer_resource_owner(self):
        """Test deleting of connected user."""
        from invenio_accounts.models import User
        from invenio.modules.oauth2server.models import Client, Token

        uid_1 = self.resource_owner.id
        cid_1 = self.u1c1.client_id
        tid_1 = self.u1c1u1t1.id
        tid_2 = self.u1c1u2t2.id

        # start testing

        # delete consumer
        self.delete_objects([self.consumer])

        # assert that t2 deleted
        self.assertFalse(
            db.session.query(
                Token.query.filter(Token.id == tid_2).exists()).scalar())
        # still exist resource_owner and client_1 and token_1
        self.assertTrue(
            db.session.query(
                User.query.filter(User.id == uid_1).exists()).scalar())
        self.assertTrue(
            db.session.query(
                Client.query.filter(
                    Client.client_id == cid_1).exists()).scalar())
        self.assertTrue(
            db.session.query(
                Token.query.filter(Token.id == tid_1).exists()).scalar())

        # delete resource_owner
        self.delete_objects([self.resource_owner])

        # still resource_owner and client_1 and token_1 deleted
        self.assertFalse(
            db.session.query(
                Client.query.filter(
                    Client.client_id == cid_1).exists()).scalar())
        self.assertFalse(
            db.session.query(
                Token.query.filter(Token.id == tid_1).exists()).scalar())

    def test_deletion_of_resource_owner_consumer(self):
        """Test deleting of connected user."""
        from invenio_accounts.models import User
        from invenio.modules.oauth2server.models import Client, Token

        uid_consumer = self.consumer.id
        cid_1 = self.u1c1.client_id
        tid_1 = self.u1c1u1t1.id
        tid_2 = self.u1c1u2t2.id

        # start testing

        # delete consumer
        self.delete_objects([self.resource_owner])

        # assert that c1, t1, t2 deleted
        self.assertFalse(
            db.session.query(
                Client.query.filter(
                    Client.client_id == cid_1).exists()).scalar())
        self.assertFalse(
            db.session.query(
                Token.query.filter(Token.id == tid_1).exists()).scalar())
        self.assertFalse(
            db.session.query(
                Token.query.filter(Token.id == tid_2).exists()).scalar())
        # still exist consumer
        self.assertTrue(
            db.session.query(
                User.query.filter(User.id == uid_consumer).exists()).scalar())

        # delete consumer
        self.delete_objects([self.consumer])

    def test_deletion_of_client1(self):
        """Test deleting of connected user."""
        from invenio_accounts.models import User
        from invenio.modules.oauth2server.models import Token

        uid_resource_manager = self.resource_owner.id
        uid_consumer = self.consumer.id
        tid_1 = self.u1c1u1t1.id
        tid_2 = self.u1c1u2t2.id

        # start testing

        # delete client_1
        self.delete_objects([self.u1c1])

        # assert that token_1, token_2 deleted
        self.assertFalse(
            db.session.query(
                Token.query.filter(Token.id == tid_1).exists()).scalar())
        self.assertFalse(
            db.session.query(
                Token.query.filter(Token.id == tid_2).exists()).scalar())
        # still exist resource_owner, consumer
        self.assertTrue(
            db.session.query(
                User.query.filter(
                    User.id == uid_resource_manager).exists()).scalar())
        self.assertTrue(
            db.session.query(
                User.query.filter(User.id == uid_consumer).exists()).scalar())

        # delete consumer
        self.delete_objects([self.consumer])

    def test_deletion_of_token1(self):
        """Test deleting of connected user."""
        from invenio_accounts.models import User
        from invenio.modules.oauth2server.models import Client, Token

        uid_resource_manager = self.resource_owner.id
        uid_consumer = self.consumer.id
        cid_1 = self.u1c1.client_id
        tid_2 = self.u1c1u2t2.id

        # start testing

        # delete token_1
        self.delete_objects([self.u1c1u1t1])

        # still exist resource_owner, consumer, client_1, token_2
        self.assertTrue(
            db.session.query(
                User.query.filter(
                    User.id == uid_resource_manager).exists()).scalar())
        self.assertTrue(
            db.session.query(
                User.query.filter(User.id == uid_consumer).exists()).scalar())
        self.assertTrue(
            db.session.query(
                Client.query.filter(
                    Client.client_id == cid_1).exists()).scalar())
        self.assertTrue(
            db.session.query(
                Token.query.filter(Token.id == tid_2).exists()).scalar())

        # delete consumer
        self.delete_objects([self.consumer])

    def test_deletion_of_token2(self):
        """Test deleting of connected user."""
        from invenio_accounts.models import User
        from invenio.modules.oauth2server.models import Client, Token

        uid_resource_manager = self.resource_owner.id
        uid_consumer = self.consumer.id
        cid_1 = self.u1c1.client_id
        tid_1 = self.u1c1u1t1.id

        # start testing

        # delete token_2
        self.delete_objects([self.u1c1u2t2])

        # still exist resource_owner, consumer, client_1, token_1
        self.assertTrue(
            db.session.query(
                User.query.filter(
                    User.id == uid_resource_manager).exists()).scalar())
        self.assertTrue(
            db.session.query(
                User.query.filter(User.id == uid_consumer).exists()).scalar())
        self.assertTrue(
            db.session.query(
                Client.query.filter(
                    Client.client_id == cid_1).exists()).scalar())
        self.assertTrue(
            db.session.query(
                Token.query.filter(Token.id == tid_1).exists()).scalar())

        # delete consumer
        self.delete_objects([self.consumer])


TEST_SUITE = make_test_suite(OAuth2ModelsTestCase)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
