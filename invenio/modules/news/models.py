# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""nwsToolTip database models."""

from invenio.ext.sqlalchemy import db


class NwsSTORY(db.Model):

    """Represents a nwsSTORY record."""

    __tablename__ = 'nwsSTORY'
    id = db.Column(
        db.Integer(11, unsigned=True),
        nullable=False,
        primary_key=True,
        autoincrement=True
    )
    title = db.Column(db.String(256), nullable=False, default='')
    body = db.Column(db.Text, nullable=False, default='')
    created = db.Column(db.TIMESTAMP, nullable=False)
    document_status = db.Column(db.String(45), nullable=False, default='SHOW')
    remote_ip = db.Column(db.String(100), nullable=False, default='0.0.0.0')
    email = db.Column(
        db.String(100),
        nullable=False,
        default='admin@admin.com'
    )
    nickname = db.Column(db.String(100), nullable=False, default='admin')
    uid = db.Column(db.Integer(11, unsigned=True), nullable=False)
    nwsToolTip = db.relationship(
        'NwsToolTip',
        backref='nwsSTORY',
        cascade='all, delete, delete-orphan'
    )
    nwsTAG = db.relationship(
        'NwsTAG',
        backref='nwsSTORY',
        cascade='all, delete, delete-orphan'
    )


class NwsToolTip(db.Model):

    """Represents a NwsToolTip record."""

    __tablename__ = 'nwsTOOLTIP'
    id = db.Column(
        db.Integer(15, unsigned=True),
        nullable=False,
        primary_key=True,
        autoincrement=True
    )
    id_story = db.Column(
        db.Integer(15, unsigned=True),
        db.ForeignKey('nwsSTORY.id')
    )
    body = db.Column(db.String(512), nullable=False, server_default='0')
    target_element = db.Column(
        db.String(256),
        nullable=False,
        server_default='0'
    )
    target_page = db.Column(db.String(256), nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format."""
        return {
            'id': self.id,
            'id_story': self.id_story,
            'body': self.body,
            'target_element': self.target_element,
            'target_page': self.target_page,
        }

    @property
    def serialize_many2many(self):
        """
        Return object's relations in easily serializeable format.

        NB! Calls many2many's serialize property.
        """
        return [item.serialize for item in self.nwsSTORY]


class NwsTAG(db.Model):

    """Represents a nwsTAG record."""

    __tablename__ = 'nwsTAG'
    id = db.Column(
        db.Integer(15, unsigned=True),
        nullable=False,
        primary_key=True,
        autoincrement=True
    )
    id_story = db.Column(
        db.Integer(15, unsigned=True),
        db.ForeignKey('nwsSTORY.id')
    )
    tag = db.Column(db.String(64), nullable=False, default='')

    @property
    def serialize_tag(self):
        """Return object data in easily serializeable format."""
        return {
            'id_story': self.id_story
        }
