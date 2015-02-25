# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""Communities configuration variables."""

from datetime import timedelta

COMMUNITIES_TABS = 'usage;comments;metadata;files'
""" Detailed record tabs to enable for a community"""

COMMUNITIES_PARENT_NAME = 'Atlantis Institute of Fictive Science'
""" Collection name of parent of public user communities """

COMMUNITIES_PARENT_NAME_PROVISIONAL = 'Atlantis Institute of Fictive Science'
""" Collection name of parent of provisional user communities """

COMMUNITIES_OUTPUTFORMAT = 'hb'
"""
Output format to use for community, use empty string for default.
"""

COMMUNITIES_OUTPUTFORMAT_PROVISIONAL = 'hbpro'
"""
Output format to use for provisional community, use empty string for default.
"""

COMMUNITIES_PORTALBOXES = [
    'communities/portalbox_main.html',
    'communities/portalbox_upload.html'
]
"""
List of templates to render as portalboxes for each community - order of
portalboxes is given by order of templates.
"""

COMMUNITIES_PORTALBOXES_PROVISIONAL = [
    'communities/portalbox_provisional.html',
]
"""
List of templates to render as portalboxes for each provisional community -
order of portalboxes is given by order of templates.
"""

COMMUNITIES_COLLECTION_TYPE = 'v'
""" Type of communities created (v, virtual or r, regular) """

COMMUNITIES_COLLECTION_SCORE = 0
""" Default score used for ordering communities """

COMMUNITIES_PORTALBOX_POSITION = 'rt'
""" Position of portal boxes """

COMMUNITIES_ID_PREFIX = 'user'
""" Collection identifier prefix for all user communities """

COMMUNITIES_ID_PREFIX_PROVISIONAL = 'provisional-user'
""" Collection identifier prefix for provisional user comunities. """

COMMUNITIES_SORTING_OPTIONS = [
    'title',
    'ranking',
]

COMMUNITIES_DEFAULT_SORTING_OPTION = 'ranking'

COMMUNITIES_DISPLAYED_PER_PAGE = 20

COMMUNITIES_PERIODIC_TASKS = {
    'ranking_deamon': {
        'run_every': timedelta(seconds=20),
    },
}
