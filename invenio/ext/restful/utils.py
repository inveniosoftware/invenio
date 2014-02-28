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

import json
from flask import url_for
from invenio.testsuite import InvenioTestCase
from invenio.ext.sqlalchemy import db


class APITestCase(InvenioTestCase):
    """
    API unit test base class
    """
    apikey = None
    accesstoken = None

    def create_api_key(self, user_id):
        from invenio.modules.apikeys import create_new_web_api_key, \
            get_available_web_api_keys

        create_new_web_api_key(
            user_id,
            key_description='test key for user id %s' % user_id
        )
        keys = get_available_web_api_keys(self.userid)
        self.apikey = keys[0].id

    def create_oauth_token(self, user_id, scopes, is_internal=True):
        """
        Create an OAuth personal access_token
        """
        # Create a personal access token as well.
        from invenio.modules.oauth2server.models import Token
        self.accesstoken = Token.create_personal(
            'test-personal-%s' % user_id,
            user_id,
            scopes=scopes,
            is_internal=is_internal
        ).access_token

    def remove_oauth_token(self):
        if self.accesstoken:
            from invenio.modules.oauth2server.models import Token
            t = Token.query.filter_by(access_token=self.accesstoken).first()
            if t:
                db.session.delete(t)
                db.session.commit()

    def remove_api_key(self):
        if self.apikey:
            from invenio.modules.apikeys.models import WebAPIKey
            k = WebAPIKey.filter_by(id=self.apikey).first()
            if k:
                db.session.delete(k)
                db.session.commit()

    def get(self, *args, **kwargs):
        """ See ``APITestCase.make_request()'' """
        return self.make_request(self.client.get, *args, **kwargs)

    def head(self, *args, **kwargs):
        """ See ``APITestCase.make_request()'' """
        return self.make_request(self.client.head, *args, **kwargs)

    def patch(self, *args, **kwargs):
        """ See ``APITestCase.make_request()'' """
        return self.make_request(self.client.patch, *args, **kwargs)

    def options(self, *args, **kwargs):
        """ See ``APITestCase.make_request()'' """
        return self.make_request(self.client.options, *args, **kwargs)

    def post(self, *args, **kwargs):
        """ See ``APITestCase.make_request()'' """
        return self.make_request(self.client.post, *args, **kwargs)

    def put(self, *args, **kwargs):
        """ See ``APITestCase.make_request()'' """
        return self.make_request(self.client.put, *args, **kwargs)

    def delete(self, *args, **kwargs):
        """ See ``APITestCase.make_request()'' """
        return self.make_request(self.client.delete, *args, **kwargs)

    def make_request(self, client_func, endpoint, urlargs={}, data=None,
                     is_json=True, code=None, headers=None,
                     follow_redirects=False):
        """
        Make a request to the API endpoint.

        Ensures request looks like they arrive on CFG_SITE_SECURE_URL.

        Athat header "Contet-Type: application/json" is added if


        :param endpoint: Endpoint passed to url_for.
        :param urlargs: Keyword args passed to url_for
        :param data: Request body, either as a dictionary if ``is_json`` is
            True, or as a string if ``is_json`` is False
        :param headers: List of headers for the request
        :param code: Assert response status code
        :param follow_redirects: Whether to follow redirects.
        """
        if headers is None:
            headers = [('content-type', 'application/json')] if is_json else []

        if data is not None:
            request_args = dict(
                data=json.dumps(data) if is_json else data,
                headers=headers,
            )
        else:
            request_args = {}

        if self.apikey:
            urlargs['apikey'] = self.apikey,
        elif self.accesstoken:
            urlargs['access_token'] = self.accesstoken

        url = url_for(endpoint, **urlargs)
        response = client_func(
            url,
            base_url=self.app.config['CFG_SITE_SECURE_URL'],
            follow_redirects=follow_redirects,
            **request_args
        )
        if code is not None:
            self.assertStatus(response, code)
        return response
