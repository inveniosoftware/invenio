# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

"""External user authentication for CERN NICE/CRA Invenio."""

__revision__ = \
    "$Id$"

import httplib
import socket

from invenio.external_authentication import ExternalAuth, \
        WebAccessExternalAuthError
from invenio.external_authentication_cern_wrapper import AuthCernWrapper


class ExternalAuthCern(ExternalAuth):
    """
    External authentication example for a custom HTTPS-based
    authentication service (called "CERN NICE").
    """


    def __init__(self):
        """Initialize stuff here"""
        ExternalAuth.__init__(self)
        self.connection = AuthCernWrapper()
        #self.name = "CERN NICE (external)"
        self.last_username = None
        self.last_password = None
        self.last_prefs = None

    def auth_user(self, username, password):
        """
        Check USERNAME and PASSWORD against CERN NICE/CRA database.
        Return None if authentication failed, email address of the
        person if authentication succeeded.
        """

        try:
            infos = self.connection.get_user_info(username, password)
        except socket.error, httplib.CannotSendRequest:
            self.connection = AuthCernWrapper()
            try:
                infos = self.connection.get_user_info(username, password)
            except socket.error, httplib.CannotSendRequest:
                raise WebAccessExternalAuthError
        if "email" in infos:
            self.last_username = username
            self.last_password = password
            self.last_prefs = infos
            return infos["email"]
        else:
            return None

    def fetch_user_groups_membership(self, email, password=None):
        """Fetch user groups membership from the CERN NICE/CRA account.
        @return a dictionary of groupname, group description
        """
        try:
            groups = self.connection.get_groups_for_user(email)
        except socket.error, httplib.CannotSendRequest:
            self.connection = AuthCernWrapper()
            try:
                groups = self.connection.get_groups_for_user(email)
            except socket.error, httplib.CannotSendRequest:
                raise WebAccessExternalAuthError
        return dict(map(lambda x: (x, '@' in x and x + ' (Mailing list)' \
                        or x + ' (Group)'), groups))


    def fetch_user_preferences(self, username, password=None):
        """Fetch user preferences/settings from the CERN Nice account.
        the external key will be '1' if the account is external to NICE/CRA,
        otherwise 0
        @return a dictionary. Note: auth and respccid are hidden
        """
        if username == self.last_username and password == self.last_password:
            prefs = self.last_prefs
        else:
            try:
                prefs = self.connection.get_user_info(username, password).items()
            except socket.error, httplib.CannotSendRequest:
                self.connection = AuthCernWrapper()
                try:
                    prefs = self.connection.get_user_info(username, password).items()
                except socket.error, httplib.CannotSendRequest:
                    raise WebAccessExternalAuthError
        ret = {}
        for key, value in prefs:
            if key in ['auth', 'respccid', 'ccid']:
                ret['HIDDEN_' + key] = value
            else:
                ret[key] = value
        if int(ret['HIDDEN_auth']) == 3 \
                and (int(ret['HIDDEN_respccid']) > 0 \
                or not ret['email'].endswith('@cern.ch')):
            ret['external'] = '1'
        else:
            ret['external'] = '0'
        return ret



