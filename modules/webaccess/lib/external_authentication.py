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

"""External user authentication for CDS Invenio."""

__revision__ = \
    "$Id$"


class WebAccessExternalAuthError(Exception):
    """Exception to signaling general external trouble."""
    pass


class ExternalAuth:
    """External authentication template example."""

    def __init__(self):
        """Initialize stuff here"""
        self.name = None
        pass

    def auth_user(self, username, password):
        """Authenticate user-supplied USERNAME and PASSWORD.  Return
        None if authentication failed, or the email address of the
        person if the authentication was successful.  In order to do
        this you may perhaps have to keep a translation table between
        usernames and email addresses.
        Raise WebAccessExternalAuthError in case of external troubles.
        """
        raise NotImplementedError
        #return None

    def user_exists(self, email):
        """Check the external authentication system for existance of email.
        @return True if the user exists, False otherwise
        """
        raise NotImplementedError


    def fetch_user_groups_membership(self, username, password=None):
        """Given a username, returns a dictionary of groups
        and their description to which the user is subscribed.
        Raise WebAccessExternalAuthError in case of troubles.
        """
        raise NotImplementedError
        #return {}

    def fetch_user_preferences(self, username, password=None):
        """Given a username and a password, returns a dictionary of keys and
        values, corresponding to external infos and settings.

        userprefs = {"telephone": "2392489",
                     "address": "10th Downing Street"}

        (WEBUSER WILL erase all prefs that starts by EXTERNAL_ and will
        store: "EXTERNAL_telephone"; all internal preferences can use whatever
        name but starting with EXTERNAL). If a pref begins with HIDDEN_ it will
        be ignored.
        """
        raise NotImplementedError
        #return {}

    def fetch_all_users_groups_membership(self):
        """Fetch all the groups with a description, and users who belong to
        each groups.
        @return {'mygroup': ('description', ['email1', 'email2', ...]), ...}
        """
        raise NotImplementedError
