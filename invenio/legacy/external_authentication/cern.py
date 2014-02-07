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

"""External user authentication for CERN NICE/CRA Invenio."""

__revision__ = \
    "$Id$"

import httplib
import socket
import re

from invenio.errorlib import register_exception
from invenio.external_authentication import ExternalAuth, \
        InvenioWebAccessExternalAuthError
from invenio.external_authentication_cern_wrapper import AuthCernWrapper


# Tunable list of settings to be hidden
CFG_EXTERNAL_AUTH_CERN_HIDDEN_SETTINGS = ['auth', 'respccid', 'ccid']
# Tunable list of groups to be hidden
CFG_EXTERNAL_AUTH_HIDDEN_GROUPS = (
    'All Exchange People',
    'CERN Users',
    'cern-computing-postmasters@cern.ch',
    'cern-nice2000-postmasters@cern.ch',
    'CMF FrontEnd Users',
    'CMF_NSC_259_NSU',
    'Domain Users',
    'GP Apply Favorites Redirection',
    'GP Apply NoAdmin',
    'info-terminalservices@cern.ch',
    'info-terminalservices-members@cern.ch',
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

class ExternalAuthCern(ExternalAuth):
    """
    External authentication example for a custom HTTPS-based
    authentication service (called "CERN NICE").
    """


    def __init__(self):
        """Initialize stuff here"""
        ExternalAuth.__init__(self)
        try:
            self.connection = AuthCernWrapper()
        except (httplib.CannotSendRequest, socket.error, AttributeError,
                IOError, TypeError), msg: # Let the user note that
                                     # no connection is available
            register_exception(alert_admin=True)
            raise InvenioWebAccessExternalAuthError, msg

    def _try_twice(self, funct, params):
        """Try twice to execute funct on self.connection passing it params.
        If for various reason the connection doesn't work it's restarted
        """
        try:
            ret = funct(self.connection, **params)
        except (httplib.CannotSendRequest, socket.error, AttributeError,
                IOError, TypeError):
            try:
                self.connection = AuthCernWrapper()
                ret = funct(self.connection, **params)
            except (httplib.CannotSendRequest, socket.error, AttributeError,
                    IOError, TypeError):
                register_exception(alert_admin=True)
                self.connection = None
                raise InvenioWebAccessExternalAuthError
        return ret


    def auth_user(self, username, password, req=None):
        """
        Check USERNAME and PASSWORD against CERN NICE/CRA database.
        Return (None, None) if authentication failed, or the
        (email address, nickname) of the
        person if the authentication was successful.  In order to do
        this you may perhaps have to keep a translation table between
        usernames and email addresses.
        If it is the first time the user logs in Invenio the nickname is
        stored alongside the email. If this nickname is unfortunatly already
        in use it is discarded. Otherwise it is ignored.
        Raise InvenioWebAccessExternalAuthError in case of external troubles.
        """

        infos = self._try_twice(funct=AuthCernWrapper.get_user_info, \
                params={"user_name":username, "password":password})
        if "email" in infos:
            return infos["email"], infos["login"]
        else:
            return None, None

    def user_exists(self, email, req=None):
        """Checks against CERN NICE/CRA for existance of email.
        @return: True if the user exists, False otherwise
        """
        users = self._try_twice(funct=AuthCernWrapper.list_users, \
                params={"display_name":email})
        return email.upper() in [user['email'].upper() for user in users]


    def fetch_user_groups_membership(self, email, password=None, req=None):
        """Fetch user groups membership from the CERN NICE/CRA account.
        @return: a dictionary of groupname, group description
        """
        groups = self._try_twice(funct=AuthCernWrapper.get_groups_for_user, \
                params={"user_name":email})
        # Filtering out uncomfortable groups
        groups = [group for group in groups if group not in
            CFG_EXTERNAL_AUTH_HIDDEN_GROUPS]
        for regexp in CFG_EXTERNAL_AUTH_HIDDEN_GROUPS_RE:
            for group in groups:
                if regexp.match(group):
                    groups.remove(group)
        # Produce list of double value: group/mailing list(with stripped
        # @cern.ch) name, and group/description built from the name.
        return dict(map(lambda x: (x.find('@') > -1 and x[:x.find('@')] or x,
                        '@' in x and x + ' (CERN Mailing list)'
                        or x + ' (CERN Group)'), groups))

    def fetch_user_nickname(self, username, password, req=None):
        """Given a username and a password, returns the right nickname
        belonging to that user (username could be an email).
        """
        infos = self._try_twice(funct=AuthCernWrapper.get_user_info,
                params={"user_name":username, "password":password})
        if "login" in infos:
            return infos["login"]
        else:
            return None


    def fetch_user_preferences(self, username, password=None, req=None):
        """Fetch user preferences/settings from the CERN Nice account.
        the external key will be '1' if the account is external to NICE/CRA,
        otherwise 0
        @return: a dictionary. Note: auth and respccid are hidden
        """
        prefs = self._try_twice(funct=AuthCernWrapper.get_user_info, \
                params={"user_name":username, "password":password})
        ret = {}
        try:
            if int(prefs['auth']) == 3 \
                    and (int(prefs['respccid']) > 0 \
                    or not prefs['email'].endswith('@cern.ch')):
                ret['external'] = '1'
            else:
                ret['external'] = '0'
        except KeyError:
            ret['external'] = '1'
        for key, value in prefs.items():
            if key in CFG_EXTERNAL_AUTH_CERN_HIDDEN_SETTINGS:
                ret['HIDDEN_' + key] = value
            else:
                ret[key] = value

        ## Hack to be forward-compatible with CERN SSO implementation
        if ret.has_key('company'):
            ret['homeinstitute'] = ret['company']
            del ret['company']
        if ret.has_key('name'):
            ret['fullname'] = ret['name']
            del ret['name']
        return ret

