# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012 CERN.
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
Web Author Profile database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.

class WapCACHE(db.Model):
    """Represents a WapCACHE record."""
    __tablename__ = 'wapCACHE'

    object_name = db.Column(db.String(120), primary_key=True, nullable=False)
    object_key = db.Column(db.String(120), primary_key=True, nullable=False)
    object_value = db.Column(db.Text) #FIXME LongText
    object_status = db.Column(db.String(120), index=True)
    last_updated = db.Column(db.DateTime, nullable=False, index=True)

__all__ = ['WapCACHE']
