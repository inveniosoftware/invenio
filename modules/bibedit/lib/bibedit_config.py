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

"""BibEdit Configuration."""

__revision__ = "$Id$"


## CFG_BIBEDIT_FILENAME - default filename for BibEdit files.
CFG_BIBEDIT_FILENAME = "bibedit_record"

## The CFG_BIBEDIT_JS_* constants are passed on and used by the BibEdit
## Javascript engine.

## CFG_BIBEDIT_JS_HASH_CHECK_INTERVAL - interval (in ms) between checking if
## hash has changed.
CFG_BIBEDIT_JS_HASH_CHECK_INTERVAL = 250

## CFG_BIBEDIT_JS_CHECK_SCROLL_INTERVAL - interval (in ms) between menu
## repositioning.
CFG_BIBEDIT_JS_CHECK_SCROLL_INTERVAL = 250

## CFG_BIBEDIT_JS_STATUS_INFO_TIME - display status info messages for how long
## (in ms).
CFG_BIBEDIT_JS_STATUS_INFO_TIME = 1000

## CFG_BIBEDIT_JS_STATUS_ERROR_TIME - display status error messages for how long
## (in ms).
CFG_BIBEDIT_JS_STATUS_ERROR_TIME = 2000

## CFG_BIBEDIT_JS_NEW_ADD_FIELD_FORM_COLOR - Color of new field forms'
## highlighting.
CFG_BIBEDIT_JS_NEW_ADD_FIELD_FORM_COLOR = 'lightblue'

## CFG_BIBEDIT_JS_NEW_ADD_FIELD_FORM_COLOR_FADE_DURATION - Duration (in ms) for
## the fading of new field forms' highlighting.
CFG_BIBEDIT_JS_NEW_ADD_FIELD_FORM_COLOR_FADE_DURATION = 2000

## CFG_BIBEDIT_JS_NEW_FIELDS_COLOR - Color of new fields' highlighting
CFG_BIBEDIT_JS_NEW_FIELDS_COLOR = 'lightgreen'

## CFG_BIBEDIT_JS_NEW_FIELDS_COLOR_FADE_DURATION - Duration (in ms) for the
## fading of new fields' highlighting.
CFG_BIBEDIT_JS_NEW_FIELDS_COLOR_FADE_DURATION = 2000

## CFG_BIBEDIT_AJAX_RESULT_CODES - dictionary of result codes and messages used
## by the Ajax engine.
CFG_BIBEDIT_AJAX_RESULT_CODES = {
    0: '',
    1: 'Search completed',
    2: 'Tag format changed',
    3: 'Record loaded',
    4: 'Record submitted',
    5: 'Cancelled',
    6: 'Record deleted',
    7: 'Cache deleted',
    8: 'Record ready for merge',
    9: 'Added controlfield',
    10: 'Added field',
    11: 'Added subfield',
    12: 'Added subfields',
    13: 'Content modified',
    14: 'Subfield moved',
    15: 'Field deleted',
    16: 'Fields deleted',
    17: 'Subfield deleted',
    18: 'Subfields deleted',
    19: 'Selection deleted',
    100: 'Error: Not logged in',
    101: 'Error: Permission denied',
    102: 'Error: Non-existent record',
    103: 'Error: Deleted record',
    104: 'Error: Record locked by user',
    105: 'Error: Record locked by queue',
    106: 'Error: Cache file missing',
    107: 'Error: Cache file changed'
}

## CFG_BIBEDIT_MAX_SEARCH_RESULTS
CFG_BIBEDIT_MAX_SEARCH_RESULTS = 99

## CFG_BIBEDIT_TAG_FORMAT - default format to use when displaying MARC tags.
CFG_BIBEDIT_TAG_FORMAT = 'MARC'

## CFG_BIBEDIT_TO_MERGE_SUFFIX - default filename suffix for XML file to be
## merged. Filename will then be constructed like this:
## <CFG_BIBEDIT_FILENAME>_<RECID>_<UID>_<CFG_BIBEDIT_TO_MERGE_SUFFIX>.xml
CFG_BIBEDIT_TO_MERGE_SUFFIX = 'merge'
