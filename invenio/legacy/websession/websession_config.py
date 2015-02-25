# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

# pylint: disable=C0301

"""WebSession configuration parameters."""

__revision__ = "$Id$"

CFG_WEBSESSION_GROUP_JOIN_POLICY = {'VISIBLEOPEN': 'VO',
                                    'VISIBLEMAIL': 'VM',
                                    'INVISIBLEOPEN': 'IO',
                                    'INVISIBLEMAIL': 'IM',
                                    'VISIBLEEXTERNAL' : 'VE'
                                    }

CFG_WEBSESSION_USERGROUP_STATUS = {'ADMIN':  'A',
                                   'MEMBER':'M',
                                   'PENDING':'P'
                                   }

CFG_WEBSESSION_INFO_MESSAGES = {"GROUP_CREATED": 'You have successfully created a new group.',
                                "JOIN_GROUP": 'You have successfully joined a new group.',
                                "GROUP_UPDATED": 'You have successfully updated a group.',
                                "GROUP_DELETED": 'You have successfully deleted a group.',
                                "MEMBER_DELETED": 'You have successfully deleted a member.',
                                "MEMBER_ADDED": 'You have successfully added a new member.',
                                "MEMBER_REJECTED": 'You have successfully removed a waiting member from the list.',
                                "JOIN_REQUEST": 'The group administrator has been notified of your request.',
                                "LEAVE_GROUP": 'You have successfully left a group.'

}

# Choose the providers which will be dislayed bigger (48x48) on login page.
# The order of the list decides the order of the login buttons.
CFG_EXTERNAL_LOGIN_LARGE = [
    "facebook",
    "google",
    "yahoo",
    "openid"
]

# Choose the order of the login buttons. The unordered providers will be
# displayed alphabetically after the ordered ones.
CFG_EXTERNAL_LOGIN_BUTTON_ORDER = []

# Select the labels of the username inputs for openid providers which needs
# username for authorization.
CFG_EXTERNAL_LOGIN_FORM_LABELS = {
    "openid": "Your OpenID Identifier",
    "aol": "Your AOL screenname",
    "myopenid": "Your myOpenID username",
    "myvidoop": "Your myvidoop username",
    "verisign": "Your VeriSign username",
    "wordpress": "Your WordPress username",
    "myspace": "Your myspace username",
    "livejournal": "Your livejournal username",
    "blogger": "The address of your blog"
}

CFG_WEBSESSION_COOKIE_NAME = "INVENIOSESSION"
CFG_WEBSESSION_ONE_DAY = 86400 #: how many seconds are there in one day
CFG_WEBSESSION_CLEANUP_CHANCE = 10000 #: cleanups have 1 in CLEANUP_CHANCE chance

# FIXME: Session locking is currently disabled because, since it's
# implementing the mod_python technique of using Apache mutexes, these
# are by default a very limited resources (according to
# <http://www.modpython.org/live/current/doc-html/inst-apacheconfig.html#l2h-21>)
# only 8 mutexes are available by default)
# Since the session would be locked at constructor time and unlocked at
# destructor time, and since we cache the session for the whole request
# handling time, enabling locking would mean that at most only 8 requests
# could been handled at the same time. This is quite limited and, anyway
# there's already local locking available thanks to our MySQL backend.
CFG_WEBSESSION_ENABLE_LOCKING = False

# Exceptions: errors
class InvenioWebSessionError(Exception):
    """A generic error for WebSession."""
    def __init__(self, message):
        """Initialisation."""
        self.message = message
    def __str__(self):
        """String representation."""
        return repr(self.message)

# Exceptions: warnings
class InvenioWebSessionWarning(Exception):
    """A generic warning for WebSession."""
    def __init__(self, message):
        """Initialisation."""
        self.message = message
    def __str__(self):
        """String representation."""
        return repr(self.message)
