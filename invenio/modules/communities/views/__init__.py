# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2013, 2014, 2015 CERN.
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
## 59 Temple Place, Suite 331, Boston, MA 02111-1307, USA.

"""Define communities views."""

from .communities import blueprint as communities_blueprint
from .community_settings import blueprint as community_settings_blueprint
from .community_teams import blueprint as community_teams_blueprint
from .community_people import blueprint as community_people_blueprint
from .community_guides import blueprint as community_guides_blueprint
from .settings_communities import blueprint as settings_communities_blueprint


blueprints = [
    communities_blueprint,
    community_settings_blueprint,
    community_teams_blueprint,
    community_people_blueprint,
    community_guides_blueprint,
    settings_communities_blueprint,
]
