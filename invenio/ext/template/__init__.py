# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
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

"""Additional extensions and filters for jinja2 module."""

import re

from flask import _request_ctx_stack, g, request, url_for

from flask_login import current_user

from jinja2 import ChoiceLoader

from six import iteritems, string_types

from werkzeug.routing import BuildError

from .bccache import BytecodeCacheWithConfig
from .context_processor import setup_app as context_processor_setup_app
from .loader import OrderAwareDispatchingJinjaLoader

ENV_PREFIX = '_collected_'


def render_template_to_string(input, _from_string=False, **context):
    """Render a template from the template folder with the given context.

    Code based on
    `<https://github.com/mitsuhiko/flask/blob/master/flask/templating.py>`_

    :param input: the string template, or name of the template to be
                  rendered, or an iterable with template names
                  the first one existing will be rendered
    :param context: the variables that should be available in the
                    context of the template.
    :return: a string

    """
    ctx = _request_ctx_stack.top
    ctx.app.update_template_context(context)
    if _from_string:
        template = ctx.app.jinja_env.from_string(input)
    else:
        template = ctx.app.jinja_env.get_or_select_template(input)
    return template.render(context)


def inject_utils():
    """Inject variables and functions to jinja execution context.

    In particular it will add:

    - ``url_for``: an Invenio specific wrapper of Flask url_for, that will let
      you obtain URLs for non Flask-native handlers (i.e. not yet ported
      Invenio URLs)
    - ``_``: this can be used to automatically translate a given string.
    - ``is_language_rtl``: True if the chosen language should be read right to
      left.
    """
    from invenio.base.i18n import is_language_rtl
    from invenio.modules.records.api import get_record
    from invenio.utils.url import create_url, get_canonical_and_alternates_urls

    def invenio_url_for(endpoint, **values):
        try:
            return url_for(endpoint, **values)
        except BuildError:
            if re.match("https?://", endpoint, re.IGNORECASE):
                return endpoint
            if endpoint.startswith('.'):
                endpoint = request.blueprint + endpoint
            url = create_url('/' + endpoint.replace('.', '/'), values, False)
            return url.decode('utf-8')

    user = current_user._get_current_object()
    canonical_url, alternate_urls = get_canonical_and_alternates_urls(
        request.path)
    alternate_urls = dict((ln.replace('_', '-'), alternate_url)
                          for ln, alternate_url in iteritems(alternate_urls))
    return dict(
        current_user=user,
        is_language_rtl=is_language_rtl,
        canonical_url=canonical_url,
        alternate_urls=alternate_urls,
        get_record=get_record,
        url_for=invenio_url_for,
    )


def setup_app(app):
    """
    Extend application template filters with custom filters and fixes.

    List of applied filters:

    - filesizeformat
    - path_join
    - quoted_txt2html
    - invenio_format_date
    - invenio_pretty_date
    - invenio_url_args
    """
    import os
    from datetime import datetime
    from invenio.utils.date import convert_datetext_to_dategui, \
        convert_datestruct_to_dategui, pretty_date

    from . import config
    app.config.from_object(config)

    context_processor_setup_app(app)
    app.context_processor(inject_utils)

    if app.config.get('JINJA2_BCCACHE', False):
        app.jinja_options = dict(
            app.jinja_options,
            auto_reload=app.config.get('JINJA2_BCCACHE_AUTO_RELOAD', False),
            cache_size=app.config.get('JINJA2_BCCACHE_SIZE', -1),
            bytecode_cache=BytecodeCacheWithConfig(app))

    # Let's customize the template loader to look into packages
    # and application templates folders.
    jinja_loader = ChoiceLoader([
        OrderAwareDispatchingJinjaLoader(app),
        app.jinja_loader,
    ])
    app.jinja_loader = jinja_loader

    for ext in app.config.get('JINJA2_EXTENSIONS', []):
        try:
            app.jinja_env.add_extension(ext)
        except Exception:
            app.logger.exception(
                'Problem with loading extension: "{0}"'.format(ext))

    def test_not_empty(v):
        return v is not None and v != ''

    @app.template_filter('u')
    def tounicode(value):
        if isinstance(value, str):
            return value.decode('utf8')
        return value

    @app.template_filter('s')
    def tostr(value):
        if not isinstance(value, str):
            if isinstance(value, unicode):
                value = value.encode('utf8')
            value = str(value)
        return value

    @app.template_filter('prefix')
    def _prefix(value, prefix=''):
        return prefix + value if test_not_empty(value) else ''

    @app.template_filter('suffix')
    def _suffix(value, suffix=''):
        return value + suffix if test_not_empty(value) else ''

    @app.template_filter('wrap')
    def _wrap(value, prefix='', suffix=''):
        return prefix + value + suffix if test_not_empty(value) else ''

    @app.template_filter('sentences')
    def _sentences(value, limit, separator='. '):
        """Return first `limit` number of sentences ending by `separator`."""
        return separator.join(value.split(separator)[:limit])

    @app.template_filter('path_join')
    def _os_path_join(d):
        """Shortcut for `os.path.join`."""
        return os.path.join(*d)

    @app.template_filter('quoted_txt2html')
    def _quoted_txt2html(*args, **kwargs):
        from invenio.utils.mail import email_quoted_txt2html
        return email_quoted_txt2html(*args, **kwargs)

    @app.template_filter('invenio_format_date')
    def _format_date(date):
        """
        Format a date into a human friendly format.

        It uses :py:func:`invenio.utils.date.convert_datetext_to_dategui`
        """
        if isinstance(date, datetime):
            return convert_datestruct_to_dategui(
                date.timetuple(),
                getattr(g, 'ln', app.config['CFG_SITE_LANG'])).decode('utf-8')
        return convert_datetext_to_dategui(
            date, getattr(g, 'ln', app.config['CFG_SITE_LANG'])
        ).decode('utf-8')

    @app.template_filter('invenio_pretty_date')
    def _pretty_date(date):
        """
        Format a timestamp into a human friendly format.

        It uses :py:func:`invenio.utils.date.pretty_date`
        """
        if isinstance(date, datetime) or isinstance(date, string_types):
            return pretty_date(
                date, ln=getattr(g, 'ln', app.config['CFG_SITE_LANG']))
        return date

    @app.template_filter('invenio_url_args')
    def _url_args(d, append=u'?', filter=[]):
        from jinja2.utils import escape
        rv = append + u'&'.join(
            u'%s=%s' % (escape(key), escape(value))
            for key, value in d.iteritems(True)
            if value is not None and key not in filter
            # and not isinstance(value, Undefined)
        )
        return rv

    return app
