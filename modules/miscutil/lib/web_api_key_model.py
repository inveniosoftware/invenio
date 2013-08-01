# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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
Web API Key database models.
"""
# General imports.
from invenio.sqlalchemyutils import db

# Create your models here.
from invenio.websession_model import User

class WebAPIKey(db.Model):
    """Represents a Web API Key record."""
    def __str__(self):
        return "%s <%s>" % (self.nickname, self.email)
    __tablename__ = 'webapikey'
    id = db.Column(db.String(150), primary_key=True, nullable=False)
    secret = db.Column(db.String(150), nullable=False)
    id_user = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(User.id),
                        nullable=False)
    status = db.Column(db.String(25), nullable=False,
                   server_default='OK', index=True)
    description = db.Column(db.String(255), nullable=True)
