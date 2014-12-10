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

from wtforms import TextAreaField
from wtforms.fields import TextField, SelectField, BooleanField, HiddenField

from invenio.base.i18n import _
from invenio.utils.forms import InvenioBaseForm

from . import models


class AlertForm(InvenioBaseForm):

    """Create new Alert."""

    id_user = HiddenField()
    id_query = HiddenField()
    frequency = SelectField(
        _('Search-checking frequency'),
        choices=[f for f in models.UserQueryBasket.FREQUENCIES.iteritems()]
    )
    id_basket = SelectField(
        _('Store results in basket'),
        coerce=int,
    )
    notification = BooleanField(_('Send notification email'))
    alert_name = TextField(_('Alert name'))
    alert_desc = TextAreaField(_('Alert description'))
    alert_recipient = TextField(_('Alert recipient'))
