# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2010, 2011 CERN.
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

   ## Description:   function Update_Approval_DB
   ##                This function updates the approval database with the
   ##             decision of the referee
   ## Author:         T.Baron
   ## PARAMETERS:    categformatDAM: variable used to compute the category
   ##                                of the document from its reference

import os
import re

from invenio.legacy.dbquery import run_sql

def Create_Cplx_Approval(parameters, curdir, form, user_info=None):
    global rn
    doctype = form['doctype']
    act = form['act']
    #categformat = parameters['categformatDAM']

    #Obtain the document category from combo<DOCTYPE> file
    category = ""
    if os.path.exists("%s/%s" % (curdir,'combo'+doctype)):
        fp = open("%s/%s" % (curdir,'combo'+doctype),"r")
        category = fp.read()
    else:
        return ""

    #Path of file containing group
    group_id = ""
    if os.path.exists("%s/%s" % (curdir,'Group')):
        fp = open("%s/%s" % (curdir,'Group'),"r")
        group = fp.read()
        group = group.replace("/","_")
        group = re.sub("[\n\r]+","",group)
        group_id = run_sql ("""SELECT id FROM usergroup WHERE name = %s""", (group,))[0][0]
    else:
        return ""

    sth = run_sql("SELECT rn FROM sbmCPLXAPPROVAL WHERE  doctype=%s and categ=%s and rn=%s and type=%s and id_group=%s", (doctype,category,rn,act,group_id))
    if len(sth) == 0:
        run_sql("INSERT INTO  sbmCPLXAPPROVAL values(%s,%s,%s,%s,'waiting',%s,'','',NOW(),NOW(),'','','','','','')",(doctype,category,rn,act,group_id,))
    else:
        run_sql("UPDATE sbmCPLXAPPROVAL SET dLastReq=NOW(), status='waiting', dProjectLeaderAction='' WHERE  doctype=%s and categ=%s and rn=%s and type=%s and id_group=%s", (doctype,category,rn,act,group_id))
    return ""

