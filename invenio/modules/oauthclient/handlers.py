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

"""Handlers for customizing oauthclient endpoints."""

import warnings

from functools import partial, wraps

from flask import current_app, flash, redirect, render_template, \
    request, session, url_for
from flask_login import current_user

from invenio.base.globals import cfg

import six

from werkzeug.utils import import_string

from .client import oauth, signup_handlers
from .errors import OAuthClientError, OAuthError, \
    OAuthRejectedRequestError, OAuthResponseError
from .forms import EmailSignUpForm
from .models import RemoteAccount, RemoteToken
from .utils import oauth_authenticate, oauth_get_user, oauth_register


#
# Token handling
#
def get_session_next_url(remote_app):
    """Return redirect url stored in session."""
    return session.get(
        "%s_%s" % (token_session_key(remote_app), "next_url")
    )


def set_session_next_url(remote_app, url):
    """Store redirect url in session for security reasons."""
    session["%s_%s" % (token_session_key(remote_app), "next_url")] = \
        url


def token_session_key(remote_app):
    """Generate a session key used to store the token for a remote app."""
    return '%s_%s' % (cfg['OAUTHCLIENT_SESSION_KEY_PREFIX'], remote_app)


def response_token_setter(remote, resp):
    """Extract token from response and set it for the user."""
    if resp is None:
        raise OAuthRejectedRequestError("User rejected request.", remote, resp)
    else:
        if 'access_token' in resp:
            return oauth2_token_setter(remote, resp)
        elif 'oauth_token' in resp and 'oauth_token_secret' in resp:
            return oauth1_token_setter(remote, resp)
        elif 'error' in resp:
            # Only OAuth2 specifies how to send error messages
            raise OAuthClientError(
                'Authorization with remote service failed.', remote, resp,
            )
    raise OAuthResponseError("Bad OAuth authorized request", remote, resp)


def oauth1_token_setter(remote, resp, token_type='', extra_data=None):
    """Set an OAuth1 token."""
    return token_setter(
        remote,
        resp['oauth_token'],
        secret=resp['oauth_token_secret'],
        extra_data=extra_data,
        token_type=token_type,
    )


def oauth2_token_setter(remote, resp, token_type='', extra_data=None):
    """Set an OAuth2 token.

    The refresh_token can be used to obtain a new access_token after
    the old one is expired. It is saved in the database for long term use.
    A refresh_token will be present only if `access_type=offline` is included
    in the authorization code request.
    """
    return token_setter(
        remote,
        resp['access_token'],
        secret='',
        token_type=token_type,
        extra_data=extra_data,
    )


def token_setter(remote, token, secret='', token_type='', extra_data=None):
    """Set token for user."""
    session[token_session_key(remote.name)] = (token, secret)

    # Save token if used is authenticated
    if current_user.is_authenticated():
        uid = current_user.get_id()
        cid = remote.consumer_key

        # Check for already existing token
        t = RemoteToken.get(uid, cid, token_type=token_type)

        if t:
            t.update_token(token, secret)
        else:
            t = RemoteToken.create(
                uid, cid, token, secret,
                token_type=token_type, extra_data=extra_data
            )
        return t
    return None


def token_getter(remote, token=''):
    """Retrieve OAuth access token.

    Used by flask-oauthlib to get the access token when making requests.

    :param token: Type of token to get. Data passed from ``oauth.request()`` to
         identify which token to retrieve.
    """
    session_key = token_session_key(remote.name)

    if session_key not in session and current_user.is_authenticated():
        # Fetch key from token store if user is authenticated, and the key
        # isn't already cached in the session.
        remote_token = RemoteToken.get(
            current_user.get_id(),
            remote.consumer_key,
            token_type=token,
        )

        if remote_token is None:
            return None

        # Store token and secret in session
        session[session_key] = remote_token.token()

    return session.get(session_key, None)


def token_delete(remote, token=''):
    """Remove OAuth access tokens from session."""
    session_key = token_session_key(remote.name)
    return session.pop(session_key, None)


#
# Error handling decorators
#
def oauth_error_handler(f):
    """Decorator to handle exceptions."""
    @wraps(f)
    def inner(*args, **kwargs):
        # OAuthErrors should not happen, so they are not caught here. Hence
        # they will result in a 500 Internal Server Error which is what we
        # are interested in.
        try:
            return f(*args, **kwargs)
        except OAuthClientError as e:
            current_app.logger.warning(e.message, exc_info=True)
            return oauth2_handle_error(
                e.remote, e.response, e.code, e.uri, e.description
            )
        except OAuthRejectedRequestError:
            flash("You rejected the authentication request.", category='info')
            return redirect('/')
    return inner


#
# Handlers
#
@oauth_error_handler
def authorized_default_handler(resp, remote, *args, **kwargs):
    """Store access token in session.

    Default authorized handler.
    """
    response_token_setter(remote, resp)
    return redirect('/')


@oauth_error_handler
def authorized_signup_handler(resp, remote, *args, **kwargs):
    """Handle sign-in/up functionality."""
    # Remove any previously stored auto register session key
    session.pop(token_session_key(remote.name) + '_autoregister', None)

    # Store token in session
    # ----------------------
    # Set token in session - token object only returned if
    # current_user.is_autenticated().
    token = response_token_setter(remote, resp)
    handlers = signup_handlers[remote.name]

    # Sign-in/up user
    # ---------------
    if not current_user.is_authenticated():
        account_info = handlers['info'](resp)

        user = oauth_get_user(
            remote.consumer_key,
            account_info=account_info,
            access_token=token_getter(remote)[0],
        )

        if user is None:
            # Auto sign-up if user not found
            user = oauth_register(account_info)
            if user is None:
                # Auto sign-up requires extra information
                session[
                    token_session_key(remote.name) + '_autoregister'] = True
                session[token_session_key(remote.name) +
                        "_account_info"] = account_info
                session[token_session_key(remote.name) +
                        "_response"] = resp
                return redirect(url_for(
                    ".signup",
                    remote_app=remote.name,
                ))

        # Authenticate user
        if not oauth_authenticate(remote.consumer_key, user,
                                  require_existing_link=False,
                                  remember=cfg['OAUTHCLIENT_REMOTE_APPS']
                                  [remote.name].get('remember', False)):
            return current_app.login_manager.unauthorized()

        # Link account
        # ------------
        # Need to store token in database instead of only the session when
        # called first time.
        token = response_token_setter(remote, resp)

    # Setup account
    # -------------
    if not token.remote_account.extra_data:
        try:
            handlers['setup'](token, resp)
        except TypeError:
            warnings.warn('Method signature of setup signup handler is '
                          'deprecated. It must take three arguments (remote,'
                          ' token, response).',
                          DeprecationWarning)
            handlers['setup'](token)

    # Redirect to next
    next_url = get_session_next_url(remote.name)
    if next_url:
        return redirect(next_url)
    else:
        return redirect('/')


def disconnect_handler(remote, *args, **kwargs):
    """Handle unlinking of remote account.

    This default handler will just delete the remote account link. You may
    wish to extend this module to perform clean-up in the remote service
    before removing the link (e.g. removing install webhooks).
    """
    if not current_user.is_authenticated():
        return current_app.login_manager.unauthorized()

    account = RemoteAccount.get(
        user_id=current_user.get_id(),
        client_id=remote.consumer_key
    )
    if account:
        account.delete()

    return redirect(url_for('oauthclient_settings.index'))


def signup_handler(remote, *args, **kwargs):
    """Handle extra signup information."""
    # User already authenticated so move on
    if current_user.is_authenticated():
        return redirect("/")

    # Retrieve token from session
    oauth_token = token_getter(remote)
    if not oauth_token:
        return redirect("/")

    session_prefix = token_session_key(remote.name)

    # Test to see if this is coming from on authorized request
    if not session.get(session_prefix + '_autoregister',
                       False):
        return redirect(url_for(".login", remote_app=remote.name))

    form = EmailSignUpForm(request.form)

    if form.validate_on_submit():
        account_info = session.get(session_prefix + "_account_info")
        response = session.get(session_prefix + "_response")

        # Register user
        user = oauth_register(account_info, form.data)

        if user is None:
            raise OAuthError("Could not create user.", remote)

        # Remove session key
        session.pop(session_prefix + '_autoregister', None)

        # Authenticate the user
        if not oauth_authenticate(remote.consumer_key, user,
                                  require_existing_link=False,
                                  remember=cfg['OAUTHCLIENT_REMOTE_APPS']
                                  [remote.name].get('remember', False)):
            return current_app.login_manager.unauthorized()

        # Link account and set session data
        token = token_setter(remote, oauth_token[0], secret=oauth_token[1])
        handlers = signup_handlers[remote.name]

        if token is None:
            raise OAuthError("Could not create token for user.", remote)

        if not token.remote_account.extra_data:
            try:
                handlers['setup'](token, response)
            except TypeError:
                warnings.warn('Method signature of setup signup handler is '
                              'deprecated. It must take three arguments'
                              ' (remote, token, response).',
                              DeprecationWarning)
                handlers['setup'](token)

        # Remove account info from session
        session.pop(session_prefix + '_account_info', None)
        session.pop(session_prefix + '_response', None)

        # Redirect to next
        next_url = get_session_next_url(remote.name)
        if next_url:
            return redirect(next_url)
        else:
            return redirect('/')

    return render_template(
        "oauthclient/signup.html",
        form=form,
        remote=remote,
        app_title=cfg['OAUTHCLIENT_REMOTE_APPS'][remote.name].get('title', ''),
        app_description=cfg['OAUTHCLIENT_REMOTE_APPS'][remote.name].get(
            'description', ''
        ),
        app_icon=cfg['OAUTHCLIENT_REMOTE_APPS'][remote.name].get('icon', None),
    )


def oauth_logout_handler(sender_app, user=None):
    """Remove all access tokens from session on logout."""
    for remote in oauth.remote_apps.values():
        token_delete(remote)


#
# Helpers
#
def make_handler(f, remote, with_response=True):
    """Make a handler for authorized and disconnect callbacks.

    :param f: Callable or an import path to a callable
    """
    if isinstance(f, six.string_types):
        f = import_string(f)

    @wraps(f)
    def inner(*args, **kwargs):
        if with_response:
            return f(args[0], remote, *args[1:], **kwargs)
        else:
            return f(remote, *args, **kwargs)
    return inner


def make_token_getter(remote):
    """Make a token getter for a remote application."""
    return partial(token_getter, remote)


def oauth2_handle_error(remote, resp, error_code, error_uri,
                        error_description):
    """Handle errors during exchange of one-time code for an access tokens."""
    flash("Authorization with remote service failed.")
    return redirect('/')
