# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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

"""Community Module Forms"""

from __future__ import absolute_import

from invenio.base.i18n import _
from invenio.utils.forms import InvenioForm as Form, InvenioBaseForm
from wtforms import TextField, \
    TextAreaField, \
    HiddenField, \
    validators
from .models import Community


#
# Form
#

class SearchForm(Form):
    """
    Search Form
    """
    p = TextField(
        validators=[validators.required()]
    )


class CommunityForm(Form):
    """
    Community form.
    """
    field_sets = [
        ('Information', [
            'identifier', 'title', 'description', 'curation_policy',
            'page'
        ], {'classes': 'in'}),
    ]

    field_placeholders = {
    }

    field_state_mapping = {
    }

    #
    # Methods
    #
    def get_field_icon(self, name):
        return self.field_icons.get(name, '')

    def get_field_by_name(self, name):
        try:
            return self._fields[name]
        except KeyError:
            return None

    def get_field_placeholder(self, name):
        return self.field_placeholders.get(name, "")

    def get_field_state_mapping(self, field):
        try:
            return self.field_state_mapping[field.short_name]
        except KeyError:
            return None

    def has_field_state_mapping(self, field):
        return field.short_name in self.field_state_mapping

    def has_autocomplete(self, field):
        return hasattr(field, 'autocomplete')

    #
    # Fields
    #
    identifier = TextField(
        label=_('Identifier'),
        description='Required. Only letters, numbers and dash are allowed. The identifier is used in the URL for the community collection, and cannot be modified later.',
        validators=[validators.required(), validators.length(max=100, message="The identifier must be less than 100 characters long."), validators.regexp(u'^[-\w]+$', message='Only letters, numbers and dash are allowed')]
    )

    title = TextField(
        description='Required.',
        validators=[validators.required()]
    )

    description = TextAreaField(
        description='Optional. A short description of the community collection, which will be displayed on the index page of the community.',
    )

    curation_policy = TextAreaField(
        description='Optional. Please describe short and precise the policy by which you accepted/reject new uploads in this community.',
    )

    page = TextAreaField(
        description='Optional. A long description of the community collection, which will be displayed on a separate page linked from the index page.',
    )

    field_icons = {
        'identifier': 'barcode',
        'title': 'file-alt',
        'description': 'pencil',
        'curation_policy': 'check',
    }

    #
    # Validation
    #
    def validate_identifier(self, field):
        if field.data:
            field.data = field.data.lower()
            if Community.query.filter_by(id=field.data).first():
                raise validators.ValidationError("The identifier already exists. Please choose a different one.")


class EditCommunityForm(CommunityForm):
    """
    Same as collection form, except identifier is removed.
    """
    identifier = None


class DeleteCommunityForm(InvenioBaseForm):
    """
    Form to confirm deletion of a collection:
    """
    delete = HiddenField(default='yes', validators=[validators.required()])
