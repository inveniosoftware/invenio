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

"""Nice API Python wrapper."""

__revision__ = \
    "$Id$"

import httplib
import urllib
import re
import socket

from invenio.config import CFG_ETCDIR
from invenio.ext.logging import register_exception

_cern_nice_soap_file = open(CFG_ETCDIR + "/webaccess/cern_nice_soap_credentials.txt", "r")
_cern_nice_soap_auth = _cern_nice_soap_file.read().strip()
_cern_nice_soap_file.close()

_re_ccd_is_nice = re.compile('<string.*>(?P<CCID>.*)</string>')
_re_get_groups_for_user = re.compile("<string>(?P<group>.*)</string>")
_re_user_is_member_of_list = re.compile('<boolean.*>(?P<membership>.*)</boolean>')
_re_user_is_member_of_group = re.compile("<boolean.*>(?P<membership>.*)</boolean>")
_re_get_user_info = re.compile("<(?P<field>.*)>(?P<value>.*)</.*>")
_re_search_groups = re.compile("<string>(?P<group>.*)</string>")
_re_get_user_info_ex = re.compile("<(?P<field>.*)>(?P<value>.*)</.*>")
_re_list_users = re.compile("<(?P<field>.*)>(?P<value>.*)</.*>")

class AuthCernWrapper:
    """Wrapper class for CERN NICE/CRA webservice"""
    def __init__(self):
        """Create a connection to CERN NICE/CRA webservice.
        Authentication credential should be in the file
        CFG_ETCDIR/webaccess/cern_nice_soap_credentials.txt which must contain
        username:password in base64 encoding.
        """
        ## WORKAROUND for bug in Python up to 2.4.3
        ## Having a timeout is buggy with SSL
        self._headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain",
                   "Authorization": "Basic " + _cern_nice_soap_auth}
        self._conn = None

    def __del__(self):
        """Close the CERN Nice webservice connection."""
        if self._conn:
            self._conn.close()

    def _request(self, name, params):
        """Call the name request with a dictionary parms.
        @return: the XML response.
        """
        params = urllib.urlencode(params)
        socket_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(None)
        try:
            self._conn = httplib.HTTPSConnection("winservices-soap.web.cern.ch")
            self._conn.connect()
            self._conn.request("POST",
                    "/winservices-soap/generic/Authentication.asmx/%s" % name,
                    params, self._headers)
            response = self._conn.getresponse().read()
            self._conn.close()
        except:
            register_exception(alert_admin=True)
            raise
        socket.setdefaulttimeout(socket_timeout)
        return response

    def ccid_is_nice(self, ccid):
        """Verify this CCID belongs to a Nice account. Returns login or -1
        if not found.
        """
        data = self._request("CCIDisNice", {"CCID": ccid})
        match = _re_ccd_is_nice.search(data)
        if match:
            if match == -1:
                return False
            else:
                return match.group("CCID")

    def get_groups_for_user(self, user_name):
        """Returns a string array containing Groups the specified User is
        member of. UserName is NICE Login or Email. Listname can be 'listname'
        or 'listname@cern.ch'."""
        data = self._request("GetGroupsForUser", {"UserName": user_name})
        groups = []
        for match in _re_get_groups_for_user.finditer(data):
            groups.append(match.group("group"))
        return groups

    def user_is_member_of_list(self, user_name, list_name):
        """Check if one user is member of specified simba list. UserName is
        NICE Login or Email. Listname can be 'listname' or 'listname@cern.ch'.
        """
        data = self._request("UserIsMemberOfList",
                {"UserName": user_name, "ListName": list_name})
        match = _re_user_is_member_of_list.search(data)
        if match:
            match = match.group("membership")
            return match == "true"
        return None

    def user_is_member_of_group(self, user_name, group_name):
        """Check if one user is member of specified NICE Group. UserName is
        NICE Login or Email."""
        data = self._request("UserIsMemberOfGroup",
                {"UserName": user_name, "GroupName": group_name})
        match = _re_user_is_member_of_group.search(data)
        if match:
            match = match.group("membership")
            return match == "true"
        return None

    def get_user_info(self, user_name, password):
        """Authenticates user from login and password. Login can be email
        address or NICE login."""
        data = self._request("GetUserInfo",
                {"UserName": user_name, "Password": password})
        infos = {}
        for row in data.split('\r\n'):
            match = _re_get_user_info.search(row)
            if match:
                infos[match.group("field")] = match.group("value")
        return infos

    def search_groups(self, pattern):
        """Search for a group, based on given pattern. 3 characters minimum are
        required. Search is done with: *pattern*."""
        data = self._request("SearchGroups", {"pattern": pattern})
        groups = []
        for match in _re_search_groups.finditer(data):
            groups.append(match.group("group"))
        return groups

    def get_user_info_ex(self, user_name, password, group_name):
        """Authenticates user from login and password. Login can be email
        address or NICE login. Group membership is verified at the same time,
        multiple groups can be specified, separated with ','."""
        data = self._request("GetUserInfoEx", {"UserName": user_name,
                                               "Password": password,
                                               "GroupName": group_name})
        infos = {}
        for row in data.split('\r\n'):
            match = _re_get_user_info_ex.search(row)
            if match:
                infos[match.group("field")] = match.group("value")
        return infos

    def list_users(self, display_name):
        """Search users with given display name. Display name is firstname +
        lastname, or email, and can contain *."""
        data = self._request("ListUsers", {"DisplayName": display_name})
        users = []
        for row in data.split('\r\n'):
            if "<userInfo>" in row:
                current_user = {}
            elif "</userInfo>" in row:
                users.append(current_user)
            else:
                match = _re_list_users.search(row)
                if match:
                    current_user[match.group("field")] = match.group("value")
        return users

