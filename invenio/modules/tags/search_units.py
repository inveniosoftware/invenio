# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

"""WebTag Plugin for search_engine"""

from invenio.intbitset import intbitset
from flask.ext.login import current_user

from .models import \
    WtgTAG, \
    WtgTAGRecord, \
    wash_tag_silent


def search_unit_in_tags(search_term):
    """
    Return hitset of recIDs that are associated with any of
    the tags in search_term
    """

    results = intbitset()

    # Names are comma-separated
    # Multiple-word names can be in quotes -> remove those quotes
    tag_names = \
        [wash_tag_silent(tag_name.replace('"', ''))
         for tag_name in search_term.split(',')]

    if not tag_names:
        return results

    tag_names_filter = WtgTAG.name.in_(tag_names) if len(tag_names)>1 else WtgTAG.name == tag_names[0]

    # Find tags matching the queries names
    tags = WtgTAG.query\
        .filter_by(id_user=current_user.get_id())\
        .filter(tag_names_filter)\
        .all()

    tag_ids = [tag.id for tag in tags]

    if not tag_ids:
        # There were no tags matching the queried names
        # return empty set
        return results

    # Find records tagged with those tags
    associations = WtgTAGRecord.query\
        .filter(WtgTAGRecord.id_tag.in_(tag_ids))\
        .all()

    for association in associations:
        results += association.id_bibrec

    return results
