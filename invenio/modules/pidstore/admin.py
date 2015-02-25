# -*- coding: utf-8 -*-
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

from __future__ import absolute_import

from invenio.ext.admin.views import ModelView
from invenio.ext.sqlalchemy import db
from invenio.modules.pidstore.models import PersistentIdentifier, PidLog


class PersistentIdentifierAdmin(ModelView):
    _can_create = False
    _can_edit = False
    _can_delete = False

    column_list = (
        'pid_type', 'pid_value', 'status', 'created', 'last_modified'
    )
    column_searchable_list = ('pid_value',)
    column_choices = {
        'status': {
            'N': 'NEW',
            'R': 'REGISTERED',
            'K': 'RESERVED',
            'D': 'INACTIVE',
        }
    }
    page_size = 100

    def __init__(self, model, session, **kwargs):
        super(PersistentIdentifierAdmin, self).__init__(
            model, session, **kwargs
        )


class PidLogAdmin(ModelView):
    _can_create = False
    _can_edit = False
    _can_delete = False

    column_list = ('id_pid', 'action', 'message')

    def __init__(self, model, session, **kwargs):
        super(PidLogAdmin, self).__init__(model, session, **kwargs)


def register_admin(app, admin):
    """
    Called on app initialization to register administration interface.
    """
    admin.add_view(PersistentIdentifierAdmin(
        PersistentIdentifier, db.session,
        name='Persistent identifiers', category="Persistent Identifiers")
    )
    admin.add_view(PidLogAdmin(
        PidLog, db.session,
        name='Log', category="Persistent Identifiers")
    )
