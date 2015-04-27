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

"""Documentation Flask Blueprint."""

from __future__ import unicode_literals

import os

from flask import Blueprint, abort, current_app, render_template, url_for
from flask.helpers import send_from_directory

from flask_breadcrumbs import current_breadcrumbs, default_breadcrumb_root, \
    register_breadcrumb

from flask_menu import register_menu

from invenio.base.globals import cfg
from invenio.base.i18n import _

from sphinx.websupport import WebSupport
from sphinx.websupport.errors import DocumentNotFoundError

from werkzeug.utils import cached_property, import_string


class DocsBlueprint(Blueprint):

    """Wrap blueprint with Sphinx ``WebSupport``."""

    @cached_property
    def documentation_package(self):
        """Return documentation package."""
        try:
            invenio_docs = import_string(cfg['DOCUMENTATION_PACKAGE'])
        except ImportError:
            import docs as invenio_docs
        return invenio_docs

    @cached_property
    def support(self):
        """Return an instance of Sphinx ``WebSupport``."""
        builddir = os.path.abspath(os.path.join(
            current_app.instance_path, 'docs'))
        return WebSupport(
            srcdir=self.documentation_package.__path__[0],
            builddir=builddir,
            staticroot=os.path.join(blueprint.url_prefix, 'static'),
            docroot=blueprint.url_prefix
        )

    def send_static_file(self, filename):
        """Return static file."""
        try:
            return super(self.__class__, self).send_static_file(filename)
        except Exception:
            cache_timeout = self.get_send_file_max_age(filename)
            return send_from_directory(
                os.path.join(current_app.instance_path, "docs", "static"),
                filename,
                cache_timeout=cache_timeout)


blueprint = DocsBlueprint('documentation', __name__,
                          url_prefix="/documentation",
                          template_folder='templates', static_folder='static')

default_breadcrumb_root(blueprint, '.documentation')


@blueprint.route('/', strict_slashes=True)
@blueprint.route('/<path:docname>')
@register_menu(blueprint, 'main.documentation', _('Help'), order=99)
@register_breadcrumb(blueprint, '.', _('Help'))
def index(docname=None):
    """Render documentation page."""
    try:
        document = blueprint.support.get_document(
            docname or cfg["DOCUMENTATION_INDEX"])
    except DocumentNotFoundError:
        abort(404)
    additional_breadcrumbs = [{'text': document['title'],
                               'url': url_for('.index', docname=docname)}]
    return render_template(
        'documentation/index.html', document=document,
        breadcrumbs=current_breadcrumbs + additional_breadcrumbs)
