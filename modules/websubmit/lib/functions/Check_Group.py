## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

import os
import re

from invenio.dbquery import run_sql
from invenio.websubmit_config import InvenioWebSubmitFunctionStop

def Check_Group(parameters, curdir, form, user_info=None):
    """
    Check that a group exists.
    Read from file "/curdir/Group"

    If the group does not exist, switch to page 1, step 0
    """
    #Path of file containing group
    if os.path.exists("%s/%s" % (curdir,'Group')):
        fp = open("%s/%s" % (curdir,'Group'),"r")
        group = fp.read()
        group = group.replace("/","_")
        group = re.sub("[\n\r]+","",group)
        res = run_sql ("""SELECT id FROM usergroup WHERE name = %s""", (group,))
        if len(res) == 0:
            raise InvenioWebSubmitFunctionStop("""
<SCRIPT>
   document.forms[0].action="/submit";
   document.forms[0].curpage.value = 1;
   document.forms[0].step.value = 0;
   user_must_confirm_before_leaving_page = false;
   document.forms[0].submit();
   alert('The given group name (%s) is invalid.');
</SCRIPT>""" % (group,))
    else:
        raise InvenioWebSubmitFunctionStop("""
<SCRIPT>
   document.forms[0].action="/submit";
   document.forms[0].curpage.value = 1;
   document.forms[0].step.value = 0;
   user_must_confirm_before_leaving_page = false;
   document.forms[0].submit();
   alert('The given group name (%s) is invalid.');
</SCRIPT>""" % (group,))

    return ""
