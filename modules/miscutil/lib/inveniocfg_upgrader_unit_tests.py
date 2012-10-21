# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2009, 2010, 2011, 2012 CERN.
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

""" Test unit for the miscutil/lib/inveniocfg_upgrader module. """

import unittest

from invenio.testutils import make_test_suite, run_test_suite
from invenio.inveniocfg_upgrader import InvenioUpgrader


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


class TestInvenioUpgraderOrdering(unittest.TestCase):

    def test_normal(self):
        """
        Normal dependency graph
        """
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
        upgrades = dictify([
            TestUpgrade('1', [], 'invenio'),
            TestUpgrade('2', ['1'], 'invenio'),
            TestUpgrade('3', ['1', 'b'], 'invenio'),
            TestUpgrade('a', [], 'other'),
            TestUpgrade('b', ['a'], 'other'),
            TestUpgrade('c', ['a'], 'other'),
        ])

        m = InvenioUpgrader()
        self.assertRaises(StandardError, m.order_upgrades, upgrades)

    def test_history(self):
        """
        History
        """
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
        self.assertEqual(
            upgrades_str(m.order_upgrades(upgrades, history)),
                         "[3, 5, 6]")

        history = dictify(['3', '5'], value=1)
        m = InvenioUpgrader()
        self.assertEqual(
            upgrades_str(m.order_upgrades(upgrades, history)), "[6]")


TEST_SUITE = make_test_suite(TestInvenioUpgraderOrdering,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
