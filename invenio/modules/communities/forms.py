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

"""Community forms."""

from __future__ import absolute_import

from invenio.base.i18n import _
from invenio.utils.forms import InvenioBaseForm, InvenioForm as Form

from wtforms import HiddenField, StringField, TextAreaField, validators

from .models import Community


class SearchForm(Form):

    """Search Form."""

    p = StringField(
        validators=[validators.DataRequired()]
    )


class CommunityForm(Form):

    """Community form."""

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
        """Return field icon."""
        return self.field_icons.get(name, '')

    def get_field_by_name(self, name):
        """Return field by name."""
        try:
            return self._fields[name]
        except KeyError:
            return None

    def get_field_placeholder(self, name):
        """Return field placeholder."""
        return self.field_placeholders.get(name, "")

    def get_field_state_mapping(self, field):
        """Return field state mapping."""
        try:
            return self.field_state_mapping[field.short_name]
        except KeyError:
            return None

    def has_field_state_mapping(self, field):
        """Check if field has state mapping."""
        return field.short_name in self.field_state_mapping

    def has_autocomplete(self, field):
        """Check if filed has autocomplete."""
        return hasattr(field, 'autocomplete')

    #
    # Fields
    #
    identifier = StringField(
        label=_('Identifier'),
        description=_('Required. Only letters, numbers and dash are allowed.'
                      ' The identifier is used in the URL for the community'
                      ' collection, and cannot be modified later.'),
        validators=[validators.DataRequired(),
                    validators.length(
                        max=100,
                        message=_("The identifier must be less"
                                  " than 100 characters long.")),
                    validators.regexp(
                        u'^[-\w]+$',
                        message=_(
                            'Only letters, numbers and dash are allowed'))]
    )

    title = StringField(
        description='Required.',
        validators=[validators.DataRequired()]
    )

    description = TextAreaField(
        description=_(
            'Optional. A short description of the community collection,'
            ' which will be displayed on the index page of the community.'),
    )

    curation_policy = TextAreaField(
        description=_(
            'Optional. Please describe short and precise the policy by which'
            ' you accepted/reject new uploads in this community.'),
    )

    page = TextAreaField(
        description=_(
            'Optional. A long description of the community collection,'
            ' which will be displayed on a separate page linked from'
            ' the index page.'),
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
        """Validate field identifier."""
        if field.data:
            field.data = field.data.lower()
            if Community.query.filter_by(id=field.data).first():
                raise validators.ValidationError(
                    _("The identifier already exists."
                      " Please choose a different one."))


class EditCommunityForm(CommunityForm):

    """Edit community form.

    Same as collection form, except identifier is removed.
    """

    identifier = None


class DeleteCommunityForm(InvenioBaseForm):

    """Confirm deletion of a collection."""

    delete = HiddenField(default='yes', validators=[validators.DataRequired()])
