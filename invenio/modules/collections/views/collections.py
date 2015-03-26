# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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


import warnings

from flask import (Blueprint, request, redirect, url_for, render_template,
                   current_app, g)
from flask_breadcrumbs import \
    register_breadcrumb, current_breadcrumbs, default_breadcrumb_root
from flask_menu import register_menu

from invenio.base.i18n import _
from invenio.base.decorators import wash_arguments, templated
from invenio.ext.template.context_processor import \
    register_template_context_processor
from invenio.modules.formatter import format_record
from invenio.modules.search.forms import EasySearchForm
from invenio.utils.text import slugify

from ..models import Collection

blueprint = Blueprint('collections', __name__, url_prefix='',
                      template_folder='../templates',
                      static_url_path='',  # static url path has to be empty
                                           # if url_prefix is empty
                      static_folder='../static')

default_breadcrumb_root(blueprint, '.')


@blueprint.route('/index.html', methods=['GET', 'POST'])
@blueprint.route('/index.py', methods=['GET', 'POST'])
@blueprint.route('/', methods=['GET', 'POST'])
@templated('search/index.html')
@register_menu(blueprint, 'main.collection', _('Search'), order=1)
@register_breadcrumb(blueprint, '.', _('Home'))
def index():
    """Render the homepage."""
    # legacy app support
    c = request.values.get('c')
    if c:
        warnings.warn("'c' argument for this url has been deprecated",
                      PendingDeprecationWarning)
    if c == current_app.config['CFG_SITE_NAME']:
        return redirect(url_for('.index', ln=g.ln))
    elif c is not None:
        return redirect(url_for('.collection', name=c, ln=g.ln))

    collection = Collection.query.get_or_404(1)

    @register_template_context_processor
    def index_context():
        return dict(
            of=request.values.get('of', collection.formatoptions[0]['code']),
            easy_search_form=EasySearchForm(csrf_enabled=False),
            format_record=format_record,
        )
    return dict(collection=collection)


@blueprint.route('/collection/', methods=['GET', 'POST'])
@blueprint.route('/collection/<name>', methods=['GET', 'POST'])
def collection(name=None):
    """Render the collection page.

    It renders it either with a collection specific template (aka
    collection_{collection_name}.html) or with the default collection
    template (collection.html)
    """
    if name is None:
        return redirect(url_for('.collection',
                                name=current_app.config['CFG_SITE_NAME']))
    collection = Collection.query.filter(Collection.name == name) \
                                 .first_or_404()

    @register_template_context_processor
    def index_context():
        breadcrumbs = current_breadcrumbs + collection.breadcrumbs(ln=g.ln)[1:]
        return dict(
            of=request.values.get('of', collection.formatoptions[0]['code']),
            format_record=format_record,
            easy_search_form=EasySearchForm(csrf_enabled=False),
            breadcrumbs=breadcrumbs)

    return render_template([
        'search/collection_{0}.html'.format(collection.id),
        'search/collection_{0}.html'.format(slugify(name, '_')),
        'search/collection.html'], collection=collection)
