# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

"""
Customization of default Flask Jinja2 template loader.

By default the Flask Jinja2 template loader is not aware of the order of
Blueprints as defined by the PACKAGES configuration variable.
"""

from flask.templating import DispatchingJinjaLoader, blueprint_is_module


class OrderAwareDispatchingJinjaLoader(DispatchingJinjaLoader):
    def _iter_loaders(self, template):
        for blueprint in self.app.extensions['registry']['blueprints']:
            if blueprint_is_module(blueprint):
                continue
            loader = blueprint.jinja_loader
            if loader is not None:
                yield loader, template
