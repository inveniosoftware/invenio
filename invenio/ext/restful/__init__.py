# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Initialization and configuration for *Flask-Restful*."""

import re
import six
import warnings

from datetime import date
from dateutil import parser
from dateutil.tz import tzlocal, tzutc
from flask import request, session
from flask.ext import restful
from flask_restful import fields
from flask_registry import ModuleAutoDiscoveryRegistry
from functools import wraps
from cerberus import Validator

error_codes = dict(
    validation_error=10,
)
"""
Available error codes for REST API.
"""

#errors and codes when validating JSON data concerning restful APIs
validation_errors = dict(
    INCORRECT_TYPE=dict(
        error_code=1,
        error_mesg="An Attribute has incorrect type according to schema"
    ),
    MISSING_FROM_USER_INPUT=dict(
        error_code=2,
        error_mesg="Input is missing a required field"
    ),
    NON_EXISTING_TO_SCHEMA=dict(
        error_code=3,
        error_mesg="Input contains a field that does not exist in schema"
    ),
    NO_UTC_ISO_FORMAT=dict(
        error_code=4,
        error_mesg=("Input contains datetime attribute "
                    "that is not in utc iso format")
    ),
    DATETIME_PARSE_ERROR=dict(
        error_code=5,
        error_mesg="Input contains datetime attribute that cannot be parsed"
    ),
    VALUE_OUT_OF_BOUNDS=dict(
        error_code=6,
        error_mesg="Input contains an attribute with an out of bounds value"
    ),
    INCORRECT_ELEMENT_TYPE_IN_DATASTRUCTURE=dict(
        error_code=7,
        error_mesg="Elements in data structure have incorrect type"),
)


class RESTValidator(Validator):

    """Validator for restful Api."""

    def _validate_utciso(self, utciso, field, value):
        """Validate UTC ISO format."""
        try:
            dt = parser.parse(value)
            if dt.tzinfo != tzutc():
                self._error(field, "not in utc iso format")
        except Exception:
            self._error(field, "cannot parse date-time")

    def get_errors(self):
        """Transform cerberus validator errors to a list of dictionaries.

        Example::

            {
                "code": c,
                "message": "a message",
                "field": f
            }
        """
        found_errors = []
        all_errors = self.errors

        for key in all_errors:
            if isinstance(all_errors[key], str):
                msg_error = all_errors[key]

                if re.match(
                    "must be of (string|integer|float|boolean|list) type",
                    msg_error
                ):
                    error_to_append = dict(
                        code=validation_errors['INCORRECT_TYPE']['error_code'],
                        message=(
                            validation_errors['INCORRECT_TYPE']['error_mesg']
                            + ": " + "'" + key + "' " + msg_error
                        ),
                        field=key
                    )
                    found_errors.append(error_to_append)

                elif msg_error == "unknown field":
                    error_to_append = dict(
                        code=(validation_errors['NON_EXISTING_TO_SCHEMA']
                              ['error_code']),
                        message=(validation_errors['NON_EXISTING_TO_SCHEMA']
                                 ['error_mesg']),
                        field=key
                    )
                    found_errors.append(error_to_append)

                elif msg_error == "required field":
                    error_to_append = dict(
                        code=(validation_errors['MISSING_FROM_USER_INPUT']
                              ['error_code']),
                        message=(validation_errors['MISSING_FROM_USER_INPUT']
                                 ['error_mesg']),
                        field=key
                    )
                    found_errors.append(error_to_append)

                elif msg_error == "not in utc iso format":
                    error_to_append = dict(
                        code=(validation_errors['NO_UTC_ISO_FORMAT']
                              ['error_code']),
                        message=(validation_errors['NO_UTC_ISO_FORMAT']
                                 ['error_mesg']),
                        field=key
                    )
                    found_errors.append(error_to_append)
                elif msg_error == "cannot parse date-time":
                    error_to_append = dict(
                        code=(validation_errors['DATETIME_PARSE_ERROR']
                              ['error_code']),
                        message=(validation_errors['DATETIME_PARSE_ERROR']
                                 ['error_mesg']),
                        field=key
                    )
                    found_errors.append(error_to_append)
                elif msg_error.startswith("unallowed value"):
                    error_to_append = dict(
                        code=(validation_errors['VALUE_OUT_OF_BOUNDS']
                              ['error_code']),
                        message=(validation_errors['VALUE_OUT_OF_BOUNDS']
                                 ['error_mesg'] +
                                 " : " + msg_error),
                        field=key
                    )
                    found_errors.append(error_to_append)

            elif isinstance(all_errors[key], dict):
                error_dict = all_errors[key]
                for entry in error_dict:
                    if re.match(
                        "must be of (string|integer|float|boolean|list) type",
                        error_dict[entry]
                    ):
                        error_to_append = dict(
                            code=(validation_errors
                                  ['INCORRECT_ELEMENT_TYPE_IN_DATASTRUCTURE']
                                  ['error_code']),
                            message=(
                                validation_errors
                                ['INCORRECT_ELEMENT_TYPE_IN_DATASTRUCTURE']
                                ['error_mesg'] +
                                " : " + error_dict[entry]),
                            field=key
                        )
                        found_errors.append(error_to_append)
                        break

        return found_errors


#
# Marshal fields
#
class ISODate(fields.Raw):

    """Format a datetime object in ISO format."""

    def format(self, dt):
        """Format a datetime object in ISO format."""
        try:
            if isinstance(dt, date):
                return six.text_type(dt.isoformat())
            else:
                return six.text_type(dt)
        except AttributeError as ae:
            raise fields.MarshallingException(ae)


class UTCISODateTime(fields.DateTime):

    """Format a datetime object in ISO format.

    Convert to UTC if necessary.
    """

    def format(self, dt):
        """Format a datetime object in ISO format.

        Convert to UTC if necessary.
        """
        try:
            if not dt.tzinfo:
                dt = dt.replace(tzinfo=tzlocal())
            return six.text_type(dt.astimezone(tzutc()).isoformat())
        except AttributeError as ae:
            raise fields.MarshallingException(ae)


class UTCISODateTimeString(fields.DateTime):

    """Format a string which represents a datetime in ISO format.

    Convert to UTC if necessary.
    """

    def format(self, value):
        """Format a string which represents a datetime in ISO format.

        Convert to UTC if necessary.
        """
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
    """Decorator to require API authentication using either API key or OAuth.

    Note, API key usage will be deprecated. Personal OAuth access tokens
    provide the same features as API keys.

    :param scopes: List of required OAuth scopes.
    """
    # Decorators specified in  ``method_decorators``  in Flask-Restful's
    # attribute is applied to a bound instance method, where as if you
    # decorate the class method is applied to an unbound instance. If you
    # are not accessing *args or **kwargs this doesn't matter. If you are
    # you can check if the method is bound using the following line:
    #   is_bound = hasattr(f, '__self__') and f.__self__

    def wrapper(f):
        # Wrap function with oauth require decorator
        from invenio.modules.oauth2server.provider import oauth2
        f_oauth_required = oauth2.require_oauth()(f)

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
            else:
                # OAuth 2.0 Authentication
                resp = f_oauth_required(*args, **kwargs)
            session.clear()
            return resp
        return decorated
    return wrapper


def require_oauth_scopes(*scopes):
    """Decorator to require a list of OAuth scopes.

    Decorator must be preceded by a ``require_api_auth()`` decorator.
    Note, API key authentication is bypassing this check
    """
    required_scopes = set(scopes)

    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Variable requests.oauth is only defined for oauth requests (see
            # require_api_auth() above).
            if hasattr(request, 'oauth') and request.oauth is not None:
                token_scopes = set(request.oauth.access_token.scopes)
                if not required_scopes.issubset(token_scopes):
                    restful.abort(403)
            return f(*args, **kwargs)
        return decorated
    return wrapper


def require_header(header, value):
    """Decorator to test if proper content-type is provided."""
    def decorator(f):
        @wraps(f)
        def inner(*args, **kwargs):
            if header == 'Content-Type':
                test_value = request.headers.get(header, '').split(';')[0]
            else:
                test_value = request.headers.get(header, '')

            if (callable(value) and not value(test_value)) or \
                    test_value != value:
                msg = value if not callable(value) else value.__doc__
                restful.abort(
                    415,
                    message="Expected %s: %s" % (header, msg),
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
