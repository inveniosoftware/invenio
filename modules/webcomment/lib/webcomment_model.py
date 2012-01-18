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
webcomment database models.
"""

# General imports.
from invenio.sqlalchemyutils import db

# Create your models here.

from bibedit_model import Bibrec
from websession_model import User

class CmtRECORDCOMMENT(db.Model):
    """Represents a CmtRECORDCOMMENT record."""
    def __init__(self):
        pass
    __tablename__ = 'cmtRECORDCOMMENT'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True, autoincrement=True)
    id_bibrec = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(Bibrec.id),
                nullable=False, server_default='0') # CmtRECORDCINNENT
    id_user = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(User.id),
                nullable=False, server_default='0')
    title = db.Column(db.String(255), nullable=False,
                server_default='')
    body = db.Column(db.Text, nullable=False)
    date_creation = db.Column(db.DateTime, nullable=False,
                server_default='0000-00-00 00:00:00')
    star_score = db.Column(db.TinyInteger(5, unsigned=True), nullable=False,
                server_default='0')
    nb_votes_yes = db.Column(db.Integer(10), nullable=False,
                server_default='0')
    nb_votes_total = db.Column(db.Integer(10, unsigned=True), nullable=False,
                server_default='0')
    nb_abuse_reports = db.Column(db.Integer(10), nullable=False,
                server_default='0')
    status = db.Column(db.Char(2), nullable=False,
                server_default='ok')
    round_name = db.Column(db.String(255), nullable=False,
                server_default='')
    restriction = db.Column(db.String(50), nullable=False,
                server_default='')
    in_reply_to_id_cmtRECORDCOMMENT = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(id), nullable=False, server_default='0')
    reply_order_cached_data = db.Column(db.iBinary,
                nullable=True)
    bibrec = db.relationship(Bibrec, backref='recordcomments')
    user = db.relationship(User, backref='recordcomments')
    in_reply_to = db.relationship('CmtRECORDCOMMENT')#FIX ME,
                #backref='replies')

class CmtACTIONHISTORY(db.Model):
    """Represents a CmtACTIONHISTORY record."""
    def __init__(self):
        pass
    __tablename__ = 'cmtACTIONHISTORY'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True,
                autoincrement=True)
    id_cmtRECORDCOMMENT = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(CmtRECORDCOMMENT.id),
            nullable=True)
    id_bibrec = db.Column(db.Integer(15, unsigned=True),
                db.ForeignKey(Bibrec.id),
                nullable=True, primary_key=True)
    id_user = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(User.id),
                nullable=True)
    client_host = db.Column(db.Integer(10, unsigned=True),
                nullable=True)
    action_time = db.Column(db.DateTime, nullable=False,
                server_default='0000-00-00 00:00:00')
    action_code = db.Column(db.Char(1), nullable=False)
    recordcomment = db.relationship(CmtRECORDCOMMENT,
                backref='actionhistory')
    bibrec = db.relationship(Bibrec)
    user = db.relationship(User)


class CmtSUBSCRIPTION(db.Model):
    """Represents a CmtSUBSCRIPTION record."""
    def __init__(self):
        pass
    __tablename__ = 'cmtSUBSCRIPTION'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id), nullable=False,
                primary_key=True)
    id_user = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(User.id),
                nullable=False,
                primary_key=True)
    creation_time = db.Column(db.DateTime, nullable=False,
                server_default='0000-00-00 00:00:00',
                primary_key=True)
    bibrec = db.relationship(Bibrec)
    user = db.relationship(User)

