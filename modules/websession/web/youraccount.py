# -*- coding: utf-8 -*-
## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""CDSware ACCOUNT HANDLING"""

__lastupdated__ = """$Date$"""

import sys
from mod_python import apache
import smtplib

from cdsware import webuser
from cdsware.config import weburl, cdsname, cdslang, supportemail
from cdsware.webpage import page
from cdsware import webaccount
from cdsware import webbasket
from cdsware import webalert
from cdsware import webuser
from cdsware.webmessage import account_new_mail
from cdsware.access_control_config import *
from cdsware.access_control_config import CFG_ACCESS_CONTROL_LEVEL_SITE, cfg_webaccess_warning_msgs, CFG_EXTERNAL_AUTHENTICATION

from cdsware.messages import gettext_set_language
import cdsware.template
websession_templates = cdsware.template.load('websession')

def edit(req, ln=cdslang):
    uid = webuser.getUid(req)

    # load the right message language
    _ = gettext_set_language(ln)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return webuser.page_not_authorized(req, "../youraccount.py/set")

    data = webuser.getDataUid(req,uid)
    email = data[0]
    passw = data[1]
    return page(title= _("Your Settings"),
                body=webaccount.perform_set(email,passw, ln),
                navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">""" % (weburl, ln) + _("Your Account") + """</a>""",
                description="CDS Personalize, Your Settings",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def change(req,email=None,password=None,password2=None,login_method="",ln=cdslang):
    uid = webuser.getUid(req)

    # load the right message language
    _ = gettext_set_language(ln)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return webuser.page_not_authorized(req, "../youraccount.py/change")

    if login_method and CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS < 4:
        title = _("Settings edited")
        act = "display"
        linkname = _("Show account")
        prefs = webuser.get_user_preferences(uid)
        prefs['login_method'] = login_method
        webuser.set_user_preferences(uid, prefs)
        mess = _("Login method successfully selected.")
    elif login_method and CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 4:
        return webuser.page_not_authorized(req, "../youraccount.py/change")
    elif email:
        uid2 = webuser.emailUnique(email)
        if (CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 2 or (CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS <= 1 and webuser.checkemail(email))) and uid2 != -1 and (uid2 == uid or uid2 == 0) and password == password2:
            if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS < 3:
                change = webuser.updateDataUser(req,uid,email,password)
            else:
                return webuser.page_not_authorized(req, "../youraccount.py/change")
            if change and CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 2:
                mess = _("Password successfully edited.")
            elif change:
                mess = _("Settings successfully edited.")
       	    act = "display"
            linkname = _("Show account")
            title = _("Settings edited")
        elif uid2 == -1 or uid2 != uid and not uid2 == 0:
            mess = _("The email address is already in use, please try again.")
       	    act = "edit"
            linkname = _("Edit settings")
            title = _("Editing settings failed")
        elif not webuser.checkemail(email):
            mess = _("The email address is not valid, please try again.")
       	    act = "edit"
            linkname = _("Edit settings")
            title = _("Editing settings failed")
        elif password != password2:
            mess = _("The passwords do not match, please try again.")
       	    act = "edit"
            linkname = _("Edit settings")
            title = _("Editing settings failed")
    else:
        mess = _("Could not update settings.")
       	act = "edit"
        linkname = _("Edit settings")
        title = _("Editing settings failed")

    return page(title=title,
 	        body=webaccount.perform_back(mess,act, linkname, ln),
                navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">""" % (weburl, ln) + _("Your Account") + """</a>""",
                description="CDS Personalize, Main page",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def lost(req, ln=cdslang):
    uid = webuser.getUid(req)

    # load the right message language
    _ = gettext_set_language(ln)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return webuser.page_not_authorized(req, "../youraccount.py/lost")

    return page(title=_("Lost your password?"),
                body=webaccount.perform_lost(ln),
                navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">""" % (weburl, ln) + _("Your Account") + """</a>""",
                description="CDS Personalize, Main page",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def display(req, ln=cdslang):
    uid =  webuser.getUid(req)

    # load the right message language
    _ = gettext_set_language(ln)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return webuser.page_not_authorized(req, "../youraccount.py/display")

    if webuser.isGuestUser(uid):
        return page(title=_("Your Account"),
                    body=webaccount.perform_info(req, ln),
                    description="CDS Personalize, Main page",
                    keywords="CDS, personalize",
                    uid=uid,
                    language=ln,
                    lastupdated=__lastupdated__)

    data = webuser.getDataUid(req,uid)
    bask = webbasket.account_list_baskets(uid, ln = ln)
    aler = webalert.account_list_alerts(uid, ln = ln)
    sear = webalert.account_list_searches(uid, ln = ln)
    msgs = account_new_mail(uid, ln = ln)
    return page(title=_("Your Account"),
                body=webaccount.perform_display_account(req,data,bask,aler,sear,msgs,ln),
                description="CDS Personalize, Main page",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def send_email(req, p_email=None, ln=cdslang):

    uid = webuser.getUid(req)

    # load the right message language
    _ = gettext_set_language(ln)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return webuser.page_not_authorized(req, "../youraccount.py/send_email")

    user_prefs = webuser.get_user_preferences(webuser.emailUnique(p_email))
    if user_prefs:
        if CFG_EXTERNAL_AUTHENTICATION.has_key(user_prefs['login_method']) or CFG_EXTERNAL_AUTHENTICATION.has_key(user_prefs['login_method']) and CFG_EXTERNAL_AUTHENTICATION[user_prefs['login_method']][0] != None:
            Msg = websession_templates.tmpl_lost_password_message(ln = ln, supportemail = supportemail)

            return page(title=_("Your Account"),
                        body=Msg,
                        description="CDS Personalize, Main page",
                        keywords="CDS, personalize",
                        uid=uid,
                        language=ln,
                        lastupdated=__lastupdated__)

    passw = webuser.givePassword(p_email)
    if passw == -999:
        eMsg = _("The entered e-mail address doesn't exist in the database")
        return page(title=_("Your Account"),
                    body=webaccount.perform_emailMessage(eMsg, ln),
                    description="CDS Personalize, Main page",
                    keywords="CDS, personalize",
                    uid=uid,
                    language=ln,
                    lastupdated=__lastupdated__)

    fromaddr = "From: %s" % supportemail
    toaddrs  = "To: " + p_email
    to = toaddrs + "\n"
    sub = "Subject: %s %s\n\n" % (_("Credentials for"), cdsname)
    body = "%s %s:\n\n" % (_("Here are your user credentials for"), cdsname)
    body += "   %s: %s\n   %s: %s\n\n" % (_("username"), p_email, _("password"), passw)
    body += "%s %s/youraccount.py/login?ln=%s" % (_("You can login at"), weburl, ln)
    msg = to + sub + body

    server = smtplib.SMTP('localhost')
    server.set_debuglevel(1)

    try:
        server.sendmail(fromaddr, toaddrs, msg)

    except smtplib.SMTPRecipientsRefused,e:
        eMsg = _("The entered email address is incorrect, please check that it is written correctly (e.g. johndoe@example.com).")
        return page(title=_("Incorrect email address"),
                    body=webaccount.perform_emailMessage(eMsg, ln),
                    description="CDS Personalize, Main page",
                    keywords="CDS, personalize",
                    uid=uid,
                    language=ln,
                    lastupdated=__lastupdated__)

    server.quit()
    return page(title=_("Lost password sent"),
                body=webaccount.perform_emailSent(p_email, ln),
                description="CDS Personalize, Main page",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def youradminactivities(req, ln=cdslang):
    uid = webuser.getUid(req)

    # load the right message language
    _ = gettext_set_language(ln)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return webuser.page_not_authorized(req, "../youraccount.py/youradminactivities")

    return page(title=_("Your Administrative Activities"),
                body=webaccount.perform_youradminactivities(uid, ln),
                navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">""" % (weburl, ln) + _("Your Account") + """</a>""",
                description="CDS Personalize, Main page",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def delete(req, ln=cdslang):
    uid = webuser.getUid(req)

    # load the right message language
    _ = gettext_set_language(ln)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return webuser.page_not_authorized(req, "../youraccount.py/delete")

    return page(title=_("Delete Account"),
                body=webaccount.perform_delete(ln),
                navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">""" % (weburl, ln) + _("Your Account") + """</a>""",
                description="CDS Personalize, Main page",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def logout(req, ln=cdslang):

    uid = webuser.logoutUser(req)

    # load the right message language
    _ = gettext_set_language(ln)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return webuser.page_not_authorized(req, "../youraccount.py/logout")

    return page(title=_("Logout"),
                body=webaccount.perform_logout(req, ln),
                navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">""" % (weburl, ln) + _("Your Account") + """</a>""",
                description="CDS Personalize, Main page",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def login(req, p_email=None, p_pw=None, login_method=None, action='login', referer='', ln=cdslang):

    if CFG_ACCESS_CONTROL_LEVEL_SITE > 0:
        return webuser.page_not_authorized(req, "../youraccount.py/login?ln=%s" % ln)

    uid = webuser.getUid(req)

    # load the right message language
    _ = gettext_set_language(ln)

    #return action+_("login")
    if action == "login" or action == _("login"):
        if p_email==None or not login_method:
            return page(title=_("Login"),
                        body=webaccount.create_login_page_box(referer, ln),
                        navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">""" % (weburl, ln) + _("Your Account") + """</a>""",
                        description="CDS Personalize, Main page",
                        keywords="CDS, personalize",
                        uid=uid,
                        language=ln,
                        lastupdated=__lastupdated__)
        (iden, p_email, p_pw, msgcode) = webuser.loginUser(req,p_email,p_pw, login_method)
        if len(iden)>0:
            
            uid = webuser.update_Uid(req,p_email,p_pw)
            uid2 = webuser.getUid(req)
            if uid2 == -1:
                webuser.logoutUser(req)
                return webuser.page_not_authorized(req, "../youraccount.py/login?ln=%s" % ln, uid=uid)
            
            # login successful!
            if referer:
                req.err_headers_out.add("Location", referer)
                raise apache.SERVER_RETURN, apache.HTTP_MOVED_PERMANENTLY
            else:
                return display(req, ln)
        else:
            mess = cfg_webaccess_warning_msgs[msgcode] % login_method
            if msgcode == 14:
                if not webuser.userNotExist(p_email,p_pw) or p_email=='' or p_email==' ':
                    mess = cfg_webaccess_warning_msgs[15] % login_method
            act = "login"
            return page(title=_("Login"),
                        body=webaccount.perform_back(mess,act, _("login"), ln),
                        navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">""" % (weburl, ln) + _("Your Account") + """</a>""",
                        description="CDS Personalize, Main page",
                        keywords="CDS, personalize",
                        uid=uid,
                        language=ln,
                        lastupdated=__lastupdated__)
    else:
        return "This should have never happened.  Please contact %s." % supportemail

def register(req, p_email=None, p_pw=None, p_pw2=None, action='login', referer='', ln=cdslang):

    if CFG_ACCESS_CONTROL_LEVEL_SITE > 0:
        return webuser.page_not_authorized(req, "../youraccount.py/register?ln=%s" % ln)

    uid = webuser.getUid(req)

    # load the right message language
    _ = gettext_set_language(ln)

    if p_email==None:
        return  page(title=_("Register"),
                     body=webaccount.create_register_page_box(referer, ln),
                     navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">""" % (weburl, ln) + _("Your Account") + """</a>""",
                     description="CDS Personalize, Main page",
                     keywords="CDS, personalize",
                     uid=uid,
                     language=ln,
                     lastupdated=__lastupdated__)

    mess=""
    act=""
    if p_pw == p_pw2:
        ruid = webuser.registerUser(req,p_email,p_pw)
    else:
        ruid = -2
    if ruid == 1:
        uid = webuser.update_Uid(req,p_email,p_pw)
        mess = _("Your account has been successfully created.")
        title = _("Account created")
        if CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT == 1:
            mess += _(" An email has been sent to the given address with the account information.")
        if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 1:
            mess += _(" A second email will be sent when the account has been activated and can be used.")
        else:
            mess += _(""" You can now access your <a href="%s">account</a>.""") % (
                      "%s/youraccount.py/display?ln=%s" % (weburl, ln))
    elif ruid == -1:
        mess = _("The user already exists in the database, please try again.")
        act = "register"
        title = _("Register failure")
    elif ruid == -2:
        mess = _("Both passwords must match, please try again.")
        act = "register"
        title = _("Register failure")
    else:
        mess = _("The email address given is not valid, please try again.")
       	act = "register"
        title = _("Register failure")

    return page(title=title,
                body=webaccount.perform_back(mess,act, (act == 'register' and _("register") or ""), ln),
                navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">""" % (weburl, ln) + _("Your Account") + """</a>""",
                description="CDS Personalize, Main page",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)
