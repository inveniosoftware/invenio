# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Admin."""

from __future__ import unicode_literals

from flask import abort, current_app

from flask_admin import AdminIndexView as FlaskAdminIndexView, \
    BaseView as FlaskBaseView
from flask_admin.contrib.sqla import ModelView as FlaskModelView

from flask_login import current_user

from invenio.ext.principal import permission_required
from invenio.ext.sslify import ssl_required


def can_acc_action(action):
    """Return getter/setter for can_<action> properties."""
    def fget(self):
        return self.acc_authorize(action)

    def fset(self, value):
        setattr(self, '_can_%s' % action, value)

    def fdel(self):
        delattr(self, '_can_%s' % action)

    return (fget, fset, fdel)


#
# Base classes
#
class BaseView(FlaskBaseView):

    """BaseView for administration interfaces."""

    acc_view_action = None

    can_view = property(*can_acc_action('view'))

    def acc_authorize(self, action):
        """Check authorization for a given action."""
        # First check if _can_<action> is set.
        if not getattr(self, '_can_%s' % action, True):
            return False

        # Next check if user is authorized to edit
        action = getattr(self, 'acc_%s_action' % action, None)
        if action:
            return permission_required(action)
        else:
            return current_user.is_super_admin

    def _handle_view(self, name, **kwargs):
        """The method will be executed before calling any view method."""
        if not current_user.is_authenticated():
            return current_app.login_manager.unauthorized()

        if not self.is_accessible():
            return abort(403)

    def is_accessible(self):
        """Check if admin interface is accessible by the current user."""
        if not current_user.is_authenticated():
            return False
        return self.can_view

    def create_blueprint(self, admin):
        """Ensure admin is only available over SSL."""
        self.blueprint = ssl_required(
            super(BaseView, self).create_blueprint(admin)
        )
        return self.blueprint


class ModelView(FlaskModelView, BaseView):

    """Invenio Admin base view for SQL alchemy models."""

    acc_edit_action = None
    acc_delete_action = None
    acc_create_action = None

    can_delete = property(*can_acc_action('delete'))
    can_edit = property(*can_acc_action('edit'))
    can_create = property(*can_acc_action('create'))


class AdminIndexView(FlaskAdminIndexView, BaseView):

    """Invenio admin index view that ensures Blueprint is being used."""

    # Ensures that templates and static files can be found
    import_name = 'flask_admin'
