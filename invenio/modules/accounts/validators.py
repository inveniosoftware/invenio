# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2013, 2015 CERN.
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

"""Implements account validators."""

import re

from flask import current_app

from flask_wtf import validators

from sqlalchemy.exc import SQLAlchemyError

from invenio.base.i18n import _

from .models import User

re_invalid_nickname = re.compile(""".*[,'@]+.*""")


def wash_login_method(login_method):
    """Wash the :param:`login_method` that came from the web input form.

    :param login_method: Wanted login_method value as it came from the
        web input form.
    :type login_method: string

    :return: Washed version of login_method.  If the login_method
        value is valid, then return it.  If it is not valid, then
        return `Local' (the default login method).
    """
    if login_method in current_app.config.get('CFG_EXTERNAL_AUTHENTICATION',
                                              []):
        return login_method
    else:
        return current_app.config.get('CFG_AUTHENTICATION_METHOD_DEFAULT',
                                      'Local')


def validate_nickname_or_email(form, field):
    """Validate nickname or email."""
    try:
        User.query.filter(User.nickname == field.data).one()
    except SQLAlchemyError:
        try:
            User.query.filter(User.email == field.data).one()
        except SQLAlchemyError:
            raise validators.ValidationError(
                _('Not a valid nickname or email: %(x_data)s',
                  x_data=field.data)
            )


def validate_nickname(nickname):
    """Check whether wanted NICKNAME supplied by the user is valid.

    At the moment we just check whether it is not empty, does not
    contain blanks or @, is not equal to `guest', etc.

    This check relies on re_invalid_nickname regexp (see above)
    Return 1 if nickname is okay, return 0 if it is not.
    """
    if nickname and \
       not(nickname.startswith(' ') or nickname.endswith(' ')) and \
       nickname.lower() != 'guest':
        if re_invalid_nickname.match(nickname) is not None:
            raise validators.ValidationError(
                _("Desired nickname %(x_name)s is invalid.", x_name=nickname)
            )


def validate_email(email):
    """Check whether wanted EMAIL address supplied by the user is valid.

    At the moment we just check whether it contains '@' and whether
    it doesn't contain blanks.  We also check the email domain if
    CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN is set.
    """
    CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN = current_app.config.get(
        'CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN')
    if (email.find("@") <= 0) or (email.find(" ") > 0):
        raise validators.ValidationError(
            _("Supplied email address %(x_addr)s is invalid.", x_addr=email)
        )
    elif CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN:
        if not email.endswith(CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN):
            raise validators.ValidationError(
                _("Supplied email address %(x_addr)s is invalid.",
                  x_addr=email)
            )
