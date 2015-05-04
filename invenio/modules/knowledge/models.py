# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2014, 2015 CERN.
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

"""Knowledge database models."""

import os

from invenio.base.globals import cfg
from invenio.ext.sqlalchemy import db
from invenio.ext.sqlalchemy.utils import session_manager
from invenio.modules.collections.models import Collection
from invenio.utils.text import slugify

from sqlalchemy.dialects import mysql
from sqlalchemy.event import listens_for
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.schema import Index


class KnwKB(db.Model):

    """Represent a KnwKB record."""

    KNWKB_TYPES = {
        'written_as': 'w',
        'dynamic': 'd',
        'taxonomy': 't',
    }

    __tablename__ = 'knwKB'
    id = db.Column(db.MediumInteger(8, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    _name = db.Column(db.String(255), server_default='',
                      unique=True, name="name")
    _description = db.Column(db.Text, nullable=False,
                             name="description", default="")
    _kbtype = db.Column(db.Char(1), nullable=True, default='w', name="kbtype")
    slug = db.Column(db.String(255), unique=True, nullable=False, default="")
    # Enable or disable the access from REST API
    is_api_accessible = db.Column(db.Boolean, default=True, nullable=False)

    @db.hybrid_property
    def name(self):
        """Get name."""
        return self._name

    @name.setter
    def name(self, value):
        """Set name and generate the slug."""
        self._name = value
        # generate slug
        if not self.slug:
            self.slug = KnwKB.generate_slug(value)

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
        import warnings
        warnings.warn("The function is deprecated. Please use the "
                      "`KnwKBRVAL.query_kb_mappings()` instead. "
                      "E.g. [kval.to_dict() for kval in "
                      "KnwKBRVAL.query_kb_mappings(kb_id).all()]")
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
        import warnings
        warnings.warn("The function is deprecated. Please use the "
                      "`KnwKBRVAL.query_kb_mappings()` instead. "
                      "E.g. [(kval.m_value,) for kval in "
                      "KnwKBRVAL.query_kb_mappings(kb_id).all()]")
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

    @staticmethod
    def generate_slug(name):
        """Generate a slug for the knowledge.

        :param name: text to slugify
        :return: slugified text
        """
        slug = slugify(name)

        i = KnwKB.query.filter(db.or_(
            KnwKB.slug.like(slug),
            KnwKB.slug.like(slug + '-%'),
        )).count()

        return slug + ('-{0}'.format(i) if i > 0 else '')

    @staticmethod
    def exists(kb_name):
        """Return True if a kb with the given name exists.

        :param kb_name: the name of the knowledge base
        :return: True if kb exists
        """
        return KnwKB.query_exists(KnwKB.name.like(kb_name))

    @staticmethod
    def query_exists(filters):
        """Return True if a kb with the given filters exists.

        E.g: KnwKB.query_exists(KnwKB.name.like('FAQ'))

        :param filters: filter for sqlalchemy
        :return: True if kb exists
        """
        return db.session.query(
            KnwKB.query.filter(
                filters).exists()).scalar()

    def get_filename(self):
        """Construct the file name for taxonomy knoledge."""
        return cfg['CFG_WEBDIR'] + "/kbfiles/" \
            + str(self.id) + ".rdf"


@listens_for(KnwKB, 'after_delete')
def del_kwnkb(mapper, connection, target):
    """Remove taxonomy file."""
    if(target.kbtype == KnwKB.KNWKB_TYPES['taxonomy']):
        # Delete taxonomy file
        if os.path.isfile(target.get_filename()):
            os.remove(target.get_filename())


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
    m_value = db.Column(
        db.Text().with_variant(mysql.TEXT(30), 'mysql'),
        nullable=False)
    id_knwKB = db.Column(db.MediumInteger(8), db.ForeignKey(KnwKB.id),
                         nullable=False, server_default='0',
                         primary_key=True)
    kb = db.relationship(
        KnwKB,
        backref=db.backref(
            'kbrvals',
            cascade="all, delete-orphan",
            collection_class=attribute_mapped_collection("m_key")))

    @staticmethod
    def query_kb_mappings(kbid, sortby="to", key="", value="",
                          match_type="s"):
        """Return a list of all mappings from the given kb, ordered by key.

        If key given, give only those with left side (mapFrom) = key.
        If value given, give only those with right side (mapTo) = value.

        :param kb_name: knowledge base name. if "", return all
        :param sortby: the sorting criteria ('from' or 'to')
        :param key: return only entries where key matches this
        :param value: return only entries where value matches this
        :param match_type: s=substring, e=exact, sw=startswith
        """
        # query
        query = KnwKBRVAL.query.filter(
            KnwKBRVAL.id_knwKB == kbid)
        # filter
        if len(key) > 0:
            if match_type == "s":
                key = "%"+key+"%"
            elif match_type == "sw":
                key = key+"%"
        else:
            key = '%'
        if len(value) > 0:
            if match_type == "s":
                value = "%"+value+"%"
            elif match_type == "sw":
                value = value+"%"
        else:
            value = '%'
        query = query.filter(
            KnwKBRVAL.m_key.like(key),
            KnwKBRVAL.m_value.like(value))
        # order by
        if sortby == "from":
            query = query.order_by(KnwKBRVAL.m_key)
        else:
            query = query.order_by(KnwKBRVAL.m_value)
        return query

    def to_dict(self):
        """Return a dict representation of KnwKBRVAL."""
        # FIXME remove 'id' dependency from invenio modules
        return {'id': self.m_key + "_" + str(self.id_knwKB),
                'key': self.m_key,
                'value': self.m_value,
                'kbid': self.kb.id if self.kb else None,
                'kbname': self.kb.name if self.kb else None}


Index('ix_knwKBRVAL_m_value', KnwKBRVAL.m_value, mysql_length=30)

__all__ = ('KnwKB', 'KnwKBDDEF', 'KnwKBRVAL')
