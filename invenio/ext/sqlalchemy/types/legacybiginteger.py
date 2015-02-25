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
# 515 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Platform-independent BigInteger type."""

from sqlalchemy.types import TypeDecorator, BigInteger
from sqlalchemy.dialects.mysql import BIGINT


class LegacyBigInteger(TypeDecorator):

    """Platform-independent BigInteger type.

    Uses MySQL's :class:`~sqlalchemy.dialects.mysql.BIGINT` type, otherwise
    uses SQLAlchemy definition of :class:`~sqlalchemy.types.BigInteger`.
    """

    impl = BigInteger

    def __init__(self, display_width=15, unsigned=False, **kwargs):
        """Reserve special arguments only for MySQL Platform."""
        self.display_width = display_width
        self.unsigned = unsigned
        super(LegacyBigInteger, self).__init__(**kwargs)

    def load_dialect_impl(self, dialect):
        """Load dialect dependent implementation."""
        if dialect.name == 'mysql':
            return dialect.type_descriptor(BIGINT(self.display_width,
                                                  unsigned=self.unsigned))
        else:
            return dialect.type_descriptor(BigInteger)
