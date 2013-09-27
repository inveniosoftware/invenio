# -*- coding: utf-8 -*-
#
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
## 59 Temple Place, Suite 330, Boston, MA 02D111-1307, USA.

"""
    invenio.modules.formatter.models
    -----------------------------------

    Database access related functions for Formatter engine and
    administration pages.
"""
from invenio.ext.sqlalchemy import db
from invenio.modules.record_editor.models import Bibrec


class Format(db.Model):
    """Represents a Format record."""
    __tablename__ = 'format'

    id = db.Column(
        db.MediumInteger(9, unsigned=True),
        primary_key=True,
        autoincrement=True)

    name = db.Column(db.String(255), nullable=False)

    code = db.Column(db.String(6), nullable=False, unique=True)

    description = db.Column(db.String(255), server_default='')

    content_type = db.Column(db.String(255), server_default='')

    visibility = db.Column(
        db.TinyInteger(4),
        nullable=False,
        server_default='1')

    last_updated = db.Column(db.DateTime, nullable=True)

    @classmethod
    def get_export_formats(cls):
        return cls.query.filter(db.and_(
            Format.content_type != 'text/html',
            Format.visibility == 1)
        ).order_by(Format.name).all()

    def set_name(self, name, lang="generic", type='ln'):
        """
        Sets the name of an output format.

        if 'type' different from 'ln' or 'sn', do nothing
        if 'name' exceeds 256 chars, 'name' is truncated to first 256 chars.

        The localized names of output formats are located in formatname table.

        :param type: either 'ln' (for long name) and 'sn' (for short name)
        :param lang: the language in which the name is given
        :param name: the name to give to the output format
        """

        if len(name) > 256:
            name = name[:256]
        if type.lower() != "sn" and type.lower() != "ln":
            return

        if lang == "generic" and type.lower() == "ln":
            self.name = name
        else:
            # Save inside formatname table for name variations
            fname = db.session.query(Formatname)\
                        .get((self.id, lang, type.lower()))

            if not fname:
                fname = db.session.merge(Formatname())
                fname.id_format = self.id
                fname.ln = lang
                fname.type = type.lower()

            fname.value = name
            db.session.save(fname)

        db.session.add(self)
        db.session.commit()


class Formatname(db.Model):
    """Represents a Formatname record."""
    __tablename__ = 'formatname'

    id_format = db.Column(
        db.MediumInteger(9, unsigned=True),
        db.ForeignKey(Format.id),
        primary_key=True)

    ln = db.Column(
        db.Char(5),
        primary_key=True,
        server_default='')

    type = db.Column(
        db.Char(3),
        primary_key=True,
        server_default='sn')

    value = db.Column(db.String(255), nullable=False)

    format = db.relationship(Format, backref='names')
    #TODO add association proxy with key (id_format, ln, type)


class Bibfmt(db.Model):
    """Represents a Bibfmt record."""

    def __init__(self):
        pass

    __tablename__ = 'bibfmt'

    id_bibrec = db.Column(
        db.MediumInteger(8, unsigned=True),
        db.ForeignKey(Bibrec.id),
        nullable=False,
        server_default='0',
        primary_key=True,
        autoincrement=False)

    format = db.Column(
        db.String(10),
        nullable=False,
        server_default='',
        primary_key=True,
        index=True)

    last_updated = db.Column(
        db.DateTime,
        nullable=False,
        server_default='1900-01-01 00:00:00',
        index=True)

    value = db.Column(db.iLargeBinary)

    bibrec = db.relationship(Bibrec, backref='bibfmt')

__all__ = [
    'Format',
    'Formatname',
    'Bibfmt',
]
