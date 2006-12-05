## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

   ## Description:   function Update_Approval_DB
   ##                This function updates the approval database with the
   ##             decision of the referee
   ## Author:         T.Baron
   ## PARAMETERS:    categformatDAM: variable used to compute the category
   ##                                of the document from its reference

import os
import re
import time

from invenio.dbquery import run_sql

def Update_Approval_DB(parameters,curdir,form):
    global rn
    doctype = form['doctype']
    act = form['act']
    categformat = parameters['categformatDAM']
    access = "%s%s" % (time.time(),os.getpid())
    if act != "APP":
        # retrieve category
        if re.search("<FILE:",categformat):
            filename = categformat.replace("<FILE:","")
            filename = filename.replace(">","")
            if os.path.exists("%s/%s" % (curdir,filename)):
                fp = open("%s/%s" % (curdir,filename))
                category = fp.read()
                fp.close()
            else:
                category=""
            category = category.replace("\n","")
        else:
            categformat = categformat.replace("<CATEG>","([^-]*)")
            category = re.match(categformat,rn).group(1)
        if category == "":
            category = "unknown"
        sth = run_sql("SELECT status,dFirstReq,dLastReq,dAction FROM sbmAPPROVAL WHERE  doctype=%s and categ=%s and rn=%s", (doctype,category,rn,))
        if len(sth) == 0:
            run_sql("INSERT INTO  sbmAPPROVAL values(%s,%s,%s,'waiting',NOW(),NOW(),'',%s)", (doctype,category,rn,access,))
        else:
            run_sql("UPDATE sbmAPPROVAL SET dLastReq=NOW(), status='waiting' WHERE  doctype=%s and categ=%s and rn=%s", (doctype,category,rn,))
    else:
        if os.path.exists("%s/decision" % curdir):
            fp = open("%s/decision" % curdir, "r")
            decision = fp.read()
            fp.close()
        else:
            decision = ""
        if decision == "approve":
            run_sql("UPDATE sbmAPPROVAL SET dAction=NOW(),status='approved' WHERE  rn=%s", (rn,))
        else:
            run_sql("UPDATE sbmAPPROVAL SET dAction=NOW(),status='rejected' WHERE  rn=%s", (rn,))
    return ""
