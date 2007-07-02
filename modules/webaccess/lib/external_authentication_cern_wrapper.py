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

"""Nice API Python wrapper."""

__revision__ = \
    "$Id$"

import httplib
import urllib
import re

from invenio.config import etcdir


class AuthCernWrapper:
    """Wrapper class for CERN NICE/CRA webservice"""
    def __init__(self):
        """Create a connection to CERN NICE/CRA webservice.
        Authentication credential should be in the file
        etcdir/webaccess/cern_nice_soap_credentials.txt which must contain
        username:password in base64 encoding.
        """
        self._cern_nice_soap_auth = \
          open(etcdir + "/webaccess/cern_nice_soap_credentials.txt",
               "r").read().strip()
        self._headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain",
                   "Authorization": "Basic " + self._cern_nice_soap_auth}
        self._conn = httplib.HTTPSConnection("winservices-soap.web.cern.ch")

    def __del__(self):
        """Close the CERN Nice webservice connection."""
        if self._conn:
            self._conn.close()

    def _request(self, name, params):
        """Call the name request with a dictionary parms.
        @return the XML response.
        """
        params = urllib.urlencode(params)
        self._conn.request("POST",
                "/winservices-soap/generic/Authentication.asmx/%s" % name,
                params, self._headers)
        response = self._conn.getresponse()
        return response.read()


    def ccid_is_nice(self, ccid):
        """Verify this CCID belongs to a Nice account. Returns login or -1
        if not found.
        """
        data = self._request("CCIDisNice", {"CCID": ccid})
        match = re.search('<string.*>(?P<CCID>.*)</string>', data)
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
        for match in re.finditer("<string>(?P<group>.*)</string>", data):
            groups.append(match.group("group"))
        return groups

    def user_is_member_of_list(self, user_name, list_name):
        """Check if one user is member of specified simba list. UserName is
        NICE Login or Email. Listname can be 'listname' or 'listname@cern.ch'.
        """
        data = self._request("UserIsMemberOfList",
                {"UserName": user_name, "ListName": list_name})
        match = re.search('<boolean.*>(?P<membership>.*)</boolean>', data)
        if match:
            match = match.group("membership")
            if match == "true":
                return True
            else:
                return False
        return None

    def user_is_member_of_group(self, user_name, group_name):
        """Check if one user is member of specified NICE Group. UserName is
        NICE Login or Email."""
        data = self._request("UserIsMemberOfGroup",
                {"UserName": user_name, "GroupName": group_name})
        match = re.search("<boolean.*>(?P<membership>.*)</boolean>", data)
        if match:
            match = match.group("membership")
            if match == "true":
                return True
            else:
                return False
        return None

    def get_user_info(self, user_name, password):
        """Authenticates user from login and password. Login can be email
        address or NICE login."""
        data = self._request("GetUserInfo",
                {"UserName": user_name, "Password": password})
        infore = re.compile("<(?P<field>.*)>(?P<value>.*)</.*>")
        infos = {}
        for row in data.split('\r\n'):
            match = infore.search(row)
            if match:
                infos[match.group("field")] = match.group("value")
        return infos

    def search_groups(self, pattern):
        """Search for a group, based on given pattern. 3 characters minimum are
        required. Search is done with: *pattern*."""
        data = self._request("SearchGroups", {"pattern": pattern})
        groups = []
        for match in re.finditer("<string>(?P<group>.*)</string>", data):
            groups.append(match.group("group"))
        return groups

    def get_user_info_ex(self, user_name, password, group_name):
        """Authenticates user from login and password. Login can be email
        address or NICE login. Group membership is verified at the same time,
        multiple groups can be specified, separated with ','."""
        data = self._request("GetUserInfoEx", {"UserName": user_name,
                                               "Password": password,
                                               "GroupName": group_name})
        infore = re.compile("<(?P<field>.*)>(?P<value>.*)</.*>")
        infos = {}
        for row in data.split('\r\n'):
            match = infore.search(row)
            if match:
                infos[match.group("field")] = match.group("value")
        return infos

    def list_users(self, display_name):
        """Search users with given display name. Display name is firstname +
        lastname, or email, and can contain *."""
        data = self._request("ListUsers", {"DisplayName": display_name})
        users = []
        infore = re.compile("<(?P<field>.*)>(?P<value>.*)</.*>")
        for row in data.split('\r\n'):
            if "<userInfo>" in row:
                current_user = {}
            elif "</userInfo>" in row:
                users.append(current_user)
            else:
                match = infore.search(row)
                if match:
                    current_user[match.group("field")] = match.group("value")
        return users

