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

"""Configuration of *Flask-Collect* extension."""

from flask_collect import Collect

collect = Collect()


def setup_app(app):
    """Set the application up with the correct static root."""
    def filter_(items):
        """Filter application blueprints."""
        order = [blueprint.name for blueprint in
                 app.extensions['registry']['blueprints']]

        def _key(item):
            if item.name in order:
                return order.index(item.name)
            return -1

        return sorted(items, key=_key)

    app.config.setdefault('COLLECT_FILTER', filter_)
    app.config.setdefault('COLLECT_STATIC_ROOT', app.static_folder)
    collect.init_app(app)

    # unsetting the static_folder so it's not picked up by collect.
    class FakeApp(object):
        name = "fakeapp"
        has_static_folder = False
        static_folder = None

    collect.app = FakeApp()
