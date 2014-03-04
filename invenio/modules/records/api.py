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
    invenio.modules.records.api
    ---------------------------

"""

from sqlalchemy.orm.exc import NoResultFound

from invenio.modules.jsonalchemy.jsonext.engines.sqlalchemy import SQLAlchemyStorage
from invenio.modules.jsonalchemy.parser import FieldParser
from invenio.modules.jsonalchemy.registry import readers
from invenio.modules.jsonalchemy.wrappers import SmartJson

from .models import RecordMetadata as RecordMetadataModel
from .models import Record as RecordModel


class Record(SmartJson):
    """
    Default/Base record class
    """

    storage_engine = SQLAlchemyStorage(RecordMetadataModel)

    @classmethod
    def create(cls, blob, master_format, **kwargs):
        if 'namespace' not in kwargs:
            kwargs['namespace'] = 'recordext'

        reader = readers[master_format](blob, **kwargs)
        return cls(reader.translate())

    @classmethod
    def create_many(cls, blobs, master_format, **kwargs):
        if 'namespace' not in kwargs:
            kwargs['namespace'] = 'recordext'

        reader = readers[master_format]

        for blob in reader.split_blob(blobs, **kwargs):
            yield cls.create(blob, master_format, **kwargs)
        raise StopIteration()

    @classmethod
    def get_record(cls, recid, reset_cache=False):
        if not reset_cache:
            try:
                json = cls.storage_engine.get_one(recid)
                return Record(json)
            except NoResultFound:
                pass
        # try to retrieve the record from the master format if any
        # this might be deprecated in the near future as soon as json will
        # become the master format, until then ...
        blob = cls.get_blob(recid)
        record_model = RecordModel.query.get(recid)
        if record_model is None or blob is None:
            return None
        additional_info = record_model.additional_info \
                if record_model.additional_info else {'master_format': 'marc'}
        record = cls.create(blob, **additional_info)
        record._save()
        record_model.additional_info = \
                record.get('__meta_metadata__.__additional_info__',
                           {'master_format': 'marc'})
        from invenio.ext.sqlalchemy import db
        db.session.merge(record_model)
        db.session.commit()
        return record

    @staticmethod
    def get_blob(recid):
        #FIXME: start using bibarchive or bibingest for this
        from invenio.modules.formatter.models import Bibfmt
        from zlib import decompress

        record_blob = Bibfmt.query.get((recid, 'xm'))
        if record_blob is None:
            return None
        return decompress(record_blob.value)

    def _save(self):
        self.storage_engine.update_one(self.dumps())

# Functional interface
create_record = Record.create
create_records = Record.create_many
get_record = Record.get_record
get_record_blob = Record.get_blob












