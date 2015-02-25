# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""Unit tests for the storage engine."""

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


def class_factory(name):
    from invenio.modules.jsonalchemy.wrappers import SmartJson

    class DummyJson(SmartJson):
        __storagename__ = name
    return DummyJson


class TestStorageEngineConfig(InvenioTestCase):
    """Test for configuration of storage engine."""

    def test_string_config(self):
        self.app.config['DUMMY_ENGINE'] = ('invenio.modules.jsonalchemy.'
                                           'jsonext.engines.memory:'
                                           'MemoryStorage')
        DummyJson = class_factory('dummy')
        database = {1: DummyJson({'_id': 1}, master_format='json',
                                 namespace='json')}
        self.app.config['DUMMY_MEMORYSTORAGE'] = {
            'database': database
        }

        self.assertEqual(DummyJson.storage_engine.get_one(1)['_id'],
                         database[1]['_id'])

    def test_instance_config(self):
        from invenio.modules.jsonalchemy.jsonext.engines import memory
        self.app.config['DUMMY_ENGINE'] = memory.MemoryStorage
        DummyJson = class_factory('dummy')
        database = {1: DummyJson({'_id': 1}, master_format='json',
                                 namespace='json')}
        self.app.config['DUMMY_MEMORYSTORAGE'] = {
            'database': database
        }

        self.assertEqual(DummyJson.storage_engine.get_one(1)['_id'],
                         database[1]['_id'])

TEST_SUITE = make_test_suite(TestStorageEngineConfig)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
