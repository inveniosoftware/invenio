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

__revision__ = "$Id$"

import sys
import string
import cgi

from invenio.config import *
from invenio.access_control_config import CFG_EXTERNAL_AUTHENTICATION
from invenio.webpage import page
from invenio.dbquery import run_sql
from invenio.webuser import getUid,isGuestUser, get_user_preferences, set_user_preferences
from invenio.access_control_admin import acc_findUserRoleActions

from invenio.messages import gettext_set_language

import invenio.template
websession_templates = invenio.template.load('websession')

# perform_info(): display the main features of CDS personalize
def perform_info(req, ln):
    out = ""
    uid = getUid(req)

    return websession_templates.tmpl_account_info(
            ln = ln,
            uid = uid,
            guest = isGuestUser(uid),
            cfg_cern_site = cfg_cern_site,
           );


def perform_youradminactivities(uid, ln):
    """Return text for the `Your Admin Activities' box.  Analyze
       whether user UID has some admin roles, and if yes, then print
       suitable links for the actions he can do.  If he's not admin,
       print a simple non-authorized message."""
    your_role_actions = acc_findUserRoleActions(uid)
    your_roles = []
    your_admin_activities = []
    guest = isGuestUser(uid)
    for (role, action) in your_role_actions:
        if role not in your_roles:
            your_roles.append(role)
        if action not in your_admin_activities:
            your_admin_activities.append(action)

    if "superadmin" in your_roles:
        for action in ["runbibedit", "cfgbibformat", "cfgbibharvest", "cfgbibrank", "cfgbibindex", "cfgwebaccess", "cfgwebcomment", "cfgwebsearch", "cfgwebsubmit"]:
            if action not in your_admin_activities:
                your_admin_activities.append(action)

    return websession_templates.tmpl_account_adminactivities(
             ln = ln,
             uid = uid,
             guest = guest,
             roles = your_roles,
             activities = your_admin_activities,
             weburl = weburl,
           )

# perform_display_account(): display a dynamic page that shows the user's account
def perform_display_account(req,username,bask,aler,sear,msgs,grps,ln):

    # load the right message language
    _ = gettext_set_language(ln)

    uid = getUid(req)
    #your account
    if isGuestUser(uid):
        user = "guest"
        login = "%s/youraccount/login?ln=%s" % (sweburl, ln)
        accBody = _("You are logged in as guest. You may want to %(x_url_open)slogin%(x_url_close)s as a regular user.") %\
            {'x_url_open': '<a href="' + login + '">', 
             'x_url_close': '</a>'}
	accBody += "<br /><br />"
        bask=aler=msgs= _("The %(x_fmt_open)sguest%(x_fmt_close)s users need to %(x_url_open)sregister%(x_url_close)s first") %\
            {'x_fmt_open': '<strong class="headline">', 
             'x_fmt_close': '</strong>',
             'x_url_open': '<a href="' + login + '">',
             'x_url_close': '</a>'}
        sear= _("No queries found")
    else:
        user = username
        accBody = websession_templates.tmpl_account_body(
                    ln = ln,
                    user = user,
                  )

    return websession_templates.tmpl_account_page(
             ln = ln,
             weburl = weburl,
             accBody = accBody,
             baskets = bask,
             alerts = aler,
             searches = sear,
             messages = msgs,
             groups = grps,
             administrative = perform_youradminactivities(uid, ln)
           )

# template_account() : it is a template for print each of the options from the user's account
def template_account(title, body, ln):
    return websession_templates.tmpl_account_template(
             ln = ln,
             title = title,
             body = body
           )

# warning_guest_user(): It returns an alert message,showing that the user is a guest user and should log into the system
def warning_guest_user(type, ln=cdslang):

    # load the right message language
    _ = gettext_set_language(ln)

    return websession_templates.tmpl_warning_guest_user(
             ln = ln,
             type = type,
           )

## perform_delete():delete  the account of the user, not implement yet
def perform_delete(ln):
    return websession_templates.tmpl_account_delete(ln = ln)

## perform_set(email,password): edit your account parameters, email and password.
def perform_set(email,password, ln):

    try:
        res = run_sql("SELECT id, nickname FROM user WHERE email=%s", (email,))
        uid = res[0][0]
        nickname = res[0][1]
    except:
        uid = 0
        nickname = ""

    CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS_LOCAL = CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS
    prefs = get_user_preferences(uid)
    if CFG_EXTERNAL_AUTHENTICATION.has_key(prefs['login_method']) and  CFG_EXTERNAL_AUTHENTICATION[prefs['login_method']][1] != True:
        CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS_LOCAL = 3

    out = websession_templates.tmpl_user_preferences(
             ln = ln,
             email = email,
             email_disabled = (CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS_LOCAL >= 2),
             password = password,
             password_disabled = (CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS_LOCAL >= 3),
             nickname = nickname,
           )

    if len(CFG_EXTERNAL_AUTHENTICATION) >= 1:
        try:
            uid = run_sql("SELECT id FROM user where email=%s", (email,))
            uid = uid[0][0]
        except:
            uid = 0
        prefs = get_user_preferences(uid)
        current_login_method = prefs['login_method']
        methods = CFG_EXTERNAL_AUTHENTICATION.keys()
        methods.sort()

        out += websession_templates.tmpl_user_external_auth(
                 ln = ln,
                 methods = methods,
                 current = current_login_method,
                 method_disabled = (CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 4)
               )
    return out

##  create_register_page_box(): register a new account
def create_register_page_box(referer='', ln=cdslang):

    return websession_templates.tmpl_register_page(
             referer = referer,
             ln = ln,
             level = CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS,
             supportemail = supportemail,
             cdsname = cdsname
           )

##  create_login_page_box(): ask for the user's email and password, for login into the system
def create_login_page_box(referer='', ln=cdslang):

    internal = None
    for system in CFG_EXTERNAL_AUTHENTICATION.keys():
        if not CFG_EXTERNAL_AUTHENTICATION[system][0]:
            internal = system
            break
    register_available = CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS <= 1 and internal
    methods = CFG_EXTERNAL_AUTHENTICATION.keys()
    methods.sort()
    selected = ''
    for method in methods:
        if CFG_EXTERNAL_AUTHENTICATION[method][1] == True:
            selected = method
            break

    return websession_templates.tmpl_login_form(
             ln = ln,
             referer = referer,
             internal = internal,
             register_available = register_available,
             methods = methods,
             selected_method = selected,
             supportemail = supportemail,
           )


# perform_logout: display the message of not longer authorized,
def perform_logout(req, ln):
    return websession_templates.tmpl_account_logout(ln = ln)

#def perform_lost: ask the user for his email, in order to send him the lost password
def perform_lost(ln):
    return websession_templates.tmpl_lost_password_form(
             ln = ln,
             msg = websession_templates.tmpl_lost_password_message(ln = ln, supportemail = supportemail),
           )

# perform_emailSent(email): confirm that the password has been emailed to 'email' address
def perform_emailSent(email, ln):
    return websession_templates.tmpl_account_emailSent(ln = ln, email = email)

# peform_emailMessage : display a error message when the email introduced is not correct, and sugest to try again
def perform_emailMessage(eMsg, ln):
    return websession_templates.tmpl_account_emailMessage( ln = ln,
                                           msg = eMsg
                                         )

# perform_back(): template for return to a previous page, used for login,register and setting
def perform_back(mess,act,linkname='', ln='en'):
    if not linkname:
        linkname = act

    return websession_templates.tmpl_back_form(
             ln = ln,
             message = mess,
             act = act,
             link = linkname,
           )
