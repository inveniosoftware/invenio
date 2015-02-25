# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2014 CERN.
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
bibsched database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.
from invenio.modules.sequencegenerator.models import SeqSTORE


class HstTASK(db.Model):
    """Represents a HstTASK record."""

    __tablename__ = 'hstTASK'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=False)
    proc = db.Column(db.String(255), nullable=False)
    host = db.Column(db.String(255), nullable=False,
                     server_default='')
    user = db.Column(db.String(50), nullable=False)
    runtime = db.Column(db.DateTime, nullable=False, index=True)
    sleeptime = db.Column(db.String(20), nullable=True)
    arguments = db.Column(db.iMediumBinary, nullable=True)
    status = db.Column(db.String(50), nullable=True, index=True)
    progress = db.Column(db.String(255), nullable=True)
    priority = db.Column(db.TinyInteger(4), nullable=False,
                         server_default='0', index=True)
    sequenceid = db.Column(db.Integer(15, unsigned=True),
                           db.ForeignKey(SeqSTORE.id))


class SchTASK(db.Model):
    """Represents a SchTASK record."""

    def __init__(self):
        pass
    __tablename__ = 'schTASK'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    proc = db.Column(db.String(255), nullable=False)
    host = db.Column(db.String(255), nullable=False,
                     server_default='')
    user = db.Column(db.String(50), nullable=False)
    runtime = db.Column(db.DateTime, nullable=False, index=True)
    sleeptime = db.Column(db.String(20), nullable=True)
    arguments = db.Column(db.iMediumBinary, nullable=True)
    status = db.Column(db.String(50), nullable=True, index=True)
    progress = db.Column(db.String(255), nullable=True)
    priority = db.Column(db.TinyInteger(4), nullable=False,
                         server_default='0', index=True)
    sequenceid = db.Column(db.Integer(15, unsigned=True),
                           db.ForeignKey(SeqSTORE.id))


# FIXME To be moved to redis when available
class SchSTATUS(db.Model):

    """Represent a SchSTATUS record."""

    __tablename__ = 'schSTATUS'

    name = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.iMediumBinary)


__all__ = ['HstTASK',
           'SchTASK',
           'SchSTATUS',
           ]
