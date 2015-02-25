# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

from wtforms import HiddenField, TextAreaField, BooleanField, validators

from invenio.base.i18n import _
from invenio.modules.deposit.fields import FileUploadField
from invenio.modules.deposit.field_widgets import plupload_widget
from invenio.utils.forms import InvenioBaseForm


class WebPageAnnotationForm(InvenioBaseForm):
    uuid = HiddenField(validators=[validators.Optional(), validators.UUID()])
    url = HiddenField(validators=[validators.DataRequired()])
    body = TextAreaField(label=_("Annotation"),
                         validators=[validators.InputRequired(),
                                     validators.Length(max=10000, message=_(
                                         "Your annotation is too long!"))])
    public = BooleanField(label=_("Public"), default=True)


class WebPageAnnotationFormAttachments(WebPageAnnotationForm):
    attachments = FileUploadField(widget=plupload_widget, label="Attachments")
