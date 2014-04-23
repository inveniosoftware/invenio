# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2014 CERN.
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

"""Unit tests for the search engine."""

__revision__ = \
    "$Id$"

from invenio.testutils import InvenioTestCase, make_test_suite, \
    run_test_suite, nottest

from invenio.bibauthorid_cluster_set import ClusterSet
from invenio.bibauthorid_bib_matrix import Bib_matrix


class Test_Bib_matrix(InvenioTestCase):

    def setUp(self):
        """
        Set up an empty bibmatrix and one filled with ten clusters of 10 elements each.
        """
        self.bm = Bib_matrix('testname', storage_dir_override='/tmp/')
        self.css = ClusterSet()
        self.css.clusters = [ClusterSet.Cluster(range(i * 10, i * 10 + 10)) for i in range(10)]
        self.css.update_bibs()
        self.bmcs0 = Bib_matrix('testname2', self.css, storage_dir_override='/tmp/')

    def tearDown(self):
        self.bm.destroy()
        self.bmcs0.destroy()

    def test_resolve_entry_simmetry(self):
        '''
        Bib matrix stores a triangular matrix. Entries should be symmetric.
        '''
        for j in range(100):
            for k in range(100):
                self.assertTrue(self.bmcs0._resolve_entry((j, k)) == self.bmcs0._resolve_entry((k, j)))

    def test_resolve_entry_unicity(self):
        '''
        resolve_entry should produce unuque indexes for any couple of values
        '''
        ntests = 30
        testvalues = set((i, j) for i in range(ntests) for j in range(ntests))
        for k in range(ntests):
            for z in range(ntests):
                tvalues = testvalues - set([(k, z)]) - set([(z, k)])
                val = self.bmcs0._resolve_entry((k, z))
                allvalues = set(self.bmcs0._resolve_entry(v) for v in tvalues)
                self.assertFalse(val in allvalues, str(val) + ' is in, from ' + str((k, z)))

    def test_matrix_content(self):
        '''
        The matrix should be simmetric, and values should be preserved
        '''
        for i in range(100):
            for j in range(i + 1):
                self.bmcs0[i, j] = (i, j)

        for i in range(100):
            for j in range(i + 1, 100):
                val = self.bmcs0[i, j]
                if i < j:
                    k, z = j, i
                else:
                    k, z = i, j
                self.assertTrue(val[0] == k)
                self.assertTrue(val[1] == z)

    def test_create_empty_matrix(self):
        """
        All elements should be None
        """
        for i in range(9, 10):
            for j in range(i * 10, i * 10 + 10):
                for k in range(i * 10, i * 10 + 10):
                        self.assertTrue(self.bmcs0[(j, k)] is None)

    @nottest
    def FIXME_1678_test_save_matrix(self):
        '''
        Matrix should save, be loadable, and stay equal to a newly loaded one on the same files
        '''
        self.bmcs0.store()
        loaded = Bib_matrix('testname2', storage_dir_override='/tmp/')
        self.assertTrue(loaded.load())
        bmcs0 = self.bmcs0
        for i in range(100):
            for j in range(100):
                self.assertTrue(bmcs0[i, j] == loaded[i, j])

    def test_duplicate_existing(self):
        self.bmcs0.store()
        self.bm.duplicate_existing('testname2', 'testnameduplicate')
        self.assertTrue(self.bmcs0.load())
        self.assertTrue(self.bm.load())
        bmcs0 = self.bmcs0
        bm = self.bm
        for i in range(100):
            for j in range(100):
                self.assertTrue(bmcs0[i, j] == bm[i, j])

    def test_special_items(self):
        self.bmcs0[0, 0] = '+'
        self.bmcs0[0, 1] = '-'
        self.bmcs0[0, 2] = None
        self.assertTrue(self.bmcs0[0, 0] == '+')
        self.assertTrue(self.bmcs0[0, 1] == '-')
        self.assertTrue(self.bmcs0[0, 2] is None)

    def test_getitem_numeric(self):
        self.bmcs0[0, 0] = '+'
        self.bmcs0[0, 1] = '-'
        self.bmcs0[0, 2] = None
        self.assertTrue(self.bmcs0.getitem_numeric([0, 0])[0] == -2)
        self.assertTrue(self.bmcs0.getitem_numeric([0, 1])[0] == -1)
        self.assertTrue(self.bmcs0.getitem_numeric([0, 2])[0] == -3)


TEST_SUITE = make_test_suite(Test_Bib_matrix)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
