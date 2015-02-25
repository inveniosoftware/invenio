# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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
import time

from invenio.legacy.dbquery import run_sql

def Update_Approval_DB(parameters, curdir, form, user_info=None):
    """
    This function updates the approval database when a document has
    just been approved or rejected. It uses the [categformatDAM]
    parameter to compute the category of the document.  Must be called
    after the Get_Report_Number function.

    Parameters:

       * categformatDAM: It contains the regular expression which
                         allows the retrieval of the category from the
                         reference number.
                         Eg: if [categformatDAM]="TEST-<CATEG>-.*" and
                         the reference is "TEST-CATEG1-2001-001" then
                         the category will be recognized as "CATEG1".
    """
    global rn
    doctype = form['doctype']
    act = form['act']
    categformat = parameters['categformatDAM']
    ## Get the name of the decision file:
    try:
        decision_filename = parameters['decision_file']
    except KeyError:
        decision_filename = ""

    pid = os.getpid()
    now = time.time()
    access = "%i_%s" % (now,pid)
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
            m_categ_search = re.match(categformat, rn)
            if m_categ_search is not None:
                if len(m_categ_search.groups()) > 0:
                    ## Found a match for the category of this document. Get it:
                    category = m_categ_search.group(1)
                else:
                    ## This document has no category.
                    category = ""
            else:
                category = ""
        if category == "":
            category = "unknown"
        sth = run_sql("SELECT status,dFirstReq,dLastReq,dAction FROM sbmAPPROVAL WHERE  doctype=%s and categ=%s and rn=%s", (doctype,category,rn,))
        if len(sth) == 0:
            run_sql("INSERT INTO sbmAPPROVAL (doctype, categ, rn, status, dFirstReq, dLastReq, dAction, access) VALUES (%s,%s,%s,'waiting',NOW(),NOW(),'',%s)", (doctype,category,rn,access,))
        else:
            run_sql("UPDATE sbmAPPROVAL SET dLastReq=NOW(), status='waiting' WHERE  doctype=%s and categ=%s and rn=%s", (doctype,category,rn,))
    else:
        ## Since this is the "APP" action, this call of the function must be
        ## on behalf of the referee - in order to approve or reject an item.
        ## We need to get the decision from the decision file:
        if decision_filename in (None, "", "NULL"):
            ## We don't have a name for the decision file.
            ## For backward compatibility reasons, try to read the decision from
            ## a file called 'decision' in curdir:
            if os.path.exists("%s/decision" % curdir):
                fh_decision = open("%s/decision" % curdir, "r")
                decision = fh_decision.read()
                fh_decision.close()
            else:
                decision = ""
        else:
            ## Try to read the decision from the decision file:
            try:
                fh_decision = open("%s/%s" % (curdir, decision_filename), "r")
                decision = fh_decision.read().strip()
                fh_decision.close()
            except IOError:
                ## Oops, unable to open the decision file.
                decision = ""
        ## Either approve or reject the item, based upon the contents
        ## of 'decision':
        if decision == "approve":
            run_sql("UPDATE sbmAPPROVAL SET dAction=NOW(),status='approved' WHERE  rn=%s", (rn,))
        else:
            run_sql("UPDATE sbmAPPROVAL SET dAction=NOW(),status='rejected' WHERE  rn=%s", (rn,))
    return ""
