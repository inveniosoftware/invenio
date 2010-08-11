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

"""WebSubmit Admin configuration parameters."""

__revision__ = \
    "$Id$"

# pylint: disable=C0301

from invenio.config import CFG_SITE_URL

WEBSUBMITADMINURL = "%s/admin/websubmit/websubmitadmin.py" % (CFG_SITE_URL,)
WEBSUBMITADMINURL_OLD = "%s/admin/websubmit" % (CFG_SITE_URL,)


class InvenioWebSubmitAdminWarningIOError(Exception):
    pass

class InvenioWebSubmitAdminWarningNoUpdate(Exception):
    """Exception used when a no update was made as a result of an action"""
    pass

class InvenioWebSubmitAdminWarningDeleteFailed(Exception):
    pass

class InvenioWebSubmitAdminWarningInsertFailed(Exception):
    pass

class InvenioWebSubmitAdminWarningTooManyRows(Exception):
    pass

class InvenioWebSubmitAdminWarningNoRowsFound(Exception):
    pass

class InvenioWebSubmitAdminWarningReferentialIntegrityViolation(Exception):
    pass


## List of the names of functions for which the parameters are files that can be edited.
## In particular, this applies to the record creation functions that make use of bibconvert.
FUNCTIONS_WITH_FILE_PARAMS = ["Make_Record", "Make_Modify_Record"]



CFG_WEBSUBMITADMIN_WARNING_MESSAGES = \
 {
     'WRN_WEBSUBMITADMIN_UNABLE_TO_DELETE_FIELD_FROM_SUBMISSION_PAGE' : '_("Unable to delete field at position %s from page %s of submission \'%s\'")',
     'WRN_WEBSUBMITADMIN_INVALID_FIELD_NUMBERS_SUPPLIED_WHEN_TRYING_TO_MOVE_FIELD_ON_SUBMISSION_PAGE' : \
                    '_("Unable to move field at position %s to position %s on page %s of submission \'%s\' - Invalid Field Position Numbers")',
     'WRN_WEBSUBMITADMIN_UNABLE_TO_SWAP_TWO_FIELDS_ON_SUBMISSION_PAGE_COULDNT_MOVE_FIELD1_TO_TEMP_POSITION' : \
     '_("Unable to swap field at position %s with field at position %s on page %s of submission %s - could not move field at position %s to temporary field location")',
     'WRN_WEBSUBMITADMIN_UNABLE_TO_SWAP_TWO_FIELDS_ON_SUBMISSION_PAGE_COULDNT_MOVE_FIELD2_TO_FIELD1_POSITION' : \
     '_("Unable to swap field at position %s with field at position %s on page %s of submission %s - could not move field at position %s to position %s. Please ask Admin to check that a field was not stranded in a temporary position")',
     'WRN_WEBSUBMITADMIN_UNABLE_TO_SWAP_TWO_FIELDS_ON_SUBMISSION_PAGE_COULDNT_MOVE_FIELD1_TO_POSITION_FIELD2_FROM_TEMPORARY_POSITION' : \
     '_("Unable to swap field at position %s with field at position %s on page %s of submission %s - could not move field that was located at position %s to position %s from temporary position. Field is now stranded in temporary position and must be corrected manually by an Admin")',
     'WRN_WEBSUBMITADMIN_UNABLE_TO_MOVE_FIELD_TO_NEW_POSITION_ON_SUBMISSION_PAGE_COULDNT_DECREMENT_POSITION_OF_FIELDS_BELOW_FIELD1' : \
     '_("Unable to move field at position %s to position %s on page %s of submission %s - could not decrement the position of the fields below position %s. Tried to recover - please check that field ordering is not broken")',
     'WRN_WEBSUBMITADMIN_UNABLE_TO_MOVE_FIELD_TO_NEW_POSITION_ON_SUBMISSION_PAGE_COULDNT_INCREMENT_POSITION_OF_FIELDS_AT_AND_BELOW_FIELD2' : \
     '_("Unable to move field at position %s to position %s on page %s of submission %s - could not increment the position of the fields at and below position %s. The field that was at position %s is now stranded in a temporary position.")',
     'WRN_WEBSUBMITADMIN_TOOMANYROWS' : '_("Too many rows found for query [%s]. Expected %s, found %s.")',
     'WRN_WEBSUBMITADMIN_NOROWSFOUND' : '_("No Rows found for query [%s].")',

     ## not warnings per-say, rather events that have taken place:
     'WRN_WEBSUBMITADMIN_DELETED_FIELD_FROM_SUBMISSION_PAGE'      : '_("Deleted field at position %s from page %s of submission \'%s\'")',
     'WRN_WEBSUBMITADMIN_MOVED_FIELD_ON_SUBMISSION_PAGE'          : '_("Moved field from position %s to position %s on page %s of submission \'%s\'")',
     'WRN_WEBSUBMITADMIN_FIELDUPDATED'                            : '_("Updated details of field at position %s on page %s of submission \'%s\'")'
 }
