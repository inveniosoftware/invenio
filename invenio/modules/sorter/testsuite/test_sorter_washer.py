# -*- mode: python; coding: utf-8; -*-
#
# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2012, 2013 CERN.
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

"""Testing module for BibSort Method Treatment"""

from invenio.legacy.bibsort.washer import BibSortWasher
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class TestBibSortWasherCreation(InvenioTestCase):
    """Test BibSortWasher Creation."""

    def test_method_creation(self):
        """Tests the creation of a method"""
        method = 'sort_alphanumerically_remove_leading_articles'
        bsm = BibSortWasher(method)
        self.assertEqual(bsm.get_washer(), method)


class TestBibSortWasherWashers(InvenioTestCase):
    """Test BibSortWasher Washers."""

    def test_sort_alphanumerically_remove_leading_articles(self):
        """Test the sort_alphanumerically_remove_leading_articles method"""
        method = "sort_alphanumerically_remove_leading_articles"
        bsm = BibSortWasher(method)
        self.assertEqual('title of a record', bsm.get_transformed_value('The title of a record'))
        self.assertEqual('title of a record', bsm.get_transformed_value('a title of a record'))
        self.assertEqual('the', bsm.get_transformed_value('The'))

    def test_sort_dates(self):
        """Test the sort_dates method"""
        method = "sort_dates"
        bsm = BibSortWasher(method)
        self.assertEqual('2010-01-10', bsm.get_transformed_value('2010-01-10'))
        self.assertEqual('2010-11-10', bsm.get_transformed_value('10 nov 2010'))
        self.assertEqual('2010-11-01', bsm.get_transformed_value('nov 2010'))
        self.assertEqual('2010-01-01', bsm.get_transformed_value('2010'))
        self.assertEqual('2010-11-08', bsm.get_transformed_value('8 nov 2010'))

    def test_sort_nosymbols_case_insensitive_strip_accents(self):
        """Test the sort_nosymbols_case_insensitive_strip_accents method"""
        method = "sort_nosymbols_case_insensitive_strip_accents"
        bsm = BibSortWasher(method)
        self.assertEqual("thooftgerardus", bsm.get_transformed_value("'t Hooft, Gerardus"))
        self.assertEqual("ahearnmichaelf", bsm.get_transformed_value("A'Hearn, Michael F."))
        self.assertEqual("zvolskymilan", bsm.get_transformed_value("Zvolský, Milan"))


TEST_SUITE = make_test_suite(TestBibSortWasherWashers,
                             TestBibSortWasherCreation)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
