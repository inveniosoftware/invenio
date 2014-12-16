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

from __future__ import absolute_import

from mock import MagicMock, patch
from six.moves.urllib_parse import quote_plus
from flask import url_for, session
from invenio.testsuite import make_test_suite, run_test_suite
from invenio.ext.sqlalchemy import db

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

    def test_login(self):
        # Test redirect
        resp = self.client.get(url_for("oauthclient.login", remote_app='test'))
        self.assertStatus(resp, 302)
        self.assertEqual(
            resp.location,
            "https://foo.bar/oauth/authorize?response_type=code&"
            "client_id=testid&redirect_uri=%s" % quote_plus(url_for(
                "oauthclient.authorized", remote_app='test', _external=True
            ))
        )

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

            resp = c.get(
                url_for(
                    "oauthclient.authorized",
                    remote_app='test',
                    code='test',
                )
            )
            assert resp.data == "TEST"
            assert self.handled_remote.name == 'test'
            assert not self.handled_args
            assert not self.handled_kwargs
            assert self.handled_resp['access_token'] == 'test_access_token'

            resp = self.assertRaises(
                TypeError,
                c.get,
                url_for(
                    "oauthclient.authorized",
                    remote_app='test_invalid',
                    code='test',
                )
            )

    def test_no_remote_app(self):
        self.assert404(self.client.get(
            url_for("oauthclient.authorized", remote_app='invalid')
        ))

        self.assert404(self.client.get(
            url_for("oauthclient.disconnect", remote_app='invalid')
        ))

    @patch('invenio.ext.session.interface.SessionInterface.save_session')
    def test_token_getter_setter(self, save_session):
        from invenio.modules.oauthclient.models import RemoteToken
        from invenio.modules.oauthclient.handlers import token_getter
        from invenio.modules.oauthclient.client import oauth

        user = MagicMock()
        user.get_id = MagicMock(return_value=1)
        user.is_authenticated = MagicMock(return_value=True)
        with patch('flask.ext.login._get_user', return_value=user):
            with self.app.test_client() as c:
                # First call login to be redirected
                res = c.get(url_for("oauthclient.login", remote_app='full'))
                assert res.status_code == 302
                assert res.location.startswith(
                    oauth.remote_apps['full'].authorize_url
                )
                # Mock resposen class
                self.mock_response(app='full')

                # Imitate that the user authorized our request in the remote
                # application.
                c.get(url_for(
                    "oauthclient.authorized", remote_app='full', code='test',
                ))

                # Assert if every is as it should be.
                assert session['oauth_token_full'] == ('test_access_token', '')

                t = RemoteToken.get(1, "fullid")
                assert t.remote_account.client_id == 'fullid'
                assert t.access_token == 'test_access_token'
                assert RemoteToken.query.count() == 1

                self.mock_response(app='full', data={
                    "access_token": "new_access_token",
                    "scope": "",
                    "token_type": "bearer"
                })

                c.get(url_for(
                    "oauthclient.authorized", remote_app='full', code='test',
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
    def test_rejected(self, save_session):
        from invenio.modules.oauthclient.client import oauth

        user = MagicMock()
        user.get_id = MagicMock(return_value=1)
        user.is_authenticated = MagicMock(return_value=True)
        with patch('flask.ext.login._get_user', return_value=user):
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
                res = c.get(url_for(
                    "oauthclient.authorized", remote_app='full', code='test',
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
