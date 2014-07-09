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

"""Group Forms"""

from wtforms_alchemy import model_form_factory
from wtforms import validators, widgets
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from invenio.base.i18n import _
from invenio.utils.forms import InvenioBaseForm
from invenio.modules.accounts.models import Usergroup

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
        query_factory=lambda: Usergroup.query.all()
    )
