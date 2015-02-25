# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2013 CERN.
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

import sys

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

bibrank_citerank_indexer = lazy_import('invenio.legacy.bibrank.citerank_indexer')
task_set_task_param = lazy_import('invenio.legacy.bibsched.bibtask:task_set_task_param')


class TestCiterankIndexer(InvenioTestCase):

    def setUp(self):
        """Initialization"""
        self.cit = {74: set([92]), 77: set([85, 86]), 78: set([91, 79]), 79: set([91]), 81: set([89, 82, 83, 87]), 18: set([96]), 84: set([88, 91, 85]), 91: set([92]), 94: set([80]), 95: set([77, 86])}
        self.dict_of_ids = {96: 14, 18: 13, 74: 0, 77: 2, 78: 5, 79: 7, 80: 18, 81: 8, 82: 10, 83: 11, 84: 15, 85: 3, 86: 4, 87: 12, 88: 16, 89: 9, 91: 6, 92: 1, 94: 17, 95: 19}
        self.ref = list([0, 2, 1, 2, 2, 0, 3, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0])
        self.dates = {0: 2001, 1: 2006, 2: 2002, 3: 2003, 4: 2003, 5: 2002, 6: 2007, 7: 2003, 8: 2002, 9: 2005, 10: 2002, 11: 2003, 12: 2003, 13: 1984, 14: 2000, 15: 2003, 16: 2003, 17: 1997, 18: 2002, 19: 1999}
        self.damping_factor = 0.85
        self.conv_threshold = 0.0001
        self.check_point = 1
        task_set_task_param('verbose', 0)

    def test_calculate_ref(self):
        """bibrank citerank indexer - calculate references"""
        self.assertEqual(self.ref, list(bibrank_citerank_indexer.construct_ref_array(self.cit, self.dict_of_ids, 20)))

    def test_calculate_ranks(self):
        """bibrank citerank indexer - calculate ranks"""
        dict_of_ranks = bibrank_citerank_indexer.run_pagerank(self.cit, self.dict_of_ids, len(self.dict_of_ids), self.ref, self.damping_factor, self.conv_threshold, self.check_point, self.dates)
        self.assertEqual({96: 0.622, 18: 1.1419839999999999, 74: 0.88200100000000003, 77: 1.142002, 78: 1.6020020000000001, 79: 0.86200299999999996, 80: 0.62200199999999994, 81: 2.712002, 82: 0.62200199999999994, 83: 0.62200299999999997, 84: 1.6520029999999999, 85: 0.62200299999999997, 86: 0.62200299999999997, 87: 0.62200299999999997, 88: 0.62200299999999997, 89: 0.62200500000000003, 91: 0.88200699999999999, 92: 0.62200599999999995, 94: 1.1419969999999999, 95: 1.8519990000000002}, dict_of_ranks)

TEST_SUITE = make_test_suite(TestCiterankIndexer,)

if __name__ == "__main__":
    try: # the citerank functions can not run if numpy is not installed
        import numpy
        run_test_suite(TEST_SUITE)
    except ImportError:
        pass
