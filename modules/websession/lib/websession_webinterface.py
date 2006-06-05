# -*- coding: utf-8 -*-
## $Id$

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

"""CDS Invenio ACCOUNT HANDLING"""

__lastupdated__ = """$Date$"""

import sys
from mod_python import apache
import smtplib

from invenio import webuser
from invenio.config import weburl, sweburl, cdsname, cdslang, supportemail
from invenio.webpage import page
from invenio import webaccount
from invenio import webbasket
from invenio import webalert
from invenio import webuser
from invenio.webmessage import account_new_mail
from invenio.access_control_config import *
from invenio.access_control_config import CFG_ACCESS_CONTROL_LEVEL_SITE, cfg_webaccess_warning_msgs, CFG_EXTERNAL_AUTHENTICATION
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.urlutils import redirect_to_url, make_canonical_urlargd

from invenio.messages import gettext_set_language
import invenio.template
websession_templates = invenio.template.load('websession')


class WebInterfaceYourAccountPages(WebInterfaceDirectory):

    _exports = ['', 'edit', 'change', 'lost', 'display',
                'send_email', 'youradminactivities',
                'delete', 'logout', 'login', 'register']

    _force_https = True

    def index(self, req, form):
        redirect_to_url(req, '/youraccount/display')
        
    def display(self, req, form):
        args = wash_urlargd(form, {})
        uid = webuser.getUid(req)

        # load the right message language
        _ = gettext_set_language(args['ln'])

        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return webuser.page_not_authorized(req, "../youraccount/display")

        if webuser.isGuestUser(uid):
            return page(title=_("Your Account"),
                        body=webaccount.perform_info(req, args['ln']),
                        description="CDS Personalize, Main page",
                        keywords="CDS, personalize",
                        uid=uid,
                        req=req,
                        secure_page_p = 1,
                        language=args['ln'],
                        lastupdated=__lastupdated__)

        data = webuser.getDataUid(req,uid)
        bask = webbasket.account_list_baskets(uid, ln=args['ln'])
        aler = webalert.account_list_alerts(uid, ln=args['ln'])
        sear = webalert.account_list_searches(uid, ln=args['ln'])
        msgs = account_new_mail(uid, ln=args['ln'])
        
        return page(title=_("Your Account"),
                    body=webaccount.perform_display_account(req,data,bask,aler,sear,msgs,args['ln']),
                    description="CDS Personalize, Main page",
                    keywords="CDS, personalize",
                    uid=uid,
                    req=req,
                    secure_page_p = 1,
                    language=args['ln'],
                    lastupdated=__lastupdated__)


    def edit(self, req, form):
        args = wash_urlargd(form, {})
        uid = webuser.getUid(req)

        # load the right message language
        _ = gettext_set_language(args['ln'])

        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return webuser.page_not_authorized(req, "../youraccount/edit")

        data = webuser.getDataUid(req,uid)
        email = data[0]
        passw = data[1]
        return page(title= _("Your Settings"),
                    body=webaccount.perform_set(email,passw, args['ln']),
                    navtrail="""<a class="navtrail" href="%s/youraccount/display?ln=%s">""" % (sweburl, args['ln']) + _("Your Account") + """</a>""",
                    description="CDS Personalize, Your Settings",
                    keywords="CDS, personalize",
                    uid=uid,
                    req=req,
                    secure_page_p = 1,
                    language=args['ln'],
                    lastupdated=__lastupdated__)

    def change(self, req, form):
        args = wash_urlargd(form, {
            'email': (str, None),
            'password': (str, None),
            'password2': (str, None),
            'login_method': (str, "")
            })
        
        uid = webuser.getUid(req)

        # load the right message language
        _ = gettext_set_language(args['ln'])

        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return webuser.page_not_authorized(req, "../youraccount/change")

        if args['login_method'] and CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS < 4:
            title = _("Settings edited")
            act = "display"
            linkname = _("Show account")
            prefs = webuser.get_user_preferences(uid)
            prefs['login_method'] = args['login_method']
            webuser.set_user_preferences(uid, prefs)
            mess = _("Login method successfully selected.")
        elif args['login_method'] and CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 4:
            return webuser.page_not_authorized(req, "../youraccount/change")
        elif args['email']:
            uid2 = webuser.emailUnique(args['email'])
            if (CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 2 or (CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS <= 1 and webuser.checkemail(args['email']))) and uid2 != -1 and (uid2 == uid or uid2 == 0) and args['password'] == args['password2']:
                if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS < 3:
                    change = webuser.updateDataUser(req,uid,args['email'],args['password'])
                else:
                    return webuser.page_not_authorized(req, "../youraccount/change")
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
            elif not webuser.checkemail(args['email']):
                mess = _("The email address is not valid, please try again.")
                act = "edit"
                linkname = _("Edit settings")
                title = _("Editing settings failed")
            elif args['password'] != args['password2']:
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
                    body=webaccount.perform_back(mess,act, linkname, args['ln']),
                    navtrail="""<a class="navtrail" href="%s/youraccount/display?ln=%s">""" % (sweburl, args['ln']) + _("Your Account") + """</a>""",
                    description="CDS Personalize, Main page",
                    keywords="CDS, personalize",
                    uid=uid,
                    req=req,
                    secure_page_p = 1,
                    language=args['ln'],
                    lastupdated=__lastupdated__)

    def lost(self, req, form):
        args = wash_urlargd(form, {})
        uid = webuser.getUid(req)

        # load the right message language
        _ = gettext_set_language(args['ln'])

        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return webuser.page_not_authorized(req, "../youraccount/lost")

        return page(title=_("Lost your password?"),
                    body=webaccount.perform_lost(args['ln']),
                    navtrail="""<a class="navtrail" href="%s/youraccount/display?ln=%s">""" % (sweburl, args['ln']) + _("Your Account") + """</a>""",
                    description="CDS Personalize, Main page",
                    keywords="CDS, personalize",
                    uid=uid,
                    req=req,
                    secure_page_p = 1,
                    language=args['ln'],
                    lastupdated=__lastupdated__)


    def send_email(self, req, form):
        # set all the declared query fields as local variables
        args = wash_urlargd(form, {'p_email': (str, None)})
        uid = webuser.getUid(req)

        # load the right message language
        _ = gettext_set_language(args['ln'])

        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return webuser.page_not_authorized(req, "../youraccount/send_email")

        user_prefs = webuser.get_user_preferences(webuser.emailUnique(args['p_email']))
        if user_prefs:
            if CFG_EXTERNAL_AUTHENTICATION.has_key(user_prefs['login_method']) or CFG_EXTERNAL_AUTHENTICATION.has_key(user_prefs['login_method']) and CFG_EXTERNAL_AUTHENTICATION[user_prefs['login_method']][0] != None:
                Msg = websession_templates.tmpl_lost_password_message(ln=args['ln'], supportemail = supportemail)

                return page(title=_("Your Account"),
                            body=Msg,
                            description="CDS Personalize, Main page",
                            keywords="CDS, personalize",
                            uid=uid,
                            req=req,
                            secure_page_p = 1,
                            language=args['ln'],
                            lastupdated=__lastupdated__)

        passw = webuser.givePassword(args['p_email'])
        if passw == -999:
            eMsg = _("The entered e-mail address doesn't exist in the database")
            return page(title=_("Your Account"),
                        body=webaccount.perform_emailMessage(eMsg, args['ln']),
                        description="CDS Personalize, Main page",
                        keywords="CDS, personalize",
                        uid=uid, req=req,
                        secure_page_p = 1,
                        language=args['ln'],
                        lastupdated=__lastupdated__)

        fromaddr = "From: %s" % supportemail
        toaddrs  = "To: " + args['p_email']
        to = toaddrs + "\n"
        sub = "Subject: %s %s\n\n" % (_("Credentials for"), cdsname)
        body = "%s %s:\n\n" % (_("Here are your user credentials for"), cdsname)
        body += "   %s: %s\n   %s: %s\n\n" % (_("username"), args['p_email'], _("password"), passw)
        body += "%s %s/youraccount/login?ln=%s" % (_("You can login at"), sweburl, args['ln'])
        msg = to + sub + body

        server = smtplib.SMTP('localhost')
        server.set_debuglevel(1)

        try:
            server.sendmail(fromaddr, toaddrs, msg)

        except smtplib.SMTPRecipientsRefused,e:
            eMsg = _("The entered email address is incorrect, please check that it is written correctly (e.g. johndoe@example.com).")
            return page(title=_("Incorrect email address"),
                        body=webaccount.perform_emailMessage(eMsg, args['ln']),
                        description="CDS Personalize, Main page",
                        keywords="CDS, personalize",
                        uid=uid,
                        req=req,
                        secure_page_p = 1,
                        language=args['ln'],
                        lastupdated=__lastupdated__)

        server.quit()
        return page(title=_("Lost password sent"),
                    body=webaccount.perform_emailSent(args['p_email'], args['ln']),
                    description="CDS Personalize, Main page",
                    keywords="CDS, personalize",
                    uid=uid, req=req,
                    secure_page_p = 1,
                    language=args['ln'],
                    lastupdated=__lastupdated__)

    def youradminactivities(self, req, form):
        args = wash_urlargd(form, {})
        uid = webuser.getUid(req)

        # load the right message language
        _ = gettext_set_language(args['ln'])

        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return webuser.page_not_authorized(req, "../youraccount/youradminactivities")

        return page(title=_("Your Administrative Activities"),
                    body=webaccount.perform_youradminactivities(uid, args['ln']),
                    navtrail="""<a class="navtrail" href="%s/youraccount/display?ln=%s">""" % (sweburl, args['ln']) + _("Your Account") + """</a>""",
                    description="CDS Personalize, Main page",
                    keywords="CDS, personalize",
                    uid=uid,
                    req=req,
                    secure_page_p = 1,
                    language=args['ln'],
                    lastupdated=__lastupdated__)

    def delete(self, req, form):
        args = wash_urlargd(form, {})
        uid = webuser.getUid(req)

        # load the right message language
        _ = gettext_set_language(args['ln'])

        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return webuser.page_not_authorized(req, "../youraccount/delete")

        return page(title=_("Delete Account"),
                    body=webaccount.perform_delete(args['ln']),
                    navtrail="""<a class="navtrail" href="%s/youraccount/display?ln=%s">""" % (sweburl, args['ln']) + _("Your Account") + """</a>""",
                    description="CDS Personalize, Main page",
                    keywords="CDS, personalize",
                    uid=uid,
                    req=req,
                    secure_page_p = 1,
                    language=args['ln'],
                    lastupdated=__lastupdated__)

    def logout(self, req, form):
        args = wash_urlargd(form, {})
        uid = webuser.logoutUser(req)

        # load the right message language
        _ = gettext_set_language(args['ln'])

        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return webuser.page_not_authorized(req, "../youraccount/logout")

        return page(title=_("Logout"),
                    body=webaccount.perform_logout(req, args['ln']),
                    navtrail="""<a class="navtrail" href="%s/youraccount/display?ln=%s">""" % (sweburl, args['ln']) + _("Your Account") + """</a>""",
                    description="CDS Personalize, Main page",
                    keywords="CDS, personalize",
                    uid=uid,
                    req=req,
                    secure_page_p = 1,
                    language=args['ln'],
                    lastupdated=__lastupdated__)

    def login(self, req, form):
        args = wash_urlargd(form, {
            'p_email': (str, None),
            'p_pw': (str, None),
            'login_method': (str, None),
            'action': (str, 'login'),
            'referer': (str, '')})

        locals().update(args)

        if CFG_ACCESS_CONTROL_LEVEL_SITE > 0:
            return webuser.page_not_authorized(req, "../youraccount/login?ln=%s" % args['ln'])

        uid = webuser.getUid(req)

        # load the right message language
        _ = gettext_set_language(args['ln'])

        #return action+_("login")
        if args['action'] == "login" or args['action'] == _("login"):
            if args['p_email']==None or not args['login_method']:
                return page(title=_("Login"),
                            body=webaccount.create_login_page_box(args['referer'], args['ln']),
                            navtrail="""<a class="navtrail" href="%s/youraccount/display?ln=%s">""" % (sweburl, args['ln']) + _("Your Account") + """</a>""",
                            description="CDS Personalize, Main page",
                            keywords="CDS, personalize",
                            uid=uid,
                            req=req,
                            secure_page_p = 1,
                            language=args['ln'],
                            lastupdated=__lastupdated__)
            (iden, args['p_email'], args['p_pw'], msgcode) = webuser.loginUser(req,args['p_email'],args['p_pw'], args['login_method'])
            if len(iden)>0:

                uid = webuser.update_Uid(req,args['p_email'],args['p_pw'])
                uid2 = webuser.getUid(req)
                if uid2 == -1:
                    webuser.logoutUser(req)
                    return webuser.page_not_authorized(req, "../youraccount/login?ln=%s" % args['ln'], uid=uid)

                # login successful!
                if args['referer']:
                    req.err_headers_out.add("Location", args['referer'])
                    raise apache.SERVER_RETURN, apache.HTTP_MOVED_PERMANENTLY
                else:
                    return self.display(req, form)
            else:
                mess = cfg_webaccess_warning_msgs[msgcode] % args['login_method']
                if msgcode == 14:
                    if not webuser.userNotExist(args['p_email'],args['p_pw']) or args['p_email']=='' or args['p_email']==' ':
                        mess = cfg_webaccess_warning_msgs[15] % args['login_method']
                act = "login"
                return page(title=_("Login"),
                            body=webaccount.perform_back(mess,act, _("login"), args['ln']),
                            navtrail="""<a class="navtrail" href="%s/youraccount/display?ln=%s">""" % (sweburl, args['ln']) + _("Your Account") + """</a>""",
                            description="CDS Personalize, Main page",
                            keywords="CDS, personalize",
                            uid=uid,
                            req=req,
                            secure_page_p = 1,
                            language=args['ln'],
                            lastupdated=__lastupdated__)
        else:
            return "This should have never happened.  Please contact %s." % supportemail

    def register(self, req, form):
        args = wash_urlargd(form, {
            'p_email': (str, None),
            'p_pw': (str, None),
            'p_pw2': (str, None),
            'action': (str, 'login'),
            'referer': (str, '')})

        if CFG_ACCESS_CONTROL_LEVEL_SITE > 0:
            return webuser.page_not_authorized(req, "../youraccount/register?ln=%s" % args['ln'])

        uid = webuser.getUid(req)

        # load the right message language
        _ = gettext_set_language(args['ln'])

        if args['p_email']==None:
            return  page(title=_("Register"),
                         body=webaccount.create_register_page_box(args['referer'], args['ln']),
                         navtrail="""<a class="navtrail" href="%s/youraccount/display?ln=%s">""" % (sweburl, args['ln']) + _("Your Account") + """</a>""",
                         description="CDS Personalize, Main page",
                         keywords="CDS, personalize",
                         uid=uid,
                         req=req,
                         secure_page_p = 1,
                         language=args['ln'],
                         lastupdated=__lastupdated__)

        mess=""
        act=""
        if args['p_pw'] == args['p_pw2']:
            ruid = webuser.registerUser(req,args['p_email'],args['p_pw'])
        else:
            ruid = -2
        if ruid == 1:
            uid = webuser.update_Uid(req,args['p_email'],args['p_pw'])
            mess = _("Your account has been successfully created.")
            title = _("Account created")
            if CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT == 1:
                mess += _(" An email has been sent to the given address with the account information.")
            if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 1:
                mess += _(" A second email will be sent when the account has been activated and can be used.")
            else:
                mess += _(""" You can now access your <a href="%s">account</a>.""") % (
                          "%s/youraccount/display?ln=%s" % (sweburl, args['ln']))
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
                    body=webaccount.perform_back(mess,act, (act == 'register' and _("register") or ""), args['ln']),
                    navtrail="""<a class="navtrail" href="%s/youraccount/display?ln=%s">""" % (sweburl, args['ln']) + _("Your Account") + """</a>""",
                    description="CDS Personalize, Main page",
                    keywords="CDS, personalize",
                    uid=uid,
                    req=req,
                    secure_page_p = 1,
                    language=args['ln'],
                    lastupdated=__lastupdated__)
