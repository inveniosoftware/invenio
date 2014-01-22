# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

"""Unit tests for the parser engine."""

__revision__ = \
    "$Id$"

import os
import tempfile

from flask_registry import PkgResourcesDirDiscoveryRegistry, \
    ImportPathRegistry, RegistryProxy

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

Field_parser = lazy_import('invenio.modules.jsonalchemy.parser:FieldParser')
Model_parser = lazy_import('invenio.modules.jsonalchemy.parser:ModelParser')
guess_legacy_field_names = lazy_import('invenio.modules.jsonalchemy.parser:guess_legacy_field_names')
get_producer_rules = lazy_import('invenio.modules.jsonalchemy.parser:get_producer_rules')

TEST_PACKAGE = 'invenio.modules.jsonalchemy.testsuite'

test_registry = RegistryProxy('testsuite', ImportPathRegistry,
                              initial=[TEST_PACKAGE])

field_definitions = lambda: PkgResourcesDirDiscoveryRegistry(
    'fields', registry_namespace=test_registry)
model_definitions = lambda: PkgResourcesDirDiscoveryRegistry(
    'models', registry_namespace=test_registry)


class TestParser(InvenioTestCase):

    def setUp(self):
        self.tmp_file_1 = tempfile.NamedTemporaryFile()
        config_1 = '''
@inherit_from(("authors[0]",))
main_author:
    """Just main author"""
        '''
        self.tmp_file_1.write(config_1)
        self.tmp_file_1.flush()
        self.tmp_file_2 = tempfile.NamedTemporaryFile()
        config_2 = '''
include "%s"

authors[0], creator:
    creator:
        @legacy((("100", "100__", "100__%%"), ""),
                ("100__a", "first author name", "full_name"),
                ("100__e", "relator_name"),
                ("100__h", "CCID"),
                ("100__i", "INSPIRE_number"),
                ("100__u", "first author affiliation", "affiliation"))
        marc, "100__", { 'full_name':value['a'], 'first_name':util_split(value['a'],',',1), 'last_name':util_split(value['a'],',',0), 'relator_name':value['e'], 'CCID':value['h'], 'INSPIRE_number':value['i'], 'affiliation':value['u'] }
    checker:
        check_field_existence(0,1)
        check_field_type('str')
    producer:
        json_for_marc(), {"100__a": "full_name", "100__e": "relator_name", "100__h": "CCID", "100__i": "INSPIRE_number", "100__u": "affiliation"}
        json_for_dc(), {"dc:creator": "full_name"}
    description:
        """Main Author"""

authors[n], contributor:
    creator:
        @legacy((("700", "700__", "700__%%"), ""),
                ("700__a", "additional author name", "full_name"),
                ("700__u", "additional author affiliation", "affiliation"))
        marc, "700__", {'full_name': value['a'], 'first_name':util_split(value['a'],',',1), 'last_name':util_split(value['a'],',',0), 'relator_name':value['e'], 'CCID':value['h'], 'INSPIRE_number':value['i'], 'affiliation':value['u'] }
    checker:
        check_field_existence(0,'n')
        check_field_type('str')
    producer:
        json_for_marc(), {"700__a": "full_name", "700__e": "relator_name", "700__h": "CCID", "700__i": "INSPIRE_number", "700__u": "affiliation"}
        json_for_dc(), {"dc:contributor": "full_name"}
    description:
        """Authors"""

        ''' % (self.tmp_file_1.name, )
        self.tmp_file_2.write(config_2)
        self.tmp_file_2.flush()

        self.app.extensions['registry']['testsuite.fields'] = field_definitions()
        for path in self.app.extensions['registry']['testsuite.fields'].registry:
            if os.path.basename(path) == 'authors.cfg':
                self.app.extensions['registry']['testsuite.fields'].registry.remove(path)
        self.app.extensions['registry']['testsuite.fields'].register(self.tmp_file_2.name)
        self.app.extensions['registry']['testsuite.models'] = model_definitions()

    def tearDown(self):
        del self.app.extensions['registry']['testsuite.fields']
        del self.app.extensions['registry']['testsuite.models']
        self.tmp_file_1.close()
        self.tmp_file_2.close()

    def test_field_rules(self):
        """JsonAlchemy - field parser"""
        self.assertTrue(len(Field_parser.field_definitions('testsuite')) >= 22)
        #Check that all files are parsed
        self.assertTrue('authors' in Field_parser.field_definitions('testsuite'))
        self.assertTrue('title' in Field_parser.field_definitions('testsuite'))
        #Check work arroung for [n] and [0]
        self.assertTrue(len(Field_parser.field_definitions('testsuite')['authors']) == 2)
        self.assertEqual(Field_parser.field_definitions('testsuite')['authors'], ['authors[0]', 'authors[n]'])
        self.assertTrue('authors[0]' in Field_parser.field_definitions('testsuite'))
        self.assertTrue('authors[n]' in Field_parser.field_definitions('testsuite'))
        self.assertTrue(Field_parser.field_definitions('testsuite')['doi']['persistent_identifier'])
        #Check if derived and calulated are well parserd
        self.assertTrue('dummy' in Field_parser.field_definitions('testsuite'))
        self.assertEquals(Field_parser.field_definitions('testsuite')['dummy']['persistent_identifier'], 2)
        self.assertEquals(Field_parser.field_definitions('testsuite')['dummy']['rules'].keys(), ['derived'])
        self.assertTrue(Field_parser.field_definitions('testsuite')['_random'])
        #Check inheritance
        self.assertTrue('main_author' in Field_parser.field_definitions('testsuite'))
        self.assertEqual(Field_parser.field_definitions('testsuite')['main_author']['rules'],
                         Field_parser.field_definitions('testsuite')['authors[0]']['rules'])
        #Check override
        value = {'a':'a', 'b':'b', 'k':'k'}
        self.assertEquals(eval(Field_parser.field_definitions('testsuite')['title']['rules']['marc'][0]['value']),
                {'form': 'k', 'subtitle': 'b', 'title': 'a'})
        #Check extras
        self.assertTrue('json_ext' in Field_parser.field_definitions('testsuite')['modification_date'])

        tmp = Field_parser.field_definitions('testsuite')
        Field_parser.reparse('testsuite')
        self.assertEquals(len(Field_parser.field_definitions('testsuite')), len(tmp))

    def test_model_definitions(self):
        """JsonAlchemy - model parser"""
        self.assertTrue(len(Model_parser.model_definitions('testsuite')) >= 2)
        self.assertTrue('base' in Model_parser.model_definitions('testsuite'))
        tmp = Model_parser.model_definitions('testsuite')
        Model_parser.reparse('testsuite')
        self.assertEquals(len(Model_parser.model_definitions('testsuite')), len(tmp))

    def test_guess_legacy_field_names(self):
        """JsonAlchemy - check legacy field names"""
        self.assertEquals(guess_legacy_field_names(('100__a', '245'), 'marc', 'testsuite'),
                {'100__a':['authors[0].full_name'], '245':['title']})
        self.assertEquals(guess_legacy_field_names('foo', 'bar', 'baz'), {'foo': []})

    def test_get_producer_rules(self):
        """JsonAlchemy - check producer rules"""
        self.assertTrue(get_producer_rules('authors[0]', 'json_for_marc', 'testsuite')[0] in get_producer_rules('authors', 'json_for_marc', 'testsuite'))
        self.assertTrue(len(get_producer_rules('keywords', 'json_for_marc', 'testsuite')) == 1)
        self.assertRaises(KeyError, lambda: get_producer_rules('foo', 'json_for_marc', 'testsuite'))


TEST_SUITE = make_test_suite(TestParser)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
