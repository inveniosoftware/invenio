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

"""Database models for search engine."""

import datetime

from flask import g, request

from flask_login import current_user

from invenio.base.globals import cfg
from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import User

from sqlalchemy.schema import Index


class Field(db.Model):

    """Represent a Field record."""

    def __repr__(self):
        """Get repr."""
        return "%s(%s)" % (self.__class__.__name__, self.id)

    __tablename__ = 'field'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(255), unique=True,
                     nullable=False)

    @property
    def name_ln(self):
        """Get name ln."""
        from .cache import get_field_i18nname
        return get_field_i18nname(self.name,
                                  getattr(g, 'ln', cfg['CFG_SITE_LANG']))
        # try:
        #    return db.object_session(self).query(Fieldname).\
        #        with_parent(self).filter(db.and_(Fieldname.ln==g.ln,
        #            Fieldname.type=='ln')).first().value
        # except Exception:
        #    return self.name

    @classmethod
    def get_field_name(cls, code):
        """Return field name for given code."""
        return cls.query.filter_by(code=code).value(cls.name)

    @classmethod
    def get_field_tags(cls, code, tagtype='marc'):
        """Yield tag values for given field code."""
        column = Tag.value if tagtype == 'marc' else Tag.recjson_value
        tags = cls.query.join(cls.tags).join(FieldTag.tag).filter(
            cls.code == code
        ).values(column)
        for tag in tags:
            for value in tag[0].split(','):
                yield value.strip()


class Fieldvalue(db.Model):

    """Represent a Fieldvalue record."""

    def __init__(self):
        """Init."""
        pass
    __tablename__ = 'fieldvalue'
    id = db.Column(db.MediumInteger(9, unsigned=True),
                   primary_key=True,
                   autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Text, nullable=False)


class Fieldname(db.Model):

    """Represent a Fieldname record."""

    __tablename__ = 'fieldname'
    id_field = db.Column(db.MediumInteger(9, unsigned=True),
                         db.ForeignKey(Field.id), primary_key=True)
    ln = db.Column(db.Char(5), primary_key=True, server_default='')
    type = db.Column(db.Char(3), primary_key=True, server_default='sn')
    value = db.Column(db.String(255), nullable=False)
    field = db.relationship(Field, backref='names')


class Tag(db.Model):

    """Represent a Tag record."""

    __tablename__ = 'tag'
    id = db.Column(db.MediumInteger(9, unsigned=True), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Char(6), nullable=False, server_default='')
    recjson_value = db.Column(db.Text, nullable=False)

    def __init__(self, tup=None, *args, **kwargs):
        """Init."""
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
        """Return tupple with name and value."""
        return self.name, self.value


class FieldTag(db.Model):

    """Represent a FieldTag record."""

    __tablename__ = 'field_tag'
    id_field = db.Column(db.MediumInteger(9, unsigned=True),
                         db.ForeignKey('field.id'), nullable=False,
                         primary_key=True)
    id_tag = db.Column(db.MediumInteger(9, unsigned=True),
                       db.ForeignKey('tag.id'), nullable=False,
                       primary_key=True)
    score = db.Column(db.TinyInteger(4, unsigned=True), nullable=False,
                      server_default='0')
    tag = db.relationship(Tag, backref='fields', order_by=score)
    field = db.relationship(Field, backref='tags', order_by=score)

    def __init__(self, score=None, tup=None, *args, **kwargs):
        """Init."""
        if score is not None:
            self.score = score
        if tup is not None:
            self.tag = Tag(tup)
        super(FieldTag, self).__init__(*args, **kwargs)

    @property
    def as_tag(self):
        """Return Tag record directly."""
        return self.tag


class WebQuery(db.Model):

    """Represent a WebQuery record."""

    __tablename__ = 'query'
    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                   autoincrement=True)
    type = db.Column(db.Char(1), nullable=False, server_default='r')
    urlargs = db.Column(
        db.Text().with_variant(db.Text(100), 'mysql'),
        nullable=False)


Index('ix_query_urlargs', WebQuery.urlargs, mysql_length=100)


class UserQuery(db.Model):

    """Represent a UserQuery record."""

    __tablename__ = 'user_query'
    id_user = db.Column(db.Integer(15, unsigned=True),
                        db.ForeignKey(User.id), primary_key=True,
                        server_default='0')
    id_query = db.Column(db.Integer(15, unsigned=True),
                         db.ForeignKey(WebQuery.id), primary_key=True,
                         index=True, server_default='0')
    hostname = db.Column(db.String(50), nullable=True,
                         server_default='unknown host')
    date = db.Column(db.DateTime, nullable=True,
                     default=datetime.datetime.now)

    webquery = db.relationship(WebQuery, backref='executions')

    @classmethod
    def log(cls, urlargs=None, id_user=None):
        """Log."""
        id_user = id_user if not None else current_user.get_id()
        urlargs = urlargs or request.query_string
        if id_user < 0:
            return
        webquery = WebQuery.query.filter_by(urlargs=urlargs).first()
        if webquery is None:
            webquery = WebQuery(urlargs=urlargs)
        db.session.add(cls(id_user=id_user, hostname=request.host,
                           webquery=webquery))
        db.session.commit()


__all__ = (
    'Field',
    'Fieldvalue',
    'Fieldname',
    'Tag',
    'FieldTag',
    'WebQuery',
    'UserQuery',
)
