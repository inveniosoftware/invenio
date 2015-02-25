# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""Unit tests for the validator."""

import uuid
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class TestValidator(InvenioTestCase):

    def setUp(self):
        from invenio.modules.jsonalchemy.validator import Validator
        self.validator = Validator()

    def tearDown(self):
        del self.validator

    def test_objectid(self):
        """Objectid type validation"""
        self.validator._validate_type_objectid(
            '_id', 'abcde12345fabcd67890efab')
        self.assertEqual(self.validator.errors, {})
        self.validator._errors = {}
        self.validator._validate_type_objectid(
            '_id', 'abcde-12345-fabcd-67890e')
        self.assertEqual(self.validator.errors,
                         {'_id': 'must be of ObjectId type'})

    def test_uuid(self):
        """Objectid type validation"""
        _uuid = str(uuid.uuid4())
        self.validator._validate_type_uuid(
            '_id', _uuid)
        self.assertEqual(self.validator.errors, {})
        self.validator._errors = {}
        self.validator._validate_type_uuid(
            '_id', _uuid.replace('-', '_'))
        self.assertEqual(self.validator.errors,
                         {'_id': 'must be of UUID type'})


TEST_SUITE = make_test_suite(TestValidator)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
