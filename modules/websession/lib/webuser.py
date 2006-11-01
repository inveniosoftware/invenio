# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
This file implements all methods necessary for working with users and
sessions in CDS Invenio.  Contains methods for logging/registration
when a user log/register into the system, checking if it is a guest
user or not.

At the same time this presents all the stuff it could need with
sessions managements, working with websession.

It also contains Apache-related user authentication stuff.
"""

__revision__ = "$Id$"

from marshal import loads, dumps
from zlib import compress, decompress
import time
import os
import crypt
import string
import smtplib
import sre

from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS, \
     CFG_ACCESS_CONTROL_LEVEL_GUESTS, \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN, \
     CFG_ACCESS_CONTROL_NOTIFY_ADMIN_ABOUT_NEW_ACCOUNTS, \
     CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT, \
     CFG_APACHE_GROUP_FILE, \
     CFG_APACHE_PASSWORD_FILE, \
     adminemail, \
     cdslang, \
     cdsname, \
     supportemail, \
     sweburl, \
     tmpdir, \
     version, \
     weburl
from invenio import session, websession
from invenio.dbquery import run_sql, escape_string, OperationalError
from invenio.websession import pSession, pSessionMapping
from invenio.session import SessionError
from invenio.access_control_config import *
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_admin import acc_findUserRoleActions
from invenio.messages import gettext_set_language
import invenio.template
tmpl = invenio.template.load('websession')

sre_invalid_nickname = sre.compile(""".*[,'@]+.*""")

# pylint: disable-msg=C0301

def createGuestUser():
    """Create a guest user , insert into user null values in all fields

       createGuestUser() -> GuestUserID
    """
    if CFG_ACCESS_CONTROL_LEVEL_GUESTS == 0:
        try:
            return run_sql("insert into user (email, note) values ('', '1')")
        except OperationalError:
            return None
            
    elif CFG_ACCESS_CONTROL_LEVEL_GUESTS >= 1:
        try:
            return run_sql("insert into user (email, note) values ('', '0')")
        except OperationalError:
            return None

def page_not_authorized(req, referer='', uid='', text='', navtrail='', ln=cdslang):
    """Show error message when account is not activated"""

    from invenio.webpage import page

    _ = gettext_set_language(ln)

    if not CFG_ACCESS_CONTROL_LEVEL_SITE:
        title = CFG_WEBACCESS_MSGS[5]
        if not uid:
            uid = getUid(req)
        try:
            res = run_sql("SELECT email FROM user WHERE id=%s" % uid)

            if res and res[0][0]:
                if text:
                    body = text
                else:
                    body = "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[9] % res[0][0],
                                      ("%s %s" % (CFG_WEBACCESS_MSGS[0] % referer, CFG_WEBACCESS_MSGS[1])))
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
                uid=getUid(req),
                body=body,
                navtrail=navtrail,
                req=req)

def getUid (req):
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

    if CFG_ACCESS_CONTROL_LEVEL_SITE == 1: return 0
    if CFG_ACCESS_CONTROL_LEVEL_SITE == 2: return -1

    guest = 0
    sm = session.MPSessionManager(pSession, pSessionMapping())
    try:
        s = sm.get_session(req)
    except SessionError:
        sm.revoke_session_cookie (req)
        s = sm.get_session(req)
    userId = s.getUid()
    if userId == -1: # first time, so create a guest user
        s.setUid(createGuestUser())
        userId = s.getUid()
        guest = 1
    sm.maintain_session(req, s)

    if guest == 0:
        guest = isGuestUser(userId)

    if guest:
        if CFG_ACCESS_CONTROL_LEVEL_GUESTS == 0:
            return userId
        elif CFG_ACCESS_CONTROL_LEVEL_GUESTS >= 1:
            return -1
    else:
        res = run_sql("SELECT note FROM user WHERE id=%s" % userId)
        if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS == 0:
            return userId
        elif CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 1 and res and res[0][0] in [1, "1"]:
            return userId
        else:
            return -1

def setUid(req, uid):
    """It sets the userId into the session, and raise the cookie to the client.
    """
    sm = session.MPSessionManager(pSession, pSessionMapping())
    try:
        s = sm.get_session(req)
    except SessionError:
        sm.revoke_session_cookie(req)
        s = sm.get_session(req)
    s.setUid(uid)
    sm.maintain_session(req, s)
    return uid

def get_user_info(uid, ln=cdslang):
    """Get infos for a given user.
    @param uid: user id (int)
    @return tuple: (uid, nickname, display_name)
    """
    _ = gettext_set_language(ln)
    query = """SELECT id, nickname
               FROM user
               WHERE id=%i"""
    res = run_sql(query%uid)
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

def isGuestUser(uid):
    """It Checks if the userId corresponds to a guestUser or not

       isGuestUser(uid) -> boolean
    """
    out = 1
    try:
        res = run_sql("select email from user where id=%s", (uid,))
        if res:
            if res[0][0]:
                out = 0
    except OperationalError:
        pass
    return out

def isUserSubmitter(uid):
    u_email = get_email(uid)
    res = run_sql("select * from sbmSUBMISSIONS where email=%s", (u_email,))
    if len(res) > 0:
        return 1
    else:
        return 0

def isUserReferee(uid):
    res = run_sql("select sdocname from sbmDOCTYPE")
    for row in res:
        doctype = row[0]
        categ = "*"
        (auth_code, auth_message) = acc_authorize_action(uid, "referee", doctype=doctype, categ=categ)
        if auth_code == 0:
            return 1
        res2 = run_sql("select sname from sbmCATEGORIES where doctype=%s", (doctype,))
        for row2 in res2:
            categ = row2[0]
            (auth_code, auth_message) = acc_authorize_action(uid, "referee", doctype=doctype, categ=categ)
            if auth_code == 0:
                return 1
    return 0

def isUserAdmin(uid):
    "Return 1 if the user UID has some admin rights; 0 otherwise."
    out = 0
    if acc_findUserRoleActions(uid):
        out = 1
    return out

def nickname_valid_p(nickname):
    """Check whether wanted NICKNAME supplied by the user is valid.
       At the moment we just check whether it is not empty, does not
       contain blanks or @, is not equal to `guest', etc.
      
       This check relies on sre_invalid_nickname regexp (see above)
       Return 1 if nickname is okay, return 0 if it is not.
    """
    if nickname and \
       not(nickname.startswith(' ') or nickname.endswith(' ')) and \
       nickname.lower() != 'guest':
        if not sre_invalid_nickname.match(nickname):
            return 1
    return 0

def email_valid_p(email):
    """Check whether wanted EMAIL address supplied by the user is valid.
       At the moment we just check whether it contains '@' and whether
       it doesn't contain blanks.  We also check the email domain if
       CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN is set.

       Return 1 if email is okay, return 0 if it is not.
    """
    if (string.find(email, "@") <= 0) or (string.find(email, " ") > 0):
        return 0
    elif CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN:
        if not email.endswith(CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN):
            return 0
    return 1

def registerUser(req, email, passw, nickname, register_without_nickname=False):
    """Register user with the desired values of NICKNAME, EMAIL and
       PASSW.

       If REGISTER_WITHOUT_NICKNAME is set to True, then ignore
       desired NICKNAME and do not set any.  This is suitable for
       external authentications so that people can login without
       having to register an internal account first.
       
       Return 0 if the registration is successful, 1 if email is not
       valid, 2 if nickname is not valid, 3 if email is already in the
       database, 4 if nickname is already in the database, 5 when
       users cannot register themselves because of the site policy.
       """

    # is email valid?
    if not email_valid_p(email):
        return 1

    # is email already taken?
    res = run_sql("SELECT * FROM user WHERE email=%s", (email,))
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
        res = run_sql("SELECT * FROM user WHERE nickname=%s", (nickname,))
        if len(res) > 0:
            return 4

    # okay, go on and register the user:
    if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS == 0:
        activated = 1
    elif CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS == 1:
        activated = 0
    elif CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 2:
        return 5

    user_preference = get_default_user_preferences()

    setUid(req, run_sql("INSERT INTO user (nickname, email, password, note, settings) VALUES (%s,%s,%s,%s,%s)",
                        (nickname, email, passw, activated, serialize_via_marshal(user_preference),)))

    if CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT:
        sendNewUserAccountWarning(email, email, passw)
    if CFG_ACCESS_CONTROL_NOTIFY_ADMIN_ABOUT_NEW_ACCOUNTS:
        sendNewAdminAccountWarning(email, adminemail)
    return 0

def updateDataUser(uid, email, password, nickname):
    """Update user data.  Used when a user changed his email or password or nickname.
    """
    if email == 'guest':
        return 0

    if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 2:
        run_sql("update user set password=%s where id=%s", (password, uid))
    else:
        run_sql("update user set email=%s,password=%s where id=%s", (email, password, uid))
    if nickname and nickname != '':
        run_sql("update user set nickname=%s where id=%s", (nickname, uid))
    return 1

def loginUser(req, p_un, p_pw, login_method):
    """It is a first simple version for the authentication of user. It returns the id of the user,
       for checking afterwards if the login is correct
    """

    # p_un passed may be an email or a nickname:
    p_email = get_email_from_username(p_un)

    # go on with the old stuff based on p_email:
    user_prefs = get_user_preferences(emailUnique(p_email))
    if user_prefs and login_method != user_prefs["login_method"]:
        if CFG_EXTERNAL_AUTHENTICATION.has_key(user_prefs["login_method"]):
            return ([], p_email, p_pw, 11)

    if not CFG_EXTERNAL_AUTHENTICATION.has_key(login_method):
        return ([], p_email, p_pw, 12)

    if CFG_EXTERNAL_AUTHENTICATION[login_method][0]:
        p_email = CFG_EXTERNAL_AUTHENTICATION[login_method][0].auth_user(p_email, p_pw)
        if p_email:
            p_pw = givePassword(p_email)
            if not p_pw or p_pw < 0:
                import random
                p_pw = int(random.random() * 1000000)
                if registerUser(req, p_email, p_pw, "", register_without_nickname=True) != 0:
                    return ([], p_email, p_pw, 13)
                else:
                    query_result = run_sql("SELECT id from user where email=%s and password=%s", (p_email, p_pw,))
                    user_prefs = get_user_preferences(query_result[0][0])
                    user_prefs["login_method"] = login_method
                    set_user_preferences(query_result[0][0], user_prefs)
        else:
            return ([], p_email, p_pw, 10)

    query_result = run_sql("SELECT id from user where email=%s and password=%s", (p_email, p_pw,))
    if query_result:
        prefered_login_method = get_user_preferences(query_result[0][0])['login_method']
    else:
        return ([], p_email, p_pw, 14)

    if login_method != prefered_login_method:
        if CFG_EXTERNAL_AUTHENTICATION.has_key(prefered_login_method):
            return ([], p_email, p_pw, 11)

    return (query_result, p_email, p_pw, 0)

def logoutUser(req):
    """It logout the user of the system, creating a guest user.
    """
    getUid(req)
    sm = session.MPSessionManager(pSession, pSessionMapping())
    try:
        s = sm.get_session(req)
    except SessionError:
        sm.revoke_session_cookie(req)
        s = sm.get_session(req)
    id1 = createGuestUser()
    s.setUid(id1)
    sm.maintain_session(req, s)
    return id1

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

def update_Uid(req, p_email, p_pw):
    """It updates the userId of the session. It is used when a guest user is logged in succesfully in the system
    with a given email and password
    """
    query_ID = int(run_sql("select id from user where email=%s and password=%s",
                           (p_email, p_pw))[0][0])
    setUid(req, query_ID)
    return query_ID

def givePassword(email):
    """ It checks in the database the password for a given email. It is used to send the password to the email of the user.It returns
	the password if the user exists, otherwise it returns -999
    """

    query_pass = run_sql("select password from user where email =%s", (email,))
    if len(query_pass)>0:
        return query_pass[0][0]
    return -999

def sendNewAdminAccountWarning(newAccountEmail, sendTo, ln=cdslang):
    """Send an email to the address given by sendTo about the new account newAccountEmail."""
    _ = gettext_set_language(ln)
    fromaddr = "From: %s" % supportemail
    toaddrs  = "To: %s" % sendTo
    to = toaddrs + "\n"
    sub = "Subject: New account on '%s'" % cdsname
    if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS == 1:
        sub += " - PLEASE ACTIVATE"
    sub += "\n\n"
    body = "A new account has been created on '%s'" % cdsname
    if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS == 1:
        body += " and is awaiting activation"
    body += ":\n\n"
    body += "   Username/Email: %s\n\n" % newAccountEmail
    body += "You can approve or reject this account request at: %s/admin/webaccess/webaccessadmin.py/manageaccounts\n" % weburl
    body += "\n---------------------------------"
    body += "\n%s" % cdsname
    body += "\nContact: %s" % supportemail
    msg = to + sub + body

    server = smtplib.SMTP('localhost')
    server.set_debuglevel(1)

    try:
        server.sendmail(fromaddr, toaddrs, msg)
    except smtplib.SMTPRecipientsRefused:
        return 0

    server.quit()
    return 1

def sendNewUserAccountWarning(newAccountEmail, sendTo, password, ln=cdslang):
    """Send an email to the address given by sendTo about the new account newAccountEmail."""
    _ = gettext_set_language(ln)
    fromaddr = "From: %s" % supportemail
    toaddrs  = "To: %s" % sendTo
    to = toaddrs + "\n"
    sub = "Subject: Your account created on '%s'\n\n" % cdsname
    body = "You have created a new account on '%s':\n\n" % cdsname
    body += "   Username/Email: %s\n" % newAccountEmail
    body += "   Password: %s\n\n" % ("*" * len(password))
    if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 1:
        body += "This account is awaiting approval by the site administrators and therefore cannot be used as of yet.\nYou will receive an email notification as soon as your account request has been processed.\n"
    body += "\n---------------------------------"
    body += "\n%s" % cdsname
    body += "\nContact: %s" % supportemail
    msg = to + sub + body

    server = smtplib.SMTP('localhost')
    server.set_debuglevel(1)

    try:
        server.sendmail(fromaddr, toaddrs, msg)
    except smtplib.SMTPRecipientsRefused:
        return 0

    server.quit()
    return 1

def get_email(uid):
    """Return email address of the user uid.  Return string 'guest' in case
    the user is not found."""
    out = "guest"
    res = run_sql("SELECT email FROM user WHERE id=%s", (uid,), 1)
    if res and res[0][0]:
        out = res[0][0]
    return out

def get_email_from_username(username):
    """Return email address of the user corresponding to USERNAME.
    The username may be either nickname or email.  Return USERNAME
    untouched if not found in the database or if found several
    matching entries.
    """
    out = username
    res = run_sql("SELECT email FROM user WHERE email=%s", (username,), 1) + \
          run_sql("SELECT email FROM user WHERE nickname=%s", (username,), 1)
    if res and len(res) == 1:
        out = res[0][0]
    return out

def get_password(uid):
    """Return password of the user uid.  Return None in case
    the user is not found."""
    out = None
    res = run_sql("SELECT password FROM user WHERE id=%s", (uid,), 1)
    if res and res[0][0]:
        out = res[0][0]
    return out

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
            out = res[0][1]
    return out

def create_userinfobox_body(req, uid, language="en"):
    """Create user info box body for user UID in language LANGUAGE."""

    if req:
        if req.subprocess_env.has_key('HTTPS') \
           and req.subprocess_env['HTTPS'] == 'on':
            url_referer = sweburl + req.unparsed_uri
        else:
            url_referer = weburl + req.unparsed_uri
    else:
        url_referer = weburl
        
    try:
        return tmpl.tmpl_create_userinfobox(ln=language,
                                            url_referer=url_referer,
                                            guest = isGuestUser(uid),
                                            username = get_nickname_or_email(uid),
                                            submitter = isUserSubmitter(uid),
                                            referee = isUserReferee(uid),
                                            admin = isUserAdmin(uid),
                                            )
    except OperationalError:
        return ""

def list_registered_users():
    """List all registered users."""
    return run_sql("SELECT id,email FROM user where email!=''")

def list_users_in_role(role):
    """List all users of a given role (see table accROLE)
    @param role: role of user (string)
    @return list of uids
    """
    query = """SELECT uacc.id_user
               FROM user_accROLE uacc JOIN accROLE acc
                    ON uacc.id_accROLE=acc.id
               WHERE acc.name='%s'"""
    res = run_sql(query% escape_string(role))
    if res:
        return map(lambda x: int(x[0]), res)
    return []

def list_users_in_roles(role_list):
    """List all users of given roles (see table accROLE)
    @param role_list: list of roles [string]
    @return list of uids
    """
    if not(type(role_list) is list or type(role_list) is tuple):
        role_list = [role_list]
    params = ''
    query = """SELECT distinct(uacc.id_user)
               FROM user_accROLE uacc JOIN accROLE acc
                    ON uacc.id_accROLE=acc.id
               %s"""
    if len(role_list) > 0:
        params = 'WHERE '
        for role in role_list[:-1]:
            params += "acc.name='%s' OR " % escape_string(role)
        params += "acc.name='%s'" % escape_string(role_list[-1])
    res = run_sql(query% params)
    if res:
        return map(lambda x: int(x[0]), res)
    return []

## --- follow some functions for Apache user/group authentication

def auth_apache_user_p(user, password, apache_password_file=CFG_APACHE_PASSWORD_FILE):
    """Check whether user-supplied credentials correspond to valid
    Apache password data file.  Return 0 in case of failure, 1 in case
    of success."""
    try:
        if not apache_password_file.startswith("/"):
            apache_password_file = tmpdir + "/" + apache_password_file
        dummy, pipe_output = os.popen2(["grep", "^" + user + ":", apache_password_file], 'r')
        line =  pipe_output.readlines()[0]
        password_apache = string.split(string.strip(line),":")[1]
    except: # no pw found, so return not-allowed status
        return 0
    salt = password_apache[:2]
    if crypt.crypt(password, salt) == password_apache:
        return 1
    else:
        return 0

def auth_apache_user_in_groups(user, apache_group_file=CFG_APACHE_GROUP_FILE):
    """Return list of Apache groups to which Apache user belong."""
    out = []
    try:
        if not apache_group_file.startswith("/"):
            apache_group_file = tmpdir + "/" + apache_group_file
        dummy, pipe_output = os.popen2(["grep", user, apache_group_file], 'r')
        for line in pipe_output.readlines():
            out.append(string.split(string.strip(line),":")[0])
    except: # no groups found, so return empty list
        pass
    return out

def auth_apache_user_collection_p(user, password, coll):
    """Check whether user-supplied credentials correspond to valid
    Apache password data file, and whether this user is authorized to
    see the given collections.  Return 0 in case of failure, 1 in case
    of success."""
    from invenio.search_engine import coll_restricted_p, coll_restricted_group
    if not auth_apache_user_p(user, password):
        return 0
    if not coll_restricted_p(coll):
        return 1
    if coll_restricted_group(coll) in auth_apache_user_in_groups(user):
        return 1
    else:
        return 0

def get_user_preferences(uid):
    pref = run_sql("SELECT id, settings FROM user WHERE id=%s", (uid,))
    if pref:
        try:
            return deserialize_via_marshal(pref[0][1])
        except:
            return get_default_user_preferences()

    return None

def set_user_preferences(uid, pref):
    run_sql("UPDATE user SET settings='%s' WHERE id=%s" % (serialize_via_marshal(pref), uid))

def get_default_user_preferences():
    user_preference = {
        'login_method': ''}

    for system in CFG_EXTERNAL_AUTHENTICATION.keys():
        if CFG_EXTERNAL_AUTHENTICATION[system][1]:
            user_preference['login_method'] = system
            break
    return user_preference

def serialize_via_marshal(obj):
    """Serialize Python object via marshal into a compressed string."""
    return escape_string(compress(dumps(obj)))
def deserialize_via_marshal(string):
    """Decompress and deserialize string into a Python object via marshal."""
    return loads(decompress(string))
