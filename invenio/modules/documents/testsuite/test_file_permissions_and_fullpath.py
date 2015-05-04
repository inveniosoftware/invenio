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

"""Test for document and legacy bibdocs access restrictions."""

import os
import shutil
import tempfile

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class DocumentAndLegacyRestrictionsTest(InvenioTestCase):

    """Test document access restrictions."""

    def setUp(self):
        """Run before the test."""
        from invenio.modules.documents.api import Document
        self.document = Document.create({'title': 'J.A.R.V.I.S'})
        self.path = tempfile.mkdtemp()

    def tearDown(self):
        """Run after the tests."""
        self.document = None
        shutil.rmtree(self.path)

    def test_legacy_syntax(self):
        """Test legacy syntax."""
        from invenio.modules.documents.utils import _parse_legacy_syntax
        uuid_1 = 'recid:22'
        uuid_2 = 'recid:22-filename.jpg'

        check_uuid_1 = _parse_legacy_syntax(uuid_1)
        check_uuid_2 = _parse_legacy_syntax(uuid_2)
        answer_uuid_1 = '22', None
        answer_uuid_2 = '22', 'filename.jpg'

        self.assertEqual(
            check_uuid_1,
            answer_uuid_1
        )
        self.assertEqual(
            check_uuid_2,
            answer_uuid_2
        )

    def test_not_found_error(self):
        """Test when the file doesn't exists."""
        from werkzeug.exceptions import NotFound
        from invenio.modules.documents.utils import identifier_to_path
        self.assertRaises(
            NotFound,
            identifier_to_path,
            'this_is_not_a_uuid'
        )
        self.assertRaises(
            NotFound,
            identifier_to_path,
            self.document.get('uuid')
        )

    def test_forbidden_error(self):
        """Test when the file is restricted."""
        from werkzeug.exceptions import Forbidden
        from invenio.modules.documents.utils import (
            identifier_to_path_and_permissions
        )
        content = 'S.H.I.E.L.D.'
        source, sourcepath = tempfile.mkstemp()

        with open(sourcepath, 'w+') as f:
            f.write(content)

        uri = os.path.join(self.path, 'classified.txt')
        self.document.setcontents(sourcepath, uri)
        self.document['restriction']['email'] = 'happy@cern.ch'
        test_document = self.document.update()
        self.assertRaises(
            Forbidden,
            identifier_to_path_and_permissions,
            test_document.get('uuid')
        )
        shutil.rmtree(sourcepath, ignore_errors=True)

TEST_SUITE = make_test_suite(DocumentAndLegacyRestrictionsTest,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
