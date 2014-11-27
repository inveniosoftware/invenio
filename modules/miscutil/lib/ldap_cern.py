## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011, 2014 CERN.
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

"""Invenio LDAP interface for CERN. """

from time import sleep
from thread import get_ident

import ldap
import ldap.filter

CFG_CERN_LDAP_URI = "ldap://xldap.cern.ch:389"
CFG_CERN_LDAP_BASE = "OU=Users,OU=Organic Units,DC=cern,DC=ch"

_ldap_connection_pool = {}


def _cern_ldap_login():
    """Get a connection from _ldap_connection_pool or create a new one"""
    try:
        connection = _ldap_connection_pool[get_ident()]
    except KeyError:
        connection = _ldap_connection_pool[get_ident()] = ldap.initialize(CFG_CERN_LDAP_URI)
    return connection


def _sanitize_input(query):
    """
    Take the query, filter it through ldap.filter.escape_filter_chars and
    replace the dots with spaces.
    """
    query = ldap.filter.escape_filter_chars(query)
    query = query.replace(".", " ")
    return query


def get_users_info_by_displayName(displayName):
    """
    Query the CERN LDAP server for information about all users whose name
    contains the displayName.
    Return a list of user dictionaries (or empty list).
    """

    connection = _cern_ldap_login()

    # Split displayName and add each part of it to the search query
    if displayName:
        query = _sanitize_input(displayName)
        query_elements = query.split()
        query_filter = "& "
        for element in query_elements:
            query_filter += '(displayName=*%s*) ' % element
        # Query will look like that: "(& (displayName=*john*) (displayName=*smith*)"
        # Eliminate the secondary accounts (aliases, etc.)
        query_filter = "(& (%s) (| (employeetype=primary) (employeetype=external) (employeetype=ExCern) ) )" % query_filter
    else:
        return []

    try:
        results = connection.search_st(CFG_CERN_LDAP_BASE, ldap.SCOPE_SUBTREE,
                                       query_filter, timeout=5)
    except ldap.LDAPError:
        ## Mmh.. connection error? Let's reconnect at least once just in case
        sleep(1)
        connection = _cern_ldap_login()
        try:
            results = connection.search_st(CFG_CERN_LDAP_BASE, ldap.SCOPE_SUBTREE,
                                           query_filter, timeout=5)
        except ldap.LDAPError:
            # Another error (maybe the LDAP query size is too big, etc.)
            # TODO, if it's needed, here we can return various different
            # information based on the error message
            results = []
    return results


def get_users_info_by_displayName_or_email(name):
    """
    Query the CERN LDAP server for information about all users whose displayName
    or email contains the name.
    Return a list of user dictionaries (or empty list).
    """

    connection = _cern_ldap_login()

    # Split name and add each part of it to the search query
    if name:
        query = _sanitize_input(name)
        query_elements = query.split()
        query_filter_name = "& "
        query_filter_email = "& "
        for element in query_elements:
            query_filter_name += '(displayName=*%s*) ' % element
            query_filter_email += '(mail=*%s*) ' % element
        # query_filter_name will look like that:
        # "(| (& (displayName=*john*) (displayName=*smith*)) (& (mail=*john*) (mail=*smith*)) )"
        # Eliminate the secondary accounts (aliases, etc.)
        query_filter = "(& (| (%s) (%s)) (| (employeetype=primary) (employeetype=external) (employeetype=ExCern) ) )" % (query_filter_name, query_filter_email)
    else:
        return []

    try:
        results = connection.search_st(CFG_CERN_LDAP_BASE, ldap.SCOPE_SUBTREE,
                                       query_filter, timeout=5)
    except ldap.LDAPError:
        ## Mmh.. connection error? Let's reconnect at least once just in case
        sleep(1)
        connection = _cern_ldap_login()
        try:
            results = connection.search_st(CFG_CERN_LDAP_BASE, ldap.SCOPE_SUBTREE,
                                           query_filter, timeout=5)
        except ldap.LDAPError:
            # Another error (maybe the LDAP query size is too big, etc.)
            # TODO, if it's needed, here we can return various different
            # information based on the error message
            results = []
    return results
