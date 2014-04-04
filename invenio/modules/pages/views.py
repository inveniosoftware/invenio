# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

from invenio.modules.pages.models import Page
from invenio.modules.pages.errors import PageNotFound
from invenio.ext.cache import cache

from sqlalchemy.orm.exc import NoResultFound
from flask import Blueprint, request, render_template

blueprint = Blueprint('pages', __name__, url_prefix='/', template_folder='templates')

DEFAULT_TEMPLATE = 'pages/default.html'


def page(request, url):
    """
    Public interface to the page view.

    Models: `pages.pages`
    Templates: Uses the template defined by the ``template_name`` field,
        or :template:`pages/default.html` if template_name is not defined.
    Context:
        page
            `pages.pages` object
    """
    if not url.startswith('/'):
        url = '/' + url

    try:
        f = Page.query.filter_by(url=url).one()
    except NoResultFound:
        return render_template('404.html'), 404

    return render_page(request, f)


def render_page(request, f):
    """
    Internal interface to the flat page view.
    """
    if f.template_name:
        return render_template(f.template_name, page=f)
    else:
        return render_template(DEFAULT_TEMPLATE, page=f)


@blueprint.app_errorhandler(404)
def errorhandler(error):
    # Is there a flat page for this url?
    pages_map = cache.get("pages-url-map")
    if not pages_map:
        # cache maybe expired, or there are no pages yet
        rebuild_pages_cache()
        pages_map = cache.get("pages-url-map")
    if pages_map:
        req_path = request.path
        if req_path in pages_map:
            try:
                return page(request, req_path)
            except PageNotFound:
                pass
    return render_template('404.html'), 404


def rebuild_pages_cache():
    urls = [page.url for page in Page.query.all()]
    cache.set("pages-url-map", dict.fromkeys(urls), timeout=84000)
