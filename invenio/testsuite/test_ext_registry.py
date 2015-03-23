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

"""
Test unit for the miscutil/mailutils module.
"""

from invenio.ext.registry import DictModuleAutoDiscoverySubRegistry
from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite
from flask_registry import ImportPathRegistry, RegistryError


class TestDictModuleAutoDiscoverySubRegistry(InvenioTestCase):
    def test_registration(self):
        r = self.app.extensions['registry']

        r['testpkgs'] = ImportPathRegistry(
            initial=['invenio.testsuite.test_apps']
        )
        assert len(r['testpkgs']) == 1

        r['myns'] = \
            DictModuleAutoDiscoverySubRegistry(
                'last',
                keygetter=lambda k, v, new_v: k if k else v.__name__,
                app=self.app,
                registry_namespace='testpkgs'
            )
        assert len(r['myns']) == 1

        from invenio.testsuite.test_apps.last import views
        assert r['myns']['invenio.testsuite.test_apps.last.views'] == \
            views

        self.assertRaises(
            RegistryError,
            DictModuleAutoDiscoverySubRegistry,
            'last',
            app=self.app,
            registry_namespace='testpkgs'
        )

        # Register simple object
        class TestObject(object):
            pass

        r['myns'].register(TestObject)

        # Identical keys raises RegistryError
        self.assertRaises(
            RegistryError,
            r['myns'].register,
            TestObject
        )

        r['myns'].unregister('TestObject')
        assert 'TestObject' not in r['myns']

        r['myns']['mykey'] = TestObject
        assert TestObject == r['myns']['mykey']

        assert len(r['myns'].items()) == 2


TEST_SUITE = make_test_suite(TestDictModuleAutoDiscoverySubRegistry)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
