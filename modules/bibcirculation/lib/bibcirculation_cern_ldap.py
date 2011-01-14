## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
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

"""Invenio LDAP interface for BibCirculation at CERN. """

from invenio.config import CFG_CERN_SITE
try:
    import ldap
    from invenio.external_authentication_cern_wrapper import _cern_nice_soap_auth
    CFG_BIBCIRCULATION_HAS_LDAP = CFG_CERN_SITE
except (ImportError, IOError):
    CFG_BIBCIRCULATION_HAS_LDAP = False

from thread import get_ident
from base64 import decodestring

CFG_CERN_LDAP_URI = "ldaps://ldap.cern.ch:636"
CFG_CERN_LDAP_BIND = "n=%s,ou=users,o=cern,c=ch"
CFG_CERN_LDAP_BASE = "O=CERN,C=CH"

_ldap_connection_pool = {}

def _cern_ldap_login():
    user, password = decodestring(_cern_nice_soap_auth).split(':', 1)
    connection = ldap.initialize(CFG_CERN_LDAP_URI)
    connection.simple_bind(CFG_CERN_LDAP_BIND % user, password)
    return connection

def get_user_info_from_ldap(nickname="", email="", ccid=""):
    """Query the CERN LDAP server for information about a user.
    Return a dictionary of information"""
    try:
        connection = _ldap_connection_pool[get_ident()]
    except KeyError:
        connection = _ldap_connection_pool[get_ident()] = _cern_ldap_login()
    if nickname:
        query = '(displayName=%s)' % nickname
    elif email:
        query = '(mail=%s)' % email
    elif ccid:
        query = '(employeeID=%s)' % ccid
    else:
        return {}
    try:
        result = connection.search_st(CFG_CERN_LDAP_BASE, ldap.SCOPE_SUBTREE, query,  timeout=5)
        if result and nickname:
            return result
        else:
            try:
                return result[0][1]
            except IndexError:
                return {}
    except ldap.TIMEOUT:
        pass
    return {}

