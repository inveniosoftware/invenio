## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
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

"""PERSONAL FEATURES - YOUR ALERTS"""

__lastupdated__ = """<: print `date +"%d %b %Y %H:%M:%S %Z"`; :>"""

import sys
import time
import zlib
import urllib
import time
from mod_python import apache

from cdsware.config import weburl, cdslang, cdsname
from cdsware.webpage import page
from cdsware import webalert
from cdsware.webuser import getUid, page_not_authorized
from cdsware.access_control_config import CFG_ACCESS_CONTROL_LEVEL_SITE

from cdsware.messages import gettext_set_language
import cdsware.template
webalert_templates = cdsware.template.load('webalert')

def relative_redirect( req, relative_url, **args ):
    tmp = []
    for param in args.keys():
        #ToDo: url encoding of the params
        tmp.append( "%s=%s"%( param, args[param] ) )
    req.err_headers_out.add("Location", "%s/%s?%s" % (weburl, relative_url, "&".join( tmp ) ))
    raise apache.SERVER_RETURN, apache.HTTP_MOVED_PERMANENTLY

### CALLABLE INTERFACE

def display(req, p="n", ln = cdslang):
    uid = getUid(req)

    # load the right message language
    _ = gettext_set_language(ln)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return page_not_authorized(req, "../youralerts.py/display")

    return page(title=_("Display searches"),
                body=webalert.perform_display(p,uid, ln = ln),
                navtrail= """<a class="navtrail" href="%(weburl)s/youraccount.py/display">%(account)s</a>""" % {
                             'weburl' : weburl,
                             'account' : _("Your Account"),
                          },
                description="CDS Personalize, Display searches",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def input(req, idq, name="", freq="week", notif="y", idb=0, error_msg="", ln = cdslang):
    uid = getUid(req)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return page_not_authorized(req, "../youralerts.py/input")

    # load the right message language
    _ = gettext_set_language(ln)

    html = webalert.perform_input_alert("add", idq, name, freq, notif, idb,uid, ln = ln)
    if error_msg != "":
        html = webalert_templates.tmpl_errorMsg(
                 ln = ln,
                 error_msg = error_msg,
                 rest = html,
               )
    return page(title=_("Set a new alert"),
                body=html,
                navtrail= """<a class="navtrail" href="%(weburl)s/youraccount.py/display">%(account)s</a>""" % {
                             'weburl' : weburl,
                             'account' : _("Your Account"),
                          },
                description="CDS Personalize, Set a new alert",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def modify(req, idq, old_idb, name="", freq="week", notif="y", idb=0, error_msg="", ln = cdslang):
    uid = getUid(req)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return page_not_authorized(req, "../youralerts.py/modify")

    # load the right message language
    _ = gettext_set_language(ln)

    html = webalert.perform_input_alert("update", idq, name, freq, notif, idb, uid, old_idb, ln = ln)
    if error_msg != "":
        html = webalert_templates.tmpl_errorMsg(
                 ln = ln,
                 error_msg = error_msg,
                 rest = html,
               )
    return page(title=_("Modify alert settings"),
                body=html,
                navtrail= """<a class="navtrail" href="%(weburl)s/youraccount.py/display">%(account)s</a>""" % {
                             'weburl' : weburl,
                             'account' : _("Your Account"),
                          },
                description="CDS Personalize, Modify alert settings",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def list(req, ln = cdslang):
    uid = getUid(req)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return page_not_authorized(req, "../youralerts.py/list")

    # load the right message language
    _ = gettext_set_language(ln)

    return page(title=_("Display alerts"),
                body=webalert.perform_list_alerts(uid, ln = ln),
                navtrail= """<a class="navtrail" href="%(weburl)s/youraccount.py/display">%(account)s</a>""" % {
                             'weburl' : weburl,
                             'account' : _("Your Account"),
                          },
                description="CDS Personalize, Display alerts",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def add(req, name, freq, notif, idb, idq, ln = cdslang):
    uid = getUid(req)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return page_not_authorized(req, "../youralerts.py/add")

    # load the right message language
    _ = gettext_set_language(ln)

    try:
        html=webalert.perform_add_alert(name, freq, notif, idb, idq, uid, ln = ln)
    except webalert.AlertError, e:
        return input(req, idq, name, freq, notif, idb, e, ln = ln)
    return page(title=_("Display alerts"),
                body=html,
                navtrail= """<a class="navtrail" href="%(weburl)s/youraccount.py/display">%(account)s</a>""" % {
                             'weburl' : weburl,
                             'account' : _("Your Account"),
                          },
                description="CDS Personalize, Display alerts",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def update(req, name, freq, notif, idb, idq, old_idb, ln = cdslang):
    uid = getUid(req)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return page_not_authorized(req, "../youralerts.py/update")

    # load the right message language
    _ = gettext_set_language(ln)

    try:
        html=webalert.perform_update_alert(name, freq, notif, idb, idq, old_idb,uid, ln = ln)
    except webalert.AlertError, e:
        return modify(req, idq, old_idb, name, freq, notif, idb, e, ln = ln)
    return page(title=_("Display alerts"),
                body=html,
                navtrail= """<a class="navtrail" href="%(weburl)s/youraccount.py/display">%(account)s</a>""" % {
                             'weburl' : weburl,
                             'account' : _("Your Account"),
                          },
                description="CDS Personalize, Display alerts",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def remove(req, name, idu, idq, idb, ln = cdslang):
    uid = getUid(req)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return page_not_authorized(req, "../youralerts.py/remove")

    # load the right message language
    _ = gettext_set_language(ln)

    return page(title=_("Display alerts"),
                body=webalert.perform_remove_alert(name, idu, idq, idb, uid, ln = ln),
                navtrail= """<a class="navtrail" href="%(weburl)s/youraccount.py/display">%(account)s</a>""" % {
                             'weburl' : weburl,
                             'account' : _("Your Account"),
                          },
                description="CDS Personalize, Display alerts",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def errorMsg(title, req, c=cdsname, ln=cdslang):
    return page(title="error",
                body = create_error_box(req, title=title,verbose=0, ln=ln),
                description="%s - Internal Error" % c,
                keywords="%s, CDSware, Internal Error" % c,
                language=ln,
                urlargs=req.args)
