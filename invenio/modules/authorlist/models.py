# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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
AuthorList database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.


class AulPAPERS(db.Model):

    """Represents an AulPAPERS record."""

    __tablename__ = 'aulPAPERS'
    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                   nullable=False, autoincrement=True)
    id_user = db.Column(db.Integer(15, unsigned=True), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    collaboration = db.Column(db.String(255), nullable=False)
    experiment_number = db.Column(db.String(255), nullable=False)
    last_modified = db.Column(db.Integer(10, unsigned=True),
                              nullable=False)
    __table_args__ = (db.Index(__tablename__+'_id_user', id_user), db.Model.__table_args__)


class AulREFERENCES(db.Model):

    """Represents an AulREFERENCES record."""

    __tablename__ = 'aulREFERENCES'
    item = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                     nullable=False, autoincrement=True)
    reference = db.Column(db.String(120), nullable=False)
    paper_id = db.Column(db.Integer(15, unsigned=True),
                         db.ForeignKey(AulPAPERS.id), primary_key=True,
                         nullable=False)
    __table_args__ = (db.Index(__tablename__+'_paper_id', paper_id), db.Index(__tablename__+'_item', item),
                      db.Model.__table_args__)


class AulAFFILIATIONS(db.Model):

    """Represents an AulAFFILIATIONS record."""

    __tablename__ = 'aulAFFILIATIONS'
    item = db.Column(db.Integer(15, unsigned=True), nullable=False,
                     primary_key=True, autoincrement=True)
    acronym = db.Column(db.String(120), nullable=False)
    umbrella = db.Column(db.String(120), nullable=False)
    name_and_address = db.Column(db.String(255), nullable=False)
    domain = db.Column(db.String(120), nullable=False)
    member = db.Column(db.TinyInteger(1), nullable=False)
    spires_id = db.Column(db.String(60), nullable=False)
    paper_id = db.Column(db.Integer(15, unsigned=True),
                         db.ForeignKey(AulPAPERS.id), primary_key=True,
                         nullable=False)
    __table_args__ = (db.Index(__tablename__+'_acronym', acronym), db.Index(__tablename__+'_item', item),
                      db.Index(__tablename__+'_paper_id', paper_id), db.Model.__table_args__)


class AulAUTHORS(db.Model):

    """Represents an AulAUTHORS record."""

    __tablename__ = 'aulAUTHORS'
    item = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                     nullable=False, autoincrement=True)
    family_name = db.Column(db.String(255), nullable=False)
    given_name = db.Column(db.String(255), nullable=False)
    name_on_paper = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    paper_id = db.Column(db.Integer(15, unsigned=True),
                         db.ForeignKey(AulPAPERS.id), primary_key=True,
                         nullable=False)
    __table_args__ = (db.Index(__tablename__+'_item', item), db.Index(__tablename__+'_paper_id', paper_id),
                      db.Model.__table_args__)


class AulAUTHORAFFILIATIONS(db.Model):

    """Represents an AulAUTHOR_AFFILIATIONS record."""

    __tablename__ = 'aulAUTHOR_AFFILIATIONS'
    item = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                     nullable=False)
    affiliation_acronym = db.Column(db.String(120), nullable=False)
    affiliation_status = db.Column(db.String(120), nullable=False)
    author_item = db.Column(db.Integer(15, unsigned=True),
                            primary_key=True, nullable=False)
    paper_id = db.Column(db.Integer(15, unsigned=True),
                         db.ForeignKey(AulPAPERS.id), primary_key=True,
                         nullable=False)
    __table_args__ = (db.Index(__tablename__+'_author_item', author_item),
                      db.Index(__tablename__+'_item', item),
                      db.Index(__tablename__+'_paper_id', paper_id), db.Model.__table_args__)


class AulAUTHORIDENTIFIERS(db.Model):

    """Represents an AulAUTHOR_IDENTIFIERS record."""

    __tablename__ = 'aulAUTHOR_IDENTIFIERS'
    item = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                     nullable=False)
    identifier_number = db.Column(db.String(120), nullable=False)
    identifier_name = db.Column(db.String(120), nullable=False)
    author_item = db.Column(db.Integer(15, unsigned=True),
                            primary_key=True, nullable=False)
    paper_id = db.Column(db.Integer(15, unsigned=True),
                         db.ForeignKey(AulPAPERS.id), primary_key=True,
                         nullable=False)
    __table_args__ = (db.Index(__tablename__+'_item', item), db.Index(__tablename__+'_paper_id', paper_id),
                      db.Index(__tablename__+'_author_item', author_item),
                      db.Model.__table_args__)

__all__ = ['AulPAPERS',
           'AulREFERENCES',
           'AulAFFILIATIONS',
           'AulAUTHORS',
           'AulAUTHORAFFILIATIONS',
           'AulAUTHORIDENTIFIERS']
