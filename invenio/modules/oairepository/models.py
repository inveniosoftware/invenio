# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""OAI repository database models."""

from invenio.ext.sqlalchemy import db

from sqlalchemy import event


class OaiREPOSITORY(db.Model):

    """Represents a OaiREPOSITORY record."""

    __tablename__ = 'oaiREPOSITORY'
    id = db.Column(db.MediumInteger(9, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    setName = db.Column(db.String(255), nullable=False,
                        server_default='')
    setSpec = db.Column(db.String(255), nullable=False,
                        server_default='')
    setCollection = db.Column(db.String(255), nullable=False,
                              server_default='')
    setDescription = db.Column(db.Text, nullable=False)
    setDefinition = db.Column(db.Text, nullable=False)
    setRecList = db.Column(db.iLargeBinary, nullable=True)
    last_updated = db.Column(db.DateTime, nullable=False,
                             server_default='1970-01-01 00:00:00')
    p1 = db.Column(db.Text, nullable=False, default='')
    f1 = db.Column(db.Text, nullable=False, default='')
    m1 = db.Column(db.Text, nullable=False, default='')
    p2 = db.Column(db.Text, nullable=False, default='')
    f2 = db.Column(db.Text, nullable=False, default='')
    m2 = db.Column(db.Text, nullable=False, default='')
    p3 = db.Column(db.Text, nullable=False, default='')
    f3 = db.Column(db.Text, nullable=False, default='')
    m3 = db.Column(db.Text, nullable=False, default='')

    @classmethod
    def update_setdefinition_listener(cls, mapper, connection, target):
        """Update setDefinition attribute on before_insert/before_update events."""
        # FIXME: Next two lines
        op1 = ''
        op2 = ''

        # Set fields to empty string if none.
        for attr in ['p1', 'f1', 'm1', 'p2', 'f2', 'm2', 'p3', 'f3', 'm3',
                     'setCollection', 'setName', 'setSpec', 'setDescription']:
            if getattr(target, attr) is None:
                setattr(target, attr, '')

        target.setDefinition = \
            'c=' + target.setCollection + ';' + \
            'p1=' + target.p1 + ';' + \
            'f1=' + target.f1 + ';' + \
            'm1=' + target.m1 + ';' + \
            'op1=' + op1 + ';' + \
            'p2=' + target.p2 + ';' + \
            'f2=' + target.f2 + ';' + \
            'm2=' + target.m2 + ';' + \
            'op2=' + op2 + ';' + \
            'p3=' + target.p3 + ';' + \
            'f3=' + target.f3 + ';' + \
            'm3=' + target.m3 + ';'

# Connect Alchemy event listeners to update setDefinition on INSERT and UPDATE
event.listen(
    OaiREPOSITORY, 'before_insert', OaiREPOSITORY.update_setdefinition_listener
)
event.listen(
    OaiREPOSITORY, 'before_update', OaiREPOSITORY.update_setdefinition_listener
)


__all__ = ('OaiREPOSITORY',)
