# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

"""
BibCatalog unit tests
"""

import unittest
from invenio.testutils import make_test_suite, run_test_suite

from invenio.bibcatalog_utils import \
    load_tag_code_from_name, \
    split_tag_code, \
    record_get_value_with_provenence, \
    record_id_from_record, \
    record_in_collection, \
    BibCatalogTagNotFound
from invenio.bibformat_dblayer import get_all_name_tag_mappings


class TestUtilityFunctions(unittest.TestCase):
    """Test non-data-specific utility functions for BibCatalog."""

    def setUp(self):
        self.record = {'001': [([], ' ', ' ', '1', 1)],
                       '650': [([('2', 'SzGeCERN'), ('a', 'Experiments and Tracks')],
                               '1', '7', '', 2),
                               ([('9', 'arXiv'), ('a', 'hep-ph')],
                               '1', '7', '', 3),
                               ([('9', 'arXiv'), ('a', 'hep-th')],
                               '1', '7', '', 4)],
                       '980': [([('a', 'PICTURE')], ' ', ' ', '', 3)]}

    def test_load_tag_code_from_name(self):
        """Tests function bibcatalog_utils.load_tag_code_from_name"""
        if 'record ID' in get_all_name_tag_mappings():
            self.assertEqual(load_tag_code_from_name("record ID"), "001")
        # Name "foo" should not exist and raise an exception
        self.assertRaises(BibCatalogTagNotFound, load_tag_code_from_name, "foo")

    def test_split_tag_code(self):
        """Tests function bibcatalog_utils.split_tag_code"""
        self.assertEqual(split_tag_code('035__a'),
                         {"tag": "035",
                          "ind1": "_",
                          "ind2": "_",
                          "code": "a"})

        self.assertEqual(split_tag_code('035'),
                         {"tag": "035",
                          "ind1": "%",
                          "ind2": "%",
                          "code": "%"})

    def test_record_in_collection(self):
        """Tests function bibcatalog_utils.record_in_collection"""
        self.assertFalse(record_in_collection(self.record, "THESIS"))
        self.assertTrue(record_in_collection(self.record, "picture"))

    def test_record_id_from_record(self):
        """Tests function bibcatalog_utils.record_id_from_record"""
        self.assertEqual("1", record_id_from_record(self.record))

    def test_record_get_value_with_provenence(self):
        """Tests function bibcatalog_utils.record_get_value_with_provenence"""
        self.assertEqual(["hep-ph", "hep-th"],
                         record_get_value_with_provenence(record=self.record,
                                                          provenence_value="arXiv",
                                                          provenence_code="9",
                                                          tag="650",
                                                          ind1="1",
                                                          ind2="7",
                                                          code="a"))


TEST_SUITE = make_test_suite(TestUtilityFunctions)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)