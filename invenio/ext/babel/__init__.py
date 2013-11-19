# -*- coding: utf-8 -*-
##
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
    invenio.ext.babel
    -----------------

    This module provides initialization and configuration for `flask.ext.babel`
    module.
"""

from contextlib import contextmanager
from flask import g, _request_ctx_stack
from flask.ext.babel import Babel, gettext
from .selectors import get_locale, get_timezone

babel = Babel()


@contextmanager
def set_locale(ln):
    ctx = _request_ctx_stack.top
    locale = getattr(ctx, 'babel_locale', None)
    setattr(ctx, 'babel_locale', ln)
    yield
    setattr(ctx, 'babel_locale', locale)


def set_translations():
    """
    Adds under g._ an already configured internationalization function
    will be available (configured to return unicode objects).
    """
    ## Well, let's make it global now
    g.ln = get_locale()
    g._ = gettext


def setup_app(app):
    """Setup Babel extension."""

    babel.init_app(app)
    babel.localeselector(get_locale)
    babel.timezoneselector(get_timezone)
    app.before_request(set_translations)
    return app
