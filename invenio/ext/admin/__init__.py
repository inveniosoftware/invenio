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

"""
Flask-Admin support in Invenio
------------------------------

Please see http://flask-admin.readthedocs.org/en/latest/quickstart/ prior to
reading this documentation, to understand how Flask-Admin works.

Flask admin allows you to easily create web administration interfaces for your
SQLAlchemy models. This extension takes care of using Blueprint as base class
for the admin views.

By default this extension will look for invenio.<name>_admin modules and call
the method register_admin(app, admin) in each module to allow to register its
administration views.

By default all view are restricted to super users only. This can be changed via
the acc_<action>_action class variables.

Usage example - create a file called <module>_admin.py::

    from invenio.ext.admin import InvenioModelView
    from invenio.ext.sqlalchemy import db
    from invenio.<module>_models import MyModel

    class MyModelAdmin(InvenioModelView):
        acc_edit_action = 'cfgmymodel'

        _can_create = False
        _can_edit = True
        _can_delete = False

        # ... Flaks-Admin options ...
        # column_list = ( ... )

        def __init__(self, model, session, **kwargs):
            super(MyModelAdmin, self).__init__(model, session, **kwargs)

    def register_admin(app, admin):
        admin.add_view(MyModelAdmin(MyModel, db.session, name='My model',
                                    category="My Category"))
"""

from __future__ import absolute_import

from flask_admin import Admin
from flask_registry import ModuleAutoDiscoveryRegistry

from .views import AdminIndexView


#
# Utility method
#
class AdminDiscoveryRegistry(ModuleAutoDiscoveryRegistry):
    setup_func_name = 'register_admin'

    def __init__(self, *args, **kwargs):
        self.admin = kwargs.pop('admin', None)
        super(AdminDiscoveryRegistry, self).__init__(*args, **kwargs)

    def register(self, module, *args, **kwargs):
        super(AdminDiscoveryRegistry, self).register(
            module, self.app, self.admin, *args, **kwargs
        )


def setup_app(app):
    """
    Register all administration views with the Flask application
    """
    app.config.setdefault("ADMIN_NAME", "Invenio")

    # Initialize app
    admin = Admin(
        name=app.config['ADMIN_NAME'],
        index_view=AdminIndexView(),
        base_template="admin_base.html",
        template_mode='bootstrap3'
    )
    admin.init_app(app)

    # Create registry and run discovery
    app.extensions['registry']['admin'] = AdminDiscoveryRegistry(
        'admin', app=app, with_setup=True, admin=admin
    )
