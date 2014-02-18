# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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

"""
    invenio.ext.restapi
    -------------------

    This module provides initialization and configuration for `flask-restful`
    module.
"""

import six
import warnings

from datetime import date
from dateutil import parser
from dateutil.tz import tzlocal, tzutc
from flask import request, session
from flask.ext import restful
from flask.ext.restful import fields
from flask.ext.registry import ModuleAutoDiscoveryRegistry
from functools import wraps

error_codes = dict(
    validation_error=10,
)
"""
Available error codes for REST API.
"""


#
# Marshal fields
#
class ISODate(fields.Raw):
    """
    Format a datetime object in ISO format
    """
    def format(self, dt):
        try:
            if isinstance(dt, date):
                return six.text_type(dt.isoformat())
            else:
                return six.text_type(dt)
        except AttributeError as ae:
            raise fields.MarshallingException(ae)


class UTCISODateTime(fields.DateTime):
    """
    Format a datetime object in ISO format and convert to UTC if necessary
    """
    def format(self, dt):
        try:
            if not dt.tzinfo:
                dt = dt.replace(tzinfo=tzlocal())
            return six.text_type(dt.astimezone(tzutc()).isoformat())
        except AttributeError as ae:
            raise fields.MarshallingException(ae)


class UTCISODateTimeString(fields.DateTime):
    """
    Format a string which represents a datetime in ISO format and convert to
    UTC if necessary.
    """
    def format(self, value):
        try:
            dt = parser.parse(value)
            if not dt.tzinfo:
                dt = dt.replace(tzinfo=tzlocal())
            return six.text_type(dt.astimezone(tzutc()).isoformat())
        except AttributeError as ae:
            raise fields.MarshallingException(ae)


#
# Decorators
#
def require_api_auth(*scopes):
    """
    Decorator to require API authentication using either API key or OAuth 2.0

    Note, API key usage will be deprecated. Personal OAuth access tokens
    provide the same features as API keys.

    :param scopes: List of required OAuth scopes.
    """
    def wrapper(f):
        # Wrap function with oauth require decorator
        from flask_oauthlib.utils import extract_params
        from invenio.modules.oauth2server.provider import oauth2

        @wraps(f)
        def decorated(*args, **kwargs):
            if 'apikey' in request.values:
                # API key authentication
                warnings.warn(
                    "API keys will be superseded by OAuth personal access "
                    "tokens",
                    PendingDeprecationWarning
                )

                from invenio.modules.apikeys.models import WebAPIKey
                from invenio.ext.login import login_user

                user_id = WebAPIKey.acc_get_uid_from_request()
                if user_id == -1:
                    restful.abort(401)

                login_user(user_id)
                resp = f(None, *args, **kwargs)
                session.clear()
                return resp
            else:
                # OAuth 2.0 Authentication
                for func in oauth2._before_request_funcs:
                    func()

                server = oauth2.server
                uri, http_method, body, headers = extract_params()
                valid, req = server.verify_request(
                    uri, http_method, body, headers, scopes
                )

                for func in oauth2._after_request_funcs:
                    valid, req = func(valid, req)

                if not valid:
                    return restful.abort(
                        401,
                        message="Unauthorized",
                        status=401,
                    )

                resp = f(req, *args, **kwargs)
                session.clear()
                return resp
            restful.abort(401)
        return decorated
    return wrapper


def require_oauth_scopes(*scopes):
    """
    Decorator to require a list of OAuth scopes. Note, if API key
    authentication is bypassing this check.
    """
    required_scopes = set(scopes)

    def wrapper(f):
        @wraps(f)
        def decorated(class_, oauth, *args, **kwargs):
            # Variable oauth is only defined for oauth requests (see
            # require_api_auth() above).
            if oauth is not None:
                token_scopes = set(oauth.access_token.scopes)
                if not required_scopes.issubset(token_scopes):
                    restful.abort(403)
            return f(class_, oauth, *args, **kwargs)
        return decorated
    return wrapper


def require_header(header, value):
    """
    Decorator to test if proper content-type is provided.
    """
    def decorator(f):
        @wraps(f)
        def inner(*args, **kwargs):
            if header == 'Content-Type':
                test_value = request.headers.get(header, '').split(';')[0]
            else:
                test_value = request.headers.get(header, '')

            if test_value != value:
                restful.abort(
                    415,
                    message="Expected %s: %s" % (header, value),
                    status=415,
                )
            return f(*args, **kwargs)
        return inner
    return decorator


def setup_app(app):
    """Setup api extension."""
    api = restful.Api(app=app)
    app.extensions['restful'] = api

    class RestfulRegistry(ModuleAutoDiscoveryRegistry):
        setup_func_name = 'setup_app'

        def register(self, module, *args, **kwargs):
            return super(RestfulRegistry, self).register(module, app, api,
                                                         *args, **kwargs)

    app.extensions['registry']['restful'] = RestfulRegistry(
        'restful', app=app, with_setup=True
    )
