# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2014, 2015 CERN.
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

"""Invenio ACCOUNT HANDLING"""

from datetime import timedelta

from invenio.base.i18n import gettext_set_language
from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS, \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     CFG_SITE_NAME, \
     CFG_SITE_NAME_INTL, \
     CFG_SITE_SECURE_URL, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_WEBSESSION_RESET_PASSWORD_EXPIRE_IN_DAYS
from invenio.ext.email import send_email
from invenio.ext.legacy.handler import wash_urlargd, WebInterfaceDirectory
from invenio.legacy import webuser
from invenio.legacy.webpage import page
from invenio.legacy.websession import webaccount
from invenio.modules.access.engine import acc_authorize_action
from invenio.utils import apache
from invenio.utils.url import redirect_to_url
from invenio.modules import apikeys as web_api_key
from invenio.modules.access.local_config import CFG_EXTERNAL_AUTHENTICATION
from invenio.modules.access.mailcookie import mail_cookie_retrieve_kind, \
    mail_cookie_create_pw_reset, mail_cookie_check_role, \
    mail_cookie_check_mail_activation
from invenio.modules.access.errors import InvenioWebAccessMailCookieError, \
    InvenioWebAccessMailCookieDeletedError

import invenio.legacy.template
websession_templates = invenio.legacy.template.load('websession')
bibcatalog_templates = invenio.legacy.template.load('bibcatalog')


class WebInterfaceYourAccountPages(WebInterfaceDirectory):

    _exports = ['',
                'send_email', 'youradminactivities', 'access',
                'delete',
                'apikey',
                ]
    _force_https = True

    def index(self, req, form):
        redirect_to_url(req, '%s/youraccount/display' % CFG_SITE_SECURE_URL)

    def access(self, req, form):
        args = wash_urlargd(form, {'mailcookie' : (str, '')})
        _ = gettext_set_language(args['ln'])
        title = _("Mail Cookie Service")
        try:
            kind = mail_cookie_retrieve_kind(args['mailcookie'])
            if kind == 'pw_reset':
                redirect_to_url(req, '%s/youraccount/resetpassword?k=%s&ln=%s' % (CFG_SITE_SECURE_URL, args['mailcookie'], args['ln']))
            elif kind == 'role':
                uid = webuser.getUid(req)
                try:
                    (role_name, expiration) = mail_cookie_check_role(args['mailcookie'], uid)
                except InvenioWebAccessMailCookieDeletedError:
                    return page(title=_("Role authorization request"), req=req, body=_("This request for an authorization has already been authorized."), uid=webuser.getUid(req), navmenuid='youraccount', language=args['ln'], secure_page_p=1)
                return page(title=title,
                body=webaccount.perform_back(
                    _("You have successfully obtained an authorization as %(x_role)s! "
                    "This authorization will last until %(x_expiration)s and until "
                    "you close your browser if you are a guest user.") %
                    {'x_role' : '<strong>%s</strong>' % role_name,
                     'x_expiration' : '<em>%s</em>' % expiration.strftime("%Y-%m-%d %H:%M:%S")},
                    '/youraccount/display?ln=%s' % args['ln'], _('login'), args['ln']),
                req=req,
                uid=webuser.getUid(req),
                language=args['ln'],
                lastupdated='',
                navmenuid='youraccount',
                secure_page_p=1)
            elif kind == 'mail_activation':
                try:
                    email = mail_cookie_check_mail_activation(args['mailcookie'])
                    if not email:
                        raise StandardError
                    webuser.confirm_email(email)
                    body = "<p>" + _("You have confirmed the validity of your email"
                        " address!") + "</p>"
                    if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS == 1:
                        body += "<p>" + _("Please, wait for the administrator to "
                            "enable your account.") + "</p>"
                    else:
                        uid = webuser.update_Uid(req, email)
                        body += "<p>" + _("You can now go to %(x_url_open)syour account page%(x_url_close)s.") % {'x_url_open' : '<a href="/youraccount/display?ln=%s">' % args['ln'], 'x_url_close' : '</a>'} + "</p>"
                    return page(title=_("Email address successfully activated"),
                    body=body, req=req, language=args['ln'], uid=webuser.getUid(req), lastupdated='', navmenuid='youraccount', secure_page_p=1)
                except InvenioWebAccessMailCookieDeletedError:
                    body = "<p>" + _("You have already confirmed the validity of your email address!") + "</p>"
                    if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS == 1:
                        body += "<p>" + _("Please, wait for the administrator to "
                            "enable your account.") + "</p>"
                    else:
                        body += "<p>" + _("You can now go to %(x_url_open)syour account page%(x_url_close)s.") % {'x_url_open' : '<a href="/youraccount/display?ln=%s">' % args['ln'], 'x_url_close' : '</a>'} + "</p>"
                    return page(title=_("Email address successfully activated"),
                        body=body, req=req, language=args['ln'], uid=webuser.getUid(req), lastupdated='', navmenuid='youraccount', secure_page_p=1)
                return webuser.page_not_authorized(req, "../youraccount/access",
                    text=_("This request for confirmation of an email "
                    "address is not valid or"
                    " is expired."), navmenuid='youraccount')
        except InvenioWebAccessMailCookieError:
            return webuser.page_not_authorized(req, "../youraccount/access",
                text=_("This request for an authorization is not valid or"
                " is expired."), navmenuid='youraccount')

    def apikey(self, req, form):
        args = wash_urlargd(form, {
                                   'key_description' : (str, None),
                                   'key_id' : (str, None),
                                   'referer': (str, ''),
                                   'csrf_token' : (str, None),
                                   })

        # do not allow non-POST methods in here:
        if req.method != 'POST':
            raise apache.SERVER_RETURN(apache.HTTP_METHOD_NOT_ALLOWED)

        # check CSRF token:
        if not webuser.is_csrf_token_valid(req, args['csrf_token']):
            raise apache.SERVER_RETURN(apache.HTTP_FORBIDDEN)

        uid = webuser.getUid(req)
        # load the right message language
        _ = gettext_set_language(args['ln'])

        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return webuser.page_not_authorized(req, "../youraccount/edit",
                                               navmenuid='youraccount')
        if webuser.isGuestUser(uid):
            return webuser.page_not_authorized(req, "../youraccount/edit",
                                               text=_("This functionality is forbidden to guest users."),
                                               navmenuid='youraccount')

        if args['key_id']:
            web_api_key.mark_web_api_key_as_removed(args['key_id'])
        else:
            uid = webuser.getUid(req)
            web_api_key.create_new_web_api_key(uid, args['key_description'])

        if args['referer']:
            redirect_to_url(req, args['referer'])
        else:
            redirect_to_url(req, '%s/youraccount/edit?ln=%s' % (CFG_SITE_SECURE_URL, args['ln']))

    def edit(self, req, form):
        args = wash_urlargd(form, {"verbose" : (int, 0)})
        uid = webuser.getUid(req)

        # load the right message language
        _ = gettext_set_language(args['ln'])

        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return webuser.page_not_authorized(req, "../youraccount/edit",
                                               navmenuid='youraccount')

        if webuser.isGuestUser(uid):
            return webuser.page_not_authorized(req, "../youraccount/edit",
                                               text=_("This functionality is forbidden to guest users."),
                                               navmenuid='youraccount')
        body = ''

        user_info = webuser.collect_user_info(req)
        if args['verbose'] == 9:
            keys = user_info.keys()
            keys.sort()
            for key in keys:
                body += "<b>%s</b>:%s<br />" % (key, user_info[key])

        # set CSRF token:
        csrf_token, dummy_csrf_token_time = webuser.regenerate_csrf_token_if_needed(req)

        #check if the user should see bibcatalog user name / passwd in the settings
        can_config_bibcatalog = (acc_authorize_action(user_info, 'runbibedit')[0] == 0)
        can_config_profiling = (acc_authorize_action(user_info, 'profiling')[0] == 0)
        return page(title= _("Your Settings"),
                    body=body+webaccount.perform_set(webuser.get_email(uid),
                                                     args['ln'],
                                                     can_config_bibcatalog,
                                                     can_config_profiling,
                                                     verbose=args['verbose'],
                                                     csrf_token=csrf_token),
                    navtrail="""<a class="navtrail" href="%s/youraccount/display?ln=%s">""" % (CFG_SITE_SECURE_URL, args['ln']) + _("Your Account") + """</a>""",
                    description=_("%(x_name)s Personalize, Your Settings", x_name=CFG_SITE_NAME_INTL.get(args['ln'], CFG_SITE_NAME)),
                    keywords=_("%(x_name)s, personalize", x_name=CFG_SITE_NAME_INTL.get(args['ln'], CFG_SITE_NAME)),
                    uid=uid,
                    req=req,
                    secure_page_p = 1,
                    language=args['ln'],
                    lastupdated='',
                    navmenuid='youraccount')


    def send_email(self, req, form):
        # set all the declared query fields as local variables
        args = wash_urlargd(form, {'p_email': (str, None)})
        uid = webuser.getUid(req)

        # load the right message language
        _ = gettext_set_language(args['ln'])

        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return webuser.page_not_authorized(req, "../youraccount/send_email",
                                               navmenuid='youraccount')

        user_prefs = webuser.get_user_preferences(webuser.emailUnique(args['p_email']))
        if user_prefs:
            if user_prefs['login_method'] in CFG_EXTERNAL_AUTHENTICATION and \
               CFG_EXTERNAL_AUTHENTICATION[user_prefs['login_method']] is not None:
                eMsg = _("Cannot send password reset request since you are using external authentication system.")
                return page(title=_("Your Account"),
                            body=webaccount.perform_emailMessage(eMsg, args['ln']),
                            description="%s Personalize, Main page" % CFG_SITE_NAME_INTL.get(args['ln'], CFG_SITE_NAME),
                            keywords=_("%(x_name)s, personalize", x_name=CFG_SITE_NAME_INTL.get(args['ln'], CFG_SITE_NAME)),
                            uid=uid, req=req,
                            secure_page_p = 1,
                            language=args['ln'],
                            lastupdated='',
                            navmenuid='youraccount')

        try:
            reset_key = mail_cookie_create_pw_reset(args['p_email'], cookie_timeout=timedelta(days=CFG_WEBSESSION_RESET_PASSWORD_EXPIRE_IN_DAYS))
        except InvenioWebAccessMailCookieError:
            reset_key = None
        if reset_key is None:
            eMsg = _("The entered email address does not exist in the database.")
            return page(title=_("Your Account"),
                        body=webaccount.perform_emailMessage(eMsg, args['ln']),
                        description="%s Personalize, Main page" % CFG_SITE_NAME_INTL.get(args['ln'], CFG_SITE_NAME),
                        keywords=_("%(x_name)s, personalize", x_name=CFG_SITE_NAME_INTL.get(args['ln'], CFG_SITE_NAME)),
                        uid=uid, req=req,
                        secure_page_p = 1,
                        language=args['ln'],
                        lastupdated='',
                        navmenuid='youraccount')

        ip_address = req.remote_host or req.remote_ip

        if not send_email(CFG_SITE_SUPPORT_EMAIL, args['p_email'], "%s %s"
                % (_("Password reset request for"),
                CFG_SITE_NAME_INTL.get(args['ln'], CFG_SITE_NAME)),
                websession_templates.tmpl_account_reset_password_email_body(
                    args['p_email'],reset_key, ip_address, args['ln'])):
            eMsg = _("The entered email address is incorrect, please check that it is written correctly (e.g. johndoe@example.com).")
            return page(title=_("Incorrect email address"),
                        body=webaccount.perform_emailMessage(eMsg, args['ln']),
                        description="%s Personalize, Main page" % CFG_SITE_NAME_INTL.get(args['ln'], CFG_SITE_NAME),
                        keywords=_("%(x_name)s, personalize", x_name=CFG_SITE_NAME_INTL.get(args['ln'], CFG_SITE_NAME)),
                        uid=uid,
                        req=req,
                        secure_page_p = 1,
                        language=args['ln'],
                        lastupdated='',
                        navmenuid='youraccount')
        return page(title=_("Reset password link sent"),
                    body=webaccount.perform_emailSent(args['p_email'], args['ln']),
                    description="%s Personalize, Main page" % CFG_SITE_NAME_INTL.get(args['ln'], CFG_SITE_NAME),
                    keywords=_("%(x_name)s, personalize", x_name=CFG_SITE_NAME_INTL.get(args['ln'], CFG_SITE_NAME)),
                    uid=uid, req=req,
                    secure_page_p = 1,
                    language=args['ln'],
                    lastupdated='',
                    navmenuid='youraccount')

    def youradminactivities(self, req, form):
        args = wash_urlargd(form, {})
        uid = webuser.getUid(req)
        user_info = webuser.collect_user_info(req)

        # load the right message language
        _ = gettext_set_language(args['ln'])

        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return webuser.page_not_authorized(req, "../youraccount/youradminactivities",
                                               navmenuid='admin')

        return page(title=_("Your Administrative Activities"),
                    body=webaccount.perform_youradminactivities(user_info, args['ln']),
                    navtrail="""<a class="navtrail" href="%s/youraccount/display?ln=%s">""" % (CFG_SITE_SECURE_URL, args['ln']) + _("Your Account") + """</a>""",
                    description="%s Personalize, Main page" % CFG_SITE_NAME_INTL.get(args['ln'], CFG_SITE_NAME),
                    keywords=_("%(x_name)s, personalize", x_name=CFG_SITE_NAME_INTL.get(args['ln'], CFG_SITE_NAME)),
                    uid=uid,
                    req=req,
                    secure_page_p = 1,
                    language=args['ln'],
                    lastupdated='',
                    navmenuid='admin')

    def delete(self, req, form):
        args = wash_urlargd(form, {})
        uid = webuser.getUid(req)

        # load the right message language
        _ = gettext_set_language(args['ln'])

        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return webuser.page_not_authorized(req, "../youraccount/delete",
                                               navmenuid='youraccount')

        return page(title=_("Delete Account"),
                    body=webaccount.perform_delete(args['ln']),
                    navtrail="""<a class="navtrail" href="%s/youraccount/display?ln=%s">""" % (CFG_SITE_SECURE_URL, args['ln']) + _("Your Account") + """</a>""",
                    description="%s Personalize, Main page" % CFG_SITE_NAME_INTL.get(args['ln'], CFG_SITE_NAME),
                    keywords=_("%(x_name)s, personalize", x_name=CFG_SITE_NAME_INTL.get(args['ln'], CFG_SITE_NAME)),
                    uid=uid,
                    req=req,
                    secure_page_p = 1,
                    language=args['ln'],
                    lastupdated='',
                    navmenuid='youraccount')


class WebInterfaceYourTicketsPages(WebInterfaceDirectory):
    #support for /yourtickets url
    _exports = ['', 'display']

    def __call__(self, req, form):
        #if there is no trailing slash
        self.index(req, form)

    def index(self, req, form):
        #take all the parameters..
        unparsed_uri = req.unparsed_uri
        qstr = ""
        if unparsed_uri.count('?') > 0:
            dummy, qstr = unparsed_uri.split('?')
            qstr = '?'+qstr
        redirect_to_url(req, '/yourtickets/display'+qstr)

    def display(self, req, form):
        #show tickets for this user
        argd = wash_urlargd(form, {'ln': (str, ''), 'start': (int, 1) })
        uid = webuser.getUid(req)
        ln = argd['ln']
        start = argd['start']
        _ = gettext_set_language(ln)
        body = bibcatalog_templates.tmpl_your_tickets(uid, ln, start)
        return page(title=_("Your tickets"),
                    body=body,
                    navtrail="""<a class="navtrail" href="%s/youraccount/display?ln=%s">""" % (CFG_SITE_SECURE_URL, argd['ln']) + _("Your Account") + """</a>""",
                    uid=uid,
                    req=req,
                    language=argd['ln'],
                    lastupdated='',
                    secure_page_p=1)


def wash_login_method(login_method):
    """
    Wash the login_method parameter that came from the web input form.

    @param login_method: Wanted login_method value as it came from the
        web input form.
    @type login_method: string

    @return: Washed version of login_method.  If the login_method
        value is valid, then return it.  If it is not valid, then
        return `Local' (the default login method).
    @rtype: string

    @warning: Beware, 'Local' is hardcoded here!
    """
    if login_method in CFG_EXTERNAL_AUTHENTICATION:
        return login_method
    else:
        return 'Local'
