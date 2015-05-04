# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2015 CERN.
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

"""WebComment database models."""

from invenio.base.signals import record_after_update
from invenio.ext.sqlalchemy import db
from invenio.ext.sqlalchemy.utils import session_manager
from invenio.modules.accounts.models import User
from invenio.modules.records.models import Record as Bibrec

from sqlalchemy import event


class CmtRECORDCOMMENT(db.Model):

    """Represents a CmtRECORDCOMMENT record."""

    __tablename__ = 'cmtRECORDCOMMENT'

    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id), nullable=False,
                          server_default='0')
    id_user = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(User.id),
                        nullable=False, server_default='0')
    title = db.Column(db.String(255), nullable=False, server_default='')
    body = db.Column(db.Text, nullable=False)
    date_creation = db.Column(db.DateTime, nullable=False,
                              server_default='1900-01-01 00:00:00')
    star_score = db.Column(db.TinyInteger(5, unsigned=True), nullable=False,
                           server_default='0')
    nb_votes_yes = db.Column(db.Integer(10), nullable=False, server_default='0')
    nb_votes_total = db.Column(db.Integer(10, unsigned=True), nullable=False,
                               server_default='0')
    nb_abuse_reports = db.Column(db.Integer(10), nullable=False,
                                 server_default='0')
    status = db.Column(db.Char(2), nullable=False, index=True,
                       server_default='ok')
    round_name = db.Column(db.String(255), nullable=False, server_default='')
    restriction = db.Column(db.String(50), nullable=False, server_default='')
    in_reply_to_id_cmtRECORDCOMMENT = db.Column(db.Integer(15, unsigned=True),
                                                db.ForeignKey(id),
                                                nullable=False,
                                                server_default='0')
    reply_order_cached_data = db.Column(db.Binary, nullable=True)
    bibrec = db.relationship(Bibrec, backref='recordcomments')
    user = db.relationship(User, backref='recordcomments')
    replies = db.relationship('CmtRECORDCOMMENT', backref=db.backref(
        'parent', remote_side=[id], order_by=date_creation))

    @property
    def is_deleted(self):
        """Check if is deleted."""
        return self.status != 'ok'

    def is_collapsed(self, id_user):
        """Return true if the comment is collapsed by user."""
        return CmtCOLLAPSED.query.filter(db.and_(
            CmtCOLLAPSED.id_bibrec == self.id_bibrec,
            CmtCOLLAPSED.id_cmtRECORDCOMMENT == self.id,
            CmtCOLLAPSED.id_user == id_user)).count() > 0

    @session_manager
    def collapse(self, id_user):
        """Collapse comment beloging to user."""
        c = CmtCOLLAPSED(id_bibrec=self.id_bibrec, id_cmtRECORDCOMMENT=self.id,
                         id_user=id_user)
        db.session.add(c)
        db.session.commit()

    def expand(self, id_user):
        """Expand comment beloging to user."""
        CmtCOLLAPSED.query.filter(db.and_(
            CmtCOLLAPSED.id_bibrec == self.id_bibrec,
            CmtCOLLAPSED.id_cmtRECORDCOMMENT == self.id,
            CmtCOLLAPSED.id_user == id_user)).delete(synchronize_session=False)

    __table_args__ = (db.Index('cmtRECORDCOMMENT_reply_order_cached_data',
                               reply_order_cached_data, mysql_length=40),
                      db.Model.__table_args__)


@event.listens_for(CmtRECORDCOMMENT, 'after_insert')
def after_insert(mapper, connection, target):
    """Update reply order cache  and send record-after-update signal."""
    record_after_update.send(CmtRECORDCOMMENT, recid=target.id_bibrec)

    from .api import get_reply_order_cache_data
    if target.in_reply_to_id_cmtRECORDCOMMENT > 0:
        parent = CmtRECORDCOMMENT.query.get(
            target.in_reply_to_id_cmtRECORDCOMMENT)
        if parent:
            trans = connection.begin()
            parent_reply_order = parent.reply_order_cached_data \
                if parent.reply_order_cached_data else ''
            parent_reply_order += get_reply_order_cache_data(target.id)
            connection.execute(
                db.update(CmtRECORDCOMMENT.__table__).
                where(CmtRECORDCOMMENT.id == parent.id).
                values(reply_order_cached_data=parent_reply_order))
            trans.commit()


class CmtACTIONHISTORY(db.Model):

    """Represents a CmtACTIONHISTORY record."""

    __tablename__ = 'cmtACTIONHISTORY'
    id_cmtRECORDCOMMENT = db.Column(db.Integer(15, unsigned=True),
                                    db.ForeignKey(CmtRECORDCOMMENT.id),
                                    nullable=True, primary_key=True)
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id), nullable=True,
                          primary_key=True)
    id_user = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(User.id),
                        nullable=True, primary_key=True)
    client_host = db.Column(db.Integer(10, unsigned=True), nullable=True)
    action_time = db.Column(db.DateTime, nullable=False,
                            server_default='1900-01-01 00:00:00')
    action_code = db.Column(db.Char(1), nullable=False, index=True)
    recordcomment = db.relationship(CmtRECORDCOMMENT, backref='actionhistory')
    bibrec = db.relationship(Bibrec)
    user = db.relationship(User)


class CmtSUBSCRIPTION(db.Model):

    """Represents a CmtSUBSCRIPTION record."""

    __tablename__ = 'cmtSUBSCRIPTION'

    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id), nullable=False,
                          primary_key=True)
    id_user = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(User.id),
                        nullable=False, primary_key=True)
    creation_time = db.Column(db.DateTime, nullable=False,
                              server_default='1900-01-01 00:00:00')

    bibrec = db.relationship(Bibrec)
    user = db.relationship(User, backref='comment_subscriptions')


class CmtCOLLAPSED(db.Model):

    """Represents a CmtCOLLAPSED record."""

    __tablename__ = 'cmtCOLLAPSED'

    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id), primary_key=True)
    id_cmtRECORDCOMMENT = db.Column(db.Integer(15, unsigned=True),
                                    db.ForeignKey(CmtRECORDCOMMENT.id),
                                    primary_key=True)
    id_user = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(User.id),
                        primary_key=True)


__all__ = ('CmtRECORDCOMMENT',
           'CmtACTIONHISTORY',
           'CmtSUBSCRIPTION',
           'CmtCOLLAPSED')
