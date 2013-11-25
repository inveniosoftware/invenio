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

from invenio.docextract_record import BibRecord, \
                                      get_record, \
                                      create_record, \
                                      create_records
from invenio.search_engine import get_record as get_record_original
from invenio.search_engine import perform_request_search
from invenio.bibrecord import print_rec
from invenio.testutils import XmlTest
from invenio.dbquery import run_sql
from invenio.testutils import (make_test_suite,
                               run_test_suite)


class BibRecordTest(XmlTest):
    def setUp(self):
        self.maxDiff = None
        from invenio import bibrecord

        def order_by_tag(field1, field2):
            """Function used to order the fields according to their tag"""
            return cmp(field1[0], field2[0])
        bibrecord._order_by_ord = order_by_tag  # pylint: disable-msg=W0212

        self.records_cache = {}
        self.xml_cache = {}
        for recid in perform_request_search(p=""):
            r = run_sql("SELECT master_format FROM bibrec WHERE id=%s", [recid])
            self.assertTrue(r, msg="bibrec row for %s missing" % recid)
            if r[0][0] != 'marc':
                continue
            record = get_record(recid)
            self.records_cache[recid] = record
            self.xml_cache[recid] = record.to_xml()

    def test_get_record(self):
        for recid in perform_request_search(p=""):
            # Our bibrecord we want to test
            record = self.records_cache[recid]
            # Reference implementation
            original_record = get_record_original(recid)
            self.assertXmlEqual(record.to_xml(), print_rec(original_record))

    def test_create_record(self):
        for dummy, xml in self.xml_cache.iteritems():
            record = create_record(xml)
            self.assertXmlEqual(record.to_xml(), xml)

    def test_create_records(self):
        xml = '\n'.join(self.xml_cache.itervalues())
        records = create_records(xml)
        for record in self.records_cache.itervalues():
            self.assertEqual(record, records.pop(0))

    def test_equality(self):
        for recid in self.records_cache.iterkeys():
            for recid2 in self.records_cache.iterkeys():
                record = self.records_cache[recid]
                xml = self.xml_cache[recid]
                if recid == recid2:
                    record2 = get_record(recid)
                    xml2 = record2.to_xml()
                    self.assertEqual(record, record2)
                    self.assertXmlEqual(xml, xml2)
                else:
                    record2 = self.records_cache[recid2]
                    xml2 = self.xml_cache[recid2]
                    self.assertNotEqual(record, record2)

    def test_hash(self):
        for dummy, original_record in self.records_cache.iteritems():
            # Our bibrecord we want to test
            record = BibRecord()

            for tag, fields in original_record.record.iteritems():
                record[tag] = list(set(fields))
                self.assertEqual(set(record[tag]), set(original_record[tag]))

            self.assertEqual(record, original_record)

    def test_add_subfield(self):
        xml = """<record>
            <datafield tag="100" ind1=" " ind2=" ">
                <subfield code="a">our title</subfield>
            </datafield>
        </record>"""
        expected_record = create_record(xml)
        print expected_record
        record = BibRecord()
        record.add_subfield('100__a', 'our title')
        print record
        self.assertEqual(record, expected_record)

TEST_SUITE = make_test_suite(BibRecordTest)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
