## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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

"""OAI Harvest Configuration."""

__revision__ = "$Id$"

## CFG_OAI_POSSIBLE_POSTMODES -- list of possible modes available for
## OAI harvest post-processing
CFG_OAI_POSSIBLE_POSTMODES = [\
         ["c", "convert (c)"], \
         ["p", "extract plots (p)"], \
         ["r", "extract references (r)"], \
         ["a", "extract authors (a)"], \
         ["t", "attach full-text (t)"], \
         ["f", "filter (f)"], \
         ["u", "upload (u)"]]

# Exceptions: warnings
class InvenioOAIHarvestWarning(Exception):
    """A generic warning for OAIHarvest."""
    def __init__(self, message):
        """Initialisation."""
        self.message = message
    def __str__(self):
        """String representation."""
        return repr(self.message)
