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

from flask import url_for, request
from flask.ext.restful import Resource

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite
from invenio.ext.restful import require_api_auth, require_oauth_scopes, \
    require_header
from invenio.ext.sqlalchemy import db


class DecoratorsTestCase(InvenioTestCase):
    def setUp(self):
        from invenio.modules.accounts.models import User
        from invenio.modules.oauth2server.registry import scopes
        from invenio.modules.oauth2server.models import Token, Scope

        # Setup variables:
        self.called = dict()

        # Setup test scopes
        with self.app.app_context():
            scopes.register(Scope(
                'test:testscope',
                group='Test',
                help_text='Test scope',
            ))

        # Setup API resources
        class Test1Resource(Resource):
            # NOTE: Method decorators are applied in reverse order
            method_decorators = [
                require_oauth_scopes('test:testscope'),
                require_api_auth(),
            ]

            def get(self):
                assert request.oauth.access_token
                return "success", 200

            def post(self):
                assert request.oauth.access_token
                return "success", 200

            @require_header('Content-Type', 'application/json')
            def put(self):
                return "success", 200

        class Test2Resource(Resource):
            @require_api_auth()
            @require_oauth_scopes('test:testscope')
            def get(self):
                assert request.oauth.access_token
                return "success", 200

            @require_api_auth()
            @require_oauth_scopes('test:testscope')
            def post(self):
                assert request.oauth.access_token
                return "success", 200

            @require_header('Content-Type', 'text/html')
            def put(self):
                return "success", 200

        # Register API resources
        api = self.app.extensions['restful']
        api.add_resource(
            Test1Resource,
            '/api/test1/decoratorstestcase/'
        )
        api.add_resource(
            Test2Resource,
            '/api/test2/decoratorstestcase/'
        )

        # Create a user
        self.user = User(
            email='info@invenio-software.org', nickname='tester'
        )
        self.user.password = "tester"
        db.session.add(self.user)
        db.session.commit()

        # Create tokens
        self.token = Token.create_personal(
            'test-', self.user.id, scopes=['test:testscope'], is_internal=True)
        self.token_noscope = Token.create_personal(
            'test-', self.user.id, scopes=[], is_internal=True)

    def tearDown(self):
        db.session.delete(self.user)
        db.session.delete(self.token.client)
        db.session.delete(self.token)
        db.session.delete(self.token_noscope.client)
        db.session.delete(self.token_noscope)
        db.session.commit()

    def test_require_api_auth_test1(self):
        res = self.client.get(url_for('test1resource'))
        self.assert401(res)
        res = self.client.get(
            url_for('test1resource', access_token=self.token.access_token))
        self.assert200(res)

    def test_require_api_auth_test2(self):
        res = self.client.get(url_for('test2resource'))
        self.assert401(res)
        res = self.client.get(
            url_for('test2resource', access_token=self.token.access_token))
        self.assert200(res)

    def test_require_oauth_scopes_test1(self):
        res = self.client.post(
            url_for('test1resource', access_token=self.token.access_token))
        self.assert200(res)
        res = self.client.post(
            url_for('test1resource',
                    access_token=self.token_noscope.access_token))
        self.assertStatus(res, 403)

    def test_require_oauth_scopes_test2(self):
        res = self.client.post(
            url_for('test2resource', access_token=self.token.access_token))
        self.assert200(res)
        res = self.client.post(
            url_for('test2resource',
                    access_token=self.token_noscope.access_token))
        self.assertStatus(res, 403)

    def test_require_header_test1(self):
        res = self.client.put(
            url_for('test1resource', access_token=self.token.access_token),
            headers=[('Content-Type', 'application/json')])
        self.assert200(res)
        res = self.client.put(
            url_for('test1resource', access_token=self.token.access_token),
            headers=[('Content-Type', 'text/html')])
        self.assertStatus(res, 415)

    def test_require_header_test2(self):
        res = self.client.put(
            url_for('test2resource'),
            headers=[('Content-Type', 'text/html; charset=UTF-8')])
        self.assert200(res)
        res = self.client.put(
            url_for('test2resource'),
            headers=[('Content-Type', 'application/json')])
        self.assertStatus(res, 415)


TEST_SUITE = make_test_suite(DecoratorsTestCase)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
