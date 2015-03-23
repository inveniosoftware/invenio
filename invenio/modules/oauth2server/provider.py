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

"""Configuration of flask-oauthlib provider."""

from datetime import datetime, timedelta

from flask import current_app
from flask_login import current_user
from flask_oauthlib.provider import OAuth2Provider

from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import User
from .models import Token, Client


oauth2 = OAuth2Provider()


@oauth2.usergetter
def get_user(username, password, *args, **kwargs):
    """Get user for grant type password.

    Needed for grant type 'password'. Note, grant type password is by default
    disabled.
    """
    user = User.query.filter_by(username=username).first()
    if user.check_password(password):
        return user


@oauth2.tokengetter
def get_token(access_token=None, refresh_token=None):
    """Load an access token.

    Add support for personal access tokens compared to flask-oauthlib
    """
    if access_token:
        t = Token.query.filter_by(access_token=access_token).first()
        if t and t.is_personal:
            t.expires = datetime.utcnow() + timedelta(
                seconds=int(current_app.config.get(
                    'OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'
                ))
            )
        return t
    elif refresh_token:
        return Token.query.join(Token.client).filter(
            Token.refresh_token == refresh_token,
            Token.is_personal == False,
            Client.is_confidential == True,
        ).first()
    else:
        return None


@oauth2.tokensetter
def save_token(token, request, *args, **kwargs):
    """Token persistence."""
    # Exclude the personal access tokens which doesn't expire.
    uid = request.user.id if request.user else current_user.get_id()

    tokens = Token.query.filter_by(
        client_id=request.client.client_id,
        user_id=uid,
        is_personal=False,
    )

    # make sure that every client has only one token connected to a user
    if tokens:
        for tk in tokens:
            db.session.delete(tk)
        db.session.commit()

    expires_in = token.get('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=int(expires_in))

    tok = Token(
        access_token=token['access_token'],
        refresh_token=token.get('refresh_token'),
        token_type=token['token_type'],
        _scopes=token['scope'],
        expires=expires,
        client_id=request.client.client_id,
        user_id=uid,
        is_personal=False,
    )
    db.session.add(tok)
    db.session.commit()
    return tok
