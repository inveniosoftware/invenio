# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013 CERN.
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
bibcirculation database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.

from invenio.modules.records.models import Record as Bibrec


class CrcBORROWER(db.Model):
    """Represents a CrcBORROWER record."""
    def __init__(self):
        pass
    __tablename__ = 'crcBORROWER'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True,
                autoincrement=True)
    ccid = db.Column(db.Integer(15, unsigned=True), nullable=True,
                unique=True, server_default=None)
    name = db.Column(db.String(255), nullable=False,
                server_default='', index=True)
    email = db.Column(db.String(255), nullable=False,
                server_default='', index=True)
    phone = db.Column(db.String(60), nullable=True)
    address = db.Column(db.String(60), nullable=True)
    mailbox = db.Column(db.String(30), nullable=True)
    borrower_since = db.Column(db.DateTime, nullable=False,
        server_default='1900-01-01 00:00:00')
    borrower_until = db.Column(db.DateTime, nullable=False,
        server_default='1900-01-01 00:00:00')
    notes = db.Column(db.Text, nullable=True)

class CrcLIBRARY(db.Model):
    """Represents a CrcLIBRARY record."""
    def __init__(self):
        pass
    __tablename__ = 'crcLIBRARY'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True,
                autoincrement=True)
    name = db.Column(db.String(80), nullable=False,
                server_default='')
    address = db.Column(db.String(255), nullable=False,
                server_default='')
    email = db.Column(db.String(255), nullable=False,
                server_default='')
    phone = db.Column(db.String(30), nullable=False,
                server_default='')
    type = db.Column(db.String(30), nullable=False,
                server_default='main')
    notes = db.Column(db.Text, nullable=True)

class CrcITEM(db.Model):
    """Represents a CrcITEM record."""
    def __init__(self):
        pass
    __tablename__ = 'crcITEM'
    barcode = db.Column(db.String(30), nullable=False,
                server_default='',
                     primary_key=True)
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id), nullable=False,
                server_default='0')
    id_crcLIBRARY = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(CrcLIBRARY.id), nullable=False,
                server_default='0')
    collection = db.Column(db.String(60), nullable=True)
    location = db.Column(db.String(60), nullable=True)
    description = db.Column(db.String(60), nullable=True)
    loan_period = db.Column(db.String(30), nullable=False,
                server_default='')
    status = db.Column(db.String(20), nullable=False,
                server_default='')
    expected_arrival_date = db.Column(db.String(60), nullable=False,
                server_default='')
    creation_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    modification_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    number_of_requests = db.Column(db.Integer(3, unsigned=True),
                nullable=False,server_default='0')


class CrcILLREQUEST(db.Model):
    """Represents a CrcILLREQUEST record."""
    def __init__(self):
        pass
    __tablename__ = 'crcILLREQUEST'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True,
                autoincrement=True)
    id_crcBORROWER = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(CrcBORROWER.id),
                nullable=False,
                server_default='0')
    barcode = db.Column(db.String(30), db.ForeignKey(CrcITEM.barcode),
                nullable=False,
                server_default='')
    period_of_interest_from = db.Column(db.DateTime,
                nullable=False,
                server_default='1900-01-01 00:00:00')
    period_of_interest_to = db.Column(db.DateTime,
                nullable=False,
                server_default='1900-01-01 00:00:00')
    id_crcLIBRARY = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(CrcLIBRARY.id), nullable=False,
                server_default='0')
    request_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    expected_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    arrival_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    due_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    return_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    status = db.Column(db.String(20), nullable=False,
                server_default='')
    cost = db.Column(db.String(30), nullable=False,
                server_default='')
    budget_code = db.Column(db.String(60), nullable=False,
                server_default='')
    item_info = db.Column(db.Text, nullable=True)
    request_type = db.Column(db.Text, nullable=True)
    borrower_comments = db.Column(db.Text, nullable=True)
    only_this_edition = db.Column(db.String(10), nullable=False,
                server_default='')
    library_notes = db.Column(db.Text, nullable=True)
    overdue_letter_number = db.Column(db.Integer(3, unsigned=True),
                                      nullable=False, server_default='0')
    overdue_letter_date = db.Column(db.DateTime, nullable=False,
                                    server_default='1900-01-01 00:00:00')
    borrower = db.relationship(CrcBORROWER, backref='illrequests')
    item = db.relationship(CrcITEM, backref='illrequests')
    library = db.relationship(CrcLIBRARY, backref='illrequests')


class CrcLOAN(db.Model):
    """Represents a CrcLOAN record."""
    def __init__(self):
        pass
    __tablename__ = 'crcLOAN'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True,
                autoincrement=True)
    id_crcBORROWER = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(CrcBORROWER.id), nullable=False, server_default='0')
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                nullable=False, server_default='0')
    barcode = db.Column(db.String(30), db.ForeignKey(CrcITEM.barcode), nullable=False,
                server_default='')
    loaned_on = db.Column(db.DateTime, nullable=False,
        server_default='1900-01-01 00:00:00')
    returned_on = db.Column(db.Date, nullable=True)
    due_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    number_of_renewals = db.Column(db.Integer(3, unsigned=True), nullable=False,
                server_default='0')
    overdue_letter_number = db.Column(db.Integer(3, unsigned=True), nullable=False,
                server_default='0')
    overdue_letter_date = db.Column(db.DateTime,
                nullable=False,
                server_default='1900-01-01 00:00:00')
    status = db.Column(db.String(20), nullable=False,
                server_default='')
    type = db.Column(db.String(20), nullable=False,
                server_default='')
    notes = db.Column(db.Text, nullable=True)
    borrower = db.relationship(CrcBORROWER, backref='loans')
    bibrec = db.relationship(Bibrec, backref='loans')
    item = db.relationship(CrcITEM, backref='loans')

class CrcLOANREQUEST(db.Model):
    """Represents a CrcLOANREQUEST record."""
    def __init__(self):
        pass
    __tablename__ = 'crcLOANREQUEST'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True,
                autoincrement=True)
    id_crcBORROWER = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(CrcBORROWER.id), nullable=False, server_default='0')
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                nullable=False, server_default='0')
    barcode = db.Column(db.String(30), db.ForeignKey(CrcITEM.barcode), nullable=False,
                server_default='')
    period_of_interest_from = db.Column(db.DateTime,
                nullable=False,
                server_default='1900-01-01 00:00:00')
    period_of_interest_to = db.Column(db.DateTime,
                nullable=False,
                server_default='1900-01-01 00:00:00')
    status = db.Column(db.String(20), nullable=False,
                server_default='')
    notes = db.Column(db.Text, nullable=True)
    request_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    borrower = db.relationship(CrcBORROWER, backref='loanrequests')
    bibrec = db.relationship(Bibrec, backref='loanrequests')
    item = db.relationship(CrcITEM, backref='loanrequests')

class CrcVENDOR(db.Model):
    """Represents a CrcVENDOR record."""
    def __init__(self):
        pass
    __tablename__ = 'crcVENDOR'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True,
                autoincrement=True)
    name = db.Column(db.String(80), nullable=False,
                server_default='')
    address = db.Column(db.String(255), nullable=False,
                server_default='')
    email = db.Column(db.String(255), nullable=False,
                server_default='')
    phone = db.Column(db.String(30), nullable=False,
                server_default='')
    notes = db.Column(db.Text, nullable=True)

class CrcPURCHASE(db.Model):
    """Represents a CrcPURCHASE record."""
    def __init__(self):
        pass
    __tablename__ = 'crcPURCHASE'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True,
                autoincrement=True)
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                nullable=False, server_default='0')
    id_crcVENDOR = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(CrcVENDOR.id), nullable=False, server_default='0')
    ordered_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    expected_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    price = db.Column(db.String(20), nullable=False,
                server_default='0')
    status = db.Column(db.String(20), nullable=False,
                server_default='')
    notes = db.Column(db.Text, nullable=True)
    bibrec = db.relationship(Bibrec, backref='purchases')
    vendor = db.relationship(CrcVENDOR, backref='purchases')


__all__ = ['CrcBORROWER',
           'CrcLIBRARY',
           'CrcITEM',
           'CrcILLREQUEST',
           'CrcLOAN',
           'CrcLOANREQUEST',
           'CrcVENDOR',
           'CrcPURCHASE']
