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

"""
errorlib database models.
"""

# General imports.
from datetime import datetime
from invenio.base.globals import cfg
from invenio.ext.sqlalchemy import db


def _is_pow_of_2(n):
    """
    Return True if n is a power of 2
    """
    while n > 1:
        if n % 2:
            return False
        n = n / 2
    return True


class HstEXCEPTION(db.Model):
    """Represents a HstEXCEPTION record."""
    __tablename__ = 'hstEXCEPTION'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(255), nullable=True)
    line = db.Column(db.Integer(9), nullable=True)
    last_seen = db.Column(db.DateTime, nullable=False,
                          server_default='1900-01-01 00:00:00', index=True)
    last_notified = db.Column(db.DateTime, nullable=False,
                              server_default='1900-01-01 00:00:00', index=True)
    counter = db.Column(db.Integer(15), nullable=False,
                        server_default='0')
    total = db.Column(db.Integer(15), nullable=False,
                      server_default='0', index=True)

    __table_args__ = (db.Index('name', name, filename, line, unique=True),
                      db.Model.__table_args__)

    @classmethod
    def get_or_create(cls, name, filename, line):
        """Finds or create exception log."""
        try:
            log = cls.query.filter_by(name=name, filename=filename,
                                      line=line).one()
            delta = datetime.datetime.now() - log.last_notified
            reset_counter = (delta.seconds + delta.days * 86400) >= \
                cfg['CFG_ERRORLIB_RESET_EXCEPTION_NOTIFICATION_COUNTER_AFTER']
            counter = 1 if reset_counter else log.counter + 1
            log.update({'last_notified': db.func.now(),
                        'counter': counter,
                        'total': log.total + 1}, synchronize_settion=False)
            db.session.add(log)
        except:
            log = HstEXCEPTION(name=name,
                               filename=filename,
                               line=line,
                               last_seen=datetime.now(),
                               last_notified=datetime.now(),
                               counter=1,
                               total=1)
            db.session.add(log)
        try:
            db.session.commit()
        except:
            db.session.rollback()
        return log

    @property
    def exception_should_be_notified(self):
        return _is_pow_of_2(self.counter)

    @property
    def pretty_notification_info(self):
        return ("This exception has already been seen %s times\n    "
                "last time it was seen: %s\n    "
                "last time it was notified: %s\n" % (
                    self.total,
                    self.last_seen.strftime("%Y-%m-%d %H:%M:%S"),
                    self.last_notified.strftime("%Y-%m-%d %H:%M:%S")))

    @classmethod
    def get_pretty_notification_info(cls, name, filename, line):
        """
        Return a sentence describing when this exception was already seen.
        """
        try:
            return cls.query.filter_by(
                name=name, filename=filename, line=line
            ).one().pretty_notification_info
        except:
            return "It is the first time this exception has been seen.\n"


__all__ = ['HstEXCEPTION']
