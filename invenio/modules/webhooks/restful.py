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

from functools import wraps

from flask import request
from flask_restful import Resource, abort
from invenio.ext.restful import require_api_auth, require_oauth_scopes
from invenio.modules.oauth2server.models import Scope
from invenio.modules.oauth2server.registry import scopes
from .models import Receiver, ReceiverDoesNotExists, InvalidPayload, \
    WebhookError


def error_handler(f):
    """Decorator to handle exceptions."""
    @wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ReceiverDoesNotExists:
            abort(404, message="Receiver does not exists.", status=404)
        except InvalidPayload as e:
            abort(
                415,
                message="Receiver does not support the"
                        " content-type '%s'." % e.args[0],
                status=415)
        except WebhookError as e:
            abort(
                500,
                message="Internal server error",
                status=500
            )
    return inner

#
# Default decorators
#
api_decorators = [
    error_handler,
]


#
# REST Resources
#
class ReceiverEventListResource(Resource):

    """Receiver event hook."""

    method_decorators = api_decorators

    def get(self, receiver_id=None):
        abort(405)

    @require_api_auth()
    @require_oauth_scopes('webhooks:event')
    def post(self, receiver_id=None):
        receiver = Receiver.get(receiver_id)
        receiver.consume_event(request.oauth.access_token.user_id)
        return {'status': 202, 'message': 'Accepted'}, 202

    def put(self, receiver_id=None):
        abort(405)

    def delete(self, receiver_id=None):
        abort(405)

    def head(self, receiver_id=None):
        abort(405)

    def options(self, receiver_id=None):
        abort(405)

    def patch(self, receiver_id=None):
        abort(405)


#
# Register API resources
#
def setup_app(app, api):
    api.add_resource(
        ReceiverEventListResource,
        '/api/hooks/receivers/<string:receiver_id>/events/',
    )

    with app.app_context():
        scopes.register(Scope(
            'webhooks:event',
            group='Notifications',
            help_text='Allow notifications from external service.',
            internal=True,
        ))
