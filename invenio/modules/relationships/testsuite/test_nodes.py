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

from flask.ext.registry import (
    ImportPathRegistry, PkgResourcesDirDiscoveryRegistry, RegistryProxy
)

from invenio.base.wrappers import lazy_import
from invenio.ext.registry import ModuleAutoDiscoverySubRegistry
from invenio.testsuite import (
    InvenioTestCase, make_test_suite, nottest, run_test_suite
)

Field_parser = lazy_import('invenio.modules.jsonalchemy.parser:FieldParser')
Model_parser = lazy_import('invenio.modules.jsonalchemy.parser:ModelParser')

TEST_PACKAGE = ('invenio.modules.records.testsuite',
                'invenio.modules.relationships.testsuite')

test_registry = RegistryProxy('testsuite', ImportPathRegistry,
                              initial=TEST_PACKAGE)


def field_definitions():
    """Load field definitions."""
    return PkgResourcesDirDiscoveryRegistry(
        'fields', registry_namespace=test_registry)


def model_definitions():
    """Load model definitions."""
    return PkgResourcesDirDiscoveryRegistry(
        'models', registry_namespace=test_registry)


def function_proxy():
    """Load functions."""
    return ModuleAutoDiscoverySubRegistry(
        'functions', registry_namespace=test_registry)


class RelationshipsNodeTestCase(InvenioTestCase):

    """Test mehods of ``Node`` class."""

    @classmethod
    def setupClass(cls):
        Field_parser._field_definitions = {}
        Field_parser._legacy_field_matchings = {}
        Model_parser._model_definitions = {}

    def setUp(self):
        """TODO"""
        self._importContext()

        self.app.extensions['registry']['testsuite.fields'] = field_definitions()
        self.app.extensions['registry']['testsuite.models'] = model_definitions()
        self.app.extensions['registry']['testsuite.functions'] = function_proxy()

        self._document = self.Document.create({'title': 'Document',
                                               'description': 'Testing'})
        self._record = self.Record(master_format='marc',
                                   namespace='testsuite')
        self._record['recid'] = 1

        self.db.session.commit()

        self._record_id = self._record['_id']
        self._document_id = self._document['_id']

    def _importContext(self):
        from invenio.ext.sqlalchemy import db
        from invenio.modules.documents.api import Document
        from invenio.modules.records.api import Record
        from invenio.modules.documents.models import Document as DocumentModel
        from invenio.modules.records.models import Record as RecordModel
        from ..api import Node

        self.db = db
        self.Node = Node
        self.Document = Document
        self.Record = Record
        self.RecordModel = RecordModel
        self.DocumentModel = DocumentModel

    def tearDown(self):
        """TODO"""
        nodes = []
        nodes.extend(self.DocumentModel.query.filter_by(id=self._document_id).all())
        nodes.extend(self.RecordModel.query.filter_by(id=self._record_id).all())

        for node in nodes:
            self.db.session.delete(node)
        self.db.session.commit()

        del self.app.extensions['registry']['testsuite.fields']
        del self.app.extensions['registry']['testsuite.models']
        del self.app.extensions['registry']['testsuite.functions']

    @nottest
    def test_annotations(self):
        # FIXME: implement and test annotations.
        self.assertTrue(hasattr(self._annotation, '_edges'))

    def test_documents(self):
        self.assertTrue(hasattr(self._document, '_edges'))

    def test_records(self):
        self.assertTrue(hasattr(self._record, '_edges'))


TEST_SUITE = make_test_suite(RelationshipsNodeTestCase)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
