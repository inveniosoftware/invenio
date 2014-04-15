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


from invenio.base.globals import cfg
from invenio.modules.pages.models import Page
from invenio.ext.cache import cache

from sqlalchemy.orm.exc import NoResultFound
from flask import Blueprint, request, render_template, got_request_exception

blueprint = Blueprint('pages', __name__, url_prefix='/',
                      template_folder='templates')


def view():
    """
    Public interface to the page view.

    Models: `pages.pages`
    Templates: Uses the template defined by the ``template_name`` field,
        or :template:`pages/default.html` if template_name is not defined.
    Context:
        page
            `pages.pages` object
    """
    try:
        page = Page.query.filter_by(url=request.path).one()
    except NoResultFound:
        return render_template('404.html'), 404

    return render_page(page)


def render_page(page):
    """
    Internal interface to the page view.
    """
    return render_template([page.template_name, cfg['PAGES_DEFAULT_TEMPLATE']],
                           page=page)


def handle_404(sender, exception, **extra):
    sender.logger.info('Got exception during processing: %s', exception)


def setup_app(app):
    with app.app_context():
        for page in Page.query.all():
            app.add_url_rule(page.url, 'pages.view', view)

    #FIXME investigate signals otherwise add new into base/wrappers.py
    got_request_exception.connect(handle_404, app)

    return app
