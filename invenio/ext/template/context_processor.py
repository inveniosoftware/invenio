# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013, 2014 CERN.
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

"""Additional decorator for extending template context with new objects."""

from flask import g


def register_template_context_processor(f):
    """Register globally the context processor."""
    g._template_context_processor.append(f)


def setup_app(app):
    """Initialize template context processor extension."""
    @app.before_request
    def reset_template_context():
        """Reset custom template context buffer."""
        g._template_context_processor = []

    @app.context_processor
    def inject_template_context():
        """Update `Jinja2` context by dynamic context processors."""
        context = {}
        for func in getattr(g, '_template_context_processor', []):
            context.update(func())
        reset_template_context()
        return context

    return app
