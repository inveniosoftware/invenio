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

"""Tests for Edge class."""

from invenio.testsuite import (
    InvenioTestCase, make_test_suite, run_test_suite
)

class RelationshipsEdgeTestCase(InvenioTestCase):

    """Test mehods of ``Edge`` class."""

    def setUp(self):
        """TODO"""
        self._importContext()

        self._source = self.Document.create({'title': 'Document',
                                             'description': 'Source'})
        self._target = self.Document.create({'title': 'Document',
                                             'description': 'Target'})
        self._relationship = self.Edge(self._source, 'link_type',
                                       'attributes', self._target)
        self._relationship.save()

        self.db.session.commit()

        self._source_id = self._source['_id']
        self._target_id = self._target['_id']
        self._relationship_uuid = self._relationship.get_uuid()

    def _importContext(self):
        from invenio.ext.sqlalchemy import db
        from invenio.modules.documents.api import Document
        from invenio.modules.documents.models import Document as DocumentModel
        from ..api import Edge, Node

        self.db = db
        self.Edge = Edge
        self.Node = Node
        self.Document = Document
        self.DocumentModel = DocumentModel

    def tearDown(self):
        """TODO"""
        nodes = []
        nodes.extend(self.DocumentModel.query.filter_by(id=self._source_id).all())
        nodes.extend(self.DocumentModel.query.filter_by(id=self._target_id).all())

        edges = []
        edges.extend(self.Edge.query.filter_by(uuid=self._relationship_uuid).all())

        for node in nodes:
            self.db.session.delete(node)

        for edge in edges:
            self.db.session.delete(edge)

        self.db.session.commit()

    def test_in_edges(self):
        in_edges = self._target.in_edges()

        self.assertTrue(self._relationship in in_edges)

    def test_in_degree(self):
        self.assertEqual(self._target.in_degree(), 1)

    def test_out_edges(self):
        out_edges = self._source.out_edges()

        self.assertTrue(self._relationship in out_edges)

    def test_out_degree(self):
        self.assertEqual(self._source.out_degree(), 1)

    def test_predecessors(self):
        predecessors = self._target.predecessors()

        self.assertEqual(len(predecessors), 1)

    def test_successors(self):
        successors = self._source.successors()

        self.assertEqual(len(successors), 1)


TEST_SUITE = make_test_suite(RelationshipsEdgeTestCase)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
