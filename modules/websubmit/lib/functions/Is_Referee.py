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

from invenio.config import supportemail
from invenio.dbquery import run_sql
from invenio.access_control_engine import acc_authorize_action
from invenio.websubmit_config import functionStop

def Is_Referee(parameters,curdir,form):
    global uid_email,sysno,rn,uid
    doctype = form['doctype']
    # Get document category
    res = run_sql("SELECT categ FROM sbmAPPROVAL WHERE rn=%s", (rn,))
    if len(res) >0:
        categ = res[0][0]
    else:
        categ=""
    # Try to retrieve the referee's email from the referee's database
    (auth_code, auth_message) = acc_authorize_action(uid, "referee",doctype=doctype, categ=categ)
    if auth_code != 0:
        raise functionStop("""
<SCRIPT> 
        document.forms[0].action="/submit";
        document.forms[0].curpage.value = 1;
        document.forms[0].step.value = 0;
        document.forms[0].submit();
        alert('Sorry you (%s) have not been recognized as a referee for this type of document.\\nIf you think this is an error, please contact %s');
</SCRIPT>""" % (uid_email,supportemail))
    return ""

