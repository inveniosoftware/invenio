# -*- coding: utf-8 -*-
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
"""Custom `Jinja2` extensions."""

from operator import itemgetter
from jinja2 import nodes
from jinja2.ext import Extension
from flask import current_app

ENV_PREFIX = '_collected_'


def prepare_tag_bundle(cls, tag):
    """Prepare the css and js tags.

    Construct function that returns collected data specified
    in jinja2 template like `{% <tag> <value> %}` in correct
    order.

    Here is an example that shows the final order when template
    inheritance is used.

    .. code-block:: jinja

       <!-- example.html -->
       {% extends 'page.html' %}
       {% css 'template2.css' %}
       {% css 'template3.css' %}

       <!-- page.html -->
       {% css 'template1.css' %}
       {{ get_css_bundle() }}

    Output:

    .. code-block:: python

       [template1.css, template2.css, template3.css]

    """
    def get_data_by_key(data, key):
        collection = []
        filters = None
        for bundle_name, filename, f in data:
            if bundle_name == key:
                collection.append(filename)
                if not filters:
                    filters = f
        return collection, filters

    def get_bundle(key=None, iterate=False):
        data = getattr(cls.environment, ENV_PREFIX + tag)

        if iterate:
            bundles = sorted(set(map(itemgetter(0), data)))

            def _generate_bundles():
                for bundle in bundles:
                    cls._reset(tag, bundle)
                    collection, filters = get_data_by_key(data, bundle)
                    yield cls.environment.new_bundle(tag,
                                                     collection,
                                                     bundle,
                                                     filters)
            return _generate_bundles()
        else:
            collection = []
            filters = None
            if key is not None:
                collection, filters = get_data_by_key(data, key)
            else:
                bundles = sorted(set(map(itemgetter(0), data)))
                for bundle in bundles:
                    c, f = get_data_by_key(data, bundle)
                    collection += c
                    if not filters:
                        filters = f

            cls._reset(tag, key)
            return cls.environment.new_bundle(tag, collection, key, filters)

    return get_bundle


class BundleExtension(Extension):

    """
    Jinja extension for css and js bundles.

    Definition of the required bundles.

    .. code-block:: jinja

        {%- bundles "jquery.js", "invenio.css" -%}
        {%- bundle "require.js" -%}

    Usage.

    .. code-block:: jinja

        {%- for bundle in get_bundle('js') %}
          {%- assets bundle %}
            <!-- {{ bundle.name }} -->
            <script type="text/javascript" src="{{ ASSET_URL }}"></script>
          {%- endassets %}
        {%- endfor %}
        </body>
        </html>
    """

    tags = set(('bundle', 'bundles'))

    @classmethod
    def inject(cls):
        """Inject the get_bundle function into the jinja templates."""
        _bundles = {}

        def get_bundle(suffix):
            # lazy build the bundles
            if not _bundles:
                registry = current_app.extensions['registry']['bundles']
                for pkg, bundle in registry:
                    try:
                        current_app.logger.info("{0}:{1}".format(pkg,
                                                                 bundle.name))
                    except AttributeError:
                        raise ValueError(bundle)
                    if bundle.name in _bundles:
                        raise ValueError("{0} was already defined!"
                                         .format(bundle.name))
                    _bundles[bundle.name] = bundle

            env = current_app.jinja_env.assets_environment
            # disable the compilation in debug mode iff asked.
            less_debug = suffix is "css" and env.debug and \
                not current_app.config.get("LESS_RUN_IN_DEBUG", True)
            requirejs_debug = suffix is "js" and env.debug and \
                not current_app.config.get("REQUIREJS_RUN_IN_DEBUG", True)

            for bundle in sorted(current_app.jinja_env.bundles):
                if bundle.endswith(suffix):
                    b = _bundles[bundle]
                    if less_debug:
                        b.filters = None
                        b.extra.update(rel="stylesheet/less")
                    if requirejs_debug:
                        b.filters = None
                    yield b

        return dict(get_bundle=get_bundle)

    def __init__(self, environment):
        """Initialize the extension."""
        super(BundleExtension, self).__init__(environment)

        def get_bundle(suffix):
            for bundle in environment.bundles:
                if bundle.endswith(suffix):
                    yield bundle

        environment.extend(bundles=set())

    def _update(self, bundles, caller):
        """Update the environment bundles.

        :return: empty html or html comment in debug mode.
        :rtype: str
        """
        self.environment.bundles.update(bundles)
        if current_app.debug:
            return '<!-- bundles: {0} -->'.format(', '.join(bundles))
        else:
            return ''

    def parse(self, parser):
        """Parse the bundles block and feed the bundles environemnt.

        Bundles entries are remplaced by an empty string.
        """
        # not usefull unless you have many tags
        #tag = parser.stream.current.value
        lineno = next(parser.stream).lineno

        bundles = []
        while parser.stream.current.type != "block_end":
            value = parser.parse_expression()
            bundles.append(value)
            parser.stream.skip_if("comma")

        call = self.call_method("_update", args=[nodes.List(bundles)])
        call_block = nodes.CallBlock(call, [], [], '')
        call_block.set_lineno(lineno)
        return call_block


class CollectionExtension(Extension):

    """Jinja extension for css and js bundles.

    **DEPRECATED**

    CollectionExtension adds new tags `css` and `js` and functions
    ``get_css_bundle`` and ``get_js_bundle`` for jinja2 templates.
    The ``new_bundle`` method is used to create bundle from
    list of file names collected using `css` and `js` tags.

    **Example:** simple case

    .. code-block:: jinja

        {% css url_for('static', filename='css/invenio.css') %}
        {% js url_for('static', filename='js/jquery.js') %}
        {% js url_for('static', filename='js/invenio.js') %}
        ...
        {% assets get_css_bundle() %}
           <link rel="stylesheet" type="text/css" href="{{ ASSET_URL }}">
        {% endassets %}
        {% assets get_js_bundle() %}
           In template, use {{ ASSETS_URL }} for printing file URL.
        {% endassets %}

    **Example:** named bundles

    .. code-block:: jinja

        <!-- record.html -->
        {% extend 'page.html' %}
        {% css url_for('static', filename='css/may-vary.css') %}
        {#
         # default bundle name can be changed in application factory
         # app.jinja_env.extend(default_bundle_name='90-default')
         #}
        {% css url_for('static', filename='css/record.css'), '10-record' %}
        {% css url_for('static', filename='css/form.css'), '10-record' %}

        <!-- page.html -->
        {% css url_for('static', filename='css/bootstrap.css'), '00-base' %}
        {% css url_for('static', filename='css/invenio.css'), '00-base' %}
        ...
        {% for bundle in get_css_bundle(iterate=True) %}
          {% assets bundle %}
            <link rel="stylesheet" type="text/css" href="{{ ASSET_URL }}">
          {% endassets %}
        {% endfor %}

    Output:

    .. code-block:: html

       <link rel="stylesheet" type="text/css" href="/css/00-base.css">
       <link rel="stylesheet" type="text/css" href="/css/10-record.css">
       <link rel="stylesheet" type="text/css" href="/css/90-default.css">

    **Note:** If you decide not to use assets bundle but directly print
    stylesheet and script html tags, you MUST define:

    .. code-block:: python

       _app.jinja_env.extend(
           use_bundle = False,
           collection_templates = {
               'css': '<link rel="stylesheet" type="text/css" href="/%s">',
               'js': '<script type="text/javascript" src="/%s"></script>'
           })

    Both callable and string with ``%s`` are allowed in
    ``collection_templates``.
    """

    tags = set(['css', 'js'])

    def __init__(self, environment):
        """Create the extension."""
        super(CollectionExtension, self).__init__(environment)
        ext = dict(('get_%s_bundle' % tag, prepare_tag_bundle(self, tag))
                   for tag in self.tags)
        environment.extend(
            default_bundle_name='10-default',
            use_bundle=True,
            collection_templates=dict((tag, lambda x: x) for tag in self.tags),
            new_bundle=lambda tag, collection, name, filters: (collection,
                                                               filters),
            **ext)
        for tag in self.tags:
            self._reset(tag)

    def _reset(self, tag, key=None):
        """Empty list of used scripts."""
        if key is None:
            setattr(self.environment, ENV_PREFIX + tag, [])
        else:
            data = filter(lambda (k, v, _): k != key,
                          getattr(self.environment, ENV_PREFIX + tag))
            setattr(self.environment, ENV_PREFIX + tag, data)

    def _update(self, tag, value, bundle_name, filters, caller=None):
        """Update list of used scripts."""
        try:
            values = getattr(self.environment, ENV_PREFIX + tag)
            values.append((bundle_name, value, filters))
        except:
            values = [(bundle_name, value, filters)]

        setattr(self.environment, ENV_PREFIX + tag, values)
        if current_app.debug:
            return '<script>console.error("Please update: {1}: {0}")</script>'\
                   .format(value, bundle_name)
        else:
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
        filters = nodes.Const(None)

        #parse filename
        if parser.stream.current.type != 'block_end':
            value = parser.parse_expression()
            # get first optional argument: bundle_name
            if parser.stream.skip_if('comma'):
                bundle_name = parser.parse_expression()
                if isinstance(bundle_name, nodes.Name):
                    bundle_name = nodes.Name(bundle_name.name, 'load')
            # get the second optional argument: filters
            if parser.stream.skip_if('comma'):
                filters = parser.parse_expression()
        else:
            value = parser.parse_tuple()

        args = [nodes.Const(tag), value, bundle_name, filters]

        # Return html tag with link to corresponding script file.
        if self.environment.use_bundle is False:
            value = value.value
            if callable(self.environment.collection_templates[tag]):
                node = self.environment.collection_templates[tag](value)
            else:
                node = self.environment.collection_templates[tag] % value
            return nodes.Output([
                nodes.MarkSafeIfAutoescape(nodes.Const(node))
            ])

        # Call :meth:`_update` to collect names of used scripts.
        return nodes.CallBlock(self.call_method('_update',
                                                args=args,
                                                lineno=lineno),
                               [], [], '')
