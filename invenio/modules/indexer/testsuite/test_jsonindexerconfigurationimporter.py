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

"""Test module importer from json for indexerext configuration."""

from invenio.base.wrappers import lazy_import
from invenio.testsuite import InvenioTestCase

db = lazy_import('invenio.ext.sqlalchemy.db')


class TestJsonIndexerConfigurationImporter(InvenioTestCase):

    """Test JsonIndexerConfigurationImporter class."""

    def setUp(self):
        """Load a json example."""
        from invenio.modules.knowledge.models import KnwKB

        self.kb_1 = KnwKB(name="testkb")
        self.kb_2 = KnwKB(name="testkb2")

        try:
            db.session.add(self.kb_1)
            db.session.add(self.kb_2)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        self.example1 = {
            "indices": {
                "index_title": {
                    "description": "Test indexing title",
                    "stemming_language": "it",
                    "synonym_kbrs": {
                        "knwkb": self.kb_1.name,
                        "type": "exact",
                    },
                    "pre_index_actions": [
                        "remove_stopwords",
                    ],
                    "field": "title",
                    "native": {
                        "tokenizer": "BibIndexAuthorCountTokenizer"
                    }
                },
                "index_author": {
                    "description": "Test indexing author",
                    "stemming_language": "it",
                    "synonym_kbrs": {
                        "knwkb": self.kb_2.name,
                        "type": "exact",
                    },
                    "pre_index_actions": [
                        "remove_stopwords",
                    ],
                    "field": "title",
                    "elasticsearch": {
                        "analyzer": "myanalyzer"
                    }
                },
                "index_empty": {
                },
            },
            "virtual_indices": {
                "virtual_index_all": {
                    "description": "Test virtual indexing author and title",
                    "indices": ["index_title", "index_author"],
                    "namespace": "records"
                },
                "virtual_index_title": {
                    "description": "Test virtual indexing title",
                    "indices": ["index_title"],
                    "namespace": "documents"
                },
                "virtual_index_author": {
                    "description": "Test virtual indexing author",
                    "indices": ["index_author"],
                    "namespace": "records"
                },
            }
        }

    def tearDown(self):
        """Run after every test."""
        # remove kb
        from invenio.modules.knowledge.models import KnwKB

        db.session.delete(
            KnwKB.query.filter_by(id=self.kb_1.id).one())
        db.session.delete(
            KnwKB.query.filter_by(id=self.kb_2.id).one())

        db.session.commit()

    def test_loading_elasticsearch_index(self):
        """Test if load elastic search index."""
        import json
        from ..indexerext.config import ElasticSearchIndex, \
            ElasticSearchIndexFactory
        from ..indexerext.importer.json_importer import \
            JsonIndexerConfigurationImporter

        importer = JsonIndexerConfigurationImporter(
            json_text=json.dumps(self.example1),
            factory=ElasticSearchIndexFactory()
        )
        config = importer.load()

        for virtual_index in config.virtual_indices:
            for index in virtual_index.indices.itervalues():
                i = next((i for (name, i)
                          in self.example1['indices'].iteritems()
                          if name == index.name), None)
                assert type(index) == ElasticSearchIndex
                if 'elasticsearch' in i and 'analyzer' in i['elasticsearch']:
                    assert index.analyzer == i['elasticsearch']['analyzer']

    def test_loading_native_index(self):
        """Test if load native index."""
        import json
        from ..indexerext.config import NativeIndex, NativeIndexFactory
        from ..indexerext.importer.json_importer import \
            JsonIndexerConfigurationImporter

        importer = JsonIndexerConfigurationImporter(
            json_text=json.dumps(self.example1),
            factory=NativeIndexFactory()
        )
        config = importer.load()

        for virtual_index in config.virtual_indices:
            for index in virtual_index.indices.itervalues():
                i = next((i for (name, i)
                          in self.example1['indices'].iteritems()
                          if name == index.name), None)
                assert type(index) == NativeIndex
                if 'native' in i and 'tokenizer' in i['native']:
                    assert index.tokenizer.__class__.__name__ \
                        == i['native']['tokenizer']

    def test_loading(self):
        """Test loading of json text."""
        import json
        from ..indexerext.importer.json_importer import \
            JsonIndexerConfigurationImporter

        importer = JsonIndexerConfigurationImporter(
            json_text=json.dumps(self.example1))
        config = importer.load()

        assert len(config.virtual_indices) == 3

        for (name, virtual_index) \
                in self.example1['virtual_indices'].iteritems():
            vi = next(
                (vi for vi in config.virtual_indices if vi.name == name), None)
            assert vi is not None
            assert vi.description == virtual_index['description']
            assert vi.namespace == virtual_index['namespace']
            # check indices
            assert len(self.example1['virtual_indices'][vi.name]['indices']) \
                == len(vi.indices)
            for name in virtual_index['indices']:
                index = next(
                    (i for (n, i) in self.example1['indices'].iteritems()
                     if n == name), None)
                i = next(
                    (i for i in vi.indices.itervalues()
                     if i.name == name), None)
                assert i is not None
                assert index['description'] == i.description
                assert i.stemming_language == index['stemming_language']
                assert i.field.code == index['field']
                for action in i.pre_index_actions:
                    assert action in index['pre_index_actions']
                    assert i.synonym_kbrs['knwkb'].name == index[
                        'synonym_kbrs']['knwkb']
                    assert i.synonym_kbrs['type'] == index[
                        'synonym_kbrs']['type']
