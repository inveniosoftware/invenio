# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

"""
webmessage config file, here you can manage error messages, size of messages,
quotas, and some db related fields...
"""

__revision__ = "$Id$"

# status of message (table user_msgMESSAGE)
CFG_WEBMESSAGE_STATUS_CODE = \
{
    'NEW': 'N',
    'READ': 'R',
    'REMINDER': 'M'
}
# values indicating which results field to display while writing a message
CFG_WEBMESSAGE_RESULTS_FIELD = \
{
    'USER': 'user',
    'GROUP': 'group',
    'NONE': 'none'
}

# separator used in every list of recipients
CFG_WEBMESSAGE_SEPARATOR = ','

# list of roles (find them in accROLE table) without quota
CFG_WEBMESSAGE_ROLES_WITHOUT_QUOTA = ['superadmin']

# alert user also by email
CFG_WEBMESSAGE_EMAIL_ALERT = True

# Exceptions: errors
class InvenioWebMessageError(Exception):
    """A generic error for WebMessage."""
    def __init__(self, message):
        """Initialisation."""
        self.message = message
    def __str__(self):
        """String representation."""
        return repr(self.message)
