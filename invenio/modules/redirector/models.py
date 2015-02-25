# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""GoTo database models."""

# External imports
from sqlalchemy.orm import validates
import datetime

# General imports.
from invenio.ext.sqlalchemy import db
from .registry import redirect_methods

# Create your models here.


class Goto(db.Model):

    """Represents a Goto record."""

    __tablename__ = 'goto'
    label = db.Column(db.String(150), primary_key=True)
    plugin = db.Column(db.String(150), nullable=False)
    _parameters = db.Column(db.JSON, nullable=False, default={},
                            name="parameters")
    creation_date = db.Column(db.DateTime, default=datetime.datetime.now,
                              nullable=False, index=True)
    modification_date = db.Column(db.DateTime, default=datetime.datetime.now,
                                  onupdate=datetime.datetime.now,
                                  nullable=False, index=True)

    @validates('plugin')
    def validate_plugin(self, key, plugin):
        """Validate plugin name."""
        if plugin not in redirect_methods:
            raise ValueError("%s plugin does not exist" % plugin)

        return plugin

    @db.hybrid_property
    def parameters(self):
        """Get parameters method."""
        return self._parameters

    @parameters.setter
    def parameters(self, value):
        """Set parameters method."""
        self._parameters = value or {}

    def to_dict(self):
        """ Return a dict representation of Goto."""
        return {'label': self.label,
                'plugin': self.plugin,
                'parameters': self.parameters,
                'creation_date': self.creation_date,
                'modification_date': self.modification_date}

__all__ = ['Goto']
