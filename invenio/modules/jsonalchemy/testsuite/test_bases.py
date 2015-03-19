# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Unit tests for the JSONAlchemy bases."""

from datetime import datetime
from flask_registry import PkgResourcesDirDiscoveryRegistry, \
    ImportPathRegistry, RegistryProxy

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

Field_parser = lazy_import('invenio.modules.jsonalchemy.parser:FieldParser')
Model_parser = lazy_import('invenio.modules.jsonalchemy.parser:ModelParser')
guess_legacy_field_names = lazy_import(
    'invenio.modules.jsonalchemy.parser:guess_legacy_field_names')
get_producer_rules = lazy_import(
    'invenio.modules.jsonalchemy.parser:get_producer_rules')

TEST_PACKAGE = 'invenio.modules.jsonalchemy.testsuite'

test_registry = RegistryProxy('testsuite', ImportPathRegistry,
                              initial=[TEST_PACKAGE])

field_definitions = lambda: PkgResourcesDirDiscoveryRegistry(
    'fields', registry_namespace=test_registry)
model_definitions = lambda: PkgResourcesDirDiscoveryRegistry(
    'models', registry_namespace=test_registry)


def clean_field_model_definitions():
    Field_parser._field_definitions = {}
    Field_parser._legacy_field_matchings = {}
    Model_parser._model_definitions = {}


class RegistryMixin(object):

    def setUp(self):
        clean_field_model_definitions()
        self.app.extensions['registry'][
            'testsuite.fields'] = field_definitions()
        self.app.extensions['registry'][
            'testsuite.models'] = model_definitions()
        list(self.app.extensions['registry'][
            'testsuite.fields'])
        list(self.app.extensions['registry'][
            'testsuite.models'])

    def tearDown(self):
        clean_field_model_definitions()
        del self.app.extensions['registry']['testsuite.fields']
        del self.app.extensions['registry']['testsuite.models']
        del self.app.extensions['registry']['testsuite']


class TestVersionable(RegistryMixin, InvenioTestCase):

    def test_versionable_base(self):
        """Versionable - model creation"""
        from invenio.modules.jsonalchemy.jsonext.engines import memory

        self.app.config['_VERSIONABLE_ENGINE'] = memory.MemoryStorage
        from invenio.modules.jsonalchemy.wrappers import SmartJson
        from invenio.modules.jsonalchemy.reader import Reader

        class _VersionableJson(SmartJson):
            __storagename__ = '_versionable'

            @classmethod
            def create(cls, data, model='test_versionable',
                       master_format='json', **kwargs):
                document = Reader.translate(
                    data, cls, master_format=master_format,
                    model=model, namespace='testsuite', **kwargs)
                cls.storage_engine.save_one(document.dumps())
                return document

            @classmethod
            def get_one(cls, _id):
                return cls(cls.storage_engine.get_one(_id))

            def _save(self):
                try:
                    return self.__class__.storage_engine.update_one(
                        self.dumps(), id=self['_id'])
                except:
                    return self.__class__.storage_engine.save_one(
                        self.dumps(), id=self['_id'])

            def update(self):
                self['modification_date'] = datetime.now()
                return self._save()

        v0 = _VersionableJson.create({'title': 'Version 0'})
        self.assertTrue('title' in v0)
        self.assertTrue('Version 0' in v0['title'])

        v0['title'] = 'Version 1'
        v1 = v0.update()

        v_older = _VersionableJson.get_one(v1['older_version'])

        self.assertTrue('older_version' in v1)
        self.assertTrue(v_older['_id'] in v1['older_version'])
        self.assertTrue('Version 1' in v1['title'])
        self.assertTrue(v1['_id'] in v_older['newer_version'])


class TestHidden(RegistryMixin, InvenioTestCase):

    def test_dumps_hidden(self):
        from invenio.modules.jsonalchemy.wrappers import SmartJson
        from invenio.modules.jsonalchemy.reader import Reader

        data = {'title': 'Test Title'}

        document = Reader.translate(
            data, SmartJson, master_format='json',
            model='test_hidden', namespace='testsuite')

        json = document.dumps()
        self.assertTrue('title' in json)
        self.assertTrue('hidden_basic' in json)

        json = document.dumps(filter_hidden=True)
        self.assertTrue('title' in json)
        self.assertFalse('hidden_basic' in json)


TEST_SUITE = make_test_suite(TestVersionable, TestHidden)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
