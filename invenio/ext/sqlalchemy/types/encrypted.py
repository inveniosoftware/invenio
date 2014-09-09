# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013, 2014 CERN.
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

"""Implement Encrypted type."""

import base64
import hashlib
from sqlalchemy.types import TypeDecorator, String
from Crypto.Cipher import AES


class EncryptDecryptModule(object):

    """Provide encryption and decryption methods."""

    BLOCK_SIZE = 16
    PADDING = '*'

    @classmethod
    def pad(cls, value):
        """Pad the message to be encrypted, if needed."""
        BS = cls.BLOCK_SIZE
        P = cls.PADDING
        padded = (value + (BS - len(value) % BS) * P)
        return padded

    @classmethod
    def encrypt(cls, key, value):
        """Encrypt a message."""
        pad_func = cls.pad
        encrypted = base64.b64encode(key.encrypt(pad_func(value)))
        return encrypted

    @classmethod
    def decrypt(cls, key, value):
        """Decrypt a message."""
        P = cls.PADDING
        decrypted = (key.decrypt(base64.b64decode(value)).
                     decode('utf-8').rstrip(P))
        return decrypted


class AESEngine(EncryptDecryptModule):

    """Wrap AES symmetric cipher engine."""

    @staticmethod
    def cipher(key):
        """Create a new AES cipher."""
        return AES.new(hashlib.sha256(key).digest())


class Encrypted(TypeDecorator):

    """Implement an Encrypted column type."""

    impl = String
    encr_decr_engine = AESEngine

    def __init__(self, key, **kwargs):
        """Initialization.

        :param key: :class:`~sqlalchemy.types.String`
            a given key for encryption/decryption
        """
        super(Encrypted, self).__init__(**kwargs)
        # produce a 32-bytes key
        self.cipher = self.encr_decr_engine.cipher(key)

    def process_bind_param(self, value, dialect):
        """Encrypt a value on the way in.

        :param value: :class:`~sqlalchemy.types.String`
            the value to be encrypted
        """
        return self.encr_decr_engine.encrypt(self.cipher, value)

    def process_result_value(self, value, dialect):
        """Decrypt value on the way out.

        :param value: the value to be decrypted
        """
        return self.encr_decr_engine.decrypt(self.cipher, value)
