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

"""WebAccount Forms"""

from wtforms.validators import Required
from flask.ext.wtf import Form, validators
from wtforms.fields import SubmitField, BooleanField, TextField, \
    TextAreaField, PasswordField, HiddenField
from sqlalchemy.exc import SQLAlchemyError

from invenio.base.i18n import _
from invenio.legacy.webuser import email_valid_p
from invenio.utils.forms import InvenioBaseForm
from .models import User
from .validators import wash_login_method, validate_nickname_or_email, \
    validate_email, validate_nickname


class LoginForm(Form):
    nickname = TextField(
        _("Nickname"),
        validators=[Required(message=_("Nickname not provided")), validate_nickname_or_email])
    password = PasswordField(_("Password"))
    remember = BooleanField(_("Remember Me"))
    referer = HiddenField()
    login_method = HiddenField()
    submit = SubmitField(_("Sign in"))

    def validate_login_method(self, field):
        field.data = wash_login_method(field.data)


class ChangeUserEmailSettingsForm(InvenioBaseForm):
    email = TextField(_("New email"))

    def validate_email(self, field):
        field.data = field.data.lower()
        if validate_email(field.data.lower()) != 1:
            raise validators.ValidationError(
                _("Supplied email address %(email)s is invalid.", email=field.data)
            )

        # is email already taken?
        try:
            User.query.filter(User.email == field.data).one()
            raise validators.ValidationError(
                _("Supplied email address %(email)s already exists in the database.", email=field.data)
            )
        except SQLAlchemyError:
            pass

        # if the email is changed we reset the password to a random one, such
        # that the user is forced to confirm the new email
        import random
        from webuser import updatePasswordUser
        updatePasswordUser(current_user['id'], int(random.random() * 1000000))

        from flask import flash, url_for
        flash(_("Note that if you have changed your email address, you \
                will have to <a href=%(link)s>reset</a> your password anew.",
                link=url_for('webaccount.lost')), 'warning')

class LostPasswordForm(InvenioBaseForm):
    email = TextField(_("Email address"))

    def validate_email(self, field):
        field.data = field.data.lower()
        if email_valid_p(field.data) != 1:
            raise validators.ValidationError(
                _("Supplied email address %(email)s is invalid.", email=field.data)
            )

        # is email registered?
        try:
            User.query.filter(User.email == field.data).one()
        except SQLAlchemyError:
            raise validators.ValidationError(
                _("Supplied email address %(email)s is not registered.", email=field.data)
            )


class ChangePasswordForm(InvenioBaseForm):
    current_password = PasswordField(_("Current password"),
                                     description=_("Your current password"))
    password = PasswordField(
        _("Password"),
        description=
        _("The password phrase may contain punctuation, spaces, etc."))
    password2 = PasswordField(_("Confirm password"),)

    def validate_current_password(self, field):
        if len(field.data) == 0:
            raise validators.ValidationError(
                _("Please enter your current password"))

        from invenio.modules.account.views import update_login
        if update_login(current_user['nickname'], field.data) is None:
            raise validators.ValidationError(
                _("The current password you entered does\
                  not match with our records."))

    def validate_password(self, field):
        CFG_ACCOUNT_MIN_PASSWORD_LENGTH = 6
        if len(field.data) < CFG_ACCOUNT_MIN_PASSWORD_LENGTH:
            raise validators.ValidationError(
                _("Password must be at least %d characters long." % (
                    CFG_ACCOUNT_MIN_PASSWORD_LENGTH, )))

    def validate_password2(self, field):
        if field.data != self.password.data:
            raise validators.ValidationError(_("Both passwords must match."))


class RegisterForm(Form):
    """
    User registration form
    """
    email = TextField(
        _("Email address"),
        validators=[Required(message=_("Email not provided"))],
        description=_("Example") + ": john.doe@example.com")
    nickname = TextField(
        _("Nickname"),
        validators=[Required(message=_("Nickname not provided"))],
        description=_("Example") + ": johnd")
    password = PasswordField(
        _("Password"),
        description=_("The password phrase may contain punctuation, spaces, etc."))
    password2 = PasswordField(_("Confirm password"),)
    referer = HiddenField()
    action = HiddenField(default='login')
    submit = SubmitField(_("Register"))

    def validate_nickname(self, field):
        validate_nickname(field.data)
        # is nickname already taken?
        try:
            User.query.filter(User.nickname == field.data).one()
            raise validators.ValidationError(
                _("Desired nickname %(nick)s already exists in the database.", nick=field.data)
            )
        except SQLAlchemyError:
            pass

    def validate_email(self, field):
        field.data = field.data.lower()
        validate_email(field.data.lower())
        # is email already taken?
        try:
            User.query.filter(User.email == field.data).one()
            raise validators.ValidationError(
                _("Supplied email address %(addr)s already exists in the database.", addr=field.data)
            )
        except SQLAlchemyError:
            pass

    def validate_password(self, field):
        CFG_ACCOUNT_MIN_PASSWORD_LENGTH = 6
        if len(field.data) < CFG_ACCOUNT_MIN_PASSWORD_LENGTH:
            raise validators.ValidationError(
                _("Password must be at least %d characters long." % (
                    CFG_ACCOUNT_MIN_PASSWORD_LENGTH, )))

    def validate_password2(self, field):
        if field.data != self.password.data:
            raise validators.ValidationError(_("Both passwords must match."))
