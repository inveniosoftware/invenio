# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

"""Documentation Flask Blueprint"""

from flask import render_template, current_app, abort, url_for, Blueprint
from flask.helpers import send_from_directory
from werkzeug.utils import cached_property, import_string
#from flask.ext.login import current_user, login_required

from sphinx.websupport import WebSupport
from sphinx.websupport.errors import DocumentNotFoundError

from invenio.base.globals import cfg
from invenio.base.i18n import _
from invenio.ext.breadcrumb import (default_breadcrumb_root,
                                    register_breadcrumb,
                                    breadcrumbs)
from invenio.ext.menu import register_menu


class DocsBlueprint(Blueprint):

    @cached_property
    def documentation_package(self):
        try:
            invenio_docs = import_string(cfg['CFG_DOCUMENTATION_PACKAGE'])
        except:
            try:
                import invenio_docs
            except:
                import docs as invenio_docs
        return invenio_docs

    @cached_property
    def support(self):
        return WebSupport(srcdir=self.documentation_package.__path__[0],
                          builddir=current_app.instance_path + '/docs',
                          staticroot=blueprint.url_prefix + '/static',
                          docroot=blueprint.url_prefix,
                          )

    def send_static_file(self, filename):
        try:
            return super(self.__class__, self).send_static_file(filename)
        except:
            cache_timeout = self.get_send_file_max_age(filename)
            return send_from_directory(
                current_app.instance_path + '/docs/static', filename,
                cache_timeout=cache_timeout)


blueprint = DocsBlueprint('documentation', __name__,
                          url_prefix="/documentation",
                          template_folder='templates', static_folder='static')

default_breadcrumb_root(blueprint, '.documentation')


@blueprint.route('/', strict_slashes=True)
@blueprint.route('/<path:docname>')
@register_menu(blueprint, 'main.documentation', _('Help'), order=99)
@register_breadcrumb(blueprint, '.', _('Help'))
def index(docname='index'):
    try:
        document = blueprint.support.get_document(docname)
    except DocumentNotFoundError:
        abort(404)
    additional_breadcrumbs = [{'text': document['title'],
                               'url': url_for('.index', docname=docname)}]
    return render_template('documentation/index.html', document=document,
                           breadcrumbs=breadcrumbs + additional_breadcrumbs)
