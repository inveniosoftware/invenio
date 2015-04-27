# This file is part of Invenio.
# Copyright (C) 2010, 2011 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""OAI Harvest Configuration."""

from __future__ import unicode_literals

__revision__ = "$Id$"


# Exceptions: warnings
class InvenioOAIHarvestWarning(Exception):
    """A generic warning for OAIHarvest."""
    def __init__(self, message):
        """Initialisation."""
        self.message = message

    def __str__(self):
        """String representation."""
        return repr(self.message)


# CFG_OAI_POSSIBLE_POSTMODES -- list of possible modes available for
# OAI harvest post-processing along with possible arguments in a list of
# key => value mappings of argument-name, required, validation checks, etc.
CFG_OAI_POSSIBLE_POSTMODES = [
         ["c",
          "convert (c)",
          [{'name': 'stylesheet',
            'required': True,
            'validation': ["file"],
            'value': "",
            'input': "text"}]
         ],
         ["p",
          "extract plots (p)",
          [{'name': 'extraction-source',
            'required': True,
            'validation': None,
            'value': ["latex"],
            'input': "checkbox",
            'labels': ["LaTeX"],
            'states': [True]}]
         ],
         ["r",
          "extract references (r)",
          [{'name': 'format',
            'required': False,
            'validation': None,
            'value': "",
            'input': "text"},
           {'name': 'kb-journal-file',
            'required': False,
            'validation': ["file"],
            'value': "",
            'input': "text"},
           {'name': 'kb-rep-no-file',
            'required': False,
            'validation': ["file"],
            'value': "",
            'input': "text"}]
         ],
         ["a",
          "extract authors (a)",
          [{'name': 'rt-queue',
            'required': False,
            'validation': None,
            'value': "",
            'input': "text"},
           {'name': 'stylesheet',
            'required': True,
            'validation': ["file"],
            'value': "",
            'input': "text"}]
         ],
         ["t",
          "attach full-text (t)",
          [{'name': 'doctype',
            'required': False,
            'validation': None,
            'value': "Fulltext",
            'input': "text"}]
         ],
         ["f",
          "filter (f)",
          [{'name': 'filter-file',
            'required': True,
            'validation': ["file"],
            'value': "",
            'input': "text"}]
         ],
         ["u",
          "upload (u)",
          [{'name': 'priority',
            'required': False,
            'validation': ["int"],
            'value': "3",
            'input': "text"},
           {'name': 'name',
            'required': False,
            'validation': None,
            'value': "oai",
            'input': "text"}]
         ]]
