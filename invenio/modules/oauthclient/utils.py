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

""" Utility methods to help find, authenticate or register a remote user. """

from flask.ext.login import logout_user
from invenio.ext.login import authenticate, UserInfo
from invenio.ext.sqlalchemy import db
from invenio.ext.script import generate_secret_key
from invenio.modules.accounts.models import User

from .models import RemoteToken, RemoteAccount


def oauth_get_user(client_id, account_info=None, access_token=None):
    """
    Retrieve user object for the given request.

    Uses either the access token or extracted account information to retrieve
    the user object.
    """
    if access_token:
        token = RemoteToken.get_by_token(client_id, access_token)
        if token:
            return UserInfo(token.remote_account.user_id)

    if account_info and account_info.get('email'):
        u = User.query.filter_by(email=account_info['email']).first()
        if u:
            return UserInfo(u.id)
    return None


def oauth_authenticate(client_id, userinfo, require_existing_link=False):
    """ Authenticate an oauth authorized callback. """
    # Authenticate via the access token (access token used to get user_id)
    if userinfo and authenticate(userinfo['email']):
        if require_existing_link:
            account = RemoteAccount.get(userinfo.get_id(), client_id)
            if account is None:
                logout_user()
                return False
        return True
    return False


def oauth_register(account_info):
    """ Register user if possible. """
    from invenio.modules.accounts.models import User
    if account_info and account_info.get('email'):
        if not User.query.filter_by(email=account_info['email']).first():
            # Email does not already exists. so we can proceed to register
            # user.
            u = User(
                nickname=account_info.get('nickname', ''),
                email=account_info['email'],
                password=generate_secret_key(),
                note='1',  # Activated - assumes email is validated
            )

            try:
                db.session.add(u)
                db.session.commit()
                return UserInfo(u.id)
            except Exception:
                pass
    return None
