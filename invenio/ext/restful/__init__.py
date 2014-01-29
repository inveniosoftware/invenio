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

from datetime import date
from dateutil import parser
from dateutil.tz import tzlocal, tzutc
from flask import request, current_app
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
def require_api_auth(f):
    """ Decorator """
    def authenticate_key(fn):
        @wraps(fn)
        def auth_key(*args, **kwargs):
            if 'apikey' in request.values:
                from invenio.modules.apikeys.models import WebAPIKey
                from flask.ext.login import login_user

                user_id = WebAPIKey.acc_get_uid_from_request()
                if user_id == -1:
                    restful.abort(401)
                login_user(user_id)
            else:
                restful.abort(401)
            return fn(*args, **kwargs)
        return auth_key
    return authenticate_key(f)

"""
Global restful API object.
"""

def setup_app(app):
    """Setup api extension."""
    api = restful.Api()
    api.init_app(app)
    app.extensions['restful'] = api

    class RestfulRegistry(ModuleAutoDiscoveryRegistry):
        setup_func_name = 'setup_app'

        def register(self, module, *args, **kwargs):
            return super(RestfulRegistry, self).register(module, app, api,
                                                         *args, **kwargs)

    app.extensions['registry']['restful'] = RestfulRegistry(
        'restful', app=app, with_setup=True
    )
