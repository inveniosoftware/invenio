# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013 CERN.
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

"""Unit tests for the search engine."""

__revision__ = \
    "$Id$"

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

search_engine = lazy_import('invenio.legacy.search_engine')


class TestWashQueryParameters(InvenioTestCase):
    """Test for washing of search query parameters."""

    def test_wash_pattern(self):
        """search engine - washing of query patterns"""
        self.assertEqual("Ellis, J", search_engine.wash_pattern('Ellis, J'))
        #self.assertEqual("ell", search_engine.wash_pattern('ell*'))

    def test_wash_dates_from_tuples(self):
        """search engine - washing of date arguments from (year,month,day) tuples"""
        self.assertEqual(search_engine.wash_dates(d1y=1980, d1m=1, d1d=28, d2y=2003, d2m=2, d2d=3),
                         ('1980-01-28 00:00:00', '2003-02-03 00:00:00'))
        self.assertEqual(search_engine.wash_dates(d1y=1980, d1m=0, d1d=28, d2y=2003, d2m=2, d2d=0),
                         ('1980-01-28 00:00:00', '2003-02-31 00:00:00'))

    def test_wash_dates_from_datetexts(self):
        """search engine - washing of date arguments from datetext strings"""
        self.assertEqual(search_engine.wash_dates(d1="1980-01-28 01:02:03", d2="1980-01-29 12:34:56"),
                         ('1980-01-28 01:02:03', '1980-01-29 12:34:56'))
        self.assertEqual(search_engine.wash_dates(d1="1980-01-28 01:02:03"),
                         ('1980-01-28 01:02:03', '9999-12-31 00:00:00'))
        self.assertEqual(search_engine.wash_dates(d2="1980-01-29 12:34:56"),
                         ('0000-01-01 00:00:00', '1980-01-29 12:34:56'))

    def test_wash_dates_from_both(self):
        """search engine - washing of date arguments from both datetext strings and (year,month,day) tuples"""
        # datetext mode takes precedence, d1* should be ignored
        self.assertEqual(search_engine.wash_dates(d1="1980-01-28 01:02:03", d1y=1980, d1m=1, d1d=28),
                         ('1980-01-28 01:02:03', '9999-12-31 00:00:00'))
        # datetext mode takes precedence, d2 missing, d2* should be ignored
        self.assertEqual(search_engine.wash_dates(d1="1980-01-28 01:02:03", d2y=2003, d2m=2, d2d=3),
                         ('1980-01-28 01:02:03', '2003-02-03 00:00:00'))


class TestSearchUnitFunction(InvenioTestCase):
    """Test for washing of search query parameters."""

    def test_collection_equality_results(self):
        """search unit - getting same results for collection name."""

        self.assertEqual(
            search_engine.search_unit('Preprints', 'collection'),
            search_engine.search_unit('PREPRINT', '980'))

        self.assertEqual(
            search_engine.search_unit('Books', 'collection'),
            search_engine.search_unit('BOOK', '980'))


TEST_SUITE = make_test_suite(TestWashQueryParameters,
                             TestSearchUnitFunction)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
