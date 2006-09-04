# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

"""External user authentication for CDS Invenio."""

import httplib
import urllib
import re

class external_auth_nice:
    """External authentication example for a custom HTTPS-based
    authentication service (CERN NICE)."""
    
    users = {}
    name = ""

    def __init__(self):
        """Initialize stuff here"""
        pass

    def auth_user(self, username, password):
        """Check USERNAME and PASSWORD against CERN NICE database.
        Return None if authentication failed, email address of the
        person if authentication succeeded."""
        params = urllib.urlencode({'Username': username, 'Password': password})
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        conn = httplib.HTTPSConnection("weba5.cern.ch") 
        conn.request("POST", "/WinServices/Authentication/CDS/default.asp", params, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        m = re.search('<CCID>\d+</CCID>', data)
        if m:
            m = m.group()
            CCID = int(re.search('\d+', m).group())
            if CCID > 0:
                m = re.search('<EMAIL>.*?</EMAIL>', data)
                if m:
                    email = m.group()
                    email = email.replace('<EMAIL>', '')   
                    email = email.replace('</EMAIL>', '')  
                    return email 
        return None

class external_auth_template:
    """External authentication template example."""
    
    def __init__(self):
        """Initialize stuff here"""
        pass

    def auth_user(self, username, password):
        """Authenticate user-supplied USERNAME and PASSWORD.  Return
        None if authentication failed, or the email address of the
        person if the authentication was successful.  In order to do
        this you may perhaps have to keep a translation table between
        usernames and email addresses."""
        return None
