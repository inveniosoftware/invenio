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

import base64
from Crypto.Cipher import AES
import hashlib
from sqlalchemy.types import TypeDecorator, VARCHAR


class Encrypted(TypeDecorator):

    """Implement an Encrypted column type."""

    impl = VARCHAR
    BLOCK_SIZE = 16
    PADDING = '*'

    def __init__(self, key, *args, **kwargs):
        """Initialization."""
        super(Encrypted, self).__init__(*args, **kwargs)
        # produce a 32-bytes key
        secret_key = hashlib.sha256(key).digest()
        self.cipher = AES.new(secret_key)

    def _pad(self, v):
        """Pad the message to be encrypted, if needed."""
        padded = v + (self.BLOCK_SIZE - len(v) % self.BLOCK_SIZE)\
            * self.PADDING
        return padded

    def _aes_encrypt(self, v):
        """Encrypt a message."""
        encrypted = base64.b64encode(self.cipher.encrypt(self._pad(v)))
        return encrypted

    def _aes_decrypt(self, v):
        """Decrypt a message."""
        decrypted = (self.cipher.decrypt(base64.b64decode(v)).
                     decode('utf-8').rstrip(self.PADDING))
        return decrypted

    def process_bind_param(self, value, dialect):
        """Encrypt a value on the way in."""
        return self._aes_enrypt(value)

    def process_result_value(self, value, dialect):
        """Decrypt value on the way out."""
        return self._aes_decrypt(value)
