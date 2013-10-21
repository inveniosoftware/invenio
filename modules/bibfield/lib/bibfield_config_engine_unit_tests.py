# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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
BibFieldParser Unit tests.
"""

import unittest

from invenio.bibfield_config_engine import BibFieldParser

from invenio.testutils import make_test_suite, run_test_suite


class BibFieldParserUnitTests(unittest.TestCase):
    """
    Test to verify the correct creation of bibfield_config.py from the rules and
    doctypes files.
    """
    def setUp(self):
        """Loads bibfield configuration test files"""
        parser = BibFieldParser(main_config_file="test_bibfield.cfg")
        self.config_rules = parser.config_rules

    def test_bibfield_rules_parser(self):
        """BibField - configuration rules building process"""
        self.assertTrue(len(self.config_rules) >= 20)
        #Check imports
        self.assertTrue('authors' in self.config_rules)
        self.assertTrue('title' in self.config_rules)
        #Check work arroung for [n] and [0]
        self.assertTrue(len(self.config_rules['authors']) == 2)
        self.assertEqual(self.config_rules['authors'], ['authors[0]', 'authors[n]'])
        self.assertTrue('authors[0]' in self.config_rules)
        self.assertTrue('authors[n]' in self.config_rules)
        self.assertTrue(self.config_rules['doi']['persistent_identifier'])
        #Check if derived and calulated are well parserd
        self.assertTrue('dummy' in self.config_rules)
        self.assertTrue(self.config_rules['dummy']['type'] == 'derived')
        self.assertTrue(self.config_rules['dummy']['persistent_identifier'])
        self.assertTrue(self.config_rules['_number_of_copies']['type'] == 'calculated')
        self.assertTrue(self.config_rules['authors[0]']['type'] == 'real')
        self.assertTrue(self.config_rules['_random']['rules']['do_not_cache'])
        self.assertFalse(self.config_rules['_number_of_copies']['rules']['do_not_cache'])
        #Check inheritance
        self.assertTrue('main_author' in self.config_rules)
        self.assertEqual(self.config_rules['main_author']['rules'],
                         self.config_rules['authors[0]']['rules'])

    def test_bibfield_docytpes_parser(self):
        #TODO: next iteration will come with this
        pass

    def test_writing_bibfield_config_file(self):
        #TODO: tests
        pass


TEST_SUITE = make_test_suite(BibFieldParserUnitTests)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
