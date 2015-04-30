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

"""Test for document access restrictions."""

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class DocumentRestrictionsTest(InvenioTestCase):

    """Test document access restrictions."""

    def setUp(self):
        """Run before the test."""
        from invenio.modules.documents.api import Document
        self.document = Document.create({'title': 'Test restrictions'})

    def tearDown(self):
        """Run after the tests."""
        self.document = None

    def test_documet_access_open(self):
        """Test the document if it's open to everyone by default."""
        self.assertEqual(
            self.document.is_authorized()[0],
            0
        )

    def test_document_no_access_for_specific_user(self):
        """The the document access only for specific user."""
        self.document['restriction']['email'] = "fake@cern.ch"
        authorize = self.document.is_authorized(
            user_info=dict(email='happy@cern.ch', uid=2222)
        )
        self.assertEqual(
            authorize[0],
            1
        )

    def test_document_has_access_for_specific_user(self):
        """The the document access only for specific user."""
        self.document['restriction']['email'] = "happy@cern.ch"
        authorize = self.document.is_authorized(
            user_info=dict(email='happy@cern.ch', uid=2222)
        )
        self.assertEqual(
            authorize[0],
            0
        )

TEST_SUITE = make_test_suite(DocumentRestrictionsTest,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
