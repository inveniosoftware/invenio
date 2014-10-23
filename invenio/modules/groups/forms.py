# -*- coding: utf-8 -*-
##
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

"""Group Forms."""

# from flask import url_for
from wtforms import validators, widgets
from wtforms.fields import BooleanField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms_alchemy import model_form_factory

from invenio.base.i18n import _
from invenio.modules.accounts.models import Usergroup
from invenio.utils.forms import InvenioBaseForm

ModelForm = model_form_factory(InvenioBaseForm)


class UsergroupForm(ModelForm):

    """Create new Usergroup."""

    class Meta:

        """Meta class model for *WTForms-Alchemy*."""

        model = Usergroup
        strip_string_fields = True
        field_args = dict(
            name=dict(
                label=_('Name'),
                validators=[validators.Required()],
                widget=widgets.TextInput(),
            ),
            description=dict(label=_('Description')),
            join_policy=dict(label=_('Join policy')),
            login_method=dict(label=_('Login method'))
        )


class JoinUsergroupForm(InvenioBaseForm):

    """Join existing group."""

    id_usergroup = QuerySelectField(
        _('Join group'),
        get_pk=lambda i: i.id,
        get_label=lambda i: i.name,
    )


class UserJoinGroupForm(InvenioBaseForm):

    """Select a user that Join an existing group."""

    # TODO use a autocomplete field instead a select
    id_user = QuerySelectField(
        _('Add user'),
        get_pk=lambda i: i.id,
        get_label=lambda i: i.nickname,
    )
    # set as admin of the group
    user_status = BooleanField(label=_('as Admin'))
