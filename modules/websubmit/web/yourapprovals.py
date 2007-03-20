## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

## import interesting modules:
import os
import sys

from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     cdslang, \
     cdsname, \
     sweburl, \
     version
from invenio.dbquery import run_sql, Error
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_admin import *
from invenio.webpage import page, create_error_box
from invenio.webuser import getUid, get_email, list_registered_users, page_not_authorized
from invenio.messages import gettext_set_language, wash_language
from invenio.websubmit_config import *
from invenio.search_engine import search_pattern

import invenio.template
websubmit_templates = invenio.template.load('websubmit')

def index(req,c=cdsname,ln=cdslang,order="",doctype="",deletedId="",deletedAction="",deletedDoctype=""):
    global uid
    ln = wash_language(ln)

    # load the right message language
    _ = gettext_set_language(ln)

    t=""
    # get user ID:
    try:
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourapprovals.py/index",
                                       navmenuid='yourapprovals')
        u_email = get_email(uid)
    except Error, e:
        return errorMsg(e.value,req, ln = ln)

    res = run_sql("select sdocname,ldocname from sbmDOCTYPE")
    referees = []
    for row in res:
        doctype = row[0]
        docname = row[1]
        reftext = ""
        if isReferee(uid,doctype,"*"):
            referees.append ({'doctype': doctype,
                              'docname': docname,
                              'categories': None})
        else:
            res2 = run_sql("select sname,lname from sbmCATEGORIES where doctype=%s",(doctype,))
            categories = []
            for row2 in res2:
                category = row2[0]
                categname = row2[1]
                if isReferee(uid,doctype,category):
                    categories.append({
                                        'id' : category,
                                        'name' : categname,
                                      })
            referees.append({
                            'doctype' : doctype,
                            'docname' : docname,
                            'categories' : categories
                           })


    t = websubmit_templates.tmpl_yourapprovals(
          ln = ln,
          referees = referees
        )
    return page(title=_("Your Approvals"),
                navtrail= """<a class="navtrail" href="%(sweburl)s/youraccount/display">%(account)s</a>""" % {
                             'sweburl' : sweburl,
                             'account' : _("Your Account"),
                          },
                body=t,
                description="",
                keywords="",
                uid=uid,
                language=ln,
                req=req,
                navmenuid='yourapprovals')

def isReferee(uid,doctype="",categ=""):
    (auth_code, auth_message) = acc_authorize_action(uid, "referee",verbose=0,doctype=doctype, categ=categ)
    if auth_code == 0:
        return 1
    else:
        return 0

def errorMsg(title,req,c=cdsname,ln=cdslang):
    return page(title="error",
                body = create_error_box(req, title=title,verbose=0, ln=ln),
                description="%s - Internal Error" % c,
                keywords="%s, CDS Invenio, Internal Error" % c,
                language=ln,
                req=req,
                navmenuid='yourapprovals')

