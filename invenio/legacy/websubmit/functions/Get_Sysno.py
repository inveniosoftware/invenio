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

"""Get the recid of a record based upon report-number, as stored
   in the global variable 'rn'.

   **Deprecated - Use Get_Recid Instead**
"""

__revision__ = "$Id$"

   ##
   ## Name:          Get_Sysno.py
   ## Description:   function Get_Sysno
   ##                This function retrieves the system number of a document
   ##             given its reference
   ## Author:         T.Baron
   ## PARAMETERS:    -
   ## OUTPUT: HTML
   ##

import os

from invenio.legacy.search_engine import search_pattern
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionStop

def Get_Sysno(parameters, curdir, form, user_info=None):
    """
       **Deprecated - Use Get_Recid Instead**
    """
    global rn,sysno
    # initialize sysno variable
    sysno = ""
    if os.path.exists("%s/SN" % curdir):
        fp = open("%s/SN" % curdir,"r")
        sysno = fp.read()
        fp.close()
    else:
        searchresults = list(search_pattern(req=None, p=rn, f="reportnumber"))
        if len(searchresults) == 0:
            raise InvenioWebSubmitFunctionStop("<SCRIPT>document.forms[0].action=\"/submit\";document.forms[0].curpage.value=1;document.forms[0].step.value=0;user_must_confirm_before_leaving_page = false;alert('The report %s cannot be found in our database.\\nPerhaps it has not been integrated yet?\\nAnyway, you can choose another report number if you wish.\\n Or retry this action in a few minutes.');document.forms[0].submit();</SCRIPT>" % rn)
        elif len(searchresults) > 1:
            raise InvenioWebSubmitFunctionStop("<SCRIPT>document.forms[0].action=\"/submit\";document.forms[0].curpage.value=1;document.forms[0].step.value=0;user_must_confirm_before_leaving_page = false;alert('Multiple documents have been found with report number %s\\nYou can try with another report number if you wish.\\n Or retry this action in a few minutes.');document.forms[0].submit();</SCRIPT>" % rn)
        else:
            sysno = searchresults[0]
        # save resultin a file
        fp = open("%s/SN" % curdir,"w")
        fp.write(str(sysno))
        fp.close()
    return ""

