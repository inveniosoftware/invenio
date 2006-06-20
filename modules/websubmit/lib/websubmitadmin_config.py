from invenio.config import weburl

websubmitadmin_weburl = "%s/admin/websubmit/websubmitadmin.py" % (weburl,)


class InvenioWebSubmitAdminWarningDeleteFailed(Exception):
    pass

class InvenioWebSubmitAdminWarningInsertFailed(Exception):
    pass

class InvenioWebSubmitAdminWarningTooManyRows(Exception):
    pass

class InvenioWebSubmitAdminWarningNoRowsFound(Exception):
    pass

class InvenioWebSubmitAdminWarningForeignKeyViolation(Exception):
    pass




cfg_websubmitadmin_warning_messages =\
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
