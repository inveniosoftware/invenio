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

"""Group Forms."""

from invenio.base.i18n import _
from invenio.utils.forms import InvenioBaseForm, InvenioForm as Form

from wtforms import StringField, TextAreaField, validators

from wtforms_alchemy import model_form_factory

ModelForm = model_form_factory(InvenioBaseForm)


class UsergroupForm(Form):

    """Create new Usergroup."""

    name = StringField(
        description='Required. A name of this group.',
        validators=[validators.DataRequired()]
    )

    description = TextAreaField(
        description=_(
            'Optional. A short description of the group'
            ' which will be displayed on the index'
            ' page of the group.'),
    )


class UsergroupNewMemberForm(InvenioBaseForm):

    """Select a user that Join an existing group."""

    emails = TextAreaField(
        description=_(
            'Required. Provide list of the emails of the users'
            ' you wish to be added'),
        validators=[validators.DataRequired(), validators.Email()]
    )
