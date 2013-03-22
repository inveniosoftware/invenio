## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""Invenio Access Control Engine in mod_python."""

__revision__ = "$Id$"

import cgi
import sys
from urllib import quote

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

from invenio.config import CFG_SITE_SECURE_URL, CFG_CERN_SITE
from invenio.dbquery import run_sql
from invenio.access_control_admin import acc_find_possible_roles, acc_is_user_in_role, CFG_SUPERADMINROLE_ID, acc_get_role_users
from invenio.access_control_config import CFG_WEBACCESS_WARNING_MSGS, CFG_WEBACCESS_MSGS
from invenio.webuser import collect_user_info
from invenio.access_control_firerole import deserialize, load_role_definition, acc_firerole_extract_emails
from invenio.urlutils import make_canonical_urlargd

def acc_authorize_action(req, name_action, authorized_if_no_roles=False, **arguments):
    """
    Given the request object (or the user_info dictionary, or the uid), checks
    if the user is allowed to run name_action with the given parameters.
    If authorized_if_no_roles is True and no role exists (different
    than superadmin) that are authorized to execute the given action, the
    authorization will be granted.
    Returns (0, msg) when the authorization is granted, (1, msg) when it's not.
    """
    user_info = collect_user_info(req)
    roles = acc_find_possible_roles(name_action, always_add_superadmin=False, **arguments)
    for id_role in roles:
        if acc_is_user_in_role(user_info, id_role):
            ## User belong to at least one authorized role.
            return (0, CFG_WEBACCESS_WARNING_MSGS[0])
    if acc_is_user_in_role(user_info, CFG_SUPERADMINROLE_ID):
        ## User is SUPERADMIN
        return (0, CFG_WEBACCESS_WARNING_MSGS[0])
    if not roles:
        ## No role is authorized for the given action/arguments
        if authorized_if_no_roles:
            ## User is authorized because no authorization exists for the given
            ## action/arguments
            return (0, CFG_WEBACCESS_WARNING_MSGS[0])
        else:
            ## User is not authorized.
            return (20, CFG_WEBACCESS_WARNING_MSGS[20] % cgi.escape(name_action))
    ## User is not authorized
    in_a_web_request_p = bool(user_info['uri'])
    if CFG_CERN_SITE and arguments.has_key('collection'):
        # We apply the checks for all actions with that 'collection'
        # argument, for simplicity not necessity.
        from invenio.search_engine import get_collection_allchildren
        if arguments.get('collection', None) in get_collection_allchildren('e-Tendering', recreate_cache_if_needed=False):
            return (1, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[1],
                                  (in_a_web_request_p and "%s %s" % (CFG_WEBACCESS_MSGS[9] % ("purchasing.service@cern.ch", "purchasing.service@cern.ch"),
                                                                     CFG_WEBACCESS_MSGS[10] % (CFG_SITE_SECURE_URL + "/goto/etendering-faq", "Frequently Asked Questions (FAQ) concerning the CERN e-tendering application")
                                                                     ) or "")))

    return (1, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], (in_a_web_request_p and "%s %s" % (CFG_WEBACCESS_MSGS[0] % quote(user_info['uri']), CFG_WEBACCESS_MSGS[1]) or "")))

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
    authorized_emails = set()
    roles = acc_find_possible_roles(name_action, always_add_superadmin=False, **arguments)
    for id_role in roles:
        for dummy1, email, dummy2 in acc_get_role_users(id_role):
            authorized_emails.add(email.lower().strip())
        firerole = load_role_definition(id_role)
        authorized_emails = authorized_emails.union(acc_firerole_extract_emails(firerole))
    return authorized_emails
