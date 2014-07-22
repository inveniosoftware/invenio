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

from __future__ import absolute_import, print_function

import os
import logging

from flask import url_for

from invenio.testsuite import FlaskSQLAlchemyTest
from invenio.ext.sqlalchemy import db
from mock import MagicMock
from flask_oauthlib.client import prepare_request
try:
    from six.moves.urllib.parse import urlparse
except ImportError:
    from urllib.parse import urlparse

from .helpers import create_client

logging.basicConfig(level=logging.DEBUG)


class OAuth2ProviderTestCase(FlaskSQLAlchemyTest):
    def create_app(self):
        try:
            app = super(OAuth2ProviderTestCase, self).create_app()
            app.debug = True
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
                uri, headers=headers, data=data, method=method
            )
            # for compatible
            resp.code = resp.status_code
            return resp, resp.data
        return make_request

    def setUp(self):
        super(OAuth2ProviderTestCase, self).setUp()
        # Set environment variable DEBUG to true, to allow testing without
        # SSL in oauthlib.
        if self.app.config.get('CFG_SITE_SECURE_URL').startswith('http://'):
            self.os_debug = os.environ.get('DEBUG', '')
            os.environ['DEBUG'] = 'true'

        from ..models import Client
        from invenio.modules.accounts.models import User

        self.base_url = self.app.config.get('CFG_SITE_SECURE_URL')

        # Create needed objects
        u = User(
            id=1, email='info@invenio-software.org', nickname='tester'
        )
        u.password = "tester"

        u2 = User(
            id=2, email='abuse@invenio-software.org', nickname='tester2'
        )
        u2.password = "tester2"

        c1 = Client(
            client_id='dev',
            client_secret='dev',
            name='dev',
            description='',
            is_confidential=False,
            user_id=u.id,
            _redirect_uris='%s/oauth2test/authorized' % self.base_url,
            _default_scopes="user"
        )

        c2 = Client(
            client_id='confidential',
            client_secret='confidential',
            name='confidential',
            description='',
            is_confidential=True,
            user_id=u.id,
            _redirect_uris='%s/oauth2test/authorized' % self.base_url,
            _default_scopes="user"
        )

        try:
            db.session.add(u)
            db.session.add(u2)
            db.session.add(c1)
            db.session.add(c2)
            db.session.commit()
        except:
            db.session.rollback()

        # Create a personal access token as well.
        from ..models import Token
        self.personal_token = Token.create_personal(
            'test-personal', 1, scopes=[], is_internal=True
        )

    def tearDown(self):
        super(OAuth2ProviderTestCase, self).tearDown()
        # Set back any previous value of DEBUG environment variable.
        if self.app.config.get('CFG_SITE_SECURE_URL').startswith('http://'):
            os.environ['DEBUG'] = self.os_debug
        self.base_url = None

    def parse_redirect(self, location):
        from werkzeug.urls import url_parse, url_decode, url_unparse
        scheme, netloc, script_root, qs, anchor = url_parse(location)
        return (
            url_unparse((scheme, netloc, script_root, '', '')),
            url_decode(qs)
        )

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

    def test_auth_flow(self):
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
        data['scope'] = 'user'
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
        assert r.json.get('client') == 'dev'
        assert r.json.get('user') == 1
        assert r.json.get('scopes') == [u'user']

        # Access token doesn't provide access to this URL.
        r = self.client.get('/oauth2test/test-invalid')
        self.assertStatus(r, 403)

        # # Now logout
        r = self.client.get('/oauth2test/logout')
        self.assertStatus(r, 200)
        assert r.data == "logout"

        # And try to access the information again
        r = self.client.get('/oauth2test/test-ping')
        self.assert403(r)

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
        data['scope'] = 'user'
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

        # Access token is not valid for this scope.
        r = self.client.get('/oauth/info')
        self.assertStatus(r, 403)

    def test_settings_index(self):
        # Create a remove account (linked account)
        self.assert401(self.client.get(url_for('oauth2server_settings.index')))
        self.login("tester", "tester")

        res = self.client.get(url_for('oauth2server_settings.index'))
        self.assert200(res)

        res = self.client.get(url_for('oauth2server_settings.client_new'))
        self.assert200(res)

        res = self.client.post(
            url_for('oauth2server_settings.client_new'),
            data=dict(
                name='Test',
                description='Test description',
                website='http://invenio-software.org',
            )
        )
        assert res.status_code == 302
