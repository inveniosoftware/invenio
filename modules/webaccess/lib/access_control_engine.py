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

"""CDS Invenio Access Control Engine in mod_python."""

__revision__ = "$Id$"

import cgi
import sys
from urllib import quote

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

from invenio.config import CFG_SITE_SECURE_URL
from invenio.dbquery import run_sql_cached
from invenio.access_control_admin import acc_find_possible_roles, acc_is_user_in_role, CFG_SUPERADMINROLE_ID, acc_get_role_users
from invenio.access_control_config import CFG_WEBACCESS_WARNING_MSGS, CFG_WEBACCESS_MSGS
from invenio.webuser import collect_user_info
from invenio.access_control_firerole import acc_firerole_suggest_apache_p, deserialize, load_role_definition, acc_firerole_extract_emails
from invenio.urlutils import make_canonical_urlargd

CFG_CALLED_FROM_APACHE = 1 #1=web,0=cli
try:
    import _apache
except ImportError, e:
    CFG_CALLED_FROM_APACHE = 0

def make_list_apache_firerole(name_action, arguments):
    """Given an action and a dictionary arguments returns a list of all the
    roles (and their descriptions) which are authorized to perform this
    action with these arguments, and whose FireRole definition expect
    an Apache Password membership.
    """
    roles = acc_find_possible_roles(name_action, **arguments)

    ret = []

    for role in roles:
        res = run_sql_cached('SELECT name, description, firerole_def_ser FROM accROLE WHERE id=%s', (role, ), affected_tables=['accROLE'])
        if acc_firerole_suggest_apache_p(deserialize(res[0][2])):
            ret.append((res[0][0], res[0][1]))
    return ret

def _format_list_of_apache_firerole(roles, referer):
    """Given a list of tuples (role, description) (returned by make_list_apache_firerole), and a referer url, returns a nice string for
    presenting urls that let the user login with Apache password through
    Firerole.
    This function is needed only at CERN for aiding in the migration of
    Apache Passwords restricted collections to FireRole roles.
    Please use it with care."""
    out = ""
    if roles:
        out += "<p>1) Here is a list of administrative roles you may have " \
        "received authorization for via an Apache password. If you are aware " \
        "of such a password, please follow the corresponding link:"
        out += "<table>"
        for name, description in roles:
            out += "<tr>"
            out += "<td><a href='%s'>%s</a></td><td> - <em>%s</em></td>" % \
            ('%s%s' % (CFG_SITE_SECURE_URL, make_canonical_urlargd({'realm' : name, 'referer' : referer}, {})), name, description)
            out += "</tr>"
        out += "</table>"
        out += "</p>"
    return out

def make_apache_message(name_action, arguments, referer=None):
    """Given an action name and a dictionary of arguments and a refere url
    it returns a a nice string for presenting urls that let the user login
    with Apache password through Firerole authorized roles.
    This function is needed only at CERN for aiding in the migration of
    Apache Passwords restricted collections to FireRole roles.
    Please use it with care."""
    if not referer:
        referer = '%s/youraccount/youradminactivities' % CFG_SITE_SECURE_URL
    roles = make_list_apache_firerole(name_action, arguments)
    if roles:
        return _format_list_of_apache_firerole(roles, referer)
    else:
        return ""

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
    return (1, "%s %s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], (CFG_CALLED_FROM_APACHE and "%s %s" % (CFG_WEBACCESS_MSGS[0] % quote(user_info['uri']), CFG_WEBACCESS_MSGS[1]) or ""), make_apache_message(name_action, arguments, user_info['uri'])))

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
        authorized_emails.union(acc_firerole_extract_emails(firerole))
    return authorized_emails
