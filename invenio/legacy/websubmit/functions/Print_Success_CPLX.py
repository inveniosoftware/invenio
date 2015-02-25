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

   ## Description:   function Print_Success_CPLX
   ##                This function outputs a message telling the user his/her
   ##             request was taken into account.
   ## Author:         A.Voitier
   ## PARAMETERS:    -

import os
import re

from invenio.legacy.dbquery import run_sql

def Print_Success_CPLX(parameters, curdir, form, user_info=None):
    global rn
    act = form['act']
    doctype = form['doctype']
    category = rn.split('-')
    categ = category[2]

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

    t="<br /><br /><B>Your request has been taken into account!</B><br /><br />"

    sth = run_sql("SELECT rn FROM sbmCPLXAPPROVAL WHERE  doctype=%s and categ=%s and rn=%s and type=%s and id_group=%s", (doctype,categ,rn,act,group_id))
    if not len(sth) == 0:
        run_sql("UPDATE sbmCPLXAPPROVAL SET dLastReq=NOW(), status='waiting', dProjectLeaderAction='' WHERE  doctype=%s and categ=%s and rn=%s and type=%s and id_group=%s", (doctype,categ,rn,act,group_id))

        if (act == "RRP") or (act == "RPB"):
            t+="NOTE: Approval has already been requested for this document. You will be warned by email as soon as the Project Leader takes his/her decision regarding your document.<br /><br />"
    else:
        if (act == "RRP") or (act == "RPB"):
            t+="A notification has been sent to the Publication Committee Chair. You will be notified by email as soon as the Project Leader makes his/her decision regarding your document."

    if act == "RDA":
        t+="An email has been sent to the Project Leader. You will be warned by email as soon as the Project Leader takes his/her decision regarding your document.<br /><br />"
    return t
