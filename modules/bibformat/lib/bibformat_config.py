# -*- coding: utf-8 -*-
##
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

"""BibFormat configuration parameters."""

__revision__ = "$Id$"

import os
from invenio.config import CFG_ETCDIR, CFG_PYLIBDIR

# True if old php format written in EL must be used by Invenio.
# False if new python format must be used. If set to 'False' but
# new format cannot be found, old format will be used.
CFG_BIBFORMAT_USE_OLD_BIBFORMAT = False

# Paths to main formats directories
CFG_BIBFORMAT_TEMPLATES_PATH = "%s%sbibformat%sformat_templates" % (CFG_ETCDIR, os.sep, os.sep)
CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH = "invenio.bibformat_elements"
CFG_BIBFORMAT_ELEMENTS_PATH = "%s%sinvenio%sbibformat_elements" % (CFG_PYLIBDIR, os.sep, os.sep)
CFG_BIBFORMAT_OUTPUTS_PATH = "%s%sbibformat%soutput_formats" % (CFG_ETCDIR, os.sep, os.sep)

# File extensions of formats
CFG_BIBFORMAT_FORMAT_TEMPLATE_EXTENSION = "bft"
CFG_BIBFORMAT_FORMAT_OUTPUT_EXTENSION = "bfo"

# Exceptions: errors
class InvenioBibFormatError(Exception):
    """A generic error for BibFormat."""
    def __init__(self, message):
        """Initialisation."""
        self.message = message
    def __str__(self):
        """String representation."""
        return repr(self.message)

# Exceptions: warnings
class InvenioBibFormatWarning(Exception):
    """A generic warning for BibFormat."""
    def __init__(self, message):
        """Initialisation."""
        self.message = message
    def __str__(self):
        """String representation."""
        return repr(self.message)
