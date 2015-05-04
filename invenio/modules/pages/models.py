# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Contains page model."""

from datetime import datetime

from invenio.ext.sqlalchemy import db


class Page(db.Model):

    """Represents a page."""

    __tablename__ = 'pages'

    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                   primary_key=True,
                   autoincrement=True)
    url = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=True)
    content = db.Column(
        db.Text().with_variant(db.Text(length=2**32-2), 'mysql'),
        nullable=True)
    # Default is pages/templates/default.html
    template_name = db.Column(db.String(70), nullable=True)
    created = db.Column(db.DateTime(), nullable=False, default=datetime.now)
    last_modified = db.Column(db.DateTime(), nullable=False,
                              default=datetime.now, onupdate=datetime.now)

__all__ = ('Page',)
