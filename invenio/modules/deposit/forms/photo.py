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

from invenio.webdeposit_form import WebDepositForm as Form
from invenio.base.i18n import _
# Import custom fields
from invenio.modules.deposit import fields
from invenio.webdeposit_field_widgets import date_widget, plupload_widget, \
                                             bootstrap_submit

__all__ = ['PhotoForm']


class PhotoForm(Form):

    title = fields.TitleField(label=_('Photo Title'))
    author = fields.AuthorField(label=_('Photo Author'))
    date = fields.Date(label=_('Photo Date'),
                       widget=date_widget)
    keywords = fields.KeywordsField(label=_('Keywords'))
    notes = fields.NotesField(label=_('Description'))
    plupload_file = fields.FileUploadField(label=_('Files'),
                                           widget=plupload_widget)
    submit = fields.SubmitField(label=_('Submit Photo'), widget=bootstrap_submit)

    #configuration variables
    _title = _("Submit a Photo")
    _drafting = True  # enable and disable drafting
