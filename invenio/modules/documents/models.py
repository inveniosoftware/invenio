# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014 CERN.
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

"""
BibDoc Filesystem database model.
"""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.
from invenio.modules.editor.models import Bibdoc


class Bibdocfsinfo(db.Model):
    """Represents a Bibdocfsinfo record."""
    __tablename__ = 'bibdocfsinfo'

    id_bibdoc = db.Column(db.MediumInteger(9, unsigned=True),
                    db.ForeignKey(Bibdoc.id), primary_key=True,
                    nullable=False, autoincrement=False)
    version = db.Column(db.TinyInteger(4, unsigned=True), primary_key=True,
                    nullable=False, autoincrement=False)
    format = db.Column(db.String(50), primary_key=True, nullable=False,
                    index=True)
    last_version = db.Column(db.Boolean, nullable=False, index=True)
    cd = db.Column(db.DateTime, nullable=False, index=True)
    md = db.Column(db.DateTime, nullable=False, index=True)
    checksum = db.Column(db.Char(32), nullable=False)
    filesize = db.Column(db.BigInteger(15, unsigned=True), nullable=False,
                    index=True)
    mime = db.Column(db.String(100), nullable=False, index=True)
    master_format = db.Column(db.String(50))


class Bibdocmoreinfo(db.Model):
    """Represents a Bibdocmoreinfo record."""
    __tablename__ = 'bibdocmoreinfo'

    id = db.Column(db.MediumInteger(9, unsigned=True), primary_key=True)
    id_bibdoc = db.Column(db.MediumInteger(9, unsigned=True),
                    db.ForeignKey(Bibdoc.id), nullable=True)
    version = db.Column(db.TinyInteger(4, unsigned=True), nullable=True)
    format = db.Column(db.String(50), nullable=True)
    id_rel = db.Column(db.MediumInteger(9, unsigned=True), nullable=True)
    namespace = db.Column(db.Char(25), nullable=True)
    data_key = db.Column(db.Char(25))
    data_value = db.Column(db.LargeBinary)

    __table_args__ = (db.Index('bibdocmoreinfo_key', id_bibdoc, version,
                               format, id_rel, namespace, data_key),
                      db.Model.__table_args__)


class Document(db.Model):
    """Represents a document object inside the SQL database"""

    __tablename__ = 'documents'
    id = db.Column(db.UUID, primary_key=True)
    parent_id = db.Column(db.UUID, nullable=True)
    creation_date = db.Column(db.DateTime, nullable=False,
                              server_default='1900-01-01 00:00:00', index=True)
    modification_date = db.Column(db.DateTime, nullable=False,
                                  server_default='1900-01-01 00:00:00',
                                  index=True)
    json = db.Column(db.JSON, nullable=True)

    #FIXME write better setter for json
