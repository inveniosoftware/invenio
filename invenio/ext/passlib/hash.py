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

"""Legacy Invenio hash support."""

import hashlib

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from passlib.utils.compat import str_to_uascii
from passlib.utils.handlers import HasUserContext, StaticHandler

__all__ = ('invenio_aes_encrypted_email', )


def _mysql_aes_key(key):
    final_key = bytearray(16)
    for i, c in enumerate(key):
        final_key[i % 16] ^= ord(key[i])
    return bytes(final_key)


def _mysql_aes_pad(val):
    pad_value = 16 - (len(val) % 16)
    return '%s%s' % (val, chr(pad_value)*pad_value)


def _mysql_aes_unpad(val):
    pad_value = ord(val[-1])
    return val[:-pad_value]


def _mysql_aes_engine(key):
    """Create MYSQL AES cipher engine."""
    return Cipher(algorithms.AES(key), modes.ECB(), default_backend())


def mysql_aes_encrypt(val, key):
    """MySQL AES encrypt value with secret key."""
    k = _mysql_aes_key(key)
    v = _mysql_aes_pad(val)
    e = _mysql_aes_engine(k).encryptor()

    return e.update(v) + e.finalize()


def mysql_aes_decrypt(encrypted_val, key):
    """MySQL AES decrypt value with secret key."""
    k = _mysql_aes_key(key)
    d = _mysql_aes_engine(k).decryptor()
    return _mysql_aes_unpad(d.update(encrypted_val) + d.finalize())


class invenio_aes_encrypted_email(HasUserContext, StaticHandler):

    """Invenio AES encryption of user email using password as secret key.

    Invenio 1.x was AES encrypting the users email address with the password
    as the secret key and storing it in a blob column. This e.g. caused
    problems when a user wanted to change email address.

    This hashing engine, differs from Invenio 1.x in that it sha256 hashes the
    encrypted value as well to produce a string in the same length instead of
    a binary blob. It is not done for extra security, just for convenience of
    migration to using passlib's sha512.

    An upgrade recipe is provided to migrated existing binary password hashes
    to hashes of this engine.
    """

    name = "invenio_aes_encrypted_email"

    def _calc_checksum(self, secret):
        """Calculate string."""
        return str_to_uascii(
            hashlib.sha256(mysql_aes_encrypt(self.user, secret)).hexdigest()
        )
