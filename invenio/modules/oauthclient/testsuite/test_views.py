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

from __future__ import absolute_import

import time
from flask import url_for, session
from invenio.base.globals import cfg
from invenio.ext.sqlalchemy import db
from invenio.testsuite import make_test_suite, run_test_suite
from itsdangerous import TimedJSONWebSignatureSerializer
from mock import MagicMock, patch
from six.moves.urllib_parse import parse_qs, urlparse
from .helpers import OAuth2ClientTestCase


class RemoteAccountTestCase(OAuth2ClientTestCase):
    def setUp(self):
        params = lambda x: dict(
            request_token_params={'scope': ''},
            base_url='https://foo.bar/',
            request_token_url=None,
            access_token_url="https://foo.bar/oauth/access_token",
            authorize_url="https://foo.bar/oauth/authorize",
            consumer_key=x,
            consumer_secret='testsecret',
        )

        self.app.config['OAUTHCLIENT_REMOTE_APPS'] = dict(
            test=dict(
                authorized_handler=self.handler,
                params=params('testid'),
                title='MyLinkedTestAccount',
            ),
            test_invalid=dict(
                authorized_handler=self.handler_invalid,
                params=params('test_invalidid'),
                title='Test Invalid',
            ),
            full=dict(
                params=params("fullid"),
                title='Full',
            ),
        )
        self.handled_resp = None
        self.handled_remote = None
        self.handled_args = None
        self.handled_kwargs = None

        from invenio.modules.oauthclient.models import RemoteToken, \
            RemoteAccount
        RemoteToken.query.delete()
        RemoteAccount.query.delete()
        db.session.commit()

    def tearDown(self):
        self.handled_resp = None
        self.handled_remote = None
        self.handled_args = None
        self.handled_kwargs = None

        from invenio.modules.oauthclient.models import RemoteToken, \
            RemoteAccount
        RemoteToken.query.delete()
        RemoteAccount.query.delete()
        db.session.commit()

    def handler(self, resp, remote, *args, **kwargs):
        self.handled_resp = resp
        self.handled_remote = remote
        self.handled_args = args
        self.handled_kwargs = kwargs
        return "TEST"

    def handler_invalid(self):
        self.handled_resp = 1
        self.handled_remote = 1
        self.handled_args = 1
        self.handled_kwargs = 1

    def mock_response(self, app='test', data=None):
        """ Mock the oauth response to use the remote """
        from invenio.modules.oauthclient.client import oauth

        # Mock oauth remote application
        oauth.remote_apps[app].handle_oauth2_response = MagicMock(
            return_value=data or {
                "access_token": "test_access_token",
                "scope": "",
                "token_type": "bearer"
            }
        )

    def test_redirect_uri(self):
        from invenio.modules.oauthclient.views.client import serializer

        # Test redirect
        resp = self.client.get(
            url_for("oauthclient.login", remote_app='test',
                    next='http://invenio-software.org')
        )
        self.assertStatus(resp, 302)

        # Verify parameters
        params = parse_qs(urlparse(resp.location).query)
        self.assertEqual(params['response_type'], ['code'])
        self.assertEqual(params['client_id'], ['testid'])
        assert params['redirect_uri']
        assert params['state']

        # Verify next parameter in state token does not allow blanco redirects
        state = serializer.loads(params['state'][0])
        self.assertIsNone(state['next'])

        # Assert redirect uri does not have any parameters.
        params = parse_qs(urlparse(params['redirect_uri'][0]).query)
        self.assertEqual(params, {})

        # Assert that local redirects are allowed
        test_urls = [
            '/search',
            url_for('oauthclient.disconnect', remote_app='test',
                    _external=True)
        ]
        for url in test_urls:
            resp = self.client.get(
                url_for("oauthclient.login", remote_app='test', next=url)
            )
            self.assertStatus(resp, 302)
            state = serializer.loads(
                parse_qs(urlparse(resp.location).query)['state'][0]
            )
            self.assertEqual(url, state['next'])

    def test_login(self):
        # Test redirect
        resp = self.client.get(
            url_for("oauthclient.login", remote_app='test', next='/')
        )
        self.assertStatus(resp, 302)

        params = parse_qs(urlparse(resp.location).query)
        self.assertEqual(params['response_type'], ['code'])
        self.assertEqual(params['client_id'], ['testid'])
        assert params['redirect_uri']
        assert params['state']

        # Invalid remote
        resp = self.client.get(
            url_for("oauthclient.login", remote_app='invalid')
        )
        self.assertStatus(resp, 404)

    def test_authorized(self):
        # Fake an authorized request
        with self.app.test_client() as c:
            # Ensure remote apps have been loaded (due to before first
            # request)
            c.get(url_for("oauthclient.login", remote_app='test'))
            self.mock_response(app='test')
            self.mock_response(app='test_invalid')

            from invenio.modules.oauthclient.views.client import serializer

            state = serializer.dumps({
                'app': 'test',
                'sid': session.sid,
                'next': None,
            })

            resp = c.get(
                url_for(
                    "oauthclient.authorized",
                    remote_app='test',
                    code='test',
                    state=state
                )
            )
            assert resp.data == "TEST"
            assert self.handled_remote.name == 'test'
            assert not self.handled_args
            assert not self.handled_kwargs
            assert self.handled_resp['access_token'] == 'test_access_token'

            state = serializer.dumps({
                'app': 'test_invalid',
                'sid': session.sid,
                'next': None,
            })

            self.assertRaises(
                TypeError,
                c.get,
                url_for(
                    "oauthclient.authorized",
                    remote_app='test_invalid',
                    code='test',
                    state=state,
                )
            )

    def test_invalid_authorized_response(self):
        from simplejson import JSONDecodeError
        from invenio.modules.oauthclient.client import oauth

        # Fake an authorized request
        with self.app.test_client() as c:
            # Ensure remote apps have been loaded (due to before first
            # request)
            c.get(url_for("oauthclient.login", remote_app='test'))

            oauth.remote_apps['test'].handle_oauth2_response = MagicMock(
                side_effect=JSONDecodeError('Expecting value', '', 0)
            )

            from invenio.modules.oauthclient.views.client import serializer

            state = serializer.dumps({
                'app': 'test',
                'sid': session.sid,
                'next': None,
            })

            self.assertRaises(
                JSONDecodeError,
                c.get,
                url_for(
                    "oauthclient.authorized",
                    remote_app='test',
                    code='test',
                    state=state
                )
            )


    @patch('invenio.modules.oauthclient.views.client.session')
    def test_state_token(self, session):
        from invenio.modules.oauthclient.views.client import serializer

        # Mock session id
        session.sid = '1234'

        with self.app.test_client() as c:
            # Ensure remote apps have been loaded (due to before first
            # request)
            c.get(url_for("oauthclient.login", remote_app='test'))
            self.mock_response(app='test')

            # Good state token
            state = serializer.dumps(
                {'app': 'test', 'sid': '1234',  'next': None, }
            )
            resp = c.get(
                url_for("oauthclient.authorized", remote_app='test',
                        code='test', state=state)
            )
            self.assert200(resp)

            outdated_serializer = TimedJSONWebSignatureSerializer(
                cfg['SECRET_KEY'],
                expires_in=0,
            )

            # Bad state - timeout
            state1 = outdated_serializer.dumps(
                {'app': 'test', 'sid': '1234',  'next': None, }
            )
            # Bad state - app
            state2 = serializer.dumps(
                # State for another existing app (test_invalid exists)
                {'app': 'test_invalid', 'sid': '1234',  'next': None, }
            )
            # Bad state - sid
            state3 = serializer.dumps(
                # State for another existing app (test_invalid exists)
                {'app': 'test', 'sid': 'bad',  'next': None, }
            )
            time.sleep(1)
            for s in [state1, state2, state3]:
                resp = c.get(
                    url_for("oauthclient.authorized", remote_app='test',
                            code='test', state=s)
                )
                self.assert403(resp)

    def test_no_remote_app(self):
        self.assert404(self.client.get(
            url_for("oauthclient.authorized", remote_app='invalid')
        ))

        self.assert404(self.client.get(
            url_for("oauthclient.disconnect", remote_app='invalid')
        ))

    @patch('invenio.ext.session.interface.SessionInterface.save_session')
    @patch('invenio.modules.oauthclient.views.client.session')
    def test_token_getter_setter(self, session, save_session):
        from invenio.modules.oauthclient.models import RemoteToken
        from invenio.modules.oauthclient.handlers import token_getter
        from invenio.modules.oauthclient.client import oauth

        # Mock user
        user = MagicMock()
        user.get_id = MagicMock(return_value=1)
        user.is_authenticated = MagicMock(return_value=True)

        # Mock session id
        session.sid = '1234'

        with patch('flask_login._get_user', return_value=user):
            with self.app.test_client() as c:
                # First call login to be redirected
                res = c.get(url_for("oauthclient.login", remote_app='full'))
                assert res.status_code == 302
                assert res.location.startswith(
                    oauth.remote_apps['full'].authorize_url
                )
                state = parse_qs(urlparse(res.location).query)['state'][0]

                # Mock resposen class
                self.mock_response(app='full')

                # Imitate that the user authorized our request in the remote
                # application.
                c.get(url_for(
                    "oauthclient.authorized", remote_app='full', code='test',
                    state=state,
                ))

                # Assert if everything is as it should be.
                from flask import session as flask_session
                assert flask_session['oauth_token_full'] == \
                    ('test_access_token', '')

                t = RemoteToken.get(1, "fullid")
                assert t.remote_account.client_id == 'fullid'
                assert t.access_token == 'test_access_token'
                assert RemoteToken.query.count() == 1

                # Mock a new authorized request
                self.mock_response(app='full', data={
                    "access_token": "new_access_token",
                    "scope": "",
                    "token_type": "bearer"
                })

                c.get(url_for(
                    "oauthclient.authorized", remote_app='full', code='test',
                    state=state
                ))

                t = RemoteToken.get(1, "fullid")
                assert t.access_token == 'new_access_token'
                assert RemoteToken.query.count() == 1

                val = token_getter(oauth.remote_apps['full'])
                assert val == ('new_access_token', '')

                # Disconnect account
                res = c.get(url_for(
                    "oauthclient.disconnect", remote_app='full',
                ))
                assert res.status_code == 302
                assert res.location.endswith(
                    url_for('oauthclient_settings.index')
                )
                # Assert that remote account have been removed.
                t = RemoteToken.get(1, "fullid")
                assert t is None

    @patch('invenio.ext.session.interface.SessionInterface.save_session')
    @patch('invenio.modules.oauthclient.views.client.session')
    def test_rejected(self, session, save_session):
        from invenio.modules.oauthclient.client import oauth

        # Mock user id
        user = MagicMock()
        user.get_id = MagicMock(return_value=1)
        user.is_authenticated = MagicMock(return_value=True)

        # Mock session id
        session.sid = '1234'

        with patch('flask_login._get_user', return_value=user):
            with self.app.test_client() as c:
                # First call login to be redirected
                res = c.get(url_for("oauthclient.login", remote_app='full'))
                assert res.status_code == 302
                assert res.location.startswith(
                    oauth.remote_apps['full'].authorize_url
                )

                # Mock response to imitate an invalid response. Here, an
                # example from GitHub when the code is expired.
                self.mock_response(app='full', data=dict(
                    error_uri='http://developer.github.com/v3/oauth/'
                              '#bad-verification-code',
                    error_description='The code passed is '
                                      'incorrect or expired.',
                    error='bad_verification_code',
                ))

                # Imitate that the user authorized our request in the remote
                # application (however, the remote app will son reply with an
                # error)
                from invenio.modules.oauthclient.views.client import serializer
                state = serializer.dumps({
                    'app': 'full', 'sid': '1234',  'next': None,
                })

                res = c.get(url_for(
                    "oauthclient.authorized", remote_app='full', code='test',
                    state=state
                ))
                assert res.status_code == 302

    def test_settings_view(self):
        # Create a remove account (linked account)
        from invenio.modules.oauthclient.models import RemoteAccount
        RemoteAccount.create(1, 'testid', None)

        self.assert401(self.client.get(url_for('oauthclient_settings.index'),
                                       follow_redirects=True))
        self.login("admin", "")

        res = self.client.get(url_for('oauthclient_settings.index'))
        self.assert200(res)
        assert 'MyLinkedTestAccount' in res.data
        assert url_for('oauthclient.disconnect', remote_app='test') in res.data
        assert url_for('oauthclient.login', remote_app='full') in res.data
        assert url_for('oauthclient.login', remote_app='test_invalid') in \
            res.data


TEST_SUITE = make_test_suite(RemoteAccountTestCase)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
