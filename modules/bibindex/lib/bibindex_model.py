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
bibindex database models.
"""

# General imports.
from invenio.sqlalchemyutils import db

# Create your models here.

from invenio.bibedit_model import Bibrec
from invenio.websearch_model import Field


class IdxINDEX(db.Model):
    """Represents a IdxINDEX record."""
    def __init__(self):
        pass
    __tablename__ = 'idxINDEX'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False,
                server_default='')
    description = db.Column(db.String(255), nullable=False,
                server_default='')
    last_updated = db.Column(db.DateTime, nullable=False,
                server_default='0001-01-01 00:00:00')
    stemming_language = db.Column(db.String(10), nullable=False,
                server_default='')
    indexer = db.Column(db.String(10), nullable=False, server_default='native')


class IdxINDEXNAME(db.Model):
    """Represents a IdxINDEXNAME record."""
    def __init__(self):
        pass
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
    """Represents a IdxINDEXField record."""
    def __init__(self):
        pass
    __tablename__ = 'idxINDEX_field'
    id_idxINDEX = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(IdxINDEX.id), primary_key=True)
    id_field = db.Column(db.MediumInteger(9, unsigned=True), db.ForeignKey(Field.id),
                primary_key=True)
    regexp_punctuation = db.Column(db.String(255),
                nullable=False,
            server_default='[.,:;?!"]')
    regexp_alphanumeric_separators = db.Column(db.String(255),
                nullable=False) #FIX ME ,
            #server_default='[!"#$\\%&''()*+,-./:;<=>?@[\\]^\\_`{|}~]')
    idxINDEX = db.relationship(IdxINDEX, backref='fields')
    field = db.relationship(Field, backref='idxINDEXes')

#GENERATED

class IdxPAIR01F(db.Model):
    """Represents a IdxPAIR01F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR01F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR01R(db.Model):
    """Represents a IdxPAIR01R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR01R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR02F(db.Model):
    """Represents a IdxPAIR02F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR02F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR02R(db.Model):
    """Represents a IdxPAIR02R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR02R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR03F(db.Model):
    """Represents a IdxPAIR03F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR03F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR03R(db.Model):
    """Represents a IdxPAIR03R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR03R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR04F(db.Model):
    """Represents a IdxPAIR04F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR04F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR04R(db.Model):
    """Represents a IdxPAIR04R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR04R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR05F(db.Model):
    """Represents a IdxPAIR05F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR05F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR05R(db.Model):
    """Represents a IdxPAIR05R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR05R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR06F(db.Model):
    """Represents a IdxPAIR06F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR06F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR06R(db.Model):
    """Represents a IdxPAIR06R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR06R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR07F(db.Model):
    """Represents a IdxPAIR07F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR07F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR07R(db.Model):
    """Represents a IdxPAIR07R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR07R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR08F(db.Model):
    """Represents a IdxPAIR08F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR08F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR08R(db.Model):
    """Represents a IdxPAIR08R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR08R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR09F(db.Model):
    """Represents a IdxPAIR09F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR09F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR09R(db.Model):
    """Represents a IdxPAIR09R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR09R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR10F(db.Model):
    """Represents a IdxPAIR10F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR10F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR10R(db.Model):
    """Represents a IdxPAIR10R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR10R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR11F(db.Model):
    """Represents a IdxPAIR11F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR11F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR11R(db.Model):
    """Represents a IdxPAIR11R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR11R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR12F(db.Model):
    """Represents a IdxPAIR12F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR12F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR12R(db.Model):
    """Represents a IdxPAIR12R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR12R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR13F(db.Model):
    """Represents a IdxPAIR13F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR13F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR13R(db.Model):
    """Represents a IdxPAIR13R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR13R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR14F(db.Model):
    """Represents a IdxPAIR14F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR14F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR14R(db.Model):
    """Represents a IdxPAIR14R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR14R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR15F(db.Model):
    """Represents a IdxPAIR15F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR15F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR15R(db.Model):
    """Represents a IdxPAIR15R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR15R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR16F(db.Model):
    """Represents a IdxPAIR16F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR16F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR16R(db.Model):
    """Represents a IdxPAIR16R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR16R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR17F(db.Model):
    """Represents a IdxPAIR17F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR17F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR17R(db.Model):
    """Represents a IdxPAIR17R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR17R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR18F(db.Model):
    """Represents a IdxPAIR18F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR18F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR18R(db.Model):
    """Represents a IdxPAIR18R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR18R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPAIR19F(db.Model):
    """Represents a IdxPAIR19F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR19F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPAIR19R(db.Model):
    """Represents a IdxPAIR19R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPAIR19R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE01F(db.Model):
    """Represents a IdxPHRASE01F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE01F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE01R(db.Model):
    """Represents a IdxPHRASE01R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE01R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE02F(db.Model):
    """Represents a IdxPHRASE02F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE02F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE02R(db.Model):
    """Represents a IdxPHRASE02R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE02R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE03F(db.Model):
    """Represents a IdxPHRASE03F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE03F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE03R(db.Model):
    """Represents a IdxPHRASE03R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE03R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE04F(db.Model):
    """Represents a IdxPHRASE04F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE04F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE04R(db.Model):
    """Represents a IdxPHRASE04R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE04R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE05F(db.Model):
    """Represents a IdxPHRASE05F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE05F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE05R(db.Model):
    """Represents a IdxPHRASE05R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE05R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE06F(db.Model):
    """Represents a IdxPHRASE06F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE06F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE06R(db.Model):
    """Represents a IdxPHRASE06R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE06R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE07F(db.Model):
    """Represents a IdxPHRASE07F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE07F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE07R(db.Model):
    """Represents a IdxPHRASE07R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE07R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE08F(db.Model):
    """Represents a IdxPHRASE08F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE08F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE08R(db.Model):
    """Represents a IdxPHRASE08R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE08R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE09F(db.Model):
    """Represents a IdxPHRASE09F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE09F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE09R(db.Model):
    """Represents a IdxPHRASE09R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE09R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE10F(db.Model):
    """Represents a IdxPHRASE10F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE10F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE10R(db.Model):
    """Represents a IdxPHRASE10R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE10R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE11F(db.Model):
    """Represents a IdxPHRASE11F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE11F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE11R(db.Model):
    """Represents a IdxPHRASE11R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE11R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE12F(db.Model):
    """Represents a IdxPHRASE12F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE12F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE12R(db.Model):
    """Represents a IdxPHRASE12R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE12R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE13F(db.Model):
    """Represents a IdxPHRASE13F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE13F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE13R(db.Model):
    """Represents a IdxPHRASE13R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE13R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE14F(db.Model):
    """Represents a IdxPHRASE14F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE14F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE14R(db.Model):
    """Represents a IdxPHRASE14R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE14R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE15F(db.Model):
    """Represents a IdxPHRASE15F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE15F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE15R(db.Model):
    """Represents a IdxPHRASE15R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE15R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE16F(db.Model):
    """Represents a IdxPHRASE16F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE16F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE16R(db.Model):
    """Represents a IdxPHRASE16R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE16R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE17F(db.Model):
    """Represents a IdxPHRASE17F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE17F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE17R(db.Model):
    """Represents a IdxPHRASE17R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE17R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE18F(db.Model):
    """Represents a IdxPHRASE18F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE18F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE18R(db.Model):
    """Represents a IdxPHRASE18R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE18R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxPHRASE19F(db.Model):
    """Represents a IdxPHRASE19F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE19F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxPHRASE19R(db.Model):
    """Represents a IdxPHRASE19R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxPHRASE19R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD01F(db.Model):
    """Represents a IdxWORD01F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD01F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD01R(db.Model):
    """Represents a IdxWORD01R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD01R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD02F(db.Model):
    """Represents a IdxWORD02F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD02F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD02R(db.Model):
    """Represents a IdxWORD02R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD02R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD03F(db.Model):
    """Represents a IdxWORD03F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD03F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD03R(db.Model):
    """Represents a IdxWORD03R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD03R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD04F(db.Model):
    """Represents a IdxWORD04F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD04F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD04R(db.Model):
    """Represents a IdxWORD04R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD04R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD05F(db.Model):
    """Represents a IdxWORD05F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD05F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD05R(db.Model):
    """Represents a IdxWORD05R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD05R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD06F(db.Model):
    """Represents a IdxWORD06F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD06F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD06R(db.Model):
    """Represents a IdxWORD06R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD06R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD07F(db.Model):
    """Represents a IdxWORD07F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD07F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD07R(db.Model):
    """Represents a IdxWORD07R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD07R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD08F(db.Model):
    """Represents a IdxWORD08F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD08F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD08R(db.Model):
    """Represents a IdxWORD08R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD08R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD09F(db.Model):
    """Represents a IdxWORD09F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD09F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD09R(db.Model):
    """Represents a IdxWORD09R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD09R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD10F(db.Model):
    """Represents a IdxWORD10F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD10F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD10R(db.Model):
    """Represents a IdxWORD10R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD10R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD11F(db.Model):
    """Represents a IdxWORD11F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD11F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD11R(db.Model):
    """Represents a IdxWORD11R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD11R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD12F(db.Model):
    """Represents a IdxWORD12F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD12F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD12R(db.Model):
    """Represents a IdxWORD12R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD12R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD13F(db.Model):
    """Represents a IdxWORD13F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD13F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD13R(db.Model):
    """Represents a IdxWORD13R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD13R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD14F(db.Model):
    """Represents a IdxWORD14F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD14F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD14R(db.Model):
    """Represents a IdxWORD14R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD14R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD15F(db.Model):
    """Represents a IdxWORD15F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD15F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD15R(db.Model):
    """Represents a IdxWORD15R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD15R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD16F(db.Model):
    """Represents a IdxWORD16F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD16F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD16R(db.Model):
    """Represents a IdxWORD16R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD16R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD17F(db.Model):
    """Represents a IdxWORD17F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD17F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD17R(db.Model):
    """Represents a IdxWORD17R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD17R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD18F(db.Model):
    """Represents a IdxWORD18F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD18F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD18R(db.Model):
    """Represents a IdxWORD18R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD18R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)

class IdxWORD19F(db.Model):
    """Represents a IdxWORD19F record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD19F'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)

class IdxWORD19R(db.Model):
    """Represents a IdxWORD19R record."""
    def __init__(self):
        pass
    __tablename__ = 'idxWORD19R'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
                primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)
    type = db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY'),
                nullable=False,
                server_default='CURRENT',
                primary_key=True)


__all__ = ['IdxINDEX',
           'IdxINDEXNAME',
           'IdxINDEXField',
           'IdxPAIR01F',
           'IdxPAIR01R',
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
           'IdxPHRASE01F',
           'IdxPHRASE01R',
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
           'IdxWORD01F',
           'IdxWORD01R',
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
           'IdxWORD19R']
