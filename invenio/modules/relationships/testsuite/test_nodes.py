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


class RelationshipNodeTestCase(InvenioTestCase):

    """Test mehods of ``Node`` class."""

    def setUp(self):
        """Import modules and create dummy record and a dummy relationship."""
        self._importContext()
        self._empty_record = self.Document.create({'title': 'Document 1',
                                                   'description': 'Testing 1'})
        self._relationship = self.Relationship(self._empty_record, 'default',
                                               self._empty_record)
        self._relationship.save()
        self.db.session.commit()
        self._id = self._empty_record['_id']
        self._dummy_record = self.Document.get_document(self._id)

    def _importContext(self):
        from invenio.ext.sqlalchemy import db
        from invenio.modules.documents.api import Document
        from invenio.modules.documents.models import Document as DocumentModel
        from ..api import Node, Relationship
        self.db = db
        self.Node = Node
        self.Document = Document
        self.DocumentModel = DocumentModel
        self.Relationship = Relationship

    def tearDown(self):
        """Delete dummy record and dummy relationship."""
        self.db.session.delete(self._relationship)
        docs = self.DocumentModel.query.filter_by(id=self._id).all()
        for doc in docs:
            self.db.session.delete(doc)
        self.db.session.commit()

    def test_get_sources(self):
        """Check reflexiveness of the dummy relationhip.

        Test the edge coming out.
        """
        self.assertEqual(self._dummy_record['_id'],
                         self._dummy_record.neighbours(outwards=False
                                                       ).pop()['_id'])

    def test_get_destinations(self):
        """Check reflexiveness of the dummy relationship.

        Test the edge coming in.
        """
        self.assertEqual(self._dummy_record['_id'],
                         self._dummy_record.neighbours(inwards=False
                                                       ).pop()['_id'])

    def test_neighbours(self):
        """Check if every node is returned only once."""
        neighbours = self._dummy_record.neighbours()
        self.assertEqual(len(neighbours), 1)
        self.assertEqual(self._dummy_record['_id'], neighbours.pop()['_id'])

    def test_edges(self):
        """Check the difference between both values of ``loops_doubled``."""
        self.assertEqual(self._dummy_record.degree(), 2)
        self.assertEqual(len(self._dummy_record.edges(loops_doubled=False)), 1)


TEST_SUITE = make_test_suite(RelationshipNodeTestCase)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
