# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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
    invenio.ext.login
    -----------------

    This module provides initialization and configuration for `flask.ext.login`
    module.
"""

from .legacy_user import UserInfo
from flask import request, flash, g, url_for, redirect
from flask.ext.login import LoginManager, current_user, \
    login_user as flask_login_user, logout_user, login_required, UserMixin


def login_user(user, *args, **kwargs):
    """Allows login user by its id."""
    if type(user) in [int, long]:
        user = UserInfo(user)
    return flask_login_user(user, *args, **kwargs)


#FIXME move to account module
def reset_password(email, ln=None):
    from datetime import timedelta
    from invenio.config import CFG_SITE_SUPPORT_EMAIL, CFG_SITE_NAME, \
        CFG_SITE_NAME_INTL, CFG_WEBSESSION_RESET_PASSWORD_EXPIRE_IN_DAYS
    # create the reset key
    if ln is None:
        ln = g.ln
    from invenio.modules.access.mailcookie import mail_cookie_create_pw_reset
    reset_key = mail_cookie_create_pw_reset(email, cookie_timeout=timedelta(days=CFG_WEBSESSION_RESET_PASSWORD_EXPIRE_IN_DAYS))
    if reset_key is None:
        return False  # reset key could not be created

    # load the email template
    import invenio.legacy.template
    websession_templates = invenio.legacy.template.load('websession')

    # finally send the email
    from invenio.ext.email import send_email
    from invenio.base.i18n import _
    if not send_email(CFG_SITE_SUPPORT_EMAIL, email, "%s %s"
                      % (_("Password reset request for"),
                         CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME)),
                      websession_templates.
                      tmpl_account_reset_password_email_body(email,
                                                             reset_key,
                                                             request.remote_addr,
                                                             ln)):
        return False  # mail could not be sent

    return True  # password reset email send successfully


def login_redirect(referer=None):
    if referer is None:
        referer = request.values.get('referer')
    if referer:
        from urlparse import urlparse
        # we should not redirect to these URLs after login
        blacklist = [url_for('webaccount.register'),
                     url_for('webaccount.logout'),
                     url_for('webaccount.login'),
                     url_for('webaccount.lost')]
        if not urlparse(referer).path in blacklist:
            # Change HTTP method to https if needed.
            from invenio.utils.url import rewrite_to_secure_url
            referer = rewrite_to_secure_url(referer)
            return redirect(referer)
    return redirect('/')


def authenticate(nickname_or_email=None, password=None,
                 login_method='Local'):
    """
    Finds user identified by given information and login method.

    :param nickname_or_email: User nickname or email address
    :param password: Password used only in login methods that need it
    :param login_method: Login method (default: 'Local')
    :return: UserInfo
    """

    from invenio.base.i18n import _
    from invenio.ext.sqlalchemy import db
    from invenio.modules.accounts.models import User

    where = [db.or_(User.nickname == nickname_or_email,
                    User.email == nickname_or_email)]
    if login_method == 'Local' and password is not None:
        where.append(User.password == password)
    try:
        user = User.query.filter(*where).one()
    except:
        return None

    if user.settings['login_method'] != login_method:
        flash(
            _("You are not authorized to use '%(x_login_method)s' login method.",
              x_login_method=login_method), 'error')
        return None

    if user.note == '2':  # account is not confirmed
        logout_user()
        flash(_("You have not yet confirmed the email address for the \
            '%(login_method)s' authentication method.",
            login_method=login_method), 'warning')

    return login_user(user.id)


def setup_app(app):
    """Setup login extension."""

    app.config.setdefault('CFG_OPENID_AUTHENTICATION', False)
    app.config.setdefault('CFG_OAUTH1_AUTHENTICATION', False)
    app.config.setdefault('CFG_OAUTH2_AUTHENTICATION', False)

    @app.errorhandler(401)
    def do_login_first(error=401):
        """Displays login page when user is not authorised."""
        if request.is_xhr:
            return g._("Authorization failure"), 401
        flash(g._("Authorization failure"), 'error')
        from invenio.modules.accounts.views import login
        return login(referer=request.url), 401

    # Let's create login manager.
    _login_manager = LoginManager(app)
    _login_manager.login_view = app.config.get('CFG_LOGIN_VIEW',
                                               'webaccount.login')
    _login_manager.anonymous_user = UserInfo
    _login_manager.unauthorized_handler(do_login_first)

    @_login_manager.user_loader
    def _load_user(uid):
        """
        Function should not raise an exception if uid is not valid
        or User was not found in database.
        """
        return UserInfo(int(uid))

    return app
