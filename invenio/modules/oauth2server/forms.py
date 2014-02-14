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


from wtforms_alchemy import model_form_factory
from wtforms import fields, validators, widgets
from invenio.utils.forms import InvenioBaseForm

from .models import Client

ModelForm = model_form_factory(InvenioBaseForm)


class ClientForm(ModelForm):
    class Meta:
        model = Client
        exclude = [
            'client_secret',
            'is_internal',
            'is_confidential',
        ]
        strip_string_fields = True
        field_args = dict(website=dict(
            validators=[validators.Required(), validators.URL()],
            widget=widgets.TextInput(),
        ))


class TokenForm(InvenioBaseForm):
    name = fields.TextField(
        description="Name of personal access token.",
        validators=[validators.Required()],
    )
    #scopes = fields.SelectMultipleField()
