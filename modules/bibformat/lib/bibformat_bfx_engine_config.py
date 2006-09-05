## $Id$

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

import os
from invenio.config import etcdir

cfg_bibformat_bfx_templates_path = "%s%sbibformat%sformat_templates" % (etcdir, os.sep, os.sep)
cfg_bibformat_bfx_format_template_extension = "bfx"
cfg_bibformat_bfx_element_namespace = "http://cdsware.cern.ch/invenio/"
cfg_bibformat_bfx_label_definitions = {

#record is a reserved keyword, don't use it
#define one or more addresses for each name or zero if you plan to define them later
'controlfield':              [r'/???'],
'datafield':                 [r'/?????'],
'datafield.subfield':        [r'datafield/?'],
'recid':                     [r'/001'],
'article_id':                [],
'language':                  [r'/041__/a'],
'title':                     [r'/245__/a'],
'subtitle':                  [r'/245__/b'],
'secondary_title':           [r'/773__/p'],
'author':                    [r'/100__/a',
                              r'/700__/a'],
'author.surname':            [r'author#(?P<value>.*),[ ]*(.*)'],
'author.names':              [r'author#(.*),[ ]*(?P<value>.*)'],
'abstract':                  [r'/520__/a'],
'publisher':                 [r'/260__/b'],
'publisher_location':        [r'/260__/a'],
'issn':                      [r'/022__/a'],
'doi':                       [r'/773__/a'],
'journal_name_long':         [r'/222__/a',
                              r'/210__/a',
                              r'/773__/p',
                              r'/909C4/p'],
'journal_name_short':        [r'/210__/a',
                              r'/773__/p',
                              r'/909C4/p'],
'journal_name':              [r'/773__/p',
                              r'/909C4/p'],
'journal_volume':            [r'/773__/v',
                              r'/909C4/v'],
'journal_issue':             [r'/773__/n'],
'pages':                     [r'/773__/c',
                              r'/909C4/c'],
'first_page':                [r'/773__/c#(?P<value>\d*)-(\d*)',
                              r'/909C4/c#(?P<value>\d*)-(\d*)'],
'last_page':                 [r'/773__/c#(\d*)-(?P<value>\d*)',
                              r'/909C4/c#(\d*)-(?P<value>\d*)'],
'date':                      [r'/260__/c'],
'year':                      [r'/773__/y#(.*)(?P<value>\d\d\d\d).*',
                              r'/260__/c#(.*)(?P<value>\d\d\d\d).*',
                              r'/925__/a#(.*)(?P<value>\d\d\d\d).*',
                              r'/909C4/y'],
'doc_type':                  [r'/980__/a'],
'uri':                       [r'/8564_/u',
                              r'/8564_/q'],
'subject':                   [r'/65017/a'],
'keyword':                   [r'/6531_/a'],
'day':                       [],
'month':                     [],
'creation_date':             [],
'reference':                 []
}


#BFX error and warning messages
cfg_bibformat_bfx_error_messages = \
{
    'ERR_BFX_TEMPLATE_REF_NO_NAME'                   :  'Missing attribute "name" in TEMPLATE_REF.',
    'ERR_BFX_TEMPLATE_NOT_FOUND'                     :  'Template %s not found.',
    'ERR_BFX_ELEMENT_NO_NAME'                        :  'Missing attribute "name" in ELEMENT.',
    'ERR_BFX_FIELD_NO_NAME'                          :  'Missing attribute "name" in FIELD.',
    'ERR_BFX_LOOP_NO_OBJECT'                         :  'Missing attribute "object" in LOOP.',
    'ERR_BFX_NO_SUCH_FIELD'                          :  'Field %s is not defined',
    'ERR_BFX_IF_NO_NAME'                             :  'Missing attrbute "name" in IF.',
    'ERR_BFX_TEXT_NO_VALUE'                          :  'Missing attribute "value" in TEXT.',
    'ERR_BFX_INVALID_RE'                             :  'Invalid regular expression: %s',
    'ERR_BFX_INVALID_OPERATOR_NAME'                  :  'Name %s is not recognised as a valid operator name.',
    'ERR_BFX_INVALID_DISPLAY_TYPE'                   :  'Invalid display type. Must be one of: value, tag, ind1, ind2, code; received: %s',
    'ERR_BFX_IF_WRONG_SYNTAX'                        :  'Invalid syntax of IF statement.'
}

cfg_bibformat_bfx_warning_messages = \
{
    'WRN_BFX_TEMPLATE_NO_NAME'          : 'No name defined for the template.',
    'WRN_BFX_TEMPLATE_NO_DESCRIPTION'   : 'No description entered for the template.',
    'WRN_BFX_TEMPLATE_NO_CONTENT'       : 'No content type specified for the template. Using default: text/xml.'
}
