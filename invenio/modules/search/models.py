# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013 CERN.
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
WebSearch database models.
"""

# General imports.
import re
from operator import itemgetter
from flask import g, url_for
from invenio.base.globals import cfg
try:
    from invenio.intbitset import intbitset
except:
    from intbitset import intbitset
#from invenio.search_engine import collection_restricted_p
from invenio.ext.sqlalchemy import db
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.collections import collection
from sqlalchemy.ext.orderinglist import ordering_list
#from invenio.websearch_external_collections_searcher import \
#    external_collections_dictionary

# Create your models here.

from invenio.modules.accounts.models import User
from invenio.modules.formatter.models import Format


class IntbitsetPickle(object):
    def dumps(self, obj, protocol=None):
        if obj is not None:
            return obj.fastdump()
        return intbitset([]).fastdump()

    def loads(self, obj):
        try:
            return intbitset(obj)
        except:
            return intbitset()


def IntbitsetCmp(x, y):
    if x is None or y is None:
        return False
    else:
        return x == y


class OrderedList(InstrumentedList):
    def append(self, item):
        if self:
            s = sorted(self, key=lambda obj: obj.score)
            item.score = s[-1].score + 1
        else:
            item.score = 1
        InstrumentedList.append(self, item)

    def set(self, item, index=0):
        if self:
            s = sorted(self, key=lambda obj: obj.score)
            if index >= len(s):
                item.score = s[-1].score + 1
            elif index < 0:
                item.score = s[0].score
                index = 0
            else:
                item.score = s[index].score + 1

            for i, it in enumerate(s[index:]):
                it.score = item.score + i + 1
                #if s[i+1].score more then break
        else:
            item.score = index
        InstrumentedList.append(self, item)

    def pop(self, item):
        #FIXME
        if self:
            obj_list = sorted(self, key=lambda obj: obj.score)
            for i, it in enumerate(obj_list):
                if obj_list[i] == item:
                    return InstrumentedList.pop(self, i)


def attribute_multi_dict_collection(creator, key_attr, val_attr):
    class MultiMappedCollection(dict):

        def __init__(self, data=None):
            self._data = data or {}

        @collection.appender
        def _append(self, obj):
            l = self._data.setdefault(key_attr(obj), [])
            l.append(obj)

        def __setitem__(self, key, value):
            self._append(creator(key, value))

        def __getitem__(self, key):
            return tuple(val_attr(obj) for obj in self._data[key])

        @collection.remover
        def _remove(self, obj):
            self._data[key_attr(obj)].remove(obj)

        @collection.iterator
        def _iterator(self):
            for objs in self._data.itervalues():
                for obj in objs:
                    yield obj

        #@collection.converter
        #def convert(self, other):
        #    print '===== CONVERT ===='
        #    print other
        #    for k, vals in other.iteritems():
        #        for v in list(vals):
        #            print 'converting: ', k,': ',v
        #            yield creator(k, v)

        #@collection.internally_instrumented
        #def extend(self, items):
        #    for k, item in items:
        #        for v in list(item):
        #            print 'setting: ', k,': ',v
        #            self.__setitem__(k,v)

        def __repr__(self):
            return '%s(%r)' % (type(self).__name__, self._data)

    return MultiMappedCollection

external_collection_mapper = attribute_multi_dict_collection(
    creator=lambda k, v: CollectionExternalcollection(type=k,
                                                      externalcollection=v),
    key_attr=lambda obj: obj.type,
    val_attr=lambda obj: obj.externalcollection)


class Collection(db.Model):
    """Represents a Collection record."""

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.id)

    __tablename__ = 'collection'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True)
    name = db.Column(db.String(255), unique=True, index=True,
                nullable=False)
    dbquery = db.Column(db.Text(20), nullable=True,
                index=True)
    nbrecs = db.Column(db.Integer(10, unsigned=True),
                server_default='0')
    #FIXME read only!!!
    reclist = db.Column(db.PickleType(pickler=IntbitsetPickle(),
                                     comparator=IntbitsetCmp))
    _names = db.relationship(lambda: Collectionname,
                backref='collection',
                collection_class=attribute_mapped_collection('ln_type'),
                cascade="all, delete, delete-orphan")

    names = association_proxy('_names', 'value',
                creator=lambda k, v: Collectionname(ln_type=k, value=v))

    _formatoptions = association_proxy('formats', 'format')

    #@cache.memoize(make_name=lambda fname: fname + '::' + g.ln)
    def formatoptions(self):
        if len(self._formatoptions):
            return [dict(f) for f in self._formatoptions]
        else:
            return [{'code': 'hb', 'name': "HTML %s" % g._("brief"),
                     'content_type': 'text/html'}]

    formatoptions = property(formatoptions)

    _examples_example = association_proxy('_examples', 'example')

    @property
    #@cache.memoize(make_name=lambda fname: fname + '::' + g.ln)
    def examples(self):
        return list(self._examples_example)

    @property
    def name_ln(self):
        from invenio.search_engine import get_coll_i18nname
        return get_coll_i18nname(self.name, g.ln).decode('utf-8')
        # Another possible implementation with cache memoize
        # @cache.memoize
        #try:
        #    return db.object_session(self).query(Collectionname).\
        #        with_parent(self).filter(db.and_(Collectionname.ln==g.ln,
        #            Collectionname.type=='ln')).first().value
        #except:
        #    return self.name

    @property
    #@cache.memoize(make_name=lambda fname: fname + '::' + g.ln)
    def portalboxes_ln(self):
        return db.object_session(self).query(CollectionPortalbox).\
            with_parent(self).\
            options(db.joinedload_all(CollectionPortalbox.portalbox)).\
            filter(CollectionPortalbox.ln == g.ln).\
            order_by(db.desc(CollectionPortalbox.score)).all()

    @property
    def most_specific_dad(self):
        return db.object_session(self).query(Collection).\
            join(Collection.sons).\
            filter(CollectionCollection.id_son == self.id).\
            order_by(db.asc(Collection.nbrecs)).\
            first()

    @property
    #@cache.memoize(make_name=lambda fname: fname + '::' + g.ln)
    def is_restricted(self):
        from invenio.search_engine import collection_restricted_p
        return collection_restricted_p(self.name)

    @property
    def type(self):
        p = re.compile("\d+:.*")
        if self.dbquery is not None and \
            p.match(self.dbquery.lower()):
            return 'r'
        else:
            return 'v'

    _collection_children = db.relationship(lambda: CollectionCollection,
            #collection_class=OrderedList,
            collection_class=ordering_list('score'),
            primaryjoin=lambda: Collection.id == CollectionCollection.id_dad,
            foreign_keys=lambda: CollectionCollection.id_dad,
            order_by=lambda: db.asc(CollectionCollection.score))
    _collection_children_r = db.relationship(lambda: CollectionCollection,
            #collection_class=OrderedList,
            collection_class=ordering_list('score'),
            primaryjoin=lambda: db.and_(
                Collection.id == CollectionCollection.id_dad,
                CollectionCollection.type == 'r'),
            foreign_keys=lambda: CollectionCollection.id_dad,
            order_by=lambda: db.asc(CollectionCollection.score))
    _collection_children_v = db.relationship(lambda: CollectionCollection,
            #collection_class=OrderedList,
            collection_class=ordering_list('score'),
            primaryjoin=lambda: db.and_(
                Collection.id == CollectionCollection.id_dad,
                CollectionCollection.type == 'v'),
            foreign_keys=lambda: CollectionCollection.id_dad,
            order_by=lambda: db.asc(CollectionCollection.score))
    collection_parents = db.relationship(lambda: CollectionCollection,
            #collection_class=OrderedList,
            collection_class=ordering_list('score'),
            primaryjoin=lambda: Collection.id == CollectionCollection.id_son,
            foreign_keys=lambda: CollectionCollection.id_son,
            order_by=lambda: db.asc(CollectionCollection.score))
    collection_children = association_proxy('_collection_children', 'son')
    collection_children_r = association_proxy('_collection_children_r', 'son',
        creator=lambda son: CollectionCollection(id_son=son.id, type='r'))
    collection_children_v = association_proxy('_collection_children_v', 'son',
        creator=lambda son: CollectionCollection(id_son=son.id, type='v'))

#
    _externalcollections = db.relationship(lambda: CollectionExternalcollection,
#            backref='collection',
            cascade="all, delete, delete-orphan")
#
#    externalcollections = association_proxy(
#        '_externalcollections',
#        'externalcollection')

    def _externalcollections_type(type):
        return association_proxy(
            '_externalcollections_' + str(type),
            'externalcollection',
            creator=lambda ext: CollectionExternalcollection(
                externalcollection=ext, type=type))

    externalcollections_0 = _externalcollections_type(0)
    externalcollections_1 = _externalcollections_type(1)
    externalcollections_2 = _externalcollections_type(2)

    externalcollections = db.relationship(lambda: CollectionExternalcollection,
            #backref='collection',
            collection_class=external_collection_mapper,
            cascade="all, delete, delete-orphan")

    # Search options
    _make_field_fieldvalue = lambda type: db.relationship(
            lambda: CollectionFieldFieldvalue,
            primaryjoin=lambda: db.and_(
                Collection.id == CollectionFieldFieldvalue.id_collection,
                CollectionFieldFieldvalue.type == type),
            order_by=lambda: CollectionFieldFieldvalue.score)

    _search_within = _make_field_fieldvalue('sew')
    _search_options = _make_field_fieldvalue('seo')

    @property
    #@cache.memoize(make_name=lambda fname: fname + '::' + g.ln)
    def search_within(self):
        """
        Collect search within options.
        """
        default = [('', g._('any field'))]
        found = [(o.field.code, o.field.name_ln) for o in self._search_within]
        if not found:
            found = [(f.name.replace(' ', ''), f.name_ln)
                for f in Field.query.filter(Field.name.in_(
                    cfg['CFG_WEBSEARCH_SEARCH_WITHIN'])).all()]
        return default + sorted(found, key=itemgetter(1))

    @property
    #@cache.memoize(make_name=lambda fname: fname + '::' + g.ln)
    def search_options(self):
        return self._search_options

    @property
    #@cache.memoize(make_name=lambda fname: fname + '::' + g.ln)
    def ancestors_ids(self):
        """Get list of parent collection ids."""
        output = intbitset([self.id])
        for c in self.dads:
            ancestors = c.dad.ancestors_ids
            if self.id in ancestors:
                raise
            output |= ancestors
        return output

    @property
    #@cache.memoize(make_name=lambda fname: fname + '::' + g.ln)
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

    # Gets the translation according to the lang code
    def translation(self, lang):
        try:
            return db.object_session(self).query(Collectionname).\
                with_parent(self).filter(db.and_(Collectionname.ln == lang,
                    Collectionname.type == 'ln')).first().value
        except:
            return ""

    portal_boxes_ln = db.relationship(
            lambda: CollectionPortalbox,
            #collection_class=OrderedList,
            collection_class=ordering_list('score'),
            primaryjoin=lambda: \
                Collection.id == CollectionPortalbox.id_collection,
            foreign_keys=lambda: CollectionPortalbox.id_collection,
            order_by=lambda: db.asc(CollectionPortalbox.score))

    #@db.hybrid_property
    #def externalcollections(self):
    #    return self._externalcollections

    #@externalcollections.setter
    #def externalcollections(self, data):
    #    if isinstance(data, dict):
    #        for k, vals in data.iteritems():
    #            for v in list(vals):
    #                self._externalcollections[k] = v
    #    else:
    #        self._externalcollections = data

    def breadcrumbs(self, builder=None, ln=None):
        """Retunds breadcrumbs for collection."""
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
                url=url_for('search.collection', name=self.name))

        breadcrumbs.append(crumb)
        return breadcrumbs



class Collectionname(db.Model):
    """Represents a Collectionname record."""
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
        return (self.ln, self.type)

    @ln_type.setter
    def set_ln_type(self, value):
        (self.ln, self.type) = value

#from sqlalchemy import event

#def collection_append_listener(target, value, initiator):
#    print "received append event for target: %s" % target.__dict__
#    print value.__dict__
#    print initiator.__dict__

#event.listen(Collection.names, 'append', collection_append_listener)


class Collectiondetailedrecordpagetabs(db.Model):
    """Represents a Collectiondetailedrecordpagetabs record."""
    __tablename__ = 'collectiondetailedrecordpagetabs'
    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Collection.id),
            nullable=False, primary_key=True)
    tabs = db.Column(db.String(255), nullable=False,
                server_default='')
    collection = db.relationship(Collection,
            backref='collectiondetailedrecordpagetabs')


class CollectionCollection(db.Model):
    """Represents a CollectionCollection record."""
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
                #FIX collection_class=db.attribute_mapped_collection('score'),
                order_by=db.asc(score))
    dad = db.relationship(Collection, primaryjoin=id_dad == Collection.id,
                backref='sons', order_by=db.asc(score))


class Example(db.Model):
    """Represents a Example record."""
    __tablename__ = 'example'
    id = db.Column(db.MediumInteger(9, unsigned=True), primary_key=True,
                autoincrement=True)
    type = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=False)


class CollectionExample(db.Model):
    """Represents a CollectionExample record."""
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
    """Represents a Portalbox record."""
    __tablename__ = 'portalbox'
    id = db.Column(db.MediumInteger(9, unsigned=True), autoincrement=True,
                primary_key=True)
    title = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=False)


def get_pbx_pos():
    """Returns a list of all the positions for a portalbox"""

    position = {}
    position["rt"] = "Right Top"
    position["lt"] = "Left Top"
    position["te"] = "Title Epilog"
    position["tp"] = "Title Prolog"
    position["ne"] = "Narrow by coll epilog"
    position["np"] = "Narrow by coll prolog"
    return position


class CollectionPortalbox(db.Model):
    """Represents a CollectionPortalbox record."""
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
    """Represents a Externalcollection record."""
    __tablename__ = 'externalcollection'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False,
                server_default='')

    @property
    def engine(self):
        from invenio.websearch_external_collections_searcher import external_collections_dictionary

        if self.name in external_collections_dictionary:
            return external_collections_dictionary[self.name]


class CollectionExternalcollection(db.Model):
    """Represents a CollectionExternalcollection record."""
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

    def _collection_type(type):
        return db.relationship(Collection,
            primaryjoin=lambda: db.and_(
                CollectionExternalcollection.id_collection == Collection.id,
                CollectionExternalcollection.type == type),
            backref='_externalcollections_' + str(type))
    collection_0 = _collection_type(0)
    collection_1 = _collection_type(1)
    collection_2 = _collection_type(2)

    externalcollection = db.relationship(Externalcollection)


class CollectionFormat(db.Model):
    """Represents a CollectionFormat record."""
    __tablename__ = 'collection_format'
    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Collection.id), primary_key=True)
    id_format = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Format.id), primary_key=True)
    score = db.Column(db.TinyInteger(4, unsigned=True),
                nullable=False, server_default='0')
    collection = db.relationship(Collection, backref='formats',
                order_by=db.desc(score))
    format = db.relationship(Format, backref='collections',
                order_by=db.desc(score))


class Field(db.Model):
    """Represents a Field record."""

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.id)

    __tablename__ = 'field'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(255), unique=True,
                nullable=False)
    #tags = db.relationship('FieldTag',
    #        collection_class=attribute_mapped_collection('score'),
    #        cascade="all, delete-orphan"
    #    )
    #tag_names = association_proxy("tags", "as_tag")

    @property
    def name_ln(self):
        from invenio.search_engine import get_field_i18nname
        return get_field_i18nname(self.name, g.ln)
        #try:
        #    return db.object_session(self).query(Fieldname).\
        #        with_parent(self).filter(db.and_(Fieldname.ln==g.ln,
        #            Fieldname.type=='ln')).first().value
        #except:
        #    return self.name


class Fieldvalue(db.Model):
    """Represents a Fieldvalue record."""
    def __init__(self):
        pass
    __tablename__ = 'fieldvalue'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Text, nullable=False)


class Fieldname(db.Model):
    """Represents a Fieldname record."""
    __tablename__ = 'fieldname'
    id_field = db.Column(db.MediumInteger(9, unsigned=True),
                         db.ForeignKey(Field.id), primary_key=True)
    ln = db.Column(db.Char(5), primary_key=True, server_default='')
    type = db.Column(db.Char(3), primary_key=True, server_default='sn')
    value = db.Column(db.String(255), nullable=False)
    field = db.relationship(Field, backref='names')


class Tag(db.Model):
    """Represents a Tag record."""
    __tablename__ = 'tag'
    id = db.Column(db.MediumInteger(9, unsigned=True), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Char(6), nullable=False)

    def __init__(self, tup=None, *args, **kwargs):
        if tup is not None and isinstance(tup, tuple):
            self.name, self.value = tup
            super(Tag, self).__init__(*args, **kwargs)
        else:
            if tup is None:
                super(Tag, self).__init__(*args, **kwargs)
            else:
                super(Tag, self).__init__(tup, *args, **kwargs)

    @property
    def as_tag(self):
        """Returns tupple with name and value."""
        return self.name, self.value


class FieldTag(db.Model):
    """Represents a FieldTag record."""
    __tablename__ = 'field_tag'
    id_field = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey('field.id'), nullable=False, primary_key=True)
    id_tag = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey('tag.id'), nullable=False, primary_key=True)
    score = db.Column(db.TinyInteger(4, unsigned=True), nullable=False,
                server_default='0')
    tag = db.relationship(Tag, backref='fields', order_by=score)
    field = db.relationship(Field, backref='tags', order_by=score)

    def __init__(self, score=None, tup=None, *args, **kwargs):
        if score is not None:
            self.score = score
        if tup is not None:
            self.tag = Tag(tup)
        super(FieldTag, self).__init__(*args, **kwargs)

    @property
    def as_tag(self):
        """ Returns Tag record directly."""
        return self.tag


class WebQuery(db.Model):
    """Represents a WebQuery record."""
    __tablename__ = 'query'
    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                autoincrement=True)
    type = db.Column(db.Char(1), nullable=False, server_default='r')
    urlargs = db.Column(db.Text(100), nullable=False, index=True)


class UserQuery(db.Model):
    """Represents a UserQuery record."""
    __tablename__ = 'user_query'
    id_user = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(User.id), primary_key=True, server_default='0')
    id_query = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(WebQuery.id), primary_key=True, index=True,
                server_default='0')
    hostname = db.Column(db.String(50), nullable=True,
                server_default='unknown host')
    date = db.Column(db.DateTime, nullable=True)


class CollectionFieldFieldvalue(db.Model):
    """Represents a CollectionFieldFieldvalue record."""
    __tablename__ = 'collection_field_fieldvalue'
    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Collection.id), primary_key=True, nullable=False)
    id_field = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Field.id), primary_key=True, nullable=False)
    id_fieldvalue = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Fieldvalue.id), primary_key=True, nullable=True)
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


__all__ = ['Collection',
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
           'Field',
           'Fieldvalue',
           'Fieldname',
           'Tag',
           'FieldTag',
           'WebQuery',
           'UserQuery',
           'CollectionFieldFieldvalue']
