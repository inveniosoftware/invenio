# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
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

from invenio.base.wrappers import lazy_import
from invenio.testsuite import InvenioXmlTestCase
from invenio.testsuite import make_test_suite, run_test_suite

BibRecord = lazy_import('invenio.legacy.docextract.record:BibRecord')
BibRecordControlField = lazy_import('invenio.legacy.docextract.record:'
                                    'BibRecordControlField')
BibRecordField = lazy_import('invenio.legacy.docextract.record:BibRecordField')
BibRecordSubField = lazy_import('invenio.legacy.docextract.record:'
                                'BibRecordSubField')
create_record = lazy_import('invenio.legacy.docextract.record:create_record')


class BibRecordTest(InvenioXmlTestCase):
    def setUp(self):
        self.xml = """<record>
            <datafield tag="100" ind1=" " ind2=" ">
                <subfield code="a">our title</subfield>
            </datafield>
        </record>"""

    def test_to_xml(self):
        record = create_record(self.xml)
        record2 = create_record(record.to_xml())
        self.assertEqual(record, record2)

    def test_del_subfield(self):
        record = create_record(self.xml)
        record.add_subfield('100__b', 'not title')

        del record['100__a']

        expected_record = BibRecord()
        expected_record.add_subfield('100__b', 'not title')

        self.assertEqual(record, expected_record)

    def test_del_subfield2(self):
        record = create_record(self.xml)
        record['100__'][0].add_subfield('b', 'not title')

        del record['100__a']

        expected_record = BibRecord()
        expected_record.add_subfield('100__b', 'not title')

        self.assertEqual(record, expected_record)

    def test_del_subfield3(self):
        field = BibRecordField()
        field.add_subfield('a', 'title')
        field.add_subfield('b', 'not title')
        del field['a']

        field2 = BibRecordField()
        field2.add_subfield('b', 'not title')

        self.assertEqual(field, field2)

    def test_set_subfield(self):
        field = BibRecordField()
        field.add_subfield('a', 'title')
        field['a'] = 'title2'

        field2 = BibRecordField()
        field2.add_subfield('a', 'title2')

        self.assertEqual(field, field2)

    def test_del_field(self):
        record = create_record(self.xml)
        record.add_subfield('101__b', 'not title')

        del record['100__']

        expected_record = BibRecord()
        expected_record.add_subfield('101__b', 'not title')

        self.assertEqual(record, expected_record)

    def test_len_subfields(self):
        field = BibRecordField()
        field.add_subfield('a', 'title')
        field.add_subfield('b', 'not title')
        self.assertEqual(len(field), 2)

    def test_add_field(self):
        expected_record = create_record(self.xml)
        record = BibRecord()
        record.add_field('100__')
        record['100__'][0].add_subfield('a', 'our title')
        self.assertEqual(record, expected_record)

    def test_find_fields(self):
        record = create_record(self.xml)
        record.add_subfield('10012b', 'not title')
        found_fields = record.find_fields('100__')
        expected_fields = [BibRecordField(ind1=' ', ind2=' ')]
        expected_fields[0].add_subfield('a', 'our title')
        self.assertEqual(found_fields, expected_fields)

    def test_add_subfield(self):
        expected_record = create_record(self.xml)
        record = BibRecord()
        record.add_subfield('100__a', 'our title')
        self.assertEqual(record, expected_record)

    def test_add_subfield2(self):
        expected_record = create_record(self.xml)
        record = BibRecord()
        field = BibRecordField()
        record['100'] = [field]
        field.add_subfield('a', 'our title')
        self.assertEqual(record, expected_record)

    def test_record_equality(self):
        record1 = create_record(self.xml)
        record2 = create_record(self.xml)
        self.assertEqual(record1, record2)

    def test_len_record(self):
        record = create_record(self.xml)
        self.assertEqual(len(record), 1)
        record.add_subfield('100__a', 'our title2')
        self.assertEqual(len(record), 2)

    def test_set_record(self):
        record = BibRecord()
        field = BibRecordField()
        record['100'] = [field]
        self.assertEqual(len(record), 1)

    def test_subfield_equality(self):
        self.assertEqual(BibRecordSubField('a', 'title'),
                         BibRecordSubField('a', 'title'))
        self.assertNotEqual(BibRecordSubField('a', 'title'),
                            BibRecordSubField('b', 'title'))
        self.assertNotEqual(BibRecordSubField('a', 'title'),
                            BibRecordSubField('a', 'title2'))

    def test_field_equality(self):
        field = BibRecordField(ind1='1', ind2='2')
        field2 = BibRecordField(ind1='1', ind2='2')
        self.assertEqual(field, field2)
        self.assertNotEqual(field, BibRecordField(ind1='2', ind2='1'))

        field.add_subfield('a', 'title')
        self.assertNotEqual(field, field2)

        field2.add_subfield('a', 'title')
        self.assertEqual(field, field2)

    def test_controlfield_equality(self):
        field = BibRecordControlField('11211')
        self.assertEqual(field, BibRecordControlField('11211'))
        self.assertNotEqual(field, BibRecordControlField('11212'))

    def test_get_subfield_values(self):
        field = BibRecordField(ind1='1', ind2='2')
        field.add_subfield('a', 'title')
        self.assertEqual(field.get_subfield_values('a'), ['title'])
        self.assertEqual(field['a'], ['title'])

    def test_find_subfields(self):
        field = BibRecordField(ind1='1', ind2='2')
        field.add_subfield('a', 'title')
        field.add_subfield('b', 'not title')
        self.assertEqual(field.find_subfields('a'),
                         [BibRecordSubField('a', 'title')])

    def test_find_subfields2(self):
        record = create_record(self.xml)
        record.add_subfield('10012b', 'not title')
        found_subfields = record.find_subfields('100__a')
        expected_subfields = [BibRecordSubField('a', 'our title')]
        self.assertEqual(found_subfields, expected_subfields)



TEST_SUITE = make_test_suite(BibRecordTest)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
