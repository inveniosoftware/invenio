# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2014 CERN.
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

"""Invenio LDAP interface for BibCirculation at CERN. """

from time import sleep
from thread import get_ident

from invenio.config import CFG_CERN_SITE
try:
    import ldap
    import ldap.filter
    #from invenio.legacy.external_authentication.cern_wrapper import _cern_nice_soap_auth
    CFG_BIBCIRCULATION_HAS_LDAP = CFG_CERN_SITE
except (ImportError, IOError):
    CFG_BIBCIRCULATION_HAS_LDAP = False

# from base64 import decodestring

# This is the old configuration
# CFG_CERN_LDAP_URI  = "ldaps://ldap.cern.ch:636"
# CFG_CERN_LDAP_BIND = "n=%s,ou=users,o=cern,c=ch"
# CFG_CERN_LDAP_BASE = "O=CERN,C=CH"

CFG_CERN_LDAP_URI  = "ldap://xldap.cern.ch:389"
#CFG_CERN_LDAP_BASE = "ou=users,ou=organic units,dc=cern,dc=ch"

CFG_CERN_LDAP_BASE = "dc=cern,dc=ch"

# This one also works but the previous one is recommended
# CFG_CERN_LDAP_URI  = "ldap://ldap.cern.ch"
# CFG_CERN_LDAP_BIND = "cn=%s,ou=users,ou=organic units,dc=cern,dc=ch"
# CFG_CERN_LDAP_BASE = "O=CERN,C=CH"

_ldap_connection_pool = {}

def _cern_ldap_login():
    #user, password = decodestring(_cern_nice_soap_auth).split(':', 1)
    connection = ldap.initialize(CFG_CERN_LDAP_URI)
    #connection.simple_bind(CFG_CERN_LDAP_BIND % user, password)
    return connection


def get_user_info_from_ldap(nickname="", email="", ccid=""):
    """Query the CERN LDAP server for information about a user.
    Return a dictionary of information"""

    try:
        connection = _ldap_connection_pool[get_ident()]
    except KeyError:
        connection = _ldap_connection_pool[get_ident()] = _cern_ldap_login()

    if nickname:
        query = '(displayName=%s)' % ldap.filter.escape_filter_chars(nickname)
    elif email:
        query = '(mail=%s)' % ldap.filter.escape_filter_chars(email)
    elif ccid:
        query = '(employeeID=%s)' % ldap.filter.escape_filter_chars(str(ccid))
    else:
        return {}

    query_filter = "(& %s (| (employeetype=primary) (employeetype=external) (employeetype=ExCern) ) )" % query
    try:
        results = connection.search_st(CFG_CERN_LDAP_BASE, ldap.SCOPE_SUBTREE,
                                query_filter, timeout=5)
    except ldap.LDAPError:
        ## Mmh.. connection error? Let's reconnect at least once just in case
        sleep(1)
        connection = _ldap_connection_pool[get_ident()] = _cern_ldap_login()
        results = connection.search_st(CFG_CERN_LDAP_BASE, ldap.SCOPE_SUBTREE,
                                query_filter, timeout=5)

    if len(results) > 1:
        ## Maybe one ExCern and primary at the same time. In this case let's give precedence to ExCern
        types = {}
        for result in results:
            if result[1]['employeeType'][0] == 'Primary' and result[1]['userAccountControl'][0] == '512':
                return result[1]
            types[result[1]['employeeType'][0]] = result[1]
        if 'ExCern' in types and 'Primary' in types:
            return types['ExCern']
        if 'Primary' in types:
            return types['Primary']
        ## Ok otherwise we just pick up something :-)
    if results:
        return results[0][1]
    else:
        return {}
