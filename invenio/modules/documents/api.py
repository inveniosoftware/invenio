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

from invenio.modules.jsonalchemy.wrappers import SmartJson
from invenio.modules.jsonalchemy.jsonext.engines.sqlalchemy import SQLAlchemyStorage
from invenio.modules.jsonalchemy.jsonext.readers.json_reader import reader

from .models import Document as DocumentModel


class Document(SmartJson):
    storage_engine = SQLAlchemyStorage(DocumentModel)

    @classmethod
    def create(cls, data, model='common_document'):
        record = reader(data, namespace='documentext', model=model)
        document = cls(record.translate())
        return cls.storage_engine.save_one(document.dumps())
