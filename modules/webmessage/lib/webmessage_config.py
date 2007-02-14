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

"""
webmessage config file, here you can manage error messages, size of messages,
quotas, and some db related fields...
"""

__revision__ = "$Id$"

# error messages. (should not happen, except in case of reload, or url
# altering)
CFG_WEBMESSAGE_ERROR_MESSAGES = \
{   'ERR_WEBMESSAGE_NOTOWNER':  '_("This message is not in your mailbox")',
    'ERR_WEBMESSAGE_NONICKNAME':'_("No nickname or user for uid #%s")',
    'ERR_WEBMESSAGE_NOMESSAGE': '_("This message doesn\'t exist")'
}

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

# max length of a message
CFG_WEBMESSAGE_MAX_SIZE_OF_MESSAGE = 20000

# quota for messages for users (admins, see below)
CFG_WEBMESSAGE_MAX_NB_OF_MESSAGES = 30

# list of roles (find them in accROLE table) without quota
CFG_WEBMESSAGE_ROLES_WITHOUT_QUOTA = ['superadmin']

CFG_WEBMESSAGE_DAYS_BEFORE_DELETE_ORPHANS = 60
