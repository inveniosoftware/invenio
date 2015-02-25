# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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
    invenio.modules.pid_store.providers.local_doi_provider
    ----------------------------------------------------------

"""

from sqlalchemy.exc import SQLAlchemyError

from invenio.ext.sqlalchemy import db
from invenio.modules.records.models import Record

from invenio.modules.pidstore.provider import PidProvider


class RecordID(PidProvider):
    """ Provider for recids"""

    pid_type = 'recid'

    def create_new_pid(self, pid_value):
        """
        Creates a new row inside the ``Record`` table.

        If ``pid_value`` is not ``None`` will be use as ``id`` to create this
        new row.
        """
        if pid_value is not None:
            record = Record(id=int(pid_value))
        else:
            record = Record()
        try:
            db.session.add(record)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise ValueError("Duplicate value for %s" % (pid_value, ))
        return str(record.id)

    def reserve(self, pid, *args, **kwargs):
        pid.log("RESERVE", "Successfully reserved recid")
        return True

    @classmethod
    def is_provider_for_pid(cls, pid_str):
        """
        A recid is valid is it is ``None`` or ``Integer``.
        """
        return pid_str is None or pid_str.isdigit()
