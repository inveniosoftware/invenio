# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

"""WebBasket configuration parameters."""

__revision__ = "$Id$"

CFG_WEBBASKET_SHARE_LEVELS = {'READITM': 'RI',
                              'READCMT': 'RC',
                              'ADDCMT': 'AC',
                              'ADDITM': 'AI',
                              'DELCMT': 'DC',
                              'DELITM': 'DI',
                              'MANAGE': 'MA'
                              }

CFG_WEBBASKET_SHARE_LEVELS_ORDERED = [CFG_WEBBASKET_SHARE_LEVELS['READITM'],
                                      CFG_WEBBASKET_SHARE_LEVELS['READCMT'],
                                      CFG_WEBBASKET_SHARE_LEVELS['ADDCMT'],
                                      CFG_WEBBASKET_SHARE_LEVELS['ADDITM'],
                                      CFG_WEBBASKET_SHARE_LEVELS['DELCMT'],
                                      CFG_WEBBASKET_SHARE_LEVELS['DELITM'],
                                      CFG_WEBBASKET_SHARE_LEVELS['MANAGE']]

CFG_WEBBASKET_CATEGORIES = {'PRIVATE':  'P',
                            'GROUP':    'G',
                            'EXTERNAL': 'E'}

CFG_WEBBASKET_ACTIONS = {'DELETE': 'delete',
                         'UP': 'moveup',
                         'DOWN': 'movedown',
                         'COPY': 'copy'}


CFG_WEBBASKET_WARNING_MESSAGES = {
    'ERR_WEBBASKET_CMTID_INVALID': '_("%i is an invalid comment ID")',
    'WRN_WEBBASKET_NO_RECORD': '_("No records to add")',
    'WRN_WEBBASKET_NO_GIVEN_TOPIC':
            '_("Please select an existing topic or create a new one")',
    'WRN_WEBBASKET_NO_BASKET_SELECTED':  '_("No basket has been selected")',
    'WRN_WEBBASKET_NO_RIGHTS_TO_ADD_THIS_RECORD':  '_("Sorry, you don\'t have sufficient rights to add record #%i")'
}

# pylint: disable-msg=C0301
CFG_WEBBASKET_ERROR_MESSAGES = {
    'ERR_WEBBASKET_CANNOT_COMMENT': '_("Sorry, you can\'t post in this baket")',
    'ERR_WEBBASKET_DB_ERROR': '_("Sorry there was an error with  the database")',
    'ERR_WEBBASKET_NO_RIGHTS': '_("Sorry, you don\'t have sufficient rights on this basket")',
    'ERR_WEBBASKET_UNDEFINED_ACTION': '_("Sorry, no such action exists")',
    'ERR_WEBBASKET_NOT_OWNER': '_("You are not owner of this basket")',
    'ERR_WEBBASKET_RESTRICTED_ACCESS': '_("This basket is not publicly accessible")'
}
