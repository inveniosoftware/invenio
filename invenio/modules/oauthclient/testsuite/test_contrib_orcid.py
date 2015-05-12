# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Test case for ORCID oauth remote app."""

from __future__ import absolute_import

from flask import session, url_for

from flask_email.backends import locmem

import httpretty

from invenio.ext.sqlalchemy import db

from invenio.testsuite import make_test_suite, run_test_suite

from mock import MagicMock

from six.moves.urllib_parse import parse_qs, urlparse

from .helpers import OAuth2ClientTestCase
from ..contrib.orcid import REMOTE_APP, account_info


class OrcidTestCase(OAuth2ClientTestCase):

    """ORCID OAuth remote app test case."""

    example_data = {
        "name": "Josiah Carberry",
        "expires_in": 3599,
        "orcid": "0000-0002-1825-0097",
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "scope": "/authenticate",
        "token_type": "bearer"
    }
    example_email = "orcidtest@invenio-software.org"
    existing_email = "existing@invenio-software.org"

    def create_app(self):
        """Create Flask application object."""
        app = super(OrcidTestCase, self).create_app()
        app.testing = True
        app.config.update(dict(
            WTF_CSRF_ENABLED=False,
            OAUTHCLIENT_STATE_ENABLED=False,
            CACHE_TYPE='simple',
            OAUTHCLIENT_REMOTE_APPS=dict(orcid=REMOTE_APP),
            ORCID_APP_CREDENTIALS=dict(
                consumer_key='changeme',
                consumer_secret='changeme',
            ),
            # use local memory mailbox
            EMAIL_BACKEND='flask_email.backends.locmem.Mail',
        ))
        return app

    def setUp(self):
        """Setup test."""
        from invenio.modules.oauthclient.models import RemoteToken, \
            RemoteAccount
        from invenio.modules.accounts.models import UserEXT, User
        RemoteToken.query.delete()
        RemoteAccount.query.delete()
        UserEXT.query.delete()
        User.query.filter_by(email=self.example_email).delete()

        self.u = User(email=self.existing_email, nickname='tester')
        self.u.password = "tester"
        db.session.add(self.u)
        db.session.commit()

    def tearDown(self):
        """Tear down test."""
        from invenio.modules.oauthclient.models import RemoteToken, \
            RemoteAccount
        from invenio.modules.accounts.models import UserEXT, User
        RemoteToken.query.delete()
        RemoteAccount.query.delete()
        UserEXT.query.delete()
        User.query.filter_by(email=self.example_email).delete()
        User.query.filter_by(email=self.existing_email).delete()
        db.session.commit()
        # empty the mailbox
        if hasattr(locmem, 'outbox'):
            del locmem.outbox[:]

    def mock_response(self, app='test', data=None):
        """Mock the oauth response to use the remote."""
        from invenio.modules.oauthclient.client import oauth

        # Mock oauth remote application
        oauth.remote_apps[app].handle_oauth2_response = MagicMock(
            return_value=data or self.example_data
        )

    def _get_state(self):
        from invenio.modules.oauthclient.views.client import serializer
        return serializer.dumps({'app': 'orcid', 'sid': session.sid,
                                 'next': None, })

    def test_account_info(self):
        """Test account info extraction."""
        from invenio.modules.oauthclient.client import oauth
        # Ensure remote apps have been loaded (due to before first
        # request)
        self.client.get(url_for("oauthclient.login", remote_app='orcid'))

        self.assertEqual(
            account_info(oauth.remote_apps['orcid'], self.example_data),
            dict(external_id="0000-0002-1825-0097",
                 external_method="orcid")
        )
        self.assertEqual(
            account_info(oauth.remote_apps['orcid'], {}),
            dict(external_id=None,
                 external_method="orcid")
        )

    def test_login(self):
        """Test ORCID login."""
        resp = self.client.get(
            url_for("oauthclient.login", remote_app='orcid',
                    next='/someurl/')
        )
        self.assertStatus(resp, 302)

        params = parse_qs(urlparse(resp.location).query)
        self.assertEqual(params['response_type'], ['code'])
        self.assertEqual(params['show_login'], ['true'])
        self.assertEqual(params['scope'], ['/authenticate'])
        assert params['redirect_uri']
        assert params['client_id']
        assert params['state']

    def test_authorized_signup(self):
        """Test authorized callback with sign-up."""
        from invenio.modules.accounts.models import UserEXT, User

        with self.app.test_client() as c:
            from invenio.modules.oauthclient.testsuite.fixture import orcid_bio

            # Ensure remote apps have been loaded (due to before first
            # request)
            c.get(url_for("oauthclient.login", remote_app='orcid'))
            self.mock_response(app='orcid')

            # User authorized the requests and is redirect back
            resp = c.get(
                url_for("oauthclient.authorized",
                        remote_app='orcid', code='test',
                        state=self._get_state()))
            self.assertStatus(resp, 302)
            self.assertRedirects(resp, url_for('oauthclient.signup',
                                               remote_app='orcid'))

            # User load sign-up page.
            resp = c.get(url_for('oauthclient.signup', remote_app='orcid'))
            self.assertStatus(resp, 200)

            # Mock request to ORCID to get user bio.
            httpretty.enable()
            httpretty.register_uri(
                httpretty.GET,
                "http://orcid.org/{0}/orcid-bio".format(
                    self.example_data['orcid']),
                body=orcid_bio,
                content_type="application/orcid+json; qs=2;charset=UTF-8",
            )

            # User fills in email address.
            resp = c.post(url_for('oauthclient.signup', remote_app='orcid'),
                          data=dict(email=self.example_email))
            self.assertStatus(resp, 302)
            httpretty.disable()

            # Assert database state (Sign-up complete)
            u = User.query.filter_by(email=self.example_email).one()
            UserEXT.query.filter_by(
                method='orcid', id_user=u.id,
                id=self.example_data['orcid']
            ).one()
            self.assertEqual(u.given_names, "Josiah")
            self.assertEqual(u.family_name, "Carberry")
            # check that the user's email is not yet validated
            self.assertEqual(u.note, '2',
                             'email address should not be validated')
            # check that the validation email has been sent
            self.assertTrue(hasattr(locmem, 'outbox') and
                            len(locmem.outbox) == 1,
                            'validation email not sent')

            # Disconnect link
            resp = c.get(
                url_for("oauthclient.disconnect", remote_app='orcid'))
            self.assertStatus(resp, 302)

            # User exists
            u = User.query.filter_by(email=self.example_email).one()
            # UserEXT removed.
            assert 0 == UserEXT.query.filter_by(
                method='orcid', id_user=u.id,
                id=self.example_data['orcid']
            ).count()

    def test_authorized_reject(self):
        """Test a rejected request."""
        with self.app.test_client() as c:
            c.get(url_for("oauthclient.login", remote_app='orcid'))
            resp = c.get(
                url_for("oauthclient.authorized",
                        remote_app='orcid', error='access_denied',
                        error_description='User denied access',
                        state=self._get_state()))
            self.assertRedirects(resp, "/")
            # Check message flash
            self.assertEqual(session['_flashes'][0][0], 'info')

    def test_authorized_already_authenticated(self):
        """Test authorized callback with sign-up."""
        from invenio.modules.accounts.models import UserEXT, User
        from invenio.modules.oauthclient.testsuite.fixture import orcid_bio

        # User logins
        self.login("tester", "tester")

        # Mock access token request
        self.mock_response(app='orcid')

        # Mock request to ORCID to get user bio.
        httpretty.enable()
        httpretty.register_uri(
            httpretty.GET,
            "https://pub.orcid.org/v1.2/{0}/orcid-bio".format(
                self.example_data['orcid']),
            body=orcid_bio,
            content_type="application/orcid+json; qs=2;charset=UTF-8",
        )

        # User then goes to "Linked accounts" and clicks "Connect"
        resp = self.client.get(
            url_for("oauthclient.login", remote_app='orcid',
                    next='/someurl/')
        )
        self.assertStatus(resp, 302)

        # User authorized the requests and is redirected back
        resp = self.client.get(
            url_for("oauthclient.authorized",
                    remote_app='orcid', code='test',
                    state=self._get_state()))
        httpretty.disable()

        # Assert database state (Sign-up complete)
        u = User.query.filter_by(email=self.existing_email).one()
        UserEXT.query.filter_by(
            method='orcid', id_user=u.id,
            id=self.example_data['orcid']
        ).one()
        self.assertEqual(u.given_names, "Josiah")
        self.assertEqual(u.family_name, "Carberry")

        # Disconnect link
        resp = self.client.get(
            url_for("oauthclient.disconnect", remote_app='orcid'))
        self.assertStatus(resp, 302)

        # User exists
        u = User.query.filter_by(email=self.existing_email).one()
        # UserEXT removed.
        assert 0 == UserEXT.query.filter_by(
            method='orcid', id_user=u.id,
            id=self.example_data['orcid']
        ).count()

TEST_SUITE = make_test_suite(OrcidTestCase)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
