# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Reserve record identifier."""

from invenio.modules.pidstore.models import PersistentIdentifier

from invenio_records.signals import before_record_insert


@before_record_insert.connect
def reserve_recid(record, *args, **kwargs):
    """Reserve a new record id for the record and set it inside."""
    if record.get('recid', None) is None:
        pid = PersistentIdentifier.create('recid', pid_value=None,
                                          pid_provider='invenio')
        pid.reserve()
        record['recid'] = int(pid.pid_value)


# FIXME @after_record_insert.connect
# FIXME maybe also @after_record_update.connect
def update_pidstore(record, *args, **kwargs):
    """Save each PID present in the record to the PID storage."""
    if not hasattr(record, 'persistent_identifiers'):
        return

    for pid_name, pid_values in record.persistent_identifiers:
        for pid_value in pid_values:
            pid = PersistentIdentifier.get(
                pid_value.get('type'), pid_value.get('value'),
                pid_value.get('provider'))
            if pid is None:
                pid = PersistentIdentifier.create(
                    pid_value.get('type'), pid_value.get('value'),
                    pid_value.get('provider'))
            if not pid.has_object('rec', record['recid']):
                pid.assign('rec', record['recid'])
