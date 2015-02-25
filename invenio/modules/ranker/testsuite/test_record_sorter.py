# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2013 CERN.
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

"""Unit tests for the ranking engine."""

__revision__ = "$Id$"

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class TestListSetOperations(InvenioTestCase):
    """Test list set operations."""

    def test_record_sorter(self):
        """bibrank record sorter - sorting records"""
        from invenio.legacy.bibrank import word_searcher as bibrank_word_searcher
        from intbitset import intbitset
        hitset = intbitset()
        hitset += (1,2,5)
        hitset2 = intbitset()
        hitset2.add(5)
        rec_termcount = {1: 1, 2: 1, 5: 1}
        (res1, res2) = bibrank_word_searcher.sort_record_relevance({1: 50, 2:30, 3:70,4:10},rec_termcount,hitset, 50,0)
        self.assertEqual(([(1, 71), (3, 100)], list(hitset2)), (res1, list(res2)))

    def test_calculate_record_relevance(self):
        """bibrank record sorter - calculating relevances"""
        from invenio.legacy.bibrank import word_searcher as bibrank_word_searcher
        from intbitset import intbitset
        hitset = intbitset()
        hitset += (1,2,5)
        self.assertEqual(({1: 7, 2: 7, 5: 5}, {1: 1, 2: 1, 5: 1}),  bibrank_word_searcher.calculate_record_relevance(("testterm", 2.0),
{"Gi":(0, 50.0), 1: (3, 4.0), 2: (4, 5.0), 5: (1, 3.5)}, hitset, {}, {}, 0, None))

TEST_SUITE = make_test_suite(TestListSetOperations,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
