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

"""Forms for module."""

from invenio.base.i18n import _
from invenio.modules.accounts.models import User
from invenio.modules.accounts.validators import validate_email
from invenio.utils.forms import InvenioBaseForm

from sqlalchemy.exc import SQLAlchemyError

from wtforms import StringField, validators


class EmailSignUpForm(InvenioBaseForm):

    """Form for requesting email address during sign up process."""

    email = StringField(
        label=_("Email address"),
        description=_("Required."),
        validators=[validators.DataRequired()]
    )

    def validate_email(self, field):
        """Validate email address.

        Ensures that the email address is not already registered.
        """
        field.data = field.data.lower()
        validate_email(field.data.lower())

        try:
            User.query.filter(User.email == field.data).one()
            raise validators.ValidationError(
                _(
                    "Email address %(addr)s already exists in the"
                    " database. If this is your address, please sign-in and go"
                    " to Profile > Linked Accounts to link your account.",
                    addr=field.data
                )
            )
        except SQLAlchemyError:
            pass
