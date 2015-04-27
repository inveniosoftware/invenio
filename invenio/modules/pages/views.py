# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Views for Pages module."""

from __future__ import unicode_literals

import six

from flask import Blueprint, current_app, render_template, request
from flask.ctx import after_this_request

from invenio.base.globals import cfg
from invenio.base.signals import before_handle_user_exception
from invenio.ext.sqlalchemy import db
from invenio.modules.pages.models import Page

from sqlalchemy import event
from sqlalchemy.orm.exc import NoResultFound

from werkzeug.exceptions import NotFound

blueprint = Blueprint('pages', __name__, url_prefix='/',
                      template_folder='templates')


@blueprint.before_app_first_request
def register():
    """Register all pages before the first application request."""
    try:
        _add_url_rule([page.url for page in Page.query.all()])
    except Exception:
        current_app.logger.warn('Pages were not loaded.')


@blueprint.errorhandler(NoResultFound)
def no_result_found(_dummy):
    """Render 404 page when no page has been found."""
    return render_template('404.html'), 404


@blueprint.errorhandler(404)
def errorhandler(exception):
    """Try to render the page otherwise continues to app error handler."""
    try:
        return view()
    except NoResultFound:
        # FIXME reraise?
        # raise exception
        pass


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
    return render_page(request.path)


# @cache.memoize for guests?
def render_page(path):
    """Internal interface to the page view."""
    page = Page.query.filter(db.or_(Page.url == request.path,
                                    Page.url == request.path + "/")).first()
    return render_template([page.template_name, cfg['PAGES_DEFAULT_TEMPLATE']],
                           page=page)


def before_url_insert(mapper, connection, target):
    """Massage target url."""
    if not target.url.startswith("/"):
        target.url = "/" + target.url
    if not target.url.endswith("/") and cfg["PAGES_APPEND_SLASH"]:
        target.url = target.url + "/"


def page_orm_handler(mapper, connection, target):
    """Handle model change."""
    _add_url_rule(target.url)


# event.listen(Page, 'after_delete', rebuild_cache)
event.listen(Page, 'before_insert', before_url_insert)
event.listen(Page, 'after_insert', page_orm_handler)
event.listen(Page, 'after_update', page_orm_handler)


def handle_not_found(exception, **extra):
    """Custom blueprint exception handler."""
    if not isinstance(exception, NotFound):
        return

    page = Page.query.filter(db.or_(Page.url == request.path,
                                    Page.url == request.path + "/")).first()
    if page is not None:
        _add_url_rule(page.url)
        # Modify request to call our errorhandler.
        req_endpoint = request.url_rule.endpoint
        request.url_rule.endpoint = blueprint.name + '.view'

        @after_this_request
        def restore_url_map(response):
            request.url_rule.endpoint = req_endpoint
            return response


before_handle_user_exception.connect(handle_not_found)


def _add_url_rule(url_or_urls):
    """Register url rule to application url map."""
    old = current_app._got_first_request
    # This is bit of cheating to overcome @flask.app.setupmethod decorator.
    current_app._got_first_request = False
    if isinstance(url_or_urls, six.string_types):
        url_or_urls = [url_or_urls]
    map(lambda url: current_app.add_url_rule(url, 'pages.view', view),
        url_or_urls)
    current_app._got_first_request = old
