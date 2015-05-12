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

"""Utility methods to help find, authenticate or register a remote user."""

from flask import current_app

from flask_login import logout_user

from invenio.base.globals import cfg
from invenio.ext.login import UserInfo, authenticate
from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import User, UserEXT

from .models import RemoteAccount, RemoteToken


def _get_external_id(account_info):
    """Get external id from account info."""
    if all(k in account_info for k in ("external_id", "external_method")):
        return dict(id=account_info['external_id'],
                    method=account_info['external_method'])
    return None


def oauth_get_user(client_id, account_info=None, access_token=None):
    """Retrieve user object for the given request.

    Uses either the access token or extracted account information to retrieve
    the user object.
    """
    if access_token:
        token = RemoteToken.get_by_token(client_id, access_token)
        if token:
            return UserInfo(token.remote_account.user_id)

    if account_info:
        external_id = _get_external_id(account_info)
        if external_id:
            u = UserEXT.query.filter_by(id=external_id['id'],
                                        method=external_id['method']
                                        ).first()
            if u:
                return UserInfo(u.id_user)
        if account_info.get('email'):
            u = User.query.filter_by(email=account_info['email']).first()
            if u:
                return UserInfo(u.id)
    return None


def oauth_authenticate(client_id, userinfo, require_existing_link=False,
                       remember=False):
    """Authenticate an oauth authorized callback."""
    # Authenticate via the access token (access token used to get user_id)
    if userinfo and authenticate(userinfo['email'], remember=remember):
        if require_existing_link:
            account = RemoteAccount.get(userinfo.get_id(), client_id)
            if account is None:
                logout_user()
                return False
        return True
    return False


def oauth_register(account_info, form_data=None):
    """Register user if possible."""
    from invenio.modules.accounts.models import User

    email = account_info.get("email")
    if form_data and form_data.get("email"):
        email = form_data.get("email")

    if email:
        if not User.query.filter_by(email=email).first():
            # Email does not already exists. so we can proceed to register
            # user.
            u = User(
                nickname=account_info.get('nickname', ''),
                email=email,
                password=None,
                # email has to be validated
                note='2',
            )

            try:
                db.session.add(u)
                db.session.commit()
            except Exception:
                current_app.logger.exception("Cannot create user")
                return None

            # verify the email
            if cfg['CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT']:
                u.verify_email()

            return UserInfo(u.id)

    return None


def oauth_link_external_id(user, external_id=None):
    """Link a user to an external id."""
    oauth_unlink_external_id(external_id)
    db.session.add(UserEXT(
        id=external_id['id'], method=external_id['method'], id_user=user.id
    ))


def oauth_unlink_external_id(external_id):
    """Unlink a user from an external id."""
    UserEXT.query.filter_by(id=external_id['id'],
                            method=external_id['method']).delete()
    db.session.commit()
