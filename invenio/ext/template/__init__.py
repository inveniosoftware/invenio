# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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
    invenio.ext.template
    --------------------

    This module provides additional extensions and filters for `jinja2` module
    used in Invenio.
"""


from .bccache import BytecodeCacheWithConfig
from .context_processor import setup_app as context_processor_setup_app
from .loader import OrderAwareDispatchingJinjaLoader
from flask import g, request, current_app, _request_ctx_stack, url_for
from jinja2 import FileSystemLoader, ChoiceLoader

ENV_PREFIX = '_collected_'


def render_template_to_string(input, _from_string=False, **context):
    """Renders a template from the template folder with the given
    context and return the string.

    :param input: the string template, or name of the template to be
                  rendered, or an iterable with template names
                  the first one existing will be rendered
    :param context: the variables that should be available in the
                    context of the template.

    :note: code based on
    [https://github.com/mitsuhiko/flask/blob/master/flask/templating.py]
    """
    ctx = _request_ctx_stack.top
    ctx.app.update_template_context(context)
    if _from_string:
        template = ctx.app.jinja_env.from_string(input)
    else:
        template = ctx.app.jinja_env.get_or_select_template(input)
    return template.render(context)


def inject_utils():
    """
    This will add some more variables and functions to the Jinja2 to execution
    context. In particular it will add:

    - `url_for`: an Invenio specific wrapper of Flask url_for, that will let
                 you obtain URLs for non Flask-native handlers (i.e. not yet
                 ported Invenio URLs)
    - `_`: this can be used to automatically translate a given string.
    - `is_language_rtl`: True if the chosen language should be read right to
                         left.
    """
    from werkzeug.routing import BuildError

    from invenio.base.i18n import is_language_rtl
    from flask.ext.babel import get_translations
    from flask.ext.login import current_user
    from invenio.utils.url import create_url, get_canonical_and_alternates_urls

    def invenio_url_for(endpoint, **values):
        try:
            return url_for(endpoint, **values)
        except BuildError:
            if endpoint.startswith('http://') or endpoint.startswith('https://'):
                return endpoint
            if endpoint.startswith('.'):
                endpoint = request.blueprint + endpoint
            return create_url('/' + '/'.join(endpoint.split('.')), values, False).decode('utf-8')

    user = current_user._get_current_object()
    canonical_url, alternate_urls = get_canonical_and_alternates_urls(
        request.environ['PATH_INFO'])
    alternate_urls = dict((ln.replace('_', '-'), alternate_url)
                          for ln, alternate_url in alternate_urls.iteritems())
    try:
        from invenio.modules.records.api import get_record  # should not be global due to bibfield_config
    except:
        get_record = lambda *args, **kwargs: None
    # from invenio.modules.formatter.engine import TEMPLATE_CONTEXT_FUNCTIONS_CACHE
    return dict(
        #FIXME use just gettext when all strings use named arguments
        _=lambda s, *args, **kwargs: get_translations().gettext(
            s.encode('utf8'), *args, **kwargs).decode('utf8'),
        current_user=user,
        get_css_bundle=current_app.jinja_env.get_css_bundle,
        get_js_bundle=current_app.jinja_env.get_js_bundle,
        is_language_rtl=is_language_rtl,
        canonical_url=canonical_url,
        alternate_urls=alternate_urls,
        get_record=get_record,
        url_for=invenio_url_for,
        #**TEMPLATE_CONTEXT_FUNCTIONS_CACHE.template_context_functions
        )


def setup_app(app):
    """
    Extends application template filters with custom filters and fixes.

    List of applied filters:
    ------------------------
    * filesizeformat
    * path_join
    * quoted_txt2html
    * invenio_format_date
    * invenio_pretty_date
    * invenio_url_args
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

    ## Let's customize the template loader to look into packages
    ## and application templates folders.
    jinja_loader = ChoiceLoader([
        OrderAwareDispatchingJinjaLoader(app),
        app.jinja_loader,
    ])
    app.jinja_loader = jinja_loader

    for ext in app.config.get('JINJA2_EXTENSIONS', []):
        try:
            app.jinja_env.add_extension(ext)
        except:
            app.logger.error('Problem with loading extension: "%s"' % (ext, ))

    test_not_empty = lambda v: v is not None and v != ''

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
        """
        Returns first `limit` number of sentences ending by `separator`.
        """
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
        This is a special Jinja2 filter that will call
        convert_datetext_to_dategui to print a human friendly date.
        """
        if isinstance(date, datetime):
            return convert_datestruct_to_dategui(date.timetuple(),
                                                 g.ln).decode('utf-8')
        return convert_datetext_to_dategui(date, g.ln).decode('utf-8')

    @app.template_filter('invenio_pretty_date')
    def _pretty_date(date):
        """
        This is a special Jinja2 filter that will call
        pretty_date to print a human friendly timestamp.
        """
        if isinstance(date, datetime) or isinstance(date, basestring):
            return pretty_date(date, ln=g.ln)
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
