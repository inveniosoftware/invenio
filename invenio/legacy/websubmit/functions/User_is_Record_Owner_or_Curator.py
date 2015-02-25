# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2014 CERN.
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

"""Test whether the user is an owner or curator of a record and based on this,
   either prevent them from working with it, or exit silently allowing
   processing on the submission to continue.
"""

__revision__ = "$Id$"

import os

from invenio.config import CFG_CERN_SITE
from invenio.legacy.bibrecord import get_fieldvalues
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionStop
from invenio.modules.access.engine import acc_authorize_action
from invenio.modules.access.control import acc_get_role_id, \
        acc_is_user_in_role, \
        CFG_SUPERADMINROLE_ID

# The field in which to search for the record submitter/owner's email address:
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
   alert('You are neither owner, nor curator of this record. You are not authorized to modify it.');
   document.forms[0].submit();
</SCRIPT>"""

def User_is_Record_Owner_or_Curator(parameters, curdir, form, user_info=None):
    """
    Check that user is either the original submitter, or that it
    belongs to the role(s) given as parameter. This enables
    collaborative editing of records, so that collections can be
    curated by a group of people in addition to the original
    submitter.

    If the user has permission, the function ends silently. If not, it
    will raise an InvenioWebSubmitFunctionStop, informing the user that
    they don't have rights and sending them back to the submission web
    form.

    This function makes it unnecessary to protect the submission with
    WebAccess (i.e. 'submit' action): the function can check
    authorizations by itself.
    However if the case the action in which this function is used is
    still protected with WebAccess (eg. an authorization exists for
    the 'submit' action, in 'MBI'), ALL the possible submitters AND
    the curators groups must be linked to the authorization in order
    for WebSubmit to let users reach this function: this function then
    ensures that only curators or submitters of the record will be
    able to continue further.

    A record owner must have her email in the record metadata.

    A record curator must be in the role given as parameter to this
    function.

    WARNING: you must remember that category-based restrictions
    require you to check that the selected category matches the
    document to modify: one can select category 'foo' to modify
    a document submitted in category 'bar', given that submissions
    are indepedendant of the record they create.

    WARNING: for backward compatibility reasons, if no role is given
    as parameter, the function simply check against the WebAccess
    'submit' action, with this submission parameters. It then means
    that anybody connected to the authorization will be able to modify
    ANY of the records this submission can handle.

    @parameters:

       - curator_role: a role or mapping of roles that determine if
                       user is a curator or not. The parameter can
                       simply be the name of a WebAccess role. For eg:
                         curator_photo
                       where 'curator_photo' is a WebAccess role
                       matching curator users for this submission.

                       The parameter can also map the submission
                       categories to different roles, so that
                       different curator groups can be defined. For eg:
                         ARTICLE=curator_art|REPORT=curator_rep|*=curator_gen
                       (syntax: '|' to split mappings, and '=' to map category->role)

                       This specifies that role 'curator_art' is used
                       when category 'Article' is selected (code for
                       this category is 'ARTICLE'), 'curator_rep' when
                       'Report' ('REPORT' code) is selected, and
                       curator_gen in all other cases. * matches all
                       categories.

                       When defining a mapping category->role, and
                       category cannot be retrieved (for eg. with
                       /submit/direct URLs that do not specify
                       category), only the * rule/role is matched.
                       Eg: foo=role1|*=role2 matches role2 only

                       When no role is defined or matched, the curator
                       role is checked against the WebAccess 'submit'
                       action, for current WebSubmit doctype, action
                       and category.

        - curator_flag: the name of a file in which '1' is written if
                        current submitter is a curator. Otherwise, an
                        empty file is written.
                        If no value is given, no file is written.

    @return: Empty string.
    @Exceptions raised: InvenioWebSubmitFunctionStop when user is denied
                permission to work with the record.
    """
    global sysno

    # Check if the user is superadmin, in which case grant access
    if acc_is_user_in_role(user_info, CFG_SUPERADMINROLE_ID):
        return ""

    # Get current doctype
    doctype_fd = open(os.path.join(curdir, 'doctype'))
    doctype = doctype_fd.read()
    doctype_fd.close()

    # Get current action
    act_fd = open(os.path.join(curdir, 'act'))
    act = act_fd.read()
    act_fd.close()

    # Get category. This one might not exist
    category = None
    if os.path.exists(os.path.join(curdir, 'combo%s' % doctype)):
        category_fd = open(os.path.join(curdir, 'combo%s' % doctype))
        category = category_fd.read()
        category_fd.close()

    # Get role to belong to in order to be curator. If not specifed,
    # we simply check against 'submit' WebAccess action for the current
    # WebSubmit action (for eg. 'MBI')
    curator_roles = []
    try:
        curator_role = parameters['curator_role']
    except:
        curator_role = ''
    if '=' in curator_role:
        # Admin specifed a different role for different category.
        # For eg: general=curator_gen|photo=curator_photo|*=curator_other
        curator_roles = [categ_and_role.split('=', 1)[1].strip() \
                         for categ_and_role in curator_role.split('|') if \
                         len(categ_and_role.split('=', 1)) == 2 and \
                         categ_and_role.split('=', 1)[0].strip() in (category, '*')]
    elif curator_role:
        curator_roles = [curator_role]

    ## Get the current user's e-mail address:
    user_email = user_info["email"].lower()

    ## Now get the email address(es) of the record submitter(s)/owner(s) from
    ## the record itself:
    record_owners_list = [email.lower().strip() for email in \
                          get_fieldvalues(sysno, CFG_WEBSUBMIT_RECORD_OWNER_EMAIL)]

    ## Now determine whether this user is listed in the record as an "owner"
    ## (or submitter):
    user_has_permission = False
    user_msg = ""
    if user_email not in ("", "guest") and user_email in record_owners_list:
        ## This user's email address is listed in the record. She should
        ## be allowed to work with it:
        user_has_permission = True

    # Check if user is curator
    is_curator = False
    if curator_roles:
        # Check against roles
        for role in curator_roles:
            if not acc_get_role_id(role):
                # Role is not defined
                continue
            if acc_is_user_in_role(user_info, acc_get_role_id(role)):
                # One matching role found
                user_has_permission = True
                is_curator = True
                break
    else:
        # Check against authorization for 'submit' (for backward compatibility)
        (auth_code, dummy) = acc_authorize_action(user_info, \
                                                  "submit", \
                                                  verbose=0, \
                                                  doctype=doctype, \
                                                  act=act)
        if auth_code == 0:
            ## The user is a curator for this
            ## submission/collection. Do not prevent access.
            is_curator = True
            user_has_permission = True

    try:
        curator_flag = parameters['curator_flag']
        if curator_flag:
            flag_fd = open(os.path.join(curdir, curator_flag), 'w')
            flag_fd.write(is_curator and '1' or '0')
            flag_fd.close()
    except:
        pass

    ## Finally, if the user still doesn't have permission to work with this
    ## record, raise an InvenioWebSubmitFunctionStop exception sending the
    ## user back to the form.
    if not user_has_permission:
        raise InvenioWebSubmitFunctionStop(CFG_MSG_USER_NOT_AUTHORIZED)
    return ""
