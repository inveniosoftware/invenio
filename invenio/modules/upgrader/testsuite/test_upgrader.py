# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013 CERN.
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

""" Test unit for the miscutil/lib/inveniocfg_upgrader module. """


from datetime import date
import os
import os.path
import shutil
import sys
import tempfile

import six

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


def dictify(ls, value=None):
    if value is not None:
        return dict([(x, value) for x in ls])
    else:
        return dict([(x['id'], x) for x in ls])


def upgrades_str(ls):
    # Helper to create a string out of a list of upgrades
    class Xcls(object):

        def __init__(self, id_val):
            self.id = id_val

        def __repr__(self):
            return str(self.id)
    return str(map(lambda x: Xcls(x['id']), ls))


class TestUpgrade(dict):

    def __init__(self, node_id, depends_on, repository):
        self['id'] = node_id
        self['depends_on'] = depends_on
        self['repository'] = repository
        self['do_upgrade'] = lambda: str(node_id)


class TestInvenioUpgraderOrdering(InvenioTestCase):

    def test_normal(self):
        """
        Normal dependency graph
        """
        from invenio.modules.upgrader.engine import InvenioUpgrader
        upgrades = dictify([
            TestUpgrade('1', [], 'invenio'),
            TestUpgrade('2', ['1'], 'invenio'),
            TestUpgrade('3', ['1'], 'invenio'),
            TestUpgrade('4', ['2'], 'invenio'),
            TestUpgrade('5', ['3', '4'], 'invenio'),
            TestUpgrade('6', ['5', ], 'invenio'),
        ])

        m = InvenioUpgrader()
        self.assertEqual(upgrades_str(m.order_upgrades(upgrades)),
                         "[1, 2, 4, 3, 5, 6]")

    def test_two_graphs(self):
        """
        Two independent graphs
        """
        from invenio.modules.upgrader.engine import InvenioUpgrader
        upgrades = dictify([
            TestUpgrade('1', [], 'invenio'),
            TestUpgrade('2', ['1'], 'invenio'),
            TestUpgrade('3', ['1'], 'invenio'),

            TestUpgrade('a', [], 'other'),
            TestUpgrade('b', ['a'], 'other'),
            TestUpgrade('c', ['a'], 'other'),

            TestUpgrade('4', ['2'], 'invenio'),
            TestUpgrade('5', ['3', '4'], 'invenio'),
            TestUpgrade('6', ['5', ], 'invenio'),

            TestUpgrade('d', ['b'], 'other'),
            TestUpgrade('e', ['c', 'd'], 'other'),
            TestUpgrade('f', ['e', ], 'other'),
        ])

        m = InvenioUpgrader()
        self.assertEqual(upgrades_str(m.order_upgrades(upgrades)),
                         "[1, 2, 4, 3, 5, 6, a, b, d, c, e, f]")

    def test_cycle(self):
        """
        Cycle 2, 4, 3.
        """
        from invenio.modules.upgrader.engine import InvenioUpgrader
        upgrades = dictify([
            TestUpgrade('1', [], 'invenio'),
            TestUpgrade('2', ['1', '3'], 'invenio'),
            TestUpgrade('3', ['1', '4'], 'invenio'),
            TestUpgrade('4', ['2'], 'invenio'),
            TestUpgrade('5', ['3', '4'], 'invenio'),
            TestUpgrade('6', ['5', ], 'invenio'),
        ])

        m = InvenioUpgrader()
        self.assertRaises(StandardError, m.order_upgrades, upgrades)

    def test_missing_dependency(self):
        """
        Missing dependency 0
        """
        from invenio.modules.upgrader.engine import InvenioUpgrader
        upgrades = dictify([
            TestUpgrade('1', [], 'invenio'),
            TestUpgrade('2', ['1'], 'invenio'),
            TestUpgrade('3', ['1', '0'], 'invenio'),
        ])

        m = InvenioUpgrader()
        self.assertRaises(StandardError, m.order_upgrades, upgrades)

    def test_cross_graph_dependency(self):
        """
        Missing dependency 0
        """
        from invenio.modules.upgrader.engine import InvenioUpgrader
        upgrades = dictify([
            TestUpgrade('1', [], 'invenio'),
            TestUpgrade('2', ['1'], 'invenio'),
            TestUpgrade('3', ['1', 'b'], 'invenio'),
            TestUpgrade('a', [], 'other'),
            TestUpgrade('b', ['a'], 'other'),
            TestUpgrade('c', ['2'], 'other'),
        ])

        m = InvenioUpgrader()
        #self.assertRaises(StandardError, m.order_upgrades, upgrades)
        self.assertEqual(upgrades_str(m.order_upgrades(upgrades)),
                         "[1, 2, c, a, b, 3]")

    def test_history(self):
        """
        History
        """
        from invenio.modules.upgrader.engine import InvenioUpgrader
        upgrades = dictify([
            TestUpgrade('1', [], 'invenio'),
            TestUpgrade('2', ['1'], 'invenio'),
            TestUpgrade('3', ['1'], 'invenio'),
            TestUpgrade('4', ['2'], 'invenio'),
            TestUpgrade('5', ['3', '4'], 'invenio'),
            TestUpgrade('6', ['5', ], 'invenio'),
        ])

        history = dictify(['1', '2', '4'], value=1)
        m = InvenioUpgrader()
        self.assertEqual(upgrades_str(m.order_upgrades(upgrades, history)),
                         "[3, 5, 6]")

        history = dictify(['3', '5'], value=1)
        m = InvenioUpgrader()
        self.assertEqual(
            upgrades_str(m.order_upgrades(upgrades, history)), "[6]")


class TestInvenioUpgraderRecipe(InvenioTestCase):
    def setUp(self):
        """
        Setup a test python package, to test upgrade recipe creation.
        """
        self.tmpdir = tempfile.mkdtemp()
        self.pkg_path = os.path.join(self.tmpdir, 'invenio_upgrader_test')
        os.makedirs(self.pkg_path)
        open(os.path.join(self.pkg_path, '__init__.py'), 'a').close()
        self.pkg_path_mymod = os.path.join(
            self.tmpdir, 'invenio_upgrader_test/mymod'
        )
        os.makedirs(self.pkg_path_mymod)

        open(os.path.join(self.pkg_path, '__init__.py'), 'a').close()
        open(os.path.join(self.pkg_path_mymod, '__init__.py'), 'a').close()

        sys.path.append(self.tmpdir)
        import invenio_upgrader_test
        import invenio_upgrader_test.mymod

    def tearDown(self):
        """ Remove test package again """
        sys.path.remove(self.tmpdir)
        keys = []
        for m in sys.modules:
            if m.startswith('invenio_upgrader_test'):
                keys.append(m)
        for k in keys:
            del sys.modules[k]

        try:
            import invenio_upgrader_test
            raise AssertionError("Test package not removed from sys.path")
        except ImportError:
            pass

        shutil.rmtree(self.tmpdir)

    def test_create(self):
        """ Test creation of upgrades """
        from invenio.modules.upgrader.commands import \
            cmd_upgrade_create_standard_recipe

        cmd_upgrade_create_standard_recipe(
            'invenio_upgrader_test.mymod',
            depends_on=['test1', 'test2']
        )

        # Test if upgrade can be imported
        expexted_name = "mymod_%s_rename_me" % \
            date.today().strftime("%Y_%m_%d")

        import invenio_upgrader_test.mymod.upgrades
        upgrade = getattr(
            __import__(
                'invenio_upgrader_test.mymod.upgrades',
                globals(), locals(), [expexted_name], -1
            ),
            expexted_name
        )
        # Test API of created upgrade recipe
        assert upgrade.depends_on == ['test1', 'test2']
        assert upgrade.estimate() == 1
        assert isinstance(upgrade.info(), six.string_types)
        upgrade.pre_upgrade()
        upgrade.do_upgrade()
        upgrade.post_upgrade()

    def test_create_load_engine(self):
        """ Test creation and loading of upgrades with engine """
        from invenio.modules.upgrader.commands import \
            cmd_upgrade_create_standard_recipe

        cmd_upgrade_create_standard_recipe(
            'invenio_upgrader_test',
            depends_on=[]
        )

        expexted_name = "invenio_upgrader_test_%s_rename_me" % \
            date.today().strftime("%Y_%m_%d")

        # Test if upgrade can be found from the Upgrade
        from invenio.modules.upgrader.engine import InvenioUpgrader
        eng = InvenioUpgrader(packages=['invenio_upgrader_test'])
        upgrades = eng.get_upgrades(remove_applied=False)
        assert len(upgrades) == 1
        assert upgrades[0]['id'] == expexted_name
        assert upgrades[0]['repository'] == 'invenio_upgrader_test'

    def test_double_create(self):
        """ Test creation of upgrades """
        from invenio.modules.upgrader.commands import \
            cmd_upgrade_create_standard_recipe

        cmd_upgrade_create_standard_recipe('invenio_upgrader_test')
        # Second call fails since module already exists, and we didn't
        # rename it yet.
        self.assertRaises(
            SystemExit,
            cmd_upgrade_create_standard_recipe,
            'invenio_upgrader_test',
        )

    def test_create_with_module(self):
        from invenio.modules.upgrader.commands import \
            cmd_upgrade_create_standard_recipe

        # Module instead of package
        self.assertRaises(
            SystemExit,
            cmd_upgrade_create_standard_recipe,
            'invenio.modules.upgrader.engine'
        )

    def test_invalid_path(self):
        """ Test creation of upgrades """
        from invenio.modules.upgrader.commands import \
            cmd_upgrade_create_standard_recipe

        self.assertRaises(
            SystemExit,
            cmd_upgrade_create_standard_recipe,
            'invenio_upgrader_test',
            output_path=os.path.join(self.tmpdir, 'this_does_not_exists')
        )

    def test_create_release(self):
        """ Test creation of upgrades """
        from invenio.modules.upgrader.engine import InvenioUpgrader
        from invenio.modules.upgrader.commands import \
            cmd_upgrade_create_standard_recipe, \
            cmd_upgrade_create_release_recipe

        engine = InvenioUpgrader(packages=[
            'invenio_upgrader_test', 'invenio_upgrader_test.mymod'])

        cmd_upgrade_create_standard_recipe(
            'invenio_upgrader_test', depends_on=[]
        )
        cmd_upgrade_create_standard_recipe(
            'invenio_upgrader_test.mymod', depends_on=[]
        )

        cmd_upgrade_create_release_recipe(
            'invenio_upgrader_test', repository='invenio', upgrader=engine
        )

        # Find all endpoints in all repositories
        upgrades = engine.get_upgrades(remove_applied=False)
        for u in upgrades:
            if u['id'] == 'invenio_release_x_y_z':
                assert len(u['depends_on']) == 2


TEST_SUITE = make_test_suite(
    TestInvenioUpgraderOrdering,
    TestInvenioUpgraderRecipe,
)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
