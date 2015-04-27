# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2014, 2015 CERN.
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

__revision__ = "$Id$"

import re
import MySQLdb
import urllib

from six import iteritems

from invenio.base.globals import cfg
from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS, \
     CFG_CERN_SITE, \
     CFG_SITE_LANG, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_SITE_ADMIN_EMAIL, \
     CFG_SITE_SECURE_URL, \
     CFG_VERSION, \
     CFG_SITE_RECORD
from invenio.modules.access.engine import acc_authorize_action
from invenio.modules.access.local_config import CFG_EXTERNAL_AUTHENTICATION, \
    SUPERADMINROLE, CFG_EXTERNAL_AUTH_DEFAULT
from invenio.legacy.dbquery import run_sql
from invenio.legacy.webuser import getUid, get_user_preferences, \
        collect_user_info
from invenio.modules.access.control import acc_find_user_role_actions
from invenio.base.i18n import gettext_set_language

import invenio.legacy.template
websession_templates = invenio.legacy.template.load('websession')

from invenio.modules import apikeys as web_api_key

def perform_info(req, ln):
    """Display the main features of CDS personalize"""
    uid = getUid(req)

    user_info = collect_user_info(req)
    return websession_templates.tmpl_account_info(
            ln = ln,
            uid = uid,
            guest = int(user_info['guest']),
            CFG_CERN_SITE = CFG_CERN_SITE,
           )

def perform_display_external_user_settings(settings, ln):
    """show external user settings which is a dictionary."""
    _ = gettext_set_language(ln)
    html_settings = ""
    print_settings = False
    settings_keys = settings.keys()
    settings_keys.sort()
    for key in settings_keys:
        value = settings[key]
        if key.startswith("EXTERNAL_") and not "HIDDEN_" in key:
            print_settings = True
            key = key[9:].capitalize()
            html_settings += websession_templates.tmpl_external_setting(ln, key, value)
    return print_settings and websession_templates.tmpl_external_user_settings(ln, html_settings) or ""

def perform_youradminactivities(user_info, ln):
    """Return text for the `Your Admin Activities' box.  Analyze
       whether user UID has some admin roles, and if yes, then print
       suitable links for the actions he can do.  If he's not admin,
       print a simple non-authorized message."""
    your_role_actions = acc_find_user_role_actions(user_info)
    your_roles = []
    your_admin_activities = []
    guest = int(user_info['guest'])
    for (role, action) in your_role_actions:
        if role not in your_roles:
            your_roles.append(role)
        if action not in your_admin_activities:
            your_admin_activities.append(action)

    if SUPERADMINROLE in your_roles:
        for action in ("runbibedit", "cfgbibformat", "cfgoaiharvest", "cfgoairepository", "cfgbibrank", "cfgbibindex", "cfgwebaccess", "cfgwebcomment", "cfgwebsearch", "cfgwebsubmiit", "cfgbibknowledge", "runbatchuploader"):
            if action not in your_admin_activities:
                your_admin_activities.append(action)

    return websession_templates.tmpl_account_adminactivities(
             ln = ln,
             uid = user_info['uid'],
             guest = guest,
             roles = your_roles,
             activities = your_admin_activities,
           )

def perform_display_account(req, username, bask, aler, sear, msgs, loan, grps, sbms, appr, admn, ln, comments):
    """Display a dynamic page that shows the user's account."""

    # load the right message language
    _ = gettext_set_language(ln)

    uid = getUid(req)
    user_info = collect_user_info(req)
    #your account
    if int(user_info['guest']):
        user = "guest"
        login = "%s/youraccount/login?ln=%s" % (CFG_SITE_SECURE_URL, ln)
        accBody = _("You are logged in as guest. You may want to %(x_url_open)slogin%(x_url_close)s as a regular user.") %\
            {'x_url_open': '<a href="' + login + '">',
             'x_url_close': '</a>'}
        accBody += "<br /><br />"
        bask=aler=msgs=comments= _("The %(x_fmt_open)sguest%(x_fmt_close)s users need to %(x_url_open)sregister%(x_url_close)s first") %\
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

    #Display warnings if user is superuser
    roles = acc_find_user_role_actions(user_info)
    warnings = "0"
    warning_list = []
    for role in roles:
        if "superadmin" in role:
            warnings = "1"
            break

    if warnings == "1":
        warning_list.extend(superuser_account_warnings())

    # Display the warning if the email of the user is autogenerated
    email_autogenerated_warning = external_user_warning(uid)

    if email_autogenerated_warning:
        warnings = "1"
        warning_list.append(email_autogenerated_warning)

    #check if tickets ok
    tickets = (acc_authorize_action(user_info, 'runbibedit')[0] == 0)

    return websession_templates.tmpl_account_page(
             ln = ln,
             warnings = warnings,
             warning_list = warning_list,
             accBody = accBody,
             baskets = bask,
             alerts = aler,
             searches = sear,
             messages = msgs,
             loans = loan,
             groups = grps,
             submissions = sbms,
             approvals = appr,
             tickets = tickets,
             administrative = admn,
             comments = comments,
           )

def superuser_account_warnings():
    """Check to see whether admin accounts have default / blank password etc. Returns a list"""
    warning_array = []

    #Try and connect to the mysql database with the default invenio password
    try:
        conn = MySQLdb.connect (host = cfg['CFG_DATABASE_HOST'],
                                user = "root",
                                passwd = "my123p$ss",
                                db = "mysql")
        conn.close()
        warning_array.append("warning_mysql_password_equal_to_invenio_password")
    except:
        pass

    #Try and connect to the invenio database with the default invenio password
    try:
        conn = MySQLdb.connect (host = cfg['CFG_DATABASE_HOST'],
                                user = "invenio",
                                passwd = "my123p$ss",
                                db = cfg['CFG_DATABASE_NAME'])
        conn.close ()
        warning_array.append("warning_invenio_password_equal_to_default")
    except:
        pass

    # Check if the admin password is empty
    from invenio.modules.accounts.models import User
    try:
        u = User.query.filter_by(nickname='admin').one()
        res1 = [u.email, ] if u.verify_password("") else []

    except Exception:
        # no account nick-named `admin' exists; keep on going
        res1 = []

    for user in res1:
        warning_array.append("warning_empty_admin_password")

    #Check if the admin email has been changed from the default
    if (CFG_SITE_ADMIN_EMAIL == "info@invenio-software.org" or CFG_SITE_SUPPORT_EMAIL == "info@invenio-software.org") and CFG_CERN_SITE == 0:
        warning_array.append("warning_site_support_email_equal_to_default")

    #Check for a new release of Invenio
    try:
        find = re.compile('Invenio v[0-9]+.[0-9]+.[0-9]+(\-rc[0-9])? is released')

        webFile = urllib.urlopen("http://invenio-software.org/repo/invenio/tree/RELEASE-NOTES")

        temp = ""
        version = ""
        version1 = ""
        while 1:
            temp = webFile.readline()
            match1 = find.match(temp)
            try:
                version = match1.group()
                break
            except:
                pass
            if not temp:
                break

        webFile.close()
        submatch = re.compile('[0-9]+.[0-9]+.[0-9]+(\-rc[0-9])?')
        version1 = submatch.search(version)
        web_version = version1.group().split(".")

        local_version = CFG_VERSION.split(".")

        if web_version[0] > local_version[0]:
            warning_array.append("note_new_release_available")
        elif web_version[0] == local_version[0] and web_version[1] > local_version[1]:
            warning_array.append("note_new_release_available")
        elif web_version[0] == local_version[0] and web_version[1] == local_version[1] and web_version[2] > local_version[2]:
            warning_array.append("note_new_release_available")
    except:
        warning_array.append("error_cannot_download_release_notes")

    return warning_array

def template_account(title, body, ln):
    """It is a template for print each of the options from the user's account."""
    return websession_templates.tmpl_account_template(
             ln = ln,
             title = title,
             body = body
           )

def warning_guest_user(type, ln=CFG_SITE_LANG):
    """It returns an alert message,showing that the user is a guest user and should log into the system."""

    # load the right message language
    _ = gettext_set_language(ln)

    return websession_templates.tmpl_warning_guest_user(
             ln = ln,
             type = type,
           )


def perform_delete(ln):
    """Delete  the account of the user, not implement yet."""
    # TODO
    return websession_templates.tmpl_account_delete(ln = ln)

def perform_set(email, ln, can_config_bibcatalog=False,
                can_config_profiling=False, verbose=0, csrf_token=''):
    """Perform_set(email,password): edit your account parameters, email and
    password.
    If can_config_bibcatalog is True, show the bibcatalog dialog (if configured).
    """

    try:
        res = run_sql("SELECT id, nickname FROM user WHERE email=%s", (email,))
        uid = res[0][0]
        nickname = res[0][1]
    except IndexError:
        uid = 0
        nickname = ""

    CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS_LOCAL = CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS
    prefs = get_user_preferences(uid)
    if prefs['login_method'] in CFG_EXTERNAL_AUTHENTICATION and CFG_EXTERNAL_AUTHENTICATION[prefs['login_method']] is not None:
        CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS_LOCAL = 3

    out = websession_templates.tmpl_user_preferences(
             ln = ln,
             email = email,
             email_disabled = (CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS_LOCAL >= 2),
             password_disabled = (CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS_LOCAL >= 3),
             nickname = nickname,
             csrf_token = csrf_token
           )

    current_group_records = prefs.get('websearch_group_records', 10)
    show_latestbox = prefs.get('websearch_latestbox', True)
    show_helpbox = prefs.get('websearch_helpbox', True)
    out += websession_templates.tmpl_user_websearch_edit(
                ln = ln,
                current = current_group_records,
                show_latestbox = show_latestbox,
                show_helpbox = show_helpbox,
                csrf_token = csrf_token,
                )

    preferred_lang = prefs.get('language', ln)
    out += websession_templates.tmpl_user_lang_edit(
                ln = ln,
                preferred_lang = preferred_lang,
                csrf_token = csrf_token,
                )

    keys_info = web_api_key.show_web_api_keys(uid=uid)
    out+=websession_templates.tmpl_user_api_key(
                ln = ln,
                keys_info = keys_info,
                csrf_token = csrf_token,
                )

    #show this dialog only if the system has been configured to use a ticket system
    from invenio.config import CFG_BIBCATALOG_SYSTEM
    if CFG_BIBCATALOG_SYSTEM and can_config_bibcatalog:
        bibcatalog_username = prefs.get('bibcatalog_username', "")
        bibcatalog_password = prefs.get('bibcatalog_password', "")
        out += websession_templates.tmpl_user_bibcatalog_auth(bibcatalog_username,
                                                              bibcatalog_password, ln=ln,
                                                              csrf_token=csrf_token)

    if can_config_profiling:
        out += websession_templates.tmpl_user_profiling_settings(ln=ln,
                                                                 enable_profiling=prefs.get('enable_profiling'),
                                                                 csrf_token=csrf_token)

    if verbose >= 9:
        for key, value in prefs.items():
            out += "<b>%s</b>:%s<br />" % (key, value)
    out += perform_display_external_user_settings(prefs, ln)
    return out

def create_register_page_box(referer='', ln=CFG_SITE_LANG):
    """Register a new account."""
    return websession_templates.tmpl_register_page(
             referer = referer,
             ln = ln,
             level = CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS,
           )

#  create_login_page_box(): ask for the user's email and password, for login into the system
def create_login_page_box(referer='', ln=CFG_SITE_LANG):
    # List of referer regexep and message to print

    _ = gettext_set_language(ln)

    login_referrer2msg = (
        (re.compile(r"/search"), "<p>" + _("This collection is restricted.  If you think you have right to access it, please authenticate yourself.") + "</p>"),
        (re.compile(r"/%s/\d+/files/.+" % CFG_SITE_RECORD), "<p>" + _("This file is restricted.  If you think you have right to access it, please authenticate yourself.") + "</p>"),
        (re.compile(r"openid-invalid"), "<p>" + _("The OpenID identifier is invalid") + "</p>"),
        (re.compile(r"openid-python"), "<p>%s</p><p>%s</p>" % (_("python-openid package must be installed: run make install-openid-package or download manually from https://github.com/openid/python-openid/"), _("Please inform the <a href='mailto%(x_email)s'>administator</a>", x_email=CFG_SITE_ADMIN_EMAIL))),
        (re.compile(r"oauth-rauth"), "<p>%s</p><p>%s</p>" % (_("rauth package must be installed: run make install-oauth-package or download manually from https://github.com/litl/rauth/"), _("Please inform the <a href='mailto%(x_email)s'>administator</a>", x_email=CFG_SITE_ADMIN_EMAIL))),
        (re.compile(r"oauth-config"), "<p>%s</p><p>%s</p>" % (_("The configuration isn't set properly"), _("Please inform the <a href='mailto%(x_email)s'>administator</a>", x_email=CFG_SITE_ADMIN_EMAIL))),
        (re.compile(r"connection-error"), "<p>%s</p>" % (_("Cannot connect the provider. Please try again later."))),
    )

    msg = ""
    for regexp, txt in login_referrer2msg:
        if regexp.search(referer):
            msg = txt
            break

    internal = None
    for system in CFG_EXTERNAL_AUTHENTICATION.keys():
        if CFG_EXTERNAL_AUTHENTICATION[system] is None:
            internal = system
            break
    register_available = CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS <= 1 and internal
    ## Let's retrieve all the login method that are not dedicated to robots
    methods = [method[0] for method in iteritems(CFG_EXTERNAL_AUTHENTICATION) if not method[1] or not method[1].robot_login_method_p()]
    methods.sort()

    return websession_templates.tmpl_login_form(
             ln = ln,
             referer = referer,
             internal = internal,
             register_available = register_available,
             methods = methods,
             selected_method = CFG_EXTERNAL_AUTH_DEFAULT,
             msg = msg,
           )


# perform_logout: display the message of not longer authorized,
def perform_logout(req, ln):
    return websession_templates.tmpl_account_logout(ln = ln)

#def perform_lost: ask the user for his email, in order to send him the lost password
def perform_lost(ln):
    return websession_templates.tmpl_lost_password_form(ln)

#def perform_reset_password: ask the user for a new password to reset the lost one
def perform_reset_password(ln, email, reset_key, msg=''):
    return websession_templates.tmpl_reset_password_form(ln, email, reset_key, msg)

# perform_emailSent(email): confirm that the password has been emailed to 'email' address
def perform_emailSent(email, ln):
    return websession_templates.tmpl_account_emailSent(ln = ln, email = email)

# peform_emailMessage : display a error message when the email introduced is not correct, and sugest to try again
def perform_emailMessage(eMsg, ln):
    return websession_templates.tmpl_account_emailMessage( ln = ln,
                                           msg = eMsg
                                         )

# perform_back(): template for return to a previous page, used for login,register and setting
def perform_back(mess, url, linkname, ln='en'):
    return websession_templates.tmpl_back_form(
             ln = ln,
             message = mess,
             url = url,
             link = linkname,
           )

def external_user_warning(uid):
    """
    Returns 'email_auto_generated' if the email of the user is auto-generated.

    @param uid: user id
    @type uid: int

    @rtype: ''|'email_auto_generated'
    """
    from invenio.modules.access.local_config import CFG_TEMP_EMAIL_ADDRESS

    query = """
        SELECT      email
        FROM        user
        WHERE       id=%s
    """

    params = (uid, )
    email = run_sql(query, params)[0][0]

    regexp = re.compile(CFG_TEMP_EMAIL_ADDRESS % "\w+", re.IGNORECASE)

    query = """
        SELECT      *
        FROM        userEXT
        WHERE       id_user=%s
    """

    if run_sql(query, params) and re.match(regexp, email):
        return 'email_auto_generated'

    return ''
