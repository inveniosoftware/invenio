# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
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

"""Provide initialization and configuration for `flask_login` module."""

import urllib
from datetime import datetime

from flask import current_app, flash, g, redirect, request, session, url_for

from flask_login import LoginManager, current_user, \
    login_user as flask_login_user, logout_user, user_logged_in

from .legacy_user import UserInfo


def login_user(user, *args, **kwargs):
    """Allow login user by its id."""
    if type(user) in [int, long]:
        user = UserInfo(user)
    return flask_login_user(user, *args, **kwargs)


# FIXME move to account module
def reset_password(email, ln=None):
    """Reset user password."""
    from datetime import timedelta
    from invenio.config import CFG_SITE_SUPPORT_EMAIL, CFG_SITE_NAME, \
        CFG_SITE_NAME_INTL, CFG_WEBSESSION_RESET_PASSWORD_EXPIRE_IN_DAYS
    # create the reset key
    if ln is None:
        ln = g.ln
    from invenio.modules.access.mailcookie import mail_cookie_create_pw_reset
    reset_key = mail_cookie_create_pw_reset(email, cookie_timeout=timedelta(
        days=CFG_WEBSESSION_RESET_PASSWORD_EXPIRE_IN_DAYS))
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
                      tmpl_account_reset_password_email_body(
                          email, reset_key, request.remote_addr, ln)):
        return False  # mail could not be sent

    return True  # password reset email send successfully


def login_redirect(referer=None):
    """Redirect to url after login."""
    if referer is None:
        referer = request.values.get('referer')
    if referer:
        from six.moves.urllib.parse import urlparse
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
                 login_method=None, remember=False):
    """
    Find user identified by given information and login method.

    :param nickname_or_email: User nickname or email address
    :param password: Password used only in login methods that need it
    :param login_method: Login method (default: 'Local')
    :return: UserInfo
    """
    from invenio.base.i18n import _
    from invenio.ext.sqlalchemy import db
    from invenio.modules.accounts.models import User
    from sqlalchemy.orm.exc import NoResultFound

    where = [db.or_(User.nickname == nickname_or_email,
                    User.email == nickname_or_email)]

    try:
        user = User.query.filter(*where).one()
        if login_method == 'Local' and password is not None:
            if not user.verify_password(password, migrate=True):
                return False
    except NoResultFound:
        return None
    except Exception:
        current_app.logger.exception("Problem checking password.")
        return False

    if login_method is not None and user.settings['login_method'] != login_method:
        flash(_("You are not authorized to use '%(x_login_method)s' login "
                "method.", x_login_method=login_method), 'error')
        return False

    if user.note == '2':  # account is not confirmed
        flash(_("You have not yet verified your email address."), 'warning')

    if user.note == '0':  # account is blocked
        logout_user()
        return False

    if remember:
        session.permanent = True
    return login_user(user.id, remember=remember)


def setup_app(app):
    """Setup login extension."""
    app.config.setdefault('CFG_OPENID_AUTHENTICATION', False)
    app.config.setdefault('CFG_OAUTH1_AUTHENTICATION', False)
    app.config.setdefault('CFG_OAUTH2_AUTHENTICATION', False)

    @app.errorhandler(401)
    def do_login_first(error=401):
        """Display login page when user is not authorised."""
        if request.is_xhr:
            return g._("Authorization failure"), 401
        secure_url = url_for(request.endpoint, _external=True, _scheme='https',
                             **request.view_args)
        if not urllib.unquote(secure_url).startswith(request.base_url):
            return redirect(secure_url)
        if current_user.is_guest:
            if not session.get('_flashes'):
                flash(g._("Please sign in to continue."), 'info')
            from invenio.modules.accounts.views.accounts import login
            return login(referer=request.url)
        else:
            from flask import render_template
            return render_template("401.html"), 401

    # Let's create login manager.
    _login_manager = LoginManager(app)
    _login_manager.login_view = app.config.get('CFG_LOGIN_VIEW',
                                               'webaccount.login')
    _login_manager.anonymous_user = UserInfo
    _login_manager.unauthorized_handler(do_login_first)

    @user_logged_in.connect_via(app)
    def _logged_in(sender, user):
        """Update last login date."""
        from invenio.modules.accounts.models import User
        User.query.filter_by(id=user.get_id()).update(dict(
            last_login=datetime.now()
        ))

    @_login_manager.user_loader
    def _load_user(uid):
        """Do not raise an exception if uid is not valid or missing."""
        return UserInfo(int(uid))

    return app
