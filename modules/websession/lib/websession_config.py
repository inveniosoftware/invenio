# -*- coding: utf-8 -*-
## $Id$
## 
## Every db-related function of module webmessage
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


cfg_websession_group_join_policy = {'VISIBLEOPEN': 'VO',
                               'VISIBLEMAIL': 'VM',
                               'INVISIBLEOPEN': 'IO',
                               'INVISIBLEMAIL': 'IM'  
                                    }
cfg_websession_usergroup_status = {'ADMIN':  'A',
                                   'MEMBER':'M',
                                   'PENDING':'P'
                                   }

cfg_websession_error_messages = {
    'ERR_WEBSESSION_DB_ERROR': '_("Sorry there was an error with  the database")',
    'ERR_WEBSESSION_GROUP_NO_RIGHTS': '_("Sorry, You don\'t have sufficient rights on this group")'
}

cfg_websession_warning_messages = {
    'WRN_WEBSESSION_DB_ERROR': '_("warning not used ")'
}
cfg_websession_info_messages = {1:'You have successfully created a new group.',
                                2:'You have successfully joined a new group.',
                                3:'You have successfully updated a group.',
                                4:'You have successfully deleted a group.',
                                5:'You have successfully deleted a member.',
                                6:'You have successfully added a new member.',
                                7:'The group administrator has been notified of your request.',
                                8:'You have successfully left a group.'
                               
}

