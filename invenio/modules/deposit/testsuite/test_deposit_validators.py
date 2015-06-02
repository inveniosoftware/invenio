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

"""Unit tests for deposit module validators."""

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite

from wtforms.validators import StopValidation, ValidationError


class Field(object):

    def __init__(self, old_doi, new_doi):
        self.object_data = old_doi
        self.data = new_doi


class Form(object):
    pass


LOCAL_DOI_PREFIX = "10.5072"
REMOTE_DOI_PREFIX = "10.7777"


class MintedDOIValidatorTest(InvenioTestCase):
    """Test MitedDOIValidator."""

    def test_doi_new(self):
        from invenio.modules.deposit.validation_utils import MintedDOIValidator

        validator = MintedDOIValidator()
        field = Field("", LOCAL_DOI_PREFIX + "/test.77777")
        field2 = Field("", REMOTE_DOI_PREFIX + "/test.77777")
        form = Form()

        with self.assertRaises(StopValidation):
            validator(form, field)
        with self.assertRaises(StopValidation):
            validator(form, field2)

    def test_matching_doi(self):
        from invenio.modules.deposit.validation_utils import MintedDOIValidator

        validator = MintedDOIValidator()
        field = Field(
            LOCAL_DOI_PREFIX + "/test.77777",
            LOCAL_DOI_PREFIX + "/test.77777")
        field2 = Field(
            REMOTE_DOI_PREFIX + "/test.77777",
            REMOTE_DOI_PREFIX + "/test.77777")
        form = Form()

        with self.assertRaises(StopValidation):
            validator(form, field)
        with self.assertRaises(StopValidation):
            validator(form, field2)

    def test__different_doi_(self):
        from invenio.modules.deposit.validation_utils import MintedDOIValidator

        validator = MintedDOIValidator()
        field = Field(
            LOCAL_DOI_PREFIX + "/test.12345",
            LOCAL_DOI_PREFIX + "/test.77777")
        field2 = Field(
            REMOTE_DOI_PREFIX + "/test.12345",
            REMOTE_DOI_PREFIX + "/test.77777")
        form = Form()

        with self.assertRaises(ValidationError):
            validator(form, field)
        with self.assertRaises(ValidationError):
            validator(form, field2)


TEST_SUITE = make_test_suite(MintedDOIValidatorTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
