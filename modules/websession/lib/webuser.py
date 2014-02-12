# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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

from socket import gaierror

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
     CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS, \
     CFG_WEBSESSION_ADDRESS_ACTIVATION_EXPIRE_IN_DAYS, \
     CFG_CERN_SITE, \
     CFG_INSPIRE_SITE, \
     CFG_BIBAUTHORID_ENABLED, \
     CFG_SITE_RECORD

try:
    from invenio.session import get_session
except ImportError:
    pass
from invenio.dbquery import run_sql, OperationalError, \
    serialize_via_marshal, deserialize_via_marshal
from invenio.access_control_admin import acc_get_role_id, acc_get_action_roles, acc_get_action_id, acc_is_user_in_role, acc_find_possible_activities
from invenio.access_control_mailcookie import mail_cookie_create_mail_activation
from invenio.access_control_firerole import acc_firerole_check_user, load_role_definition
from invenio.access_control_config import SUPERADMINROLE, CFG_EXTERNAL_AUTH_USING_SSO
from invenio.messages import gettext_set_language, wash_languages, wash_language
from invenio.mailutils import send_email
from invenio.errorlib import register_exception
from invenio.webgroup_dblayer import get_groups
from invenio.external_authentication import InvenioWebAccessExternalAuthError
from invenio.access_control_config import CFG_EXTERNAL_AUTHENTICATION, \
    CFG_WEBACCESS_MSGS, CFG_WEBACCESS_WARNING_MSGS, CFG_EXTERNAL_AUTH_DEFAULT, \
    CFG_TEMP_EMAIL_ADDRESS
from invenio.webuser_config import CFG_WEBUSER_USER_TABLES
import invenio.template
tmpl = invenio.template.load('websession')

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

    from invenio.webpage import page

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

        except OperationalError, e:
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
    if hasattr(req, '_user_info'):
        return req._user_info['uid']
    if CFG_ACCESS_CONTROL_LEVEL_SITE == 1: return 0
    if CFG_ACCESS_CONTROL_LEVEL_SITE == 2: return -1

    guest = 0
    try:
        session = get_session(req)
    except Exception:
        ## Not possible to obtain a session
        return 0
    uid = session.get('uid', -1)
    if not session.need_https:
        if uid == -1: # first time, so create a guest user
            if CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                uid = session['uid'] = createGuestUser()
                session.set_remember_me(False)
                guest = 1
            else:
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

def setUid(req, uid, remember_me=False):
    """It sets the userId into the session, and raise the cookie to the client.
    """
    if hasattr(req, '_user_info'):
        del req._user_info
    session = get_session(req)
    try:
        guest_personinfo = session['personinfo']
    except KeyError:
        guest_personinfo = dict()
    session.invalidate()
    session = get_session(req)
    # a part of the session before the user logged in (browsing as guest)
    # is copied to the new session
    session['guest_personinfo'] = guest_personinfo
    session['uid'] = uid
    if remember_me:
        session.set_timeout(86400)
    session.set_remember_me(remember_me)
    if uid > 0:
        user_info = collect_user_info(req, login_time=True)
        session['user_info'] = user_info
        req._user_info = user_info
        session.save()
    else:
        del session['user_info']
    return uid

def session_param_del(req, key):
    """
    Remove a given key from the session.
    """
    session = get_session(req)
    del session[key]

def session_param_set(req, key, value):
    """
    Set a VALUE for the session param KEY for the current session.
    """
    session = get_session(req)
    session[key] = value

def session_param_get(req, key, default = None):
    """
    Return session parameter value associated with session parameter KEY for the current session.
    If the key doesn't exists return the provided default.
    """
    session = get_session(req)
    return session.get(key, default)

def session_param_list(req):
    """
    List all available session parameters.
    """
    session = get_session(req)
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
    return acc_find_possible_activities(user_info) != {}

def isUserSuperAdmin(user_info):
    """Return True if the user is superadmin; False otherwise."""
    if run_sql("""SELECT r.id
        FROM accROLE r LEFT JOIN user_accROLE ur
        ON r.id = ur.id_accROLE
        WHERE r.name = %s AND
        ur.id_user = %s AND ur.expiration>=NOW() LIMIT 1""", (SUPERADMINROLE, user_info['uid']), 1, run_on_slave=True):
        return True
    return acc_firerole_check_user(user_info, load_role_definition(acc_get_role_id(SUPERADMINROLE)))

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

        if CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT:
            address_activation_key = mail_cookie_create_mail_activation(
                email,
                cookie_timeout=datetime.timedelta(
                    days=CFG_WEBSESSION_ADDRESS_ACTIVATION_EXPIRE_IN_DAYS
                )
            )
            ip_address = req.remote_host or req.remote_ip
            try:
                if not send_email(CFG_SITE_SUPPORT_EMAIL, email, _("Account registration at %s") % CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME),
                                  tmpl.tmpl_account_address_activation_email_body(email,
                                                  address_activation_key, ip_address, ln)):
                    return 1
            except (smtplib.SMTPException, socket.error):
                return 6

    # okay, go on and register the user:
    user_preference = get_default_user_preferences()
    uid = run_sql("INSERT INTO user (nickname, email, password, note, settings, last_login) "
        "VALUES (%s,%s,AES_ENCRYPT(email,%s),%s,%s, NOW())",
        (nickname, email, passw, activated, serialize_via_marshal(user_preference)))
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
        run_sql("update user set password=AES_ENCRYPT(email,%s) where id=%s", (password, uid))
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
        from invenio.bibauthorid_dbinterface import webuser_merge_user
        webuser_merge_user(id_usera, id_userb)
        index = 0
        table = ''
        try:
            for index, (table, column) in enumerate(CFG_WEBUSER_USER_TABLES):
                run_sql("UPDATE %(table)s SET %(column)s=%%s WHERE %(column)s=%%s; DELETE FROM %(table)s WHERE %(column)s=%%s;" % {
                    'table': table,
                    'column': column
                }, (id_userb, id_usera, id_usera))
        except Exception, err:
            msg = "Error when merging id_user=%s into id_userb=%s for table %s: %s\n" % (id_usera, id_userb, table, err)
            msg += "users where succesfully already merged for tables: %s\n" % ', '.join([table[0] for table in CFG_WEBUSER_USER_TABLES[:index]])
            msg += "users where not succesfully already merged for tables: %s\n" % ', '.join([table[0] for table in CFG_WEBUSER_USER_TABLES[index:]])
            register_exception(alert_admin=True, prefix=msg)
            raise
    finally:
        ## FIXME: locking disabled
        #run_sql("UNLOCK TABLES")
        pass

def loginUser(req, p_un, p_pw, login_method):
    """It is a first simple version for the authentication of user. It returns the id of the user,
       for checking afterwards if the login is correct
    """

    # p_un passed may be an email or a nickname:
    p_email = get_email_from_username(p_un)

    # go on with the old stuff based on p_email:

    if not login_method in CFG_EXTERNAL_AUTHENTICATION:
        return (None, p_email, p_pw, 12)

    if CFG_EXTERNAL_AUTHENTICATION[login_method]: # External Authentication
        try:
            result = CFG_EXTERNAL_AUTHENTICATION[login_method].auth_user(p_email, p_pw, req)
            if (result == (None, None) or result is None) and not login_method in ['oauth1', 'oauth2', 'openid']:
                # There is no need to call auth_user with username for
                # OAuth1, OAuth2 and OpenID authentication
                result = CFG_EXTERNAL_AUTHENTICATION[login_method].auth_user(p_un, p_pw, req) ## We try to login with either the email of the nickname
            if isinstance(result, (tuple, list)) and len(result) == 2:
                p_email, p_extid = result
            else:
                ## For backward compatibility we use the email as external
                ## identifier if it was not returned already by the plugin
                p_email, p_extid = str(result), str(result)

            if p_email:
                p_email = p_email.lower()
                if not p_extid:
                    p_extid = p_email
            elif not p_extid:
                try:
                    # OpenID and OAuth authentications have own error messages
                    return (None, p_email, p_pw, CFG_EXTERNAL_AUTHENTICATION[login_method].get_msg(req))
                except NotImplementedError:
                    return(None, p_email, p_pw, 15)
            else:
                # External login is successfull but couldn't fetch the email
                # address.
                generate_string = lambda: reduce((lambda x, y: x+y), [random.choice("qwertyuiopasdfghjklzxcvbnm1234567890") for i in range(32)])
                random_string = generate_string()
                p_email = CFG_TEMP_EMAIL_ADDRESS % random_string
                while run_sql("SELECT * FROM user WHERE email=%s", (p_email,)):
                    random_string = generate_string()
                    p_email = CFG_TEMP_EMAIL_ADDRESS % random_string

        except InvenioWebAccessExternalAuthError:
            register_exception(req=req, alert_admin=True)
            raise
        if p_email: # Authenthicated externally
            query_result = run_sql("SELECT id_user FROM userEXT WHERE id=%s and method=%s", (p_extid, login_method))
            if query_result:
                ## User was already registered with this external method.
                id_user = query_result[0][0]
                old_email = run_sql("SELECT email FROM user WHERE id=%s", (id_user,))[0][0]

                # Look if the email address matches with the template given.
                # If it matches, use the email address saved in the database.
                regexp = re.compile(CFG_TEMP_EMAIL_ADDRESS % r"\w*")
                if regexp.match(p_email):
                    p_email = old_email

                if old_email != p_email:
                    ## User has changed email of reference.
                    res = run_sql("SELECT id FROM user WHERE email=%s", (p_email,))
                    if res:
                        ## User was also registered with the other email.
                        ## We should merge the two!
                        new_id = res[0][0]
                        if new_id == id_user:
                            raise AssertionError("We should not reach this situation: new_id=%s, id_user=%s, old_email=%s, p_email=%s" % (new_id, id_user, old_email, p_email))
                        merge_usera_into_userb(id_user, new_id)
                        run_sql("DELETE FROM user WHERE id=%s", (id_user, ))
                        for row in run_sql("SELECT method FROM userEXT WHERE id_user=%s", (id_user, )):
                            ## For all known accounts of id_user not conflicting with new_id we move them to refer to new_id
                            if not run_sql("SELECT method FROM userEXT WHERE id_user=%s AND method=%s", (new_id, row[0])):
                                run_sql("UPDATE userEXT SET id_user=%s WHERE id_user=%s AND method=%s", (new_id, id_user, row[0]))
                        ## And we delete the duplicate remaining ones :-)
                        run_sql("DELETE FROM userEXT WHERE id_user=%s", (id_user, ))
                        id_user = new_id
                    else:
                        ## We just need to rename the email address of the
                        ## corresponding user. Unfortunately the local
                        ## password will be then invalid, but its unlikely
                        ## the user is using both an external and a local
                        ## account.
                        run_sql("UPDATE user SET email=%s WHERE id=%s", (p_email, id_user))
            else:
                ## User was not already registered with this external method.
                query_result = run_sql("SELECT id FROM user WHERE email=%s", (p_email, ))
                if query_result:
                    ## The user was already known with this email
                    id_user = query_result[0][0]
                    ## We fix the inconsistence in the userEXT table.
                    run_sql("INSERT INTO userEXT(id, method, id_user) VALUES(%s, %s, %s) ON DUPLICATE KEY UPDATE id=%s, method=%s, id_user=%s", (p_extid, login_method, id_user, p_extid, login_method, id_user))
                else:
                    ## First time user
                    p_pw_local = int(random.random() * 1000000)
                    p_nickname = ''
                    if CFG_EXTERNAL_AUTHENTICATION[login_method].enforce_external_nicknames:
                        try: # Let's discover the external nickname!
                            p_nickname = CFG_EXTERNAL_AUTHENTICATION[login_method].fetch_user_nickname(p_email, p_pw, req)
                        except (AttributeError, NotImplementedError):
                            pass
                        except:
                            register_exception(req=req, alert_admin=True)
                            raise
                    res = registerUser(req, p_email, p_pw_local, p_nickname,
                            register_without_nickname=p_nickname == '',
                            login_method=login_method)
                    if res == 4 or res == 2: # The nickname was already taken
                        res = registerUser(req, p_email, p_pw_local, '',
                        register_without_nickname=True,
                        login_method=login_method)
                        query_result = run_sql("SELECT id from user where email=%s", (p_email,))
                        id_user = query_result[0][0]
                    elif res == 0: # Everything was ok, with or without nickname.
                        query_result = run_sql("SELECT id from user where email=%s", (p_email,))
                        id_user = query_result[0][0]
                    elif res == 6: # error in contacting the user via email
                        return (None, p_email, p_pw_local, 19)
                    else:
                        return (None, p_email, p_pw_local, 13)
                    run_sql("INSERT INTO userEXT(id, method, id_user) VALUES(%s, %s, %s)", (p_extid, login_method, id_user))
            if CFG_EXTERNAL_AUTHENTICATION[login_method].enforce_external_nicknames:
                ## Let's still fetch a possibly upgraded nickname.
                try: # Let's discover the external nickname!
                    p_nickname = CFG_EXTERNAL_AUTHENTICATION[login_method].fetch_user_nickname(p_email, p_pw, req)
                    if nickname_valid_p(p_nickname) and nicknameUnique(p_nickname) == 0:
                        updateDataUser(id_user, p_email, p_nickname)
                except (AttributeError, NotImplementedError):
                    pass
                except:
                    register_exception(alert_admin=True)
                    raise
            try:
                groups = CFG_EXTERNAL_AUTHENTICATION[login_method].fetch_user_groups_membership(p_email, p_pw, req)
                # groups is a dictionary {group_name : group_description,}
                new_groups = {}
                for key, value in groups.items():
                    new_groups[key + " [" + str(login_method) + "]"] = value
                groups = new_groups
            except (AttributeError, NotImplementedError):
                pass
            except:
                register_exception(req=req, alert_admin=True)
                return (None, p_email, p_pw, 16)
            else: # Groups synchronization
                if groups:
                    from invenio.webgroup import synchronize_external_groups
                    synchronize_external_groups(id_user, groups, login_method)

            user_prefs = get_user_preferences(id_user)
            if not CFG_EXTERNAL_AUTHENTICATION[login_method]:
                ## I.e. if the login method is not of robot type:
                if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 4:
                    # Let's prevent the user to switch login_method
                    if user_prefs.has_key("login_method") and \
                            user_prefs["login_method"] != login_method:
                        return (None, p_email, p_pw, 11)
                user_prefs["login_method"] = login_method

            # Cleaning external settings
            for key in user_prefs.keys():
                if key.startswith('EXTERNAL_'):
                    del user_prefs[key]
            try:
                # Importing external settings
                new_prefs = CFG_EXTERNAL_AUTHENTICATION[login_method].fetch_user_preferences(p_email, p_pw, req)
                for key, value in new_prefs.items():
                    user_prefs['EXTERNAL_' + key] = value
            except (AttributeError, NotImplementedError):
                pass
            except InvenioWebAccessExternalAuthError:
                register_exception(req=req, alert_admin=True)
                return (None, p_email, p_pw, 16)
            # Storing settings
            set_user_preferences(id_user, user_prefs)
        else:
            return (None, p_un, p_pw, 10)
    else: # Internal Authenthication
        if not p_pw:
            p_pw = ''
        query_result = run_sql("SELECT id,email,note from user where email=%s and password=AES_ENCRYPT(email,%s)", (p_email, p_pw,))
        if query_result:
            #FIXME drop external groups and settings
            note = query_result[0][2]
            id_user = query_result[0][0]
            if note == '1': # Good account
                preferred_login_method = get_user_preferences(query_result[0][0])['login_method']
                p_email = query_result[0][1].lower()
                if login_method != preferred_login_method:
                    if preferred_login_method in CFG_EXTERNAL_AUTHENTICATION:
                        return (None, p_email, p_pw, 11)
            elif note == '2': # Email address need to be confirmed by user
                return (None, p_email, p_pw, 17)
            elif note == '0': # Account need to be confirmed by administrator
                return (None, p_email, p_pw, 18)
        else:
            return (None, p_email, p_pw, 14)
    # Login successful! Updating the last access time
    run_sql("UPDATE user SET last_login=NOW() WHERE email=%s", (p_email,))
    return (id_user, p_email, p_pw, 0)


def drop_external_settings(userId):
    """Drop the external (EXTERNAL_) settings of userid."""
    prefs = get_user_preferences(userId)
    for key in prefs.keys():
        if key.startswith('EXTERNAL_'):
            del prefs[key]
    set_user_preferences(userId, prefs)

def logoutUser(req):
    """It logout the user of the system, creating a guest user.
    """
    session = get_session(req)
    if CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
        uid = createGuestUser()
        session['uid'] = uid
        session.set_remember_me(False)
        session.save()
    else:
        uid = 0
        session.invalidate()
    if hasattr(req, '_user_info'):
        delattr(req, '_user_info')
    return uid

def username_exists_p(username):
    """Check if USERNAME exists in the system.  Username may be either
    nickname or email.

    Return 1 if it does exist, 0 if it does not.
    """

    if username == "":
        # return not exists if asked for guest users
        return 0
    res = run_sql("SELECT email FROM user WHERE email=%s", (username,)) + \
          run_sql("SELECT email FROM user WHERE nickname=%s", (username,))
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

def nicknameUnique(p_nickname):
    """Check if the nickname only exists once. If yes, return userid, if not, -1
    """

    query_result = run_sql("select id, nickname from user where nickname=%s", (p_nickname,))
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

def create_useractivities_menu(req, uid, navmenuid, ln="en"):
    """Create user activities menu.

    @param req: request object
    @param uid: user id
    @type uid: int
    @param navmenuid: the section of the website this page belongs (search, submit, baskets, etc.)
    @type navmenuid: string
    @param ln: language
    @type ln: string
    @return: HTML menu of the user activities
    @rtype: string
    """

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

    is_user_menu_selected = False
    if navmenuid == 'personalize' or  \
       navmenuid.startswith('your') and \
       navmenuid != 'youraccount':
        is_user_menu_selected = True

    try:
        return tmpl.tmpl_create_useractivities_menu(
            ln=ln,
            selected=is_user_menu_selected,
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
            usestats=user_info['precached_usestats'],
            usecomments=user_info['precached_sendcomments'],
            )
    except OperationalError:
        return ""

def create_adminactivities_menu(req, uid, navmenuid, ln="en"):
    """Create admin activities menu.

    @param req: request object
    @param uid: user id
    @type uid: int
    @param navmenuid: the section of the website this page belongs (search, submit, baskets, etc.)
    @type navmenuid: string
    @param ln: language
    @type ln: string
    @return: HTML menu of the user activities
    @rtype: string
    """
    _ = gettext_set_language(ln)
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
    activities = acc_find_possible_activities(user_info, ln)

    # For BibEdit and BibDocFile menu items, take into consideration
    # current record whenever possible
    if activities.has_key(_("Run Record Editor")) or \
           activities.has_key(_("Run Document File Manager")) and \
           user_info['uri'].startswith('/' + CFG_SITE_RECORD + '/'):
        try:
            # Get record ID and try to cast it to an int
            current_record_id = int(urlparse.urlparse(user_info['uri'])[2].split('/')[2])
        except:
            pass
        else:
            if activities.has_key(_("Run Record Editor")):
                activities[_("Run Record Editor")] = activities[_("Run Record Editor")] + '&amp;#state=edit&amp;recid=' + str(current_record_id)
            if activities.has_key(_("Run Document File Manager")):
                activities[_("Run Document File Manager")] = activities[_("Run Document File Manager")] + '&amp;recid=' + str(current_record_id)

    try:
        return tmpl.tmpl_create_adminactivities_menu(
            ln=ln,
            selected=navmenuid == 'admin',
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
            usestats=user_info['precached_usestats'],
            activities=activities
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

def get_uid_based_on_pref(prefname, prefvalue):
    """get the user's UID based where his/her preference prefname has value prefvalue in preferences"""
    prefs = run_sql("SELECT id, settings FROM user WHERE settings is not NULL")
    the_uid = None
    for pref in prefs:
        try:
            settings = deserialize_via_marshal(pref[1])
            if (settings.has_key(prefname)) and (settings[prefname] == prefvalue):
                the_uid = pref[0]
        except:
            pass
    return the_uid

def get_user_preferences(uid):
    pref = run_sql("SELECT settings FROM user WHERE id=%s", (uid,))
    if pref and pref[0][0]:
        return deserialize_via_marshal(pref[0][0])
    return get_default_user_preferences() # empty dict mean no preferences

def set_user_preferences(uid, pref):
    assert(type(pref) == type({}))
    run_sql("UPDATE user SET settings=%s WHERE id=%s",
            (serialize_via_marshal(pref), uid))

def get_default_user_preferences():
    user_preference = {
        'login_method': ''}

    if CFG_EXTERNAL_AUTH_DEFAULT in CFG_EXTERNAL_AUTHENTICATION:
        user_preference['login_method'] = CFG_EXTERNAL_AUTH_DEFAULT
    return user_preference

def get_preferred_user_language(req):
    def _get_language_from_req_header(accept_language_header):
        """Extract langs info from req.headers_in['Accept-Language'] which
        should be set to something similar to:
        'fr,en-us;q=0.7,en;q=0.3'
        """
        tmp_langs = {}
        for lang in accept_language_header.split(','):
            lang = lang.split(';q=')
            if len(lang) == 2:
                lang[1] = lang[1].replace('"', '') # Hack for Yeti robot
                try:
                    tmp_langs[float(lang[1])] = lang[0]
                except ValueError:
                    pass
            else:
                tmp_langs[1.0] = lang[0]
        ret = []
        priorities = tmp_langs.keys()
        priorities.sort()
        priorities.reverse()
        for priority in priorities:
            ret.append(tmp_langs[priority])
        return ret

    uid = getUid(req)
    guest = isGuestUser(uid)
    new_lang = None
    preferred_lang = None

    if not guest:
        user_preferences = get_user_preferences(uid)
        preferred_lang = new_lang = user_preferences.get('language', None)

    if not new_lang:
        try:
            new_lang = wash_languages(cgi.parse_qs(req.args)['ln'])
        except (TypeError, AttributeError, KeyError):
            pass

    if not new_lang:
        try:
            new_lang = wash_languages(_get_language_from_req_header(req.headers_in['Accept-Language']))
        except (TypeError, AttributeError, KeyError):
            pass

    new_lang = wash_language(new_lang)

    if new_lang != preferred_lang and not guest:
        user_preferences['language'] = new_lang
        set_user_preferences(uid, user_preferences)

    return new_lang

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
    from invenio.search_engine import get_permitted_restricted_collections
    user_info = {
        'remote_ip' : '',
        'remote_host' : '',
        'referer' : '',
        'uri' : '',
        'agent' : '',
        'uid' :-1,
        'nickname' : '',
        'email' : '',
        'group' : [],
        'guest' : '1',
        'session' : None,
        'precached_permitted_restricted_collections' : [],
        'precached_usebaskets' : False,
        'precached_useloans' : False,
        'precached_usegroups' : False,
        'precached_usealerts' : False,
        'precached_usemessages' : False,
        'precached_viewsubmissions' : False,
        'precached_useapprove' : False,
        'precached_useadmin' : False,
        'precached_usestats' : False,
        'precached_viewclaimlink' : False,
        'precached_usepaperclaim' : False,
        'precached_usepaperattribution' : False,
        'precached_canseehiddenmarctags' : False,
        'precached_sendcomments' : False,
    }

    try:
        is_req = False
        if not req:
            uid = -1
        elif type(req) in (type(1), type(1L)):
            ## req is infact a user identification
            uid = req
        elif type(req) is dict:
            ## req is by mistake already a user_info
            try:
                assert(req.has_key('uid'))
                assert(req.has_key('email'))
                assert(req.has_key('nickname'))
            except AssertionError:
                ## mmh... misuse of collect_user_info. Better warn the admin!
                register_exception(alert_admin=True)
            user_info.update(req)
            return user_info
        else:
            is_req = True
            uid = getUid(req)
            if hasattr(req, '_user_info') and not login_time:
                user_info = req._user_info
                if not refresh:
                    return req._user_info
            req._user_info = user_info
            try:
                user_info['remote_ip'] = req.remote_ip
            except gaierror:
                #FIXME: we should support IPV6 too. (hint for FireRole)
                pass
            user_info['session'] = get_session(req).sid()
            user_info['remote_host'] = req.remote_host or ''
            user_info['referer'] = req.headers_in.get('Referer', '')
            user_info['uri'] = req.unparsed_uri or ()
            user_info['agent'] = req.headers_in.get('User-Agent', 'N/A')
        user_info['uid'] = uid
        user_info['nickname'] = get_nickname(uid) or ''
        user_info['email'] = get_email(uid) or ''
        user_info['group'] = []
        user_info['guest'] = str(isGuestUser(uid))

        if user_info['guest'] == '1' and CFG_INSPIRE_SITE:
            usepaperattribution = False
            viewclaimlink = False

            if (CFG_BIBAUTHORID_ENABLED
                and acc_is_user_in_role(user_info, acc_get_role_id("paperattributionviewers"))):
                usepaperattribution = True

#            if (CFG_BIBAUTHORID_ENABLED
#                and usepaperattribution
#                and acc_is_user_in_role(user_info, acc_get_role_id("paperattributionlinkviewers"))):
#                viewclaimlink = True
            if is_req:
                session = get_session(req)
                viewlink = False
                try:
                    viewlink = session['personinfo']['claim_in_process']
                except (KeyError, TypeError):
                    viewlink = False
            else:
                viewlink = False

            if (CFG_BIBAUTHORID_ENABLED
                and usepaperattribution
                and viewlink):
                viewclaimlink = True

            user_info['precached_viewclaimlink'] = viewclaimlink
            user_info['precached_usepaperattribution'] = usepaperattribution

        if user_info['guest'] == '0':
            user_info['group'] = [group[1] for group in get_groups(uid)]
            prefs = get_user_preferences(uid)
            try:
                login_method = prefs['login_method']
            except KeyError:
                # login_method is missing for some reason, bad news..
                msg = "Data error: The mandatory key 'login_method' is missing"
                register_exception(prefix=msg,
                                   alert_admin=True)
                login_method = get_default_user_preferences()['login_method']
            ## NOTE: we fall back to default login_method if the login_method
            ## specified in the user settings does not exist (e.g. after
            ## a migration.)
            login_object = CFG_EXTERNAL_AUTHENTICATION.get(login_method, CFG_EXTERNAL_AUTHENTICATION[CFG_EXTERNAL_AUTH_DEFAULT])
            if login_object and ((datetime.datetime.now() - get_last_login(uid)).seconds > 3600):
                ## The user uses an external authentication method and it's a bit since
                ## she has not performed a login
                if not CFG_EXTERNAL_AUTH_USING_SSO or (
                    is_req and login_object.in_shibboleth(req)):
                    ## If we're using SSO we must be sure to be in HTTPS and Shibboleth handler
                    ## otherwise we can't really read anything, hence
                    ## it's better skip the synchronization
                    try:
                        groups = login_object.fetch_user_groups_membership(user_info['email'], req=req)
                        # groups is a dictionary {group_name : group_description,}
                        new_groups = {}
                        for key, value in groups.items():
                            new_groups[key + " [" + str(login_method) + "]"] = value
                        groups = new_groups
                    except (AttributeError, NotImplementedError, TypeError, InvenioWebAccessExternalAuthError):
                        pass
                    else: # Groups synchronization
                        from invenio.webgroup import synchronize_external_groups
                        synchronize_external_groups(uid, groups, login_method)
                        user_info['group'] = [group[1] for group in get_groups(uid)]

                    try:
                        # Importing external settings
                        new_prefs = login_object.fetch_user_preferences(user_info['email'], req=req)
                        for key, value in new_prefs.items():
                            prefs['EXTERNAL_' + key] = value
                    except (AttributeError, NotImplementedError, TypeError, InvenioWebAccessExternalAuthError):
                        pass
                    else:
                        set_user_preferences(uid, prefs)
                        prefs = get_user_preferences(uid)

                    run_sql('UPDATE user SET last_login=NOW() WHERE id=%s', (uid,))
            if prefs:
                for key, value in prefs.iteritems():
                    user_info[key.lower()] = value
            if login_time:
                ## Heavy computational information
                from invenio.access_control_engine import acc_authorize_action
                user_info['precached_permitted_restricted_collections'] = get_permitted_restricted_collections(user_info)
                user_info['precached_usebaskets'] = acc_authorize_action(user_info, 'usebaskets')[0] == 0
                user_info['precached_useloans'] = acc_authorize_action(user_info, 'useloans')[0] == 0
                user_info['precached_usegroups'] = acc_authorize_action(user_info, 'usegroups')[0] == 0
                user_info['precached_usealerts'] = acc_authorize_action(user_info, 'usealerts')[0] == 0
                user_info['precached_usemessages'] = acc_authorize_action(user_info, 'usemessages')[0] == 0
                user_info['precached_usestats'] = acc_authorize_action(user_info, 'runwebstatadmin')[0] == 0
                user_info['precached_viewsubmissions'] = isUserSubmitter(user_info)
                user_info['precached_useapprove'] = isUserReferee(user_info)
                user_info['precached_useadmin'] = isUserAdmin(user_info)
                user_info['precached_canseehiddenmarctags'] = acc_authorize_action(user_info, 'runbibedit')[0] == 0
                user_info['precached_sendcomments'] = acc_authorize_action(user_info, 'sendcomment', '*')[0] == 0
                usepaperclaim = False
                usepaperattribution = False
                viewclaimlink = False

                if (CFG_BIBAUTHORID_ENABLED
                    and acc_is_user_in_role(user_info, acc_get_role_id("paperclaimviewers"))):
                    usepaperclaim = True

                if (CFG_BIBAUTHORID_ENABLED
                    and acc_is_user_in_role(user_info, acc_get_role_id("paperattributionviewers"))):
                    usepaperattribution = True

                if is_req:
                    session = get_session(req)
                    viewlink = False
                    try:
                        viewlink = session['personinfo']['claim_in_process']
                    except (KeyError, TypeError):
                        viewlink = False
                else:
                    viewlink = False

                if (CFG_BIBAUTHORID_ENABLED
                    and usepaperattribution
                    and viewlink):
                    viewclaimlink = True

#                if (CFG_BIBAUTHORID_ENABLED
#                    and ((usepaperclaim or usepaperattribution)
#                         and acc_is_user_in_role(user_info, acc_get_role_id("paperattributionlinkviewers")))):
#                    viewclaimlink = True

                user_info['precached_viewclaimlink'] = viewclaimlink
                user_info['precached_usepaperclaim'] = usepaperclaim
                user_info['precached_usepaperattribution'] = usepaperattribution

    except Exception, e:
        register_exception()
    return user_info
