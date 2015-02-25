# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012 CERN.
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
misc database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.

class Publreq(db.Model):
    """Represents a Publreq record."""
    def __init__(self):
        pass
    __tablename__ = 'publreq'
    id = db.Column(db.Integer(11), nullable=False,
                primary_key=True,
                autoincrement=True)
    host = db.Column(db.String(255), nullable=False,
                server_default='')
    date = db.Column(db.String(255), nullable=False,
                server_default='')
    name = db.Column(db.String(255), nullable=False,
                server_default='')
    email = db.Column(db.String(255), nullable=False,
                server_default='')
    address = db.Column(db.Text, nullable=False)
    publication = db.Column(db.Text, nullable=False)

__all__ = ['Publreq']
