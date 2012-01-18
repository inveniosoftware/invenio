# -*- coding: utf-8 -*-
#
## Author: Jiri Kuncar <jiri.kuncar@gmail.com> 
##
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
websearch database models.
"""

# General imports.
from invenio.sqlalchemyutils import db

# Create your models here.

from invenio.websession_model import User

#class NodeMap(db.MappedCollection):
#    """Holds 'Node' objects, keyed by the 'name' attribute with insert
#    order maintained."""
#    def __init__(self, *args, **kw):
#        db.MappedCollection.__init__(self, keyfunc=lambda name: name.type_ln)
#
#    #@collection.internally_instrumented
#    def __setitem__(self, key, value, _sa_initiator=None):
#        print "Key Mapped Collection"
#        print key
#        print value.__dict__
#        new_key = self.keyfunc(value)
#        if new_key != key:
#            try:
#                super(NodeMap, self).__delitem__(self.keyfunc(value))
#            except:
#                pass
#            value.type_ln = key
#        super(NodeMap, self).__setitem__(key,
#                value)
#
#    #@collection.internally_instrumented
#    def __delitem__(self, key, _sa_initiator=None):
#        super(NodeMap, self).__delitem__(key)


class Collection(db.Model):
    """Represents a Collection record."""
    def __init__(self):
        pass
    __tablename__ = 'collection'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True)
    name = db.Column(db.String(255), unique=True, index=True,
                nullable=False)
    dbquery = db.Column(db.Text(20), nullable=True,
                index=True)
    nbrecs = db.Column(db.Integer(10, unsigned=True),
                server_default='0')
    reclist = db.Column(db.iLargeBinary)
    names = db.relationship("Collectionname",
                         backref='collection',
                         #collection_class=NodeMap
                         #mapped_collection(keyfunc=lambda name: name.type_ln)
                         #ln + ":" + name.type)
                         )

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
    #collection = db.relationship(Collection, backref='names')

#    @hybrid_property
#    def type_ln(self):
#        #return self.type + ":" + self.ln
#        return (self.type, self.ln)

#    @type_ln.setter
#    def type_ln(self, value):
#        #print self.__dict__
#        #assoc_collection = self.collection
#        #try:
#        #    assoc_collection.names.remove(self)
#        #except:
#        #    pass
#        #(self.type, self.ln) = value.split(":")
#        (self.type, self.ln) = value
#        #print self.__dict__
#        #try:
#        #    assoc_collection.names.set(self)
#        #except:
#        #    pass

#from sqlalchemy import event

#def collection_append_listener(target, value, initiator):
#    print "received append event for target: %s" % target.__dict__
#    print value.__dict__
#    print initiator.__dict__

#event.listen(Collection.names, 'append', collection_append_listener)

class Collectiondetailedrecordpagetabs(db.Model):
    """Represents a Collectiondetailedrecordpagetabs record."""
    def __init__(self):
        pass
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
    def __init__(self):
        pass
    __tablename__ = 'collection_collection'
    id_dad = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Collection.id), primary_key=True)
    id_son = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Collection.id), primary_key=True)
    type = db.Column(db.Char(1), nullable=False,
                server_default='r')
    score = db.Column(db.TinyInteger(4, unsigned=True), nullable=False,
                server_default='0')
    son = db.relationship(Collection, primaryjoin=id_son==Collection.id,
                backref='dads',
                #FIX collection_class=db.attribute_mapped_collection('score'),
                order_by=score)
    dad = db.relationship(Collection, primaryjoin=id_dad==Collection.id,
            backref='sons', order_by=score)

class Example(db.Model):
    """Represents a Example record."""
    def __init__(self):
        pass
    __tablename__ = 'example'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    type = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=False)

class CollectionExample(db.Model):
    """Represents a CollectionExample record."""
    def __init__(self):
        pass
    __tablename__ = 'collection_example'
    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Collection.id), primary_key=True)
    id_example = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Example.id), primary_key=True)
    score = db.Column(db.TinyInteger(4, unsigned=True), nullable=False,
                server_default='0')
    collection = db.relationship(Collection, backref='examples',
                order_by=score)
    example = db.relationship(Example, backref='collections',
                order_by=score)

class Portalbox(db.Model):
    """Represents a Portalbox record."""
    def __init__(self):
        pass
    __tablename__ = 'portalbox'
    id = db.Column(db.MediumInteger(9, unsigned=True), autoincrement=True,
                primary_key=True)
    title = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=False)

class CollectionPortalbox(db.Model):
    """Represents a CollectionPortalbox record."""
    def __init__(self):
        pass
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
    def __init__(self):
        pass
    __tablename__ = 'externalcollection'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False,
                server_default='')

class CollectionExternalcollection(db.Model):
    """Represents a CollectionExternalcollection record."""
    def __init__(self):
        pass
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
    collection = db.relationship(Collection, backref='externalcollections')
    externalcollection = db.relationship(Externalcollection) #,
                                    # backref='collections')

class Format(db.Model):
    """Represents a Format record."""
    def __init__(self):
        pass
    __tablename__ = 'format'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True,
                autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    description = db.Column(db.String(255), server_default='')
    content_type = db.Column(db.String(255), server_default='')
    visibility = db.Column(db.TinyInteger(4), nullable=False,
                server_default='1')

class CollectionFormat(db.Model):
    """Represents a CollectionFormat record."""
    def __init__(self):
        pass
    __tablename__ = 'collection_format'
    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Collection.id), primary_key=True)
    id_format = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Externalcollection.id), primary_key=True)
    score = db.Column(db.TinyInteger(4, unsigned=True),
                nullable=False,
            server_default='0')
    collection = db.relationship(Collection, backref='formats',
                order_by=score)
    format = db.relationship(Externalcollection,
                backref='collections',
            order_by=score)

class Formatname(db.Model):
    """Represents a Formatname record."""
    def __init__(self):
        pass
    __tablename__ = 'formatname'
    id_format = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Format.id), primary_key=True)
    ln = db.Column(db.Char(5), primary_key=True,
                server_default='')
    type = db.Column(db.Char(3), primary_key=True,
                server_default='sn')
    value = db.Column(db.String(255), nullable=False)
    format = db.relationship(Format, backref='names')

class Field(db.Model):
    """Represents a Field record."""
    def __init__(self):
        pass
    __tablename__ = 'field'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True)
    name = db.Column(db.String(255), unique=True,
                nullable=False)
    code = db.Column(db.String(255), nullable=False)
    #tags = db.relationship('FieldTag',
    #        collection_class=attribute_mapped_collection('score'),
    #        cascade="all, delete-orphan"
    #    )
    #tag_names = association_proxy("tags", "as_tag")

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
    def __init__(self):
        pass
    __tablename__ = 'fieldname'
    id_field = db.Column(db.MediumInteger(9, unsigned=True), db.ForeignKey(Field.id),
                primary_key=True)
    ln = db.Column(db.Char(5), primary_key=True,
                server_default='')
    type = db.Column(db.Char(3), primary_key=True,
                server_default='sn')
    value = db.Column(db.String(255), nullable=False)
    field = db.relationship(Field, backref='names')

class Tag(db.Model):
    """Represents a Tag record."""
    __tablename__ = 'tag'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Char(6), nullable=False)

    def __init__(self, tup):
        self.name, self.value = tup

    @property
    def as_tag(self):
        """Returns tupple with name and value."""
        return self.name, self.value

class FieldTag(db.Model):
    """Represents a FieldTag record."""
    __tablename__ = 'field_tag'
    id_field = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey('field.id'),
            nullable=False, primary_key=True)
    id_tag = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey("tag.id"),
            nullable=False, primary_key=True)
    score = db.Column(db.TinyInteger(4, unsigned=True),
                nullable=False,
            server_default='0')

    tag = db.relationship(Tag, backref='fields',
                order_by=score)
    field = db.relationship(Field, backref='tags',
                order_by=score)

    def __init__(self, score, tup):
        self.score = score
        self.tag = Tag(tup)

    @property
    def as_tag(self):
        """ Returns Tag record directly."""
        return self.tag

class WebQuery(db.Model):
    """Represents a WebQuery record."""
    def __init__(self):
        pass
    __tablename__ = 'query'
    id = db.Column(db.Integer(15, unsigned=True),
                primary_key=True,
                autoincrement=True)
    type = db.Column(db.Char(1), nullable=False,
                server_default='r')
    urlargs = db.Column(db.Text, nullable=False)

class UserQuery(db.Model):
    """Represents a UserQuery record."""
    def __init__(self):
        pass
    __tablename__ = 'user_query'
    id_user = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(User.id),
            primary_key=True, server_default='0')
    id_query = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(WebQuery.id),
                primary_key=True,
            index=True, server_default='0')
    hostname = db.Column(db.String(50), nullable=True,
                server_default='unknown host')
    date = db.Column(db.DateTime, nullable=True)

class CollectionFieldFieldvalue(db.Model):
    """Represents a CollectionFieldFieldvalue record."""
    def __init__(self):
        pass
    __tablename__ = 'collection_field_fieldvalue'
    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Collection.id), primary_key=True,
            nullable=False)
    id_field = db.Column(db.MediumInteger(9, unsigned=True), db.ForeignKey(Field.id),
                primary_key=True,
            nullable=False)
    id_fieldvalue = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Fieldvalue.id), primary_key=True,
            nullable=True)
    type = db.Column(db.Char(3), nullable=False,
                server_default='src') 
    score = db.Column(db.TinyInteger(4, unsigned=True), nullable=False,
                server_default='0')
    score_fieldvalue = db.Column(db.TinyInteger(4, unsigned=True), nullable=False,
                server_default='0')
    collection = db.relationship(Collection, backref='field_fieldvalues')
    field = db.relationship(Field, backref='collection_fieldvalues')
    fieldvalue = db.relationship(Fieldvalue, backref='collection_fields')

from bibclassify_model import ClsMETHOD

class CollectionClsMETHOD(db.Model):
    """Represents a Collection_clsMETHOD record."""
    def __init__(self):
        pass
    __tablename__ = 'collection_clsMETHOD'
    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Collection.id), primary_key=True,
            nullable=False)
    id_clsMETHOD = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(ClsMETHOD.id), primary_key=True,
            nullable=False)
    collection = db.relationship(Collection, backref='clsMETHODs')
    clsMETHOD = db.relationship(ClsMETHOD, backref='collections')

from bibrank_model import RnkMETHOD

class CollectionRnkMETHOD(db.Model):
    """Represents a CollectionRnkMETHOD record."""
    def __init__(self):
        pass
    __tablename__ = 'collection_rnkMETHOD'
    id_collection = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Collection.id), primary_key=True,
            nullable=False)
    id_rnkMETHOD = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(RnkMETHOD.id), primary_key=True,
            nullable=False)
    score = db.Column(db.TinyInteger(4, unsigned=True),
                nullable=False,
            server_default='0')
    collection = db.relationship(Collection, backref='rnkMETHODs')
    rnkMETHOD = db.relationship(RnkMETHOD, backref='collections')


