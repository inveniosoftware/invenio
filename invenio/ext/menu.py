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

"""Administration menu."""

from flask_menu import Menu
from flask_login import current_user
from invenio.base.i18n import _

menu = Menu()


def setup_app(app):
    """Register all subitems to the 'main.admin' menu item."""
    menu.init_app(app)

    @app.before_first_request
    def register_item():
        item = app.extensions['menu'].submenu('main.admin')
        item.register('admin.index', _('Admin'), order=10,
                      visible_when=lambda: current_user.is_admin)
