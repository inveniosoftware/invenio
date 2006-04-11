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

## import interesting modules:
import os
import sys

from cdsware.config import weburl,cdsname,cdslang
from cdsware.dbquery import run_sql
from cdsware.access_control_engine import acc_authorize_action
from cdsware.access_control_admin import *
from cdsware.webpage import page, create_error_box
from cdsware.webuser import getUid, get_email, list_registered_users, page_not_authorized
from cdsware.messages import gettext_set_language, wash_language
from cdsware.websubmit_config import *
from cdsware.search_engine import search_pattern
from cdsware.access_control_config import CFG_ACCESS_CONTROL_LEVEL_SITE

import cdsware.template
websubmit_templates = cdsware.template.load('websubmit')

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
            return page_not_authorized(req, "../yourapprovals.py/index")
        u_email = get_email(uid)
    except MySQLdb.Error, e:
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
                navtrail= """<a class="navtrail" href="%(weburl)s/youraccount.py/display">%(account)s</a>""" % {
                             'weburl' : weburl,
                             'account' : _("Your Account"),
                          },
                body=t,
                description="",
                keywords="",
                uid=uid,
                language=ln,
                urlargs=req.args)

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
                    keywords="%s, CDSware, Internal Error" % c,
                    language=ln,
                    urlargs=req.args)

