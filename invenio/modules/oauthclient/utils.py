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


from flask.ext.login import current_user, logout_user, login_user
from invenio.ext.login import authenticate, UserInfo
from invenio.ext.sqlalchemy import db
from invenio.ext.script import generate_secret_key


from .models import RemoteToken, RemoteAccount


def oauth_authenticate(client_id, email=None, access_token=None,
                       require_existing_link=True, auto_register=False):
    """
    Authenticate and authenticated oauth request
    """
    if email is None and access_token is None:
        return False

    # Authenticate via the access token
    if access_token:
        token = RemoteToken.get_by_token(client_id, access_token)

        if token:
            u = UserInfo(token.remote_account.user_id)
            if login_user(u):
                return True

    if email:
        if authenticate(email):
            if not require_existing_link:
                return True

            # Pre-existing link required so check
            account = RemoteAccount.get(current_user.get_id(), client_id)
            if account:
                return True

            # Account doesn't exists, and thus the user haven't linked
            # the accounts
            logout_user()
            return None
        elif auto_register:
            from invenio.modules.accounts.models import User
            if not User.query.filter_by(email=email).first():
                # Email doesn't exists so we can proceed to register user.
                u = User(
                    nickname="",
                    email=email,
                    password=generate_secret_key(),
                    note='1',  # Activated
                )

                try:
                    db.session.add(u)
                    db.session.commit()
                    login_user(UserInfo(u.id))
                    return True
                except Exception:
                    pass
    return False
