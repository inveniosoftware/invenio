## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2010, 2011 CERN.
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

# pylint: disable=C0301

"""BibFormat BFX engine configuration."""

__revision__ = "$Id$"

import os
from invenio.config import CFG_ETCDIR

CFG_BIBFORMAT_BFX_TEMPLATES_PATH = "%s%sbibformat%sformat_templates" % (CFG_ETCDIR, os.sep, os.sep)

CFG_BIBFORMAT_BFX_FORMAT_TEMPLATE_EXTENSION = "bfx"

CFG_BIBFORMAT_BFX_ELEMENT_NAMESPACE = "http://invenio-software.org/"

CFG_BIBFORMAT_BFX_LABEL_DEFINITIONS = {
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
'first_author':              [r'/100__/a'],
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
'doc_status':                [r'/980__/c'],
'uri':                       [r'/8564_/u',
                              r'/8564_/q'],
'subject':                   [r'/65017/a'],
'keyword':                   [r'/6531_/a'],
'day':                       [],
'month':                     [],
'creation_date':             [],
'reference':                 []
}

# Exceptions: errors
class InvenioBibFormatBfxError(Exception):
    """A generic error for BibFormat_Bfx."""
    def __init__(self, message):
        """Initialisation."""
        self.message = message
    def __str__(self):
        """String representation."""
        return repr(self.message)

# Exceptions: warnings
class InvenioBibFormatBfxWarning(Exception):
    """A generic warning for BibFormat_Bfx."""
    def __init__(self, message):
        """Initialisation."""
        self.message = message
    def __str__(self):
        """String representation."""
        return repr(self.message)