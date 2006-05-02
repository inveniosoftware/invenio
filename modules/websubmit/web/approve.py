## $Id$
##
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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
from mod_python import apache

from cdsware.config import cdsname,cdslang
from cdsware.dbquery import run_sql
from cdsware.access_control_engine import acc_authorize_action
from cdsware.access_control_admin import acc_isRole
from cdsware.websubmit_config import *
from cdsware.webpage import page, create_error_box
from cdsware.webuser import getUid, get_email, page_not_authorized
from cdsware.messages import wash_language
from cdsware.access_control_config import CFG_ACCESS_CONTROL_LEVEL_SITE

def index(req,c=cdsname,ln=cdslang):

    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return page_not_authorized(req, "../approve.py/index")

    ln = wash_language(ln)
    form = req.form
    if form.keys():
        access = form.keys()[0]
        if access == "":
            return errorMsg("approve.py: cannot determine document reference",req)
        res = run_sql("select doctype,rn from sbmAPPROVAL where access=%s",(access,))
        if len(res) == 0:
            return errorMsg("approve.py: cannot find document in database",req)
        else:
            doctype = res[0][0]
            rn = res[0][1]
        res = run_sql("select value from sbmPARAMETERS where name='edsrn' and doctype=%s",(doctype,))
        edsrn = res[0][0]
        url = "%s/sub.py?%s=%s&password=%s@APP%s" % (urlpath,edsrn,rn,access,doctype)
        req.err_headers_out.add("Location", url)
        raise apache.SERVER_RETURN, apache.HTTP_MOVED_PERMANENTLY
        return ""
    else:
        return errorMsg("Sorry parameter missing...", req, c, ln)

def errorMsg(title,req,c=cdsname,ln=cdslang):
    return page(title="error",
                    body = create_error_box(req, title=title,verbose=0, ln=ln),
                    description="%s - Internal Error" % c, 
                    keywords="%s, CDSware, Internal Error" % c,
                    language=ln,
                    urlargs=req.args)

