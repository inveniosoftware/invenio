# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2014 CERN.
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
SeqUtils database models.
"""

from invenio.ext.sqlalchemy import db


class SeqSTORE(db.Model):
    """Represents a SeqSTORE record."""
    __tablename__ = 'seqSTORE'

    id = db.Column(
        db.Integer(15, unsigned=True),
        primary_key=True, nullable=False,
        autoincrement=True
    )
    seq_name = db.Column(db.String(15))
    seq_value = db.Column(db.String(20))

    __table_args__ = (db.Index('seq_name_value', seq_name, seq_value,
                               unique=True),
                      db.Model.__table_args__)

__all__ = ['SeqSTORE']
