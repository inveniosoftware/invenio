# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

from invenio.ext.admin.views import ModelView
from invenio.ext.sqlalchemy import db
from invenio.modules.pages.models import Page


class PagesAdmin(ModelView):
    _can_create = True
    _can_edit = True
    _can_delete = True

    create_template = 'pages/edit.html'
    edit_template = 'pages/edit.html'

    column_list = (
        'url', 'title'
    )
    column_searchable_list = ('url',)

    page_size = 100

    def __init__(self, model, session, **kwargs):
        super(PagesAdmin, self).__init__(
            model, session, **kwargs
        )


def register_admin(app, admin):
    """
    Called on app initialization to register administration interface.
    """
    admin.add_view(PagesAdmin(
        Page, db.session,
        name='Pages', category="")
    )
