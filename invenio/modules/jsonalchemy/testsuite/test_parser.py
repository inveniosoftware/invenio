# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Unit tests for the parser engine."""

__revision__ = \
    "$Id$"

import tempfile

from flask_registry import PkgResourcesDirDiscoveryRegistry, \
    ImportPathRegistry, RegistryProxy

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

Field_parser = lazy_import('invenio.modules.jsonalchemy.parser:FieldParser')
Model_parser = lazy_import('invenio.modules.jsonalchemy.parser:ModelParser')
guess_legacy_field_names = lazy_import(
    'invenio.modules.jsonalchemy.parser:guess_legacy_field_names')
get_producer_rules = lazy_import(
    'invenio.modules.jsonalchemy.parser:get_producer_rules')

TEST_PACKAGE = 'invenio.modules.jsonalchemy.testsuite'

test_registry = RegistryProxy('testsuite', ImportPathRegistry,
                              initial=[TEST_PACKAGE])

field_definitions = lambda: PkgResourcesDirDiscoveryRegistry(
    'fields', registry_namespace=test_registry)
model_definitions = lambda: PkgResourcesDirDiscoveryRegistry(
    'models', registry_namespace=test_registry)


def clean_field_model_definitions():
    Field_parser._field_definitions = {}
    Field_parser._legacy_field_matchings = {}
    Model_parser._model_definitions = {}


class TestParser(InvenioTestCase):

    def setUp(self):
        self.app.extensions['registry'][
            'testsuite.fields'] = field_definitions()
        self.app.extensions['registry'][
            'testsuite.models'] = model_definitions()

    def tearDown(self):
        del self.app.extensions['registry']['testsuite.fields']
        del self.app.extensions['registry']['testsuite.models']

    def test_wrong_indent(self):
        """JSONAlchemy - wrong indent"""
        from invenio.modules.jsonalchemy.parser import _create_field_parser
        import pyparsing
        parser = _create_field_parser()
        test = """
        foo:
            creator:
        bar, '1', foo()
        """
        self.assertRaises(pyparsing.ParseException, parser.parseString, test)

        from invenio.modules.jsonalchemy.errors import FieldParserException
        tmp_file = tempfile.NamedTemporaryFile()
        config = """
        foo:
            creator:
        bar, '1', foo()
        """
        tmp_file.write(config)
        tmp_file.flush()

        self.app.extensions['registry'][
            'testsuite.fields'].register(tmp_file.name)
        clean_field_model_definitions()
        self.assertRaises(
            FieldParserException, Field_parser.reparse, 'testsuite')
        tmp_file.close()
        clean_field_model_definitions()

    def test_wrong_field_definitions(self):
        """JSONAlchemy - wrong field definitions"""
        from invenio.modules.jsonalchemy.errors import FieldParserException
        tmp_file_4 = tempfile.NamedTemporaryFile()
        config_4 = '''
        title:
            creator:
                marc, '245__', value
        '''
        tmp_file_4.write(config_4)
        tmp_file_4.flush()
        clean_field_model_definitions()
        self.app.extensions['registry'][
            'testsuite.fields'].register(tmp_file_4.name)
        self.assertRaises(
            FieldParserException, Field_parser.reparse, 'testsuite')
        tmp_file_4.close()
        clean_field_model_definitions()

    def test_wrong_field_inheritance(self):
        """JSONAlchmey - not parent field definition"""
        from invenio.modules.jsonalchemy.errors import FieldParserException
        tmp_file_5 = tempfile.NamedTemporaryFile()
        config_5 = '''
        @extend
        wrong_field:
            """ Desc """
        '''
        tmp_file_5.write(config_5)
        tmp_file_5.flush()
        clean_field_model_definitions()
        self.app.extensions['registry'][
            'testsuite.fields'].register(tmp_file_5.name)
        self.assertRaises(
            FieldParserException, Field_parser.reparse, 'testsuite')
        tmp_file_5.close()
        clean_field_model_definitions()

    def test_field_rules(self):
        """JsonAlchemy - field parser"""
        self.assertTrue(len(Field_parser.field_definitions('testsuite')) >= 22)
        # Check that all files are parsed
        self.assertTrue(
            'authors' in Field_parser.field_definitions('testsuite'))
        self.assertTrue('title' in Field_parser.field_definitions('testsuite'))
        # Check work around for [n] and [0]
        self.assertTrue(
            Field_parser.field_definitions('testsuite')['doi']['pid'])
        # Check if derived and calulated are well parserd
        self.assertTrue('dummy' in Field_parser.field_definitions('testsuite'))
        self.assertEquals(
            Field_parser.field_definitions('testsuite')['dummy']['pid'], 2)
        self.assertEquals(Field_parser.field_definitions(
            'testsuite')['dummy']['rules'].keys(), ['json', 'derived'])
        self.assertTrue(
            len(Field_parser.field_definitions(
                'testsuite')['dummy']['producer']
                ),
            2
        )
        self.assertTrue(Field_parser.field_definitions('testsuite')['_random'])
        # Check override
        value = {'a': 'a', 'b': 'b', 'k': 'k'}  # noqa
        self.assertEquals(
            eval(Field_parser.field_definitions('testsuite')
                 ['title']['rules']['marc'][1]['function']),
            {'form': 'k', 'subtitle': 'b', 'title': 'a'})
        # Check extras
        self.assertTrue(
            'json_ext' in
            Field_parser.field_definitions('testsuite')['modification_date']
        )

        tmp = Field_parser.field_definitions('testsuite')
        Field_parser.reparse('testsuite')
        self.assertEquals(
            len(Field_parser.field_definitions('testsuite')), len(tmp))

    def test_field_hidden_decorator(self):
        """JsonAlchemy - field hidden decorator."""
        # Check that all files are parsed
        self.assertTrue(
            'hidden_basic' in Field_parser.field_definitions('testsuite'))
        # Check default hidden value
        self.assertFalse(
            Field_parser.field_definitions('testsuite')['_id']['hidden'])
        # Check hidden field
        self.assertTrue(Field_parser.field_definitions(
            'testsuite')['hidden_basic']['hidden'])

    def test_wrong_field_name_inside_model(self):
        """JSONAlchmey - wrong field name inside model"""
        from invenio.modules.jsonalchemy.errors import ModelParserException
        tmp_file_8 = tempfile.NamedTemporaryFile()
        config_8 = '''
        fields:
            not_existing_field
        '''
        tmp_file_8.write(config_8)
        tmp_file_8.flush()
        clean_field_model_definitions()
        self.app.extensions['registry'][
            'testsuite.models'].register(tmp_file_8.name)
        self.assertRaises(
            ModelParserException, Model_parser.reparse, 'testsuite')
        tmp_file_8.close()
        clean_field_model_definitions()

    def test_model_definitions(self):
        """JsonAlchemy - model parser"""
        clean_field_model_definitions()
        self.assertTrue(len(Model_parser.model_definitions('testsuite')) >= 2)
        self.assertTrue(
            'test_base' in Model_parser.model_definitions('testsuite'))
        tmp = Model_parser.model_definitions('testsuite')
        Model_parser.reparse('testsuite')
        self.assertEquals(
            len(Model_parser.model_definitions('testsuite')), len(tmp))
        clean_field_model_definitions()

    def test_resolve_several_models(self):
        """JSONAlchemy - test resolve several models"""
        test_model = Model_parser.model_definitions('testsuite')['test_model']
        clean_field_model_definitions()
        self.assertEquals(
            Model_parser.resolve_models('test_model', 'testsuite')['fields'],
            test_model['fields'])
        self.assertEquals(
            Model_parser.resolve_models(
                ['test_base', 'test_model'], 'testsuite')['fields'],
            test_model['fields'])
        clean_field_model_definitions()

    def test_field_name_model_based(self):
        """JSONAlchemy - field name model based"""
        clean_field_model_definitions()
        field_model_def = Field_parser.field_definition_model_based(
            'title', 'test_model', 'testsuite')
        field_def = Field_parser.field_definitions('testsuite')['title_title']

        value = {'a': 'Awesome title', 'b': 'sub title', 'k': 'form'}
        from invenio.base.utils import try_to_eval

        self.assertEqual(
            try_to_eval(field_model_def['rules'][
                        'marc'][0]['function'], value=value),
            try_to_eval(field_def['rules']['marc'][0]['function'],
                        value=value))
        clean_field_model_definitions()

    def test_guess_legacy_field_names(self):
        """JsonAlchemy - check legacy field names"""
        self.assertEquals(
            guess_legacy_field_names(('100__a', '245'), 'marc', 'testsuite'),
            {'100__a': ['_first_author.full_name'], '245': ['title']})
        self.assertEquals(
            guess_legacy_field_names('foo', 'bar', 'baz'), {'foo': []})

    def test_get_producer_rules(self):
        """JsonAlchemy - check producer rules"""
        clean_field_model_definitions()
        self.assertEquals(
            len(get_producer_rules('keywords', 'json_for_marc', 'testsuite')),
            1
        )
        self.assertRaises(
            KeyError,
            lambda: get_producer_rules('foo', 'json_for_marc', 'testsuite'))
        clean_field_model_definitions()


TEST_SUITE = make_test_suite(TestParser)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
