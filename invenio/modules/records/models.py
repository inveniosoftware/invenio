# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Record models."""

from flask import current_app
from sqlalchemy.ext.declarative import declared_attr
from werkzeug import cached_property

from invenio.ext.sqlalchemy import db, utils


class Record(db.Model):

    """Represent a record object inside the SQL database."""

    __tablename__ = 'bibrec'

    id = db.Column(
        db.MediumInteger(8, unsigned=True), primary_key=True,
        nullable=False, autoincrement=True)
    creation_date = db.Column(
        db.DateTime, nullable=False,
        server_default='1900-01-01 00:00:00',
        index=True)
    modification_date = db.Column(
        db.DateTime, nullable=False,
        server_default='1900-01-01 00:00:00',
        index=True)
    master_format = db.Column(
        db.String(16), nullable=False,
        server_default='marc')
    additional_info = db.Column(db.JSON)

    # FIXME: remove this from the model and add them to the record class, all?

    @property
    def deleted(self):
        """Return True if record is marked as deleted."""
        from invenio.legacy.bibrecord import get_fieldvalues
        # record exists; now check whether it isn't marked as deleted:
        dbcollids = get_fieldvalues(self.id, "980__%")

        return ("DELETED" in dbcollids) or \
               (current_app.config.get('CFG_CERN_SITE')
                and "DUMMY" in dbcollids)

    @staticmethod
    def _next_merged_recid(recid):
        """Return the ID of record merged with record with ID = recid."""
        from invenio.legacy.bibrecord import get_fieldvalues
        merged_recid = None
        for val in get_fieldvalues(recid, "970__d"):
            try:
                merged_recid = int(val)
                break
            except ValueError:
                pass

        if not merged_recid:
            return None
        else:
            return merged_recid

    @cached_property
    def merged_recid(self):
        """Return record object with which the given record has been merged.

        :param recID: deleted record recID
        :return: merged record recID
        """
        return Record._next_merged_recid(self.id)

    @property
    def merged_recid_final(self):
        """Return the last record from hierarchy merged with this one."""
        cur_id = self.id
        next_id = Record._next_merged_recid(cur_id)

        while next_id:
            cur_id = next_id
            next_id = Record._next_merged_recid(cur_id)

        return cur_id

    @cached_property
    def is_restricted(self):
        """Return True is record is restricted."""
        from invenio.legacy.search_engine import \
            get_restricted_collections_for_recid

        if get_restricted_collections_for_recid(
                self.id, recreate_cache_if_needed=False):
            return True
        elif self.is_processed:
            return True
        return False

    @cached_property
    def is_processed(self):
        """Return True is recods is processed (not in any collection)."""
        from invenio.legacy.search_engine import is_record_in_any_collection
        return not is_record_in_any_collection(self.id,
                                               recreate_cache_if_needed=False)


class RecordMetadata(db.Model):

    """Represent a json record inside the SQL database."""

    __tablename__ = 'record_json'

    id = db.Column(
        db.MediumInteger(8, unsigned=True),
        db.ForeignKey(Record.id),
        primary_key=True,
        nullable=False,
        autoincrement=True
    )

    json = db.Column(db.JSON, nullable=False)

    record = db.relationship(Record, backref='record_json')


class BibxxxMixin(utils.TableNameMixin):

    """Mixin for Bibxxx tables."""

    id = db.Column(db.MediumInteger(8, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                    server_default='')
    value = db.Column(db.Text(35), nullable=False,
                      index=True)


class BibrecBibxxxMixin(utils.TableFromCamelNameMixin):

    """Mixin for BibrecBibxxx tables."""

    @declared_attr
    def _bibxxx(cls):
        return globals()[cls.__name__[6:]]

    @declared_attr
    def id_bibrec(cls):
        return db.Column(db.MediumInteger(8, unsigned=True),
                         db.ForeignKey(Record.id), nullable=False,
                         primary_key=True, index=True, server_default='0')

    @declared_attr
    def id_bibxxx(cls):
        return db.Column(db.MediumInteger(8, unsigned=True),
                         db.ForeignKey(cls._bibxxx.id), nullable=False,
                         primary_key=True, index=True, server_default='0')

    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                             primary_key=True)

    @declared_attr
    def bibrec(cls):
        return db.relationship(Record)

    @declared_attr
    def bibxxx(cls):
        return db.relationship(cls._bibxxx, backref='bibrecs')

models = []

for idx in range(100):
    Bibxxx = "Bib{0:02d}x".format(idx)
    globals()[Bibxxx] = type(Bibxxx, (db.Model, BibxxxMixin), {})
    BibrecBibxxx = "BibrecBib{0:02d}x".format(idx)
    globals()[BibrecBibxxx] = type(BibrecBibxxx,
                                   (db.Model, BibrecBibxxxMixin), {})

    models += [Bibxxx, BibrecBibxxx]

__all__ = tuple([
    'Record',
    'RecordMetadata',
] + models)
