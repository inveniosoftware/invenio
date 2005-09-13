# -*- coding: utf-8 -*-
## $Id$
## Comments and reviews for records.
                                                                                                                                                                                                     
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
                                                                                                                                                                                                     
__lastupdated__ = """FIXME: last updated"""

from config import  *

cfg_webcomment_error_messages = \
{   'ERR_WEBCOMMENT_RECID_INVALID'       :  ' %s is an invalid record ID ',
    'ERR_WEBCOMMENT_RECID_NAN'           :  ' Record ID %s is not a number ',
    'ERR_WEBCOMMENT_UID_INVALID'         :  ' %s is an invalid user ID ',
    'ERR_WEBCOMMENT_DB_ERROR'            :  ' %s ',
    'ERR_WEBCOMMENT_COMMENTS_NOT_ALLOWED':  ' Comments on library record have been disallowed by the Administrator ',
    'ERR_WEBCOMMENT_ARGUMENT_NAN'        :  ' %s is not a number ',
    'ERR_WEBCOMMENT_ARGUEMENT_INVALID'   :  ' %s invalid argument ',
    'ERR_WEBCOMMENT_PROGRAMMING_ERROR'   :  ' Programming error, please inform the Administrator ',
    'ERR_WEBCOMMENT_FOR_TESTING_PURPOSES':  ' THIS IS FOR TESTING PURPOSES ONLY var1=%s var2=%s var3=%s var4=%s var5=%s var6=%s ',
    'ERR_WEBCOMMENT_REPLY_REVIEW'        :  ' Cannot reply to a review '
}

cfg_webcomment_warning_messages = \
{   'WRN_WEBCOMMENT_INVALID_PAGE_NB'                : "Bad page number --> showing first page",
    'WRN_WEBCOMMENT_INVALID_NB_RESULTS_PER_PAGE'    : "Bad number of results per page --> showing 10 results per page",
    'WRN_WEBCOMMENT_INVALID_REVIEW_DISPLAY_ORDER'   : "Bad display order --> showing most helpful first",
    'WRN_WEBCOMMENT_INVALID_DISPLAY_ORDER'          : "Bad display order --> showing oldest first",
    'WRN_WEBCOMMENT_FEEDBACK_RECORDED_GREEN_TEXT'   : "Your feedback has been recorded, many thanks",
    'WRN_WEBCOMMENT_FEEDBACK_NOT_RECORDED_RED_TEXT' : "Your feedback could not be recorded, please try again",
    'WRN_WEBCOMMENT_ADD_NO_TITLE'                   : "You must enter a title",
    'WRN_WEBCOMMENT_ADD_NO_SCORE'                   : "You must choose a score",
    'WRN_WEBCOMMENT_ADD_NO_BODY'                    : "You must enter a text",
    'ERR_WEBCOMMENT_DB_INSERT_ERROR'                : 'Failed to insert your comment to the database. Please try again.',
    'WRN_WEBCOMMENT_ADD_UNKNOWN_ACTION'             : 'Unknown action --> showing you the default add comment form',
    'WRN_WEBCOMMENT_ADMIN_COMID_NAN'                : 'comment ID must be a number, try again',
    'WRN_WEBCOMMENT_ADMIN_INVALID_COMID'            : 'Invalid comment ID, try again',
    'WRN_WEBCOMMENT_ADMIN_COMID_INEXISTANT'         : "Comment ID %s does not exist, try again",

}


