## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""PERSONAL FEATURES - YOUR ALERTS"""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

from invenio.config import CFG_SITE_SECURE_URL, CFG_SITE_NAME, \
  CFG_ACCESS_CONTROL_LEVEL_SITE, CFG_SITE_NAME_INTL
from invenio.webpage import page
from invenio.webalert import perform_input_alert, \
                             perform_request_youralerts_display, \
                             perform_add_alert, \
                             perform_update_alert, \
                             perform_remove_alert, \
                             perform_request_youralerts_popular, \
                             AlertError
from invenio.webuser import getUid, page_not_authorized, isGuestUser
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.urlutils import redirect_to_url, make_canonical_urlargd
from invenio.webstat import register_customevent
from invenio.errorlib import register_exception
from invenio.webuser import collect_user_info

from invenio.messages import gettext_set_language
import invenio.template
webalert_templates = invenio.template.load('webalert')

class WebInterfaceYourAlertsPages(WebInterfaceDirectory):
    """Defines the set of /youralerts pages."""

    _exports = ['',
                'display',
                'input',
                'modify',
                'list',
                'add',
                'update',
                'remove',
                'popular']

    def index(self, req, dummy):
        """Index page."""

        redirect_to_url(req, '%s/youralerts/display' % CFG_SITE_SECURE_URL)

    def list(self, req, form):
        """
        Legacy youralerts list page.
        Now redirects to the youralerts display page.
        """

        redirect_to_url(req, '%s/youralerts/display' % (CFG_SITE_SECURE_URL,))

    def input(self, req, form):

        argd = wash_urlargd(form, {'idq': (int, None),
                                   'name': (str, ""),
                                   'freq': (str, "week"),
                                   'notif': (str, "y"),
                                   'idb': (int, 0),
                                   'error_msg': (str, ""),
                                   })

        uid = getUid(req)

        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/youralerts/input" % \
                                             (CFG_SITE_SECURE_URL,),
                                       navmenuid="youralerts")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/youralerts/input%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        # load the right language
        _ = gettext_set_language(argd['ln'])
        user_info = collect_user_info(req)
        if not user_info['precached_usealerts']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use alerts."))

        try:
            html = perform_input_alert("add", argd['idq'], argd['name'], argd['freq'],
                                                argd['notif'], argd['idb'], uid, ln=argd['ln'])
        except AlertError, msg:
            return page(title=_("Error"),
                        body=webalert_templates.tmpl_errorMsg(ln=argd['ln'], error_msg=msg),
                        navtrail= """<a class="navtrail" href="%(sitesecureurl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                     'sitesecureurl' : CFG_SITE_SECURE_URL,
                                     'ln': argd['ln'],
                                     'account' : _("Your Account"),
                                  },
                        description=_("%s Personalize, Set a new alert") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                        keywords=_("%s, personalize") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                        uid=uid,
                        language=argd['ln'],
                        req=req,
                        lastupdated=__lastupdated__,
                        navmenuid='youralerts')

        if argd['error_msg'] != "":
            html = webalert_templates.tmpl_errorMsg(
                     ln = argd['ln'],
                     error_msg = argd['error_msg'],
                     rest = html,
                   )

        # register event in webstat
        alert_str = "%s (%d)" % (argd['name'], argd['idq'])
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("alerts", ["input", alert_str, user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title=_("Set a new alert"),
                    body=html,
                    navtrail= """<a class="navtrail" href="%(sitesecureurl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                 'sitesecureurl' : CFG_SITE_SECURE_URL,
                                 'ln': argd['ln'],
                                 'account' : _("Your Account"),
                              },
                    description=_("%s Personalize, Set a new alert") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                    keywords=_("%s, personalize") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                    uid=uid,
                    language=argd['ln'],
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='youralerts')

    def modify(self, req, form):

        argd = wash_urlargd(form, {'idq': (int, None),
                                   'old_idb': (int, None),
                                   'name': (str, ""),
                                   'freq': (str, "week"),
                                   'notif': (str, "y"),
                                   'idb': (int, 0),
                                   'error_msg': (str, ""),
                                   })

        uid = getUid(req)

        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/youralerts/modify" % \
                                             (CFG_SITE_SECURE_URL,),
                                       navmenuid="youralerts")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/youralerts/modify%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        # load the right language
        _ = gettext_set_language(argd['ln'])
        user_info = collect_user_info(req)
        if not user_info['precached_usealerts']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use alerts."))

        try:
            html = perform_input_alert("update", argd['idq'], argd['name'], argd['freq'],
                                                argd['notif'], argd['idb'], uid, argd['old_idb'], ln=argd['ln'])
        except AlertError, msg:
            return page(title=_("Error"),
                        body=webalert_templates.tmpl_errorMsg(ln=argd['ln'], error_msg=msg),
                        navtrail= """<a class="navtrail" href="%(sitesecureurl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                     'sitesecureurl' : CFG_SITE_SECURE_URL,
                                     'ln': argd['ln'],
                                     'account' : _("Your Account"),
                                  },
                        description=_("%s Personalize, Set a new alert") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                        keywords=_("%s, personalize") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                        uid=uid,
                        language=argd['ln'],
                        req=req,
                        lastupdated=__lastupdated__,
                        navmenuid='youralerts')

        if argd['error_msg'] != "":
            html = webalert_templates.tmpl_errorMsg(
                     ln = argd['ln'],
                     error_msg = argd['error_msg'],
                     rest = html,
                   )

        # register event in webstat
        alert_str = "%s (%d)" % (argd['name'], argd['idq'])
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("alerts", ["modify", alert_str, user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title=_("Modify alert settings"),
                    body=html,
                    navtrail= """<a class="navtrail" href="%(sitesecureurl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                 'sitesecureurl' : CFG_SITE_SECURE_URL,
                                 'ln': argd['ln'],
                                 'account' : _("Your Account"),
                              },
                    description=_("%s Personalize, Modify alert settings") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                    keywords=_("%s, personalize") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                    uid=uid,
                    language=argd['ln'],
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='youralerts')

    def display(self, req, form):

        argd = wash_urlargd(form, {})

        uid = getUid(req)

        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/youralerts/display" % \
                                             (CFG_SITE_SECURE_URL,),
                                       navmenuid="youralerts")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/youralerts/display%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        # load the right language
        _ = gettext_set_language(argd['ln'])
        user_info = collect_user_info(req)
        if not user_info['precached_usealerts']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use alerts."))

        # register event in webstat
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("alerts", ["display", "", user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title=_("Your Alerts"),
                    body=perform_request_youralerts_display(uid, ln = argd['ln']),
                    navtrail= """<a class="navtrail" href="%(sitesecureurl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                 'sitesecureurl' : CFG_SITE_SECURE_URL,
                                 'ln': argd['ln'],
                                 'account' : _("Your Account"),
                              },
                    description=_("%s Personalize, Display alerts") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                    keywords=_("%s, personalize") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                    uid=uid,
                    language=argd['ln'],
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='youralerts')

    def add(self, req, form):

        argd = wash_urlargd(form, {'idq': (int, None),
                                   'name': (str, None),
                                   'freq': (str, None),
                                   'notif': (str, None),
                                   'idb': (int, None),
                                   })

        uid = getUid(req)

        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/youralerts/add" % \
                                             (CFG_SITE_SECURE_URL,),
                                       navmenuid="youralerts")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/youralerts/add%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        # load the right language
        _ = gettext_set_language(argd['ln'])
        user_info = collect_user_info(req)
        if not user_info['precached_usealerts']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use alerts."))

        try:
            html = perform_add_alert(argd['name'], argd['freq'], argd['notif'],
                                              argd['idb'], argd['idq'], uid, ln=argd['ln'])
        except AlertError, msg:
            return page(title=_("Error"),
                        body=webalert_templates.tmpl_errorMsg(ln=argd['ln'], error_msg=msg),
                        navtrail= """<a class="navtrail" href="%(sitesecureurl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                     'sitesecureurl' : CFG_SITE_SECURE_URL,
                                     'ln': argd['ln'],
                                     'account' : _("Your Account"),
                                  },
                        description=_("%s Personalize, Set a new alert") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                        keywords=_("%s, personalize") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                        uid=uid,
                        language=argd['ln'],
                        req=req,
                        lastupdated=__lastupdated__,
                        navmenuid='youralerts')

        # register event in webstat
        alert_str = "%s (%d)" % (argd['name'], argd['idq'])
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("alerts", ["add", alert_str, user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title=_("Display alerts"),
                    body=html,
                    navtrail= """<a class="navtrail" href="%(sitesecureurl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                 'sitesecureurl' : CFG_SITE_SECURE_URL,
                                 'ln': argd['ln'],
                                 'account' : _("Your Account"),
                              },
                    description=_("%s Personalize, Display alerts") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                    keywords=_("%s, personalize") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                    uid=uid,
                    language=argd['ln'],
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='youralerts')

    def update(self, req, form):

        argd = wash_urlargd(form, {'name': (str, None),
                                   'freq': (str, None),
                                   'notif': (str, None),
                                   'idb': (int, None),
                                   'idq': (int, None),
                                   'old_idb': (int, None),
                                   })

        uid = getUid(req)

        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/youralerts/update" % \
                                             (CFG_SITE_SECURE_URL,),
                                       navmenuid="youralerts")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/youralerts/update%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        # load the right language
        _ = gettext_set_language(argd['ln'])
        user_info = collect_user_info(req)
        if not user_info['precached_usealerts']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use alerts."))

        try:
            html = perform_update_alert(argd['name'], argd['freq'], argd['notif'],
                                                 argd['idb'], argd['idq'], argd['old_idb'], uid, ln=argd['ln'])
        except AlertError, msg:
            return page(title=_("Error"),
                        body=webalert_templates.tmpl_errorMsg(ln=argd['ln'], error_msg=msg),
                        navtrail= """<a class="navtrail" href="%(sitesecureurl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                     'sitesecureurl' : CFG_SITE_SECURE_URL,
                                     'ln': argd['ln'],
                                     'account' : _("Your Account"),
                                  },
                        description=_("%s Personalize, Set a new alert") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                        keywords=_("%s, personalize") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                        uid=uid,
                        language=argd['ln'],
                        req=req,
                        lastupdated=__lastupdated__,
                        navmenuid='youralerts')

        # register event in webstat
        alert_str = "%s (%d)" % (argd['name'], argd['idq'])
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("alerts", ["update", alert_str, user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title=_("Display alerts"),
                    body=html,
                    navtrail= """<a class="navtrail" href="%(sitesecureurl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                 'sitesecureurl' : CFG_SITE_SECURE_URL,
                                 'ln': argd['ln'],
                                 'account' : _("Your Account"),
                              },
                    description=_("%s Personalize, Display alerts") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                    keywords=_("%s, personalize") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                    uid=uid,
                    language=argd['ln'],
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='youralerts')

    def remove(self, req, form):

        argd = wash_urlargd(form, {'name': (str, None),
                                   'idq': (int, None),
                                   'idb': (int, None),
                                   })

        uid = getUid(req)

        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/youralerts/remove" % \
                                             (CFG_SITE_SECURE_URL,),
                                       navmenuid="youralerts")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/youralerts/remove%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        # load the right language
        _ = gettext_set_language(argd['ln'])
        user_info = collect_user_info(req)
        if not user_info['precached_usealerts']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use alerts."))

        try:
            html = perform_remove_alert(argd['name'], argd['idq'],
                                                 argd['idb'], uid, ln=argd['ln'])
        except AlertError, msg:
            return page(title=_("Error"),
                        body=webalert_templates.tmpl_errorMsg(ln=argd['ln'], error_msg=msg),
                        navtrail= """<a class="navtrail" href="%(sitesecureurl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                     'sitesecureurl' : CFG_SITE_SECURE_URL,
                                     'ln': argd['ln'],
                                     'account' : _("Your Account"),
                                  },
                        description=_("%s Personalize, Set a new alert") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                        keywords=_("%s, personalize") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                        uid=uid,
                        language=argd['ln'],
                        req=req,
                        lastupdated=__lastupdated__,
                        navmenuid='youralerts')


        # register event in webstat
        alert_str = "%s (%d)" % (argd['name'], argd['idq'])
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("alerts", ["remove", alert_str, user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        # display success
        return page(title=_("Display alerts"),
                    body=html,
                    navtrail= """<a class="navtrail" href="%(sitesecureurl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                 'sitesecureurl' : CFG_SITE_SECURE_URL,
                                 'ln': argd['ln'],
                                 'account' : _("Your Account"),
                              },
                    description=_("%s Personalize, Display alerts") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                    keywords=_("%s, personalize") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                    uid=uid,
                    language=argd['ln'],
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='youralerts')

    def popular(self, req, form):
        """
        Display a list of popular alerts.
        """

        argd = wash_urlargd(form, {'ln': (str, "en")})

        uid = getUid(req)

        # load the right language
        _ = gettext_set_language(argd['ln'])

        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/youralerts/popular" % \
                                            (CFG_SITE_SECURE_URL,),
                                       navmenuid="youralerts")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % \
                                        (CFG_SITE_SECURE_URL,
                                         make_canonical_urlargd(
                                            {'referer' : "%s/youralerts/popular%s" % (
                                                CFG_SITE_SECURE_URL,
                                                make_canonical_urlargd(argd, {})),
                                             'ln' : argd['ln']},
                                            {})
                                         )
            )

        user_info = collect_user_info(req)
        if not user_info['precached_usealerts']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use alerts."))

        # register event in webstat
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("alerts", ["popular", "", user_str])
        except:
            register_exception(
                suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title=_("Popular Alerts"),
                    body = perform_request_youralerts_popular(ln=argd['ln']),
                    navtrail = """<a class="navtrail" href="%(sitesecureurl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                  'sitesecureurl' : CFG_SITE_SECURE_URL,
                                  'ln': argd['ln'],
                                  'account' : _("Your Account"),
                                  },
                    description=_("%s Personalize, Popular Alerts") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                    keywords=_("%s, personalize") % CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME),
                    uid=uid,
                    language=argd['ln'],
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='youralerts',
                    secure_page_p=1)
