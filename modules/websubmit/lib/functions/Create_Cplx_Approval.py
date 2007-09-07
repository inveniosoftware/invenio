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

def Create_Cplx_Approval(parameters,curdir,form):
    global rn
    doctype = form['doctype']
    act = form['act']
    categformat = parameters['categformatDAM']
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

    #Path of file containing group
    if os.path.exists("%s/%s" % (curdir,'Group')):
        fp = open("%s/%s" % (curdir,'Group'),"r")
        group = fp.read()
        group = group.replace("/","_")
        group = re.sub("[\n\r]+","",group)
        group_id = run_sql ("""SELECT id FROM usergroup WHERE name = %s""", (group,))[0][0]

    sth = run_sql("SELECT rn FROM sbmCPLXAPPROVAL WHERE  doctype=%s and categ=%s and rn=%s and type=%s and id_group=%s", (doctype,category,rn,act,group_id))
    if len(sth) == 0:
        run_sql("INSERT INTO  sbmCPLXAPPROVAL values(%s,%s,%s,%s,'waiting',%s,'','',NOW(),NOW(),'','','','','','')", (doctype,category,rn,act,group_id,))
    else:
        run_sql("UPDATE sbmCPLXAPPROVAL SET dLastReq=NOW(), status='waiting', dProjectLeaderAction='' WHERE  doctype=%s and categ=%s and rn=%s and type=%s and id_group=%s", (doctype,category,rn,act,group_id))
    return ""
