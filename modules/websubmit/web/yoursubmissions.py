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
import string
import os
import sys
import time
import types
import re
import MySQLdb
import shutil
import operator

from cdsware.config import weburl,cdsname,cdslang
from cdsware.dbquery import run_sql
from cdsware.access_control_engine import acc_authorize_action
from cdsware.access_control_admin import *
from cdsware.webpage import page, create_error_box
from cdsware.webuser import getUid, get_email, list_registered_users, page_not_authorized
from cdsware.messages import *
from cdsware.websubmit_config import *
from cdsware.search_engine import search_pattern
from cdsware.access_control_config import CFG_ACCESS_CONTROL_LEVEL_SITE

from cdsware.messages import gettext_set_language
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
            return page_not_authorized(req, "../yoursubmissions.py/index")
        u_email = get_email(uid)
    except MySQLdb.Error, e:
        return errorMsg(e.value, req, ln)

    if u_email == "guest" or u_email == "":
        return warningMsg(websubmit_templates.tmpl_warning_message(
                 ln = ln,
                 msg = _("You first have to login before using this feature. Use the left menu to log in."),
               ),req, ln = ln)


    if deletedId != "":
        t += deleteSubmission(deletedId,deletedAction,deletedDoctype,u_email)

    # doctypes
    res = run_sql("select ldocname,sdocname from sbmDOCTYPE order by ldocname")
    doctypes = []
    for row in res:
        doctypes.append({
                          'id' : row[1],
                          'name' : row[0],
                          'selected' : (doctype == row[1]),
                        })

    # submissions
    # request order default value
    reqorder = "sbmSUBMISSIONS.md DESC, lactname"
    # requested value
    if order == "actiondown":
        reqorder = "lactname ASC, sbmSUBMISSIONS.md DESC"
    elif order == "actionup":
        reqorder = "lactname DESC, sbmSUBMISSIONS.md DESC"
    elif order == "refdown":
        reqorder = "reference ASC, sbmSUBMISSIONS.md DESC, lactname DESC"
    elif order == "refup":
        reqorder = "reference DESC, sbmSUBMISSIONS.md DESC, lactname DESC"
    elif order == "cddown":
        reqorder = "sbmSUBMISSIONS.cd DESC, lactname"
    elif order == "cdup":
        reqorder = "sbmSUBMISSIONS.cd ASC, lactname"
    elif order == "mddown":
        reqorder = "sbmSUBMISSIONS.md DESC, lactname"
    elif order == "mdup":
        reqorder = "sbmSUBMISSIONS.md ASC, lactname"
    elif order == "statusdown":
        reqorder = "sbmSUBMISSIONS.status DESC, lactname"
    elif order == "statusup":
        reqorder = "sbmSUBMISSIONS.status ASC, lactname"
    if doctype != "":
        docselect = " and doctype='%s' " % doctype
    else:
        docselect = ""

    res = run_sql("SELECT sbmSUBMISSIONS.* FROM sbmSUBMISSIONS,sbmACTION WHERE sactname=action and email=%s and id!='' "+docselect+" ORDER BY doctype,"+reqorder,(u_email,))
    currentdoctype = ""
    currentaction = ""
    currentstatus = ""

    submissions = []
    for row in res:
        if currentdoctype != row[1]:
            currentdoctype = row[1]
            currentaction = ""
            currentstatus = ""
            res2 = run_sql("SELECT ldocname FROM sbmDOCTYPE WHERE  sdocname=%s",(currentdoctype,))
            if res2:
                ldocname = res2[0][0]
            else:
                ldocname = """***Unknown Document Type - (%s)""" % (currentdoctype,)

        if currentaction != row[2]:
            currentaction = row[2]
            res2 = run_sql("SELECT lactname FROM sbmACTION WHERE  sactname=%s",(currentaction,))
            if res2:
                lactname = res2[0][0]
            else:
                lactname = "\""
        else:
            lactname = "\""

        if currentstatus != row[3]:
            currentstatus = row[3]
            status=row[3]
        else:
            status = "\""

        submissions.append({
                             'docname' : ldocname,
                             'actname' : lactname,
                             'status' : status,
                             'cdate' : row[6],
                             'mdate' : row[7],
                             'reference' : row[5],
                             'id' : row[4],
                             'act' : currentaction,
                             'doctype' : currentdoctype,
                             'pending' : (row[3] == "pending")
                           })
    # display
    t += websubmit_templates.tmpl_yoursubmissions(
           ln = ln,
           weburl = weburl,
           images = images,
           order = order,
           doctypes = doctypes,
           submissions = submissions,
         )

    return page(title="Your Submissions",
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

def deleteSubmission(id, action, doctype, u_email):
    global storage
    run_sql("delete from sbmSUBMISSIONS WHERE doctype=%s and action=%s and email=%s and status='pending' and id=%s",(doctype,action,u_email,id,))
    res = run_sql("select dir from sbmACTION where sactname=%s",(action,))
    dir = res[0][0]
    if re.search("\.\.",doctype) == None and re.search("\.\.",id) == None and id != "":
        if os.path.exists("%s/%s/%s/%s" % (storage,dir,doctype,id)):
            os.rmdir("%s/%s/%s/%s" % (storage,dir,doctype,id))
    return ""

def warningMsg(title,req,c=cdsname,ln=cdslang):
    return page(title="warning",
                body = title,
                description="%s - Internal Error" % c,
                keywords="%s, CDSware, Internal Error" % c,
                language=ln,
                urlargs=req.args)

def errorMsg(title,req,c=cdsname,ln=cdslang):
    return page(title="error",
                body = create_error_box(req, title=title,verbose=0, ln=ln),
                description="%s - Internal Error" % c,
                keywords="%s, CDSware, Internal Error" % c,
                language=ln,
                urlargs=req.args)

