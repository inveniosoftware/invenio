# -*- coding: utf-8 -*-
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
                              'MANAGE': 'MA'}

CFG_WEBBASKET_SHARE_LEVELS_ORDERED = [CFG_WEBBASKET_SHARE_LEVELS['READITM'],
                                      CFG_WEBBASKET_SHARE_LEVELS['READCMT'],
                                      CFG_WEBBASKET_SHARE_LEVELS['ADDCMT'],
                                      CFG_WEBBASKET_SHARE_LEVELS['ADDITM'],
                                      CFG_WEBBASKET_SHARE_LEVELS['DELCMT'],
                                      CFG_WEBBASKET_SHARE_LEVELS['DELITM'],
                                      CFG_WEBBASKET_SHARE_LEVELS['MANAGE']]

CFG_WEBBASKET_CATEGORIES = {'PRIVATE':      'P',
                            'GROUP':        'G',
                            'EXTERNAL':     'E',
                            'ALLPUBLIC':    'A'}

CFG_WEBBASKET_ACTIONS = {'DELETE':  'delete',
                         'UP':      'moveup',
                         'DOWN':    'movedown',
                         'COPY':    'copy'}

# Specify how many levels of indentation discussions can be.  This can
# be used to ensure that discussions will not go into deep levels of
# nesting if users don't understand the difference between "reply to
# comment" and "add comment". When the depth is reached, any "reply to
# comment" is conceptually converted to a "reply to thread"
# (i.e. reply to this parent's comment). Use -1 for no limit, 0 for
# unthreaded (flat) discussions.
CFG_WEBBASKET_MAX_COMMENT_THREAD_DEPTH = 1

CFG_WEBBASKET_WARNING_MESSAGES = {
    'ERR_WEBBASKET_CMTID_INVALID': '_("%i is an invalid comment ID")',
    'WRN_WEBBASKET_NO_RECORD': '_("No records to add")',
    'WRN_WEBBASKET_NO_GIVEN_TOPIC': '_("Please select an existing topic or create a new one")',
    'WRN_WEBBASKET_NO_BASKET_SELECTED':  '_("No basket has been selected")',
    'WRN_WEBBASKET_NO_RIGHTS_TO_ADD_THIS_RECORD':  '_("Sorry, you don\'t have sufficient rights to add record #%i")',
    'WRN_WEBBASKET_NO_RIGHTS_TO_ADD_RECORDS':  '_("Some of the items were not added due to lack of sufficient rights")',
    'WRN_WEBBASKET_NO_EXTERNAL_SOURCE_TITLE': '_("Please provide a title for the external source")',
    'WRN_WEBBASKET_NO_EXTERNAL_SOURCE_DESCRIPTION': '_("Please provide a description for the external source")',
    'WRN_WEBBASKET_NO_EXTERNAL_SOURCE_URL': '_("Please provide a url for the external source")',
    'WRN_WEBBASKET_NO_VALID_URL_0': '_("The url you have provided is not valid")',
    'WRN_WEBBASKET_NO_VALID_URL_3': '_("The url you have provided is not valid: There was some kind of redirection")',
    'WRN_WEBBASKET_NO_VALID_URL_4': '_("The url you have provided is not valid: The request contains bad syntax or cannot be fulfilled")',
    'WRN_WEBBASKET_NO_VALID_URL_5': '_("The url you have provided is not valid: The server failed to fulfil an apparently valid request")',
    'WRN_WEBBASKET_DEFAULT_TOPIC_AND_BASKET': '_("A default topic and basket have been automatically created. Edit them to rename them as you see fit.")',
    'WRN_WEBBASKET_NO_CATEGORY': '_("You have not selected any category. The Personal baskets category has been selected by default.")',
    'WRN_WEBBASKET_INVALID_CATEGORY': '_("The category you have selected does not exist. Please select a valid category.")',
    'WRN_WEBBASKET_CANNOT_COMMENT': '_("Sorry, you can\'t post in this baket")',
    'WRN_WEBBASKET_NO_RIGHTS': '_("Sorry, you don\'t have sufficient rights on this basket")',
    'WRN_WEBBASKET_UNDEFINED_ACTION': '_("Sorry, no such action exists")',
    'WRN_WEBBASKET_NOT_OWNER': '_("You are not owner of this basket")',
    'WRN_WEBBASKET_RESTRICTED_ACCESS': '_("This basket is not publicly accessible")',
    'WRN_WEBBASKET_NO_SEARCH_PATTERN': '_("Please enter a string to search for.")',
    'WRN_WEBBASKET_INVALID_OR_RESTRICTED_TOPIC': '_("The selected topic does not exist or you do not have access to it.")',
    'WRN_WEBBASKET_INVALID_OR_RESTRICTED_GROUP': '_("The selected group does not exist or you do not have access to it.")',
    'WRN_WEBBASKET_INVALID_OR_RESTRICTED_BASKET': '_("The selected basket does not exist or you do not have access to it.")',
    'WRN_WEBBASKET_INVALID_OR_RESTRICTED_PUBLIC_BASKET': '_("The selected public basket does not exist or you do not have access to it.")',
    'WRN_WEBBASKET_INVALID_OR_RESTRICTED_ITEM': '_("The selected item does not exist or you do not have access to it.")',
    'WRN_WEBBASKET_FORMER_PUBLIC_BASKET': '_("The selected basket is no longer public.")',
    'WRN_WEBBASKET_INVALID_OR_RESTRICTED_ITEM': '_("The selected item does not exist or you do not have access to it.")',
    'WRN_WEBBASKET_RESTRICTED_WRITE_NOTES': '_("You do not have permission to write notes to this item.")',
    'WRN_WEBBASKET_RESTRICTED_DELETE_NOTES': '_("You do not have permission to delete this note.")',
    'WRN_WEBBASKET_INCOMPLETE_NOTE': '_("You must fill in both the subject and the body of the note.")',
    'WRN_WEBBASKET_QUOTE_INVALID_NOTE': '_("The note you are quoting does not exist or you do not have access to it.")',
    'WRN_WEBBASKET_DELETE_INVALID_NOTE': '_("The note you are deleting does not exist or you do not have access to it.")',
    'WRN_WEBBASKET_RETURN_TO_PUBLIC_BASKET': '_("Returning to the public basket view.")',
    'WRN_WEBBASKET_SHOW_LIST_PUBLIC_BASKETS': '_("Please select a valid public basket from the list of public baskets.")',
    'WRN_WEBBASKET_INVALID_ADD_TO_PARAMETERS': '_("Cannot add items to the selected basket. Invalid parameters.")',
    'WRN_WEBBASKET_CAN_NOT_SUBSCRIBE': '_("You cannot subscribe to this basket, you are the either owner or you have already subscribed.")',
    'WRN_WEBBASKET_CAN_NOT_UNSUBSCRIBE': '_("You cannot unsubscribe from this basket, you are the either owner or you have already unsubscribed.")',
    'WRN_WEBBASKET_INVALID_OUTPUT_FORMAT': '_("The selected output format is not available or is invalid.")',
    }

# pylint: disable-msg=C0301
CFG_WEBBASKET_ERROR_MESSAGES = {
    'ERR_WEBBASKET_DB_ERROR': '_("There was an error with the database")',
    }

CFG_WEBBASKET_DIRECTORY_BOX_NUMBER_OF_COLUMNS = 3

CFG_WEBBASKET_MAX_NUMBER_OF_NOTES = 100
