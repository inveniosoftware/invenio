# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2014 CERN.
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
RefExtract database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.


class XtrJOB(db.Model):

    """Represents a XtrJOB record."""

    __tablename__ = 'xtrJOB'

    id = db.Column(db.TinyInteger(4), primary_key=True, nullable=False)
    name = db.Column(db.String(30), nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False)
    last_recid = db.Column(db.MediumInteger(8, unsigned=True), nullable=False)


__all__ = ['XtrJOB']
