# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

from wtforms import TextField, \
                    FileField, \
                    FormField, \
                    SubmitField
from invenio.webdeposit_form import WebDepositForm as Form
from invenio.webinterface_handler_flask_utils import _
# Import custom fields
from invenio.webdeposit_load_fields import fields
from invenio.webdeposit_field_widgets import bootstrap_submit

__all__ = ['PhotoForm']


class Dimensions(Form):
    height = TextField(label=_('Height'))
    width = TextField(label=_('Width'))


class PhotoForm(Form):

    title = fields.TitleField(label=_('Photo Title'))
    dimensions = FormField(Dimensions)
    file_field = FileField(label=_('File'))
    submit = SubmitField(label=_('Submit Photo'), widget=bootstrap_submit)

    #configuration variables
    _title = _("Submit a Photo")
    _drafting = True  # enable and disable drafting
