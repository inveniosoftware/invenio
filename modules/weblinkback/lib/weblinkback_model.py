# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02D111-1307, USA.

"""
WebLinkBack database models.
"""

# General imports.
from invenio.sqlalchemyutils import db

# Create your models here.

class LnkADMINURL(db.Model):
    """Represents a LnkADMINURL record."""
    __tablename__ = 'lnkADMINURL'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    url = db.Column(db.String, nullable=False)
    list = db.Column(db.String, nullable=False)


class LnkADMINURLLOG(db.Model):
    """Represents a LnkADMINURLLOG record."""
    __tablename__ = 'lnkADMINURLLOG'

    id_lnkADMINURL = db.Column(db.Integer, nullable=False, primary_key=True)
    id_lnkLOG = db.Column(db.Integer, nullable=False, primary_key=True)


class LnkENTRY(db.Model):
    """Represents a LnkENTRY record."""
    __tablename__ = 'lnkENTRY'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    origin_url = db.Column(db.String, nullable=False)
    id_bibrec = db.Column(db.Integer, nullable=False)
    additional_properties = db.Column(db.Binary)
    type = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    insert_time = db.Column(db.DateTime)

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


class LnkENTRYLOG(db.Model):
    """Represents a LnkENTRYLOG record."""
    __tablename__ = 'lnkENTRYLOG'

    id_lnkENTRY = db.Column(db.Integer, nullable=False, primary_key=True)
    id_lnkLOG = db.Column(db.Integer, nullable=False, primary_key=True)


class LnkENTRYURLTITLE(db.Model):
    """Represents a LnkENTRYURLTITLE record."""
    __tablename__ = 'lnkENTRYURLTITLE'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    url = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    manual_set = db.Column(db.Integer, nullable=False)
    broken_count = db.Column(db.Integer)
    broken = db.Column(db.Integer, nullable=False)


class LnkLOG(db.Model):
    """Represents a LnkLOG record."""
    __tablename__ = 'lnkLOG'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    id_user = db.Column(db.Integer)
    action = db.Column(db.String, nullable=False)
    log_time = db.Column(db.DateTime)

__all__ = [ 'LnkADMINURL',
            'LnkADMINURLLOG',
            'LnkENTRY',
            'LnkENTRYLOG',
            'LnkENTRYURLTITLE',
            'LnkLOG']
