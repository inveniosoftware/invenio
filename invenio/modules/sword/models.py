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
bibsword database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.

from invenio.modules.accounts.models import User
from invenio.modules.records.models import Record as Bibrec

class SwrREMOTESERVER(db.Model):
    """Represents a SwrREMOTESERVER record."""
    def __init__(self):
        pass
    __tablename__ = 'swrREMOTESERVER'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    host = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    realm = db.Column(db.String(50), nullable=False)
    url_base_record = db.Column(db.String(50), nullable=False)
    url_servicedocument = db.Column(db.String(80),
                nullable=False)
    xml_servicedocument = db.Column(db.LargeBinary,
                nullable=True)
    last_update = db.Column(db.Integer(15, unsigned=True),
                nullable=False)

class SwrCLIENTDATA(db.Model):
    """Represents a SwrCLIENTDATA record."""
    def __init__(self):
        pass
    __tablename__ = 'swrCLIENTDATA'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True,
                autoincrement=True)
    id_swrREMOTESERVER = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(SwrREMOTESERVER.id),
                nullable=False)
    id_record = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                nullable=False)
    report_no = db.Column(db.String(50), nullable=False)
    id_remote = db.Column(db.String(50), nullable=False)
    id_user = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(User.id),
                nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(100), nullable=False)
    xml_media_deposit = db.Column(db.LargeBinary,
                nullable=False)
    xml_metadata_submit = db.Column(db.LargeBinary,
                nullable=False)
    submission_date = db.Column(db.DateTime, nullable=False,
        server_default='1900-01-01 00:00:00')
    publication_date = db.Column(db.DateTime, nullable=False,
        server_default='1900-01-01 00:00:00')
    removal_date = db.Column(db.DateTime, nullable=False,
        server_default='1900-01-01 00:00:00')
    link_medias = db.Column(db.String(150), nullable=False)
    link_metadata = db.Column(db.String(150), nullable=False)
    link_status = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(150), nullable=False,
                server_default='submitted')
    last_update = db.Column(db.DateTime, nullable=False)
    remoteserver = db.relationship(SwrREMOTESERVER,
                backref='clientdata')
    user = db.relationship(User, backref='clientdata')
    bibrec = db.relationship(Bibrec)

__all__ = ['SwrREMOTESERVER',
           'SwrCLIENTDATA']
