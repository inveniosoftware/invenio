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

"""Account database models."""

import re

from flask_login import current_user

from invenio.ext.passlib import password_context
from invenio.ext.passlib.hash import invenio_aes_encrypted_email
from invenio.ext.sqlalchemy import db

from sqlalchemy.ext.hybrid import hybrid_property

from .helpers import send_account_activation_email
from .signals import profile_updated


def get_default_user_preferences():
    """Return default user preferences."""
    from invenio.modules.access.local_config import \
        CFG_EXTERNAL_AUTHENTICATION, CFG_EXTERNAL_AUTH_DEFAULT

    user_preference = {
        'login_method': 'Local'}

    if CFG_EXTERNAL_AUTH_DEFAULT in CFG_EXTERNAL_AUTHENTICATION:
        user_preference['login_method'] = CFG_EXTERNAL_AUTH_DEFAULT
    return user_preference


class User(db.Model):

    """Represents a User record."""

    def __str__(self):
        """Return string representation."""
        return "%s <%s>" % (self.nickname, self.email)

    __tablename__ = 'user'
    __mapper_args__ = {'confirm_deleted_rows': False}

    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                   autoincrement=True)
    email = db.Column(db.String(255), nullable=False, server_default='',
                      index=True)
    _password = db.Column(db.String(255), name="password",
                          nullable=True)
    password_salt = db.Column(db.String(255))
    password_scheme = db.Column(db.String(50), nullable=False, index=True)

    _note = db.Column(db.String(255), name="note", nullable=True)
    given_names = db.Column(db.String(255), nullable=False, server_default='')
    family_name = db.Column(db.String(255), nullable=False, server_default='')
    settings = db.Column(db.MutableDict.as_mutable(db.MarshalBinary(
        default_value=get_default_user_preferences, force_type=dict)),
        nullable=True)
    nickname = db.Column(db.String(255), nullable=False, server_default='',
                         index=True)
    last_login = db.Column(db.DateTime, nullable=False,
                           server_default='1900-01-01 00:00:00')

    PROFILE_FIELDS = ['nickname', 'email', 'family_name', 'given_names']
    """List of fields that can be updated with update_profile."""

    @staticmethod
    def check_nickname(nickname):
        """Check if it's a valid nickname."""
        re_invalid_nickname = re.compile(""".*[,'@]+.*""")
        return bool(nickname) and not nickname.startswith(' ') and \
            not nickname.endswith(' ') and \
            nickname.lower() != 'guest' and \
            not re_invalid_nickname.match(nickname)

    @staticmethod
    def check_email(email):
        """Check if it's a valid email."""
        r = re.compile(r'(.)+\@(.)+\.(.)+')
        return bool(email) and r.match(email) and not email.find(" ") > 0

    @hybrid_property
    def note(self):
        """Return the note."""
        return self._note

    @note.setter
    def note(self, note):
        """Set the note."""
        self._note = str(note)

    @hybrid_property
    def password(self):
        """Return the password."""
        return self._password

    @password.setter
    def password(self, password):
        """Set the password."""
        if password is None:
            # Unusable password.
            self._password = None
            self.password_scheme = ''
        else:
            self._password = password_context.encrypt(password)
            self.password_scheme = password_context.default_scheme()

        # Invenio legacy salt is stored in password_salt, and every new
        # password set will be migrated to new hash not relying on
        # password_salt, thus is force to empty value.
        self.password_salt = ""

    def verify_password(self, password, migrate=False):
        """Verify if password matches the stored password hash."""
        if self.password is None or password is None:
            return False

        # Invenio 1.x legacy needs externally store password salt to compute
        # hash.
        scheme_ctx = {} if \
            self.password_scheme != invenio_aes_encrypted_email.name else \
            {'user': self.password_salt}

        # Verify password
        if not password_context.verify(password, self.password,
                                       scheme=self.password_scheme,
                                       **scheme_ctx):
                return False

        # Migrate hash if needed.
        if migrate and password_context.needs_update(self.password):
            self.password = password
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise

        return True

    def verify_email(self, force=False):
        """Verify email address."""
        if force or self.note == "2":
            if self.note != "2":
                self.note = 2
                try:
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    raise
            send_account_activation_email(self)
            return True
        return False

    def update_profile(self, data):
        """Update user profile.

        Sends signal to allow other modules to subscribe to changes.
        """
        changed_attrs = {}
        for field in self.PROFILE_FIELDS:
            if field in data and getattr(self, field) != data[field]:
                changed_attrs[field] = getattr(self, field)
                setattr(self, field, data[field])

        if 'email' in changed_attrs:
            self.verify_email(force=True)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        current_user.reload()
        profile_updated.send(
            sender=self.id, user=self, changed_attrs=changed_attrs
        )

        return changed_attrs

    @property
    def guest(self):
        """Return True if the user is a guest."""
        return False if self.email else True

    #
    # Basic functions for user authentification.
    #
    def get_id(self):
        """Return the id."""
        return self.id

    def is_confirmed(self):
        """Return true if accounts has been confirmed."""
        return self.note == "1"

    def is_guest(self):
        """Return if the user is a guest."""
        return self.guest

    def is_authenticated(self):
        """Return True if user is a authenticated user."""
        return True if self.email else False

    def is_active(self):
        """Return True if use is active."""
        return self.note != "0"


class UserEXT(db.Model):

    """Represent a UserEXT record."""

    __tablename__ = 'userEXT'

    id = db.Column(db.String(255), primary_key=True, nullable=False)
    method = db.Column(db.String(50), primary_key=True, nullable=False)
    id_user = db.Column(db.Integer(15, unsigned=True),
                        db.ForeignKey(User.id), nullable=False)

    user = db.relationship(User, backref="external_identifiers")

    __table_args__ = (db.Index('id_user', id_user, method, unique=True),
                      db.Model.__table_args__)

__all__ = ('User', 'UserEXT')
