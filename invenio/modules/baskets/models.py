# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2015 CERN.
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

"""webbasket database models."""

from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import User, Usergroup
from invenio.modules.collections.models import Collection


class BskBASKET(db.Model):

    """Represents a BskBASKET record."""

    __tablename__ = 'bskBASKET'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                   primary_key=True)
    id_owner = db.Column(
        db.Integer(15, unsigned=True),
        db.ForeignKey(User.id), nullable=False, server_default='0')
    name = db.Column(db.String(50), nullable=False, server_default='',
                     index=True)
    date_modification = db.Column(db.DateTime, nullable=False,
                                  server_default='1900-01-01 00:00:00')
    nb_views = db.Column(db.Integer(15), nullable=False,
                         server_default='0')
    owner = db.relationship(User, backref='baskets')


class BskEXTREC(db.Model):

    """Represents a BskEXTREC record."""

    __tablename__ = 'bskEXTREC'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                   primary_key=True)
    external_id = db.Column(db.Integer(15), nullable=False,
                            server_default='0')
    collection_id = db.Column(db.MediumInteger(9, unsigned=True),
                              db.ForeignKey(Collection.id), nullable=False,
                              server_default='0')
    original_url = db.Column(db.Text, nullable=True)
    creation_date = db.Column(db.DateTime, nullable=False,
                              server_default='1900-01-01 00:00:00')
    modification_date = db.Column(db.DateTime, nullable=False,
                                  server_default='1900-01-01 00:00:00')
    collection = db.relationship(Collection, backref='EXTRECs')


class BskEXTFMT(db.Model):

    """Represents a BskEXTFMT record."""

    __tablename__ = 'bskEXTFMT'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                   primary_key=True)
    id_bskEXTREC = db.Column(db.Integer(15, unsigned=True),
                             db.ForeignKey(BskEXTREC.id), nullable=False,
                             server_default='0')
    format = db.Column(db.String(10), nullable=False, index=True,
                       server_default='')
    last_updated = db.Column(db.DateTime, nullable=False,
                             server_default='1900-01-01 00:00:00')
    value = db.Column(db.iLargeBinary, nullable=True)
    EXTREC = db.relationship(BskEXTREC, backref='EXTFMTs')


class BskREC(db.Model):

    """Represents a BskREC record."""

    __tablename__ = 'bskREC'
    id_bibrec_or_bskEXTREC = db.Column(
        db.Integer(16), nullable=False,
        server_default='0', primary_key=True, index=True)
    id_bskBASKET = db.Column(db.Integer(15, unsigned=True),
                             db.ForeignKey(BskBASKET.id), nullable=False,
                             server_default='0', primary_key=True)
    id_user_who_added_item = db.Column(db.Integer(15, unsigned=True),
                                       db.ForeignKey(User.id),
                                       nullable=False, server_default='0')
    score = db.Column(db.Integer(15), nullable=False,
                      server_default='0')
    date_added = db.Column(db.DateTime, nullable=False, index=True,
                           server_default='1900-01-01 00:00:00')
    basket = db.relationship(BskBASKET, backref='RECs')
    user_who_added_item = db.relationship(User)


class BskRECORDCOMMENT(db.Model):

    """Represents a BskRECORDCOMMENT record."""

    __tablename__ = 'bskRECORDCOMMENT'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    id_bibrec_or_bskEXTREC = db.Column(db.Integer(16), nullable=False,
                                       server_default='0')
    id_bskBASKET = db.Column(db.Integer(15, unsigned=True),
                             db.ForeignKey(BskBASKET.id), nullable=False,
                             server_default='0')
    id_user = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(User.id),
                        nullable=False, server_default='0')
    title = db.Column(db.String(255), nullable=False,
                      server_default='')
    body = db.Column(db.Text, nullable=False)
    date_creation = db.Column(db.DateTime, nullable=False,
                              server_default='1900-01-01 00:00:00', index=True)
    priority = db.Column(db.Integer(15), nullable=False,
                         server_default='0')
    in_reply_to_id_bskRECORDCOMMENT = db.Column(
        db.Integer(15, unsigned=True),
        db.ForeignKey(id), nullable=False, server_default='0')
    reply_order_cached_data = db.Column(db.Binary, nullable=True)
    in_reply_to = db.relationship('BskRECORDCOMMENT')
    basket = db.relationship(BskBASKET, backref='RECORDCOMMENTs')
    user = db.relationship(User)

    __table_args__ = (db.Index('bskRECORDCOMMENT_reply_order_cached_data',
                               reply_order_cached_data, mysql_length=40),
                      db.Model.__table_args__)


class UserBskBASKET(db.Model):

    """Represents a UserBskBASKET record."""

    __tablename__ = 'user_bskBASKET'
    id_user = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(User.id),
                        nullable=False, server_default='0', primary_key=True)
    id_bskBASKET = db.Column(db.Integer(15, unsigned=True),
                             db.ForeignKey(BskBASKET.id), nullable=False,
                             server_default='0', primary_key=True)
    topic = db.Column(db.String(50), nullable=False, server_default='')
    user = db.relationship(User, backref='user_baskets')
    user_basket = db.relationship(BskBASKET, backref='users')


class UsergroupBskBASKET(db.Model):

    """Represents a UsergroupBskBASKET record."""

    __tablename__ = 'usergroup_bskBASKET'
    id_usergroup = db.Column(db.Integer(15, unsigned=True),
                             db.ForeignKey(Usergroup.id), nullable=False,
                             server_default='0', primary_key=True)
    id_bskBASKET = db.Column(db.Integer(15, unsigned=True),
                             db.ForeignKey(BskBASKET.id), nullable=False,
                             server_default='0', primary_key=True)
    topic = db.Column(db.String(50), nullable=False,
                      server_default='')
    date_shared = db.Column(db.DateTime, nullable=False,
                            server_default='1900-01-01 00:00:00')
    share_level = db.Column(db.Char(2), nullable=False, server_default='')
    usergroup = db.relationship(Usergroup, backref='usergroup_baskets')
    usergroup_basket = db.relationship(BskBASKET, backref='usergroups')


__all__ = ('BskBASKET',
           'BskEXTREC',
           'BskEXTFMT',
           'BskREC',
           'BskRECORDCOMMENT',
           'UserBskBASKET',
           'UsergroupBskBASKET')
