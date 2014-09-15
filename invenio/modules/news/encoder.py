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

"""Encoder for the news module."""

import base64

from Crypto.Cipher import AES

BLOCK_SIZE = 32

# the character used for padding--with a block cipher such as AES, the value
# you encrypt must be a multiple of BLOCK_SIZE in length.  This character is
# used to ensure that your value is always a multiple of BLOCK_SIZE
PADDING = '{'


def pad(s):
    """sufficiently pad the text to be encrypted."""
    return s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING


def EncodeAES(c, s):
    """encrypt (with AES) / encode (with base64) a string."""
    return base64.b64encode(c.encrypt(pad(s)))


def DecodeAES(c, e):
    """decrypt/decode a string."""
    return c.decrypt(base64.b64decode(e)).rstrip(PADDING)

cipher = AES.new('aaaaaaaaaa123456')


class EncryptClass:

    """the Encrypt class."""

    def EncodeStr(args, Arr):
        """encode a string."""
        try:
            return EncodeAES(cipher, str(Arr))
        except Exception:
            return Arr

    def DecodeStr(args, Arr):
        """decode a string."""
        try:
            return DecodeAES(cipher, str(Arr).replace(" ", "+"))
        except Exception:
            return Arr


def Encode(Arr):
    """encode function."""
    # x=EncryptClass()
    # return x.EncodeStr(Arr)
    return Arr


def Decode(Arr):
    """decode function."""
    # x=EncryptClass()
    # return x.DecodeStr(Arr)
    return Arr
