# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2014, 2015 CERN.
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

"""Invenio Access Control Engine in mod_python."""

__revision__ = "$Id$"

import cgi
from urllib import quote

from .control import acc_find_possible_roles, acc_is_user_in_any_role, acc_get_roles_emails
from .local_config import CFG_WEBACCESS_WARNING_MSGS, CFG_WEBACCESS_MSGS
from invenio.legacy.webuser import collect_user_info
from invenio.modules.access.firerole import load_role_definition, acc_firerole_extract_emails
from flask_login import current_user


def acc_authorize_action(req, name_action, authorized_if_no_roles=False, batch_args=False, **arguments):
    """
    Given the request object (or the user_info dictionary, or the uid), checks
    if the user is allowed to run name_action with the given parameters.
    If authorized_if_no_roles is True and no role exists (different
    than superadmin) that are authorized to execute the given action, the
    authorization will be granted.
    Returns (0, msg) when the authorization is granted, (1, msg) when it's not.
    """
    from invenio.ext.login import UserInfo
    from werkzeug.local import LocalProxy
    if isinstance(req, LocalProxy):
        req = req._get_current_object()
    if isinstance(req, UserInfo):
        user_info = req
        uid = user_info.get_id()
    elif type(req) is dict:
        uid = req.get('uid', None)
        user_info = req
    elif type(req) not in [int, long]:
        uid = current_user.get_id()
        user_info = collect_user_info(uid)  # FIXME
    else:
        user_info = collect_user_info(req)

    roles_list = acc_find_possible_roles(name_action, always_add_superadmin=True, batch_args=batch_args, **arguments)

    if not batch_args:
        roles_list = [roles_list]

    result = []
    for roles in roles_list:
        if acc_is_user_in_any_role(user_info, roles):
            ## User belong to at least one authorized role
            ## or User is SUPERADMIN
            ret_val = (0, CFG_WEBACCESS_WARNING_MSGS[0])
        elif len(roles) <= 1:
            ## No role is authorized for the given action/arguments
            if authorized_if_no_roles:
                ## User is authorized because no authorization exists for the given
                ## action/arguments
                ret_val = (0, CFG_WEBACCESS_WARNING_MSGS[0])
            else:
                ## User is not authorized.
                ret_val = (20, CFG_WEBACCESS_WARNING_MSGS[20] % cgi.escape(name_action))
        else:
            ## User is not authorized
            in_a_web_request_p = bool(user_info.get('uri', ''))
            ret_val = (1, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], (in_a_web_request_p and "%s %s" % (CFG_WEBACCESS_MSGS[0] % quote(user_info.get('uri', '')), CFG_WEBACCESS_MSGS[1]) or "")))
        result.append(ret_val)
    # FIXME removed CERN specific hack!
    return result if batch_args else result[0]


def acc_get_authorized_emails(name_action, **arguments):
    """
    Given the action and its arguments, try to retireve all the matching
    email addresses of users authorized.
    This is a best effort operation, because if a role is authorized and
    happens to be defined using a FireRole rule based on regular expression
    or on IP addresses, non every email might be returned.
    @param name_action: the name of the action.
    @type name_action: string
    @param arguments: the arguments to the action.
    @return: the list of authorized emails.
    @rtype: set of string
    """
    roles = acc_find_possible_roles(name_action, always_add_superadmin=False, **arguments)
    authorized_emails = acc_get_roles_emails(roles)
    for id_role in roles:
        firerole = load_role_definition(id_role)
        authorized_emails = authorized_emails.union(acc_firerole_extract_emails(firerole))
    return authorized_emails
