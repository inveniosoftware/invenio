# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2014 CERN.
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
BibSort database models.
"""

# General imports.
from flask import g
from sqlalchemy import and_
from invenio.ext.sqlalchemy import db
from invenio.base.globals import cfg

# Create your models here.
from invenio.modules.search.models import Collection


class BsrMETHOD(db.Model):

    """Represents a BsrMETHOD record."""

    __tablename__ = 'bsrMETHOD'

    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True, nullable=False)
    name = db.Column(db.String(20), nullable=False, unique=True)
    definition = db.Column(db.String(255), nullable=False)
    washer = db.Column(db.String(255), nullable=False)

    def get_name_ln(self, ln=None):
        """Return localized method name."""
        try:
            if ln is None:
                ln = g.ln
            return self.names.filter_by(ln=g.ln, type='ln').one().value
        except:
            return self.name


class BsrMETHODDATA(db.Model):

    """Represents a BsrMETHODDATA record."""

    __tablename__ = 'bsrMETHODDATA'

    id_bsrMETHOD = db.Column(db.MediumInteger(9, unsigned=True),
                             db.ForeignKey(BsrMETHOD.id),
                             primary_key=True, nullable=False,
                             autoincrement=False)
    data_dict = db.Column(db.LargeBinary)
    data_dict_ordered = db.Column(db.LargeBinary)
    data_list_sorted = db.Column(db.LargeBinary)
    last_updated = db.Column(db.DateTime)


class BsrMETHODDATABUCKET(db.Model):

    """Represents a BsrMETHODDATABUCKET record."""

    __tablename__ = 'bsrMETHODDATABUCKET'

    id_bsrMETHOD = db.Column(db.MediumInteger(9, unsigned=True),
                             db.ForeignKey(BsrMETHOD.id), autoincrement=False,
                             primary_key=True, nullable=False)
    bucket_no = db.Column(db.TinyInteger(2), primary_key=True, nullable=False,
                          autoincrement=False)
    bucket_data = db.Column(db.LargeBinary)
    bucket_last_value = db.Column(db.String(255))
    last_updated = db.Column(db.DateTime)


class BsrMETHODNAME(db.Model):

    """Represents a BsrMETHODNAME record."""

    __tablename__ = 'bsrMETHODNAME'

    id_bsrMETHOD = db.Column(db.MediumInteger(9, unsigned=True),
                             db.ForeignKey(BsrMETHOD.id),
                             primary_key=True, nullable=False,
                             autoincrement=False)
    ln = db.Column(db.String(5), primary_key=True, nullable=False)
    type = db.Column(db.String(3), primary_key=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
    method = db.relationship(BsrMETHOD, backref=db.backref('names',
                                                           lazy='dynamic'))


class Collection_bsrMETHOD(db.Model):

    """Represents a Collection_bsrMETHOD record."""

    __tablename__ = 'collection_bsrMETHOD'

    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                              db.ForeignKey(Collection.id),
                              primary_key=True, nullable=False,
                              autoincrement=False)
    id_bsrMETHOD = db.Column(db.MediumInteger(9, unsigned=True),
                             db.ForeignKey(BsrMETHOD.id),
                             primary_key=True, nullable=False,
                             autoincrement=False)
    score = db.Column(db.TinyInteger(4, unsigned=True), server_default='0',
                      nullable=False)

    collection = db.relationship(Collection, backref='bsrMETHODs')
    bsrMETHOD = db.relationship(BsrMETHOD, backref='collections')
