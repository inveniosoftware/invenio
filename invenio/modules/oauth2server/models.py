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

from __future__ import absolute_import

from flask import current_app
from flask.ext.login import current_user
from werkzeug.security import gen_salt
from wtforms import validators
from sqlalchemy_utils import URLType

from invenio.ext.sqlalchemy import db
from invenio.ext.login.legacy_user import UserInfo


class OAuthUserProxy(object):
    """
    Proxy object to an Invenio User
    """
    def __init__(self, user):
        self._user = user

    def __getattr__(self, name):
        """ Pass any undefined attribute to the underlying object """
        return getattr(self._user, name)

    def __getstate__(self):
        return self.id

    def __setstate__(self, state):
        self._user = UserInfo(state)

    @property
    def id(self):
        return self._user.get_id()

    def check_password(self, password):
        return self.password == password

    @classmethod
    def get_current_user(cls):
        return cls(current_user._get_current_object())


class Scope(object):
    def __init__(self, id_, help_text='', group='', internal=False):
        self.id = id_
        self.group = group
        self.help_text = help_text
        self.is_internal = internal


class Client(db.Model):
    """
    A client is the app which want to use the resource of a user. It is
    suggested that the client is registered by a user on your site, but it
    is not required.

    The client should contain at least these information:

        client_id: A random string
        client_secret: A random string
        client_type: A string represents if it is confidential
        redirect_uris: A list of redirect uris
        default_redirect_uri: One of the redirect uris
        default_scopes: Default scopes of the client

    But it could be better, if you implemented:

        allowed_grant_types: A list of grant types
        allowed_response_types: A list of response types
        validate_scopes: A function to validate scopes

    """

    __tablename__ = 'oauth2CLIENT'

    name = db.Column(
        db.String(40),
        info=dict(
            label='Name',
            description='Name of application (displayed to users).',
            validators=[validators.Required()]
        )
    )
    """ Human readable name of the application """

    description = db.Column(
        db.Text(),
        default=u'',
        info=dict(
            label='Description',
            description='Optional. Description of the application'
                        ' (displayed to users).',
        )
    )
    """ Human readable description """

    website = db.Column(
        URLType(),
        info=dict(
            label='Website URL',
            description='URL of your application (displayed to users).',
        ),
        default=u'',
    )

    user_id = db.Column(db.ForeignKey('user.id'))
    """ Creator of the client application """

    client_id = db.Column(db.String(255), primary_key=True)
    """ Client application ID """

    client_secret = db.Column(
        db.String(255), unique=True, index=True, nullable=False
    )
    """ Client application secret """

    is_confidential = db.Column(db.Boolean, default=True)
    """ Determine if client application is public or not.  """

    is_internal = db.Column(db.Boolean, default=False)
    """ Determins if client application is an internal application """

    _redirect_uris = db.Column(db.Text)
    """
    A comma-separated list of redirect URIs. First URI is the default URI.
    """

    _default_scopes = db.Column(db.Text)
    """
    A comma-separated list of default scopes of the client. The value of the
    scope parameter is expressed as a list of space-delimited,
    case-sensitive strings.
    """

    user = db.relationship('User')
    """ Relationship to user """

    @property
    def allowed_grant_types(self):
        return current_app.config['OAUTH2_ALLOWED_GRANT_TYPES']

    @property
    def allowed_response_types(self):
        return current_app.config['OAUTH2_ALLOWED_RESPONSE_TYPES']

    # def validate_scopes(self, scopes):
    #     return self._validate_scopes

    @property
    def client_type(self):
        if self.is_confidential:
            return 'confidential'
        return 'public'

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        try:
            return self.redirect_uris[0]
        except IndexError:
            pass

    @property
    def default_scopes(self):
        if self._default_scopes:
            return self._default_scopes.split()
        return []

    def gen_salt(self):
        self.reset_client_id()
        self.reset_client_secret()

    def reset_client_id(self):
        self.client_id = gen_salt(
            current_app.config.get('OAUTH2_CLIENT_ID_SALT_LEN')
        )

    def reset_client_secret(self):
        self.client_secret = gen_salt(
            current_app.config.get('OAUTH2_CLIENT_SECRET_SALT_LEN')
        )


class Token(db.Model):
    """
    A bearer token is the final token that can be used by the client.
    """
    __tablename__ = 'oauth2TOKEN'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    """ Object ID """

    client_id = db.Column(
        db.String(40), db.ForeignKey('oauth2CLIENT.client_id'),
        nullable=False,
    )
    """ Foreign key to client application """

    client = db.relationship('Client')
    """ SQLAlchemy relationship to client application """

    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id')
    )
    """ Foreign key to user """

    user = db.relationship('User')
    """ SQLAlchemy relationship to user """

    token_type = db.Column(db.String(255), default='bearer')
    """ Token type - only bearer is supported at the moment """

    access_token = db.Column(db.String(255), unique=True)

    refresh_token = db.Column(db.String(255), unique=True)

    expires = db.Column(db.DateTime, nullable=True)

    _scopes = db.Column(db.Text)

    is_personal = db.Column(db.Boolean, default=False)
    """ Personal accesss token """

    is_internal = db.Column(db.Boolean, default=False)
    """ Determines if token is an internally generated token. """

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []

    @scopes.setter
    def scopes(self, scopes):
        self._scopes = " ".join(scopes) if scopes else ""

    def scopes_ordered(self, scopes):
        self._scopes = " ".join(scopes) if scopes else ""

    def get_visible_scopes(self):
        """ Get list of non-internal scopes for token. """
        from .registry import scopes as scopes_registry
        return [k for k, s in scopes_registry.choices() if k in self.scopes]

    @classmethod
    def create_personal(cls, name, user_id, scopes=None, is_internal=False):
        """
        Create a personal access token (a token that is bound to a specific
        user and which doesn't expire).
        """
        scopes = " ".join(scopes) if scopes else ""

        c = Client(
            name=name,
            user_id=user_id,
            is_internal=True,
            is_confidential=False,
            _default_scopes=scopes
        )
        c.gen_salt()

        t = Token(
            client_id=c.client_id,
            user_id=user_id,
            access_token=gen_salt(
                current_app.config.get('OAUTH2_TOKEN_PERSONAL_SALT_LEN')
            ),
            expires=None,
            _scopes=scopes,
            is_personal=True,
            is_internal=is_internal,
        )

        db.session.add(c)
        db.session.add(t)
        db.session.commit()

        return t
