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

"""Tests for Node class."""
from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class RelationshipsNodeTestCase(InvenioTestCase):

    """Test mehods of ``Node`` class."""

    def setUp(self):
        """TODO"""
        self._importContext()
        self._empty_record = self.Document.create({'title': 'Document 1',
                                                   'description': 'Testing 1'})
        self.db.session.commit()
        self._id = self._empty_record['_id']
        self._dummy_record = self.Document.get_document(self._id)

    def _importContext(self):
        from invenio.ext.sqlalchemy import db
        from invenio.modules.documents.api import Document
        from invenio.modules.documents.models import Document as DocumentModel
        from ..api import Node

        self.db = db
        self.Node = Node
        self.Document = Document
        self.DocumentModel = DocumentModel

    def tearDown(self):
        """TODO"""
        docs = self.DocumentModel.query.filter_by(id=self._id).all()
        for doc in docs:
            self.db.session.delete(doc)
        self.db.session.commit()

    def test_sanity(self):
        self.assertEqual(True, True)


TEST_SUITE = make_test_suite(RelationshipsNodeTestCase)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
