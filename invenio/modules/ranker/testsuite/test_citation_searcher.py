# -*- coding: utf-8 -*-
#
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

"""Unit tests for the citation searcher."""

__revision__ = "$Id$"

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class TestCitationSearcher(InvenioTestCase):

    def setUp(self):
        # pylint: disable=C0103
        """Initialize stuff"""
        self.recid = 339705
        self.recids = [339705, 339706]
        self.rank_method_code = 'citation'

    def xtest_init_cited_by_dictionary(self):
        """bibrank citation searcher - init cited-by data"""
        # FIXME: test postponed
        #self.assert_(bibrank_citation_searcher.init_cited_by_dictionary())

    def xtest_init_reference_list_dictionary(self):
        """bibrank citation searcher - init reference data"""
        # FIXME: test postponed
        #self.assert_(bibrank_citation_searcher.init_reference_list_dictionary())

    def xtest_calculate_cited_by_list(self):
        """bibrank citation searcher - get citing relevance"""
        # FIXME: test postponed

    def xtest_calculate_co_cited_with_list(self):
        """bibrank citation searcher - get co-cited-with data"""
        # FIXME: test postponed

TEST_SUITE = make_test_suite(TestCitationSearcher,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
