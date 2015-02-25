# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2010, 2011, 2013 CERN.
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

__revision__ = "$Id$"

from invenio.legacy.bibrank import downloads_indexer as bibrank_downloads_indexer
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class TestListSetOperations(InvenioTestCase):
    """Test list set operations."""

    def test_uniq(self):
        """bibrank downloads indexer - uniq function"""
        self.assertEqual([1, 2, 3], bibrank_downloads_indexer.uniq([1, 2, 3, 3, 3, 2]))

    def test_database_tuples_to_single_list(self):
        """bibrank downloads indexer - database tuples to list"""
        self.assertEqual([1, 2, 3], bibrank_downloads_indexer.database_tuples_to_single_list(((1,), (2,), (3,))))

class TestMergeDictionnaries(InvenioTestCase):
    """Test bibrank_downloads_indexer merge 2 dictionnaries"""

    def test_merge_with_old_dictionnary(self):
        """bibrank downloads indexer - merging with old dictionary"""
        self.assertEqual({1:[(2, 3)], 2:[(3, 4)], 3:[(4, 5)]}, bibrank_downloads_indexer.merge_with_old_dictionnary(\
            {3:[(4, 5)]}, {1:[(2, 3)], 2:[(3, 4)]}))
        self.assertEqual({1:[(2, 4)], 2:[(3, 4)]}, bibrank_downloads_indexer.merge_with_old_dictionnary(\
            {1:[(2, 1)]}, {1:[(2, 3)], 2:[(3, 4)]}))
        self.assertEqual({1:[(3, 3), (2, 3)], 2:[(3, 4)]}, bibrank_downloads_indexer.merge_with_old_dictionnary(\
            {1:[(2, 3)]}, {1:[(3, 3)], 2:[(3, 4)]}))
        self.assertEqual({}, bibrank_downloads_indexer.merge_with_old_dictionnary({}, {}))

TEST_SUITE = make_test_suite(TestListSetOperations,
                             TestMergeDictionnaries,)
if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
