# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Post database creation listener."""

from invenio.ext.sqlalchemy import db
from invenio.base.factory import with_app_context


@with_app_context(new_context=True)
def post_handler_database_create(sender, default_data='', *args, **kwargs):
    """Fill format table with new format for Communities module."""
    from invenio.modules.formatter.models import Format
    data = {'code': 'hbpro',
            'last_updated': None,
            'description': u'Provisional HTML brief',
            'content_type': u'text/html',
            'visibility': 0,
            'name': u'hbpro'}
    format = Format.query.filter_by(code='hbpro').first()
    if not format:
        c = Format(**data)
        db.session.add(c)
        db.session.commit()
