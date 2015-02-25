# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014, 2015 CERN.
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

"""Comments Forms."""

from invenio.base.i18n import _
from invenio.modules.annotations.noteutils import HOWTO
from invenio.utils.forms import InvenioBaseForm

from wtforms import HiddenField, SelectField, StringField, \
    TextAreaField, validators


class AddCmtRECORDCOMMENTForm(InvenioBaseForm):

    """Define form for writing new comment."""

    title = StringField(_('Title'))
    body = TextAreaField(_('Message'), [
        validators.length(
            0, 10000,
            message=_(
                "Your message is too long, please edit it. "
                "Maximum size allowed is %{length}i characters.",
                length=10000
            )
        )
    ])
    in_reply_to_id_cmtRECORDCOMMENT = HiddenField(default=0)
    notes_howto = HOWTO
    pdf_page = HiddenField(validators=[validators.Optional(),
                                       validators.NumberRange()])


class AddCmtRECORDCOMMENTFormReview(AddCmtRECORDCOMMENTForm):

    """Define form for record comment review."""

    star_score = SelectField(_('Stars'), choices=[('1', _('*')),
                                                  ('2', _('**')),
                                                  ('3', _('***')),
                                                  ('4', _('****')),
                                                  ('5', _('*****'))])
