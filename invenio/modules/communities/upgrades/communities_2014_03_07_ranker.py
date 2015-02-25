# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

from sqlalchemy import *
from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op

depends_on = []


def info():
    return "Add ranker"


def do_upgrade():
    """ Implement your upgrades here  """
    op.add_column(u'community', db.Column('fixed_points',
                  db.Integer(display_width=9), nullable=False))
    op.add_column(u'community',
                  db.Column('last_record_accepted', db.DateTime(),
                            nullable=False))
    op.add_column(u'community',
                  db.Column('ranking', db.Integer(display_width=9),
                            nullable=False))


def estimate():
    """  Estimate running time of upgrade in seconds (optional). """
    return 1
