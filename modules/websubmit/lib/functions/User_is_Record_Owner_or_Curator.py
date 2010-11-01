## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Test whether the user is an owner or curator of a record and based on this,
   either prevent them from working with it, or exit silently allowing
   processing on the submission to continue.
"""

__revision__ = "$Id$"

from invenio.config import CFG_CERN_SITE
from invenio.search_engine import print_record
from invenio.websubmit_config import InvenioWebSubmitFunctionStop
from invenio.access_control_engine import acc_authorize_action

## The field in which to search for the record submitter/owner's email address:
if CFG_CERN_SITE:
    ## This is a CERN site - we use 859__f for submitter/record owner's email:
    CFG_WEBSUBMIT_RECORD_OWNER_EMAIL = "859__f"
else:
    ## Non-CERN site. Use 8560_f for submitter/record owner's email:
    CFG_WEBSUBMIT_RECORD_OWNER_EMAIL = "8560_f"

CFG_MSG_USER_NOT_AUTHORIZED = """
<SCRIPT>
   document.forms[0].action="/submit";
   document.forms[0].curpage.value = 1;
   document.forms[0].step.value = 0;
   user_must_confirm_before_leaving_page = false;
   document.forms[0].submit();
   alert('You are neither owner, nor curator of this record. You are not authorized to modify it.');
</SCRIPT>"""

def User_is_Record_Owner_or_Curator(parameters, curdir, form, user_info=None):
    """
    Check that user is either the original submitter, or that it has
    been granted access to carry out the action via Webaccess. This
    enables collaborative editing of records, so that collections can
    be curated by a group of people in addition to the original submitter.

    If the user has permission, the function ends silently. If not, it
    will raise an InvenioWebSubmitFunctionStop, informing the user that
    they don't have rights and sending them back to the submission web
    form.

    Note that the original author must also be authorized by WebAccess
    in order to modify the record.

    WARNING: you have to understand that wherever you use this
    function, any user authorized via WebAccess for this action will
    be able to modify any records that can go through this
    workflow. For eg. when using this function in a DEMOPIC
    submission, in a 'MBI' action, it is enough that a user is
    connected to the 'submit' action with the 'DEMOPIC/MBI' parameters
    to modify any record.

    @parameters: None.
    @return: Empty string.
    @Exceptions raised: InvenioWebSubmitFunctionStop when user is denied
                permission to work with the record.
    """
    global sysno
    ## Get the document type and action from the form. They can be used to
    ## ask webaccess whether the user is a super-user for this doctype/action.
    doctype = form['doctype']
    act = form['act']
    ## Get the current user's e-mail address:
    user_email = user_info["email"].lower()
    ## Now get the email address(es) of the record submitter(s)/owner(s) from
    ## the record itself:
    record_owners = print_record(sysno, 'tm', \
                                 [CFG_WEBSUBMIT_RECORD_OWNER_EMAIL]).strip()
    if record_owners != "":
        record_owners_list = record_owners.split("\n")
        record_owners_list = [email.lower().strip() \
                              for email in record_owners_list]
    else:
        record_owners_list = []
    ## Now determine whether this user is listed in the record as an "owner"
    ## (or submitter):
    user_has_permission = False
    user_msg = ""
    if user_email not in ("", "guest") and user_email in record_owners_list:
        ## This user's email address is listed in the record. She should
        ## be allowed to work with it:
        user_has_permission = True
    if not user_has_permission:
        ## The user isn't listed in the record.
        ## Using WebAccess, test if she is a "curator" for this submission:
        (auth_code, dummy) = acc_authorize_action(user_info, \
                                                  "submit", \
                                                  verbose=0, \
                                                  doctype=doctype, \
                                                  act=act)
        if auth_code == 0:
            ## The user is a curator for this submission/collection. Do not
            ## prevent access.
            user_has_permission = True
    ## Finally, if the user still doesn't have permission to work with this
    ## record, raise an InvenioWebSubmitFunctionStop exception sending the
    ## user back to the form.
    if not user_has_permission:
        raise InvenioWebSubmitFunctionStop(CFG_MSG_USER_NOT_AUTHORIZED)
    return ""
