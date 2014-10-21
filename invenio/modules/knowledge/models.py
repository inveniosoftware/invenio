# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2014 CERN.
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

"""Knowledge database models."""

from sqlalchemy.orm.collections import attribute_mapped_collection

from invenio.ext.sqlalchemy import db
from invenio.ext.sqlalchemy.utils import session_manager
from invenio.modules.search.models import Collection


class KnwKB(db.Model):

    """Represent a KnwKB record."""

    __tablename__ = 'knwKB'
    id = db.Column(db.MediumInteger(8, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), server_default='', unique=True)
    _description = db.Column(db.Text, nullable=False, name="description")
    _kbtype = db.Column(db.Char(1), nullable=True, default='w', name="kbtype")

    @db.hybrid_property
    def description(self):
        """Get description."""
        return self._description

    @description.setter
    def description(self, value):
        """Set description."""
        # TEXT in mysql don't support default value
        # @see http://bugs.mysql.com/bug.php?id=21532
        self._description = value or ''

    @db.hybrid_property
    def kbtype(self):
        """Get kbtype."""
        return self._kbtype

    @kbtype.setter
    def kbtype(self, value):
        """Set kbtype."""
        if value is None:
            # set the default value
            return
        # or set one of the available values
        kbtype = value[0] if len(value) > 0 else 'w'
        if kbtype not in ['t', 'd', 'w']:
            raise ValueError('unknown type "{value}", please use one of \
                             following values: "taxonomy", "dynamic" or \
                             "written_as"'.format(value=value))
        self._kbtype = kbtype

    def is_dynamic(self):
        """Return true if the type is dynamic."""
        return self._kbtype == 'd'

    def to_dict(self):
        """Return a dict representation of KnwKB."""
        mydict = {'id': self.id, 'name': self.name,
                  'description': self.description,
                  'kbtype': self.kbtype}
        if self.kbtype == 'd':
            mydict.update((self.kbdefs.to_dict() if self.kbdefs else {}) or {})

        return mydict

    def get_kbr_items(self, searchkey="", searchvalue="", searchtype='s'):
        """
        Return dicts of 'key' and 'value' from a knowledge base.

        :param kb_name the name of the knowledge base
        :param searchkey search using this key
        :param searchvalue search using this value
        :param searchtype s=substring, e=exact, sw=startswith
        :return a list of dictionaries [{'key'=>x, 'value'=>y},..]
        """
        if searchtype == 's' and searchkey:
            searchkey = '%'+searchkey+'%'
        if searchtype == 's' and searchvalue:
            searchvalue = '%'+searchvalue+'%'
        if searchtype == 'sw' and searchvalue:  # startswith
            searchvalue = searchvalue+'%'
        if not searchvalue:
            searchvalue = '%'
        if not searchkey:
            searchkey = '%'

        kvals = KnwKBRVAL.query.filter(
            KnwKBRVAL.id_knwKB.like(self.id),
            KnwKBRVAL.m_value.like(searchvalue),
            KnwKBRVAL.m_key.like(searchkey)).all()
        return [kval.to_dict() for kval in kvals]

    def get_kbr_values(self, searchkey="", searchvalue="", searchtype='s'):
        """
        Return dicts of 'key' and 'value' from a knowledge base.

        :param kb_name the name of the knowledge base
        :param searchkey search using this key
        :param searchvalue search using this value
        :param searchtype s=substring, e=exact, sw=startswith
        :return a list of dictionaries [{'key'=>x, 'value'=>y},..]
        """
        # prepare filters
        if searchtype == 's':
            searchkey = '%'+searchkey+'%'
        if searchtype == 's' and searchvalue:
            searchvalue = '%'+searchvalue+'%'
        if searchtype == 'sw' and searchvalue:  # startswith
            searchvalue = searchvalue+'%'
        if not searchvalue:
            searchvalue = '%'
        # execute query
        return db.session.execute(
            db.select([KnwKBRVAL.m_value],
                      db.and_(KnwKBRVAL.id_knwKB.like(self.id),
                              KnwKBRVAL.m_value.like(searchvalue),
                              KnwKBRVAL.m_key.like(searchkey))))

    @session_manager
    def set_dyn_config(self, field, expression, collection=None):
        """Set dynamic configuration."""
        if self.kbdefs:
            # update
            self.kbdefs.output_tag = field
            self.kbdefs.search_expression = expression
            self.kbdefs.collection = collection
            db.session.merge(self.kbdefs)
        else:
            # insert
            self.kbdefs = KnwKBDDEF(output_tag=field,
                                    search_expression=expression,
                                    collection=collection)


class KnwKBDDEF(db.Model):

    """Represent a KnwKBDDEF record."""

    __tablename__ = 'knwKBDDEF'
    id_knwKB = db.Column(db.MediumInteger(8, unsigned=True),
                         db.ForeignKey(KnwKB.id), nullable=False,
                         primary_key=True)
    id_collection = db.Column(db.MediumInteger(unsigned=True),
                              db.ForeignKey(Collection.id),
                              nullable=True)
    output_tag = db.Column(db.Text, nullable=True)
    search_expression = db.Column(db.Text, nullable=True)
    kb = db.relationship(
        KnwKB,
        backref=db.backref('kbdefs', uselist=False,
                           cascade="all, delete-orphan"),
        single_parent=True)
    collection = db.relationship(
        Collection,
        backref=db.backref('kbdefs'))

    def to_dict(self):
        """Return a dict representation of KnwKBDDEF."""
        return {'field': self.output_tag,
                'expression': self.search_expression,
                'coll_id': self.id_collection,
                'collection': self.collection.name
                if self.collection else None}


class KnwKBRVAL(db.Model):

    """Represent a KnwKBRVAL record."""

    __tablename__ = 'knwKBRVAL'
    m_key = db.Column(db.String(255), nullable=False, primary_key=True,
                      index=True)
    m_value = db.Column(db.Text(30), nullable=False, index=True)
    id_knwKB = db.Column(db.MediumInteger(8), db.ForeignKey(KnwKB.id),
                         nullable=False, server_default='0',
                         primary_key=True)
    kb = db.relationship(
        KnwKB,
        backref=db.backref(
            'kbrvals',
            cascade="all, delete-orphan",
            collection_class=attribute_mapped_collection("m_key")))

    def to_dict(self):
        """Return a dict representation of KnwKBRVAL."""
        # FIXME remove 'id' dependency from invenio modules
        return {'id': self.m_key + "_" + str(self.id_knwKB),
                'key': self.m_key,
                'value': self.m_value,
                'kbid': self.kb.id if self.kb else None,
                'kbname': self.kb.name if self.kb else None}

__all__ = ('KnwKB', 'KnwKBDDEF', 'KnwKBRVAL')
