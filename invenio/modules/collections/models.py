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

"""Database models for collections."""

# General imports.
import re

from operator import itemgetter

from flask import g, url_for

from intbitset import intbitset

from invenio.base.globals import cfg
from invenio.base.i18n import _, gettext_set_language
from invenio.ext.sqlalchemy import db
from invenio.ext.sqlalchemy.utils import attribute_multi_dict_collection
from invenio.modules.formatter.registry import output_formats
from invenio.modules.search.models import Field, Fieldvalue

from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.schema import Index

from werkzeug.utils import cached_property


external_collection_mapper = attribute_multi_dict_collection(
    creator=lambda k, v: CollectionExternalcollection(type=k,
                                                      externalcollection=v),
    key_attr=lambda obj: obj.type,
    val_attr=lambda obj: obj.externalcollection)


class Collection(db.Model):

    """Represent a Collection record."""

    def __repr__(self):
        """Return class representation."""
        return 'Collection <id: {0.id}, name: {0.name}, dbquery: {0.query}, ' \
               'nbrecs: {0.nbrecs}>'.format(self)

    def __unicode__(self):
        """Unicode."""
        suffix = ' ({0})'.format(_('default')) if self.id == 1 else ''
        return u"{0.id}. {0.name}{1}".format(self, suffix)

    def __str__(self):
        """Str."""
        # TODO it's compatible with python 3?
        return unicode(self).encode('utf-8')

    __tablename__ = 'collection'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True)
    name = db.Column(db.String(255), unique=True, index=True, nullable=False)
    dbquery = db.Column(
        db.Text().with_variant(db.Text(20), 'mysql'),
        nullable=True)

    @property
    def nbrecs(self):
        """Number of records in the collection."""
        from .cache import get_collection_nbrecs
        return get_collection_nbrecs(self.name)

    @property
    def reclist(self):
        """Return hit set with record identifiers."""
        from .cache import get_collection_reclist
        return get_collection_reclist(self.name)

    @property
    def is_hosted(self):
        """Return True if collection is hosted elsewhere."""
        return self.dbquery.startswith('hostedcollection:') if self.dbquery \
            else False

    _names = db.relationship(lambda: Collectionname,
                             backref='collection',
                             collection_class=attribute_mapped_collection(
                                 'ln_type'),
                             cascade="all, delete, delete-orphan")

    names = association_proxy(
        '_names', 'value',
        creator=lambda k, v: Collectionname(ln_type=k, value=v)
    )
    _boxes = db.relationship(lambda: Collectionboxname,
                             backref='collection',
                             collection_class=attribute_mapped_collection(
                                 'ln_type'),
                             cascade="all, delete, delete-orphan")

    boxes = association_proxy(
        '_boxes', 'value',
        creator=lambda k, v: Collectionboxname(ln_type=k, value=v)
    )

    _formatoptions = association_proxy('formats', 'format')

    # @cache.memoize(make_name=lambda fname: fname + '::' + g.ln)
    def formatoptions(self):
        """Return list of format options."""
        if len(self._formatoptions):
            return [dict(f) for f in self._formatoptions]
        else:
            return [{'code': u'hb',
                     'name': _("HTML %(format)s", format=_("brief")),
                     'content_type': u'text/html'}]

    formatoptions = property(formatoptions)

    _examples_example = association_proxy('_examples', 'example')

    @property
    # @cache.memoize(make_name=lambda fname: fname + '::' + g.ln)
    def examples(self):
        """Return list of example queries."""
        return list(self._examples_example)

    @property
    def name_ln(self):
        """Name ln."""
        from invenio.legacy.search_engine import get_coll_i18nname
        return get_coll_i18nname(self.name,
                                 getattr(g, 'ln', cfg['CFG_SITE_LANG']))
        # Another possible implementation with cache memoize
        # @cache.memoize
        # try:
        #    return db.object_session(self).query(Collectionname).\
        #        with_parent(self).filter(db.and_(Collectionname.ln==g.ln,
        #            Collectionname.type=='ln')).first().value
        # except Exception:
        #    return self.name

    @property
    # @cache.memoize(make_name=lambda fname: fname + '::' + g.ln)
    def portalboxes_ln(self):
        """Get Portalboxes ln."""
        return db.object_session(self).query(CollectionPortalbox).\
            with_parent(self).\
            options(db.joinedload_all(CollectionPortalbox.portalbox)).\
            filter(CollectionPortalbox.ln == g.ln).\
            order_by(db.desc(CollectionPortalbox.score)).all()

    @property
    def most_specific_dad(self):
        """Most specific dad."""
        results = sorted(
            db.object_session(self).query(Collection).join(
                Collection.sons
            ).filter(CollectionCollection.id_son == self.id).all(),
            key=lambda c: c.nbrecs)
        return results[0] if len(results) else None

    @property
    # @cache.memoize(make_name=lambda fname: fname + '::' + g.ln)
    def is_restricted(self):
        """Return ``True`` if the collection is restricted."""
        from invenio.legacy.search_engine import collection_restricted_p
        return collection_restricted_p(self.name)

    @property
    def type(self):
        """Return relation type."""
        p = re.compile("\d+:.*")
        if self.dbquery is not None and \
                p.match(self.dbquery.lower()):
            return 'r'
        else:
            return 'v'

    _collection_children = db.relationship(
        lambda: CollectionCollection,
        collection_class=ordering_list('score'),
        primaryjoin=lambda: Collection.id == CollectionCollection.id_dad,
        foreign_keys=lambda: CollectionCollection.id_dad,
        order_by=lambda: db.asc(CollectionCollection.score)
    )
    _collection_children_r = db.relationship(
        lambda: CollectionCollection,
        collection_class=ordering_list('score'),
        primaryjoin=lambda: db.and_(
            Collection.id == CollectionCollection.id_dad,
            CollectionCollection.type == 'r'),
        foreign_keys=lambda: CollectionCollection.id_dad,
        order_by=lambda: db.asc(CollectionCollection.score)
    )
    _collection_children_v = db.relationship(
        lambda: CollectionCollection,
        collection_class=ordering_list('score'),
        primaryjoin=lambda: db.and_(
            Collection.id == CollectionCollection.id_dad,
            CollectionCollection.type == 'v'),
        foreign_keys=lambda: CollectionCollection.id_dad,
        order_by=lambda: db.asc(CollectionCollection.score)
    )
    collection_parents = db.relationship(
        lambda: CollectionCollection,
        collection_class=ordering_list('score'),
        primaryjoin=lambda: Collection.id == CollectionCollection.id_son,
        foreign_keys=lambda: CollectionCollection.id_son,
        order_by=lambda: db.asc(CollectionCollection.score)
    )
    collection_children = association_proxy('_collection_children', 'son')
    collection_children_r = association_proxy(
        '_collection_children_r', 'son',
        creator=lambda son: CollectionCollection(id_son=son.id, type='r')
    )
    collection_children_v = association_proxy(
        '_collection_children_v', 'son',
        creator=lambda son: CollectionCollection(id_son=son.id, type='v')
    )

    _externalcollections = db.relationship(
        lambda: CollectionExternalcollection,
        cascade="all, delete, delete-orphan"
    )

    def _externalcollections_type(type_):
        return association_proxy(
            '_externalcollections_' + str(type_),
            'externalcollection',
            creator=lambda ext: CollectionExternalcollection(
                externalcollection=ext, type=type_))

    externalcollections_0 = _externalcollections_type(0)
    externalcollections_1 = _externalcollections_type(1)
    externalcollections_2 = _externalcollections_type(2)

    externalcollections = db.relationship(
        lambda: CollectionExternalcollection,
        collection_class=external_collection_mapper,
        cascade="all, delete, delete-orphan"
    )

    # Search options
    def _make_field_fieldvalue(type_):
        return db.relationship(
            lambda: CollectionFieldFieldvalue,
            primaryjoin=lambda: db.and_(
                Collection.id == CollectionFieldFieldvalue.id_collection,
                CollectionFieldFieldvalue.type == type_),
            order_by=lambda: CollectionFieldFieldvalue.score)

    _search_within = _make_field_fieldvalue('sew')
    _search_options = _make_field_fieldvalue('seo')

    @property
    # @cache.memoize(make_name=lambda fname: fname + '::' + g.ln)
    def search_within(self):
        """Collect search within options."""
        default = [('', _('any field'))]
        found = [(o.field.code, o.field.name_ln) for o in self._search_within]
        if not found:
            found = [(f.name.replace(' ', ''), f.name_ln)
                     for f in Field.query.filter(Field.name.in_(
                         cfg['CFG_WEBSEARCH_SEARCH_WITHIN'])).all()]
        return default + sorted(found, key=itemgetter(1))

    @property
    # @cache.memoize(make_name=lambda fname: fname + '::' + g.ln)
    def search_options(self):
        """Return search options."""
        return self._search_options

    @cached_property
    def ancestors(self):
        """Get list of parent collection ids."""
        output = set([self])
        for c in self.dads:
            output |= c.dad.ancestors
        return output

    @cached_property
    def ancestors_ids(self):
        """Get list of parent collection ids."""
        output = intbitset([self.id])
        for c in self.dads:
            ancestors = c.dad.ancestors_ids
            if self.id in ancestors:
                raise
            output |= ancestors
        return output

    @cached_property
    def descendants_ids(self):
        """Get list of child collection ids."""
        output = intbitset([self.id])
        for c in self.sons:
            descendants = c.son.descendants_ids
            if self.id in descendants:
                raise
            output |= descendants
        return output

    # Gets the list of localized names as an array
    collection_names = db.relationship(
        lambda: Collectionname,
        primaryjoin=lambda: Collection.id == Collectionname.id_collection,
        foreign_keys=lambda: Collectionname.id_collection
    )

    def translation(self, lang):
        """Get the translation according to the language code."""
        try:
            return db.object_session(self).query(Collectionname).\
                with_parent(self).filter(db.and_(
                    Collectionname.ln == lang,
                    Collectionname.type == 'ln'
                )).first().value
        except Exception:
            return ""

    @property
    def sort_methods(self):
        """Get sort methods for collection.

        If not sort methods are defined for a collection the root collections
        sort methods are retuned. If not methods are defined for the root
        collection, all possible sort methods are returned.

        Note: Noth sorting methods and ranking methods are now defined via
        the sorter.
        """
        from invenio.modules.sorter.models import BsrMETHOD, \
            Collection_bsrMETHOD

        for coll_id in (self.id, 1):
            methods = Collection_bsrMETHOD.query.filter_by(
                id_collection=coll_id
            ).order_by(
                Collection_bsrMETHOD.score
            ).options(
                db.joinedload(Collection_bsrMETHOD.bsrMETHOD)
            ).all()

            if len(methods) > 0:
                return map(lambda obj: obj.bsrMETHOD, methods)

        return BsrMETHOD.query.order_by(BsrMETHOD.name).all()

    def get_collectionbox_name(self, ln=None, box_type="r"):
        """Return collection-specific labelling subtrees.

        - 'Focus on': regular collection
        - 'Narrow by': virtual collection
        - 'Latest addition': boxes

        If translation for given language does not exist, use label
        for CFG_SITE_LANG. If no custom label is defined for
        CFG_SITE_LANG, return default label for the box.

        :param ln: the language of the label
        :param box_type: can be 'r' (=Narrow by), 'v' (=Focus on),
                         'l' (=Latest additions)
        """
        if ln is None:
            ln = g.ln
        collectionboxnamequery = db.object_session(self).query(
            Collectionboxname).with_parent(self)
        try:
            collectionboxname = collectionboxnamequery.filter(db.and_(
                Collectionboxname.ln == ln,
                Collectionboxname.type == box_type,
            )).one()
        except Exception:
            try:
                collectionboxname = collectionboxnamequery.filter(db.and_(
                    Collectionboxname.ln == ln,
                    Collectionboxname.type == box_type,
                )).one()
            except Exception:
                collectionboxname = None

        if collectionboxname is None:
            # load the right message language
            _ = gettext_set_language(ln)
            return _(Collectionboxname.TYPES.get(box_type, ''))
        else:
            return collectionboxname.value

    portal_boxes_ln = db.relationship(
        lambda: CollectionPortalbox,
        collection_class=ordering_list('score'),
        primaryjoin=lambda:
        Collection.id == CollectionPortalbox.id_collection,
        foreign_keys=lambda: CollectionPortalbox.id_collection,
        order_by=lambda: db.asc(CollectionPortalbox.score))

    def breadcrumbs(self, builder=None, ln=None):
        """Return breadcrumbs for collection."""
        ln = cfg.get('CFG_SITE_LANG') if ln is None else ln
        breadcrumbs = []
        # Get breadcrumbs for most specific dad if it exists.
        if self.most_specific_dad is not None:
            breadcrumbs = self.most_specific_dad.breadcrumbs(builder=builder,
                                                             ln=ln)

        if builder is not None:
            crumb = builder(self)
        else:
            crumb = dict(
                text=self.name_ln,
                url=url_for('collections.collection', name=self.name))

        breadcrumbs.append(crumb)
        return breadcrumbs


Index('ix_collection_dbquery', Collection.dbquery, mysql_length=20)


class Collectionname(db.Model):

    """Represent a Collectionname record."""

    __tablename__ = 'collectionname'

    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                              db.ForeignKey(Collection.id),
                              nullable=False, primary_key=True)
    ln = db.Column(db.Char(5), nullable=False, primary_key=True,
                   server_default='')
    type = db.Column(db.Char(3), nullable=False, primary_key=True,
                     server_default='sn')
    value = db.Column(db.String(255), nullable=False)

    @db.hybrid_property
    def ln_type(self):
        """Get ln type."""
        return (self.ln, self.type)

    @ln_type.setter
    def set_ln_type(self, value):
        """Set ln type."""
        (self.ln, self.type) = value


class Collectionboxname(db.Model):

    """Represent a Collectionboxname record."""

    __tablename__ = 'collectionboxname'

    TYPES = {
        'v': 'Focus on:',
        'r': 'Narrow by collection:',
        'l': 'Latest additions:',
    }

    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                              db.ForeignKey(Collection.id),
                              nullable=False, primary_key=True)
    ln = db.Column(db.Char(5), nullable=False, primary_key=True,
                   server_default='')
    type = db.Column(db.Char(3), nullable=False, primary_key=True,
                     server_default='r')
    value = db.Column(db.String(255), nullable=False)

    @db.hybrid_property
    def ln_type(self):
        return (self.ln, self.type)

    @ln_type.setter
    def set_ln_type(self, value):
        (self.ln, self.type) = value


class Collectiondetailedrecordpagetabs(db.Model):

    """Represent a Collectiondetailedrecordpagetabs record."""

    __tablename__ = 'collectiondetailedrecordpagetabs'
    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                              db.ForeignKey(Collection.id),
                              nullable=False, primary_key=True)
    tabs = db.Column(db.String(255), nullable=False,
                     server_default='')
    collection = db.relationship(Collection,
                                 backref='collectiondetailedrecordpagetabs')


class CollectionCollection(db.Model):

    """Represent a CollectionCollection record."""

    __tablename__ = 'collection_collection'
    id_dad = db.Column(db.MediumInteger(9, unsigned=True),
                       db.ForeignKey(Collection.id), primary_key=True)
    id_son = db.Column(db.MediumInteger(9, unsigned=True),
                       db.ForeignKey(Collection.id), primary_key=True)
    type = db.Column(db.Char(1), nullable=False,
                     server_default='r')
    score = db.Column(db.TinyInteger(4, unsigned=True), nullable=False,
                      server_default='0')
    son = db.relationship(Collection, primaryjoin=id_son == Collection.id,
                          backref='dads',
                          # FIX
                          # collection_class=db.attribute_mapped_collection('score'),
                          order_by=db.asc(score))
    dad = db.relationship(Collection, primaryjoin=id_dad == Collection.id,
                          backref='sons', order_by=db.asc(score))


class Example(db.Model):

    """Represent a Example record."""

    __tablename__ = 'example'
    id = db.Column(db.MediumInteger(9, unsigned=True), primary_key=True,
                   autoincrement=True)
    type = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=False)


class CollectionExample(db.Model):

    """Represent a CollectionExample record."""

    __tablename__ = 'collection_example'
    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                              db.ForeignKey(Collection.id), primary_key=True)
    id_example = db.Column(db.MediumInteger(9, unsigned=True),
                           db.ForeignKey(Example.id), primary_key=True)
    score = db.Column(db.TinyInteger(4, unsigned=True), nullable=False,
                      server_default='0')
    collection = db.relationship(Collection, backref='_examples',
                                 order_by=score)
    example = db.relationship(Example, backref='collections', order_by=score)


class Portalbox(db.Model):

    """Represent a Portalbox record."""

    __tablename__ = 'portalbox'
    id = db.Column(db.MediumInteger(9, unsigned=True), autoincrement=True,
                   primary_key=True)
    title = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=False)


def get_pbx_pos():
    """Return a list of all the positions for a portalbox."""
    position = {}
    position["rt"] = "Right Top"
    position["lt"] = "Left Top"
    position["te"] = "Title Epilog"
    position["tp"] = "Title Prolog"
    position["ne"] = "Narrow by coll epilog"
    position["np"] = "Narrow by coll prolog"
    return position


class CollectionPortalbox(db.Model):

    """Represent a CollectionPortalbox record."""

    __tablename__ = 'collection_portalbox'
    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                              db.ForeignKey(Collection.id), primary_key=True)
    id_portalbox = db.Column(db.MediumInteger(9, unsigned=True),
                             db.ForeignKey(Portalbox.id), primary_key=True)
    ln = db.Column(db.Char(5), primary_key=True, server_default='',
                   nullable=False)
    position = db.Column(db.Char(3), nullable=False,
                         server_default='top')
    score = db.Column(db.TinyInteger(4, unsigned=True),
                      nullable=False,
                      server_default='0')
    collection = db.relationship(Collection, backref='portalboxes',
                                 order_by=score)
    portalbox = db.relationship(Portalbox, backref='collections',
                                order_by=score)


class Externalcollection(db.Model):

    """Represent a Externalcollection record."""

    __tablename__ = 'externalcollection'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False,
                     server_default='')

    @property
    def engine(self):
        """Engine."""
        from invenio.legacy.websearch_external_collections.searcher import (
            external_collections_dictionary
        )
        if self.name in external_collections_dictionary:
            return external_collections_dictionary[self.name]


class CollectionExternalcollection(db.Model):

    """Represent a CollectionExternalcollection record."""

    __tablename__ = 'collection_externalcollection'
    id_collection = db.Column(db.MediumInteger(9,
                                               unsigned=True),
                              db.ForeignKey(Collection.id), primary_key=True,
                              server_default='0')
    id_externalcollection = db.Column(db.MediumInteger(9,
                                                       unsigned=True),
                                      db.ForeignKey(Externalcollection.id),
                                      primary_key=True,
                                      server_default='0')
    type = db.Column(db.TinyInteger(4, unsigned=True),
                     server_default='0',
                     nullable=False)

    def _collection_type(type_):
        return db.relationship(
            Collection,
            primaryjoin=lambda: db.and_(
                CollectionExternalcollection.id_collection == Collection.id,
                CollectionExternalcollection.type == type_),
            backref='_externalcollections_{0}'.format(str(type_))
        )

    collection_0 = _collection_type(0)
    collection_1 = _collection_type(1)
    collection_2 = _collection_type(2)

    externalcollection = db.relationship(Externalcollection)


class CollectionFormat(db.Model):

    """Represent a CollectionFormat record."""

    __tablename__ = 'collection_format'
    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                              db.ForeignKey(Collection.id), primary_key=True)
    format_code = db.Column('format', db.String(10), primary_key=True)
    score = db.Column(db.TinyInteger(4, unsigned=True),
                      nullable=False, server_default='0')

    collection = db.relationship(
        Collection, backref=db.backref(
            'formats', order_by=db.desc(score)
        ), order_by=db.desc(score))

    @property
    def format(self):
        """Return output format definition."""
        return output_formats[self.format_code]


class CollectionFieldFieldvalue(db.Model):

    """Represent a CollectionFieldFieldvalue record."""

    __tablename__ = 'collection_field_fieldvalue'

    id = db.Column(db.MediumInteger(9, unsigned=True), autoincrement=True,
                   primary_key=True, nullable=False)
    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                              db.ForeignKey(Collection.id),
                              nullable=False)
    id_field = db.Column(db.MediumInteger(9, unsigned=True),
                         db.ForeignKey(Field.id),
                         nullable=False)
    _id_fieldvalue = db.Column(db.MediumInteger(9, unsigned=True),
                               db.ForeignKey(Fieldvalue.id),
                               nullable=True, default=None,
                               name="id_fieldvalue")
    type = db.Column(db.Char(3), nullable=False,
                     server_default='src')
    score = db.Column(db.TinyInteger(4, unsigned=True), nullable=False,
                      server_default='0')
    score_fieldvalue = db.Column(db.TinyInteger(4, unsigned=True),
                                 nullable=False, server_default='0')

    collection = db.relationship(Collection, backref='field_fieldvalues',
                                 order_by=score)
    field = db.relationship(Field, backref='collection_fieldvalues',
                            lazy='joined')
    fieldvalue = db.relationship(Fieldvalue, backref='collection_fields',
                                 lazy='joined')

    @db.hybrid_property
    def id_fieldvalue(self):
        """Get id_fieldvalue."""
        return self._id_fieldvalue

    @id_fieldvalue.setter
    def id_fieldvalue(self, value):
        """Set id_fieldvalue."""
        self._id_fieldvalue = value or None


class FacetCollection(db.Model):

    """Facet configuration for collection."""

    __tablename__ = 'facet_collection'

    id = db.Column(db.Integer, primary_key=True)
    id_collection = db.Column(db.Integer, db.ForeignKey(Collection.id))
    order = db.Column(db.Integer)
    facet_name = db.Column(db.String(80))

    collection = db.relationship(Collection, backref='facets')

    def __repr__(self):
        """Return class representation."""
        return ('FacetCollection <id: {0.id}, id_collection: '
                '{0.id_collection}, order: {0.order}, '
                'facet_name: {0.facet_name}>'.format(self))

    @classmethod
    def is_place_taken(cls, id_collection, order):
        """Check if there is already a facet on the given position.

        .. note:: This works well as a pre-check, however saving can still fail
            if somebody else creates the same record in other session
            (phantom reads).
        """
        return bool(cls.query.filter(
            cls.id_collection == id_collection,
            cls.order == order).count())

    @classmethod
    def is_duplicated(cls, id_collection, facet_name):
        """Check if the given facet is already assigned to this collection.

        .. note:: This works well as a pre-check, however saving can still fail
            if somebody else creates the same record in other session
            (phantom reads).
        """
        return bool(cls.query.filter(
            cls.id_collection == id_collection,
            cls.facet_name == facet_name).count())


__all__ = (
    'Collection',
    'Collectionname',
    'Collectiondetailedrecordpagetabs',
    'CollectionCollection',
    'Example',
    'CollectionExample',
    'Portalbox',
    'CollectionPortalbox',
    'Externalcollection',
    'CollectionExternalcollection',
    'CollectionFormat',
    'CollectionFieldFieldvalue',
    'FacetCollection',
)
