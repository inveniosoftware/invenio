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
import string
import os
import sys
import time
import types
import re
import shutil

from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     accessurl, \
     adminemail, \
     cdslang, \
     cdsname, \
     images, \
     pylibdir, \
     storage, \
     supportemail, \
     sweburl, \
     urlpath, \
     version
from invenio.dbquery import run_sql, Error
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_admin import *
from invenio.webpage import page, create_error_box
from invenio.webuser import getUid, get_email, list_registered_users, page_not_authorized
from invenio.messages import gettext_set_language, wash_language
from invenio.websubmit_config import *
from invenio.search_engine import search_pattern
from invenio.websubmit_functions.Retrieve_Data import Get_Field
from invenio.mailutils import send_email

execfile("%s/invenio/websubmit_functions/Retrieve_Data.py" % pylibdir)

import invenio.template
websubmit_templates = invenio.template.load('websubmit')

def index(req,c=cdsname,ln=cdslang,doctype="",categ="",RN="",send=""):
    global uid
    ln = wash_language(ln)

    # load the right message language
    _ = gettext_set_language(ln)

    t=""
    # get user ID:
    try:
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../publiline.py/index",
                                       navmenuid='yourapprovals')
        uid_email = get_email(uid)
    except Error, e:
        return errorMsg(e.value,req, ln = ln)
    if doctype == "":
        t = selectDoctype(ln)
    elif categ == "":
        t = selectCateg(doctype, ln)
    elif RN == "":
        t = selectDocument(doctype,categ, ln)
    else:
        t = displayDocument(req, doctype,categ,RN,send, ln)
    return page(title="publication line",
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

def selectDoctype(ln = cdslang):
    res = run_sql("select DISTINCT doctype from sbmAPPROVAL")
    docs = []
    for row in res:
        res2 = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s", (row[0],))
        docs.append({
                     'doctype' : row[0],
                     'docname' : res2[0][0],
                    })
    t = websubmit_templates.tmpl_publiline_selectdoctype(
          ln = ln,
          docs = docs,
        )
    return t

def selectCateg(doctype, ln = cdslang):
    t=""
    res = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s",(doctype,))
    title = res[0][0]
    sth = run_sql("select * from sbmCATEGORIES where doctype=%s order by lname",(doctype,))
    if len(sth) == 0:
        categ = "unknown"
        return selectDocument(doctype,categ, ln = ln)

    categories = []
    for arr in sth:
        waiting = 0
        rejected = 0
        approved = 0
        sth2 = run_sql("select COUNT(*) from sbmAPPROVAL where doctype=%s and categ=%s and status='waiting'", (doctype,arr[1],))
        waiting = sth2[0][0]
        sth2 = run_sql("select COUNT(*) from sbmAPPROVAL where doctype=%s and categ=%s and status='approved'",(doctype,arr[1],))
        approved = sth2[0][0]
        sth2 = run_sql("select COUNT(*) from sbmAPPROVAL where doctype=%s and categ=%s and status='rejected'",(doctype,arr[1],))
        rejected = sth2[0][0]
        categories.append({
                            'waiting' : waiting,
                            'approved' : approved,
                            'rejected' : rejected,
                            'id' : arr[1],
                          })

    t = websubmit_templates.tmpl_publiline_selectcateg(
          ln = ln,
          categories = categories,
          doctype = doctype,
          title = title,
          images = images,
        )
    return t

def selectDocument(doctype,categ, ln = cdslang):
    t=""
    res = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s", (doctype,))
    title = res[0][0]
    if categ == "":
        categ == "unknown"

    docs = []
    sth = run_sql("select rn,status from sbmAPPROVAL where doctype=%s and categ=%s order by status DESC,rn DESC",(doctype,categ))
    for arr in sth:
        docs.append({
                     'RN' : arr[0],
                     'status' : arr[1],
                    })

    t = websubmit_templates.tmpl_publiline_selectdocument(
          ln = ln,
          doctype = doctype,
          title = title,
          categ = categ,
          images = images,
          docs = docs,
        )
    return t

def displayDocument(req, doctype,categ,RN,send, ln = cdslang):

    # load the right message language
    _ = gettext_set_language(ln)

    t=""
    res = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s", (doctype,))
    docname = res[0][0]
    if categ == "":
        categ = "unknown"
    sth = run_sql("select rn,status,dFirstReq,dLastReq,dAction,access from sbmAPPROVAL where rn=%s",(RN,))
    if len(sth) > 0:
        arr = sth[0]
        rn = arr[0]
        status = arr[1]
        dFirstReq = arr[2]
        dLastReq = arr[3]
        dAction = arr[4]
        access = arr[5]
    else:
        return _("Approval has never been requested for this document.") + "<BR>&nbsp;"

    try:
        (authors,title,sysno,newrn) = getInfo(doctype,categ,RN)
    except TypeError:
        return _("Unable to display document.")

    confirm_send = 0
    if send == _("Send Again"):
        if authors == "unknown" or title == "unknown":
            SendWarning(doctype,categ,RN,title,authors,access, ln = ln)
        else:
            # @todo - send in different languages
            SendEnglish(doctype,categ,RN,title,authors,access,sysno)
            run_sql("update sbmAPPROVAL set dLastReq=NOW() where rn=%s",(RN,))
            confirm_send = 1

    if status == "waiting":
        (auth_code, auth_message) = acc_authorize_action(req, "referee",verbose=0,doctype=doctype, categ=categ)
    else:
        (auth_code, auth_message) = (None, None)

    t = websubmit_templates.tmpl_publiline_displaydoc(
          ln = ln,
          docname = docname,
          doctype = doctype,
          categ = categ,
          rn = rn,
          status = status,
          dFirstReq = dFirstReq,
          dLastReq = dLastReq,
          dAction = dAction,
          access = access,
          images = images,
          accessurl = accessurl,
          confirm_send = confirm_send,
          auth_code = auth_code,
          auth_message = auth_message,
          authors = authors,
          title = title,
          sysno = sysno,
          newrn = newrn,
        )
    return t

# Retrieve info about document
def getInfo(doctype,categ,RN):
    result = getInPending(doctype,categ,RN)
    if not result:
        result = getInAlice(doctype,categ,RN)
    return result

#seek info in pending directory
def getInPending(doctype,categ,RN):
    PENDIR="%s/pending" % storage
    if os.path.exists("%s/%s/%s/AU" % (PENDIR,doctype,RN)):
        fp = open("%s/%s/%s/AU" % (PENDIR,doctype,RN),"r")
        authors=fp.read()
        fp.close()
    else:
        authors = ""
    if os.path.exists("%s/%s/%s/TI" % (PENDIR,doctype,RN)):
        fp = open("%s/%s/%s/TI" % (PENDIR,doctype,RN),"r")
        title=fp.read()
        fp.close()
    else:
        title = ""
    if os.path.exists("%s/%s/%s/SN" % (PENDIR,doctype,RN)):
        fp = open("%s/%s/%s/SN" % (PENDIR,doctype,RN),"r")
        sysno=fp.read()
        fp.close()
    else:
        sysno = ""
    if title == "" and os.path.exists("%s/%s/%s/TIF" % (PENDIR,doctype,RN)):
        fp = open("%s/%s/%s/TIF" % (PENDIR,doctype,RN),"r")
        title=fp.read()
        fp.close()
    if title == "":
        return 0
    else:
        return (authors,title,sysno,"")

#seek info in Alice database
def getInAlice(doctype,categ,RN):
    # initialize sysno variable
    sysno = ""
    searchresults = search_pattern(req=None, p=RN, f="reportnumber").items().tolist()
    if len(searchresults) == 0:
        return 0
    sysno = searchresults[0]
    if sysno != "":
        title = Get_Field('245__a',sysno)
        emailvalue = Get_Field('8560_f',sysno)
        authors = Get_Field('100__a',sysno)
        authors += "\n%s" % Get_Field('700__a',sysno)
        newrn = Get_Field('037__a',sysno)
        return (authors,title,sysno,newrn)
    else:
        return 0

def SendEnglish(doctype,categ,RN,title,authors,access,sysno):
    FROMADDR = '%s Submission Engine <%s>' % (cdsname,supportemail)
    # retrieve useful information from webSubmit configuration
    res = run_sql("select value from sbmPARAMETERS where name='categformatDAM' and doctype=%s", (doctype,))
    categformat = res[0][0]
    categformat = re.sub("<CATEG>","([^-]*)",categformat)
    categs = re.match(categformat,RN)
    if categs is not None:
        categ = categs.group(1)
    else:
        categ = "unknown"
    res = run_sql("select value from sbmPARAMETERS where name='addressesDAM' and doctype=%s",(doctype,))
    if len(res) > 0:
        otheraddresses = res[0][0]
        otheraddresses = otheraddresses.replace("<CATEG>",categ)
    else:
        otheraddresses = ""
    # Build referee's email address
    refereeaddress = ""
    # Try to retrieve the referee's email from the referee's database
    for user in acc_get_role_users(acc_getRoleId("referee_%s_%s" % (doctype,categ))):
        refereeaddress += user[1] + ","
    # And if there are general referees
    for user in acc_get_role_users(acc_getRoleId("referee_%s_*" % doctype)):
        refereeaddress += user[1] + ","
    refereeaddress = re.sub(",$","",refereeaddress)
    # Creation of the mail for the referee
    addresses = ""
    if refereeaddress != "":
        addresses = refereeaddress + ","
    if otheraddresses != "":
        addresses += otheraddresses
    else:
        addresses = re.sub(",$","",addresses)
    if addresses=="":
        SendWarning(doctype,categ,RN,title,authors,access)
        return 0
    if authors == "":
        authors = "-"
    res = run_sql("select value from sbmPARAMETERS where name='directory' and doctype=%s", (doctype,))
    directory = res[0][0]
    message = """
    The document %s has been published as a Communication.
    Your approval is requested for it to become an official Note.

    Title: %s

    Author(s): %s

    To access the document(s), select the file(s) from the location:
    <%s/record/%s/files/>

    To approve/reject the document, you should go to this URL:
    <%s/approve.py?%s>

    ---------------------------------------------
    Best regards.
    The submission team.""" % (RN,title,authors,urlpath,sysno,urlpath,access)
    # send the mail
    send_email(FROMADDR,addresses,"Request for Approval of %s" % RN, message,footer="")
    return ""

def SendWarning(doctype,categ,RN,title,authors,access):
    FROMADDR = '%s Submission Engine <%s>' % (cdsname,supportemail)
    message = "Failed sending approval email request for %s" % RN
    # send the mail
    send_email(FROMADDR,adminemail,"Failed sending approval email request",message)
    return ""

def errorMsg(title,req,c=cdsname,ln=cdslang):
    return page(title="error",
                body = create_error_box(req, title=title,verbose=0, ln=ln),
                description="%s - Internal Error" % c,
                keywords="%s, Internal Error" % c,
                language=ln,
                req=req,
                navmenuid='yourapprovals')

def warningMsg(title,req,c=cdsname,ln=cdslang):
    return page(title="warning",
                body = title,
                description="%s - Internal Error" % c,
                keywords="%s, Internal Error" % c,
                language=ln,
                req=req,
                navmenuid='yourapprovals')

