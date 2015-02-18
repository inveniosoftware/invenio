# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012,
#               2013, 2014, 2015  CERN.
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

"""
This file implements all methods necessary for working with users and
sessions in Invenio.  Contains methods for logging/registration
when a user log/register into the system, checking if it is a guest
user or not.

At the same time this presents all the stuff it could need with
sessions managements, working with websession.

It also contains Apache-related user authentication stuff.
"""

__revision__ = "$Id$"

import cgi
import urllib
import urlparse
import socket
import smtplib
import re
import random
import datetime

from flask import Request, current_app
from six import iteritems
from socket import gaierror
import os
import binascii
import time

from invenio.base.wrappers import lazy_import
from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS, \
     CFG_ACCESS_CONTROL_LEVEL_GUESTS, \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN, \
     CFG_ACCESS_CONTROL_NOTIFY_ADMIN_ABOUT_NEW_ACCOUNTS, \
     CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT, \
     CFG_SITE_ADMIN_EMAIL, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_SITE_NAME_INTL, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_SITE_SECURE_URL, \
     CFG_SITE_URL, \
     CFG_WEBSESSION_ADDRESS_ACTIVATION_EXPIRE_IN_DAYS, \
     CFG_CERN_SITE, \
     CFG_INSPIRE_SITE, \
     CFG_BIBAUTHORID_ENABLED, \
     CFG_SITE_RECORD

try:
    from flask import session
except ImportError:
    pass
from invenio.legacy.dbquery import run_sql
from invenio.utils.serializers import serialize_via_marshal


from invenio.base.i18n import gettext_set_language, wash_languages, wash_language
from invenio.ext.email import send_email
from invenio.ext.logging import register_exception
from invenio.ext.sqlalchemy import db
from invenio.legacy.websession.dblayer import get_groups
from invenio.modules.accounts.models import User

from invenio.legacy.websession.webuser_config import CFG_WEBUSER_USER_TABLES

from sqlalchemy.exc import OperationalError

acc_get_role_id = lazy_import('invenio.modules.access.control:acc_get_role_id')
acc_get_action_roles = lazy_import('invenio.modules.access.control:acc_get_action_roles')
acc_get_action_id = lazy_import('invenio.modules.access.control:acc_get_action_id')
acc_is_user_in_role = lazy_import('invenio.modules.access.control:acc_is_user_in_role')
acc_find_possible_activities = lazy_import('invenio.modules.access.control:acc_find_possible_activities')
mail_cookie_create_mail_activation = lazy_import('invenio.modules.access.mailcookie:mail_cookie_create_mail_activation')
acc_firerole_check_user = lazy_import('invenio.modules.access.firerole:acc_firerole_check_user')
load_role_definition = lazy_import('invenio.modules.access.firerole:load_role_definition')
SUPERADMINROLE = lazy_import('invenio.modules.access.local_config:SUPERADMINROLE')
CFG_EXTERNAL_AUTH_USING_SSO = lazy_import('invenio.modules.access.local_config:CFG_EXTERNAL_AUTH_USING_SSO')
CFG_EXTERNAL_AUTHENTICATION = lazy_import('invenio.modules.access.local_config:CFG_EXTERNAL_AUTHENTICATION')
CFG_WEBACCESS_MSGS = lazy_import('invenio.modules.access.local_config:CFG_WEBACCESS_MSGS')
CFG_WEBACCESS_WARNING_MSGS = lazy_import('invenio.modules.access.local_config:CFG_WEBACCESS_WARNING_MSGS')
CFG_EXTERNAL_AUTH_DEFAULT = lazy_import('invenio.modules.access.local_config:CFG_EXTERNAL_AUTH_DEFAULT')
CFG_TEMP_EMAIL_ADDRESS = lazy_import('invenio.modules.access.local_config:CFG_TEMP_EMAIL_ADDRESS')




# import invenio.legacy.template
# tmpl = invenio.legacy.template.load('websession')
tmpl = lazy_import('invenio.legacy.websession.templates:Template')()
# tmpl = object


re_invalid_nickname = re.compile(""".*[,'@]+.*""")

# pylint: disable=C0301

def createGuestUser():
    """Create a guest user , insert into user null values in all fields

       createGuestUser() -> GuestUserID
    """
    if CFG_ACCESS_CONTROL_LEVEL_GUESTS == 0:
        try:
            return run_sql("insert into user (email, note) values ('', '1')")
        except OperationalError:
            return None
    else:
        try:
            return run_sql("insert into user (email, note) values ('', '0')")
        except OperationalError:
            return None

def page_not_authorized(req, referer='', uid='', text='', navtrail='', ln=CFG_SITE_LANG,
                        navmenuid=""):
    """Show error message when user is not authorized to do something.

    @param referer: in case the displayed message propose a login link, this
    is the url to return to after logging in. If not specified it is guessed
    from req.

    @param uid: the uid of the user. If not specified it is guessed from req.

    @param text: the message to be displayed. If not specified it will be
    guessed from the context.
    """

    from invenio.legacy.webpage import page

    _ = gettext_set_language(ln)

    if not referer:
        referer = req.unparsed_uri

    if not CFG_ACCESS_CONTROL_LEVEL_SITE:
        title = CFG_WEBACCESS_MSGS[5]
        if not uid:
            uid = getUid(req)
        try:
            res = run_sql("SELECT email FROM user WHERE id=%s AND note=1", (uid,))

            if res and res[0][0]:
                if text:
                    body = text
                else:
                    body = "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[9] % cgi.escape(res[0][0]),
                                      ("%s %s" % (CFG_WEBACCESS_MSGS[0] % urllib.quote(referer), CFG_WEBACCESS_MSGS[1])))
            else:
                if text:
                    body = text
                else:
                    if CFG_ACCESS_CONTROL_LEVEL_GUESTS == 1:
                        body = CFG_WEBACCESS_MSGS[3]
                    else:
                        body = CFG_WEBACCESS_WARNING_MSGS[4] + CFG_WEBACCESS_MSGS[2]

        except OperationalError as e:
            body = _("Database problem") + ': ' + str(e)


    elif CFG_ACCESS_CONTROL_LEVEL_SITE == 1:
        title = CFG_WEBACCESS_MSGS[8]
        body = "%s %s" % (CFG_WEBACCESS_MSGS[7], CFG_WEBACCESS_MSGS[2])

    elif CFG_ACCESS_CONTROL_LEVEL_SITE == 2:
        title = CFG_WEBACCESS_MSGS[6]
        body = "%s %s" % (CFG_WEBACCESS_MSGS[4], CFG_WEBACCESS_MSGS[2])

    return page(title=title,
                language=ln,
                uid=getUid(req),
                body=body,
                navtrail=navtrail,
                req=req,
                navmenuid=navmenuid)

def getUid(req):
    """Return user ID taking it from the cookie of the request.
       Includes control mechanism for the guest users, inserting in
       the database table when need be, raising the cookie back to the
       client.

       User ID is set to 0 when client refuses cookie or we are in the
       read-only site operation mode.

       User ID is set to -1 when we are in the permission denied site
       operation mode.

       getUid(req) -> userId
    """
    #if hasattr(req, '_user_info'):
    #    return req._user_info['_uid']
    if CFG_ACCESS_CONTROL_LEVEL_SITE == 1: return 0
    if CFG_ACCESS_CONTROL_LEVEL_SITE == 2: return -1

    guest = 0
    from flask import session

    uid = session.uid
    if not session.need_https:
        if uid == -1: # first time, so create a guest user
            if CFG_ACCESS_CONTROL_LEVEL_GUESTS == 0:
                session['uid'] = 0
                session.set_remember_me(False)
                return 0
            else:
                return -1
        else:
            if not hasattr(req, '_user_info') and 'user_info' in session:
                req._user_info = session['user_info']
                req._user_info = collect_user_info(req, refresh=True)

    if guest == 0:
        guest = isGuestUser(uid)

    if guest:
        if CFG_ACCESS_CONTROL_LEVEL_GUESTS == 0:
            return uid
        elif CFG_ACCESS_CONTROL_LEVEL_GUESTS >= 1:
            return -1
    else:
        res = run_sql("SELECT note FROM user WHERE id=%s", (uid,))
        if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS == 0:
            return uid
        elif CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 1 and res and res[0][0] in [1, "1"]:
            return uid
        else:
            return -1


from invenio.ext.login import current_user, login_user, logout_user
getUid = lambda req: current_user.get_id()


def setUid(req, uid, remember_me=False):
    """It sets the userId into the session, and raise the cookie to the client.
    """
    if uid > 0:
        login_user(uid, remember_me)
    else:
        logout_user()
    return uid

def session_param_del(req, key):
    """
    Remove a given key from the session.
    """
    del session[key]

def session_param_set(req, key, value):
    """
    Set a VALUE for the session param KEY for the current session.
    """
    session[key] = value

def session_param_get(req, key, default = None):
    """
    Return session parameter value associated with session parameter KEY for the current session.
    If the key doesn't exists return the provided default.
    """
    return session.get(key, default)

def session_param_list(req):
    """
    List all available session parameters.
    """
    return session.keys()

def get_last_login(uid):
    """Return the last_login datetime for uid if any, otherwise return the Epoch."""
    res = run_sql('SELECT last_login FROM user WHERE id=%s', (uid,), 1)
    if res and res[0][0]:
        return res[0][0]
    else:
        return datetime.datetime(1970, 1, 1)

def get_user_info(uid, ln=CFG_SITE_LANG):
    """Get infos for a given user.
    @param uid: user id (int)
    @return: tuple: (uid, nickname, display_name)
    """
    _ = gettext_set_language(ln)
    query = """SELECT id, nickname
               FROM user
               WHERE id=%s"""
    res = run_sql(query, (uid,))
    if res:
        if res[0]:
            user = list(res[0])
            if user[1]:
                user.append(user[1])
            else:
                user[1] = str(user[0])
                user.append(_("user") + ' #' + str(user[0]))
            return tuple(user)
    return (uid, '', _("N/A"))

def get_uid_from_email(email):
    """Return the uid corresponding to an email.
    Return -1 when the email does not exists."""
    try:
        res = run_sql("SELECT id FROM user WHERE email=%s", (email,))
        if res:
            return res[0][0]
        else:
            return -1
    except OperationalError:
        register_exception()
        return -1

def isGuestUser(uid, run_on_slave=True):
    """It Checks if the userId corresponds to a guestUser or not

       isGuestUser(uid) -> boolean
    """
    out = 1
    try:
        res = run_sql("SELECT email FROM user WHERE id=%s LIMIT 1", (uid,), 1,
                      run_on_slave=run_on_slave)
        if res:
            if res[0][0]:
                out = 0
    except OperationalError:
        register_exception()
    return out

def isUserSubmitter(user_info):
    """Return True if the user is a submitter for something; False otherwise."""
    u_email = get_email(user_info['uid'])
    res = run_sql("SELECT email FROM sbmSUBMISSIONS WHERE email=%s LIMIT 1", (u_email,), 1)
    return len(res) > 0

def isUserReferee(user_info):
    """Return True if the user is a referee for something; False otherwise."""
    if CFG_CERN_SITE:
        return True
    else:
        for (role_id, role_name, role_description) in acc_get_action_roles(acc_get_action_id('referee')):
            if acc_is_user_in_role(user_info, role_id):
                return True
    return False

def isUserAdmin(user_info):
    """Return True if the user has some admin rights; False otherwise."""
    user = User.query.get(user_info['uid'])
    return user and user.has_admin_role

def isUserSuperAdmin(user_info):
    """Return True if the user is superadmin; False otherwise."""
    user = User.query.get(user_info['uid'])
    if user and user.has_super_admin_role:
        return True
    return acc_firerole_check_user(
        user_info, load_role_definition(acc_get_role_id(SUPERADMINROLE)))

def nickname_valid_p(nickname):
    """Check whether wanted NICKNAME supplied by the user is valid.
       At the moment we just check whether it is not empty, does not
       contain blanks or @, is not equal to `guest', etc.

       This check relies on re_invalid_nickname regexp (see above)
       Return 1 if nickname is okay, return 0 if it is not.
    """
    if nickname and \
       not(nickname.startswith(' ') or nickname.endswith(' ')) and \
       nickname.lower() != 'guest':
        if not re_invalid_nickname.match(nickname):
            return 1
    return 0

def email_valid_p(email):
    """Check whether wanted EMAIL address supplied by the user is valid.
       At the moment we just check whether it contains '@' and whether
       it doesn't contain blanks.  We also check the email domain if
       CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN is set.

       Return 1 if email is okay, return 0 if it is not.
    """
    if (email.find("@") <= 0) or (email.find(" ") > 0):
        return 0
    elif CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN:
        if not email.endswith(CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN):
            return 0
    return 1

def confirm_email(email):
    """Confirm the email. It returns None when there are problems, otherwise
    it return the uid involved."""
    if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS == 0:
        activated = 1
    elif CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS == 1:
        activated = 0
    elif CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 2:
        return -1
    run_sql('UPDATE user SET note=%s where email=%s', (activated, email))
    res = run_sql('SELECT id FROM user where email=%s', (email,))
    if res:
        if CFG_ACCESS_CONTROL_NOTIFY_ADMIN_ABOUT_NEW_ACCOUNTS:
            send_new_admin_account_warning(email, CFG_SITE_ADMIN_EMAIL)
        return res[0][0]
    else:
        return None


def registerUser(req, email, passw, nickname, register_without_nickname=False,
        login_method=None, ln=CFG_SITE_LANG):
    """Register user with the desired values of NICKNAME, EMAIL and
       PASSW.

       If REGISTER_WITHOUT_NICKNAME is set to True, then ignore
       desired NICKNAME and do not set any.  This is suitable for
       external authentications so that people can login without
       having to register an internal account first.

       Return 0 if the registration is successful, 1 if email is not
       valid, 2 if nickname is not valid, 3 if email is already in the
       database, 4 if nickname is already in the database, 5 when
       users cannot register themselves because of the site policy, 6 when the
       site is having problem contacting the user.

       If login_method is None or is equal to the key corresponding to local
       authentication, then CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS is taken
       in account for deciding the behaviour about registering.
       """

    # is email valid?
    email = email.lower()
    if not email_valid_p(email):
        return 1

    _ = gettext_set_language(ln)

    # is email already taken?
    res = run_sql("SELECT email FROM user WHERE email=%s", (email,))
    if len(res) > 0:
        return 3

    if register_without_nickname:
        # ignore desired nick and use default empty string one:
        nickname = ""
    else:
        # is nickname valid?
        if not nickname_valid_p(nickname):
            return 2
        # is nickname already taken?
        res = run_sql("SELECT nickname FROM user WHERE nickname=%s", (nickname,))
        if len(res) > 0:
            return 4

    activated = 1 # By default activated

    if not login_method or not CFG_EXTERNAL_AUTHENTICATION[login_method]: # local login
        if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 2:
            return 5
        elif CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT:
            activated = 2 # Email confirmation required
        elif CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 1:
            activated = 0 # Administrator confirmation required


    # okay, go on and register the user: FIXME
    user = User(nickname=nickname,
                email=email,
                password=passw,
                note=activated,
                last_login=datetime.datetime.now())

    if CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT:
        user.verify_email()

    try:
        db.session.add(user)
        db.session.commit()
    except Exception:
        current_app.logger.exception("Could not store user.")
        db.session.rollback()
        return 7
    if activated == 1: # Ok we consider the user as logged in :-)
        setUid(req, uid)
    return 0

def updateDataUser(uid, email, nickname):
    """
    Update user data.  Used when a user changed his email or password
    or nickname.
    """
    email = email.lower()
    if email == 'guest':
        return 0

    if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS < 2:
        run_sql("update user set email=%s where id=%s", (email, uid))

    if nickname and nickname != '':
        run_sql("update user set nickname=%s where id=%s", (nickname, uid))

    return 1

def updatePasswordUser(uid, password):
    """Update the password of a user."""
    if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS < 3:
        u = User.query.filter_by(id=uid).first()
        if u:
            u.password = password
        db.session.commit()
    return 1

def merge_usera_into_userb(id_usera, id_userb):
    """
    Merges all the information of usera into userb.
    Deletes afterwards any reference to usera.
    The information about SQL tables is contained in the CFG_WEBUSER_USER_TABLES
    variable.
    """
    preferencea = get_user_preferences(id_usera)
    preferenceb = get_user_preferences(id_userb)
    preferencea.update(preferenceb)
    set_user_preferences(id_userb, preferencea)
    try:
        ## FIXME: for the time being, let's disable locking
        ## until we will move to InnoDB and we will have
        ## real transitions
        #for table, dummy in CFG_WEBUSER_USER_TABLES:
            #run_sql("LOCK TABLE %s WRITE" % table)

        ## Special treatment for BibAuthorID
        index = 0
        table = ''
        try:
            for index, (table, column) in enumerate(CFG_WEBUSER_USER_TABLES):
                run_sql("UPDATE %(table)s SET %(column)s=%%s WHERE %(column)s=%%s; DELETE FROM %(table)s WHERE %(column)s=%%s;" % {
                    'table': table,
                    'column': column
                }, (id_userb, id_usera, id_usera))
        except Exception as err:
            msg = "Error when merging id_user=%s into id_userb=%s for table %s: %s\n" % (id_usera, id_userb, table, err)
            msg += "users where succesfully already merged for tables: %s\n" % ', '.join([table[0] for table in CFG_WEBUSER_USER_TABLES[:index]])
            msg += "users where not succesfully already merged for tables: %s\n" % ', '.join([table[0] for table in CFG_WEBUSER_USER_TABLES[index:]])
            register_exception(alert_admin=True, prefix=msg)
            raise
    finally:
        ## FIXME: locking disabled
        #run_sql("UNLOCK TABLES")
        pass


def username_exists_p(username):
    """Check if USERNAME exists in the system.  Username may be either
    nickname or email.

    Return 1 if it does exist, 0 if it does not.
    """

    if username == "":
        # return not exists if asked for guest users
        return 0
    res = run_sql("SELECT email FROM user WHERE email=%s OR nicname=%s",
                  (username, username))
    if len(res) > 0:
        return 1
    return 0

def emailUnique(p_email):
    """Check if the email address only exists once. If yes, return userid, if not, -1
    """

    query_result = run_sql("select id, email from user where email=%s", (p_email,))
    if len(query_result) == 1:
        return query_result[0][0]
    elif len(query_result) == 0:
        return 0
    return -1


def update_Uid(req, p_email, remember_me=False):
    """It updates the userId of the session. It is used when a guest user is logged in succesfully in the system with a given email and password.
    As a side effect it will discover all the restricted collection to which the user has right to
    """
    query_ID = int(run_sql("select id from user where email=%s",
                           (p_email,))[0][0])

    setUid(req, query_ID, remember_me)
    return query_ID

def send_new_admin_account_warning(new_account_email, send_to, ln=CFG_SITE_LANG):
    """Send an email to the address given by send_to about the new account new_account_email."""
    _ = gettext_set_language(ln)
    sub = _("New account on") + " '%s'" % CFG_SITE_NAME
    if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS == 1:
        sub += " - " + _("PLEASE ACTIVATE")
    body = _("A new account has been created on") + " '%s'" % CFG_SITE_NAME
    if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS == 1:
        body += _(" and is awaiting activation")
    body += ":\n\n"
    body += _("   Username/Email") + ": %s\n\n" % new_account_email
    body += _("You can approve or reject this account request at") + ": %s/admin/webaccess/webaccessadmin.py/manageaccounts\n" % CFG_SITE_URL
    return send_email(CFG_SITE_SUPPORT_EMAIL, send_to, subject=sub, content=body)

def get_email(uid):
    """Return email address of the user uid.  Return string 'guest' in case
    the user is not found."""
    out = "guest"
    res = run_sql("SELECT email FROM user WHERE id=%s", (uid,), 1)
    if res and res[0][0]:
        out = res[0][0].lower()
    return out

def get_email_from_username(username):
    """Return email address of the user corresponding to USERNAME.
    The username may be either nickname or email.  Return USERNAME
    untouched if not found in the database or if found several
    matching entries.
    """
    if username == '':
        return ''
    out = username
    res = run_sql("SELECT email FROM user WHERE email=%s", (username,), 1) + \
          run_sql("SELECT email FROM user WHERE nickname=%s", (username,), 1)
    if res and len(res) == 1:
        out = res[0][0].lower()
    return out

#def get_password(uid):
    #"""Return password of the user uid.  Return None in case
    #the user is not found."""
    #out = None
    #res = run_sql("SELECT password FROM user WHERE id=%s", (uid,), 1)
    #if res and res[0][0] != None:
        #out = res[0][0]
    #return out

def get_nickname(uid):
    """Return nickname of the user uid.  Return None in case
    the user is not found."""
    out = None
    res = run_sql("SELECT nickname FROM user WHERE id=%s", (uid,), 1)
    if res and res[0][0]:
        out = res[0][0]
    return out

def get_nickname_or_email(uid):
    """Return nickname (preferred) or the email address of the user uid.
    Return string 'guest' in case the user is not found."""
    out = "guest"
    res = run_sql("SELECT nickname, email FROM user WHERE id=%s", (uid,), 1)
    if res and res[0]:
        if res[0][0]:
            out = res[0][0]
        elif res[0][1]:
            out = res[0][1].lower()
    return out

def create_userinfobox_body(req, uid, language="en"):
    """Create user info box body for user UID in language LANGUAGE."""

    if req:
        if req.is_https():
            url_referer = CFG_SITE_SECURE_URL + req.unparsed_uri
        else:
            url_referer = CFG_SITE_URL + req.unparsed_uri
        if '/youraccount/logout' in url_referer:
            url_referer = ''
    else:
        url_referer = CFG_SITE_URL

    user_info = collect_user_info(req)

    try:
        return tmpl.tmpl_create_userinfobox(ln=language,
                                            url_referer=url_referer,
                                            guest=int(user_info['guest']),
                                            username=get_nickname_or_email(uid),
                                            submitter=user_info['precached_viewsubmissions'],
                                            referee=user_info['precached_useapprove'],
                                            admin=user_info['precached_useadmin'],
                                            usebaskets=user_info['precached_usebaskets'],
                                            usemessages=user_info['precached_usemessages'],
                                            usealerts=user_info['precached_usealerts'],
                                            usegroups=user_info['precached_usegroups'],
                                            useloans=user_info['precached_useloans'],
                                            usestats=user_info['precached_usestats']
                                            )
    except OperationalError:
        return ""


def list_registered_users():
    """List all registered users."""
    return run_sql("SELECT id,email FROM user where email!=''")

def list_users_in_role(role):
    """List all users of a given role (see table accROLE)
    @param role: role of user (string)
    @return: list of uids
    """
    res = run_sql("""SELECT uacc.id_user
                       FROM user_accROLE uacc JOIN accROLE acc
                         ON uacc.id_accROLE=acc.id
                      WHERE acc.name=%s""",
                  (role,), run_on_slave=True)
    if res:
        return map(lambda x: int(x[0]), res)
    return []

def list_users_in_roles(role_list):
    """List all users of given roles (see table accROLE)
    @param role_list: list of roles [string]
    @return: list of uids
    """
    if not(type(role_list) is list or type(role_list) is tuple):
        role_list = [role_list]
    query = """SELECT DISTINCT(uacc.id_user)
               FROM user_accROLE uacc JOIN accROLE acc
                    ON uacc.id_accROLE=acc.id
               """
    query_addons = ""
    query_params = ()
    if len(role_list) > 0:
        query_params = role_list
        query_addons = " WHERE "
        for role in role_list[:-1]:
            query_addons += "acc.name=%s OR "
        query_addons += "acc.name=%s"
    res = run_sql(query + query_addons, query_params, run_on_slave=True)
    if res:
        return map(lambda x: int(x[0]), res)
    return []

def get_user_preferences(uid):
    user = User.query.get(uid)
    if user is not None:
        return user.settings
    from invenio.modules.accounts.models import get_default_user_preferences
    return get_default_user_preferences() # empty dict mean no preferences

def set_user_preferences(uid, pref):
    assert isinstance(pref, dict)
    run_sql("UPDATE user SET settings=%s WHERE id=%s",
            (serialize_via_marshal(pref), uid))


def collect_user_info(req, login_time=False, refresh=False):
    """Given the mod_python request object rec or a uid it returns a dictionary
    containing at least the keys uid, nickname, email, groups, plus any external keys in
    the user preferences (collected at login time and built by the different
    external authentication plugins) and if the mod_python request object is
    provided, also the remote_ip, remote_host, referer, agent fields.
    NOTE: if req is a mod_python request object, the user_info dictionary
    is saved into req._user_info (for caching purpouses)
    setApacheUser & setUid will properly reset it.
    """
    from flask_login import current_user
    from invenio.ext.login import UserInfo

    if (type(req) in [long, int] and current_user.get_id() != req) \
            or req is None:
        return UserInfo(req)

    return current_user._get_current_object()


def generate_csrf_token(req):
    """Generate a new CSRF token and store it in the user session.

    Generate random CSRF token for the current user and store it in
    the current session.  Also, store the time stamp when it was
    generated.

    Return tuple (csrf_token, csrf_token_time).

    """
    csrf_token = binascii.hexlify(os.urandom(32))
    csrf_token_time = time.time()
    session_param_set(req, 'csrf_token', csrf_token)
    session_param_set(req, 'csrf_token_time', csrf_token_time)
    return (csrf_token, csrf_token_time)


def regenerate_csrf_token_if_needed(req, token_expiry=300):
    """Regenerate CSRF token, if necessary, and store it in session.

    Check whether user session has stored CSRF token, and whether it
    is still not expired, i.e. whether not more than `token_expiry`
    seconds elapsed since current session's CSRF token was created.
    If not, then create new one.

    Return tuple (csrf_token, csrf_token_time).
    """

    csrf_token = session_param_get(req, 'csrf_token')
    csrf_token_time = session_param_get(req, 'csrf_token_time')

    if not csrf_token or not csrf_token_time:
        csrf_token, csrf_token_time = generate_csrf_token(req)

    if csrf_token_time + token_expiry < time.time():
        csrf_token, csrf_token_time = generate_csrf_token(req)

    return (csrf_token, csrf_token_time)


def is_csrf_token_valid(req, token_value, token_expiry=300):
    """Check whether CSRF token is still valid.

    Take CSRF token value from current session and check whether it is
    equal to the passed `token_value`.  Also, check whether it has not
    expired yet, i.e. whether not more than `token_expiry` seconds
    elapsed since current session's CSRF token was created.

    Return True if everything is OK, False otherwise.
    """

    # retrieve CSRF token from session:
    csrf_token = session_param_get(req, 'csrf_token')
    if not csrf_token:
        return False

    # retrieve CSRF token's timestamp from session:
    csrf_token_time = session_param_get(req, 'csrf_token_time')
    if not csrf_token_time:
        return False

    # is session's CSRF token not yet expired?
    if csrf_token_time + token_expiry < time.time():
        return False

    # is session's CSRF token equal to given value?
    if not token_value or token_value != csrf_token:
        return False

    # OK, every test passed, we are good:
    return True
