# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2015 CERN.
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

"""Tests for Relationship model."""
from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class RelationshipModelTestCase(InvenioTestCase):

    """Test additional features of Relationship model."""

    def setUp(self):
        """Import modules and prepare a dummy record."""
        self._import_context()
        self._dummy_record = self.Document.create({'title': 'Document 1',
                                                   'description': 'Testing 1'})
        self._id = self._dummy_record['_id']
        self.db.session.commit()

    def tearDown(self):
        docs = self.DocumentModel.query.filter_by(id=self._id).all()
        for doc in docs:
            self.db.session.delete(doc)
        self.db.session.commit()

    def _import_context(self):
        from uuid import UUID
        from invenio.ext.sqlalchemy import db
        from invenio.modules.documents.api import Document
        from invenio.modules.documents.models import Document as DocumentModel
        from ..models import Relationship
        self.db = db
        self.Document = Document
        self.DocumentModel = DocumentModel
        self.Relationship = Relationship
        self.UUID = UUID

    def test_correct_relationship(self):
        """Check a reflexive relationship."""
        rec = self._dummy_record
        relationship = self.Relationship(rec, 'default', rec)
        self.assertEqual(relationship.uuid.__class__, self.UUID)
        self.assertEqual(relationship.link_type, 'default')


TEST_SUITE = make_test_suite(RelationshipModelTestCase)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
