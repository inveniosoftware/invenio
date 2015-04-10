# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Flask-Admin page to configure roles and authorizations."""

from __future__ import unicode_literals

from flask_admin.form.fields import DateTimeField

from invenio.ext.admin.views import ModelView
from invenio.ext.sqlalchemy import db

from wtforms.fields import IntegerField
from wtforms.validators import DataRequired

from .models import AccAuthorization, AccROLE, UserAccROLE


class AccMixin(object):

    """Configure access rights."""

    _can_create = True
    _can_edit = True
    _can_delete = True

    acc_view_action = 'cfgwebaccess'
    acc_edit_action = 'cfgwebaccess'
    acc_delete_action = 'cfgwebaccess'


class AccROLEAdmin(ModelView, AccMixin):

    """Flask-Admin view to manage roles."""

    column_list = (
        'name', 'description', 'firerole_def_src',
    )

    form_excluded_columns = ['authorizations', 'users']

    form_args = {
        'name': {
            'validators': [
                DataRequired(),
            ],
        },
    }


class UserAccROLEAdmin(ModelView, AccMixin):

    """Flask-Admin view to manage user roles."""

    column_list = (
        'user', 'role', 'expiration',
    )

    form_args = {
        'user': {
            'validators': [
                DataRequired(),
            ],
        },
        'accROLE': {
            'validators': [
                DataRequired(),
            ],
        },
    }

    form_overrides = {
        'expiration': DateTimeField
    }


class AccAuthorizationAdmin(ModelView, AccMixin):

    """Flask-Admin view to manage authorizations."""

    column_list = (
        'role', 'action', 'argument', 'argumentlistid'
    )

    column_display_pk = True

    form_args = {
        'role': {
            'validators': [
                DataRequired(),
            ],
        },
        'action': {
            'validators': [
                DataRequired(),
            ],
        },
        'argumentlistid': {},
    }

    form_overrides = {
        'argumentlistid': IntegerField
    }


def register_admin(app, admin):
    """Call on app initialization to register administration interface."""
    category = "Access"
    admin.add_view(
        AccROLEAdmin(AccROLE, db.session, name="Role", category=category)
    )
    admin.add_view(
        UserAccROLEAdmin(UserAccROLE, db.session, name="User Roles",
                         category=category)
    )
    admin.add_view(
        AccAuthorizationAdmin(AccAuthorization, db.session,
                              name="Authorizations", category=category)
    )
