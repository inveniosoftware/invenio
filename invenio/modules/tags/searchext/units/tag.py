# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Tag plugin for search unit."""

from intbitset import intbitset
from flask_login import current_user

from invenio.ext.sqlalchemy import db

from ...models import WtgTAG, WtgTAGRecord, wash_tag_silent


def search_unit(query, f, m, wl=None):
    """Return hitset of recIDs that are associated with tags in query."""
    # Names are comma-separated
    # Multiple-word names can be in quotes -> remove those quotes
    tag_names = [wash_tag_silent(tag_name.replace('"', ''))
                 for tag_name in query.split(',')]

    if not tag_names:
        return intbitset()

    tag_names_filter = WtgTAG.name.in_(tag_names) if len(tag_names) > 1 \
        else WtgTAG.name == tag_names[0]

    return intbitset(
        db.session.query(WtgTAGRecord.id_bibrec).options(
            db.joined(WtgTAGRecord.tag)
        ).filter(tag_names_filter,
                 WtgTAG.id_user == current_user.get_id()).all()
    )
