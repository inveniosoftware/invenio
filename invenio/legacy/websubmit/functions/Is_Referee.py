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

from invenio.config import CFG_SITE_SUPPORT_EMAIL
from invenio.legacy.dbquery import run_sql
from invenio.modules.access.engine import acc_authorize_action
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionStop

def Is_Referee(parameters, curdir, form, user_info=None):
    """
    This function checks whether the currently logged user is a
    referee for this document.
    """
    global uid_email,sysno,rn,uid
    doctype = form['doctype']
    # Get document category
    res = run_sql("SELECT categ FROM sbmAPPROVAL WHERE rn=%s", (rn,))
    if len(res) >0:
        categ = res[0][0]
        if categ == "unknown":
            ## FIXME: This was necessary for document types without categories,
            ## such as DEMOBOO:
            categ = "*"
    else:
        categ=""
    # Try to retrieve the referee's email from the referee's database
    (auth_code, auth_message) = acc_authorize_action(user_info, "referee",doctype=doctype, categ=categ)
    if auth_code != 0:
        raise InvenioWebSubmitFunctionStop("""
<SCRIPT>
        document.forms[0].action="/submit";
        document.forms[0].curpage.value = 1;
        document.forms[0].step.value = 0;
        user_must_confirm_before_leaving_page = false;
        alert('Sorry you (%s) have not been recognized as a referee for this type of document.\\nIf you think this is an error, please contact %s');
        document.forms[0].submit();
</SCRIPT>""" % (uid_email,CFG_SITE_SUPPORT_EMAIL))
    return ""

