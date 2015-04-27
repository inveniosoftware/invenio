# -*- coding: utf-8 -*-
#
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

"""Flask-Admin page to configure facets sets per collection."""

from __future__ import unicode_literals

from invenio.ext.admin.views import ModelView
from invenio.ext.sqlalchemy import db
from invenio.modules.collections.models import Collection, FacetCollection
from invenio.modules.search.registry import facets

from wtforms.fields import IntegerField, SelectField
from wtforms.validators import DataRequired, ValidationError


def is_place_taken(form, field):
    """Check if the given place for given collection is already taken.

    :param form: the form containing the validated field
    :param field: the validated field
    """
    order = field.data
    collection = form.data['collection']
    if not collection:
        return

    if FacetCollection.is_place_taken(collection.id, order):
        raise ValidationError('A facet on the given place already exists')


def is_duplicated(form, field):
    """Check if the given facet is already assigned to this collection.

    :param form: the form containing the validated field
    :param field: the validated field
    """
    facet_name = field.data
    collection = form.data['collection']
    if not collection:
        return

    if FacetCollection.is_duplicated(collection.id, facet_name):
        raise ValidationError(
            'This facet is already assigned to this collection.')


def is_module_facet_module(form, field):
    """Check if the given module is a proper one.

    :param form: the form containing the validated field
    :param field: the validated field
    """
    facet_name = field.data

    if facets.get(facet_name) is None:
        raise ValidationError('The given facet does not exist.')


class FacetsAdmin(ModelView):

    """Flask-Admin module to manage facets configuration."""

    _can_create = True
    _can_edit = True
    _can_delete = True

    column_list = (
        'collection', 'order', 'facet_name',
    )

    form_args = {
        'collection': {
            'validators': [
                DataRequired(),
            ],
            'allow_blank': False,
            'query_factory':
            lambda: db.session.query(Collection).order_by(Collection.id),
        },
        'order': {
            'validators': [
                is_place_taken,
                DataRequired(),
            ],
        },
        'facet_name': {
            'validators': [
                is_module_facet_module,
                is_duplicated,
                DataRequired(),
            ],
            'query_factory': lambda: [(facet_name, facet_name)
                                      for facet_name in facets.keys()],
        },
    }

    form_overrides = {
        'facet_name': SelectField,
        'order': IntegerField,
    }

    column_default_sort = 'id_collection'

    def __init__(self, app, *args, **kwargs):
        """Constructor.

        :param app: flask application
        """
        super(FacetsAdmin, self).__init__(*args, **kwargs)


def register_admin(app, admin):
    """Called on app initialization to register administration interface."""
    admin.add_view(
        FacetsAdmin(app, FacetCollection, db.session, name='Facets',
                    category="")
    )
