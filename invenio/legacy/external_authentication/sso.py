# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011, 2014 CERN.
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

"""External user authentication for CERN NICE/CRA Invenio."""

__revision__ = \
    "$Id$"

import re

from invenio.legacy.external_authentication import ExternalAuth


# Tunable list of settings to be hidden
# e.g.: CFG_EXTERNAL_AUTH_HIDDEN_SETTINGS = ('auth', 'respccid', 'personid')
CFG_EXTERNAL_AUTH_HIDDEN_SETTINGS = ()
# Tunable list of groups to be hidden
CFG_EXTERNAL_AUTH_HIDDEN_GROUPS = (
    'All Exchange People',
    'CERN Users',
    'cern-computing-postmasters',
    'cern-nice2000-postmasters',
    'CMF FrontEnd Users',
    'CMF_NSC_259_NSU',
    'Domain Users',
    'GP Apply Favorites Redirection',
    'GP Apply NoAdmin',
    'info-terminalservices',
    'info-terminalservices-members',
    'IT Web IT',
    'NICE Deny Enforce Password-protected Screensaver',
    'NICE Enforce Password-protected Screensaver',
    'NICE LightWeight Authentication WS Users',
    'NICE MyDocuments Redirection (New)',
    'NICE Profile Redirection',
    'NICE Terminal Services Users',
    'NICE Users',
    'NICE VPN Users',
    )
CFG_EXTERNAL_AUTH_HIDDEN_GROUPS_RE = (
    re.compile(r'Users by Letter [A-Z]'),
    re.compile(r'building-[\d]+'),
    re.compile(r'Users by Home CERNHOME[A-Z]'),
    )

# Prefix name for Shibboleth variables
CFG_EXTERNAL_AUTH_SSO_PREFIX_NAMES = ('ADFS_', 'Shib-')
# Name of the variable containing groups
CFG_EXTERNAL_AUTH_SSO_GROUP_VARIABLE = CFG_EXTERNAL_AUTH_SSO_PREFIX_NAMES[0] + 'GROUP'
# Name of the variable containing login name
CFG_EXTERNAL_AUTH_SSO_LOGIN_VARIABLE = CFG_EXTERNAL_AUTH_SSO_PREFIX_NAMES[0] + 'LOGIN'
# Name of the variable containing email
CFG_EXTERNAL_AUTH_SSO_EMAIL_VARIABLE = CFG_EXTERNAL_AUTH_SSO_PREFIX_NAMES[0] + 'EMAIL'
# Name of the variable containing groups
CFG_EXTERNAL_AUTH_SSO_GROUP_VARIABLE = CFG_EXTERNAL_AUTH_SSO_PREFIX_NAMES[0] + 'GROUP'
# Name of the variable containing federation
CFG_EXTERNAL_AUTH_SSO_FEDERATION_VARIABLE = CFG_EXTERNAL_AUTH_SSO_PREFIX_NAMES[0] + 'FEDERATION'
# Name of the variable containing fullname
CFG_EXTERNAL_AUTH_SSO_FULLNAME_VARIABLE = CFG_EXTERNAL_AUTH_SSO_PREFIX_NAMES[0] + 'FULLNAME'
# Name of the variable containing role
CFG_EXTERNAL_AUTH_SSO_ROLE_VARIABLE = CFG_EXTERNAL_AUTH_SSO_PREFIX_NAMES[0] + 'ROLE'
# Separator character for group variable
CFG_EXTERNAL_AUTH_SSO_GROUPS_SEPARATOR = ';'

class ExternalAuthSSO(ExternalAuth):
    """
    External authentication example for a custom SSO-based
    authentication service.
    """


    def __init__(self, enforce_external_nicknames=False):
        """Initialize stuff here"""
        ExternalAuth.__init__(self, enforce_external_nicknames)
        self.egroup_cache = None


    def in_shibboleth(self, req):
        """
        Return True if the current request handler is actually under
        Shibboleth control.
        """
        return CFG_EXTERNAL_AUTH_SSO_EMAIL_VARIABLE in req.subprocess_env

    def auth_user(self, username, password, req=None):
        """
        Check USERNAME and PASSWORD against the SSO system.
        Return (None, None) if authentication failed, or the
        (email address, nickname) of the
        person if the authentication was successful.  In order to do
        this you may perhaps have to keep a translation table between
        usernames and email addresses.
        If it is the first time the user logs in Invenio the nickname is
        stored alongside the email. If this nickname is unfortunatly already
        in use it is discarded. Otherwise it is ignored.
        Raise InvenioWebAccessExternalAuthError in case of external troubles.
        Note: for SSO the parameter are discarded and overloaded by Shibboleth
        variables
        """
        if req:
            req.add_common_vars()
            if CFG_EXTERNAL_AUTH_SSO_EMAIL_VARIABLE in req.subprocess_env:
                return req.subprocess_env[CFG_EXTERNAL_AUTH_SSO_EMAIL_VARIABLE], req.subprocess_env[CFG_EXTERNAL_AUTH_SSO_LOGIN_VARIABLE]
        return None, None

    #def user_exists(self, email, req=None):
        #"""Checks against CERN NICE/CRA for existance of email.
        #@return: True if the user exists, False otherwise
        #"""
        #users = self._try_twice(funct=AuthCernWrapper.list_users, \
                #params={"display_name":email})
        #return email.upper() in [user['email'].upper() for user in users]


    def fetch_user_groups_membership(self, email, password=None, req=None):
        """Fetch user groups membership from the SSO system.
        @return: a dictionary of groupname, group description
        Note: for SSO the parameter are discarded and overloaded by Shibboleth
        variables
        """
        return self._fetch_egroups(req)

    def fetch_user_nickname(self, username, password=None, req=None):
        """Given a username and a password, returns the right nickname
        belonging to that user (username could be an email).
        Note: for SSO the parameter are discarded and overloaded by Shibboleth
        variables
        """
        if req:
            req.add_common_vars()
            # Extract all necessary adfs variables
            federation = req.subprocess_env.get(
                CFG_EXTERNAL_AUTH_SSO_FEDERATION_VARIABLE)
            fullname = req.subprocess_env.get(
                CFG_EXTERNAL_AUTH_SSO_FULLNAME_VARIABLE)
            email = req.subprocess_env.get(
                CFG_EXTERNAL_AUTH_SSO_EMAIL_VARIABLE)
            role = req.subprocess_env.get(
                CFG_EXTERNAL_AUTH_SSO_ROLE_VARIABLE)
            if federation == "CERN" and role == "CERN Users":
                nickname = fullname
            else:
                if fullname != email:
                    nickname = fullname
                else:
                    local_part, domain_part = email.split("@", 1)
                    joined_name = " ".join(domain_part.split(".")[:-1]).upper()
                    nickname = "{0} [{1}]".format(
                        local_part, joined_name
                    )
            return nickname
        else:
            return None

    def _fetch_egroups(self, req=None):
        if False: #self.egroup_cache is not None:
            return self.egroup_cache
        elif req:
            req.add_common_vars()
            if CFG_EXTERNAL_AUTH_SSO_GROUP_VARIABLE in req.subprocess_env:
                groups = req.subprocess_env[CFG_EXTERNAL_AUTH_SSO_GROUP_VARIABLE].split(CFG_EXTERNAL_AUTH_SSO_GROUPS_SEPARATOR)
                # Filtering out uncomfortable groups
                groups = [group for group in groups if group not in CFG_EXTERNAL_AUTH_HIDDEN_GROUPS]
                for regexp in CFG_EXTERNAL_AUTH_HIDDEN_GROUPS_RE:
                    for group in groups:
                        if regexp.match(group):
                            groups.remove(group)
                self.egroup_cache = dict(map(lambda x: (x, '@' in x and x + ' (Mailing list)' \
                                or x + ' (Group)'), groups))
                return self.egroup_cache
        return {}


    def _fetch_particular_preferences(self, req=None):
        """This hidden method is there to be overwritten in order to get some
        particular value from non standard variables.
        """
        if req:
            ret = {}
            req.add_common_vars()
            if 'HTTP_SHIB_AUTHENTICATION_METHOD' in req.subprocess_env:
                ret['authmethod'] = req.subprocess_env['HTTP_SHIB_AUTHENTICATION_METHOD']
            ret['external'] = '1'
            if 'ADFS_IDENTITYCLASS' in req.subprocess_env and \
              req.subprocess_env['ADFS_IDENTITYCLASS'] in ('CERN Registered', 'CERN Shared'):
                ret['external'] = '0'
            return ret
        return {}


    def fetch_user_preferences(self, username, password=None, req=None):
        """Fetch user preferences/settings from the SSO account.
        the external key will be '1' if the account is external to SSO,
        otherwise 0
        @return: a dictionary.
        Note: for SSO the parameter are discarded and overloaded by Shibboleth
        variables
        """
        if req:
            req.add_common_vars()
            ret = {}
            prefs = self._fetch_particular_preferences(req)
            for key, value in req.subprocess_env.items():
                for prefix in CFG_EXTERNAL_AUTH_SSO_PREFIX_NAMES:
                    if key.startswith(prefix) and not key == CFG_EXTERNAL_AUTH_SSO_GROUP_VARIABLE:
                        prefs[key[len(prefix):].lower()] = value
                        break
            for key, value in prefs.items():
                if key in CFG_EXTERNAL_AUTH_HIDDEN_SETTINGS:
                    ret['HIDDEN_' + key] = value
                else:
                    ret[key] = value
            return ret
        return {}
