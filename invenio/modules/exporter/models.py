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
bibexport database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.

from invenio.modules.accounts.models import User

class ExpJOB(db.Model):
    """Represents a ExpJOB record."""
    __tablename__ = 'expJOB'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True, autoincrement=True)
    jobname = db.Column(db.String(50), nullable=False,
                server_default='', unique=True)
    jobfreq = db.Column(db.MediumInteger(12), nullable=False,
                server_default='0')
    output_format = db.Column(db.MediumInteger(12),
                nullable=False, server_default='0')
    deleted = db.Column(db.MediumInteger(12), nullable=False,
                server_default='0')
    lastrun = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    output_directory = db.Column(db.Text, nullable=True)
    #users = db.relationship(User, secondary=UserExpJOB.__table__,
    #            backref='jobs')

class UserExpJOB(db.Model):
    """Represents a UserExpJOB record."""
    __tablename__ = 'user_expJOB'
    id_user = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(User.id),
                nullable=False, primary_key=True)
    id_expJOB = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(ExpJOB.id),
                nullable=False, primary_key=True)

class ExpJOBRESULT(db.Model):
    """Represents a ExpJOBRESULT record."""
    __tablename__ = 'expJOBRESULT'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True,
                autoincrement=True)
    id_expJOB = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(ExpJOB.id),
                nullable=False)
    execution_time = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    status = db.Column(db.MediumInteger(12), nullable=False,
                server_default='0')
    status_message = db.Column(db.Text, nullable=False)
    job = db.relationship(ExpJOB, backref='jobresults')

class ExpQUERY(db.Model):
    """Represents a ExpQUERY record."""
    __tablename__ = 'expQUERY'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    search_criteria = db.Column(db.Text, nullable=False)
    output_fields = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    deleted = db.Column(db.MediumInteger(12), nullable=False,
                server_default='0')

class ExpJOBExpQUERY(db.Model):
    """Represents a ExpJOBExpQUERY record."""
    __tablename__ = 'expJOB_expQUERY'
    id_expJOB = db.Column(db.Integer(15, unsigned=True),
                    db.ForeignKey(ExpJOB.id), nullable=False,
                    primary_key=True)
    id_expQUERY = db.Column(db.Integer(15, unsigned=True),
                    db.ForeignKey(ExpQUERY.id), nullable=False,
                    primary_key=True)

    query = db.relationship(ExpQUERY, backref='jobs')
    job = db.relationship(ExpJOB, backref='queries')

class ExpQUERYRESULT(db.Model):
    """Represents a ExpQUERYRESULT record."""
    __tablename__ = 'expQUERYRESULT'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True,
                autoincrement=True)
    id_expQUERY = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(ExpQUERY.id),
                nullable=False)
    result = db.Column(db.Text, nullable=False)
    status = db.Column(db.MediumInteger(12), nullable=False,
                server_default='0')
    status_message = db.Column(db.Text, nullable=False)
    query = db.relationship(ExpQUERY, backref='queryresults')
#    jobresults = db.relationship(ExpJOBRESULT,
#            secondary=expJOBRESULT_expQUERYRESULT,
#            backref='queryresults')

class ExpJOBRESULTExpQUERYRESULT(db.Model):
    """Represents a ExpJOBRESULTExpQUERYRESULT record."""
    __tablename__ = 'expJOBRESULT_expQUERYRESULT'
    id_expJOBRESULT = db.Column(db.Integer(15, unsigned=True),
            db.ForeignKey(ExpJOBRESULT.id),
            nullable=False, primary_key=True)
    id_expQUERYRESULT = db.Column(db.Integer(15, unsigned=True),
            db.ForeignKey(ExpQUERYRESULT.id),
            nullable=False, primary_key=True)



__all__ = ['ExpJOB',
           'UserExpJOB',
           'ExpJOBRESULT',
           'ExpQUERY',
           'ExpQUERYRESULT',
           'ExpJOBRESULTExpQUERYRESULT']
