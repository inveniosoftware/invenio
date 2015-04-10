# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013 CERN.
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

from __future__ import unicode_literals

import re

EMPTY                       = re.compile('^\s*$')
UNDEFINED                   = 'UNDEFINED'


class Resources:
    SCRIPTS                 = ['jquery.min.js',
                               'jquery-ui.min.js',
                               'jquery.dataTables.min.js',
                               'jquery.dataTables.ColVis.min.js',
                               'authorlist.js',
                               'authorlist.spreadSheet.js',
                               'authorlist.select.js']

    STYLESHEETS             = ['authorlist.css',
                               'authorlist.dataTable.css',
                               'authorlist.dataTable.jquery-ui.css',
                               'authorlist.jquery-ui.custom.css',
                               'authorlist.colVis.css',
                               'authorlist.spreadSheet.css']


class JSON:
    AFFILIATIONS_KEY        = 'affiliations'
    AUTHORS_KEY             = 'authors'
    COLLABORATION           = 'collaboration'
    EXPERIMENT_NUMBER       = 'experiment_number'
    PAPER_ID                = 'paper_id'
    LAST_MODIFIED           = 'last_modified'
    PAPER_TITLE             = 'paper_title'
    REFERENCE_IDS           = 'reference_ids'

    # Author table indices
    INDEX                   = 0
    EDIT                    = 1
    FAMILY_NAME             = 2
    GIVEN_NAME              = 3
    PAPER_NAME              = 4
    STATUS                  = 5
    AFFILIATIONS            = 6
    IDENTIFIERS             = 7

    # Affiliation indices in author table
    AFFILIATION_ACRONYM     = 0
    AFFILIATION_STATUS      = 1

    # Identifiers indices in author table
    IDENTIFIER_NUMBER      = 0
    IDENTIFIER_NAME        = 1

    # Affiliation table indices
    ACRONYM                = 2
    UMBRELLA               = 3
    NAME                   = 4
    DOMAIN                 = 5
    MEMBER                 = 6
    SPIRES_ID              = 7


class AuthorsXML:
    COLLABORATION_ID       = 'c1'
    DECEASED               = 'Deceased'
    MEMBER                 = 'member'
    NONMEMBER              = 'nonmember'
    ORGANIZATION_ID        = 'o'
    SPIRES                 = 'SPIRES'
    TIME_FORMAT            = '%Y-%m-%d_%H:%M'


class OPTIONS:
  IDENTIFIERS_LIST         = ['Inspire ID', 'ORCID']
  IDENTIFIERS_MAPPING      = {'Inspire ID': 'Inspire ID',
                              'INSPIRE': 'Inspire ID',
                              'Inspire': 'Inspire ID',
                              'ORCID': 'ORCID'}
  AUTHOR_AFFILIATION_TYPE  = ['Affiliated with', 'Now at', 'Also at',
                              'On leave from', 'Visitor']
