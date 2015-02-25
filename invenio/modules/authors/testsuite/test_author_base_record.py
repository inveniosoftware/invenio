# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Tests for author_base records."""

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class AuthorBaseRecordTestCase(InvenioTestCase):

    """Base class for author_base records test."""

    def setUp(self):
        """Preparing evironment for tests."""
        self.import_context()

    def import_context(self):
        """Import the Invenio classes here.

        Makes sure the testing context is valid.
        """
        from invenio.modules.records.api import Record
        self.Record = Record

    def create_record_from_json(self, json_dict):
        """Return record created from json dictionary.

        :param json_dict: The dictionary in JSON from with author content
        :return: an author base record
        """
        return self.Record.create(json_dict, 'json', model='author_base')

    def create_record_from_marc(self, xml_string):
        """Return record created from MARCxml string.

        :param xml_string: The string representing MARCxml of an author
        :return: an author base record
        """
        return self.Record.create(xml_string, 'marc', model='author_base')


class AuthorBaseRecordRequiredFieldsTestCase(AuthorBaseRecordTestCase):

    """Test case for `ids` and `name` fields."""

    def test_empty_id_list(self):
        """Empty id list should not be allowed."""
        record = self.create_record_from_json({'ids': [],
                                               'name': {'last': 'Nvenio',
                                                        'first': 'Ian'},
                                               'publications_list': [9]})
        validation = record.validate()
        self.assertTrue('ids' in validation)

    def test_wrong_id_type(self):
        """Record should allow only few specified types in ids field."""
        record = self.create_record_from_json({'ids': [{'type': 'invenioid',
                                                        'value': '9'}],
                                               'name': {'last': 'Nvenio',
                                                        'first': 'Ian'},
                                               'publications_list': [9]})
        validation = record.validate()
        self.assertTrue('type' in validation)

    def test_no_id_type(self):
        """Record should have a type defined in ids field."""
        record = self.create_record_from_json({'ids': [{'value': '9'}],
                                               'name': {'last': 'Nvenio',
                                                        'first': 'Ian'},
                                               'publications_list': [9]})
        validation = record.validate()
        self.assertTrue('type' in validation)

    def test_no_id_value(self):
        """Record should contain values in ids field."""
        record = self.create_record_from_json({'ids': [{'type': 'authorid'}],
                                               'name': {'last': 'Nvenio',
                                                        'first': 'I.'},
                                               'publications_list': [9]})
        validation = record.validate()
        self.assertTrue('value' in validation)

    def test_no_first_name(self):
        """Name should contain both last and first names."""
        record = self.create_record_from_json({'ids': [{'type': 'authorid',
                                                        'value': '15783'}],
                                               'name': {'last': 'Nvenio'},
                                               'publications_list': [9]})
        validation = record.validate()
        self.assertTrue('name' in validation and 'first' in validation['name'])

    def test_correct_author_base(self):
        """Example of a correct base record."""
        record = self.create_record_from_json({'ids': [{'type': 'authorid',
                                                       'value': '15783'},
                                                       {'type': 'authorid',
                                                       'value': 'somename'}],
                                               'name': {'last': 'Nvenio',
                                                        'first': 'I.'},
                                               'publications_list': [9]})
        validation = record.validate()
        self.assertEqual(validation, {})

    def test_correct_name_split(self):
        """Example of a correct marcXML for an author base record."""
        xml_string = '<collection><record><datafield tag="035" ind1="" ind2' \
            '=""><subfield code="9">authorid</subfield><subfield code="a">' \
            '0000-0002-0003-2345</subfield></datafield><datafield tag="100" ind1' \
            '="" ind2=""><subfield code="a">van der Nvenio, I.</subfield>' \
            '</datafield><datafield tag="900" ind1' \
            '="" ind2=""><subfield code="a">9</subfield>' \
            '</datafield></record></collection>'
        record = self.create_record_from_marc(xml_string)

        self.assertEqual(record['name']['last'], 'van der Nvenio')
        self.assertEqual(record['name']['first'], 'I.')

        validation = record.validate()
        self.assertEqual(validation, {})

    def test_no_first_name_split(self):
        """Name should contain not empty information about the name."""
        xml_string = '<collection><record><datafield tag="035" ind1="" ind2' \
            '=""><subfield code="9">authorid</subfield><subfield code="a">' \
            '0000-0002-0003-2345</subfield></datafield><datafield tag="900" ind1' \
            '="" ind2=""><subfield code="a">9</subfield>' \
            '</datafield><datafield tag="100" ind1' \
            '="" ind2=""><subfield code="a">van der Nvenio, </subfield>' \
            '</datafield></record></collection>'
        record = self.create_record_from_marc(xml_string)

        self.assertEqual(record['name']['last'], 'van der Nvenio')
        self.assertEqual(record['name']['first'], '')

        validation = record.validate()
        self.assertTrue('name' in validation)


TEST_SUITE = make_test_suite(AuthorBaseRecordRequiredFieldsTestCase)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
