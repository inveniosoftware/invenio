# -*- coding: utf-8 -*-

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
Record model
"""

from invenio.ext.sqlalchemy import db

class Record(db.Model):
    """Represents a record object inside the SQL database"""

    __tablename__ = 'record'
    id = db.Column(db.MediumInteger(8, unsigned=True),
            primary_key=True,
            nullable=False,
            autoincrement=True)
    creation_date = db.Column(db.DateTime,
            nullable=False,
            server_default='1900-01-01 00:00:00',
            index=True)
    modification_date = db.Column(db.DateTime,
            nullable=False,
            server_default='1900-01-01 00:00:00',
            index=True)
    additional_info = db.Column(db.JSON,
            nullable=False,
            server_default='{}')
