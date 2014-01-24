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

from invenio.testutils import InvenioTestCase

from invenio.bibfield_config_engine import BibFieldParser, \
        guess_legacy_field_names, get_producer_rules

from invenio.testutils import make_test_suite, run_test_suite


class BibFieldParserUnitTests(InvenioTestCase):
    """
    Test to verify the correct creation of bibfield_config.py from the rules and
    doctypes files.
    """
    def setUp(self):
        """Loads bibfield configuration test files"""
        BibFieldParser._field_definitions = {}
        BibFieldParser._legacy_field_matchings = {}
        parser = BibFieldParser(main_config_file="test_bibfield.cfg")._create()
        self.config_rules = BibFieldParser.field_definitions()

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
        self.assertEquals(self.config_rules['dummy']['persistent_identifier'], 2)
        self.assertEquals(self.config_rules['dummy']['rules'].keys(), ['derived'])
        self.assertTrue(self.config_rules['_random'])
        #Check inheritance
        self.assertTrue('main_author' in self.config_rules)
        self.assertEqual(self.config_rules['main_author']['rules'],
                         self.config_rules['authors[0]']['rules'])
        #Check json
        self.assertTrue('json_ext' in self.config_rules['modification_date'])
        #Check override
        value = {'a':'a', 'b':'b', 'k':'k'}
        self.assertEquals(eval(self.config_rules['title']['rules']['marc'][0]['value']),
                {'form': 'k', 'subtitle': 'b', 'title': 'a'})

    def test_guess_legacy_field_names(self):
        """BibField - check legacy field names"""
        self.assertEquals(guess_legacy_field_names(('100__a', '245'), 'marc'),
                {'100__a':['authors[0].full_name'], '245':['title']})
        self.assertEquals(guess_legacy_field_names('foo', 'bar'), {'foo': []})

    def test_get_producer_rules(self):
        """BibField - check producer rules"""
        self.assertTrue(get_producer_rules('authors[0]', 'json_for_marc')[0] in get_producer_rules('authors', 'json_for_marc'))
        self.assertTrue(len(get_producer_rules('keywords', 'json_for_marc')) == 1)
        self.assertRaises(KeyError, lambda: get_producer_rules('foo', 'json_for_marc'))


TEST_SUITE = make_test_suite(BibFieldParserUnitTests)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
