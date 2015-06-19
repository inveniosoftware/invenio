# -*- coding: utf-8 -*-
#
# This file is part of Invenio
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
# along with Invenio; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Test *Passlib* integration."""

from __future__ import absolute_import

from binascii import hexlify, unhexlify

from invenio.ext.passlib.hash import mysql_aes_decrypt, mysql_aes_encrypt
from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class MySQLAESEncryptTestCase(InvenioTestCase):

    """Test of extension creation."""

    def test_mysql_aes_encrypt(self):
        """Test mysql_aes_encrypt."""
        self.assertEqual(
            hexlify(mysql_aes_encrypt("test", "key")),
            "9e9ce44cd9df2b201f51947e03bccbe2"
        )
        self.assertEqual(
            hexlify(mysql_aes_encrypt(u"test", "key")),
            "9e9ce44cd9df2b201f51947e03bccbe2"
        )
        self.assertEqual(
            hexlify(mysql_aes_encrypt("test", u"key")),
            "9e9ce44cd9df2b201f51947e03bccbe2"
        )
        self.assertEqual(
            hexlify(mysql_aes_encrypt(u"test", u"key")),
            "9e9ce44cd9df2b201f51947e03bccbe2"
        )
        self.assertRaises(AssertionError, mysql_aes_encrypt, object(), "key")
        self.assertRaises(AssertionError, mysql_aes_encrypt, "val", object())

    def test_mysql_aes_decrypt(self):
        """Test mysql_aes_encrypt."""
        self.assertEqual(
            mysql_aes_decrypt(unhexlify("9e9ce44cd9df2b201f51947e03bccbe2"),
                              "key"),
            "test"
        )
        self.assertEqual(
            mysql_aes_decrypt(unhexlify(u"9e9ce44cd9df2b201f51947e03bccbe2"),
                              u"key"),
            "test"
        )
        self.assertRaises(AssertionError, mysql_aes_decrypt, object(), "key")
        self.assertRaises(AssertionError, mysql_aes_decrypt, "val", object())


class PasslibTestCase(InvenioTestCase):

    """Test passlib extensions."""

    config = {
        'PASSLIB_SCHEMES': ['sha512_crypt', 'invenio_aes_encrypted_email'],
        'PASSLIB_DEPRECATED_SCHEMES': ['invenio_aes_encrypted_email']
    }

    def test_context(self):
        """Test passlib password context."""
        ctx = self.app.extensions['passlib']
        hashval = ctx.encrypt("test")
        assert hashval != "test"
        assert ctx.verify("test", hashval)
        assert not ctx.needs_update(hashval)
        assert ctx.encrypt("test") != ctx.encrypt("test")

    def test_invenio_aes_encrypted_email(self):
        """Test legacy encryption."""
        ctx = self.app.extensions['passlib']
        hashval = ctx.encrypt(
            "mypassword",
            scheme="invenio_aes_encrypted_email",
            user="info@invenio-software.org",
        )
        assert ctx.verify("mypassword", hashval,
                          scheme="invenio_aes_encrypted_email",
                          user="info@invenio-software.org", )
        assert ctx.needs_update(hashval)

    def test_unicode_regression(self):
        """Test legacy encryption."""
        ctx = self.app.extensions['passlib']
        hashval = ctx.encrypt(
            u"mypassword",
            scheme="invenio_aes_encrypted_email",
            user=u"info@invenio-software.org",
        )
        assert ctx.verify(u"mypassword", hashval,
                          scheme="invenio_aes_encrypted_email",
                          user=u"info@invenio-software.org", )
        assert ctx.needs_update(hashval)


TEST_SUITE = make_test_suite(
    MySQLAESEncryptTestCase,
    PasslibTestCase
)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
