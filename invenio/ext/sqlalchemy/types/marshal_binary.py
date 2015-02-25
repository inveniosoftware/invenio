# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014 CERN.
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

"""Implement compressed column type."""

from sqlalchemy.types import TypeDecorator, LargeBinary
from invenio.utils.serializers import ZlibMarshal


class MarshalBinary(TypeDecorator):

    """Implement compressed column type."""

    impl = LargeBinary

    def __init__(self, default_value, force_type=None, *args, **kwargs):
        """Initialize default value and type."""
        super(MarshalBinary, self).__init__(*args, **kwargs)
        self.default_value = default_value
        self.force_type = force_type if force_type is not None else lambda x: x

    def process_bind_param(self, value, dialect):
        """Compress data in column."""
        if value is not None:
            value = ZlibMarshal.dumps(self.force_type(value))
            return value
        return value

    def process_result_value(self, value, dialect):
        """Load comressed data from column."""
        if value is not None:
            try:
                value = ZlibMarshal.loads(value)
            except:
                value = None
        return value if value is not None else \
            (self.default_value() if callable(self.default_value) else
             self.default_value)
