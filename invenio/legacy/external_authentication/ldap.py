# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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

"""External user authentication for EPFL's LDAP instance.

This LDAP external authentication system relies on a collaborative LDAP
organized like this:

o=EPFL, c=CH
    |
    |
    +--ou=groups
    |      |
    |      |
    |      +--- cn=xxx
    |           displayName= name of the group
    |           uniqueIdentifier= some local id for groups
    |
    |
    |
    +--ou=users
    |     |
    |     |
    |     +---uid= some local id for users (ex: grfavre)
    |         uniqueIdentifier= another local id (ex: 128933)
    |         mail=xxx@xxx.xx
    |         memberOf= id of a group
    |         memberOf= id of another group
    |
    +

This example of an LDAP authentication should help you develop yours in your
specific installation.
"""

__revision__ = \
    "$Id$"

import ldap
from invenio.external_authentication import ExternalAuth, \
                                            InvenioWebAccessExternalAuthError



CFG_EXTERNAL_AUTH_LDAP_SERVERS = ['ldap://scoldap.epfl.ch']
CFG_EXTERNAL_AUTH_LDAP_CONTEXT = "o=EPFL,c=CH"
CFG_EXTERNAL_AUTH_LDAP_USER_UID  = ["uid", "uniqueIdentifier", "mail"]
CFG_EXTERNAL_AUTH_LDAP_MAIL_ENTRY = 'mail'
CFG_EXTERNAL_AUTH_LDAP_GROUP_MEMBERSHIP = 'memberOf'
CFG_EXTERNAL_AUTH_LDAP_GROUP_UID = 'uniqueIdentifier'
CFG_EXTERNAL_AUTH_LDAP_GROUP_NAME = 'displayName'

CFG_EXTERNAL_AUTH_LDAP_HIDDEN_GROUPS = ['EPFL-unit', 'users']

class ExternalAuthLDAP(ExternalAuth):
    """
    External authentication example for a custom LDAP-based
    authentication service.
    """
    def __init__(self):
        """Initialize stuff here"""
        ExternalAuth.__init__(self)
        self.enforce_external_nicknames = True

    def _ldap_try (self, command):
        """ Try to run the specified command on the first LDAP server that
        is not down."""
        for server in CFG_EXTERNAL_AUTH_LDAP_SERVERS:
            try:
                connection = ldap.initialize(server)
                return command(connection)
            except ldap.SERVER_DOWN, error_message:
                continue
        raise InvenioWebAccessExternalAuthError


    def auth_user(self, username, password, req=None):
        """
        Check USERNAME and PASSWORD against the LDAP system.
        Return (None, None) if authentication failed, or the (email address, user_dn) of the
        person if the authentication was successful.
        Raise InvenioWebAccessExternalAuthError in case of external troubles.
        Note: for SSO the parameter are discarded and overloaded by Shibboleth
        variables
        """
        if not password:
            return None, None

        query = '(|' + ''.join (['(%s=%s)' % (attrib, username)
                                 for attrib in
                                     CFG_EXTERNAL_AUTH_LDAP_USER_UID]) \
                 + ')'

        def _check (connection):
            users = connection.search_s(CFG_EXTERNAL_AUTH_LDAP_CONTEXT,
                                        ldap.SCOPE_SUBTREE,
                                        query)

            # We pick the first result, as all the data we are interested
            # in should be the same in all the entries.
            if len(users):
                user_dn, user_info = users [0]
            else:
                return None, None
            try:
                connection.simple_bind_s(user_dn, password)
            except ldap.INVALID_CREDENTIALS:
                # It is enough to fail on one server to consider the credential
                # to be invalid
                return None, None
            return user_info[CFG_EXTERNAL_AUTH_LDAP_MAIL_ENTRY][0], user_dn

        return self._ldap_try(_check)

    def user_exists(self, email, req=None):
        """Check the external authentication system for existance of email.
        @return: True if the user exists, False otherwise
        """
        query = '(%s=%s)' % (CFG_EXTERNAL_AUTH_LDAP_MAIL_ENTRY, email)
        def _check (connection):
            users = connection.search_s(CFG_EXTERNAL_AUTH_LDAP_CONTEXT,
                                        ldap.SCOPE_SUBTREE,
                                        query)
            return len(users) != 0
        return self._ldap_try(_check)

    def fetch_user_nickname(self, username, password=None, req=None):
        """Given a username and a password, returns the right nickname belonging
        to that user (username could be an email).
        """
        query = '(|' + ''.join (['(%s=%s)' % (attrib, username)
                                 for attrib in
                                     CFG_EXTERNAL_AUTH_LDAP_USER_UID]) \
                 + ')'
        def _get_nickname(connection):
            users = connection.search_s(CFG_EXTERNAL_AUTH_LDAP_CONTEXT,
                                        ldap.SCOPE_SUBTREE,
                                        query)
            # We pick the first result, as all the data we are interested
            # in should be the same in all the entries.
            if len(users):
                user_dn, user_info = users [0]
            else:
                return None
            emails = user_info[CFG_EXTERNAL_AUTH_LDAP_MAIL_ENTRY]
            if len(emails):
                email = emails[0]
            else:
                return False
            (left_part, right_part) = email.split('@')
            nickname = left_part.replace('.', ' ').title()
            if right_part != 'epfl.ch':
                nickname += ' - ' + right_part
            return nickname
        return self._ldap_try(_get_nickname)

    def fetch_user_groups_membership(self, username, password=None, req=None):
        """Given a username and a password, returns a dictionary of groups
        and their description to which the user is subscribed.
        Raise InvenioWebAccessExternalAuthError in case of troubles.
        """
        query_person = '(|' + ''.join (['(%s=%s)' % (attrib, username)
                                 for attrib in
                                     CFG_EXTERNAL_AUTH_LDAP_USER_UID]) \
                        + ')'
        def _get_groups(connection):
            users = connection.search_s(CFG_EXTERNAL_AUTH_LDAP_CONTEXT,
                                        ldap.SCOPE_SUBTREE,
                                        query_person)
            if len(users):
                user_dn, user_info = users [0]
            else:
                return {}
            groups = {}
            group_ids = user_info[CFG_EXTERNAL_AUTH_LDAP_GROUP_MEMBERSHIP]
            for group_id in group_ids:
                query_group = '(%s=%s)' % (CFG_EXTERNAL_AUTH_LDAP_GROUP_UID,
                                           group_id)
                ldap_group = connection.search_s(CFG_EXTERNAL_AUTH_LDAP_CONTEXT,
                                                 ldap.SCOPE_SUBTREE,
                                                 query_group)
                if len(ldap_group):
                    group_dn, group_infos = ldap_group[0]
                    group_name = group_infos[CFG_EXTERNAL_AUTH_LDAP_GROUP_NAME][0]
                    if group_name in CFG_EXTERNAL_AUTH_LDAP_HIDDEN_GROUPS:
                        continue
                    groups[group_id] = group_name
            return groups
        return self._ldap_try(_get_groups)

    def fetch_user_preferences(self, username, password=None, req=None):
        """Given a username and a password, returns a dictionary of keys and
        values, corresponding to external infos and settings.

        userprefs = {"telephone": "2392489",
                     "address": "10th Downing Street"}

        (WEBUSER WILL erase all prefs that starts by EXTERNAL_ and will
        store: "EXTERNAL_telephone"; all internal preferences can use whatever
        name but starting with EXTERNAL). If a pref begins with HIDDEN_ it will
        be ignored.
        """
        query = '(|' + ''.join (['(%s=%s)' % (attrib, username)
                                 for attrib in
                                     CFG_EXTERNAL_AUTH_LDAP_USER_UID]) \
                 + ')'
        def _get_personal_infos(connection):
            users = connection.search_s(CFG_EXTERNAL_AUTH_LDAP_CONTEXT,
                                        ldap.SCOPE_SUBTREE,
                                        query)
            if len(users):
                user_dn, user_info = users [0]
                return user_info
            else:
                return {}
        return self._ldap_try(_get_personal_infos)


