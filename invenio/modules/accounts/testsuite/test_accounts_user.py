# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2010, 2011, 2013, 2015 CERN.
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

"""Unit tests for the user handling library."""

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class UserTestCase(InvenioTestCase):
    """Test User class."""

    def test_note_is_converted_to_string(self):
        from invenio.modules.accounts.models import User
        u = User(email="test@test.pl", password="")
        u.note = 2
        self.assertTrue(isinstance(u.note, str))

    def test_verify_email_works_with_numbers_and_strings(self):
        from invenio.modules.accounts.models import User
        u = User(email="test@test.pl", password="")
        u.note = 2
        self.assertTrue(u.verify_email())

        u2 = User(email="test2@test2.pl", password="")
        u2.note = "2"
        self.assertTrue(u2.verify_email())


TEST_SUITE = make_test_suite(UserTestCase)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
