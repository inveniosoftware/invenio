# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""Define additional global proxies."""

from flask import current_app, request
from werkzeug.local import LocalProxy


def _lookup_current_function():
    return current_app.view_functions.get(request.endpoint)


def _lookup_current_blueprint():
    return current_app.blueprints.get(request.blueprint, None)

# context data
current_function = LocalProxy(_lookup_current_function)
current_blueprint = LocalProxy(_lookup_current_blueprint)
cfg = LocalProxy(lambda: current_app.config)
