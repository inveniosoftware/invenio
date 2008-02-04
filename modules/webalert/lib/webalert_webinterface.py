## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

"""PERSONAL FEATURES - YOUR ALERTS"""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import sys
import time
import zlib
import urllib
from mod_python import apache

from invenio.config import weburl, sweburl, cdslang, cdsname, \
  CFG_ACCESS_CONTROL_LEVEL_SITE, cdsnameintl
from invenio.webpage import page
from invenio import webalert
from invenio.webuser import getUid, page_not_authorized, isGuestUser
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.urlutils import redirect_to_url, make_canonical_urlargd

from invenio.messages import gettext_set_language
import invenio.template
webalert_templates = invenio.template.load('webalert')

class WebInterfaceYourAlertsPages(WebInterfaceDirectory):
    """Defines the set of /youralerts pages."""

    _exports = ['', 'display', 'input', 'modify', 'list', 'add',
                'update', 'remove']

    def index(self, req, form):
        """Index page."""
        redirect_to_url(req, '%s/youralerts/list' % weburl)

    def display(self, req, form):
        """Display search history page.  A misnomer."""

        argd = wash_urlargd(form, {'p': (str, "n")
                                   })

        uid = getUid(req)

        # load the right message language
        _ = gettext_set_language(argd['ln'])

        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/youralerts/display" % \
                                             (weburl,),
                                       navmenuid="youralerts")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                sweburl,
                make_canonical_urlargd({
                    'referer' : "%s/youralerts/display%s" % (
                        weburl,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        return page(title=_("Display searches"),
                    body=webalert.perform_display(argd['p'], uid, ln=argd['ln']),
                    navtrail= """<a class="navtrail" href="%(sweburl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                 'sweburl' : sweburl,
                                 'ln': argd['ln'],
                                 'account' : _("Your Account"),
                              },
                    description=_("%s Personalize, Display searches") % cdsnameintl.get(argd['ln'], cdsname),
                    keywords=_("%s, personalize") % cdsnameintl.get(argd['ln'], cdsname),
                    uid=uid,
                    language=argd['ln'],
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='youralerts')

    def input(left, req, form):

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
                                             (weburl,),
                                       navmenuid="youralerts")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                sweburl,
                make_canonical_urlargd({
                    'referer' : "%s/youralerts/input%s" % (
                        weburl,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        # load the right message language
        _ = gettext_set_language(argd['ln'])

        html = webalert.perform_input_alert("add", argd['idq'], argd['name'], argd['freq'],
                                            argd['notif'], argd['idb'], uid, ln=argd['ln'])
        if argd['error_msg'] != "":
            html = webalert_templates.tmpl_errorMsg(
                     ln = argd['ln'],
                     error_msg = argd['error_msg'],
                     rest = html,
                   )
        return page(title=_("Set a new alert"),
                    body=html,
                    navtrail= """<a class="navtrail" href="%(sweburl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                 'sweburl' : sweburl,
                                 'ln': argd['ln'],
                                 'account' : _("Your Account"),
                              },
                    description=_("%s Personalize, Set a new alert") % cdsnameintl.get(argd['ln'], cdsname),
                    keywords=_("%s, personalize") % cdsnameintl.get(argd['ln'], cdsname),
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
                                             (weburl,),
                                       navmenuid="youralerts")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                sweburl,
                make_canonical_urlargd({
                    'referer' : "%s/youralerts/modify%s" % (
                        weburl,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        # load the right message language
        _ = gettext_set_language(argd['ln'])

        html = webalert.perform_input_alert("update", argd['idq'], argd['name'], argd['freq'],
                                            argd['notif'], argd['idb'], uid, argd['old_idb'], ln=argd['ln'])
        if argd['error_msg'] != "":
            html = webalert_templates.tmpl_errorMsg(
                     ln = argd['ln'],
                     error_msg = argd['error_msg'],
                     rest = html,
                   )
        return page(title=_("Modify alert settings"),
                    body=html,
                    navtrail= """<a class="navtrail" href="%(sweburl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                 'sweburl' : sweburl,
                                 'ln': argd['ln'],
                                 'account' : _("Your Account"),
                              },
                    description=_("%s Personalize, Modify alert settings") % cdsnameintl.get(argd['ln'], cdsname),
                    keywords=_("%s, personalize") % cdsnameintl.get(argd['ln'], cdsname),
                    uid=uid,
                    language=argd['ln'],
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='youralerts')

    def list(self, req, form):

        argd = wash_urlargd(form, {})

        uid = getUid(req)

        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/youralerts/list" % \
                                             (weburl,),
                                       navmenuid="youralerts")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                sweburl,
                make_canonical_urlargd({
                    'referer' : "%s/youralerts/list%s" % (
                        weburl,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        # load the right message language
        _ = gettext_set_language(argd['ln'])

        return page(title=_("Display alerts"),
                    body=webalert.perform_list_alerts(uid, ln = argd['ln']),
                    navtrail= """<a class="navtrail" href="%(sweburl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                 'sweburl' : sweburl,
                                 'ln': argd['ln'],
                                 'account' : _("Your Account"),
                              },
                    description=_("%s Personalize, Display alerts") % cdsnameintl.get(argd['ln'], cdsname),
                    keywords=_("%s, personalize") % cdsnameintl.get(argd['ln'], cdsname),
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
                                             (weburl,),
                                       navmenuid="youralerts")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                sweburl,
                make_canonical_urlargd({
                    'referer' : "%s/youralerts/add%s" % (
                        weburl,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        # load the right message language
        _ = gettext_set_language(argd['ln'])

        try:
            html = webalert.perform_add_alert(argd['name'], argd['freq'], argd['notif'],
                                              argd['idb'], argd['idq'], uid, ln=argd['ln'])
        except webalert.AlertError, e:
            html = e
            #return self.input(req, form)
        return page(title=_("Display alerts"),
                    body=html,
                    navtrail= """<a class="navtrail" href="%(sweburl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                 'sweburl' : sweburl,
                                 'ln': argd['ln'],
                                 'account' : _("Your Account"),
                              },
                    description=_("%s Personalize, Display alerts") % cdsnameintl.get(argd['ln'], cdsname),
                    keywords=_("%s, personalize") % cdsnameintl.get(argd['ln'], cdsname),
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
                                             (weburl,),
                                       navmenuid="youralerts")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                sweburl,
                make_canonical_urlargd({
                    'referer' : "%s/youralerts/update%s" % (
                        weburl,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        # load the right message language
        _ = gettext_set_language(argd['ln'])

        try:
            html = webalert.perform_update_alert(argd['name'], argd['freq'], argd['notif'],
                                                 argd['idb'], argd['idq'], argd['old_idb'], uid, ln=argd['ln'])
        except webalert.AlertError, e:
            return self.modify(req, form)
        return page(title=_("Display alerts"),
                    body=html,
                    navtrail= """<a class="navtrail" href="%(sweburl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                 'sweburl' : sweburl,
                                 'ln': argd['ln'],
                                 'account' : _("Your Account"),
                              },
                    description=_("%s Personalize, Display alerts") % cdsnameintl.get(argd['ln'], cdsname),
                    keywords=_("%s, personalize") % cdsnameintl.get(argd['ln'], cdsname),
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
                                             (weburl,),
                                       navmenuid="youralerts")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                sweburl,
                make_canonical_urlargd({
                    'referer' : "%s/youralerts/remove%s" % (
                        weburl,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        # load the right message language
        _ = gettext_set_language(argd['ln'])

        return page(title=_("Display alerts"),
                    body=webalert.perform_remove_alert(argd['name'], argd['idq'],
                                                       argd['idb'], uid, ln=argd['ln']),
                    navtrail= """<a class="navtrail" href="%(sweburl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                 'sweburl' : sweburl,
                                 'ln': argd['ln'],
                                 'account' : _("Your Account"),
                              },
                    description=_("%s Personalize, Display alerts") % cdsnameintl.get(argd['ln'], cdsname),
                    keywords=_("%s, personalize") % cdsnameintl.get(argd['ln'], cdsname),
                    uid=uid,
                    language=argd['ln'],
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='youralerts')
