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

"""Sorter database models."""

# General imports.
from datetime import datetime
from flask import g
from intbitset import intbitset
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.collections import attribute_mapped_collection

from invenio.ext.sqlalchemy import db
from invenio.utils.serializers import deserialize_via_marshal

# Create your models here.
from invenio.modules.collections.models import Collection


class BsrMETHOD(db.Model):

    """Represent a BsrMETHOD record."""

    __tablename__ = 'bsrMETHOD'

    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True, nullable=False)
    name = db.Column(db.String(20), nullable=False, unique=True)
    definition = db.Column(db.String(255), nullable=False)
    washer = db.Column(db.String(255), nullable=False)

    bucket_data = association_proxy('buckets', 'data')

    def get_name_ln(self, ln=None):
        """Return localized method name."""
        try:
            if ln is None:
                ln = g.ln
            return self.names.filter_by(ln=g.ln, type='ln').one().value
        except:
            return self.name

    @classmethod
    def get_sorting_methods(cls):
        """Return initialized method mapping."""
        return dict(db.session.query(cls.name, cls.definition).filter(
            db.session.query(BsrMETHODDATA).filter(
                BsrMETHODDATA.id_bsrMETHOD == cls.id
            ).exists()
        ).all())

    def get_cache(self):
        """Return data to populate cache."""
        if len(self.methoddata) < 1:
            return {}
        return dict(
            data_dict_ordered=self.methoddata[0].ordered,
            bucket_data=dict(self.bucket_data),
        )

    @classmethod
    def timestamp_verifier(cls, name):
        """Return last modification time for given sorting method."""
        min_date = datetime(1970, 1, 1)
        method_id = db.select([cls.id], cls.name == name)
        data_updated = db.session.query(
            db.func.max(BsrMETHODDATA.last_updated)
        ).filter(BsrMETHODDATA.id_bsrMETHOD.in_(method_id)).scalar()
        bucket_updated = db.session.query(
            db.func.max(BsrMETHODDATABUCKET.last_updated)
        ).filter(BsrMETHODDATABUCKET.id_bsrMETHOD.in_(method_id)).scalar()
        return max(data_updated, bucket_updated, min_date)


class BsrMETHODDATA(db.Model):

    """Represent a BsrMETHODDATA record."""

    __tablename__ = 'bsrMETHODDATA'

    id_bsrMETHOD = db.Column(db.MediumInteger(9, unsigned=True),
                             db.ForeignKey(BsrMETHOD.id),
                             primary_key=True, nullable=False,
                             autoincrement=False)
    data_dict = db.Column(db.LargeBinary)
    data_dict_ordered = db.Column(db.LargeBinary)
    data_list_sorted = db.Column(db.LargeBinary)
    last_updated = db.Column(db.DateTime)

    @property
    def ordered(self):
        """Return deserialized orderd dict."""
        return deserialize_via_marshal(self.data_dict_ordered)

    method = db.relationship(BsrMETHOD, backref='methoddata')


class BsrMETHODDATABUCKET(db.Model):

    """Represent a BsrMETHODDATABUCKET record."""

    __tablename__ = 'bsrMETHODDATABUCKET'

    id_bsrMETHOD = db.Column(db.MediumInteger(9, unsigned=True),
                             db.ForeignKey(BsrMETHOD.id), autoincrement=False,
                             primary_key=True, nullable=False)
    bucket_no = db.Column(db.TinyInteger(2), primary_key=True, nullable=False,
                          autoincrement=False)
    bucket_data = db.Column(db.LargeBinary)
    bucket_last_value = db.Column(db.String(255))
    last_updated = db.Column(db.DateTime)

    method = db.relationship(BsrMETHOD, backref=db.backref(
        "buckets",
        collection_class=attribute_mapped_collection("bucket_no"),
        cascade="all, delete-orphan"
        )
    )

    @property
    def data(self):
        """Return bucket data as intbitset."""
        return intbitset(self.bucket_data)


class BsrMETHODNAME(db.Model):

    """Represent a BsrMETHODNAME record."""

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

    """Represent a Collection_bsrMETHOD record."""

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
