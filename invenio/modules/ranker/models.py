# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014 CERN.
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

"""BibRank database models."""

# General imports.

from flask import g
from invenio.ext.sqlalchemy import db

# Create your models here.

from invenio.modules.accounts.models import User
from invenio.modules.editor.models import Bibdoc
from invenio.modules.records.models import Record as Bibrec
from invenio.modules.collections.models import Collection


class RnkMETHOD(db.Model):

    """Represent a RnkMETHOD record."""

    __tablename__ = 'rnkMETHOD'
    id = db.Column(db.MediumInteger(9, unsigned=True), primary_key=True,
                   nullable=False)
    name = db.Column(db.String(20), unique=True, nullable=False,
                     server_default='')
    last_updated = db.Column(db.DateTime, nullable=False,
                             server_default='1900-01-01 00:00:00')

    def get_name_ln(self, ln=None):
        """Return localized method name."""
        try:
            if ln is None:
                ln = g.ln
            return self.names.filter_by(ln=g.ln, type='ln').one().value
        except:
            return self.name


class RnkMETHODDATA(db.Model):

    """Represent a RnkMETHODDATA record."""

    __tablename__ = 'rnkMETHODDATA'
    id_rnkMETHOD = db.Column(db.MediumInteger(9, unsigned=True),
                             db.ForeignKey(RnkMETHOD.id), primary_key=True)
    relevance_data = db.Column(db.iLargeBinary, nullable=True)


class RnkMETHODNAME(db.Model):

    """Represent a RnkMETHODNAME record."""

    __tablename__ = 'rnkMETHODNAME'
    id_rnkMETHOD = db.Column(db.MediumInteger(9, unsigned=True),
                             db.ForeignKey(RnkMETHOD.id), primary_key=True)
    ln = db.Column(db.Char(5), primary_key=True, server_default='')
    type = db.Column(db.Char(3), primary_key=True, server_default='sn')
    value = db.Column(db.String(255), nullable=False)
    method = db.relationship(RnkMETHOD, backref=db.backref('names',
                                                           lazy='dynamic'))


class RnkCITATIONDICT(db.Model):

    """Represent a RnkCITATIONDICT record."""

    __tablename__ = 'rnkCITATIONDICT'
    citee = db.Column(db.Integer(10, unsigned=True), primary_key=True)
    citer = db.Column(db.Integer(10, unsigned=True), primary_key=True)
    last_updated = db.Column(db.DateTime, nullable=False)
    __table_args__ = (db.Index('rnkCITATIONDICT_reverse', citer, citee),
                      db.Model.__table_args__)

class RnkCITATIONDATAERR(db.Model):

    """Represent a RnkCITATIONDATAERR record."""

    __tablename__ = 'rnkCITATIONDATAERR'
    type = db.Column(db.Enum('multiple-matches', 'not-well-formed',
                             name='rnkcitattiondataerr_type'),
                     primary_key=True)
    citinfo = db.Column(db.String(255), primary_key=True, server_default='')

class RnkCITATIONLOG(db.Model):

    """Represents a RnkCITATIONLOG record."""

    __tablename__ = 'rnkCITATIONLOG'
    id = db.Column(db.Integer(11, unsigned=True), primary_key=True,
                   autoincrement=True, nullable=False)
    citee = db.Column(db.Integer(10, unsigned=True), nullable=False)
    citer = db.Column(db.Integer(10, unsigned=True), nullable=False)
    type = db.Column(db.Enum('added', 'removed', name='rnkcitationlog_type'),
                     nullable=True)
    action_date = db.Column(db.DateTime, nullable=False)
    __table_args__ = (db.Index('citee', citee), db.Index('citer', citer),
                      db.Model.__table_args__)

class RnkCITATIONDATAEXT(db.Model):

    """Represent a RnkCITATIONDATAEXT record."""

    __tablename__ = 'rnkCITATIONDATAEXT'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id), autoincrement=False,
                          primary_key=True, nullable=False, server_default='0')
    extcitepubinfo = db.Column(db.String(255), primary_key=True,
                               nullable=False, index=True)


class RnkAUTHORDATA(db.Model):

    """Represent a RnkAUTHORDATA record."""

    __tablename__ = 'rnkAUTHORDATA'
    aterm = db.Column(db.String(50), primary_key=True, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class RnkDOWNLOADS(db.Model):

    """Represent a RnkDOWNLOADS record."""

    __tablename__ = 'rnkDOWNLOADS'
    id = db.Column(db.Integer, primary_key=True, nullable=False,
                   autoincrement=True)
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id), nullable=True)
    download_time = db.Column(db.DateTime, nullable=True,
                              server_default='1900-01-01 00:00:00')
    client_host = db.Column(db.Integer(10, unsigned=True), nullable=True)
    id_user = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(User.id),
                        nullable=True)
    id_bibdoc = db.Column(db.MediumInteger(9, unsigned=True),
                          db.ForeignKey(Bibdoc.id), nullable=True)
    file_version = db.Column(db.SmallInteger(2, unsigned=True), nullable=True)
    file_format = db.Column(db.String(50), nullable=True)
    bibrec = db.relationship(Bibrec, backref='downloads')
    bibdoc = db.relationship(Bibdoc, backref='downloads')
    user = db.relationship(User, backref='downloads')


class RnkPAGEVIEWS(db.Model):

    """Represent a RnkPAGEVIEWS record."""

    __tablename__ = 'rnkPAGEVIEWS'
    id = db.Column(db.MediumInteger, primary_key=True, nullable=False,
                   autoincrement=True)
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id), nullable=True,
                          primary_key=True)
    id_user = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(User.id),
                        server_default='0', primary_key=True)
    client_host = db.Column(db.Integer(10, unsigned=True), nullable=True)
    view_time = db.Column(db.DateTime, primary_key=True,
                          server_default='1900-01-01 00:00:00')
    bibrec = db.relationship(Bibrec, backref='pageviews')
    user = db.relationship(User, backref='pageviews')


class RnkWORD01F(db.Model):

    """Represent a RnkWORD01F record."""

    __tablename__ = 'rnkWORD01F'
    id = db.Column(db.MediumInteger(9, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    term = db.Column(db.String(50), nullable=True, unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class RnkWORD01R(db.Model):

    """Represent a RnkWORD01R record."""

    __tablename__ = 'rnkWORD01R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id), nullable=False,
                          primary_key=True)
    termlist = db.Column(db.LargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name='rnkword_type'),
                     nullable=False, server_default='CURRENT',
                     primary_key=True)
    bibrec = db.relationship(Bibrec, backref='word01rs')


class RnkEXTENDEDAUTHORS(db.Model):

    """Represent a RnkEXTENDEDAUTHORS record."""

    __tablename__ = 'rnkEXTENDEDAUTHORS'
    id = db.Column(db.Integer(10, unsigned=True), primary_key=True,
                   nullable=False, autoincrement=False)
    authorid = db.Column(db.BigInteger(10), primary_key=True, nullable=False,
                         autoincrement=False)


class RnkRECORDSCACHE(db.Model):

    """Represent a RnkRECORDSCACHE record."""

    __tablename__ = 'rnkRECORDSCACHE'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id), nullable=True,
                          primary_key=True)
    authorid = db.Column(db.BigInteger(10), primary_key=True, nullable=False)


class RnkSELFCITES(db.Model):

    """Represent a RnkSELFCITES record."""

    __tablename__ = 'rnkSELFCITES'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id), nullable=True,
                          primary_key=True)
    count = db.Column(db.Integer(10, unsigned=True), nullable=False)
    references = db.Column(db.Text, nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False)

class RnkSELFCITEDICT(db.Model):

    """Represents a RnkSELFCITEDICT record."""

    __tablename__ = 'rnkSELFCITEDICT'
    citee = db.Column(db.Integer(10, unsigned=True), nullable=False,
                      primary_key=True, autoincrement=False)
    citer = db.Column(db.Integer(10, unsigned=True), nullable=False,
                      primary_key=True, autoincrement=False)
    last_updated = db.Column(db.DateTime, nullable=False)
    __table_args__ = (db.Index('rnkSELFCITEDICT_reverse', citer, citee),
                      db.Model.__table_args__)


class CollectionRnkMETHOD(db.Model):

    """Represent a CollectionRnkMETHOD record."""

    __tablename__ = 'collection_rnkMETHOD'
    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                              db.ForeignKey(Collection.id), primary_key=True,
                              nullable=False)
    id_rnkMETHOD = db.Column(db.MediumInteger(9, unsigned=True),
                             db.ForeignKey(RnkMETHOD.id), primary_key=True,
                             nullable=False)
    score = db.Column(db.TinyInteger(4, unsigned=True), nullable=False,
                      server_default='0')
    collection = db.relationship(Collection, backref='rnkMETHODs')
    rnkMETHOD = db.relationship(RnkMETHOD, backref='collections')


__all__ = ('RnkMETHOD',
           'RnkMETHODDATA',
           'RnkMETHODNAME',
           'RnkCITATIONDICT',
           'RnkCITATIONDATAERR',
           'RnkCITATIONDATAEXT',
           'RnkCITATIONLOG',
           'RnkAUTHORDATA',
           'RnkDOWNLOADS',
           'RnkPAGEVIEWS',
           'RnkWORD01F',
           'RnkWORD01R',
           'RnkEXTENDEDAUTHORS',
           'RnkRECORDSCACHE',
           'RnkSELFCITES',
           'RnkSELFCITEDICT',
           'CollectionRnkMETHOD',
           )
