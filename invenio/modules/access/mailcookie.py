# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011, 2013, 2015 CERN.
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

"""Invenio Access Control MailCookie.

These functions are temporaly managing roles and other authorization via
unique urls sent by email.

FIXME: This module should be refactored into a class, as there is no point
it has to host client specific code, when each client can instead
derive from the base class and add specific bits.
"""

from datetime import datetime, timedelta

from invenio.ext.sqlalchemy import db

from .errors import InvenioWebAccessMailCookieError
from .models import AccMAILCOOKIE, User

_datetime_format = "%Y-%m-%d %H:%M:%S"


def mail_cookie_create_common(kind, params, cookie_timeout=timedelta(days=1),
                              onetime=False):
    """Create a unique url to be sent via email to access this authorization.

    :param kind: kind of authorization
        (e.g. 'pw_reset', 'mail_activation', 'role')
    :param params: whatever parameters are needed
    :param cookie_timeout: for how long the url will be valid
    :param onetime: whether to remove the cookie after it has used.
    """
    return AccMAILCOOKIE.create(kind, params, cookie_timeout, onetime)


def mail_cookie_create_role(role_name, role_timeout=timedelta(hours=3),
                            cookie_timeout=timedelta(days=1), onetime=True):
    """Create a unique url to belong temporaly to a role."""
    from .control import acc_get_role_id
    assert(acc_get_role_id(role_name) != 0)
    kind = 'role'
    params = (role_name, role_timeout)
    return mail_cookie_create_common(kind, params, cookie_timeout, onetime)


def mail_cookie_create_pw_reset(email, cookie_timeout=timedelta(days=1)):
    """Create a unique url to be sent via email to reset the local password."""
    user = db.session.query(User.query.filter_by(email=email).exists())
    if user.scalar():
        kind = 'pw_reset'
        return mail_cookie_create_common(kind, email, cookie_timeout, False)
    else:
        raise InvenioWebAccessMailCookieError(
            "Email '%s' doesn't exist" % email)


def mail_cookie_create_mail_activation(email,
                                       cookie_timeout=timedelta(days=1)):
    """Create cookie to be sent via email to activate an email address."""
    kind = 'mail_activation'
    params = email
    return mail_cookie_create_common(kind, params, cookie_timeout, True)


def mail_cookie_create_authorize_action(action_name, arguments,
                                        cookie_timeout=timedelta(days=1)):
    """Create a cookie for a valid authorization.

    It contanins all the information to authorize an action.
    Well it's a meta-cookie :-).
    """
    kind = 'authorize_action'
    params = (action_name, arguments)
    return mail_cookie_create_common(kind, params, cookie_timeout, False)


def mail_cookie_retrieve_kind(cookie):
    """Retrieve if it exists the kind of a cookie."""
    try:
        return AccMAILCOOKIE.get(cookie).kind
    except StandardError:
        raise InvenioWebAccessMailCookieError("Cookie doesn't exist")


def mail_cookie_check_common(cookie, delete=False):
    """Retrieve data pointed by a cookie.

    Return a tuple (kind, params) or None if the cookie is not valid or
    it is expired.
    """
    obj = AccMAILCOOKIE.get(cookie, delete=delete)
    return (obj.kind, obj.data[1])


def mail_cookie_check_role(cookie, uid):
    """Check a given role cookie for a valid authorization.

    Temporarily add the given uid to the role specified.
    """
    from .control import acc_get_role_id, acc_add_user_role
    try:
        (kind, params) = mail_cookie_check_common(cookie)
        assert kind == 'role'
        (role_name, role_timeout) = params
        role_id = acc_get_role_id(role_name)
        assert role_id != 0
        assert type(role_timeout) is timedelta
    except (TypeError, AssertionError, StandardError):
        raise InvenioWebAccessMailCookieError
    expiration = (datetime.today()+role_timeout).strftime(_datetime_format)
    acc_add_user_role(uid, role_id, expiration=expiration)
    return (role_name, expiration)


def mail_cookie_check_pw_reset(cookie):
    """Check a given reset password cookie for a valid authorization.

    Return the name of a valid email to reset it's password or None otherwise.
    """
    try:
        (kind, email) = mail_cookie_check_common(cookie)
        assert kind == 'pw_reset'
        return email
    except (TypeError, AssertionError, StandardError):
        raise InvenioWebAccessMailCookieError


def mail_cookie_check_mail_activation(cookie):
    """Check a mail activation cookie for a valid authorization."""
    #try:
    (kind, email) = mail_cookie_check_common(cookie)
    assert(kind == 'mail_activation')
    user = db.session.query(User.query.filter_by(email=email).exists())
    if user.scalar():
        return email
    else:
        raise InvenioWebAccessMailCookieError(
            "email '%s' doesn't exist" % email)
        #except (TypeError, AssertionError):
        #raise InvenioWebAccessMailCookieError


def mail_cookie_check_authorize_action(cookie):
    """Check a given cookie for a valid authorization.

    It must contanin all the information to authorize an action.
    Well it's a meta-cookie :-).
    """
    try:
        (kind, params) = mail_cookie_check_common(cookie)
        assert(kind == 'authorize_action')
        return params
    except (TypeError, AssertionError):
        raise InvenioWebAccessMailCookieError


def mail_cookie_delete_cookie(cookie):
    """Remove a particular cookie."""
    mail_cookie_check_common(cookie, delete=True)


def mail_cookie_gc():
    """Clean the table for expired cookies."""
    return AccMAILCOOKIE.gc()
