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
from __future__ import absolute_import

from invenio.ext.admin.views import ModelView
from invenio.ext.sqlalchemy import db
from invenio.modules.communities.models import Community
from flask.ext.admin import expose

class CommunitiesAdmin(ModelView):
    #acc_edit_action = 'cfgmymodel'

    _can_create = True
    _can_edit = True
    _can_delete = True

    column_list = ('id', 'title', 'description', 'page', 'last_modified', 'ranking', 'fixed_points')
    column_searchable_list = ('title',)

    page_size = 100

    def __init__(self, model, session, **kwargs):
        super(CommunitiesAdmin, self).__init__(model, session, **kwargs)

def register_admin(app, admin):
    admin.add_view(CommunitiesAdmin(Community,
                                    db.session,
                                    name='Communities',
                                    endpoint='Communities',
                                    ))
