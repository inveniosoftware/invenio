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

"""OAuth 2.0 Provider."""

from __future__ import absolute_import

import os
from functools import wraps

from flask import Blueprint, current_app, request, render_template, jsonify, \
    abort, redirect
from flask_oauthlib.contrib.oauth2 import bind_cache_grant, bind_sqlalchemy
from flask_login import login_required
from flask_breadcrumbs import register_breadcrumb
from oauthlib.oauth2.rfc6749.errors import OAuth2Error
from werkzeug.urls import url_encode

from invenio.ext.sqlalchemy import db
from invenio.ext.login import login_user
from invenio.base.i18n import _
from invenio.base.globals import cfg

from ..provider import oauth2
from ..models import Client, OAuthUserProxy
from ..registry import scopes as scopes_registry


blueprint = Blueprint(
    'oauth2server',
    __name__,
    url_prefix='/oauth',
    static_folder="../static",
    template_folder="../templates",
)


@blueprint.before_app_first_request
def setup_app():
    """Setup OAuth2 provider."""
    # Initialize OAuth2 provider
    oauth2.init_app(current_app)

    # Configures the OAuth2 provider to use the SQLALchemy models for getters
    # and setters for user, client and tokens.
    bind_sqlalchemy(oauth2, db.session, client=Client)

    # Flask-OAuthlib does not support CACHE_REDIS_URL
    if cfg['OAUTH2_CACHE_TYPE'] == 'redis' and \
       cfg.get('CACHE_REDIS_URL'):
        from redis import from_url as redis_from_url
        cfg.setdefault(
            'OAUTH2_CACHE_REDIS_HOST',
            redis_from_url(cfg['CACHE_REDIS_URL'])
        )

    # Configures an OAuth2Provider instance to use configured caching system
    # to get and set the grant token.
    bind_cache_grant(current_app, oauth2, OAuthUserProxy.get_current_user)

    # Disables oauthlib's secure transport detection in in debug mode.
    if current_app.debug or current_app.testing:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


@oauth2.after_request
def login_oauth2_user(valid, oauth):
    """Log in a user after having been verified."""
    if valid:
        login_user(oauth.user.id)
    return valid, oauth


def error_handler(f):
    """Handle uncaught OAuth errors."""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except OAuth2Error as e:
            # Only FatalClientError are handled by Flask-OAuthlib (as these
            # errors should not be redirect back to the client - see
            # http://tools.ietf.org/html/rfc6749#section-4.2.2.1)
            if hasattr(e, 'redirect_uri'):
                return redirect(e.in_uri(e.redirect_uri))
            else:
                return redirect(e.in_uri(oauth2.error_uri))
    return decorated


def urlreencode(f):
    """Re-encode query string.

    oauthlib's URL decoding is very strict and very often chokes on
    common user mistakes like not encoding colons, hence let Flask decode the
    request args and reencode them.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.args:
            request.url = request.base_url + "?" + url_encode(request.args)
        return f(*args, **kwargs)
    return decorated


#
# Views
#
@blueprint.route('/authorize', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.', _('Authorize application'))
@login_required
@error_handler
@urlreencode
@oauth2.authorize_handler
def authorize(*args, **kwargs):
    """View for rendering authorization request."""
    if request.method == 'GET':
        client = Client.query.filter_by(
            client_id=kwargs.get('client_id')
        ).first()

        if not client:
            abort(404)

        ctx = dict(
            client=client,
            oauth_request=kwargs.get('request'),
            scopes=map(lambda x: scopes_registry[x], kwargs.get('scopes', []))
        )
        return render_template('oauth2server/authorize.html', **ctx)

    confirm = request.form.get('confirm', 'no')
    return confirm == 'yes'


@blueprint.route('/token', methods=['POST', ])
@oauth2.token_handler
def access_token():
    """Token view handles exchange/refresh access tokens."""
    # Return None or a dictionary. Dictionary will be merged with token
    # returned to the client requesting the access token.
    # Response is in application/json
    return None


@blueprint.route('/errors/')
def errors():
    """Error view in case of invalid oauth requests."""
    from oauthlib.oauth2.rfc6749.errors import raise_from_error
    try:
        raise_from_error(request.values.get('error'), params=dict())
        return render_template('oauth2server/errors.html', error=None)
    except OAuth2Error as e:
        return render_template('oauth2server/errors.html', error=e)


@blueprint.route('/ping/', methods=['GET', 'POST'])
@oauth2.require_oauth()
def ping():
    """Test to verify that you have been authenticated."""
    return jsonify(dict(ping="pong"))


@blueprint.route('/info/')
@oauth2.require_oauth('test:scope')
def info():
    """Test to verify that you have been authenticated."""
    if current_app.testing or current_app.debug:
        return jsonify(dict(
            user=request.oauth.user.id,
            client=request.oauth.client.client_id,
            scopes=list(request.oauth.scopes)
        ))
    else:
        abort(404)


@blueprint.route('/invalid/')
@oauth2.require_oauth('invalid_scope')
def invalid():
    """Test to verify that you have been authenticated."""
    if current_app.testing or current_app.debug:
        # Not reachable
        return jsonify(dict(ding="dong"))
    else:
        abort(404)
