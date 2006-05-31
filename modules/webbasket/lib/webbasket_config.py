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


cfg_webbasket_share_levels = {'READITM': 'RI',
                               'READCMT': 'RC',
                               'ADDCMT': 'AC',
                               'ADDITM': 'AI',
                               'DELCMT': 'DC',
                               'DELITM': 'DI',
                               'MANAGE': 'MA'
                               }
cfg_webbasket_share_levels_ordered = [cfg_webbasket_share_levels['READITM'],
                                      cfg_webbasket_share_levels['READCMT'],
                                      cfg_webbasket_share_levels['ADDCMT'],
                                      cfg_webbasket_share_levels['ADDITM'],
                                      cfg_webbasket_share_levels['DELCMT'],
                                      cfg_webbasket_share_levels['DELITM'],
                                      cfg_webbasket_share_levels['MANAGE']]
cfg_webbasket_categories = {'PRIVATE':  'P',
                            'GROUP':    'G',
                            'EXTERNAL': 'E'}
cfg_webbasket_actions = {'DELETE': 'delete',
                         'UP': 'moveup',
                         'DOWN': 'movedown',
                         'COPY': 'copy'}

cfg_webbasket_max_number_of_displayed_baskets = 20
cfg_webbasket_warning_messages = {
    'ERR_WEBBASKET_CMTID_INVALID': '_("%i is an invalid comment ID")',
    'WRN_WEBBASKET_NO_RECORD': '_("No records to add")'
}

cfg_webbasket_error_messages = {
    'ERR_WEBBASKET_CANNOT_COMMENT': '_("Sorry, you can\'t post in this baket")',
    'ERR_WEBBASKET_DB_ERROR': '_("Sorry there was an error with  the database")',
    'ERR_WEBBASKET_NO_RIGHTS': '_("Sorry, you don\'t have sufficient rights on this basket")',
    'ERR_WEBBASKET_UNDEFINED_ACTION': '_("Sorry, no such action exists")',
    'ERR_WEBBASKET_NOT_OWNER': '_("You are not owner of this basket")',
    'ERR_WEBBASKET_RESTRICTED_ACCESS': '_("This basket is not publicly accessible")'
}
