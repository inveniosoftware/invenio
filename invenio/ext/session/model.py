# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014, 2015 CERN.
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

"""Example implementation of SQLAlchemy session model backend."""

from datetime import datetime
from flask_login import current_user
from invenio.ext.sqlalchemy import db


class Session(db.Model):

    """Represent Session record."""

    __tablename__ = 'session'
    session_key = db.Column(db.String(32), nullable=False,
                            server_default='', primary_key=True)
    session_expiry = db.Column(db.DateTime, nullable=True, index=True)
    session_object = db.Column(db.LargeBinary, nullable=True)
    uid = db.Column(db.Integer(15, unsigned=True), nullable=False, index=True)

    def get_session(self, name, expired=False):
        """Return an instance of :class:`Session`."""
        where = Session.session_key == name
        if expired:
            where = db.and_(
                where, Session.session_expiry >= db.func.current_timestamp())
        return self.query.filter(where).one()

    def set_session(self, name, value, timeout=None):
        """Store value in database."""
        uid = current_user.get_id()
        session_expiry = datetime.utcnow() + timeout
        return Session(session_key=name,
                       session_object=value,
                       session_expiry=session_expiry,
                       uid=uid)
