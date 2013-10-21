## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""BibEdit Configuration."""

__revision__ = "$Id$"

from invenio.config import CFG_ETCDIR, CFG_TMPSHAREDDIR

import os

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

## CFG_BIBEDIT_JS_CLONED_RECORD_COLOR - Color of cloned record ID highlighting.
CFG_BIBEDIT_JS_CLONED_RECORD_COLOR = 'yellow'

## CFG_BIBEDIT_JS_CLONED_RECORD_COLOR_FADE_DURATION - Duration (in ms) for the
## fading of cloned record ID highlighting.
CFG_BIBEDIT_JS_CLONED_RECORD_COLOR_FADE_DURATION = 5000

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

## CFG_BIBEDIT_JS_NEW_CONTENT_HIGHLIGHT_DELAY - Duration (in ms) before
## highlighting newly modified content.
## WARNING: If set to low, the Jeditable plugin won't have time to update the
## cell with the new content (recommended: >50).
CFG_BIBEDIT_JS_NEW_CONTENT_HIGHLIGHT_DELAY = 50

## CFG_BIBEDIT_JS_NEW_FIELDS_COLOR - Color of new fields' highlighting
CFG_BIBEDIT_JS_NEW_CONTENT_COLOR = 'lightgreen'

## CFG_BIBEDIT_JS_NEW_FIELDS_COLOR_FADE_DURATION - Duration (in ms) for the
## fading of new fields' highlighting.
CFG_BIBEDIT_JS_NEW_CONTENT_COLOR_FADE_DURATION = 2000

## CFG_BIBEDIT_JS_TICKET_REFRESH_DELAY - Duration (in ms) before refreshing
## a record's tickets after the user clicks on the link to create a new one.
## WARNING: If set to low, the request for RT to generate the ticket won't have
## time to finish (recommended: >2000).
CFG_BIBEDIT_JS_TICKET_REFRESH_DELAY = 5000

## CFG_BIBEDIT_REQUESTS_UNTIL_SAVE - number of requests until changes in the
## editor will be saved
CFG_BIBEDIT_REQUESTS_UNTIL_SAVE = 3

## CFG_BIBEDIT_AJAX_RESULT_CODES - dictionary of result codes and messages used
## by the Ajax engine.

CFG_BIBEDIT_AJAX_RESULT_CODES_REV = {
#TODO: all the result codes should be accessible through the constants rather than
#      a direct number ! some parts of the bibedit_engine.py are not readable because
#      of using the numbers
#      The dictionary is convenient at this place because it can be imported with one command
#      unlike a number of constants
    'record_submitted': 4,
    'editor_modifications_changed': 33,
    'disabled_hp_changeset' : 34,
    'added_positioned_subfields' : 35,
    'autosuggestion_scanned' : 36,
    'error_rec_locked_by_user' : 104,
    'error_rec_locked_by_queue' : 105,
    'server_error' : 111,
    'error_physical_copies_exist': 112,
    'cache_updated_with_references': 114,
    'textmarc_parsing_error' : 115,
    'tableview_change_success' : 116,
    'error_no_doi_specified': 117,
    'error_crossref_record_not_found': 118,
    'error_crossref_malformed_doi': 119,
    'error_crossref_no_account' : 120,
    'ticket_closed' : 121,
    'error_ticket_closed': 122,
    'ticket_opened' : 123,
    'error_ticket_opened': 124,
    'error_rt_connection': 125
}

CFG_BIBEDIT_AJAX_RESULT_CODES = {
    0: '',
    1: 'Search completed',
    2: 'Tag format changed',
    3: 'Record loaded',
    4: 'Record submitted',
    5: 'Cancelled',
    6: 'Record created (new)',
    7: 'Record created (from template)',
    8: 'Record created (from existing)',
    9: 'Record cloned',
    10: 'Record deleted',
    11: 'Cache deleted',
    12: 'Record ready for merge',
    20: 'Added controlfield',
    21: 'Added field',
    22: 'Added subfield',
    23: 'Added subfields',
    24: 'Content modified',
    25: 'Subfield moved',
    26: 'Field deleted',
    27: 'Fields deleted',
    28: 'Subfield deleted',
    29: 'Subfields deleted',
    30: 'Selection deleted',
    31: 'Tickets retrieved',
    32: 'Field moved',
    33: 'Modifications updates',
    34: 'Disabled a changeset',
    35: 'Added fields/subfields',
    36: 'Autosuggestion scanned',
    100: 'Error: Not logged in',
    101: 'Error: Permission denied',
    102: 'Error: Non-existent record',
    103: 'Error: Deleted record',
    104: 'Error: Record locked by user',
    105: 'Error: Record locked by queue',
    106: 'Error: Cache file missing',
    107: 'Error: Cache file changed',
    108: 'Error: Template file missing',
    109: 'Error: Invalid template file',
    110: 'Error: Invalid content in record',
    111: 'Error: Wrong cache file format',
    112: 'Error: Physical copies of this record exist',
    113: 'Error: Upload simulation found some errors'
}

CFG_BIBEDIT_MSG = {
    "not_authorised" : "You are not authorised to submit a record into the given \
                        collection. Please, review the collection tags."
}
## CFG_BIBEDIT_MAX_SEARCH_RESULTS
CFG_BIBEDIT_MAX_SEARCH_RESULTS = 99

## CFG_BIBEDIT_TAG_FORMAT - default format to use when displaying MARC tags.
CFG_BIBEDIT_TAG_FORMAT = 'MARC'

## CFG_BIBEDIT_TO_MERGE_SUFFIX - default filename suffix for XML file to be
## merged. Filename will then be constructed like this:
## <CFG_BIBEDIT_FILENAME>_<RECID>_<UID>_<CFG_BIBEDIT_TO_MERGE_SUFFIX>.xml
CFG_BIBEDIT_TO_MERGE_SUFFIX = 'merge'

# CFG_BIBEDIT_RECORD_TEMPLATES_PATH - path to record template directory

CFG_BIBEDIT_RECORD_TEMPLATES_PATH = "%s%sbibedit%srecord_templates" % (CFG_ETCDIR, os.sep, os.sep)
CFG_BIBEDIT_FIELD_TEMPLATES_PATH = "%s%sbibedit%sfield_templates" % (CFG_ETCDIR, os.sep, os.sep)

# CFG_BIBEDIT_AUTOSUGGEST_TAGS - for which tags the editor should try to autosuggest values
# This is "safe" to have configured since it does not rely to a particular existing KB
CFG_BIBEDIT_AUTOSUGGEST_TAGS = ['100__a']

# CFG_BIBEDIT_AUTOCOMPLETE_TAGS_KBS - a dictionary whose keys are tags and values kb names
# This is better left empty when in doubt
CFG_BIBEDIT_AUTOCOMPLETE_TAGS_KBS = {} # { '65017a': 'SISC-65017a---65017a' }

# CFG_BIBEDIT_KEYWORD_TAXONOMY - the name of the taxonomy DB that holds the taxonomy file used
# for getting the keywords. Use only if you have a taxonomy KB.
CFG_BIBEDIT_KEYWORD_TAXONOMY = "" #'HEP.RDF'

#what tag is used for keywords
CFG_BIBEDIT_KEYWORD_TAG = "" # '6531_a'

#what label inside the RDF file contains the term
CFG_BIBEDIT_KEYWORD_RDFLABEL = "" #'prefLabel'

#where are BibEdit cache files stored
CFG_BIBEDIT_CACHEDIR = CFG_TMPSHAREDDIR + '/bibedit-cache'

# CFG_BIBEDIT_DOI_LOOKUP_FIELD - for which tag bibedit should add a link
# to a DOI name resolver
CFG_BIBEDIT_DOI_LOOKUP_FIELD = '0247_a'

# Name of User-Agent header that is send to the DOI name resolver page
# Without the User-Agent, dx.doi.org page returns 404 error
CFG_DOI_USER_AGENT = "Invenio"

# CFG_BIBEDIT_REFERENCE_TAGS - which tags to be considered when showing/hiding
# references
CFG_BIBEDIT_DISPLAY_REFERENCE_TAGS = ['999']

# CFG_BIBEDIT_AUTHOR_TAGS - which tags to be considered when showing/hiding
# authors
CFG_BIBEDIT_DISPLAY_AUTHOR_TAGS = ['100', '700']

# CFG_BIBEDIT_EXCLUDE_CURATOR_TAGS - which tags to be excluded in the
# curator view
CFG_BIBEDIT_EXCLUDE_CURATOR_TAGS = ['035', '041', '520', '540', '595', '650', '653', '690', '695', '856']

# CFG_BIBEDIT_AUTHOR_DISPLAY_THRESHOLD - if number of authors is higher than this number
# they will be hidden by default
CFG_BIBEDIT_AUTHOR_DISPLAY_THRESHOLD = 200
