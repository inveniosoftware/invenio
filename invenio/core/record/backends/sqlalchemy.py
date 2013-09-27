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

"""
    invenio.core.record.backends.sqlalchemy
    ---------------------------------------

    - RECORD_BACKEND_SQLALCHEMY = 'invenio.ext.sqlalchemy:db'

"""
from itertools import izip, imap

from flask import current_app
from flask.helpers import locked_cached_property
from werkzeug import import_string

from ..storage import RecordStorage
from ..model import Record
from invenio.ext.sqlalchemy import db


class RecordMetadata(db.Model):
    """Represents a json record inside the SQL database"""

    __tablename__ = 'record_metadata'
    id = db.Column(db.MediumInteger(8, unsigned=True),
            db.ForeignKey(Record.id),
            primary_key=True,
            nullable=False,
            autoincrement=True)
    json = db.Column(db.PickleBinary,
            nullable=False)

    record = db.relationship(Record, backref='record_metadata')


class Storage(RecordStorage):
    """
    Implements database backend for SQLAlchemy model storage.
    """
    #FIXME: This storage engine should use transactions!
    #FIXME: manage errors and return values

    def __init__(self, *args, **kwards):
        if not self.db.engine.dialect.has_table(self.db.engine,
                self.model.__tablename__):
            self.model.__table__.create(bind=self.db.engine)
            self.db.session.commit()

    @locked_cached_property
    def db(self):
        """Returns SQLAlchemy database object."""
        return import_string(current_app.config.get(
            'RECORD_BACKEND_SQLALCHEMY', 'invenio.ext.sqlalchemy:db'))

    @locked_cached_property
    def model(self):
        """Returns SQLAlchemy model."""
        return RecordMetadata

    def save_one(self, json_record, recid=None):
        if recid is None:
            recid = json_record['recid']

        new_record_metadata = RecordMetadata(id=recid, json=json_record)
        self.db.session.add(new_record_metadata)
        self.db.session.commit()

    def save_many(self, json_records, recids=None):
        if recids is None:
            recids = imap(lambda j: j['recid'], json_records)
        self.db.session.add_all([RecordMetadata(id=recid, json=json_record)
            for recid, json_record in izip(recids, json_records)])
        self.db.session.commit()

    def update_one(self, json, recid=None):
        #FIXME: what if we get only the fields that have change
        if recid is None:
            recid = json_record['recid']

        new_record_metadata = RecordMetadata(id=recid, json=json_record)
        self.db.session.merge(new_record_metadata)
        self.db.session.commit()

    def update_many(self, jsons, recids=None):
        #FIXME: what if we get only the fields that have change
        if recids is None:
            recids = imap(lambda j: j['recid'], json_records)

        for recid, json_record in izip(recids, json_records):
            new_record_metadata = RecordMetadata(id=recid, json=json_record)
            self.db.session.merge(new_record_metadata)
        self.db.session.commit()

    def get_one(self, recid):
        return self.db.session.query(RecordMetadata.json)\
                .filter_by(id=recid).one().json

    def get_many(self, recids):
        for json in self.db.session.query(RecordMetadata.json)\
                .filter(RecordMetadata.id.in_(recids))\
                .all():
            yield json[0]

    def get_field_values(recids, field, repetitive_values=True, count=False,
            include_recid=False, split_by=0):
        raise NotImplementedError()

    def get_fields_values(recids, fields, repetitive_values=True, count=False,
            include_recid=False, split_by=0):
        raise NotImplementedError()
