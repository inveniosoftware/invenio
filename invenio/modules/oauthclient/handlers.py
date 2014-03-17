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

import six
from functools import wraps, partial
from werkzeug.utils import import_string
from flask import session, redirect, flash, url_for, current_app
from flask.ext.login import current_user

from invenio.base.globals import cfg

from .models import RemoteToken, RemoteAccount


def token_session_key(remote_app):
    """ Generate a session key used to store the token for a remote app """
    return '%s_%s' % (cfg['OAUTHCLIENT_SESSION_KEY_PREFIX'], remote_app)


def oauth1_token_setter(remote, resp, token_type='', extra_data=None):
    return token_setter(
        remote,
        resp['oauth_token'],
        secret=resp['oauth_token_secret'],
        extra_data=extra_data,
        token_type=token_type,
    )


def oauth2_token_setter(remote, resp, token_type='', extra_data=None):
    return token_setter(
        remote,
        resp['access_token'],
        secret='',
        token_type=token_type,
        extra_data=extra_data,
    )


def token_setter(remote, token, secret='', token_type='', extra_data=None):
    """
    Set token for user
    """
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
    """
    Retrieve OAuth access token - used by flask-oauthlib to get the access
    token when making requests.

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


def default_handler(resp, remote, *args, **kwargs):
    """
    Default authorized handler

    :param resp:
    :param remote:
    """
    if resp is not None:
        if 'access_token' in resp:
            oauth2_token_setter(remote, resp)
        else:
            oauth1_token_setter(remote, resp)
    else:
        flash("You rejected the authentication request.")
    return redirect('/')


def disconnect_handler(remote, *args, **kwargs):
    if not current_user.is_authenticated():
        return current_app.login_manager.unauthorized()

    account = RemoteAccount.get(
        user_id=current_user.get_id(),
        client_id=remote.consumer_key
    )
    if account:
        account.delete()

    return redirect(url_for('oauthclient_settings.index'))


def make_handler(f, remote, with_response=True):
    """
    Make a handler for authorized and disconnect callbacks

    :param f: Callable or an import path to a callable
    """
    if isinstance(f, six.text_type):
        f = import_string(f)

    @wraps(f)
    def inner(*args, **kwargs):
        if with_response:
            return f(args[0], remote, *args[1:], **kwargs)
        else:
            return f(remote, *args, **kwargs)
    return inner


def make_token_getter(remote):
    """
    Make a token getter for a remote application
    """
    return partial(token_getter, remote)
