# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2014 CERN.
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

"""Alert database models."""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.

from invenio.modules.accounts.models import User
from invenio.modules.baskets.models import BskBASKET
from invenio.modules.search.models import WebQuery


class UserQueryBasket(db.Model):

    """Represent a UserQueryBasket record."""

    __tablename__ = 'user_query_basket'

    id_user = db.Column(db.Integer(15, unsigned=True),
                        db.ForeignKey(User.id), nullable=False,
                        server_default='0', primary_key=True)
    id_query = db.Column(db.Integer(15, unsigned=True),
                         db.ForeignKey(WebQuery.id), nullable=False,
                         server_default='0', primary_key=True,
                         index=True)
    id_basket = db.Column(db.Integer(15, unsigned=True),
                          db.ForeignKey(BskBASKET.id), nullable=False,
                          server_default='0', primary_key=True,
                          index=True)
    frequency = db.Column(db.String(5), nullable=False, server_default='',
                          primary_key=True)
    date_creation = db.Column(db.Date, nullable=True)
    date_lastrun = db.Column(db.Date, nullable=True,
                             server_default='1900-01-01')
    alert_name = db.Column(db.String(30), nullable=False,
                           server_default='', index=True)
    alert_desc = db.Column(db.Text)
    alert_recipient = db.Column(db.Text)
    notification = db.Column(db.Char(1), nullable=False,
                             server_default='y')

    user = db.relationship(User, backref='query_baskets')
    webquery = db.relationship(WebQuery, backref='user_baskets')
    basket = db.relationship(BskBASKET, backref='user_queries')


__all__ = ('UserQueryBasket', )
