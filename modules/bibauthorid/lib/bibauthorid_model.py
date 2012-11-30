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
bibauthorid database models.
"""

# General imports.
from invenio.sqlalchemyutils import db

# Create your models here.

#FIX ME Add db.relationships

class AidCACHE(db.Model):
    """Represents a AidCACHE record."""
    __tablename__ = 'aidCACHE'
    id = db.Column(db.Integer(15), nullable=False,
                primary_key=True,
                autoincrement=True)
    object_name = db.Column(db.String(120), nullable=False,
                index=True)
    object_key = db.Column(db.String(120), nullable=False,
                index=True)
    object_value = db.Column(db.Text, nullable=True)
    last_updated = db.Column(db.DateTime, nullable=False,
                index=True)


class AidUSERINPUTLOG(db.Model):
    """Represents a AidUSERINPUTLOG record."""
    __tablename__ = 'aidUSERINPUTLOG'
    id = db.Column(db.BigInteger(15), nullable=False,
                primary_key=True,
                autoincrement=True)
    transactionid = db.Column(db.BigInteger(15), nullable=False,
                primary_key=True,
            autoincrement=True, index=True)
    timestamp = db.Column(db.DateTime, nullable=False,
                index=True)
    userinfo = db.Column(db.String(255), nullable=False,
                index=True)
    personid = db.Column(db.BigInteger(15), nullable=False,
                primary_key=True,
            autoincrement=True, index=True)
    action = db.Column(db.String(50), nullable=False,
                index=True)
    tag = db.Column(db.String(50), nullable=False,
                index=True)
    value = db.Column(db.String(200), nullable=False,
                index=True)
    comment = db.Column(db.Text, nullable=True)


class AidPERSONIDDATA(db.Model):
    """Represents a AidPERSONIDDATA record."""

    __tablename__ = 'aidPERSONIDDATA'

    personid = db.Column(db.BigInteger, primary_key=True, nullable=False)
    tag = db.Column(db.String(64), primary_key=True, nullable=False)
    data = db.Column(db.String(256), nullable=False)
    opt1 = db.Column(db.Integer)
    opt2 = db.Column(db.Integer)
    opt3 = db.Column(db.String(256))


class AidPERSONIDPAPERS(db.Model):
    """Represents a AidPERSONIDPAPERS record."""

    __tablename__ = 'aidPERSONIDPAPERS'

    personid = db.Column(db.BigInteger, primary_key=True, nullable=False)
    bibref_table = db.Column(db.Enum('100', '700'), primary_key=True, nullable=False)
    bibref_value = db.Column(db.Integer, primary_key=True, nullable=False)
    bibrec = db.Column(db.MediumInteger(8, unsigned=True), primary_key=True, nullable=False)
    name = db.Column(db.String(256), nullable=False)
    flag = db.Column(db.SmallInteger, nullable=False)
    lcul = db.Column(db.SmallInteger, nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False)


class AidRESULTS(db.Model):
    """Represents a AidRESULTS record."""

    __tablename__ = 'aidRESULTS'

    personid = db.Column(db.String(128), primary_key=True, nullable=False,
                    index=True)
    bibref_table = db.Column(db.Enum('100', '700'), primary_key=True,
                    nullable=False, index=True)
    bibref_value = db.Column(db.MediumInteger(8, unsigned=True),
                    primary_key=True, nullable=False, index=True,
                    autoincrement=False)
    bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                    primary_key=True, nullable=False, index=True,
                    autoincrement=False)


__all__ = [
           'AidCACHE',
           'AidPERSONIDDATA',
           'AidPERSONIDPAPERS',
           'AidRESULTS',
           'AidUSERINPUTLOG',
           ]

