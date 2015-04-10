# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Extension for password contexts via Passlib.

Support validation of multiple hashing algorithms to allow for easy migration
from one algorithm to another.

Example:

.. code-block:: console

   from invenio.ext.passlib import password_context
   hash = password_context.encrypt("mypassword")
   password_context.verify("mypassword", hash)
   password_context.needs_update(hash)

Invenio legacy support:

.. code-block:: console

   from invenio.ext.passlib import password_context
   hash = password_context.encrypt(
       "mypassword",
       scheme="invenio_aes_encrypted_email",
       user="info@invenio-software.org",
    )
   password_context.verify(
       "mypassword", hash
       scheme="invenio_aes_encrypted_email",
       user="info@invenio-software.org",
   )
   password_context.needs_update(hash)


Configuration Settings
----------------------
Invenio's default password hashing algorithms can be modified using the
following application settings:

============================ ==================================================
`PASSLIB_SCHEMES`            List of supported password hashing schemes. The
                             default password hashing scheme is the first item
                             in the list.
                             **Default:**
                             `['sha512_crypt', 'invenio_aes_encrypted_email']`
`PASSLIB_DEPRECATED_SCHEMES` List of password hashing schemes that are
                             deprecated (which results in the users' hash being
                             automatically upgrade on next login). Note, all
                             deprecated scheme must also be present in
                             `PASSLIB_SCHEMES`.
                             **Default:** `['invenio_aes_encrypted_email']`
============================ ==================================================
"""

from flask import current_app

from passlib.context import CryptContext
from passlib.registry import register_crypt_handler

from werkzeug.local import LocalProxy

from .hash import invenio_aes_encrypted_email

password_context = LocalProxy(
    lambda: current_app.extensions['passlib']
)


class Passlib(object):

    """Flask-Passlib integration."""

    def __init__(self, app=None):
        """Initialize extension."""
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize application."""
        # Register Invenio legacy password hashing.
        register_crypt_handler(invenio_aes_encrypted_email)

        app.config.setdefault(
            'PASSLIB_SCHEMES',
            ['sha512_crypt', 'invenio_aes_encrypted_email']
        )
        app.config.setdefault(
            'PASSLIB_DEPRECATED_SCHEMES',
            ['invenio_aes_encrypted_email']
        )

        # Create password context.
        app.extensions['passlib'] = CryptContext(
            schemes=app.config['PASSLIB_SCHEMES'],
            deprecated=app.config['PASSLIB_DEPRECATED_SCHEMES']
        )
