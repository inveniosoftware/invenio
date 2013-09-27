# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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
errorlib database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.

class HstEXCEPTION(db.Model):
    """Represents a HstEXCEPTION record."""
    __tablename__ = 'hstEXCEPTION'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(255), nullable=True)
    line = db.Column(db.Integer(9), nullable=True)
    last_seen = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00', index=True)
    last_notified = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00', index=True)
    counter = db.Column(db.Integer(15), nullable=False,
                server_default='0')
    total = db.Column(db.Integer(15), nullable=False,
                server_default='0', index=True)

    __table_args__ = (db.Index('name', name, filename, line, unique=True),
                      db.Model.__table_args__)


__all__ = ['HstEXCEPTION']
