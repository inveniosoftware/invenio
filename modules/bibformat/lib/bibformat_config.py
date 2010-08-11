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

# pylint: disable=C0301

"""BibFormat configuration parameters."""

__revision__ = "$Id$"

import os
from invenio.config import CFG_ETCDIR, CFG_PYLIBDIR

#True if old php format written in EL must be used by Invenio.
#False if new python format must be used. If set to 'False' but
#new format cannot be found, old format will be used.
CFG_BIBFORMAT_USE_OLD_BIBFORMAT = False

#Enable internationalization of brief format (HB). When set to 'True',
#BibFormat will try to display each record of the search results list
#in the language chosen by the user. This currently means that the
#formatting of each record will be done on-the-fly for each language
#different from CFG_SITE_LANG, as bibreformat precreates formatted
#output in this language only. If set to 'False', the cache created by
#bibreformat will be used independently of the language chosen by the
#user. You might want to set this setting to True if your users comes
#from various language zones and if you provide language-dependant
#content in the brief format. Also consider the impact on the
#performance of your server to have on-the-fly formatting enabled.
CFG_BIBFORMAT_ENABLE_I18N_BRIEF_FORMAT = True

#Paths to main formats directories
CFG_BIBFORMAT_TEMPLATES_PATH = "%s%sbibformat%sformat_templates" % (CFG_ETCDIR, os.sep, os.sep)
CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH = "invenio.bibformat_elements"
CFG_BIBFORMAT_ELEMENTS_PATH = "%s%sinvenio%sbibformat_elements" % (CFG_PYLIBDIR, os.sep, os.sep)
CFG_BIBFORMAT_OUTPUTS_PATH = "%s%sbibformat%soutput_formats" % (CFG_ETCDIR, os.sep, os.sep)

#File extensions of formats
CFG_BIBFORMAT_FORMAT_TEMPLATE_EXTENSION = "bft"
CFG_BIBFORMAT_FORMAT_OUTPUT_EXTENSION = "bfo"

CFG_BIBFORMAT_ERROR_MESSAGES = \
{   'ERR_BIBFORMAT_INVALID_TAG'                   :  '%s is an invalid tag.',
    'ERR_BIBFORMAT_NO_TEMPLATE_FOUND'             :  'No template could be found for output format %s.',
    'ERR_BIBFORMAT_CANNOT_RESOLVE_ELEMENT_NAME'   :  'Could not find format element named %s.',
    'ERR_BIBFORMAT_CANNOT_RESOLVE_OUTPUT_NAME'    :  'Could not find output format named %s.',
    'ERR_BIBFORMAT_CANNOT_RESOLVE_TEMPLATE_FILE'  :  'Could not find format template named %s.',
    'ERR_BIBFORMAT_FORMAT_ELEMENT_NOT_FOUND'      :  'Format element %s could not be found.',
    'ERR_BIBFORMAT_BAD_BFO_RECORD'                :  'Could not initialize new BibFormatObject with record id %s.',
    'ERR_BIBFORMAT_NB_OUTPUTS_LIMIT_REACHED'      :  'Could not find a fresh name for output format %s.',
    'ERR_BIBFORMAT_KB_ID_UNKNOWN'                 :  'Knowledge base with id %s is unknown.',
    'ERR_BIBFORMAT_OUTPUT_FORMAT_CODE_UNKNOWN'    :  'Output format with code %s could not be found.',
    'ERR_BIBFORMAT_CANNOT_READ_TEMPLATE_FILE'     :  'Format template %s cannot not be read. %s',
    'ERR_BIBFORMAT_CANNOT_WRITE_TEMPLATE_FILE'    :  'BibFormat could not write to format template %s. %s',
    'ERR_BIBFORMAT_CANNOT_READ_OUTPUT_FILE'       :  'Output format %s cannot not be read. %s',
    'ERR_BIBFORMAT_CANNOT_WRITE_OUTPUT_FILE'      :  'BibFormat could not write to output format %s. %s',
    'ERR_BIBFORMAT_EVALUATING_ELEMENT'            :  'Error when evaluating format element %s with parameters %s',
    'ERR_BIBFORMAT_CANNOT_READ_ELEMENT_FILE'      :  'Format element %s cannot not be read. %s',
    'ERR_BIBFORMAT_INVALID_OUTPUT_RULE_FIELD'     :  'Should be "tag field_number:" at line %s.',
    'ERR_BIBFORMAT_INVALID_OUTPUT_RULE_FIELD_TAG' :  'Invalid tag "%s" at line %s.',
    'ERR_BIBFORMAT_OUTPUT_CONDITION_OUTSIDE_FIELD':  'Condition "%s" is outside a tag specification at line %s.',
    'ERR_BIBFORMAT_INVALID_OUTPUT_CONDITION'      :  'Condition "%s" can only have a single separator --- at line %s.',
    'ERR_BIBFORMAT_WRONG_OUTPUT_RULE_TEMPLATE_REF':  'Template "%s" does not exist at line %s.',
    'ERR_BIBFORMAT_WRONG_OUTPUT_LINE'             :  'Line %s could not be understood at line %s.',
    'ERR_BIBFORMAT_OUTPUT_WRONG_TAG_CASE'         :  '"tag" must be lowercase in "%s" at line %s.',
    'ERR_BIBFORMAT_OUTPUT_RULE_FIELD_COL'         :  'Tag specification "%s" must end with column ":" at line %s.',
    'ERR_BIBFORMAT_OUTPUT_TAG_MISSING'            :  'Tag specification "%s" must start with "tag" at line %s.',
    'ERR_BIBFORMAT_OUTPUT_WRONG_DEFAULT_CASE'     :  '"default" keyword must be lowercase in "%s" at line %s',
    'ERR_BIBFORMAT_OUTPUT_RULE_DEFAULT_COL'       :  'Missing column ":" after "default" in "%s" at line %s.',
    'ERR_BIBFORMAT_OUTPUT_DEFAULT_MISSING'        :  'Default template specification "%s" must start with "default :" at line %s.',
    'ERR_BIBFORMAT_FORMAT_ELEMENT_FORMAT_FUNCTION':  'Format element %s has no function named "format".',
    'ERR_BIBFORMAT_VALIDATE_NO_FORMAT'            :  'No format specified for validation. Please specify one.',
    'ERR_BIBFORMAT_TEMPLATE_HAS_NO_NAME'          :  'Could not find a name specified in tag "<name>" inside format template %s.',
    'ERR_BIBFORMAT_TEMPLATE_HAS_NO_DESCRIPTION'   :  'Could not find a description specified in tag "<description>" inside format template %s.',
    'ERR_BIBFORMAT_TEMPLATE_CALLS_UNREADABLE_ELEM':  'Format template %s calls unreadable element "%s". Check element file permissions.',
    'ERR_BIBFORMAT_TEMPLATE_CALLS_UNLOADABLE_ELEM':  'Cannot load element "%s" in template %s. Check element code.',
    'ERR_BIBFORMAT_TEMPLATE_CALLS_UNDEFINED_ELEM' :  'Format template %s calls undefined element "%s".',
    'ERR_BIBFORMAT_TEMPLATE_WRONG_ELEM_ARG'       :  'Format element %s uses unknown parameter "%s" in format template %s.',
    'ERR_BIBFORMAT_IN_FORMAT_ELEMENT'             :  'Error in format element %s. %s',
    'ERR_BIBFORMAT_NO_RECORD_FOUND_FOR_PATTERN'   :  'No Record Found for %s.',
    'ERR_BIBFORMAT_NBMAX_NOT_INT'                 :  '"nbMax" parameter for %s must be an "int".',
    'ERR_BIBFORMAT_EVALUATING_ELEMENT_ESCAPE'     :  'Escape mode for format element %s could not be retrieved. Using default mode instead.'
}

CFG_BIBFORMAT_WARNING_MESSAGES = \
{   'WRN_BIBFORMAT_OUTPUT_FORMAT_NAME_TOO_LONG'   : 'Name %s is too long for output format %s in language %s. Truncated to first 256 characters.',
    'WRN_BIBFORMAT_KB_NAME_UNKNOWN'               : 'Cannot find knowledge base named %s.',
    'WRN_BIBFORMAT_KB_MAPPING_UNKNOWN'            : 'Cannot find a mapping with key %s in knowledge base %s.',
    'WRN_BIBFORMAT_CANNOT_WRITE_IN_ETC_BIBFORMAT' : 'Cannot write in etc/bibformat dir of your Invenio installation. Check directory permission.',
    'WRN_BIBFORMAT_CANNOT_WRITE_MIGRATION_STATUS' : 'Cannot write file migration_status.txt in etc/bibformat dir of your Invenio installation. Check file permission.',
    'WRN_BIBFORMAT_CANNOT_EXECUTE_REQUEST'        : 'Your request could not be executed.'
}

