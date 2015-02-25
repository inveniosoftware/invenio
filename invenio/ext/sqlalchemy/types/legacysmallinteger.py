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
# 55 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Platform-independent SmallInteger type."""

from sqlalchemy.types import SmallInteger
from sqlalchemy.dialects.mysql import SMALLINT
from . import LegacyInteger


class LegacySmallInteger(LegacyInteger):

    """Platform-independent SmallInteger type.

    Uses MySQL's :class:`~sqlalchemy.dialects.mysql.SMALLINT` type, otherwise
    uses SQLAlchemy definition of :class:`~sqlalchemy.types.SmallInteger`.
    """

    impl = SmallInteger

    def __init__(self, display_width=5, unsigned=False, zerofill=True,
                 **kwargs):
        """Reserve special arguments only for MySQL Platform."""
        self.zerofill = zerofill
        super(LegacySmallInteger, self).__init__(
            display_width, unsigned, **kwargs)

    def load_dialect_impl(self, dialect):
        """Load dialect dependent implementation."""
        if dialect.name == 'mysql':
            return dialect.type_descriptor(SMALLINT(self.display_width,
                                                    unsigned=self.unsigned,
                                                    zerofill=self.zerofill))
        else:
            return dialect.type_descriptor(SmallInteger)
