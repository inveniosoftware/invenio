# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2012, 2015 CERN.
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

# import interesting modules:
import os
import shutil

from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_WEBSUBMIT_STORAGEDIR, \
     CFG_SITE_SECURE_URL
from invenio.legacy.dbquery import run_sql
from invenio.modules.access.engine import acc_authorize_action
from invenio.legacy.webpage import page, error_page
from invenio.legacy.webuser import getUid, get_email, page_not_authorized
from invenio.base.i18n import gettext_set_language, wash_language

from sqlalchemy.exc import SQLAlchemyError as Error

import invenio.legacy.template
websubmit_templates = invenio.legacy.template.load('websubmit')

def index(req, c=CFG_SITE_NAME, ln=CFG_SITE_LANG, order="", doctype="", deletedId="", deletedAction="", deletedDoctype=""):
    global uid
    ln = wash_language(ln)

    # load the right message language
    _ = gettext_set_language(ln)

    t = ""
    # get user ID:
    try:
        uid = getUid(req)
        (auth_code, auth_message) = acc_authorize_action(uid, 'submit')
        if auth_code > 0 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yoursubmissions.py/index",
                                       navmenuid='yoursubmissions',
                                       text=auth_message)
        u_email = get_email(uid)
    except Error as e:
        return error_page(str(e), req, ln=ln)

    if deletedId != "":
        t += deleteSubmission(deletedId, deletedAction, deletedDoctype, u_email)

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
            status = row[3]
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
           order = order,
           doctypes = doctypes,
           submissions = submissions,
         )

    return page(title=_("Your Submissions"),
                navtrail= """<a class="navtrail" href="%(sitesecureurl)s/youraccount/display">%(account)s</a>""" % {
                             'sitesecureurl' : CFG_SITE_SECURE_URL,
                             'account' : _("Your Account"),
                          },
                body=t,
                description="",
                keywords="",
                uid=uid,
                language=ln,
                req=req,
                navmenuid='yoursubmissions')

def deleteSubmission(id, action, doctype, u_email):
    global CFG_WEBSUBMIT_STORAGEDIR
    run_sql("delete from sbmSUBMISSIONS WHERE doctype=%s and action=%s and email=%s and status='pending' and id=%s", (doctype, action, u_email, id,))
    res = run_sql("select dir from sbmACTION where sactname=%s", (action,))
    dir = res[0][0]
    if not ('..' in doctype or '..' in id) and id != "":
        full = os.path.join(CFG_WEBSUBMIT_STORAGEDIR, dir, doctype, id)
        if os.path.isdir(full):
            shutil.rmtree(full)
    return ""
