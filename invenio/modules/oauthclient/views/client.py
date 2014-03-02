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

"""
OAuth client blueprint
"""

from __future__ import absolute_import

from flask import Blueprint, abort, current_app, url_for, request

from invenio.base.globals import cfg
from invenio.ext.sslify import ssl_required

from ..client import oauth, handlers, disconnect_handlers
from ..handlers import default_handler, make_token_getter, make_handler, \
    disconnect_handler


blueprint = Blueprint(
    'oauthclient',
    __name__,
    url_prefix="/oauth",
    static_folder="../static",
    template_folder="../templates",
)


@blueprint.before_app_first_request
def setup_app():
    """
    Setup OAuth clients
    """
    oauth.init_app(current_app)

    # Add remote applications
    for remote_app, conf in cfg['OAUTHCLIENT_REMOTE_APPS'].items():
        # Prevent double creation problems
        if remote_app not in oauth.remote_apps:
            remote = oauth.remote_app(
                remote_app,
                **conf['params']
            )

        remote = oauth.remote_apps[remote_app]

        # Set token getter for remote
        remote.tokengetter(make_token_getter(remote))

        # Register authorized handler
        handlers.register(
            remote_app,
            remote.authorized_handler(make_handler(
                conf.get('authorized_handler', default_handler),
                remote,
            ))
        )

        # Register disconnect handler
        disconnect_handlers.register(
            remote_app, make_handler(
                conf.get('disconnect_handler', disconnect_handler),
                remote,
                with_response=False,
            )
        )


@blueprint.route('/login/<remote_app>/')
@ssl_required
def login(remote_app):
    """
    Send user to remote application for authentication
    """
    if remote_app not in oauth.remote_apps:
        return abort(404)

    callback_url = url_for(
        '.authorized',
        remote_app=remote_app,
        next=request.args.get('next') or request.referrer or None,
        _external=True,
    )

    return oauth.remote_apps[remote_app].authorize(callback=callback_url)


@blueprint.route('/authorized/<remote_app>/')
@ssl_required
def authorized(remote_app=None):
    """
    Authorized handler callback
    """
    if remote_app not in handlers:
        return abort(404)

    return handlers[remote_app]()


@blueprint.route('/disconnect/<remote_app>/')
@ssl_required
def disconnect(remote_app):
    """
    Disconnect user from remote application. Removes application as well as
    associated information.
    """
    if remote_app not in disconnect_handlers:
        return abort(404)

    return disconnect_handlers[remote_app]()
