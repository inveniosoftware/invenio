## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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

"""Invenio Access Control MailCookie."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

"""These functions are temporaly managing roles and other authorization via
unique urls sent by email.

FIXME: This module should be refactored into a class, as there is no point
it has to host client specific code, when each client can instead
derive from the base class and add specific bits.
"""

import sys

from invenio.dbquery import run_sql
from invenio.access_control_admin import acc_get_role_id, acc_add_user_role
from invenio.utils.hash import md5
from datetime import datetime, timedelta
from random import random
from cPickle import dumps, loads


class InvenioWebAccessMailCookieError(Exception):
    pass

class InvenioWebAccessMailCookieDeletedError(InvenioWebAccessMailCookieError):
    pass


_authorizations_kind = ('pw_reset', 'mail_activation', 'role', 'authorize_action',
                        'comment_msg', 'generic')
_datetime_format = "%Y-%m-%d %H:%M:%S"

def mail_cookie_create_common(kind, params, cookie_timeout=timedelta(days=1), onetime=False):
    """Create a unique url to be sent via email to access this authorization
    @param kind: kind of authorization (e.g. 'pw_reset', 'mail_activation', 'role')
    @param params: whatever parameters are needed
    @param cookie_timeout: for how long the url will be valid
    @param onetime: whetever to remove the cookie after it has used.
    """
    assert(kind in _authorizations_kind)
    expiration = datetime.today()+cookie_timeout
    data = (kind, params, expiration, onetime)
    password = md5(str(random())).hexdigest()
    cookie_id = run_sql('INSERT INTO accMAILCOOKIE (data,expiration,kind,onetime) VALUES '
        '(AES_ENCRYPT(%s, %s),%s,%s,%s)',
        (dumps(data), password, expiration.strftime(_datetime_format), kind, onetime))
    cookie = password[:16]+hex(cookie_id)[2:-1]+password[-16:]
    return cookie

def mail_cookie_create_role(role_name, role_timeout=timedelta(hours=3), cookie_timeout=timedelta(days=1), onetime=True):
    """Create a unique url to be sent via email to belong temporaly to a role."""
    assert(acc_get_role_id(role_name) != 0)
    kind = 'role'
    params = (role_name, role_timeout)
    return mail_cookie_create_common(kind, params, cookie_timeout, onetime)

def mail_cookie_create_pw_reset(email, cookie_timeout=timedelta(days=1)):
    """Create a unique url to be sent via email to reset the local password."""
    kind = 'pw_reset'
    if (run_sql('SELECT email FROM user WHERE email=%s', (email, ))):
        params = email
        return mail_cookie_create_common(kind, params, cookie_timeout, False)
    else:
        raise InvenioWebAccessMailCookieError, "Email '%s' doesn't exist" % email

def mail_cookie_create_mail_activation(email, cookie_timeout=timedelta(days=1)):
    """Create a unique url to be sent via email to activate an email address"""
    kind = 'mail_activation'
    params = email
    return mail_cookie_create_common(kind, params, cookie_timeout, True)

def mail_cookie_create_authorize_action(action_name, arguments,  cookie_timeout=timedelta(days=1)):
    """Create a cookie for a valid authorization contanin all the
    information to authorize an action. Well it's a meta-cookie :-)."""

    kind = 'authorize_action'
    params = (action_name, arguments)
    return mail_cookie_create_common(kind, params, cookie_timeout, False)

def mail_cookie_retrieve_kind(cookie):
    """Retrieve if it exists the kind of a cookie."""
    try:
        password = cookie[:16]+cookie[-16:]
        cookie_id = int(cookie[16:-16], 16)
        res = run_sql("SELECT kind FROM accMAILCOOKIE WHERE id=%s", (cookie_id, ), run_on_slave=True)
        if res:
            kind = res[0][0]
            assert(kind in _authorizations_kind)
            return kind
    except StandardError:
        raise InvenioWebAccessMailCookieError, "Cookie doesn't exist"

def mail_cookie_check_common(cookie, delete=False):
    """Retrieve data pointed by a cookie, returning a tuple (kind, params) or None
    if the cookie is not valid or is expired"""
    try:
        password = cookie[:16]+cookie[-16:]
        cookie_id = int(cookie[16:-16], 16)
    except Exception, e:
        raise InvenioWebAccessMailCookieError, "Cookie not valid: %s" % e
    try:
        res = run_sql("SELECT kind, AES_DECRYPT(data,%s), onetime, status FROM accMAILCOOKIE WHERE "
            "id=%s AND expiration>=NOW()", (password, cookie_id), run_on_slave=True)
        if not res:
            raise StandardError
    except StandardError:
        raise InvenioWebAccessMailCookieError, "Cookie doesn't exist"
    (kind, data, onetime, status) = res[0]
    (kind_check, params, expiration, onetime_check) = loads(data)
    if not (kind == kind_check and onetime == onetime_check):
        raise InvenioWebAccessMailCookieError, "Cookie is corrupted"
    if status == 'D':
        raise InvenioWebAccessMailCookieDeletedError, "Cookie has been deleted"
    if onetime or delete:
        run_sql("UPDATE accMAILCOOKIE SET status='D' WHERE id=%s", (cookie_id, ))
    return (kind, params)

def mail_cookie_check_role(cookie, uid):
    """Check a given cookie for a valid authorization to a particular role and
    temporaly add the given uid to the role specified."""
    try:
        (kind, params) = mail_cookie_check_common(cookie)
        assert(kind == 'role')
        (role_name, role_timeout) = params
        role_id = acc_get_role_id(role_name)
        assert(role_id != 0)
        assert(type(role_timeout) is timedelta)
    except (TypeError, AssertionError, StandardError), e:
        raise InvenioWebAccessMailCookieError, e
    expiration = (datetime.today()+role_timeout).strftime(_datetime_format)
    acc_add_user_role(uid, role_id, expiration)
    return (role_name, expiration)

def mail_cookie_check_pw_reset(cookie):
    """Check a given cookie for a valid authorization to reset the password of
    a particular email address. Return the name of a valid email to reset
    it's password or None otherwise"""
    try:
        (kind, email) = mail_cookie_check_common(cookie)
        assert(kind == 'pw_reset')
        return email
    except (TypeError, AssertionError, StandardError), e:
        raise InvenioWebAccessMailCookieError, e

def mail_cookie_check_mail_activation(cookie):
    """Check a given cookie for a valid authorization to activate a particular email address."""
    try:
        (kind, email) = mail_cookie_check_common(cookie)
        assert(kind == 'mail_activation')
        res = run_sql('SELECT note FROM user WHERE email=%s', (email, ))
        if res:
            return email
        else:
            raise InvenioWebAccessMailCookieError, "email '%s' doesn't exist" % email
    except (TypeError, AssertionError), e:
        raise InvenioWebAccessMailCookieError, e

def mail_cookie_check_authorize_action(cookie):
    """Check a given cookie for a valid authorization contanin all the
    information to authorize an action. Well it's a meta-cookie :-)."""
    try:
        (kind, params) = mail_cookie_check_common(cookie)
        assert(kind == 'authorize_action')
        return params
    except (TypeError, AssertionError), e:
        raise InvenioWebAccessMailCookieError, e


def mail_cookie_delete_cookie(cookie):
    """Remove a particular cookie."""
    mail_cookie_check_common(cookie, delete=True)


def mail_cookie_gc():
    """Clean the table for expired cookies"""
    return run_sql("DELETE FROM accMAILCOOKIE WHERE expiration<NOW()")
