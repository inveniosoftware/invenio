# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2015 CERN.
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

"""Database model for persisting relationships."""

from uuid import uuid4

from invenio.ext.sqlalchemy import db, utils

from sqlalchemy_utils import UUIDType


class Relationship(db.Model):

    """Represent a graph edge."""

    uuid = db.Column(UUIDType(binary=False), primary_key=True)
    storagename_from = db.Column(db.String(255), index=True)
    id_from = db.Column(db.String(255), index=True)
    link_type = db.Column(db.String(255), index=True)
    # FIX ME: add index
    link_attributes = db.Column(db.JSON)
    storagename_to = db.Column(db.String(255), index=True)
    id_to = db.Column(db.String(255), index=True)

    def __init__(self, json_from, link_type, json_to, uuid=None):
        """Initialize the relationship between two records.

        Parameters
        ----------
        :param json_from: integer
            The source record.
        :param link_type: string
            Name of the relation.
        :param json_to: string
            The destination record.
        :param uuid: UUID
            Presetted uuid. Optional
        """
        self.uuid = uuid4() if uuid is None else uuid
        self.id_from = str(json_from['_id'])
        self.storagename_from = json_from.__storagename__
        self.link_type = link_type
        self.id_to = str(json_to['_id'])
        self.storagename_to = json_to.__storagename__

    @utils.session_manager
    def save(self):
        """Helper method for adding to ``SQLAlchemy`` session."""
        db.session.add(self)


__all__ = ("Relationship")
