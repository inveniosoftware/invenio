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

from operator import itemgetter
from jinja2 import nodes
from jinja2.ext import Extension
from flask import g, request, current_app, _request_ctx_stack, url_for

try:
    from markupsafe import Markup as jinja2_Markup, escape as jinja2_escape
except ImportError:
    from jinja2._markupsafe import Markup as jinja2_Markup, \
        escape as jinja2_escape

from invenio.datastructures import LazyDict

ENV_PREFIX = '_collected_'


def prepare_tag_bundle(cls, tag):
    """
    Construct function that returns collected data specified
    in jinja2 template like `{% <tag> <value> %}` in correct
    order.

    Here is an example that shows the final order when template
    inheritance is used::

        example.html
        ------------
        {%\ extends 'page.html' %}
        {%\ css 'template2.css' %}
        {%\ css 'template3.css' %}

        page.html
        ---------
        {%\ css 'template1.css' %}
        {{ get_css_bundle() }}

        Output:
        -------
        [template1.css, template2.css, template3.css]

    """
    def get_bundle(key=None, iterate=False):

        def _get_data_by_key(data_, key_):
            return map(itemgetter(1), filter(lambda (k, v): k == key_, data_))

        data = getattr(cls.environment, ENV_PREFIX+tag)

        if iterate:
            bundles = sorted(set(map(itemgetter(0), data)))

            def _generate_bundles():
                for bundle in bundles:
                    cls._reset(tag, bundle)
                    yield cls.environment.new_bundle(tag,
                                                     _get_data_by_key(data,
                                                                      bundle),
                                                     bundle)
            return _generate_bundles()
        else:
            if key is not None:
                data = _get_data_by_key(data, key)
            else:
                bundles = sorted(set(map(itemgetter(0), data)))
                data = [f for bundle in bundles
                        for f in _get_data_by_key(data, bundle)]

            cls._reset(tag, key)
            return cls.environment.new_bundle(tag, data, key)
    return get_bundle


class CollectionExtension(Extension):
    """
    CollectionExtension adds new tags `css` and `js` and functions
    ``get_css_bundle`` and ``get_js_bundle`` for jinja2 templates.
    The ``new_bundle`` method is used to create bundle from
    list of file names collected using `css` and `js` tags.

    Example: simple case

        {% css 'css/invenio.css' %}
        {% js 'js/jquery.js' %}
        {% js 'js/invenio.js' %}
        ...
        {% assets get_css_bundle() %}
           <link rel="stylesheet" type="text/css" href="{{ ASSET_URL }}"></link>
        {% endassets %}
        {% assets get_js_bundle() %}
           In template, use {{ ASSETS_URL }} for printing file URL.
        {% endassets %}

    Example: named bundles

        record.html:
        {% extend 'page.html' %}
        {% css 'css/may-vary.css' %}
        # default bundle name can be changed in application factory
        # app.jinja_env.extend(default_bundle_name='90-default')
        {% css 'css/record.css', '10-record' %}
        {% css 'css/form.css', '10-record' %}

        page.html:
        {% css 'css/bootstrap.css', '00-base' %}
        {% css 'css/invenio.css', '00-base' %}
        ...
        {% for bundle in get_css_bundle(iterate=True) %}
          {% assets bundle %}
            <link rel="stylesheet" type="text/css" href="{{ ASSET_URL }}"></link>
          {% endassets %}
        {% endfor %}

        Output:
            <link rel="stylesheet" type="text/css" href="/css/00-base.css"></link>
            <link rel="stylesheet" type="text/css" href="/css/10-record.css"></link>
            <link rel="stylesheet" type="text/css" href="/css/90-default.css"></link>

     Note:
       If you decide not to use assets bundle but directly print
       stylesheet and script html tags, you MUST define:
       ```
       _app.jinja_env.extend(
           use_bundle = False,
           collection_templates = {
               'css': '<link rel="stylesheet" type="text/css" href="/%s"></link>',
               'js': '<script type="text/javascript" src="/%s"></script>'
           })
       ```
       Both callable and string with '%s' are allowed in
       ``collection_templates``.

    """
    tags = set(['css', 'js'])

    def __init__(self, environment):
        super(CollectionExtension, self).__init__(environment)
        ext = dict(('get_%s_bundle' % tag, prepare_tag_bundle(self, tag))
                   for tag in self.tags)
        environment.extend(
            default_bundle_name='10-default',
            use_bundle=True,
            collection_templates=dict((tag, lambda x: x) for tag in self.tags),
            new_bundle=lambda tag, collection, name: collection,
            **ext)
        for tag in self.tags:
            self._reset(tag)

    def _reset(self, tag, key=None):
        """
        Empty list of used scripts.
        """
        if key is None:
            setattr(self.environment, ENV_PREFIX+tag, [])
        else:
            data = filter(lambda (k, v): k != key,
                          getattr(self.environment, ENV_PREFIX+tag))
            setattr(self.environment, ENV_PREFIX+tag, data)

    def _update(self, tag, value, key, caller=None):
        """
        Update list of used scripts.
        """
        try:
            values = getattr(self.environment, ENV_PREFIX+tag)
            values.append((key, value))
        except:
            values = [(key, value)]

        setattr(self.environment, ENV_PREFIX+tag, values)
        return ''

    def parse(self, parser):
        """
        Parse Jinja statement tag defined in `self.tags` (default: css, js).

        This accually tries to build corresponding html script tag
        or collect script file name in jinja2 environment variable.
        If you use bundles it is important to call ``get_css_bundle``
        or ``get_js_bundle`` in template after all occurrences of
        script tags (e.g. {% css ... %}, {% js ...%}).
        """
        tag = parser.stream.current.value
        lineno = next(parser.stream).lineno

        default_bundle_name = u"%s" % (self.environment.default_bundle_name)
        default_bundle_name.encode('utf-8')
        bundle_name = nodes.Const(default_bundle_name)

        #parse filename
        if parser.stream.current.type != 'block_end':
            value = parser.parse_expression()
            # get first optional argument: bundle_name
            if parser.stream.skip_if('comma'):
                bundle_name = parser.parse_expression()
                if isinstance(bundle_name, nodes.Name):
                    bundle_name = nodes.Name(bundle_name.name, 'load')
        else:
            value = parser.parse_tuple()

        args = [nodes.Const(tag), value, bundle_name]

        # Return html tag with link to corresponding script file.
        if self.environment.use_bundle is False:
            value = value.value
            if callable(self.environment.collection_templates[tag]):
                node = self.environment.collection_templates[tag](value)
            else:
                node = self.environment.collection_templates[tag] % value
            return nodes.Output([nodes.MarkSafeIfAutoescape(nodes.Const(node))])

        # Call :meth:`_update` to collect names of used scripts.
        return nodes.CallBlock(self.call_method('_update', args=args,
                                                lineno=lineno),
                               [], [], '')


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


class LangExtension(Extension):
    tags = set(['lang'])

    def parse(self, parser):
        lineno = parser.stream.next().lineno

        body = parser.parse_statements(['name:endlang'], drop_needle=True)

        return nodes.CallBlock(self.call_method('_lang'),
                               [], [], body).set_lineno(lineno)

    def _lang(self,  caller):
        from invenio.bibformat_engine import filter_languages
        return filter_languages('<lang>' + caller() + '</lang>', g.ln)


def hack_jinja2_utf8decoding():
    """
    Jinja2 requires all strings to be unicode objects. Invenio however operates
    with UTF8 encoded str objects. Jinja2 will automatically convert non-unicode
    objects into unicode objects, but via the ascii codec. This function
    replaces the escape function and Markup class in Jinja2/MarkupSafe, to
    use the utf8 codec when converting 8-bit str objects into unicode objects.

    Ideally Jinja2/MarkupSafe should allow specifying which default encoding to
    use when decoding strings. Other alternatives is to decode any str object
    into unicode prior to passing the values to Jinja2 methods. This will
    however require large changes over the entire Invenio codebase, with the
    risk of introducing many errors. This runtime hack is unfortunately
    currently the least intrusive way to fix the str to unicode decoding.
    """
    # Jinja2 will try to load escape method and Markup class from a variety of
    # different modules. First it will try from MarkupSafe package, then from
    # jinja2._markupsafe._speedup, then jinja2._markupsafe._native. Ideally, we
    # should only replace the function and class at the implementing module.
    # However, due to Python's package/module loading behaviour, the function
    # and class will be imported into other jinja2 modules as soon as we try to
    # import the module implementing the function and class. Hence, we need to
    # replace the function and class in the modules where it has already been
    # imported.
    import jinja2
    import jinja2.runtime
    import jinja2.utils
    import jinja2.nodes
    import jinja2.filters
    import jinja2.ext
    import jinja2.environment
    import jinja2.compiler

    # Escape function replacement in Jinja2 library
    try:
        jinja2._markupsafe.escape = utf8escape
    except:
        pass
    jinja2.runtime.escape = utf8escape
    jinja2.utils.escape = utf8escape
    jinja2.filters.escape = utf8escape
    jinja2.compiler.escape = utf8escape
    jinja2.escape = utf8escape

    # Markup class replacement in Jinja2 library
    try:
        jinja2._markupsafe.Markup = Markup
    except:
        pass
    jinja2.runtime.Markup = Markup
    jinja2.utils.Markup = Markup
    jinja2.filters.Markup = Markup
    jinja2.compiler.Markup = Markup
    jinja2.Markup = Markup
    jinja2.nodes.Markup = Markup
    jinja2.ext.Markup = Markup
    jinja2.environment.Markup = Markup

    # Escape/Markup replacement in MarkupSafe library.
    ## FIXME causes recursive calls in `Markup.__new__` and `escape`
    #try:
    #    import markupsafe
    #    markupsafe.escape = utf8escape
    #    #markupsafe.Markup = Markup
    #except ImportError:
    #    pass


def utf8escape(s):
    """
    UTF8-8-bit-string-friendly replacement function for MarkupSafe/Jinja2
    escape function.

    WARNING: Do not use this method. Use jinja2.escape() instead.
    """
    if isinstance(s, str):
        return jinja2_escape(s.decode('utf8'))
    return jinja2_escape(s)
# Ensure function name is identical to replaced function.
utf8escape.__name__ = jinja2_escape.__name__


class Markup(jinja2_Markup):
    """
    Markup replacement class

    Forces the use of utf8 codec for decoding 8-bit strings, in case no
    encoding is specified.

    WARNING: Do not use this class. Use jinja2.Markup instead.
    """
    def __new__(cls, base=u'', encoding=None, errors='strict'):
        if encoding is None and isinstance(base, str):
            encoding = 'utf8'
        return jinja2_Markup.__new__(cls, base=base, encoding=encoding,
                                     errors=errors)

def load_template_context_filters():
    from invenio.importutils import autodiscover_modules
    modules = autodiscover_modules(['invenio.template_context_filters'],
                                   'tfi_.+')
    filters = {}
    for m in modules:
        register_func = getattr(m, 'template_context_filter', None)
        if register_func and isinstance(register_func, types.FunctionType):
            filters[m.__name__.split('.')[-1]] = register_func
    return filters

TEMPLATE_CONTEXT_FILTERS = LazyDict(load_template_context_filters)


def inject_utils():
    """
    This will add some more variables and functions to the Jinja2 to execution
    context. In particular it will add:

    - `url_for`: an Invenio specific wrapper of Flask url_for, that will let you
                 obtain URLs for non Flask-native handlers (i.e. not yet ported
                 Invenio URLs)
    - `breadcrumbs`: this will be a list of three-elements tuples, containing
                 the hierarchy of Label -> URLs of navtrails/breadcrumbs.
    - `_`: this can be used to automatically translate a given string.
    - `is_language_rtl`: is True if the chosen language should be read right to left
    """
    from werkzeug.routing import BuildError

    from invenio.messages import is_language_rtl
    from invenio.webinterface_handler_flask_utils import _, guess_language
    from invenio.webuser_flask import current_user
    from invenio.urlutils import create_url, get_canonical_and_alternates_urls

    def invenio_url_for(endpoint, **values):
        try:
            return url_for(endpoint, **values)
        except BuildError:
            if endpoint.startswith('http://') or endpoint.startswith('https://'):
                return endpoint
            if endpoint.startswith('.'):
                endpoint = request.blueprint + endpoint
            return create_url('/' + '/'.join(endpoint.split('.')), values, False).decode('utf-8')

    if request.endpoint in current_app.config['breadcrumbs_map']:
        breadcrumbs = current_app.config['breadcrumbs_map'][request.endpoint]
    elif request.endpoint:
        breadcrumbs = [(_('Home'), '')] + current_app.config['breadcrumbs_map'].get(request.endpoint.split('.')[0], [])
    else:
        breadcrumbs = [(_('Home'), '')]

    user = current_user._get_current_object()
    canonical_url, alternate_urls = get_canonical_and_alternates_urls(
        request.environ['PATH_INFO'])
    alternate_urls = dict((ln.replace('_', '-'), alternate_url)
                          for ln, alternate_url in alternate_urls.iteritems())

    guess_language()

    from invenio.bibfield import get_record  # should not be global due to bibfield_config
    return dict(_=lambda *args, **kwargs: g._(*args, **kwargs),
                current_user=user,
                get_css_bundle=current_app.jinja_env.get_css_bundle,
                get_js_bundle=current_app.jinja_env.get_js_bundle,
                is_language_rtl=is_language_rtl,
                canonical_url=canonical_url,
                alternate_urls=alternate_urls,
                get_record=get_record,
                url_for=invenio_url_for,
                breadcrumbs=breadcrumbs,
                **TEMPLATE_CONTEXT_FILTERS
                )

def extend_application_template_filters(app):
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
    from invenio.dateutils import convert_datetext_to_dategui, \
        convert_datestruct_to_dategui, pretty_date
    from invenio.webmessage_mailutils import email_quoted_txt2html
    from invenio.config import CFG_PYLIBDIR
    from invenio.pluginutils import PluginContainer

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
