# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

from wtforms import TextField, ValidationError
from invenio.modules.deposit.field_base import WebDepositField

__all__ = ['TitleField']


def validate_title(form, field):
    value = field.data or ''
    # Empty string allowed (required validator may be defined on per-field basis)
    if value == "" or value.isspace():
        return

    error_message = ''
    if len(value) <= 4:
        raise ValidationError("This field must have at least 4 characters")


class TitleField(WebDepositField, TextField):
    def __init__(self, **kwargs):
        defaults = dict(
            icon='book',
            export_key='title.title',
            widget_classes="form-control"
            #FIXMEvalidators=[validate_title]
        )
        defaults.update(kwargs)
        super(TitleField, self).__init__(**defaults)
