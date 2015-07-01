# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2015 CERN.
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

"""WebAccount Forms."""

from flask import current_app

from flask_login import current_user

from flask_wtf import Form, validators

from invenio.base.globals import cfg
from invenio.base.i18n import _
from invenio.utils.forms import InvenioBaseForm

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from wtforms.fields import BooleanField, HiddenField, PasswordField, \
    StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, StopValidation, \
    ValidationError

from .models import User
from .validators import validate_email, validate_nickname, \
    validate_nickname_or_email, wash_login_method


def nickname_validator(form, field):
    """Validate nickname."""
    validate_nickname(field.data)
    # is nickname already taken?
    try:
        User.query.filter(User.nickname == field.data).one()
        raise validators.ValidationError(
            _("Desired nickname %(nick)s already exists in the database.",
              nick=field.data)
        )
    except (NoResultFound, MultipleResultsFound):
        pass
    except SQLAlchemyError:
        current_app.logger.exception("User nickname query problem.")


def email_validator(form, field):
    """Validate email."""
    field.data = field.data.lower()
    validate_email(field.data)


def user_email_validator(form, field):
    """Validate email and check it is not known."""
    email_validator(form, field)

    # is email already taken?
    try:
        User.query.filter(User.email == field.data).one()
        raise validators.ValidationError(
            _("Supplied email address %(email)s already exists.",
              email=field.data)
        )
    except (NoResultFound, MultipleResultsFound):
        pass
    except SQLAlchemyError:
        current_app.logger.exception("User email query problem.")


def repeat_email_validator(form, field):
    """Validate repeat email field."""
    if form.email.short_name in form.errors or \
       (form.email.data == current_user['email'] and field.data == ""):
        raise StopValidation()

    if field.data != form.email.data:
        raise ValidationError(_("Email addresses do not match."))


def min_length_password_validator(form, field):
    """Validate minimum length for password."""
    min_length = cfg['CFG_ACCOUNT_MIN_PASSWORD_LENGTH']
    if len(field.data) < min_length:
        raise validators.ValidationError(
            _("Password must be at least %(x_pass)d characters long.",
              x_pass=min_length))


def current_user_validator(attr):
    """Validator to check if value is same as current_user."""
    def _validator(form, field):
        if current_user[attr] == field.data:
            raise StopValidation()
    return _validator


def current_user_password_validator(form, field):
    """Validate password field if is the password of the user."""
    id_user = current_user.get_id()
    if not id_user:
        raise validators.ValidationError(
            _("Nobody is currently logged-in."))

    user = User.query.filter_by(id=id_user).one()
    if not user.verify_password(field.data):
        raise validators.ValidationError(
            _('The password inserted is not valid.')
        )


class VerificationForm(InvenioBaseForm):

    """Form to render a button to request email confirmation."""

    send_verification_email = SubmitField(_("Send verification email"))


class LoginForm(Form):

    """Login Form."""

    nickname = StringField(
        _("Nickname"),
        validators=[
            DataRequired(message=_("Nickname not provided")),
            validate_nickname_or_email
        ]
    )
    password = PasswordField(_("Password"))
    remember = BooleanField(_("Remember Me"))
    referer = HiddenField()
    login_method = HiddenField()
    submit = SubmitField(_("Sign in"))

    def validate_login_method(self, field):
        """Validate login_method."""
        field.data = wash_login_method(field.data)


class ProfileForm(InvenioBaseForm):

    """Profile form."""

    nickname = StringField(
        _("Username"),
        validators=[
            DataRequired(),
            current_user_validator('nickname'),
            nickname_validator
        ]
    )
    family_name = StringField(_("Family name"))
    given_names = StringField(_("Given names"))
    email = StringField(
        _("Email address"),
        filters=[lambda x: x.lower(), ],
        validators=[
            DataRequired(),
            current_user_validator('email'),
            user_email_validator
        ]
    )
    repeat_email = StringField(
        _("Re-enter email address"),
        description=_("Please re-enter your email address."),
        filters=[lambda x: x.lower() if x else x, ],
        validators=[repeat_email_validator]
    )


class LostPasswordForm(InvenioBaseForm):

    """Form to recover lost password."""

    email = StringField(
        _("Email address"),
        validators=[
            DataRequired(),
            email_validator
        ]
    )


class ResetPasswordForm(InvenioBaseForm):

    """Form to change password."""

    password = PasswordField(
        _("New password"),
        description=_("The password phrase may contain punctuation, "
                      "spaces, etc."),
        validators=[
            DataRequired(),
            min_length_password_validator
        ]
    )
    password2 = PasswordField(
        _("Confirm new password"),
        validators=[
            EqualTo('password', message=_('Both passwords must match.'))
        ]
    )


class ChangePasswordForm(InvenioBaseForm):

    """Form to change password."""

    current_password = PasswordField(
        _("Current password"),
        description=_("Your current password"),
        validators=[
            DataRequired(),
            current_user_password_validator
        ]
    )
    password = PasswordField(
        _("New password"),
        description=_("The password phrase may contain punctuation, "
                      "spaces, etc."),
        validators=[
            DataRequired(),
            min_length_password_validator,
        ]
    )
    password2 = PasswordField(
        _("Confirm new password"),
        validators=[
            EqualTo('password', message=_('Both passwords must match.'))
        ]
    )

    def validate_current_password(self, field):
        """Validate current password."""
        from invenio.ext.login import authenticate
        if not authenticate(current_user['nickname'], field.data):
            raise validators.ValidationError(
                _("Password mismatch."))


class RegisterForm(Form):

    """User registration form."""

    email = StringField(
        _("Email address"),
        validators=[
            DataRequired(message=_("Email not provided")),
            user_email_validator
        ],
        description=_("Example") + ": john.doe@example.com")
    nickname = StringField(
        _("Nickname"),
        validators=[
            DataRequired(message=_("Nickname not provided")),
            nickname_validator
        ],
        description=_("Example") + ": johnd")
    password = PasswordField(
        _("Password"),
        description=_(
            "The password phrase may contain punctuation, spaces, etc."
        ),
        validators=[
            DataRequired(),
            min_length_password_validator
        ],
    )
    password2 = PasswordField(
        _("Confirm password"),
        validators=[
            EqualTo('password', message=_('Both passwords must match.')),
        ]
    )
    referer = HiddenField()
    action = HiddenField(default='login')
    submit = SubmitField(_("Register"))
