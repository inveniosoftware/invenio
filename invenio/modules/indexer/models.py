# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013, 2014 CERN.
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
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Define database models for native indexer."""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.

from invenio.modules.records.models import Record as Bibrec
from invenio.modules.search.models import Field


class IdxINDEX(db.Model):

    """Represent a IdxINDEX record."""

    __tablename__ = 'idxINDEX'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False,
                     server_default='')
    description = db.Column(db.String(255), nullable=False,
                            server_default='')
    last_updated = db.Column(db.DateTime, nullable=False,
                             server_default='1900-01-01 00:00:00')
    stemming_language = db.Column(db.String(10), nullable=False,
                                  server_default='')
    indexer = db.Column(db.String(10), nullable=False, server_default='native')
    synonym_kbrs = db.Column(db.String(255), nullable=False, server_default='')
    remove_stopwords = db.Column(
        db.String(255), nullable=False, server_default='')
    remove_html_markup = db.Column(
        db.String(10), nullable=False, server_default='')
    remove_latex_markup = db.Column(
        db.String(10), nullable=False, server_default='')
    tokenizer = db.Column(db.String(50), nullable=False, server_default='')


class IdxINDEXIdxINDEX(db.Model):

    """Represent an IdxINDEXIdxINDEX record."""

    __tablename__ = 'idxINDEX_idxINDEX'
    id_virtual = db.Column(db.MediumInteger(9, unsigned=True),
                           db.ForeignKey(IdxINDEX.id), nullable=False,
                           server_default='0', primary_key=True)
    id_normal = db.Column(db.MediumInteger(9, unsigned=True),
                          db.ForeignKey(IdxINDEX.id), nullable=False,
                          server_default='0', primary_key=True)


class IdxINDEXNAME(db.Model):

    """Represent a IdxINDEXNAME record."""

    __tablename__ = 'idxINDEXNAME'
    id_idxINDEX = db.Column(db.MediumInteger(9, unsigned=True),
                            db.ForeignKey(IdxINDEX.id), primary_key=True)
    ln = db.Column(db.Char(5), primary_key=True,
                   server_default='')
    type = db.Column(db.Char(3), primary_key=True,
                     server_default='sn')
    value = db.Column(db.String(255), nullable=False)
    idxINDEX = db.relationship(IdxINDEX, backref='names')


class IdxINDEXField(db.Model):

    """Represent a IdxINDEXField record."""

    __tablename__ = 'idxINDEX_field'
    id_idxINDEX = db.Column(db.MediumInteger(9, unsigned=True),
                            db.ForeignKey(IdxINDEX.id), primary_key=True)
    id_field = db.Column(db.MediumInteger(9, unsigned=True),
                         db.ForeignKey(Field.id), primary_key=True)
    regexp_punctuation = db.Column(db.String(255),
                                   nullable=False,
                                   server_default='[.,:;?!"]')
    regexp_alphanumeric_separators = db.Column(db.String(255),
                                               nullable=False)  # FIX ME ,
    #server_default='[!"#$\\%&''()*+,-./:;<=>?@[\\]^\\_`{|}~]')
    idxINDEX = db.relationship(IdxINDEX, backref='fields')
    field = db.relationship(Field, backref='idxINDEXes')

#GENERATED


class IdxPAIR01F(db.Model):

    """Represent a IdxPAIR01F record."""

    __tablename__ = 'idxPAIR01F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR01R(db.Model):

    """Represent a IdxPAIR01R record."""

    __tablename__ = 'idxPAIR01R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR01Q(db.Model):

    """Represent a IdxPAIR01Q record."""

    __tablename__ = 'idxPAIR01Q'

    id = db.Column(db.MediumInteger(10, unsigned=True),
                   primary_key=True, autoincrement=True)
    runtime = db.Column(db.DateTime, nullable=False, index=True,
                        server_default='0001-01-01 00:00:00')
    id_bibrec_low = db.Column(db.MediumInteger(9, unsigned=True),
                              nullable=False)
    id_bibrec_high = db.Column(db.MediumInteger(9, unsigned=True),
                               nullable=False)
    index_name = db.Column(db.String(50), nullable=False, server_default='',
                           index=True)
    mode = db.Column(db.String(50), nullable=False, server_default='update')


class IdxPAIR02F(db.Model):

    """Represent a IdxPAIR02F record."""

    __tablename__ = 'idxPAIR02F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR02R(db.Model):

    """Represent a IdxPAIR02R record."""

    __tablename__ = 'idxPAIR02R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR03F(db.Model):

    """Represent a IdxPAIR03F record."""

    __tablename__ = 'idxPAIR03F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR03R(db.Model):

    """Represent a IdxPAIR03R record."""

    __tablename__ = 'idxPAIR03R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR04F(db.Model):

    """Represent a IdxPAIR04F record."""

    __tablename__ = 'idxPAIR04F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR04R(db.Model):

    """Represent a IdxPAIR04R record."""

    __tablename__ = 'idxPAIR04R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR05F(db.Model):

    """Represent a IdxPAIR05F record."""

    __tablename__ = 'idxPAIR05F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR05R(db.Model):

    """Represent a IdxPAIR05R record."""

    __tablename__ = 'idxPAIR05R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR06F(db.Model):

    """Represent a IdxPAIR06F record."""

    __tablename__ = 'idxPAIR06F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR06R(db.Model):

    """Represent a IdxPAIR06R record."""

    __tablename__ = 'idxPAIR06R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR07F(db.Model):

    """Represent a IdxPAIR07F record."""

    __tablename__ = 'idxPAIR07F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR07R(db.Model):

    """Represent a IdxPAIR07R record."""

    __tablename__ = 'idxPAIR07R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR08F(db.Model):

    """Represent a IdxPAIR08F record."""

    __tablename__ = 'idxPAIR08F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR08R(db.Model):

    """Represent a IdxPAIR08R record."""

    __tablename__ = 'idxPAIR08R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR09F(db.Model):

    """Represent a IdxPAIR09F record."""

    __tablename__ = 'idxPAIR09F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR09R(db.Model):

    """Represent a IdxPAIR09R record."""

    __tablename__ = 'idxPAIR09R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR10F(db.Model):

    """Represent a IdxPAIR10F record."""

    __tablename__ = 'idxPAIR10F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR10R(db.Model):

    """Represent a IdxPAIR10R record."""

    __tablename__ = 'idxPAIR10R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR11F(db.Model):

    """Represent a IdxPAIR11F record."""

    __tablename__ = 'idxPAIR11F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR11R(db.Model):

    """Represent a IdxPAIR11R record."""

    __tablename__ = 'idxPAIR11R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR12F(db.Model):

    """Represent a IdxPAIR12F record."""

    __tablename__ = 'idxPAIR12F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR12R(db.Model):

    """Represent a IdxPAIR12R record."""

    __tablename__ = 'idxPAIR12R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR13F(db.Model):

    """Represent a IdxPAIR13F record."""

    __tablename__ = 'idxPAIR13F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR13R(db.Model):

    """Represent a IdxPAIR13R record."""

    __tablename__ = 'idxPAIR13R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR14F(db.Model):

    """Represent a IdxPAIR14F record."""

    __tablename__ = 'idxPAIR14F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR14R(db.Model):

    """Represent a IdxPAIR14R record."""

    __tablename__ = 'idxPAIR14R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR15F(db.Model):

    """Represent a IdxPAIR15F record."""

    __tablename__ = 'idxPAIR15F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR15R(db.Model):

    """Represent a IdxPAIR15R record."""

    __tablename__ = 'idxPAIR15R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR16F(db.Model):

    """Represent a IdxPAIR16F record."""

    __tablename__ = 'idxPAIR16F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR16R(db.Model):

    """Represent a IdxPAIR16R record."""

    __tablename__ = 'idxPAIR16R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR17F(db.Model):

    """Represent a IdxPAIR17F record."""

    __tablename__ = 'idxPAIR17F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR17R(db.Model):

    """Represent a IdxPAIR17R record."""

    __tablename__ = 'idxPAIR17R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR18F(db.Model):

    """Represent a IdxPAIR18F record."""

    __tablename__ = 'idxPAIR18F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR18R(db.Model):

    """Represent a IdxPAIR18R record."""

    __tablename__ = 'idxPAIR18R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR19F(db.Model):

    """Represent a IdxPAIR19F record."""

    __tablename__ = 'idxPAIR19F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR19R(db.Model):

    """Represent a IdxPAIR19R record."""

    __tablename__ = 'idxPAIR19R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR20F(db.Model):

    """Represent a IdxPAIR20F record."""

    __tablename__ = 'idxPAIR20F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR20R(db.Model):

    """Represent a IdxPAIR20R record."""

    __tablename__ = 'idxPAIR20R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR21F(db.Model):

    """Represent a IdxPAIR21F record."""

    __tablename__ = 'idxPAIR21F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR21R(db.Model):

    """Represent a IdxPAIR21R record."""

    __tablename__ = 'idxPAIR21R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR22F(db.Model):

    """Represent a IdxPAIR22F record."""

    __tablename__ = 'idxPAIR22F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR22R(db.Model):

    """Represent a IdxPAIR22R record."""

    __tablename__ = 'idxPAIR22R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR23F(db.Model):

    """Represent a IdxPAIR23F record."""

    __tablename__ = 'idxPAIR23F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR23R(db.Model):

    """Represent a IdxPAIR23R record."""

    __tablename__ = 'idxPAIR23R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR24F(db.Model):

    """Represent a IdxPAIR24F record."""

    __tablename__ = 'idxPAIR24F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR24R(db.Model):

    """Represent a IdxPAIR24R record."""

    __tablename__ = 'idxPAIR24R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR25F(db.Model):

    """Represent a IdxPAIR25F record."""

    __tablename__ = 'idxPAIR25F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR25R(db.Model):

    """Represent a IdxPAIR25R record."""

    __tablename__ = 'idxPAIR25R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR26F(db.Model):

    """Represent a IdxPAIR26F record."""

    __tablename__ = 'idxPAIR26F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR26R(db.Model):

    """Represent a IdxPAIR26R record."""

    __tablename__ = 'idxPAIR26R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR27F(db.Model):

    """Represent a IdxPAIR27F record."""

    __tablename__ = 'idxPAIR27F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR27R(db.Model):

    """Represent a IdxPAIR27R record."""

    __tablename__ = 'idxPAIR27R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPAIR28F(db.Model):

    """Represent a IdxPAIR28F record."""

    __tablename__ = 'idxPAIR28F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR28R(db.Model):

    """Represent a IdxPAIR28R record."""

    __tablename__ = 'idxPAIR28R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE01F(db.Model):

    """Represent a IdxPHRASE01F record."""

    __tablename__ = 'idxPHRASE01F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE01R(db.Model):

    """Represent a IdxPHRASE01R record."""

    __tablename__ = 'idxPHRASE01R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE01Q(db.Model):

    """Represent a IdxPHRASE01Q record."""

    __tablename__ = 'idxPHRASE01Q'

    id = db.Column(db.MediumInteger(10, unsigned=True),
                   primary_key=True, autoincrement=True)
    runtime = db.Column(db.DateTime, nullable=False, index=True,
                        server_default='0001-01-01 00:00:00')
    id_bibrec_low = db.Column(db.MediumInteger(9, unsigned=True),
                              nullable=False)
    id_bibrec_high = db.Column(db.MediumInteger(9, unsigned=True),
                               nullable=False)
    index_name = db.Column(db.String(50), nullable=False, server_default='',
                           index=True)
    mode = db.Column(db.String(50), nullable=False, server_default='update')


class IdxPHRASE02F(db.Model):

    """Represent a IdxPHRASE02F record."""

    __tablename__ = 'idxPHRASE02F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE02R(db.Model):

    """Represent a IdxPHRASE02R record."""

    __tablename__ = 'idxPHRASE02R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE03F(db.Model):

    """Represent a IdxPHRASE03F record."""

    __tablename__ = 'idxPHRASE03F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE03R(db.Model):

    """Represent a IdxPHRASE03R record."""

    __tablename__ = 'idxPHRASE03R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE04F(db.Model):

    """Represent a IdxPHRASE04F record."""

    __tablename__ = 'idxPHRASE04F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE04R(db.Model):

    """Represent a IdxPHRASE04R record."""

    __tablename__ = 'idxPHRASE04R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE05F(db.Model):

    """Represent a IdxPHRASE05F record."""

    __tablename__ = 'idxPHRASE05F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE05R(db.Model):

    """Represent a IdxPHRASE05R record."""

    __tablename__ = 'idxPHRASE05R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE06F(db.Model):

    """Represent a IdxPHRASE06F record."""

    __tablename__ = 'idxPHRASE06F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE06R(db.Model):

    """Represent a IdxPHRASE06R record."""

    __tablename__ = 'idxPHRASE06R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE07F(db.Model):

    """Represent a IdxPHRASE07F record."""

    __tablename__ = 'idxPHRASE07F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE07R(db.Model):

    """Represent a IdxPHRASE07R record."""

    __tablename__ = 'idxPHRASE07R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE08F(db.Model):

    """Represent a IdxPHRASE08F record."""

    __tablename__ = 'idxPHRASE08F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE08R(db.Model):

    """Represent a IdxPHRASE08R record."""

    __tablename__ = 'idxPHRASE08R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE09F(db.Model):

    """Represent a IdxPHRASE09F record."""

    __tablename__ = 'idxPHRASE09F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE09R(db.Model):

    """Represent a IdxPHRASE09R record."""

    __tablename__ = 'idxPHRASE09R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE10F(db.Model):

    """Represent a IdxPHRASE10F record."""

    __tablename__ = 'idxPHRASE10F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE10R(db.Model):

    """Represent a IdxPHRASE10R record."""

    __tablename__ = 'idxPHRASE10R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE11F(db.Model):

    """Represent a IdxPHRASE11F record."""

    __tablename__ = 'idxPHRASE11F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE11R(db.Model):

    """Represent a IdxPHRASE11R record."""

    __tablename__ = 'idxPHRASE11R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE12F(db.Model):

    """Represent a IdxPHRASE12F record."""

    __tablename__ = 'idxPHRASE12F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE12R(db.Model):

    """Represent a IdxPHRASE12R record."""

    __tablename__ = 'idxPHRASE12R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE13F(db.Model):

    """Represent a IdxPHRASE13F record."""

    __tablename__ = 'idxPHRASE13F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE13R(db.Model):

    """Represent a IdxPHRASE13R record."""

    __tablename__ = 'idxPHRASE13R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE14F(db.Model):

    """Represent a IdxPHRASE14F record."""

    __tablename__ = 'idxPHRASE14F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE14R(db.Model):

    """Represent a IdxPHRASE14R record."""

    __tablename__ = 'idxPHRASE14R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE15F(db.Model):

    """Represent a IdxPHRASE15F record."""

    __tablename__ = 'idxPHRASE15F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE15R(db.Model):

    """Represent a IdxPHRASE15R record."""

    __tablename__ = 'idxPHRASE15R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE16F(db.Model):

    """Represent a IdxPHRASE16F record."""

    __tablename__ = 'idxPHRASE16F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE16R(db.Model):

    """Represent a IdxPHRASE16R record."""

    __tablename__ = 'idxPHRASE16R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE17F(db.Model):

    """Represent a IdxPHRASE17F record."""

    __tablename__ = 'idxPHRASE17F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE17R(db.Model):

    """Represent a IdxPHRASE17R record."""

    __tablename__ = 'idxPHRASE17R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE18F(db.Model):

    """Represent a IdxPHRASE18F record."""

    __tablename__ = 'idxPHRASE18F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE18R(db.Model):

    """Represent a IdxPHRASE18R record."""

    __tablename__ = 'idxPHRASE18R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE19F(db.Model):

    """Represent a IdxPHRASE19F record."""

    __tablename__ = 'idxPHRASE19F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE19R(db.Model):

    """Represent a IdxPHRASE19R record."""

    __tablename__ = 'idxPHRASE19R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE20F(db.Model):

    """Represent a IdxPHRASE20F record."""

    __tablename__ = 'idxPHRASE20F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE20R(db.Model):

    """Represent a IdxPHRASE20R record."""

    __tablename__ = 'idxPHRASE20R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE21F(db.Model):

    """Represent a IdxPHRASE21F record."""

    __tablename__ = 'idxPHRASE21F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE21R(db.Model):

    """Represent a IdxPHRASE21R record."""

    __tablename__ = 'idxPHRASE21R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE22F(db.Model):

    """Represent a IdxPHRASE22F record."""

    __tablename__ = 'idxPHRASE22F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE22R(db.Model):

    """Represent a IdxPHRASE22R record."""

    __tablename__ = 'idxPHRASE22R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE23F(db.Model):

    """Represent a IdxPHRASE23F record."""

    __tablename__ = 'idxPHRASE23F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE23R(db.Model):

    """Represent a IdxPHRASE23R record."""

    __tablename__ = 'idxPHRASE23R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE24F(db.Model):

    """Represent a IdxPHRASE24F record."""

    __tablename__ = 'idxPHRASE24F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE24R(db.Model):

    """Represent a IdxPHRASE24R record."""

    __tablename__ = 'idxPHRASE24R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE25F(db.Model):

    """Represent a IdxPHRASE25F record."""

    __tablename__ = 'idxPHRASE25F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE25R(db.Model):

    """Represent a IdxPHRASE25R record."""

    __tablename__ = 'idxPHRASE25R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE26F(db.Model):

    """Represent a IdxPHRASE26F record."""

    __tablename__ = 'idxPHRASE26F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE26R(db.Model):

    """Represent a IdxPHRASE26R record."""

    __tablename__ = 'idxPHRASE26R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE27F(db.Model):

    """Represent a IdxPHRASE27F record."""

    __tablename__ = 'idxPHRASE27F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE27R(db.Model):

    """Represent a IdxPHRASE27R record."""

    __tablename__ = 'idxPHRASE27R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxPHRASE28F(db.Model):

    """Represent a IdxPHRASE28F record."""

    __tablename__ = 'idxPHRASE28F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE28R(db.Model):

    """Represent a IdxPHRASE28R record."""

    __tablename__ = 'idxPHRASE28R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD01F(db.Model):

    """Represent a IdxWORD01F record."""

    __tablename__ = 'idxWORD01F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD01R(db.Model):

    """Represent a IdxWORD01R record."""

    __tablename__ = 'idxWORD01R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD01Q(db.Model):

    """Represent a IdxWORD01Q record."""

    __tablename__ = 'idxWORD01Q'

    id = db.Column(db.MediumInteger(10, unsigned=True),
                   primary_key=True, autoincrement=True)
    runtime = db.Column(db.DateTime, nullable=False, index=True,
                        server_default='0001-01-01 00:00:00')
    id_bibrec_low = db.Column(db.MediumInteger(9, unsigned=True),
                              nullable=False)
    id_bibrec_high = db.Column(db.MediumInteger(9, unsigned=True),
                               nullable=False)
    index_name = db.Column(db.String(50), nullable=False, server_default='',
                           index=True)
    mode = db.Column(db.String(50), nullable=False, server_default='update')


class IdxWORD02F(db.Model):

    """Represent a IdxWORD02F record."""

    __tablename__ = 'idxWORD02F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD02R(db.Model):

    """Represent a IdxWORD02R record."""

    __tablename__ = 'idxWORD02R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD03F(db.Model):

    """Represent a IdxWORD03F record."""

    __tablename__ = 'idxWORD03F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD03R(db.Model):

    """Represent a IdxWORD03R record."""

    __tablename__ = 'idxWORD03R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD04F(db.Model):

    """Represent a IdxWORD04F record."""

    __tablename__ = 'idxWORD04F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD04R(db.Model):

    """Represent a IdxWORD04R record."""

    __tablename__ = 'idxWORD04R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD05F(db.Model):

    """Represent a IdxWORD05F record."""

    __tablename__ = 'idxWORD05F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD05R(db.Model):

    """Represent a IdxWORD05R record."""

    __tablename__ = 'idxWORD05R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD06F(db.Model):

    """Represent a IdxWORD06F record."""

    __tablename__ = 'idxWORD06F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD06R(db.Model):

    """Represent a IdxWORD06R record."""

    __tablename__ = 'idxWORD06R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD07F(db.Model):

    """Represent a IdxWORD07F record."""

    __tablename__ = 'idxWORD07F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD07R(db.Model):

    """Represent a IdxWORD07R record."""

    __tablename__ = 'idxWORD07R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD08F(db.Model):

    """Represent a IdxWORD08F record."""

    __tablename__ = 'idxWORD08F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD08R(db.Model):

    """Represent a IdxWORD08R record."""

    __tablename__ = 'idxWORD08R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD09F(db.Model):

    """Represent a IdxWORD09F record."""

    __tablename__ = 'idxWORD09F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD09R(db.Model):

    """Represent a IdxWORD09R record."""

    __tablename__ = 'idxWORD09R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD10F(db.Model):

    """Represent a IdxWORD10F record."""

    __tablename__ = 'idxWORD10F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD10R(db.Model):

    """Represent a IdxWORD10R record."""

    __tablename__ = 'idxWORD10R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD11F(db.Model):

    """Represent a IdxWORD11F record."""

    __tablename__ = 'idxWORD11F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD11R(db.Model):

    """Represent a IdxWORD11R record."""

    __tablename__ = 'idxWORD11R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD12F(db.Model):

    """Represent a IdxWORD12F record."""

    __tablename__ = 'idxWORD12F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD12R(db.Model):

    """Represent a IdxWORD12R record."""

    __tablename__ = 'idxWORD12R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD13F(db.Model):

    """Represent a IdxWORD13F record."""

    __tablename__ = 'idxWORD13F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD13R(db.Model):

    """Represent a IdxWORD13R record."""

    __tablename__ = 'idxWORD13R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD14F(db.Model):

    """Represent a IdxWORD14F record."""

    __tablename__ = 'idxWORD14F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD14R(db.Model):

    """Represent a IdxWORD14R record."""

    __tablename__ = 'idxWORD14R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD15F(db.Model):

    """Represent a IdxWORD15F record."""

    __tablename__ = 'idxWORD15F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD15R(db.Model):

    """Represent a IdxWORD15R record."""

    __tablename__ = 'idxWORD15R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD16F(db.Model):

    """Represent a IdxWORD16F record."""

    __tablename__ = 'idxWORD16F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD16R(db.Model):

    """Represent a IdxWORD16R record."""

    __tablename__ = 'idxWORD16R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD17F(db.Model):

    """Represent a IdxWORD17F record."""

    __tablename__ = 'idxWORD17F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD17R(db.Model):

    """Represent a IdxWORD17R record."""

    __tablename__ = 'idxWORD17R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD18F(db.Model):

    """Represent a IdxWORD18F record."""

    __tablename__ = 'idxWORD18F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD18R(db.Model):

    """Represent a IdxWORD18R record."""

    __tablename__ = 'idxWORD18R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD19F(db.Model):

    """Represent a IdxWORD19F record."""

    __tablename__ = 'idxWORD19F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD19R(db.Model):

    """Represent a IdxWORD19R record."""

    __tablename__ = 'idxWORD19R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD20F(db.Model):

    """Represent a IdxWORD20F record."""

    __tablename__ = 'idxWORD20F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD20R(db.Model):

    """Represent a IdxWORD20R record."""

    __tablename__ = 'idxWORD20R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD21F(db.Model):

    """Represent a IdxWORD21F record."""

    __tablename__ = 'idxWORD21F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD21R(db.Model):

    """Represent a IdxWORD21R record."""

    __tablename__ = 'idxWORD21R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD22F(db.Model):

    """Represent a IdxWORD22F record."""

    __tablename__ = 'idxWORD22F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD22R(db.Model):

    """Represent a IdxWORD22R record."""

    __tablename__ = 'idxWORD22R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD23F(db.Model):

    """Represent a IdxWORD23F record."""

    __tablename__ = 'idxWORD23F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD23R(db.Model):

    """Represent a IdxWORD23R record."""

    __tablename__ = 'idxWORD23R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD24F(db.Model):

    """Represent a IdxWORD24F record."""

    __tablename__ = 'idxWORD24F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD24R(db.Model):

    """Represent a IdxWORD24R record."""

    __tablename__ = 'idxWORD24R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD25F(db.Model):

    """Represent a IdxWORD25F record."""

    __tablename__ = 'idxWORD25F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD25R(db.Model):

    """Represent a IdxWORD25R record."""

    __tablename__ = 'idxWORD25R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD26F(db.Model):

    """Represent a IdxWORD26F record."""

    __tablename__ = 'idxWORD26F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD26R(db.Model):

    """Represent a IdxWORD26R record."""

    __tablename__ = 'idxWORD26R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD27F(db.Model):

    """Represent a IdxWORD27F record."""

    __tablename__ = 'idxWORD27F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD27R(db.Model):

    """Represent a IdxWORD27R record."""

    __tablename__ = 'idxWORD27R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


class IdxWORD28F(db.Model):

    """Represent a IdxWORD28F record."""

    __tablename__ = 'idxWORD28F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxWORD28R(db.Model):

    """Represent a IdxWORD28R record."""

    __tablename__ = 'idxWORD28R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                             name=__tablename__ + '_type'),
                     nullable=False,
                     server_default='CURRENT',
                     primary_key=True)


__all__ = ('IdxINDEX',
           'IdxINDEXIdxINDEX',
           'IdxINDEXNAME',
           'IdxINDEXField',
           'IdxPAIR01F',
           'IdxPAIR01R',
           'IdxPAIR01Q',
           'IdxPAIR02F',
           'IdxPAIR02R',
           'IdxPAIR03F',
           'IdxPAIR03R',
           'IdxPAIR04F',
           'IdxPAIR04R',
           'IdxPAIR05F',
           'IdxPAIR05R',
           'IdxPAIR06F',
           'IdxPAIR06R',
           'IdxPAIR07F',
           'IdxPAIR07R',
           'IdxPAIR08F',
           'IdxPAIR08R',
           'IdxPAIR09F',
           'IdxPAIR09R',
           'IdxPAIR10F',
           'IdxPAIR10R',
           'IdxPAIR11F',
           'IdxPAIR11R',
           'IdxPAIR12F',
           'IdxPAIR12R',
           'IdxPAIR13F',
           'IdxPAIR13R',
           'IdxPAIR14F',
           'IdxPAIR14R',
           'IdxPAIR15F',
           'IdxPAIR15R',
           'IdxPAIR16F',
           'IdxPAIR16R',
           'IdxPAIR17F',
           'IdxPAIR17R',
           'IdxPAIR18F',
           'IdxPAIR18R',
           'IdxPAIR19F',
           'IdxPAIR19R',
           'IdxPAIR20F',
           'IdxPAIR20R',
           'IdxPAIR21F',
           'IdxPAIR21R',
           'IdxPAIR22F',
           'IdxPAIR22R',
           'IdxPAIR23F',
           'IdxPAIR23R',
           'IdxPAIR24F',
           'IdxPAIR24R',
           'IdxPAIR25F',
           'IdxPAIR25R',
           'IdxPAIR26F',
           'IdxPAIR26R',
           'IdxPAIR27F',
           'IdxPAIR27R',
           'IdxPAIR28F',
           'IdxPAIR28R',
           'IdxPHRASE01F',
           'IdxPHRASE01R',
           'IdxPHRASE01Q',
           'IdxPHRASE02F',
           'IdxPHRASE02R',
           'IdxPHRASE03F',
           'IdxPHRASE03R',
           'IdxPHRASE04F',
           'IdxPHRASE04R',
           'IdxPHRASE05F',
           'IdxPHRASE05R',
           'IdxPHRASE06F',
           'IdxPHRASE06R',
           'IdxPHRASE07F',
           'IdxPHRASE07R',
           'IdxPHRASE08F',
           'IdxPHRASE08R',
           'IdxPHRASE09F',
           'IdxPHRASE09R',
           'IdxPHRASE10F',
           'IdxPHRASE10R',
           'IdxPHRASE11F',
           'IdxPHRASE11R',
           'IdxPHRASE12F',
           'IdxPHRASE12R',
           'IdxPHRASE13F',
           'IdxPHRASE13R',
           'IdxPHRASE14F',
           'IdxPHRASE14R',
           'IdxPHRASE15F',
           'IdxPHRASE15R',
           'IdxPHRASE16F',
           'IdxPHRASE16R',
           'IdxPHRASE17F',
           'IdxPHRASE17R',
           'IdxPHRASE18F',
           'IdxPHRASE18R',
           'IdxPHRASE19F',
           'IdxPHRASE19R',
           'IdxPHRASE20F',
           'IdxPHRASE20R',
           'IdxPHRASE21F',
           'IdxPHRASE21R',
           'IdxPHRASE22F',
           'IdxPHRASE22R',
           'IdxPHRASE23F',
           'IdxPHRASE23R',
           'IdxPHRASE24F',
           'IdxPHRASE24R',
           'IdxPHRASE25F',
           'IdxPHRASE25R',
           'IdxPHRASE26F',
           'IdxPHRASE26R',
           'IdxPHRASE27F',
           'IdxPHRASE27R',
           'IdxPHRASE28F',
           'IdxPHRASE28R',
           'IdxWORD01F',
           'IdxWORD01R',
           'IdxWORD01Q',
           'IdxWORD02F',
           'IdxWORD02R',
           'IdxWORD03F',
           'IdxWORD03R',
           'IdxWORD04F',
           'IdxWORD04R',
           'IdxWORD05F',
           'IdxWORD05R',
           'IdxWORD06F',
           'IdxWORD06R',
           'IdxWORD07F',
           'IdxWORD07R',
           'IdxWORD08F',
           'IdxWORD08R',
           'IdxWORD09F',
           'IdxWORD09R',
           'IdxWORD10F',
           'IdxWORD10R',
           'IdxWORD11F',
           'IdxWORD11R',
           'IdxWORD12F',
           'IdxWORD12R',
           'IdxWORD13F',
           'IdxWORD13R',
           'IdxWORD14F',
           'IdxWORD14R',
           'IdxWORD15F',
           'IdxWORD15R',
           'IdxWORD16F',
           'IdxWORD16R',
           'IdxWORD17F',
           'IdxWORD17R',
           'IdxWORD18F',
           'IdxWORD18R',
           'IdxWORD19F',
           'IdxWORD19R',
           'IdxWORD20F',
           'IdxWORD20R',
           'IdxWORD21F',
           'IdxWORD21R',
           'IdxWORD22F',
           'IdxWORD22R',
           'IdxWORD23F',
           'IdxWORD23R',
           'IdxWORD24F',
           'IdxWORD24R',
           'IdxWORD25F',
           'IdxWORD25R',
           'IdxWORD26F',
           'IdxWORD26R',
           'IdxWORD27F',
           'IdxWORD27R',
           'IdxWORD28F',
           'IdxWORD28R',
           )
