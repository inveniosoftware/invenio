# -*- coding: utf-8 -*-
## $Id$
## 
## Configuration for webmessage module
##
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""
webmessage config file, here you can manage error messages, size of messages,
quotas, and some db related fields...
"""
__revision__ = '1.3, 15 nov 2005 '

# error messages. (should not happen, except in case of reload, or url altering) 
cfg_webmessage_error_messages = \
{   'ERR_WEBMESSAGE_NOTOWNER':  '_("This message is not in your mailbox")',
    'ERR_WEBMESSAGE_NONICKNAME':'_("No nickname or user for uid #%s")',
    'ERR_WEBMESSAGE_NOMESSAGE': '_("This message doesn\'t exist")'
}

# status of message (table user_msgMESSAGE)
cfg_webmessage_status_code = \
{
    'NEW': 'N',
    'READ': 'R',
    'REMINDER': 'M'
}

# separator used in every list of recipients
cfg_webmessage_separator = ','

# max length of a message
cfg_webmessage_max_size_of_message = 20000

# quota for messages for users (admins, see below)
cfg_webmessage_max_nb_of_messages = 30

# list of roles (find them in accROLE table) without quota
cfg_webmessage_roles_without_quota = ['superadmin']

cfg_webmessage_days_before_delete_orphans = 60
