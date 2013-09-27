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
    invenio.ext.assets.extensions
    -----------------------------

    This module contains custom `Jinja2` extensions.
"""

from operator import itemgetter
from jinja2 import nodes
from jinja2.ext import Extension

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
