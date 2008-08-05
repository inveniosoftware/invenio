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

# pylint: disable-msg=C0301

"""WebComment configuration parameters."""

__revision__ = "$Id$"

CFG_WEBCOMMENT_ERROR_MESSAGES = \
{   'ERR_WEBCOMMENT_RECID_INVALID'       :  '_("%s is an invalid record ID")',
    'ERR_WEBCOMMENT_RECID_NAN'           :  '_("Record ID %s is not a number")',
    'ERR_WEBCOMMENT_UID_INVALID'         :  '_("%s is an invalid user ID")',
    'ERR_WEBCOMMENT_DB_ERROR'            :  '%s',
    'ERR_WEBCOMMENT_COMMENTS_NOT_ALLOWED':  '_("Comments on records have been disallowed by the administrator")',
    'ERR_WEBCOMMENT_ARGUMENT_NAN'        :  '_("%s is not a number")',
    'ERR_WEBCOMMENT_ARGUMENT_INVALID'   :  '_("%s invalid argument")',
    'ERR_WEBCOMMENT_PROGRAMMING_ERROR'   :  '_("Programming error, please inform the administrator")',
    'ERR_WEBCOMMENT_FOR_TESTING_PURPOSES':  ' THIS IS FOR TESTING PURPOSES ONLY var1=%s var2=%s var3=%s var4=%s var5=%s var6=%s ',
    'ERR_WEBCOMMENT_REPLY_REVIEW'        :  '_("Cannot reply to a review")',
    'ERR_WEBCOMMENT_DB_INSERT_ERROR' : '_("Failed to insert your comment to the database. Please try again.")'
}

CFG_WEBCOMMENT_WARNING_MESSAGES = \
{   'WRN_WEBCOMMENT_INVALID_PAGE_NB': '_("Bad page number --> showing first page")',
    'WRN_WEBCOMMENT_INVALID_NB_RESULTS_PER_PAGE': '_("Bad number of results per page --> showing 10 results per page")',
    'WRN_WEBCOMMENT_INVALID_REVIEW_DISPLAY_ORDER': '_("Bad display order --> showing most helpful first")',
    'WRN_WEBCOMMENT_INVALID_DISPLAY_ORDER': '_("Bad display order --> showing oldest first")',
    'WRN_WEBCOMMENT_FEEDBACK_RECORDED': '_("Your feedback has been recorded, many thanks")',
    'WRN_WEBCOMMENT_FEEDBACK_NOT_RECORDED': '_("Your feedback could not be recorded, please try again")',
    'WRN_WEBCOMMENT_ALREADY_VOTED': '_("Sorry, you have already voted. This vote hasn\'t been recorded.")',
    'WRN_WEBCOMMENT_ALREADY_REPORTED': '_("You have already reported an abuse for this comment.")',
    'WRN_WEBCOMMENT_ADD_NO_TITLE': '_("You must enter a title")',
    'WRN_WEBCOMMENT_ADD_NO_SCORE': '_("You must choose a score")',
    'WRN_WEBCOMMENT_ADD_NO_BODY': '_("You must enter a text")',
    'WRN_WEBCOMMENT_ADD_UNKNOWN_ACTION': '_("Unknown action --> showing you the default add comment form")',
    'WRN_WEBCOMMENT_ADMIN_COMID_NAN': '_("comment ID must be a number")',
    'WRN_WEBCOMMENT_ADMIN_INVALID_COMID': '_("Invalid comment ID")',
    'WRN_WEBCOMMENT_ADMIN_COMID_INEXISTANT': '_("Comment ID %s does not exist")',
    'WRN_WEBCOMMENT_ADMIN_RECID_INEXISTANT': '_("Record ID %s does not exist")',
    'ERR_WEBCOMMENT_RECID_MISSING': '_("No record ID was given")',
    'ERR_WEBCOMMENT_RECID_INEXISTANT': '_("Record ID %s does not exist in the database")',
    'ERR_WEBCOMMENT_RECID_INVALID': '_("Record ID %s is an invalid ID")',
    'ERR_WEBCOMMENT_RECID_NAN': '_("Record ID %s is not a number")',
    'WRN_WEBCOMMENT_TIMELIMIT': '_("You already posted a comment short ago. Please retry later")',
    'WRN_WEBCOMMENT_CANNOT_REVIEW_TWICE': '_("You already wrote a review for this record.")'
}

CFG_WEBCOMMENT_ACTION_CODE = {
    'ADD_COMMENT': 'C',
    'ADD_REVIEW': 'R',
    'VOTE': 'V',
    'REPORT_ABUSE': 'A'
}
