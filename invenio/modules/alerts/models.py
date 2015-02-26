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
from datetime import datetime
from time import strftime

from invenio.ext.sqlalchemy import db, utils
from invenio.base.i18n import _

# Create your models here.

from invenio.modules.accounts.models import User
from invenio.modules.baskets.models import BskBASKET
from invenio.modules.search.models import WebQuery

from .utils import logger


class UserQueryBasket(db.Model):

    """Represent a UserQueryBasket record."""

    FREQUENCIES = {
        'day': _('Day'),
        'week': _('Week'),
        'month': _('Month'),
    }

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
    date_creation = db.Column(db.Date, nullable=True, default=datetime.now)
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

    @db.validates('frequency')
    def validate_frequency(self, key, value):
        assert value in self.FREQUENCIES
        return value

    @staticmethod
    def exists(id_query):
        """Return True if already exists a alert for a specific query.

        :param id_query: query id
        :return: True if exists
        """
        return db.session.query(UserQueryBasket.query.filter(
            UserQueryBasket.id_query.like(id_query)).exists()).scalar()

    @classmethod
    def get_query_alerts(cls, date, **kwargs):
        frequencies = ['day']
        if date.isoweekday() == 1:
            frequencies.append('week')
        if date.day == 1:
            frequencies.append('month')

        return cls.query.filter(cls.frequency.in_(frequencies),
                                cls.date_lastrun <= date).filter_by(**kwargs)

    @utils.session_manager
    def run(self, date_until):

        if self.frequency == 'day':
            date_from = date_until - datetime.timedelta(days=1)

        elif self.frequency == 'week':
            date_from = date_until - datetime.timedelta(weeks=1)

        else:
            # Months are not an explicit notion of timedelta (it's the
            # most ambiguous too). So we explicitely take the same day of
            # the previous month.
            d, m, y = (date_until.day, date_until.month, date_until.year)
            m = m - 1

            if m == 0:
                m = 12
                y = y - 1

            date_from = datetime.date(year=y, month=m, day=d)

        from invenio.ext.logging import register_exception
        from invenio.legacy.webalert.alert_engine import get_record_ids
        records = get_record_ids(self.webquery.urlargs, date_from, date_until)

        n = len(records[0])
        if n:
            logger.info(
                'query %08s produced %08s records for all the local '
                'collections' % (self.id_query, n))

        for external_collection_results in records[1][0]:
            n = len(external_collection_results[1][0])
            if n:
                logger.info(
                    'query %08s produced %08s records for external collection '
                    '\"%s\"' % (
                        self.id_query, n, external_collection_results[0]))

        logger.debug(
            "[%s] run query: %s with dates: from=%s, until=%s\n"
            "  found rec ids: %s" % (
                strftime("%c"), str(self.to_dict()), date_from, date_until,
                records))

        if self.id_basket:
            from invenio.legacy.webalert.alert_engine import \
                add_records_to_basket
            add_records_to_basket(records, self.id_basket)
        if self.notifications == 'y':
            from invenio.legacy.webalert.alert_engine import \
                update_arguments
            argstr = update_arguments(self.webquery.argstr, date_from,
                                      date_until)
            try:
                email_notify(a, records, argstr)
            except Exception:
                # There were troubles sending this alert, so register
                # this exception and continue with other alerts:
                register_exception(
                    alert_admin=True,
                    prefix="Error when sending alert %s, %s\n." % (
                        repr(self), repr(argstr)))
        # Inform the admin when external collections time out
        if len(records[1][1]) > 0:
            register_exception(
                alert_admin=True,
                prefix=("External collections %s timed out when sending "
                        "alert %s, %s\n." % (", ".join(records[1][1]),
                                             repr(self), repr(argstr))))

        self.date_lastrun = datetime.now()
        db.session.add(self)


__all__ = ('UserQueryBasket', )
