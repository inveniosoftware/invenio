# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2015 CERN.
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

"""sequencegenerator backend."""

from invenio.legacy.dbquery import run_sql

from sqlalchemy.exc import IntegrityError


# Number of retries to insert a value in the DB storage
MAX_DB_RETRY = 10


class SequenceGenerator(object):

    """Sequence generator."""

    seq_name = None

    def __init__(self):
        """Init."""
        assert self.seq_name

    def _value_exists(self, value):
        """Check if the value exists in the storage.

        :param value: value to be checked in storage
        :type value: string

        :return: result of select SQL query
        :rtype: tuple
        """
        return run_sql("""SELECT seq_value FROM "seqSTORE"
                       WHERE seq_value=%s AND seq_name=%s""",
                       (value, self.seq_name))

    def _insert_value(self, value):
        """Insert value into storage.

        :param value: value to be stored
        :type value: string

        :return: result of insert SQL query
        :rtype: tuple
        """
        run_sql("""INSERT INTO "seqSTORE" (seq_name, seq_value)
                VALUES (%s, %s)""",
                (self.seq_name, value))

    def _next_value(self, *args, **kwargs):
        """Internal implementation to calculate next value in sequence."""
        raise NotImplementedError

    def next_value(self, *args, **kwargs):
        """Get the next value in the sequence.

        :return: next value in sequence
        :rtype: string
        """
        db_retries = 0
        value = None
        while MAX_DB_RETRY > db_retries:
            value = self._next_value(*args, **kwargs)
            try:
                self._insert_value(value)
                break
            except IntegrityError:
                # The value is already in the storage, get next one
                db_retries += 1

        return value
