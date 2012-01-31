# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

from jinja2 import nodes
from jinja2.ext import Extension
from flask import current_app
from flask.ext.assets import Environment, Bundle

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
    def get_bundle():
        data = getattr(cls.environment, ENV_PREFIX+tag)
        cls._reset(tag)
        return cls.environment.new_bundle(tag, data)
    return get_bundle

class CollectionExtension(Extension):
    """
     CollectionExtension adds new tags `css` and `js` and functions
     ``get_css_bundle`` and ``get_js_bundle`` for jinja2 templates.
     The ``new_bundle`` method is used to create bundle from
     list of file names collected using `css` and `js` tags.

     Example:
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
        ext = dict(('get_%s_bundle' % tag, prepare_tag_bundle(self, tag)) for tag in self.tags)
        environment.extend(
            use_bundle=True,
            collection_templates=dict((tag, lambda x:x) for tag in self.tags),
            new_bundle=lambda tag, collection: collection,
            **ext)
        for tag in self.tags:
            self._reset(tag)

    def _reset(self, tag):
        """
        Empty list of used scripts.
        """
        setattr(self.environment, ENV_PREFIX+tag, [])

    def _update(self, tag, value, caller=None):
        """
        Update list of used scripts.
        """
        try:
            values = getattr(self.environment, ENV_PREFIX+tag)
            values.append(value)
        except:
            values = [value]
        current_app.logger.info(values)
        setattr(self.environment, ENV_PREFIX+tag, values)
        return ''
        #return values

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
        value = parser.parse_tuple()
        current_app.logger.info("%s: Collecting %s (%s)" % (parser.name, tag, value))

        # Return html tag with link to corresponding script file.
        if self.environment.use_bundle is False:
            value = value.value
            if callable(self.environment.collection_templates[tag]):
                node = self.environment.collection_templates[tag](value)
            else:
                node = self.environment.collection_templates[tag] % value
            return nodes.Output([nodes.MarkSafeIfAutoescape(nodes.Const(node))])

        # Call :meth:`_update` to collect names of used scripts.
        return nodes.CallBlock(
            self.call_method('_update',
                args=[nodes.Const(tag), value],
                lineno=lineno),
            [], [], '')

