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

"""Client blueprint used to handle OAuth callbacks."""

from __future__ import absolute_import

from flask import Blueprint, abort, current_app, request, session, url_for
from flask_login import user_logged_out
from itsdangerous import BadData, TimedJSONWebSignatureSerializer
from werkzeug.local import LocalProxy

from invenio.base.globals import cfg
from invenio.ext.sslify import ssl_required
from invenio.utils.url import get_safe_redirect_target

from ..client import disconnect_handlers, handlers, oauth, signup_handlers
from ..handlers import authorized_default_handler, disconnect_handler, \
    make_handler, make_token_getter, oauth_logout_handler, set_session_next_url


blueprint = Blueprint(
    'oauthclient',
    __name__,
    url_prefix="/oauth",
    static_folder="../static",
    template_folder="../templates",
)


serializer = LocalProxy(
    lambda: TimedJSONWebSignatureSerializer(
        cfg['SECRET_KEY'],
        expires_in=cfg['OAUTHCLIENT_STATE_EXPIRES'],
    )
)


@blueprint.before_app_first_request
def setup_app():
    """Setup OAuth clients."""
    # Connect signal to remove access tokens on logout
    user_logged_out.connect(oauth_logout_handler)

    # Add remote applications
    oauth.init_app(current_app)

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
                conf.get('authorized_handler', authorized_default_handler),
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

        # Register sign-up handlers
        def dummy_handler(remote, *args, **kargs):
            pass

        signup_handler = conf.get('signup_handler', dict())
        account_info_handler = make_handler(
            signup_handler.get('info', dummy_handler),
            remote,
            with_response=False
        )
        account_setup_handler = make_handler(
            signup_handler.get('setup', dummy_handler),
            remote,
            with_response=False
        )
        account_view_handler = make_handler(
            signup_handler.get('view', dummy_handler),
            remote,
            with_response=False
        )

        signup_handlers.register(
            remote_app,
            dict(
                info=account_info_handler,
                setup=account_setup_handler,
                view=account_view_handler,
            )
        )


@blueprint.route('/login/<remote_app>/')
@ssl_required
def login(remote_app):
    """Send user to remote application for authentication."""
    if remote_app not in oauth.remote_apps:
        return abort(404)

    # Get redirect target in safe manner.
    next_param = get_safe_redirect_target(arg='next')

    # Redirect URI - must be registered in the remote service.
    callback_url = url_for(
        '.authorized',
        remote_app=remote_app,
        _external=True,
    )

    # Create a JSON Web Token that expires after OAUTHCLIENT_STATE_EXPIRES
    # seconds.
    state_token = serializer.dumps({
        'app': remote_app,
        'next': next_param,
        'sid': session.sid,
    })

    return oauth.remote_apps[remote_app].authorize(
        callback=callback_url,
        state=state_token,
    )


@blueprint.route('/authorized/<remote_app>/')
@ssl_required
def authorized(remote_app=None):
    """Authorized handler callback."""
    if remote_app not in handlers:
        return abort(404)

    state_token = request.args.get('state')

    # Verify state parameter
    try:
        assert state_token
        # Checks authenticity and integrity of state and decodes the value.
        state = serializer.loads(state_token)
        # Verify that state is for this session, app and that next parameter
        # have not been modified.
        assert state['sid'] == session.sid
        assert state['app'] == remote_app
        # Store next URL
        set_session_next_url(remote_app, state['next'])
    except (AssertionError, BadData):
        if current_app.config.get('OAUTHCLIENT_STATE_ENABLED', True) or (
           not(current_app.debug or current_app.testing)):
            abort(403)

    return handlers[remote_app]()


@blueprint.route('/signup/<remote_app>/', methods=['GET', 'POST'])
@ssl_required
def signup(remote_app):
    """Extra signup step."""
    if remote_app not in signup_handlers:
        return abort(404)
    res = signup_handlers[remote_app]['view']()
    return abort(404) if res is None else res


@blueprint.route('/disconnect/<remote_app>/')
@ssl_required
def disconnect(remote_app):
    """Disconnect user from remote application.

    Removes application as well as associated information.
    """
    if remote_app not in disconnect_handlers:
        return abort(404)

    return disconnect_handlers[remote_app]()
