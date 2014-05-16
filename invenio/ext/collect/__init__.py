# -*- coding: utf-8 -*-
##
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

"""Configuration of *Flask-Collect* extension."""

from flask.ext.collect import Collect

collect = Collect()


def setup_app(app):
    """Set the application up with the corresct static root."""
    app.config['COLLECT_STATIC_ROOT'] = app.static_folder
    collect.init_app(app)

    # unsetting the static_folder so it's not picked up by collect.
    class FakeApp(object):
        has_static_folder = False
        static_folder = None

    collect.app = FakeApp()
