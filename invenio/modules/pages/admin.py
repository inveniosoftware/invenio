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

"""Pages admin interface."""

from __future__ import unicode_literals

from flask import current_app

from invenio.ext.admin.views import ModelView
from invenio.ext.sqlalchemy import db
from invenio.modules.pages.models import Page, PageList, PagePageList
from wtforms import TextAreaField, IntegerField

from jinja2 import TemplateNotFound

from wtforms.validators import ValidationError


def template_exists(form, field):
    """ Form validation: check that selected template exists """
    if not field.data:
        return
    template_name = field.data
    try:
        current_app.jinja_env.get_template(template_name)
    except TemplateNotFound:
        raise ValidationError("Template selected does not exist")


class PagesAdmin(ModelView):

    """Page admin."""

    _can_create = True
    _can_edit = True
    _can_delete = True

    create_template = 'pages/edit.html'
    edit_template = 'pages/edit.html'

    column_list = (
        'url', 'title', 'last_modified',
    )
    column_searchable_list = ('url',)

    page_size = 100

    form_excluded_columns = ('represents_list', 'part_of_lists')
    """Exclude foreign keys."""

    form_args = dict(
        template_name=dict(
            default="pages/default.html",  # FIXME: PAGES_DEFAULT_TEMPLATE
            validators=[template_exists]
        ))

    form_widget_args = {
        'created': {
            'readonly': True
        },
        'last_modified': {
            'readonly': True
        },
    }

    form_overrides = dict(description=TextAreaField)

    def __init__(self, model, session, **kwargs):
        """Init."""
        super(PagesAdmin, self).__init__(
            model, session, **kwargs
        )


class PagesListAdmin(ModelView):
    _can_create = True
    _can_edit = True
    _can_delete = True

    column_list = (
        'id', 'page_id',
    )

    form_columns = ('id', 'page_id')
    form_overrides = dict(page_id=IntegerField)

    page_size = 100

    def __init__(self, model, session, **kwargs):
        super(PagesListAdmin, self).__init__(
            model, session, **kwargs
        )


class PagesPagesListAdmin(ModelView):
    _can_create = True
    _can_edit = True
    _can_delete = True

    column_list = (
        'id', 'list_id', 'page_id'
    )

    form_columns = ('list_id', 'page_id')
    form_overrides = dict(list_id=IntegerField, page_id=IntegerField)

    page_size = 100

    def __init__(self, model, session, **kwargs):
        super(PagesPagesListAdmin, self).__init__(
            model, session, **kwargs
        )


def register_admin(app, admin):
    """Called on app init to register administration interface."""
    admin.add_view(PagesAdmin(
        Page, db.session,
        name='Pages',
        endpoint='Pages',
        category='Pages')
    )

    admin.add_view(PagesListAdmin(
        PageList, db.session,
        name='PagesList',
        endpoint='PagesList',
        category='Pages')
    )

    admin.add_view(PagesPagesListAdmin(
        PagePageList, db.session,
        name='PagesPagesList',
        endpoint='PagesPagesList',
        category='Pages')
    )
