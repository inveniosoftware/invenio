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

from jinja2 import nodes
from jinja2.ext import Extension
from flask import current_app


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

            static_url_path = current_app.static_url_path + "/"
            bundles = []
            for bundle_name in current_app.jinja_env.bundles:
                if bundle_name.endswith(suffix):
                    bundle = _bundles[bundle_name]
                    bundles.append((bundle.weight, bundle))

            for _, bundle in sorted(bundles):
                if less_debug:
                    bundle.filters = None
                    bundle.extra.update(rel="stylesheet/less")
                if requirejs_debug:
                    bundle.filters = None
                if less_debug or requirejs_debug:
                    bundle.extra.update(static_url_path=static_url_path)
                yield bundle

        return dict(get_bundle=get_bundle)

    def __init__(self, environment):
        """Initialize the extension."""
        super(BundleExtension, self).__init__(environment)

        def get_bundle(suffix):
            for bundle in environment.bundles:
                if bundle.endswith(suffix):
                    yield bundle

        environment.extend(bundles=set())

    def _update(self, filename, bundles, caller):
        """Update the environment bundles.

        :return: empty html or html comment in debug mode.
        :rtype: str
        """
        self.environment.bundles.update(bundles)
        if current_app.debug:
            return "<!-- {0}: {1} -->\n".format(filename, ", ".join(bundles))
        else:
            return ''

    def parse(self, parser):
        """Parse the bundles block and feed the bundles environment.

        Bundles entries are replaced by an empty string.
        """
        lineno = next(parser.stream).lineno

        bundles = []
        while parser.stream.current.type != "block_end":
            value = parser.parse_expression()
            bundles.append(value)
            parser.stream.skip_if("comma")

        call = self.call_method("_update", args=[nodes.Const(parser.name),
                                                 nodes.List(bundles)])
        call_block = nodes.CallBlock(call, [], [], '')
        call_block.set_lineno(lineno)
        return call_block
