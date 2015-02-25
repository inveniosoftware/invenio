# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012 CERN.
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
WebLinkBack database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.
from invenio.modules.records.models import Record as Bibrec
from invenio.modules.accounts.models import User

class LnkADMINURL(db.Model):
    """Represents a LnkADMINURL record."""
    __tablename__ = 'lnkADMINURL'

    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                nullable=False)
    url = db.Column(db.String(100), nullable=False, unique=True)
    list = db.Column(db.String(30), nullable=False, index=True)


class LnkENTRY(db.Model):
    """Represents a LnkENTRY record."""
    __tablename__ = 'lnkENTRY'

    id = db.Column(db.Integer(15, unsigned=True), primary_key=True, nullable=False)
    origin_url = db.Column(db.String(100), nullable=False)
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id), nullable=False)
    additional_properties = db.Column(db.Binary)
    type = db.Column(db.String(30), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, server_default='PENDING',
                index=True)
    insert_time = db.Column(db.DateTime, server_default='1900-01-01 00:00:00',
                index=True)

    @property
    def title(self):
        try:
            return db.object_session(self).query(LnkENTRYURLTITLE).\
                filter(db.and_(
                    LnkENTRYURLTITLE.url==self.origin_url,
                    LnkENTRYURLTITLE.title<>"",
                    LnkENTRYURLTITLE.broken==0)).first().title
        except:
            return self.origin_url


class LnkENTRYURLTITLE(db.Model):
    """Represents a LnkENTRYURLTITLE record."""
    __tablename__ = 'lnkENTRYURLTITLE'

    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                nullable=False)
    url = db.Column(db.String(100), nullable=False, unique=True)
    title = db.Column(db.String(100), nullable=False, index=True)
    manual_set = db.Column(db.TinyInteger(1), nullable=False,
                server_default='0')
    broken_count = db.Column(db.Integer(5), server_default='0')
    broken = db.Column(db.TinyInteger(1), nullable=False, server_default='0')


class LnkLOG(db.Model):
    """Represents a LnkLOG record."""
    __tablename__ = 'lnkLOG'

    id = db.Column(db.Integer(15, unsigned=True), primary_key=True, nullable=False)
    id_user = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(User.id))
    action = db.Column(db.String(30), nullable=False, index=True)
    log_time = db.Column(db.DateTime, server_default='1900-01-01 00:00:00',
                index=True)


class LnkENTRYLOG(db.Model):
    """Represents a LnkENTRYLOG record."""
    __tablename__ = 'lnkENTRYLOG'

    id_lnkENTRY = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(LnkENTRY.id), nullable=False, primary_key=True)
    id_lnkLOG = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(LnkLOG.id), nullable=False, primary_key=True)


class LnkADMINURLLOG(db.Model):
    """Represents a LnkADMINURLLOG record."""
    __tablename__ = 'lnkADMINURLLOG'

    id_lnkADMINURL = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(LnkADMINURL.id), primary_key=True, nullable=False)
    id_lnkLOG = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(LnkLOG.id), primary_key=True, nullable=False)


__all__ = [ 'LnkADMINURL',
            'LnkADMINURLLOG',
            'LnkENTRY',
            'LnkENTRYLOG',
            'LnkENTRYURLTITLE',
            'LnkLOG']
