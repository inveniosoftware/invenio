# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

from invenio.webinterface_handler_flask_utils import _
from flask.ext.wtf import Form, SubmitField, BooleanField, TextField, \
                         TextAreaField, PasswordField, Required, \
                         HiddenField,  validators
from invenio.websession_model import User

def validate_nickname_or_email(form, field):
    try:
        u = User.query.filter(User.nickname==field.data).one()
    except:
        try:
            u = User.query.filter(User.email==field.data).one()
        except:
            raise validators.ValidationError(
                _('Not valid nickname or email: %s') % (field.data, ))

#def validate_password(form, field):
#    try:
#        db.session.query(User).filter(db.or_(
#            User.nickname==form.nickname.data, User.email==form.nickname.data),
#            User.password==db.func.aes_encrypt(User.email,field.data)).one()
#    except:
#        raise validators.ValidationError(_("Password does not match."))

class LoginForm(Form):
    nickname = TextField(_("Nickname"),
        validators=[Required(message=_("Nickname not provided")),
                    validate_nickname_or_email])
    password = PasswordField(_("Password"))#,
    #    validators=[Required(message=_("Password not provided"))])#,
    #                validate_password])
    remember = BooleanField(_("Remember Me"))
    referer = HiddenField()
    submit = SubmitField(_("Sing in"))
