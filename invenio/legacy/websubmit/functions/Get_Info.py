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

   ##
   ## Name:          Get_Info.py
   ## Description:   function Get_Info
   ##                This function retrieves some bibliographic data (title,
   ##                submitter email, author and sets global variables with
   ##                the values, so that other functions may use them.
   ## Author:         T.Baron
   ## PARAMETERS:    authorFile: name of the file in which the author is stored
   ##             emailFile: name of the file in which the email is stored
   ##             titleFile: name of the file in which the title is stored
   ## OUTPUT: HTML
   ##

import os

from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionStop
from invenio.legacy.websubmit.functions.Retrieve_Data import Get_Field

titlevalue = ""
emailvalue = ""
authorvalue = ""

def Get_Info(parameters, curdir, form, user_info=None):
    """
    This function tries to retrieve in the 'pending' directory or
    directly in the documents database, some information about the
    document: title, original submitter's email and author(s).  If found,
    this information is stored in 3 global variables: $emailvalue,
    $titlevalue, $authorvalue to be used in other functions.  If not
    found, an error message is displayed.

    Parameters:

         * authorFile: Name of the file in which the author may be
                       found if the document has not yet been
                       integrated (in this case it is still in the
                       'pending' directory).

         * emailFile: Name of the file in which the email of the
                      riginal submitter may be found if the document
                      has not yet been integrated (in this case it is
                      still in the 'pending' directory).

         * titleFile: Name of the file in which the title may be found
                      if the document has not yet been integrated (in
                      this case it is still in the 'pending'
                      directory).
    """
    global titlevalue,emailvalue,authorvalue,rn
    doctype = form['doctype']
    titlefile = parameters["titleFile"]
    emailfile = parameters["emailFile"]
    authorfile = parameters["authorFile"]
    if not Get_Info_In_Curdir(rn,titlefile,emailfile,authorfile,doctype):
        if not Get_Info_In_DB(rn,parameters,curdir):
            DocumentNotFound(rn)
    return ""

def Get_Info_In_Curdir(repno,titlefile,emailfile,authorfile,doctype):
    global titlevalue,emailvalue,authorvalue
    if not os.path.exists("%s/%s" % (curdir,titlefile)):
        return 0
    else:
        if os.path.exists("%s/%s" % (curdir,titlefile)):
            fp = open("%s/%s" % (curdir,titlefile),"r")
            titlevalue = fp.read()
            fp.close()
        else :
            titlevalue = "-"
        if os.path.exists("%s/%s" % (curdir,emailfile)):
            fp = open("%s/%s" % (curdir,emailfile),"r")
            emailvalue = fp.read()
            fp.close()
        else :
            emailvalue = "-"
        if os.path.exists("%s/%s" % (curdir,authorfile)):
            fp = open("%s/%s" % (curdir,authorfile),"r")
            authorvalue = fp.read()
            fp.close()
        else :
            authorvalue = "-"
    return 1

def Get_Info_In_DB(rn,parameters,curdir):
    global titlevalue,emailvalue,authorvalue,sysno
    if sysno != "":
        titlevalue = Get_Field('245__a',sysno)
        emailvalue = Get_Field('8560_f',sysno)
        authorvalue = Get_Field('100__a',sysno)
        authorvalue += "\n%s" % Get_Field('700__a',sysno)
        # save result
        fp = open("%s/SN" % curdir,"w")
        fp.write(sysno)
        fp.close()
        return 1
    else:
        return 0

def DocumentNotFound(repno):
    raise InvenioWebSubmitFunctionStop("""
<SCRIPT>
   document.forms[0].action="/submit";
   document.forms[0].curpage.value = 1;
   document.forms[0].step.value = 0;
   user_must_confirm_before_leaving_page = false;
   alert('The document %s cannot be found in our database.\\nAnyway, you can still choose another document if you wish.');
   document.forms[0].submit();
</SCRIPT>""" % repno)
    return 0

