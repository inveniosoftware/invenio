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
   ## Name:          Is_Original_Submitter
   ## Description:   function Is_Original_Submitter
   ##                This function compares the email of the current logged
   ##             user with the original submitter of the document, then
   ##             check whether the user has special rights.
   ## Author:         T.Baron
   ##
   ## PARAMETERS:    -
   ## OUTPUT: HTML
   ##


import re
import os
from invenio.modules.access.engine import acc_authorize_action
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionStop
from invenio.legacy.websubmit.functions.Retrieve_Data import Get_Field
from invenio.legacy.websubmit.functions.Shared_Functions import write_file

def Is_Original_Submitter(parameters, curdir, form, user_info=None):
    """
    This function compares the current logged in user email with the
    email of the original submitter of the record. If it is the same
    (or if the current user has superuser rights), we go on. If it
    differs, an error message is issued.
    """
    global uid_email,sysno,uid
    doctype = form['doctype']
    act = form['act']
    email = Get_Field("8560_f",sysno)
    email = re.sub("[\n\r ]+","",email)
    uid_email = re.sub("[\n\r ]+","",uid_email)
    (auth_code, auth_message) = acc_authorize_action(user_info, "submit",verbose=0,doctype=doctype, act=act)
    if re.search(uid_email,email,re.IGNORECASE) is None and auth_code != 0:
        raise InvenioWebSubmitFunctionStop("""
<SCRIPT>
   document.forms[0].action="/submit";
   document.forms[0].curpage.value = 1;
   document.forms[0].step.value = 0;
   user_must_confirm_before_leaving_page = false;
   alert('Only the submitter of this document has the right to do this action. \\nYour login (%s) is different from the one of the submitter (%s).');
   document.forms[0].submit();
</SCRIPT>""" % (uid_email,email))
    elif re.search(uid_email,email, re.IGNORECASE) is None and \
             auth_code == 0:
        if not os.path.exists(os.path.join(curdir, 'is_original_submitter_warning')):
            write_file(os.path.join(curdir, 'is_original_submitter_warning'), '')
            return ("""
<SCRIPT>
alert('Only the submitter of this document has the right to do this action. \\nYour login (%s) is different from the one of the submitter (%s).\\n\\nAnyway, as you have a special authorization for this type of documents,\\nyou are allowed to proceed! Watch out your actions!');
</SCRIPT>""" % (uid_email,email))

    return ""

