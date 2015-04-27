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

"""Custom hooks and hacks needed for Flask-Babel."""

import sys

from contextlib import contextmanager

from babel import support

from flask import _request_ctx_stack, current_app, g

from flask_babel import Babel, gettext

from invenio.utils.datastructures import LaziestDict

import pkg_resources

import six

from .errors import NoCompiledTranslationError
from .filters import filter_format_date, filter_format_datetime, \
    filter_format_time, filter_format_timedelta, filter_to_user_timezone, \
    filter_to_utc
from .selectors import get_locale, get_timezone

babel = Babel()


@contextmanager
def set_locale(ln):
    """Set Babel localization in request context."""
    ctx = _request_ctx_stack.top
    locale = getattr(ctx, 'babel_locale', None)
    setattr(ctx, 'babel_locale', ln)
    yield
    setattr(ctx, 'babel_locale', locale)


def get_translation(locale):
    """Generate translation for given language."""
    translations = None
    # NOTE that packages have to be loaded in reversed order!
    for plugin in reversed(current_app.extensions['registry']['packages']):
        if not pkg_resources.resource_isdir(plugin, 'translations'):
            continue
        dirname = pkg_resources.resource_filename(plugin, 'translations')
        if translations is None:
            translations = support.Translations.load(dirname, [locale])
        else:
            try:
                translations.merge(
                    support.Translations.load(dirname, [locale]))
            except AttributeError:
                # translations is probably support.NullTranslations
                six.reraise(NoCompiledTranslationError,
                            "Compiled translations seems to be missing",
                            sys.exc_info()[2])
    return translations

# Lazy translation cache.
TRANSLATIONS = LaziestDict(get_translation)


def get_translations():
    """Return the correct gettext translations for this request."""
    ctx = _request_ctx_stack.top
    if ctx is None:
        return None
    translations = getattr(ctx, 'babel_translations', None)
    if translations is None:
        locale = get_locale()
        translations = TRANSLATIONS.get(locale)
        ctx.babel_translations = translations
    return translations


def set_translations():
    """Add under ``g._`` an already configured internationalization function.

    Translations will be returned as unicode objects.
    """
    # Well, let's make it global now
    g.ln = get_locale()
    g._ = gettext


def get_lazystring_encoder(app):
    """Add a custom JSONEncoder that handles lazy strings from Babel."""
    from speaklater import _LazyString

    class JSONEncoder(app.json_encoder):
        def default(self, o):
            if isinstance(o, _LazyString):
                return six.text_type(o)

            return super(JSONEncoder, self).default(o)

    return JSONEncoder


def setup_app(app):
    """Setup Babel extension.

    Replaces implementation of ``get_translations`` in ``flask_babel``.
    """
    import flask_babel
    flask_babel.get_translations = get_translations

    babel.init_app(app)
    babel.localeselector(get_locale)
    babel.timezoneselector(get_timezone)

    app.json_encoder = get_lazystring_encoder(app)
    app.before_request(set_translations)

    # Register template filters for date formatting
    app.add_template_filter(filter_format_date, name="formatdate")
    app.add_template_filter(filter_format_datetime, name="formatdatetime")
    app.add_template_filter(filter_format_time, name="formattime")
    app.add_template_filter(filter_format_timedelta, name="formattimedelta")
    app.add_template_filter(filter_to_utc, name="toutc")
    app.add_template_filter(filter_to_user_timezone, name="tousertimezone")

    return app
