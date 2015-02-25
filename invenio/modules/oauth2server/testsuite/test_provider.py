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

import logging
import os

from datetime import datetime, timedelta
from flask import url_for, request
from flask_oauthlib.client import prepare_request
from mock import MagicMock
try:
    from six.moves.urllib.parse import urlparse
except ImportError:
    from urllib.parse import urlparse

from invenio.base.globals import cfg
from invenio.ext.sqlalchemy import db
from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite

from .helpers import create_client

logging.basicConfig(level=logging.DEBUG)


class ProviderTestCase(InvenioTestCase):

    def create_app(self):
        try:
            app = super(ProviderTestCase, self).create_app()
            app.testing = True
            app.config.update(dict(
                OAUTH2_CACHE_TYPE='simple',
            ))
            client = create_client(app, 'oauth2test')
            client.http_request = MagicMock(
                side_effect=self.patch_request(app)
            )
        except Exception as e:
            print(e)
        return app

    def patch_request(self, app):
        test_client = app.test_client()

        def make_request(uri, headers=None, data=None, method=None):
            uri, headers, data, method = prepare_request(
                uri, headers, data, method
            )
            if not headers and data is not None:
                headers = {
                    'Content-Type': ' application/x-www-form-urlencoded'
                }

            # test client is a `werkzeug.test.Client`
            parsed = urlparse(uri)
            uri = '%s?%s' % (parsed.path, parsed.query)
            resp = test_client.open(
                uri, headers=headers, data=data, method=method,
                base_url=cfg['CFG_SITE_SECURE_URL']
            )
            # for compatible
            resp.code = resp.status_code
            return resp, resp.data
        return make_request

    def setUp(self):
        super(ProviderTestCase, self).setUp()
        # Set environment variable DEBUG to true, to allow testing without
        # SSL in oauthlib.
        if self.app.config.get('CFG_SITE_SECURE_URL').startswith('http://'):
            self.os_debug = os.environ.get('OAUTHLIB_INSECURE_TRANSPORT', '')
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'

        from ..models import Client, Scope
        from invenio.modules.accounts.models import User
        from ..registry import scopes as scopes_registry

        # Register a test scope
        scopes_registry.register(Scope('test:scope'))

        self.base_url = self.app.config.get('CFG_SITE_SECURE_URL')

        # Create needed objects
        u = User(
            email='info@invenio-software.org', nickname='tester'
        )
        u.password = "tester"

        u2 = User(
            email='abuse@invenio-software.org', nickname='tester2'
        )
        u2.password = "tester2"

        db.session.add(u)
        db.session.add(u2)

        c1 = Client(
            client_id='dev',
            client_secret='dev',
            name='dev',
            description='',
            is_confidential=False,
            user=u,
            _redirect_uris='%s/oauth2test/authorized' % self.base_url,
            _default_scopes="test:scope"
        )

        c2 = Client(
            client_id='confidential',
            client_secret='confidential',
            name='confidential',
            description='',
            is_confidential=True,
            user=u,
            _redirect_uris='%s/oauth2test/authorized' % self.base_url,
            _default_scopes="test:scope"
        )

        db.session.add(c1)
        db.session.add(c2)

        db.session.commit()

        self.objects = [u, u2, c1, c2]

        # Create a personal access token as well.
        from ..models import Token
        self.personal_token = Token.create_personal(
            'test-personal', 1, scopes=[], is_internal=True
        )

    def tearDown(self):
        super(ProviderTestCase, self).tearDown()
        # Set back any previous value of DEBUG environment variable.
        if self.app.config.get('CFG_SITE_SECURE_URL').startswith('http://'):
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = self.os_debug
        self.base_url = None

        for o in self.objects:
            db.session.delete(o)
        db.session.commit()

    def parse_redirect(self, location, parse_fragment=False):
        from werkzeug.urls import url_parse, url_decode, url_unparse
        scheme, netloc, script_root, qs, anchor = url_parse(location)
        return (
            url_unparse((scheme, netloc, script_root, '', '')),
            url_decode(anchor if parse_fragment else qs)
        )


class OAuth2ProviderTestCase(ProviderTestCase):

    def test_client_salt(self):
        from ..models import Client

        c = Client(
            name='Test something',
            is_confidential=True,
            user_id=1,
        )

        c.gen_salt()
        assert len(c.client_id) == \
            self.app.config.get('OAUTH2_CLIENT_ID_SALT_LEN')
        assert len(c.client_secret) == \
            self.app.config.get('OAUTH2_CLIENT_SECRET_SALT_LEN')

        db.session.add(c)
        db.session.commit()

    def test_invalid_authorize_requests(self):
        # First login on provider site
        self.login("tester", "tester")

        for client_id in ['dev', 'confidential']:
            redirect_uri = '%s/oauth2test/authorized' % self.base_url
            scope = 'test:scope'
            response_type = 'code'

            error_url = url_for('oauth2server.errors')

            # Valid request authorize request
            r = self.client.get(url_for(
                'oauth2server.authorize', redirect_uri=redirect_uri,
                scope=scope, response_type=response_type, client_id=client_id,
            ))
            self.assertStatus(r, 200)

            # Invalid scope
            r = self.client.get(url_for(
                'oauth2server.authorize', redirect_uri=redirect_uri,
                scope='INVALID', response_type=response_type,
                client_id=client_id,
            ))
            self.assertStatus(r, 302)
            next_url, data = self.parse_redirect(r.location)
            self.assertEqual(data['error'], 'invalid_scope')
            assert next_url == redirect_uri

            # Invalid response type
            r = self.client.get(url_for(
                'oauth2server.authorize', redirect_uri=redirect_uri,
                scope=scope, response_type='invalid', client_id=client_id,
            ))
            self.assertStatus(r, 302)
            next_url, data = self.parse_redirect(r.location)
            self.assertEqual(data['error'], 'unauthorized_client')
            assert next_url == redirect_uri

            # Missing response_type
            r = self.client.get(url_for(
                'oauth2server.authorize', redirect_uri=redirect_uri,
                scope=scope, client_id=client_id,
            ))
            self.assertStatus(r, 302)
            next_url, data = self.parse_redirect(r.location)
            self.assertEqual(data['error'], 'invalid_request')
            assert next_url == redirect_uri

            # Duplicate parameter
            r = self.client.get(url_for(
                'oauth2server.authorize', redirect_uri=redirect_uri,
                scope=scope, response_type='invalid', client_id=client_id,
            ) + "&client_id=%s" % client_id)
            self.assertStatus(r, 302)
            next_url, data = self.parse_redirect(r.location)
            self.assertEqual(data['error'], 'invalid_request')
            assert next_url == redirect_uri

            # Invalid cilent_id
            r = self.client.get(url_for(
                'oauth2server.authorize', redirect_uri=redirect_uri,
                scope=scope, response_type=response_type, client_id='invalid',
            ))
            self.assertStatus(r, 302)
            next_url, data = self.parse_redirect(r.location)
            self.assertEqual(data['error'], 'invalid_client_id')
            assert error_url in next_url

            r = self.client.get(next_url, query_string=data)
            assert 'invalid_client_id' in r.data

            # Invalid redirect uri
            r = self.client.get(url_for(
                'oauth2server.authorize', redirect_uri='http://localhost/',
                scope=scope, response_type=response_type, client_id=client_id,
            ))
            self.assertStatus(r, 302)
            next_url, data = self.parse_redirect(r.location)
            self.assertEqual(data['error'], 'mismatching_redirect_uri')
            assert error_url in next_url

    def test_refresh_flow(self):
        # First login on provider site
        self.login("tester", "tester")

        data = dict(
            redirect_uri='%s/oauth2test/authorized' % self.base_url,
            scope='test:scope',
            response_type='code',
            client_id='confidential',
            state='mystate'
        )

        r = self.client.get(url_for('oauth2server.authorize', **data))
        self.assertStatus(r, 200)

        data['confirm'] = 'yes'
        data['scope'] = 'test:scope'
        data['state'] = 'mystate'

        # Obtain one time code
        r = self.client.post(
            url_for('oauth2server.authorize'), data=data
        )
        self.assertStatus(r, 302)
        next_url, res_data = self.parse_redirect(r.location)
        assert res_data['code']
        assert res_data['state'] == 'mystate'

        # Exchange one time code for access token
        r = self.client.post(
            url_for('oauth2server.access_token'), data=dict(
                client_id='confidential',
                client_secret='confidential',
                grant_type='authorization_code',
                code=res_data['code'],
            )
        )
        self.assertStatus(r, 200)
        assert r.json['access_token']
        assert r.json['refresh_token']
        assert r.json['scope'] == 'test:scope'
        assert r.json['token_type'] == 'Bearer'
        refresh_token = r.json['refresh_token']
        old_access_token = r.json['access_token']

        # Access token valid
        r = self.client.get(url_for('oauth2server.info',
                            access_token=old_access_token))
        self.assert200(r)

        # Obtain new access token with refresh token
        r = self.client.post(
            url_for('oauth2server.access_token'), data=dict(
                client_id='confidential',
                client_secret='confidential',
                grant_type='refresh_token',
                refresh_token=refresh_token,
            )
        )
        self.assertStatus(r, 200)
        assert r.json['access_token']
        assert r.json['refresh_token']
        assert r.json['access_token'] != old_access_token
        assert r.json['refresh_token'] != refresh_token
        assert r.json['scope'] == 'test:scope'
        assert r.json['token_type'] == 'Bearer'

        # New access token valid
        r = self.client.get(url_for('oauth2server.info',
                                    access_token=r.json['access_token']))
        self.assert200(r)

        # Old access token no longer valid
        r = self.client.get(url_for('oauth2server.info',
                                    access_token=old_access_token,),
                            base_url=cfg['CFG_SITE_SECURE_URL'])
        self.assert401(r)

    def test_web_auth_flow(self):
        # Go to login - should redirect to oauth2 server for login an
        # authorization
        r = self.client.get('/oauth2test/test-ping')

        # First login on provider site
        self.login("tester", "tester")

        r = self.client.get('/oauth2test/login')
        self.assertStatus(r, 302)
        next_url, data = self.parse_redirect(r.location)

        # Authorize page
        r = self.client.get(next_url, query_string=data)
        self.assertStatus(r, 200)

        # User confirms request
        data['confirm'] = 'yes'
        data['scope'] = 'test:scope'
        data['state'] = ''

        r = self.client.post(next_url, data=data)
        self.assertStatus(r, 302)
        next_url, data = self.parse_redirect(r.location)
        assert next_url == '%s/oauth2test/authorized' % self.base_url
        assert 'code' in data

        # User is redirected back to client site.
        # - The client view /oauth2test/authorized will in the
        #   background fetch the access token.
        r = self.client.get(next_url, query_string=data)
        self.assertStatus(r, 200)

        # Authentication flow has now been completed, and the access
        # token can be used to access protected resources.
        r = self.client.get('/oauth2test/test-ping')
        self.assert200(r)
        self.assertEqual(r.json, dict(ping='pong'))

        # Authentication flow has now been completed, and the access
        # token can be used to access protected resources.
        r = self.client.get('/oauth2test/test-ping')
        self.assert200(r)
        self.assertEqual(r.json, dict(ping='pong'))

        r = self.client.get('/oauth2test/test-info')
        self.assert200(r)
        assert r.json.get('client') == 'confidential'
        assert r.json.get('user') == self.objects[0].id
        assert r.json.get('scopes') == [u'test:scope']

        # Access token doesn't provide access to this URL.
        r = self.client.get(
            '/oauth2test/test-invalid',
            base_url=cfg['CFG_SITE_SECURE_URL']
        )
        self.assertStatus(r, 401)

        # # Now logout
        r = self.client.get('/oauth2test/logout')
        self.assertStatus(r, 200)
        assert r.data == "logout"

        # And try to access the information again
        r = self.client.get('/oauth2test/test-ping')
        self.assert403(r)

    def test_implicit_flow(self):
        # First login on provider site
        self.login("tester", "tester")

        for client_id in ['dev', 'confidential']:
            data = dict(
                redirect_uri='%s/oauth2test/authorized' % self.base_url,
                response_type='token',  # For implicit grant type
                client_id=client_id,
                scope='test:scope',
                state='teststate'
            )

            # Authorize page
            r = self.client.get(url_for(
                'oauth2server.authorize',
                **data
            ))
            self.assertStatus(r, 200)

            # User confirms request
            data['confirm'] = 'yes'
            data['scope'] = 'test:scope'
            data['state'] = 'teststate'

            r = self.client.post(url_for('oauth2server.authorize'), data=data)
            self.assertStatus(r, 302)
            # Important - access token exists in URI fragment and must not be
            # sent to the client.
            next_url, data = self.parse_redirect(r.location, parse_fragment=True)

            assert data['access_token']
            assert data['token_type'] == 'Bearer'
            assert data['state'] == 'teststate'
            assert data['scope'] == 'test:scope'
            assert data.get('refresh_token') is None
            assert next_url == '%s/oauth2test/authorized' % self.base_url

            # Authentication flow has now been completed, and the client can
            # use the access token to make request to the provider.
            r = self.client.get(url_for('oauth2server.info',
                                access_token=data['access_token']))
            self.assert200(r)
            assert r.json.get('client') == client_id
            assert r.json.get('user') == self.objects[0].id
            assert r.json.get('scopes') == [u'test:scope']

    def test_client_flow(self):
        data = dict(
            client_id='dev',
            client_secret='dev',  # A public client should NOT do this!
            grant_type='client_credentials',
            scope='test:scope',
        )

        # Public clients are not allowed to use grant_type=client_credentials
        r = self.client.post(url_for(
            'oauth2server.access_token',
            **data
        ))
        self.assertStatus(r, 401)
        self.assertEqual(r.json['error'], 'invalid_client')

        data = dict(
            client_id='confidential',
            client_secret='confidential',
            grant_type='client_credentials',
            scope='test:scope',
        )

        # Retrieve access token using client_crendentials
        r = self.client.post(url_for(
            'oauth2server.access_token',
            **data
        ))
        self.assertStatus(r, 200)
        data = r.json
        assert data['access_token']
        assert data['token_type'] == 'Bearer'
        assert data['scope'] == 'test:scope'
        assert data.get('refresh_token') is None

        # Authentication flow has now been completed, and the client can
        # use the access token to make request to the provider.
        r = self.client.get(url_for('oauth2server.info',
                            access_token=data['access_token']))
        self.assert200(r)
        assert r.json.get('client') == 'confidential'
        assert r.json.get('user') == self.objects[0].id
        assert r.json.get('scopes') == [u'test:scope']

    def test_auth_flow_denied(self):
        # First login on provider site
        self.login("tester", "tester")

        r = self.client.get('/oauth2test/login')
        self.assertStatus(r, 302)
        next_url, data = self.parse_redirect(r.location)

        # Authorize page
        r = self.client.get(next_url, query_string=data)
        self.assertStatus(r, 200)

        # User rejects request
        data['confirm'] = 'no'
        data['scope'] = 'test:scope'
        data['state'] = ''

        r = self.client.post(next_url, data=data)
        self.assertStatus(r, 302)
        next_url, data = self.parse_redirect(r.location)
        assert next_url == '%s/oauth2test/authorized' % self.base_url
        assert data.get('error') == 'access_denied'

        # Returned
        r = self.client.get(next_url, query_string=data)
        self.assert200(r)
        assert r.data == "Access denied: error=access_denied"

    def test_personal_access_token(self):
        r = self.client.get(
            '/oauth/ping',
            query_string="access_token=%s" % self.personal_token.access_token
        )
        self.assert200(r)
        self.assertEqual(r.json, dict(ping='pong'))

        # Access token is not valid for this scope
        r = self.client.get(
            '/oauth/info/',
            query_string="access_token=%s" % self.personal_token.access_token,
            base_url=cfg['CFG_SITE_SECURE_URL']
        )
        self.assertStatus(r, 401)

    def test_resource_auth_methods(self):
        # Query string
        r = self.client.get(
            '/oauth/ping',
            query_string="access_token=%s" % self.personal_token.access_token
        )
        self.assert200(r)
        self.assertEqual(r.json, dict(ping='pong'))

        # POST request body
        r = self.client.post(
            '/oauth/ping',
            data=dict(access_token=self.personal_token.access_token),
        )
        self.assert200(r)
        self.assertEqual(r.json, dict(ping='pong'))

        # Authorization Header
        r = self.client.get(
            '/oauth/ping',
            headers=[
                ("Authorization",
                 "Bearer %s" % self.personal_token.access_token),
            ]
        )
        self.assert200(r)
        self.assertEqual(r.json, dict(ping='pong'))

    def test_settings_index(self):
        # Create a remote account (linked account)
        r = self.client.get(
            url_for('oauth2server_settings.index'),
            base_url=cfg['CFG_SITE_SECURE_URL'],
        )
        self.assertStatus(r, 401)
        self.login("tester", "tester")

        res = self.client.get(
            url_for('oauth2server_settings.index'),
            base_url=cfg['CFG_SITE_SECURE_URL'],
        )
        self.assert200(res)

        res = self.client.get(
            url_for('oauth2server_settings.client_new'),
            base_url=cfg['CFG_SITE_SECURE_URL'],
        )
        self.assert200(res)

        # Valid POST
        res = self.client.post(
            url_for('oauth2server_settings.client_new'),
            base_url=cfg['CFG_SITE_SECURE_URL'],
            data=dict(
                name='Test',
                description='Test description',
                website='http://invenio-software.org',
                is_confidential=1,
                redirect_uris="http://localhost/oauth/authorized/"
            )
        )
        self.assertStatus(res, 302)

        # Invalid redirect_uri (must be https)
        res = self.client.post(
            url_for('oauth2server_settings.client_new'),
            base_url=cfg['CFG_SITE_SECURE_URL'],
            data=dict(
                name='Test',
                description='Test description',
                website='http://invenio-software.org',
                is_confidential=1,
                redirect_uris="http://example.org/oauth/authorized/"
            )
        )
        self.assertStatus(res, 200)

        # Valid
        res = self.client.post(
            url_for('oauth2server_settings.client_new'),
            base_url=cfg['CFG_SITE_SECURE_URL'],
            data=dict(
                name='Test',
                description='Test description',
                website='http://invenio-software.org',
                is_confidential=1,
                redirect_uris="https://example.org/oauth/authorized/\n"
                              "http://localhost:4000/oauth/authorized/"
            )
        )
        self.assertStatus(res, 302)


class OAuth2ProviderExpirationTestCase(ProviderTestCase):

    @property
    def config(self):
        ctx = super(OAuth2ProviderExpirationTestCase, self).config
        ctx.update(
            OAUTH2_PROVIDER_TOKEN_EXPIRES_IN=1,  # make them all expired
        )
        return ctx

    def test_refresh_flow(self):
        # First login on provider site
        self.login("tester", "tester")

        data = dict(
            redirect_uri='%s/oauth2test/authorized' % self.base_url,
            scope='test:scope',
            response_type='code',
            client_id='confidential',
            state='mystate'
        )

        r = self.client.get(url_for('oauth2server.authorize', **data))
        self.assertStatus(r, 200)

        data['confirm'] = 'yes'
        data['scope'] = 'test:scope'
        data['state'] = 'mystate'

        # Obtain one time code
        r = self.client.post(
            url_for('oauth2server.authorize'), data=data
        )
        self.assertStatus(r, 302)
        next_url, res_data = self.parse_redirect(r.location)
        assert res_data['code']
        assert res_data['state'] == 'mystate'

        # Exchange one time code for access token
        r = self.client.post(
            url_for('oauth2server.access_token'), data=dict(
                client_id='confidential',
                client_secret='confidential',
                grant_type='authorization_code',
                code=res_data['code'],
            )
        )
        self.assertStatus(r, 200)
        assert r.json['access_token']
        assert r.json['refresh_token']
        assert r.json['expires_in'] > 0
        assert r.json['scope'] == 'test:scope'
        assert r.json['token_type'] == 'Bearer'
        refresh_token = r.json['refresh_token']
        old_access_token = r.json['access_token']

        # Access token valid
        r = self.client.get(url_for('oauth2server.info',
                            access_token=old_access_token))
        self.assert200(r)

        from ..models import Token
        Token.query.filter_by(access_token=old_access_token).update(
            dict(expires=datetime.utcnow() - timedelta(seconds=1))
        )
        db.session.commit()

        # Access token is expired
        r = self.client.get(url_for('oauth2server.info',
                            access_token=old_access_token),
                            base_url=cfg['CFG_SITE_SECURE_URL'])
        self.assert401(r)

        # Obtain new access token with refresh token
        r = self.client.post(
            url_for('oauth2server.access_token'), data=dict(
                client_id='confidential',
                client_secret='confidential',
                grant_type='refresh_token',
                refresh_token=refresh_token,
            )
        )
        self.assertStatus(r, 200)
        assert r.json['access_token']
        assert r.json['refresh_token']
        assert r.json['expires_in'] > 0
        assert r.json['access_token'] != old_access_token
        assert r.json['refresh_token'] != refresh_token
        assert r.json['scope'] == 'test:scope'
        assert r.json['token_type'] == 'Bearer'

        # New access token valid
        r = self.client.get(url_for('oauth2server.info',
                                    access_token=r.json['access_token']))
        self.assert200(r)

        # Old access token no longer valid
        r = self.client.get(url_for('oauth2server.info',
                                    access_token=old_access_token,),
                            base_url=cfg['CFG_SITE_SECURE_URL'])
        self.assert401(r)

    def test_not_allowed_public_refresh_flow(self):
        # First login on provider site
        self.login("tester", "tester")

        data = dict(
            redirect_uri='%s/oauth2test/authorized' % self.base_url,
            scope='test:scope',
            response_type='code',
            client_id='dev',
            state='mystate'
        )

        r = self.client.get(url_for('oauth2server.authorize', **data))
        self.assertStatus(r, 200)

        data['confirm'] = 'yes'
        data['scope'] = 'test:scope'
        data['state'] = 'mystate'

        # Obtain one time code
        r = self.client.post(
            url_for('oauth2server.authorize'), data=data
        )
        self.assertStatus(r, 302)
        next_url, res_data = self.parse_redirect(r.location)
        assert res_data['code']
        assert res_data['state'] == 'mystate'

        # Exchange one time code for access token
        r = self.client.post(
            url_for('oauth2server.access_token'), data=dict(
                client_id='dev',
                client_secret='dev',
                grant_type='authorization_code',
                code=res_data['code'],
            )
        )
        self.assertStatus(r, 200)
        assert r.json['access_token']
        assert r.json['refresh_token']
        assert r.json['expires_in'] > 0
        assert r.json['scope'] == 'test:scope'
        assert r.json['token_type'] == 'Bearer'
        refresh_token = r.json['refresh_token']
        old_access_token = r.json['access_token']

        # Access token valid
        r = self.client.get(url_for('oauth2server.info',
                            access_token=old_access_token))
        self.assert200(r)

        from ..models import Token
        Token.query.filter_by(access_token=old_access_token).update(
            dict(expires=datetime.utcnow() - timedelta(seconds=1))
        )
        db.session.commit()

        # Access token is expired
        r = self.client.get(url_for('oauth2server.info',
                            access_token=old_access_token),
                            follow_redirects=True)
        self.assert401(r)

        # Obtain new access token with refresh token
        r = self.client.post(
            url_for('oauth2server.access_token'), data=dict(
                client_id='dev',
                client_secret='dev',
                grant_type='refresh_token',
                refresh_token=refresh_token,
            ),
            follow_redirects=True
        )

        # Only confidential clients can refresh expired token.
        self.assert401(r)


class RedisTestCase(ProviderTestCase):
    def create_app(self):
        app = super(ProviderTestCase, self).create_app()
        app.testing = True
        app.config.update(dict(
            OAUTH2_CACHE_TYPE='redis',
            CACHE_REDIS_URL='redis://:mypw@example.org:1234/2',
        ))
        return app

    def test_cache_url(self):
        """Test that CACHE_REDIS_URL is being properly used if set."""
        from flask_oauthlib.contrib.cache import Cache

        connargs = None
        with self.app.test_request_context("/"):
            # Let oauth2server initialize the right configuration variables.
            self.app.try_trigger_before_first_request_functions()
            # Now try to create the cache object and check it's connection
            # properties
            cache = Cache(self.app, 'OAUTH2')
            connargs = cache.cache._client.connection_pool.connection_kwargs

        assert self.app.config.get('OAUTH2_CACHE_REDIS_HOST')
        self.assertEqual(self.app.config.get('OAUTH2_CACHE_TYPE'), 'redis')
        self.assertEqual(connargs['host'], "example.org")
        self.assertEqual(connargs['port'], 1234)
        self.assertEqual(connargs['db'], 2)
        self.assertEqual(connargs['password'], "mypw")


class UtilsTestCase(InvenioTestCase):
    def test_urleencode(self):
        from invenio.modules.oauth2server.views.server import urlreencode

        # Test encoding of unencoded colon which oauthlib will choke on if is
        # not re-encoded,
        testurl = '/test?a=b:d&a=d'

        def test_fun(*args,  **kwargs):
            pass

        with self.app.test_request_context(testurl):
            self.assertEqual(request.url, "http://localhost"+testurl)
            urlreencode(test_fun)()
            self.assertEqual(request.url, "http://localhost/test?a=b%3Ad&a=d")


TEST_SUITE = make_test_suite(OAuth2ProviderTestCase,
                             OAuth2ProviderExpirationTestCase,
                             UtilsTestCase,
                             RedisTestCase)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
