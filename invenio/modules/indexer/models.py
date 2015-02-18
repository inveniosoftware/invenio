# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014, 2015 CERN.
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

"""Define database models for native indexer."""

from invenio.base.globals import cfg
from invenio.ext.sqlalchemy import db
from invenio.ext.sqlalchemy.utils import TableNameMixin
from invenio.modules.records.models import Record as Bibrec
from invenio.modules.search.models import Field

from sqlalchemy.ext.declarative import declared_attr


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

    @classmethod
    def get_idxpair_field_ids(cls):
        """Return list of field ids that idxPAIRS should be used on."""
        return [item[0] for item in cls.query.filter(cls.name.in_(
            cfg['CFG_WEBSEARCH_IDXPAIRS_FIELDS']
        )).values(cls.id)]

    @classmethod
    def get_from_field(cls, field='global'):
        """Return index instance corresponding to FIELD."""
        index = cls.query.filter_by(name=field).first()
        if index is None:
            index = cls.query.join(IdxINDEXField).join(Field).filter(
                Field.code == field
            ).first()
        return index

    @classmethod
    def get_index_id_from_field(cls, field='global'):
        """Return index instance with name corresponding to FIELD.

        Alternatively, return the first index where the logical field code
        named FIELD is indexed.

        Example: field='author', output=4.
        """
        field = 'global' if not field else field
        index = cls.query.filter_by(name=field).value(cls.id)
        if index is None:
            index = cls.query.join(IdxINDEXField).join(Field).filter(
                Field.code == field
            ).value(cls.id)
        return index or 0

    @classmethod
    def idxWORDF(cls, field, fallback=True):
        """Return correct word index for given field."""
        model = globals().get('IdxWORD{:02d}F'.format(
            cls.get_index_id_from_field(field)))
        if fallback and model is None:
            model = globals().get('IdxWORD{:02d}F'.format(
                cls.get_index_id_from_field('anyfield')))
        return model

    @classmethod
    def idxPHRASEF(cls, field, fallback=True):
        """Return correct word index for given field."""
        model = globals().get('IdxPHRASE{:02d}F'.format(
            cls.get_index_id_from_field(field)))
        if fallback and model is None:
            model = globals().get('IdxPHRASE{:02d}F'.format(
                cls.get_index_id_from_field('anyfield')))
        return model

    @classmethod
    def idxPHRASER(cls, field, fallback=True):
        """Return correct word index for given field."""
        model = globals().get('IdxPHRASE{:02d}R'.format(
            cls.get_index_id_from_field(field)))
        if fallback and model is None:
            model = globals().get('IdxPHRASE{:02d}R'.format(
                cls.get_index_id_from_field('anyfield')))
        return model

    @classmethod
    def idxPAIRF(cls, field, fallback=True):
        """Return correct pairs for given field."""
        model = globals().get('IdxPAIR{:02d}F'.format(
            cls.get_index_id_from_field(field)))
        if fallback and model is None:
            model = globals().get('IdxPAIR{:02d}F'.format(
                cls.get_index_id_from_field('anyfield')))
        return model

    @property
    def wordf(self):
        """Return correct word index."""
        return globals().get('IdxWORD{:02d}F'.format(self.id))

    @property
    def pairf(self):
        """Return correct pair index."""
        return globals().get('IdxPAIR{:02d}F'.format(self.id))


class IdxINDEXIdxINDEX(db.Model):

    """Represent an IdxINDEXIdxINDEX record."""

    __tablename__ = 'idxINDEX_idxINDEX'
    id_virtual = db.Column(db.MediumInteger(9, unsigned=True),
                           db.ForeignKey(IdxINDEX.id), nullable=False,
                           server_default='0', primary_key=True)
    id_normal = db.Column(db.MediumInteger(9, unsigned=True),
                          db.ForeignKey(IdxINDEX.id), nullable=False,
                          server_default='0', primary_key=True)

    virtual = db.relationship(
        IdxINDEX,
        backref=db.backref('normal'),
        primaryjoin="and_(IdxINDEXIdxINDEX.id_virtual==IdxINDEX.id)"
    )

    normal = db.relationship(
        IdxINDEX,
        backref=db.backref('virtual'),
        primaryjoin="and_(IdxINDEXIdxINDEX.id_normal==IdxINDEX.id)"
    )

    @staticmethod
    def is_virtual(id_virtual):
        """Check if index is virtual."""
        return db.session.query(
            IdxINDEXIdxINDEX.query.filter_by(
                id_virtual=id_virtual).exists()).scalar()


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
    # server_default='[!"#$\\%&''()*+,-./:;<=>?@[\\]^\\_`{|}~]')
    idxINDEX = db.relationship(IdxINDEX, backref='fields', lazy='joined',
                               innerjoin=True)
    field = db.relationship(Field, backref='idxINDEXes', lazy='joined',
                            innerjoin=True)

    @classmethod
    def get_field_tokenizers(cls):
        """Get field tokenizers."""
        return db.session.query(Field.name, IdxINDEX.tokenizer).all()

# GENERATED


class IdxQMixin(TableNameMixin):

    """Mixin for Idx(PAIR|PHRASE|WORD)01Q tables."""

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


class IdxPAIRFMixin(TableNameMixin):

    """Mixin for IdxPAIRxxF tables."""

    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(100), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPAIR01Q(db.Model, IdxQMixin):

    """Represent a IdxPAIR01Q record."""

    pass


class IdxPHRASEFMixin(TableNameMixin):

    """Mixin for IdxPHRASExxF tables."""

    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.Text, nullable=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxPHRASE01Q(db.Model, IdxQMixin):

    """Represent a IdxPHRASE01Q record."""

    pass


class IdxWORDFMixin(TableNameMixin):

    """Mixin for IdxWORDxxF tables."""

    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    term = db.Column(db.String(50), nullable=True,
                     unique=True)
    hitlist = db.Column(db.iLargeBinary, nullable=True)


class IdxRMixin(TableNameMixin):

    """Mixin for Idx(PAIR|PHRASE|WORD)xxR tables."""

    @declared_attr
    def id_bibrec(cls):
        return db.Column(db.MediumInteger(8, unsigned=True),
                         db.ForeignKey(Bibrec.id),
                         primary_key=True)
    termlist = db.Column(db.iLargeBinary, nullable=True)

    @declared_attr
    def type(cls):
        return db.Column(db.Enum('CURRENT', 'FUTURE', 'TEMPORARY',
                                 name=cls.__tablename__ + '_type'),
                         nullable=False, server_default='CURRENT',
                         primary_key=True)


class IdxWORD01Q(db.Model, IdxQMixin):

    """Represent a IdxWORD01Q record."""

    pass


models = []

for idx in range(1, 29):
    IdxPAIRF = "IdxPAIR{:02d}F".format(idx)
    globals()[IdxPAIRF] = type(IdxPAIRF, (db.Model, IdxPAIRFMixin), {})
    IdxPAIRR = "IdxPAIR{:02d}R".format(idx)
    globals()[IdxPAIRR] = type(IdxPAIRR, (db.Model, IdxRMixin), {})

    IdxPHRASEF = "IdxPHRASE{:02d}F".format(idx)
    globals()[IdxPHRASEF] = type(IdxPHRASEF, (db.Model, IdxPHRASEFMixin), {})
    IdxPHRASER = "IdxPHRASE{:02d}R".format(idx)
    globals()[IdxPHRASER] = type(IdxPHRASER, (db.Model, IdxRMixin), {})

    IdxWORDF = "IdxWORD{:02d}F".format(idx)
    globals()[IdxWORDF] = type(IdxWORDF, (db.Model, IdxWORDFMixin), {})
    IdxWORDR = "IdxWORD{:02d}R".format(idx)
    globals()[IdxWORDR] = type(IdxWORDR, (db.Model, IdxRMixin), {})

    models += [IdxPAIRF, IdxPAIRR, IdxPHRASEF, IdxPHRASER, IdxWORDF, IdxWORDR]


__all__ = tuple([
    'IdxINDEX',
    'IdxINDEXIdxINDEX',
    'IdxINDEXNAME',
    'IdxINDEXField',
    'IdxPAIR01Q',
    'IdxPHRASE01Q',
    'IdxWORD01Q',
] + models)
