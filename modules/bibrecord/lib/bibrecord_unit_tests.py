# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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
The BibRecord test suite.
"""

from invenio.testutils import InvenioTestCase

from invenio.config import CFG_TMPDIR, \
     CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG
from invenio import bibrecord, bibrecord_config
from invenio.testutils import make_test_suite, run_test_suite

try:
    import pyRXP
    parser_pyrxp_available = True
except ImportError:
    parser_pyrxp_available = False

try:
    from lxml import etree
    parser_lxml_available = True
except ImportError:
    parser_lxml_available = False

try:
    import Ft.Xml.Domlette
    parser_4suite_available = True
except ImportError:
    parser_4suite_available = False

try:
    import xml.dom.minidom
    import xml.parsers.expat
    parser_minidom_available = True
except ImportError:
    parser_minidom_available = False

class BibRecordSuccessTest(InvenioTestCase):
    """ bibrecord - demo file parsing test """

    def setUp(self):
        """Initialize stuff"""
        f = open(CFG_TMPDIR + '/demobibdata.xml', 'r')
        xmltext = f.read()
        f.close()
        self.recs = [rec[0] for rec in bibrecord.create_records(xmltext)]

    def test_records_created(self):
        """ bibrecord - demo file how many records are created """
        self.assertEqual(145, len(self.recs))

    def test_tags_created(self):
        """ bibrecord - demo file which tags are created """
        ## check if the tags are correct

        tags = ['003', '005', '020', '024', '035', '037', '041', '080', '084', '088',
                '100', '110', '148', '150', '242', '245', '246', '250', '260', '269',
                '270', '300', '340', '371', '372', '400', '410', '430', '440', '450',
                '490', '500', '502', '506', '510', '520', '542', '550', '588', '590',
                '595', '643', '650', '653', '670', '678', '680', '690', '691', '693',
                '694', '695', '697', '700', '710', '711', '720', '773', '786', '852',
                '856', '859', '901', '909', '913', '914', '916', '920', '960', '961',
                '962', '963', '964', '970', '980', '999', 'FFT']

        t = []
        for rec in self.recs:
            t.extend(rec.keys())
        t.sort()
        #eliminate the elements repeated
        tt = []
        for x in t:
            if not x in tt:
                tt.append(x)
        self.assertEqual(tags, tt)

    def test_fields_created(self):
        """bibrecord - demo file how many fields are created"""
        ## check if the number of fields for each record is correct

        fields = [14, 14, 8, 11, 11, 13, 11, 15, 10, 18, 15, 16,
                  10, 9, 15, 10, 11, 11, 11, 9, 11, 11, 10, 9, 9, 9,
                  10, 9, 10, 10, 8, 9, 8, 9, 14, 13, 14, 14, 15, 12,
                  13, 12, 15, 15, 13, 16, 16, 15, 15, 14, 16, 15, 15,
                  15, 16, 15, 16, 15, 15, 16, 15, 15, 14, 15, 12, 13,
                  11, 15, 8, 11, 14, 13, 12, 13, 6, 6, 25, 24, 27, 26,
                  26, 24, 26, 26, 25, 28, 24, 23, 27, 25, 25, 26, 26,
                  25, 20, 26, 25, 22, 9, 8, 9, 9, 8, 7, 19, 21, 27, 23,
                  23, 22, 9, 8, 16, 7, 7, 9, 5, 5, 3, 9, 12, 6,
                  8, 8, 8, 13, 20, 20, 5, 8, 7, 7, 7, 7, 7, 8, 7, 8, 7, 7, 8,
                  3, 3, 3, 3]
        cr = []
        ret = []
        for rec in self.recs:
            cr.append(len(rec.values()))
            ret.append(rec)
        self.assertEqual(fields, cr, "\n%s\n!=\n%s" % (fields, cr))

    def test_create_record_with_collection_tag(self):
        """ bibrecord - create_record() for single record in collection"""
        xmltext = """
        <collection>
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        </datafield>
        </record>
        </collection>
        """
        record = bibrecord.create_record(xmltext)
        record1 = bibrecord.create_records(xmltext)[0]
        self.assertEqual(record1, record)

class BibRecordParsersTest(InvenioTestCase):
    """ bibrecord - testing the creation of records with different parsers"""

    def setUp(self):
        """Initialize stuff"""
        self.xmltext = """
        <!-- A first comment -->
        <collection>
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1=" " ind2=" ">
        <!-- A second comment -->
        <subfield code="a">eng</subfield>
        </datafield>
        </record>
        </collection>
        """
        self.expected_record = {
            '001': [([], ' ', ' ', '33', 1)],
            '041': [([('a', 'eng')], ' ', ' ', '', 2)]
            }

    if parser_pyrxp_available:
        def test_pyRXP(self):
            """ bibrecord - create_record() with pyRXP """
            record = bibrecord._create_record_rxp(self.xmltext)
            self.assertEqual(record, self.expected_record)

    if parser_lxml_available:
        def test_lxml(self):
            """ bibrecord - create_record() with lxml"""
            record = bibrecord._create_record_lxml(self.xmltext)
            self.assertEqual(record, self.expected_record)

    if parser_4suite_available:
        def test_4suite(self):
            """ bibrecord - create_record() with 4suite """
            record = bibrecord._create_record_4suite(self.xmltext)
            self.assertEqual(record, self.expected_record)

    if parser_minidom_available:
        def test_minidom(self):
            """ bibrecord - create_record() with minidom """
            record = bibrecord._create_record_minidom(self.xmltext)
            self.assertEqual(record, self.expected_record)

class BibRecordDropDuplicateFieldsTest(InvenioTestCase):
    def test_drop_duplicate_fields(self):
        """bibrecord - testing record_drop_duplicate_fields()"""
        record = """
        <record>
        <controlfield tag="001">123</controlfield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe, John</subfield>
        <subfield code="u">Foo University</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe, John</subfield>
        <subfield code="u">Foo University</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="u">Foo University</subfield>
        <subfield code="a">Doe, John</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe, John</subfield>
        <subfield code="u">Foo University</subfield>
        <subfield code="a">Doe, John</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2=" ">
        <subfield cde="a">On the foo and bar</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe, John</subfield>
        <subfield code="u">Foo University</subfield>
        </datafield>
        </record>
        """
        record_result = """
        <record>
        <controlfield tag="001">123</controlfield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe, John</subfield>
        <subfield code="u">Foo University</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="u">Foo University</subfield>
        <subfield code="a">Doe, John</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe, John</subfield>
        <subfield code="u">Foo University</subfield>
        <subfield code="a">Doe, John</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2=" ">
        <subfield cde="a">On the foo and bar</subfield>
        </datafield>
        </record>
        """
        rec = bibrecord.create_record(record)[0]
        rec = bibrecord.record_drop_duplicate_fields(rec)
        rec2 = bibrecord.create_record(record_result)[0]
        self.maxDiff = None
        self.assertEqual(rec, rec2)


class BibRecordBadInputTreatmentTest(InvenioTestCase):
    """ bibrecord - testing for bad input treatment """
    def test_empty_collection(self):
        """bibrecord - empty collection"""
        xml_error0 = """<collection></collection>"""
        rec = bibrecord.create_record(xml_error0)[0]
        self.assertEqual(rec, {})
        records = bibrecord.create_records(xml_error0)
        self.assertEqual(len(records), 0)

    def test_wrong_attribute(self):
        """bibrecord - bad input subfield \'cde\' instead of \'code\'"""
        ws = bibrecord.CFG_BIBRECORD_WARNING_MSGS
        xml_error1 = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe, John</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2=" ">
        <subfield cde="a">On the foo and bar</subfield>
        </datafield>
        </record>
        """
        e = bibrecord.create_record(xml_error1, 1, 1)[2]
        ee =''
        for i in e:
            if type(i).__name__ == 'str':
                if i.count(ws[3])>0:
                    ee = i
        self.assertEqual(bibrecord._warning((3, '(field number: 4)')), ee)

    def test_missing_attribute(self):
        """ bibrecord - bad input missing \"tag\" """
        ws = bibrecord.CFG_BIBRECORD_WARNING_MSGS
        xml_error2 = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe, John</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2=" ">
        <subfield code="a">On the foo and bar</subfield>
        </datafield>
        </record>
        """
        e = bibrecord.create_record(xml_error2, 1, 1)[2]
        ee = ''
        for i in e:
            if type(i).__name__ == 'str':
                if i.count(ws[1])>0:
                    ee = i
        self.assertEqual(bibrecord._warning((1, '(field number(s): [2])')), ee)

    def test_empty_datafield(self):
        """ bibrecord - bad input no subfield """
        ws = bibrecord.CFG_BIBRECORD_WARNING_MSGS
        xml_error3 = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1=" " ind2=" ">
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe, John</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2=" ">
        <subfield code="a">On the foo and bar</subfield>
        </datafield>
        </record>
        """
        e = bibrecord.create_record(xml_error3, 1, 1)[2]
        ee = ''
        for i in e:
            if type(i).__name__ == 'str':
                if i.count(ws[8])>0:
                    ee = i
        self.assertEqual(bibrecord._warning((8, '(field number: 2)')), ee)

    def test_missing_tag(self):
        """bibrecord - bad input missing end \"tag\" """
        ws = bibrecord.CFG_BIBRECORD_WARNING_MSGS
        xml_error4 = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe, John</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2=" ">
        <subfield code="a">On the foo and bar</subfield>
        </record>
        """
        e = bibrecord.create_record(xml_error4, 1, 1)[2]
        ee = ''
        for i in e:
            if type(i).__name__ == 'str':
                if i.count(ws[99])>0:
                    ee = i
        self.assertEqual(bibrecord._warning((99, '(Tagname : datafield)')), ee)

class BibRecordAccentedUnicodeLettersTest(InvenioTestCase):
    """ bibrecord - testing accented UTF-8 letters """

    def setUp(self):
        """Initialize stuff"""
        self.xml_example_record = """<record>
  <controlfield tag="001">33</controlfield>
  <datafield tag="041" ind1=" " ind2=" ">
    <subfield code="a">eng</subfield>
  </datafield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Döè1, John</subfield>
  </datafield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Doe2, J>ohn</subfield>
    <subfield code="b">editor</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2="1">
    <subfield code="a">Пушкин</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2="2">
    <subfield code="a">On the foo and bar2</subfield>
  </datafield>
</record>"""
        self.rec = bibrecord.create_record(self.xml_example_record, 1, 1)[0]

    def test_accented_unicode_characters(self):
        """bibrecord - accented Unicode letters"""
        self.assertEqual(self.xml_example_record,
                         bibrecord.record_xml_output(self.rec))
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "100", " ", " "),
                         [([('a', 'Döè1, John')], " ", " ", "", 3), ([('a', 'Doe2, J>ohn'), ('b', 'editor')], " ", " ", "", 4)])
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "245", " ", "1"),
                         [([('a', 'Пушкин')], " ", '1', "", 5)])

class BibRecordGettingFieldValuesTest(InvenioTestCase):
    """ bibrecord - testing for getting field/subfield values """

    def setUp(self):
        """Initialize stuff"""
        xml_example_record = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe1, John</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe2, John</subfield>
        <subfield code="b">editor</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="1">
        <subfield code="a">On the foo and bar1</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="2">
        <subfield code="a">On the foo and bar2</subfield>
        </datafield>
        <datafield tag="700" ind1=" " ind2="2">
        <subfield code="a">Penrose, Roger</subfield>
        <subfield code="u">University College London</subfield>
        </datafield>
        <datafield tag="700" ind1=" " ind2="2">
        <subfield code="a">Messi, Lionel</subfield>
        <subfield code="u">FC Barcelona</subfield>
        </datafield>
        </record>
        """
        self.rec = bibrecord.create_record(xml_example_record, 1, 1)[0]

    def test_get_field_instances(self):
        """bibrecord - getting field instances"""
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "100", " ", " "),
                         [([('a', 'Doe1, John')], " ", " ", "", 3), ([('a', 'Doe2, John'), ('b', 'editor')], " ", " ", "", 4)])
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "", " ", " "),
                        [('245', [([('a', 'On the foo and bar1')], " ", '1', "", 5), ([('a', 'On the foo and bar2')], " ", '2', "", 6)]), ('001', [([], " ", " ", '33', 1)]), ('700', [([('a', 'Penrose, Roger'), ('u', "University College London")], ' ', '2', '', 7), ([('a', 'Messi, Lionel'), ('u', 'FC Barcelona')], ' ', '2', '', 8)]), ('100', [([('a', 'Doe1, John')], " ", " ", "", 3), ([('a', 'Doe2, John'), ('b', 'editor')], " ", " ", "", 4)]), ('041', [([('a', 'eng')], " ", " ", "", 2)]),])

    def test_get_field_values(self):
        """bibrecord - getting field values"""
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", " ", " ", "a"),
                         ['Doe1, John', 'Doe2, John'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", " ", " ", "b"),
                         ['editor'])

    def test_get_field_value(self):
        """bibrecord - getting first field value"""
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "100", " ", " ", "a"),
                         'Doe1, John')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "100", " ", " ", "b"),
                         'editor')

    def test_get_subfield_values(self):
        """bibrecord - getting subfield values"""
        fi1, fi2 = bibrecord.record_get_field_instances(self.rec, "100", " ", " ")
        self.assertEqual(bibrecord.field_get_subfield_values(fi1, "b"), [])
        self.assertEqual(bibrecord.field_get_subfield_values(fi2, "b"), ["editor"])

    def test_filter_field(self):
        """bibrecord - filter field instances"""
        field_instances = bibrecord.record_get_field_instances(self.rec, "700", "%", "%")
        out = bibrecord.filter_field_instances(field_instances, "u", "University College London", 'e')
        self.assertEqual(out, [([('a', 'Penrose, Roger'), ('u', "University College London")], ' ', '2', '', 7)])
        out = bibrecord.filter_field_instances(field_instances, "u", "Bar", "s")
        self.assertEqual(out, [([('a', 'Messi, Lionel'), ('u', 'FC Barcelona')], ' ', '2', '', 8)])
        out = bibrecord.filter_field_instances(field_instances, "u", "on", "s")
        self.assertEqual(out, [([('a', 'Penrose, Roger'), ('u', "University College London")], ' ', '2', '', 7),
                               ([('a', 'Messi, Lionel'), ('u', 'FC Barcelona')], ' ', '2', '', 8)])
        out = bibrecord.filter_field_instances(field_instances, "u", r".*\scoll", "r")
        self.assertEqual(out,[])
        out = bibrecord.filter_field_instances(field_instances, "u", r"[FC]{2}\s.*", "r")
        self.assertEqual(out, [([('a', 'Messi, Lionel'), ('u', 'FC Barcelona')], ' ', '2', '', 8)])


class BibRecordGettingFieldValuesViaWildcardsTest(InvenioTestCase):
    """ bibrecord - testing for getting field/subfield values via wildcards """

    def setUp(self):
        """Initialize stuff"""
        xml_example_record = """
        <record>
        <controlfield tag="001">1</controlfield>
        <datafield tag="100" ind1="C" ind2="5">
        <subfield code="a">val1</subfield>
        </datafield>
        <datafield tag="555" ind1="A" ind2="B">
        <subfield code="a">val2</subfield>
        </datafield>
        <datafield tag="555" ind1="A" ind2=" ">
        <subfield code="a">val3</subfield>
        </datafield>
        <datafield tag="555" ind1=" " ind2=" ">
        <subfield code="a">val4a</subfield>
        <subfield code="b">val4b</subfield>
        </datafield>
        <datafield tag="555" ind1=" " ind2="B">
        <subfield code="a">val5</subfield>
        </datafield>
        <datafield tag="556" ind1="A" ind2="C">
        <subfield code="a">val6</subfield>
        </datafield>
        <datafield tag="556" ind1="A" ind2=" ">
        <subfield code="a">val7a</subfield>
        <subfield code="b">val7b</subfield>
        </datafield>
        </record>
        """
        self.rec = bibrecord.create_record(xml_example_record, 1, 1)[0]

    def test_get_field_instances_via_wildcard(self):
        """bibrecord - getting field instances via wildcards"""
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "100", " ", " "),
                         [])
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "100", "%", " "),
                         [])
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "100", "%", "%"),
                         [([('a', 'val1')], 'C', '5', "", 2)])
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "55%", "A", "%"),
                         [([('a', 'val2')], 'A', 'B', "", 3),
                          ([('a', 'val3')], 'A', " ", "", 4),
                          ([('a', 'val6')], 'A', 'C', "", 7),
                          ([('a', 'val7a'), ('b', 'val7b')], 'A', " ", "", 8)])
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "55%", "A", " "),
                         [([('a', 'val3')], 'A', " ", "", 4),
                          ([('a', 'val7a'), ('b', 'val7b')], 'A', " ", "", 8)])
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "556", "A", " "),
                         [([('a', 'val7a'), ('b', 'val7b')], 'A', " ", "", 8)])

    def test_get_field_values_via_wildcard(self):
        """bibrecord - getting field values via wildcards"""
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", " ", " ", " "),
                         [])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", "%", " ", " "),
                         [])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", " ", "%", " "),
                         [])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", "%", "%", " "),
                         [])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", "%", "%", "z"),
                         [])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", " ", " ", "%"),
                         [])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", " ", " ", "a"),
                        [])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", "%", " ", "a"),
                         [])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", "%", "%", "a"),
                         ['val1'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", "%", "%", "%"),
                         ['val1'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "55%", "A", "%", "a"),
                         ['val2', 'val3', 'val6', 'val7a'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "55%", "A", " ", "a"),
                         ['val3', 'val7a'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "556", "A", " ", "a"),
                         ['val7a'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "555", " ", " ", " "),
                         [])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "555", " ", " ", "z"),
                         [])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "555", " ", " ", "%"),
                         ['val4a', 'val4b'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "55%", " ", " ", "b"),
                         ['val4b'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "55%", "%", "%", "b"),
                         ['val4b', 'val7b'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "55%", "A", " ", "b"),
                         ['val7b'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "55%", "A", "%", "b"),
                         ['val7b'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "55%", "A", " ", "a"),
                         ['val3', 'val7a'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "55%", "A", "%", "a"),
                         ['val2', 'val3', 'val6', 'val7a'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "55%", "%", "%", "a"),
                         ['val2', 'val3', 'val4a', 'val5', 'val6', 'val7a'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "55%", " ", " ", "a"),
                         ['val4a'])

    def test_get_field_values_filtering_exact(self):
        """bibrecord - getting field values and exact filtering"""
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "556", "%", "%", "%", 'a', 'val7a'),
                         ['val7a', 'val7b'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "556", "%", "%", "a", 'a', 'val7a'),
                         ['val7a'])

    def test_get_field_values_filtering_substring(self):
        """bibrecord - getting field values and substring filtering"""
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "556", "%", "%", "%", 'a', '7a', 's'),
                         ['val7a', 'val7b'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "556", "%", "%", "b", 'a', '7a', 's'),
                         ['val7b'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "55%", "%", "%", "%", 'b', 'val', 's'),
                         ['val4a', 'val4b', 'val7a', 'val7b'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "55%", "%", "%", " ", 'b', 'val', 's'),
                         [])

    def test_get_field_values_filtering_regexp(self):
        """bibrecord - getting field values and regexp filtering"""
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "55%", "%", "%", "%", 'b', r'al', 'r'),
                         [])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "55%", "%", "%", "%", 'a', r'.*al[6,7]', 'r'),
                         ['val6', 'val7a', 'val7b'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "55%", "%", "%", "a", 'a', r'.*al[6,7]', 'r'),
                         ['val6', 'val7a'])

    def test_get_field_value_via_wildcard(self):
        """bibrecord - getting first field value via wildcards"""
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "100", " ", " ", " "),
                         '')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "100", "%", " ", " "),
                         '')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "100", " ", "%", " "),
                         '')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "100", "%", "%", " "),
                         '')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "100", " ", " ", "%"),
                         '')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "100", " ", " ", "a"),
                         '')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "100", "%", " ", "a"),
                         '')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "100", "%", "%", "a"),
                         'val1')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "100", "%", "%", "%"),
                         'val1')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "55%", "A", "%", "a"),
                         'val2')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "55%", "A", " ", "a"),
                         'val3')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "556", "A", " ", "a"),
                         'val7a')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "555", " ", " ", " "),
                         '')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "555", " ", " ", "%"),
                         'val4a')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "55%", " ", " ", "b"),
                         'val4b')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "55%", "%", "%", "b"),
                         'val4b')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "55%", "A", " ", "b"),
                         'val7b')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "55%", "A", "%", "b"),
                         'val7b')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "55%", "A", " ", "a"),
                         'val3')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "55%", "A", "%", "a"),
                         'val2')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "55%", "%", "%", "a"),
                         'val2')
        self.assertEqual(bibrecord.record_get_field_value(self.rec, "55%", " ", " ", "a"),
                         'val4a')

class BibRecordAddFieldTest(InvenioTestCase):
    """ bibrecord - testing adding field """

    def setUp(self):
        """Initialize stuff"""
        xml_example_record = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe1, John</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe2, John</subfield>
        <subfield code="b">editor</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="1">
        <subfield code="a">On the foo and bar1</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="2">
        <subfield code="a">On the foo and bar2</subfield>
        </datafield>
        </record>
        """
        self.rec = bibrecord.create_record(xml_example_record, 1, 1)[0]

    def test_add_controlfield(self):
        """bibrecord - adding controlfield"""
        field_position_global_1 = bibrecord.record_add_field(self.rec, "003",
                                                    controlfield_value="SzGeCERN")
        field_position_global_2 = bibrecord.record_add_field(self.rec, "004",
                                                    controlfield_value="Test")
        self.assertEqual(field_position_global_1, 2)
        self.assertEqual(field_position_global_2, 3)
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "003", " ", " ", ""),
                         ['SzGeCERN'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "004", " ", " ", ""),
                         ['Test'])

    def test_add_datafield(self):
        """bibrecord - adding datafield"""
        field_position_global_1 = bibrecord.record_add_field(self.rec, "100",
                                                    subfields=[('a', 'Doe3, John')])
        field_position_global_2 = bibrecord.record_add_field(self.rec, "100",
                                                    subfields= [('a', 'Doe4, John'), ('b', 'editor')])
        self.assertEqual(field_position_global_1, 5)
        self.assertEqual(field_position_global_2, 6)
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", " ", " ", "a"),
                         ['Doe1, John', 'Doe2, John', 'Doe3, John', 'Doe4, John'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", " ", " ", "b"),
                         ['editor', 'editor'])

    def test_add_controlfield_on_desired_position(self):
        """bibrecord - adding controlfield on desired position"""
        field_position_global_1 = bibrecord.record_add_field(self.rec, "005",
                                                    controlfield_value="Foo",
                                                    field_position_global=0)
        field_position_global_2 = bibrecord.record_add_field(self.rec, "006",
                                                    controlfield_value="Bar",
                                                    field_position_global=0)
        self.assertEqual(field_position_global_1, 7)
        self.assertEqual(field_position_global_2, 8)

    def test_add_datafield_on_desired_position_field_position_global(self):
        """bibrecord - adding datafield on desired global field position"""
        field_position_global_1 = bibrecord.record_add_field(self.rec, "100",
            subfields=[('a', 'Doe3, John')], field_position_global=0)
        field_position_global_2 = bibrecord.record_add_field(self.rec, "100",
            subfields=[('a', 'Doe4, John'), ('b', 'editor')], field_position_global=0)
        self.assertEqual(field_position_global_1, 3)
        self.assertEqual(field_position_global_2, 3)

    def test_add_datafield_on_desired_position_field_position_local(self):
        """bibrecord - adding datafield on desired local field position"""
        field_position_global_1 = bibrecord.record_add_field(self.rec, "100",
             subfields=[('a', 'Doe3, John')], field_position_local=0)
        field_position_global_2 = bibrecord.record_add_field(self.rec, "100",
             subfields=[('a', 'Doe4, John'), ('b', 'editor')],
             field_position_local=2)
        self.assertEqual(field_position_global_1, 3)
        self.assertEqual(field_position_global_2, 5)

class BibRecordManageMultipleFieldsTest(InvenioTestCase):
    """ bibrecord - testing the management of multiple fields """

    def setUp(self):
        """Initialize stuff"""
        xml_example_record = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="245" ind1=" " ind2=" ">
        <subfield code="a">subfield1</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2=" ">
        <subfield code="a">subfield2</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2=" ">
        <subfield code="a">subfield3</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2=" ">
        <subfield code="a">subfield4</subfield>
        </datafield>
        </record>
        """
        self.rec = bibrecord.create_record(xml_example_record, 1, 1)[0]

    def test_delete_multiple_datafields(self):
        """bibrecord - deleting multiple datafields"""
        self.fields = bibrecord.record_delete_fields(self.rec, '245', [1, 2])
        self.assertEqual(self.fields[0],
            ([('a', 'subfield2')], ' ', ' ', '', 3))
        self.assertEqual(self.fields[1],
            ([('a', 'subfield3')], ' ', ' ', '', 4))

    def test_add_multiple_datafields_default_index(self):
        """bibrecord - adding multiple fields with the default index"""
        fields = [([('a', 'subfield5')], ' ', ' ', '', 4),
            ([('a', 'subfield6')], ' ', ' ', '', 19)]
        index = bibrecord.record_add_fields(self.rec, '245', fields)
        self.assertEqual(index, None)
        self.assertEqual(self.rec['245'][-2],
            ([('a', 'subfield5')], ' ', ' ', '', 6))
        self.assertEqual(self.rec['245'][-1],
            ([('a', 'subfield6')], ' ', ' ', '', 7))

    def test_add_multiple_datafields_with_index(self):
        """bibrecord - adding multiple fields with an index"""
        fields = [([('a', 'subfield5')], ' ', ' ', '', 4),
            ([('a', 'subfield6')], ' ', ' ', '', 19)]
        index = bibrecord.record_add_fields(self.rec, '245', fields,
            field_position_local=0)
        self.assertEqual(index, 0)
        self.assertEqual(self.rec['245'][0],
            ([('a', 'subfield5')], ' ', ' ', '', 2))
        self.assertEqual(self.rec['245'][1],
            ([('a', 'subfield6')], ' ', ' ', '', 3))
        self.assertEqual(self.rec['245'][2],
            ([('a', 'subfield1')], ' ', ' ', '', 4))

    def test_move_multiple_fields(self):
        """bibrecord - move multiple fields"""
        bibrecord.record_move_fields(self.rec, '245', [1, 3])
        self.assertEqual(self.rec['245'][0],
            ([('a', 'subfield1')], ' ', ' ', '', 2))
        self.assertEqual(self.rec['245'][1],
            ([('a', 'subfield3')], ' ', ' ', '', 4))
        self.assertEqual(self.rec['245'][2],
            ([('a', 'subfield2')], ' ', ' ', '', 5))
        self.assertEqual(self.rec['245'][3],
            ([('a', 'subfield4')], ' ', ' ', '', 6))

class BibRecordDeleteFieldTest(InvenioTestCase):
    """ bibrecord - testing field deletion """

    def setUp(self):
        """Initialize stuff"""
        xml_example_record = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe1, John</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe2, John</subfield>
        <subfield code="b">editor</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="1">
        <subfield code="a">On the foo and bar1</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="2">
        <subfield code="a">On the foo and bar2</subfield>
        </datafield>
        </record>
        """
        self.rec = bibrecord.create_record(xml_example_record, 1, 1)[0]

        xml_example_record_empty = """
        <record>
        </record>
        """
        self.rec_empty = bibrecord.create_record(xml_example_record_empty, 1, 1)[0]

    def test_delete_controlfield(self):
        """bibrecord - deleting controlfield"""
        bibrecord.record_delete_field(self.rec, "001", " ", " ")
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "001", " ", " ", " "),
                         [])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", " ", " ", "b"),
                         ['editor'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "245", " ", "2", "a"),
                         ['On the foo and bar2'])

    def test_delete_datafield(self):
        """bibrecord - deleting datafield"""
        bibrecord.record_delete_field(self.rec, "100", " ", " ")
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "001", " ", " ", ""),
                         ['33'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", " ", " ", "b"),
                         [])
        bibrecord.record_delete_field(self.rec, "245", " ", " ")
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "245", " ", "1", "a"),
                         ['On the foo and bar1'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "245", " ", "2", "a"),
                         ['On the foo and bar2'])
        bibrecord.record_delete_field(self.rec, "245", " ", "2")
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "245", " ", "1", "a"),
                         ['On the foo and bar1'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "245", " ", "2", "a"),
                         [])

    def test_add_delete_add_field_to_empty_record(self):
        """bibrecord - adding, deleting, and adding back a field to an empty record"""
        field_position_global_1 = bibrecord.record_add_field(self.rec_empty, "003",
                                                    controlfield_value="SzGeCERN")
        self.assertEqual(field_position_global_1, 1)
        self.assertEqual(bibrecord.record_get_field_values(self.rec_empty, "003", " ", " ", ""),
                         ['SzGeCERN'])
        bibrecord.record_delete_field(self.rec_empty, "003", " ", " ")
        self.assertEqual(bibrecord.record_get_field_values(self.rec_empty, "003", " ", " ", ""),
                         [])
        field_position_global_1 = bibrecord.record_add_field(self.rec_empty, "003",
                                                    controlfield_value="SzGeCERN2")
        self.assertEqual(field_position_global_1, 1)
        self.assertEqual(bibrecord.record_get_field_values(self.rec_empty, "003", " ", " ", ""),
                         ['SzGeCERN2'])


class BibRecordDeleteFieldFromTest(InvenioTestCase):
    """ bibrecord - testing field deletion from position"""

    def setUp(self):
        """Initialize stuff"""
        xml_example_record = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe1, John</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe2, John</subfield>
        <subfield code="b">editor</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="1">
        <subfield code="a">On the foo and bar1</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="2">
        <subfield code="a">On the foo and bar2</subfield>
        </datafield>
        </record>
        """
        self.rec = bibrecord.create_record(xml_example_record, 1, 1)[0]

    def test_delete_field_from(self):
        """bibrecord - deleting field from position"""
        bibrecord.record_delete_field(self.rec, "100", field_position_global=4)
        self.assertEqual(self.rec['100'], [([('a', 'Doe1, John')], ' ', ' ', '', 3)])
        bibrecord.record_delete_field(self.rec, "100", field_position_global=3)
        self.failIf(self.rec.has_key('100'))
        bibrecord.record_delete_field(self.rec, "001", field_position_global=1)
        bibrecord.record_delete_field(self.rec, "245", field_position_global=6)
        self.failIf(self.rec.has_key('001'))
        self.assertEqual(self.rec['245'], [([('a', 'On the foo and bar1')], ' ', '1', '', 5)])

        # Some crash tests
        bibrecord.record_delete_field(self.rec, '999', field_position_global=1)
        bibrecord.record_delete_field(self.rec, '245', field_position_global=999)


class BibRecordAddSubfieldIntoTest(InvenioTestCase):
    """ bibrecord - testing subfield addition """

    def setUp(self):
        """Initialize stuff"""
        xml_example_record = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe2, John</subfield>
        <subfield code="b">editor</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="1">
        <subfield code="a">On the foo and bar1</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="2">
        <subfield code="a">On the foo and bar2</subfield>
        </datafield>
        </record>
        """
        self.rec = bibrecord.create_record(xml_example_record, 1, 1)[0]

    def test_add_subfield_into(self):
        """bibrecord - adding subfield into position"""
        bibrecord.record_add_subfield_into(self.rec, "100", "b", "Samekniv",
            field_position_global=3)
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", " ", " ", "b"),
                         ['editor', 'Samekniv'])
        bibrecord.record_add_subfield_into(self.rec, "245", "x", "Elgokse",
            field_position_global=4)
        bibrecord.record_add_subfield_into(self.rec, "245", "x", "Fiskeflue",
            subfield_position=0, field_position_global=4)
        bibrecord.record_add_subfield_into(self.rec, "245", "z", "Ulriken",
            subfield_position=2, field_position_global=4)
        bibrecord.record_add_subfield_into(self.rec, "245", "z",
            "Stortinget", subfield_position=999, field_position_global=4)
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "245", " ", "1", "%"),
                         ['Fiskeflue', 'On the foo and bar1', 'Ulriken', 'Elgokse', 'Stortinget'])
        # Some crash tests
        self.assertRaises(bibrecord.InvenioBibRecordFieldError,
            bibrecord.record_add_subfield_into, self.rec, "187", "x", "Crash",
            field_position_global=1)
        self.assertRaises(bibrecord.InvenioBibRecordFieldError,
            bibrecord.record_add_subfield_into, self.rec, "245", "x", "Crash",
            field_position_global=999)


class BibRecordModifyControlfieldTest(InvenioTestCase):
    """ bibrecord - testing controlfield modification """

    def setUp(self):
        """Initialize stuff"""
        xml_example_record = """
        <record>
        <controlfield tag="001">33</controlfield>
        <controlfield tag="005">A Foo's Tale</controlfield>
        <controlfield tag="008">Skeech Skeech</controlfield>
        <controlfield tag="008">Whoop Whoop</controlfield>
        <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="2">
        <subfield code="a">On the foo and bar2</subfield>
        </datafield>
        </record>
        """
        self.rec = bibrecord.create_record(xml_example_record, 1, 1)[0]

    def test_modify_controlfield(self):
        """bibrecord - modify controlfield"""
        bibrecord.record_modify_controlfield(self.rec, "001", "34",
            field_position_global=1)
        bibrecord.record_modify_controlfield(self.rec, "008", "Foo Foo",
            field_position_global=3)
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "001"), ["34"])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "005"), ["A Foo's Tale"])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "008"), ["Foo Foo", "Whoop Whoop"])
        # Some crash tests
        self.assertRaises(bibrecord.InvenioBibRecordFieldError,
            bibrecord.record_modify_controlfield, self.rec, "187", "Crash",
            field_position_global=1)
        self.assertRaises(bibrecord.InvenioBibRecordFieldError,
            bibrecord.record_modify_controlfield, self.rec, "008", "Test",
            field_position_global=10)
        self.assertRaises(bibrecord.InvenioBibRecordFieldError,
            bibrecord.record_modify_controlfield, self.rec, "245", "Burn",
            field_position_global=5)
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "245", " ", "2", "%"),
                         ["On the foo and bar2"])


class BibRecordModifySubfieldTest(InvenioTestCase):
    """ bibrecord - testing subfield modification """

    def setUp(self):
        """Initialize stuff"""
        xml_example_record = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe2, John</subfield>
        <subfield code="b">editor</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="1">
        <subfield code="a">On the foo and bar1</subfield>
        <subfield code="b">On writing unit tests</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="2">
        <subfield code="a">On the foo and bar2</subfield>
        </datafield>
        </record>
        """
        self.rec = bibrecord.create_record(xml_example_record, 1, 1)[0]

    def test_modify_subfield(self):
        """bibrecord - modify subfield"""
        bibrecord.record_modify_subfield(self.rec, "245", "a", "Holmenkollen",
            0, field_position_global=4)
        bibrecord.record_modify_subfield(self.rec, "245", "x", "Brann", 1,
            field_position_global=4)
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "245", " ", "1", "%"),
                         ['Holmenkollen', 'Brann'])
        # Some crash tests
        self.assertRaises(bibrecord.InvenioBibRecordFieldError,
            bibrecord.record_modify_subfield, self.rec, "187", "x", "Crash", 0,
            field_position_global=1)
        self.assertRaises(bibrecord.InvenioBibRecordFieldError,
            bibrecord.record_modify_subfield, self.rec, "245", "x", "Burn", 1,
            field_position_global=999)
        self.assertRaises(bibrecord.InvenioBibRecordFieldError,
            bibrecord.record_modify_subfield, self.rec, "245", "a", "Burn",
            999, field_position_global=4)

class BibRecordDeleteSubfieldFromTest(InvenioTestCase):
    """ bibrecord - testing subfield deletion """

    def setUp(self):
        """Initialize stuff"""
        xml_example_record = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe2, John</subfield>
        <subfield code="b">editor</subfield>
        <subfield code="z">Skal vi danse?</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="1">
        <subfield code="a">On the foo and bar1</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="2">
        <subfield code="a">On the foo and bar2</subfield>
        </datafield>
        </record>
        """
        self.rec = bibrecord.create_record(xml_example_record, 1, 1)[0]

    def test_delete_subfield_from(self):
        """bibrecord - delete subfield from position"""
        bibrecord.record_delete_subfield_from(self.rec, "100", 2,
            field_position_global=3)
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", " ", " ", "z"),
                         [])
        bibrecord.record_delete_subfield_from(self.rec, "100", 0,
            field_position_global=3)
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", " ", " ", "%"),
                         ['editor'])
        bibrecord.record_delete_subfield_from(self.rec, "100", 0,
            field_position_global=3)
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", " ", " ", "%"),
                         [])
        # Some crash tests
        self.assertRaises(bibrecord.InvenioBibRecordFieldError,
            bibrecord.record_delete_subfield_from, self.rec, "187", 0,
            field_position_global=1)
        self.assertRaises(bibrecord.InvenioBibRecordFieldError,
            bibrecord.record_delete_subfield_from, self.rec, "245", 0,
            field_position_global=999)
        self.assertRaises(bibrecord.InvenioBibRecordFieldError,
            bibrecord.record_delete_subfield_from, self.rec, "245", 999,
            field_position_global=4)


class BibRecordDeleteSubfieldTest(InvenioTestCase):
    """ bibrecord - testing subfield deletion """

    def setUp(self):
        """Initialize stuff"""
        self.xml_example_record = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1=" " ind2=" ">
            <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
            <subfield code="a">Doe2, John</subfield>
            <subfield code="b">editor</subfield>
            <subfield code="z">Skal vi danse?</subfield>
            <subfield code="a">Doe3, Zbigniew</subfield>
            <subfield code="d">Doe4, Joachim</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="1">
            <subfield code="a">On the foo and bar1</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="2">
            <subfield code="a">On the foo and bar2</subfield>
        </datafield>
        <datafield tag="246" ind1="1" ind2="2">
            <subfield code="c">On the foo and bar1</subfield>
        </datafield>
        <datafield tag="246" ind1="1" ind2="2">
            <subfield code="c">On the foo and bar2</subfield>
        </datafield>
        </record>
        """

    def test_simple_removals(self):
        """ bibrecord - delete subfield by its code"""
        # testing a simple removals where all the fields are removed
        rec = bibrecord.create_record(self.xml_example_record, 1, 1)[0]

        bibrecord.record_delete_subfield(rec, "041", "b") # nothing should change
        self.assertEqual(rec["041"][0][0], [("a", "eng")])
        bibrecord.record_delete_subfield(rec, "041", "a")
        self.assertEqual(rec["041"][0][0], [])

    def test_indices_important(self):
        """ bibrecord - delete subfield where indices are important"""
        rec = bibrecord.create_record(self.xml_example_record, 1, 1)[0]
        bibrecord.record_delete_subfield(rec, "245", "a", " ", "1")
        self.assertEqual(rec["245"][0][0], [])
        self.assertEqual(rec["245"][1][0], [("a", "On the foo and bar2")])
        bibrecord.record_delete_subfield(rec, "245", "a", " ", "2")
        self.assertEqual(rec["245"][1][0], [])

    def test_remove_some(self):
        """ bibrecord - delete subfield when some should be preserved and some removed"""
        rec = bibrecord.create_record(self.xml_example_record, 1, 1)[0]
        bibrecord.record_delete_subfield(rec, "100", "a", " ", " ")
        self.assertEqual(rec["100"][0][0], [("b", "editor"), ("z", "Skal vi danse?"), ("d", "Doe4, Joachim")])

    def test_more_fields(self):
        """ bibrecord - delete subfield where more fits criteria"""
        rec = bibrecord.create_record(self.xml_example_record, 1, 1)[0]
        bibrecord.record_delete_subfield(rec, "246", "c", "1", "2")
        self.assertEqual(rec["246"][1][0], [])
        self.assertEqual(rec["246"][0][0], [])

    def test_nonexisting_removals(self):
        """ bibrecord - delete subfield that does not exist """
        rec = bibrecord.create_record(self.xml_example_record, 1, 1)[0]
        # further preparation
        bibrecord.record_delete_subfield(rec, "100", "a", " ", " ")
        self.assertEqual(rec["100"][0][0], [("b", "editor"), ("z", "Skal vi danse?"), ("d", "Doe4, Joachim")])
        #the real tests begin
        #   1) removing the subfield from an empty list of subfields
        bibrecord.record_delete_subfield(rec, "246", "c", "1", "2")
        self.assertEqual(rec["246"][1][0], [])
        self.assertEqual(rec["246"][0][0], [])
        bibrecord.record_delete_subfield(rec, "246", "8", "1", "2")
        self.assertEqual(rec["246"][1][0], [])
        self.assertEqual(rec["246"][0][0], [])
        #   2) removing a subfield from a field that has some subfields but none has an appropriate code
        bibrecord.record_delete_subfield(rec, "100", "a", " ", " ")
        self.assertEqual(rec["100"][0][0], [("b", "editor"), ("z", "Skal vi danse?"), ("d", "Doe4, Joachim")])
        bibrecord.record_delete_subfield(rec, "100", "e", " ", " ")
        self.assertEqual(rec["100"][0][0], [("b", "editor"), ("z", "Skal vi danse?"), ("d", "Doe4, Joachim")])


class BibRecordMoveSubfieldTest(InvenioTestCase):
    """ bibrecord - testing subfield moving """

    def setUp(self):
        """Initialize stuff"""
        xml_example_record = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe2, John</subfield>
        <subfield code="b">editor</subfield>
        <subfield code="c">fisk</subfield>
        <subfield code="d">eple</subfield>
        <subfield code="e">hammer</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="1">
        <subfield code="a">On the foo and bar1</subfield>
        </datafield>
        </record>
        """
        self.rec = bibrecord.create_record(xml_example_record, 1, 1)[0]

    def test_move_subfield(self):
        """bibrecord - move subfields"""
        bibrecord.record_move_subfield(self.rec, "100", 2, 4,
            field_position_global=3)
        bibrecord.record_move_subfield(self.rec, "100", 1, 0,
            field_position_global=3)
        bibrecord.record_move_subfield(self.rec, "100", 2, 999,
            field_position_global=3)
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", " ", " ", "%"),
                         ['editor', 'Doe2, John', 'hammer', 'fisk', 'eple'])
        # Some crash tests
        self.assertRaises(bibrecord.InvenioBibRecordFieldError,
            bibrecord.record_move_subfield, self.rec, "187", 0, 1,
            field_position_global=3)
        self.assertRaises(bibrecord.InvenioBibRecordFieldError,
            bibrecord.record_move_subfield, self.rec, "100", 1, 0,
            field_position_global=999)
        self.assertRaises(bibrecord.InvenioBibRecordFieldError,
            bibrecord.record_move_subfield, self.rec, "100", 999, 0,
            field_position_global=3)


class BibRecordCompareSubfieldTest(InvenioTestCase):
    """ bibrecord -  """
    
    def setUp(self):
        """Initialize stuff"""
        xml_example_record = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe2, John</subfield>
        <subfield code="b">editor</subfield>
        <subfield code="c">fisk</subfield>
        <subfield code="d">eple</subfield>
        <subfield code="e">hammer</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2="1">
        <subfield code="a">On the foo and bar1</subfield>
        </datafield>
        </record>
        """
        self.rec = bibrecord.create_record(xml_example_record, 1, 1)[0]
        # For simplicity, create an alias of the function
        self._func = bibrecord.record_match_subfields

    def test_check_subfield_exists(self):
        self.assertEqual(self._func(self.rec, '100', sub_key='a'), 3)
        self.assertEqual(self._func(self.rec, '100', sub_key='e'), 3)
        self.assertFalse(self._func(self.rec, '245', sub_key='a'))
        self.assertEqual(self._func(self.rec, '245', ind2='1', sub_key='a'), 4)
        self.assertFalse(self._func(self.rec, '999', sub_key='x'))
        self.assertFalse(self._func(self.rec, '100', sub_key='x'))

    def test_check_subfield_values(self):
        self.assertEqual(self._func(self.rec, '100', sub_key='b',
            sub_value='editor'), 3)
        self.assertEqual(self._func(self.rec, '245', ind2='1', sub_key='a',
            sub_value='On the foo and bar1'), 4)
        self.assertEqual(self._func(self.rec, '100', sub_key='e',
            sub_value='ponies suck'), False)
        self.assertEqual(self._func(self.rec, '100', sub_key='c',
            sub_value='FISK'), False)
        self.assertEqual(self._func(self.rec, '100', sub_key='c',
            sub_value='FISK', case_sensitive=False), 3)

    def test_compare_subfields(self):
        self.assertEqual(self._func(self.rec, '100', sub_key='c',
            sub_value='fisk', sub_key2='d', sub_value2='eple'), 3)
        self.assertFalse(self._func(self.rec, '100', sub_key='c',
            sub_value='fisk', sub_key2='d', sub_value2='tom'))
        self.assertEqual(self._func(self.rec, '100', sub_key='c',
            sub_value='fiSk', sub_key2='d', sub_value2='Eple',
            case_sensitive=False), 3)

    def test_error_conditions(self):
        self.assertRaises(TypeError,
            self._func, self.rec, '100')
        self.assertRaises(TypeError,
            self._func, self.rec, '100', sub_key='a',
                sub_value='fiSk', sub_key2='d')


class BibRecordSpecialTagParsingTest(InvenioTestCase):
    """ bibrecord - parsing special tags (FMT, FFT)"""

    def setUp(self):
        """setting up example records"""
        self.xml_example_record_with_fmt = """
        <record>
         <controlfield tag="001">33</controlfield>
         <datafield tag="041" ind1=" " ind2=" ">
          <subfield code="a">eng</subfield>
         </datafield>
         <datafield tag="FMT" ind1=" " ind2=" ">
          <subfield code="f">HB</subfield>
          <subfield code="g">Let us see if this gets inserted well.</subfield>
         </datafield>
        </record>
        """
        self.xml_example_record_with_fft = """
        <record>
         <controlfield tag="001">33</controlfield>
         <datafield tag="041" ind1=" " ind2=" ">
          <subfield code="a">eng</subfield>
         </datafield>
         <datafield tag="FFT" ind1=" " ind2=" ">
          <subfield code="a">file:///foo.pdf</subfield>
          <subfield code="a">http://bar.com/baz.ps.gz</subfield>
         </datafield>
        </record>
        """
        self.xml_example_record_with_xyz = """
        <record>
         <controlfield tag="001">33</controlfield>
         <datafield tag="041" ind1=" " ind2=" ">
          <subfield code="a">eng</subfield>
         </datafield>
         <datafield tag="XYZ" ind1=" " ind2=" ">
          <subfield code="f">HB</subfield>
          <subfield code="g">Let us see if this gets inserted well.</subfield>
         </datafield>
        </record>
        """

    def test_parsing_file_containing_fmt_special_tag_with_correcting(self):
        """bibrecord - parsing special FMT tag, correcting on"""
        rec = bibrecord.create_record(self.xml_example_record_with_fmt, 1, 1)[0]
        self.assertEqual(rec,
                         {u'001': [([], " ", " ", '33', 1)],
                          'FMT': [([('f', 'HB'), ('g', 'Let us see if this gets inserted well.')], " ", " ", "", 3)],
                          '041': [([('a', 'eng')], " ", " ", "", 2)]})
        self.assertEqual(bibrecord.record_get_field_values(rec, "041", " ", " ", "a"),
                         ['eng'])
        self.assertEqual(bibrecord.record_get_field_values(rec, "FMT", " ", " ", "f"),
                         ['HB'])
        self.assertEqual(bibrecord.record_get_field_values(rec, "FMT", " ", " ", "g"),
                         ['Let us see if this gets inserted well.'])

    def test_parsing_file_containing_fmt_special_tag_without_correcting(self):
        """bibrecord - parsing special FMT tag, correcting off"""
        rec = bibrecord.create_record(self.xml_example_record_with_fmt, 1, 0)[0]
        self.assertEqual(rec,
                         {u'001': [([], " ", " ", '33', 1)],
                          'FMT': [([('f', 'HB'), ('g', 'Let us see if this gets inserted well.')], " ", " ", "", 3)],
                          '041': [([('a', 'eng')], " ", " ", "", 2)]})
        self.assertEqual(bibrecord.record_get_field_values(rec, "041", " ", " ", "a"),
                         ['eng'])
        self.assertEqual(bibrecord.record_get_field_values(rec, "FMT", " ", " ", "f"),
                         ['HB'])
        self.assertEqual(bibrecord.record_get_field_values(rec, "FMT", " ", " ", "g"),
                         ['Let us see if this gets inserted well.'])

    def test_parsing_file_containing_fft_special_tag_with_correcting(self):
        """bibrecord - parsing special FFT tag, correcting on"""
        rec = bibrecord.create_record(self.xml_example_record_with_fft, 1, 1)[0]
        self.assertEqual(rec,
                         {u'001': [([], " ", " ", '33', 1)],
                          'FFT': [([('a', 'file:///foo.pdf'), ('a', 'http://bar.com/baz.ps.gz')], " ", " ", "", 3)],
                          '041': [([('a', 'eng')], " ", " ", "", 2)]})
        self.assertEqual(bibrecord.record_get_field_values(rec, "041", " ", " ", "a"),
                         ['eng'])
        self.assertEqual(bibrecord.record_get_field_values(rec, "FFT", " ", " ", "a"),
                         ['file:///foo.pdf', 'http://bar.com/baz.ps.gz'])

    def test_parsing_file_containing_fft_special_tag_without_correcting(self):
        """bibrecord - parsing special FFT tag, correcting off"""
        rec = bibrecord.create_record(self.xml_example_record_with_fft, 1, 0)[0]
        self.assertEqual(rec,
                         {u'001': [([], " ", " ", '33', 1)],
                          'FFT': [([('a', 'file:///foo.pdf'), ('a', 'http://bar.com/baz.ps.gz')], " ", " ", "", 3)],
                          '041': [([('a', 'eng')], " ", " ", "", 2)]})
        self.assertEqual(bibrecord.record_get_field_values(rec, "041", " ", " ", "a"),
                         ['eng'])
        self.assertEqual(bibrecord.record_get_field_values(rec, "FFT", " ", " ", "a"),
                         ['file:///foo.pdf', 'http://bar.com/baz.ps.gz'])

    def test_parsing_file_containing_xyz_special_tag_with_correcting(self):
        """bibrecord - parsing unrecognized special XYZ tag, correcting on"""
        # XYZ should not get accepted when correcting is on; should get changed to 000
        rec = bibrecord.create_record(self.xml_example_record_with_xyz, 1, 1)[0]
        self.assertEqual(rec,
                         {u'001': [([], " ", " ", '33', 1)],
                          '000': [([('f', 'HB'), ('g', 'Let us see if this gets inserted well.')], " ", " ", "", 3)],
                          '041': [([('a', 'eng')], " ", " ", "", 2)]})
        self.assertEqual(bibrecord.record_get_field_values(rec, "041", " ", " ", "a"),
                         ['eng'])
        self.assertEqual(bibrecord.record_get_field_values(rec, "XYZ", " ", " ", "f"),
                         [])
        self.assertEqual(bibrecord.record_get_field_values(rec, "XYZ", " ", " ", "g"),
                         [])
        self.assertEqual(bibrecord.record_get_field_values(rec, "000", " ", " ", "f"),
                         ['HB'])
        self.assertEqual(bibrecord.record_get_field_values(rec, "000", " ", " ", "g"),
                         ['Let us see if this gets inserted well.'])

    def test_parsing_file_containing_xyz_special_tag_without_correcting(self):
        """bibrecord - parsing unrecognized special XYZ tag, correcting off"""
        # XYZ should get accepted without correcting
        rec = bibrecord.create_record(self.xml_example_record_with_xyz, 1, 0)[0]
        self.assertEqual(rec,
                         {u'001': [([], " ", " ", '33', 1)],
                          'XYZ': [([('f', 'HB'), ('g', 'Let us see if this gets inserted well.')], " ", " ", "", 3)],
                          '041': [([('a', 'eng')], " ", " ", "", 2)]})
        self.assertEqual(bibrecord.record_get_field_values(rec, "041", " ", " ", "a"),
                         ['eng'])
        self.assertEqual(bibrecord.record_get_field_values(rec, "XYZ", " ", " ", "f"),
                         ['HB'])
        self.assertEqual(bibrecord.record_get_field_values(rec, "XYZ", " ", " ", "g"),
                         ['Let us see if this gets inserted well.'])


class BibRecordPrintingTest(InvenioTestCase):
    """ bibrecord - testing for printing record """

    def setUp(self):
        """Initialize stuff"""
        self.xml_example_record = """
        <record>
        <controlfield tag="001">81</controlfield>
        <datafield tag="037" ind1=" " ind2=" ">
        <subfield code="a">TEST-ARTICLE-2006-001</subfield>
        </datafield>
        <datafield tag="037" ind1=" " ind2=" ">
        <subfield code="a">ARTICLE-2006-001</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2=" ">
        <subfield code="a">Test ti</subfield>
        </datafield>
        </record>"""

        self.xml_example_record_short = """
        <record>
        <controlfield tag="001">81</controlfield>
        <datafield tag="037" ind1=" " ind2=" ">
        <subfield code="a">TEST-ARTICLE-2006-001</subfield>
        </datafield>
        <datafield tag="037" ind1=" " ind2=" ">
        <subfield code="a">ARTICLE-2006-001</subfield>
        </datafield>
        </record>"""

        self.xml_example_multi_records = """
        <record>
        <controlfield tag="001">81</controlfield>
        <datafield tag="037" ind1=" " ind2=" ">
        <subfield code="a">TEST-ARTICLE-2006-001</subfield>
        </datafield>
        <datafield tag="037" ind1=" " ind2=" ">
        <subfield code="a">ARTICLE-2006-001</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2=" ">
        <subfield code="a">Test ti</subfield>
        </datafield>
        </record>
        <record>
        <controlfield tag="001">82</controlfield>
        <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Author, t</subfield>
        </datafield>
        </record>"""

        self.xml_example_multi_records_short = """
        <record>
        <controlfield tag="001">81</controlfield>
        <datafield tag="037" ind1=" " ind2=" ">
        <subfield code="a">TEST-ARTICLE-2006-001</subfield>
        </datafield>
        <datafield tag="037" ind1=" " ind2=" ">
        <subfield code="a">ARTICLE-2006-001</subfield>
        </datafield>
        </record>
        <record>
        <controlfield tag="001">82</controlfield>
        </record>"""

    def test_record_xml_output(self):
        """bibrecord - xml output"""
        rec = bibrecord.create_record(self.xml_example_record, 1, 1)[0]
        rec_short = bibrecord.create_record(self.xml_example_record_short, 1, 1)[0]
        self.assertEqual(bibrecord.create_record(bibrecord.record_xml_output(rec, tags=[]), 1, 1)[0], rec)
        self.assertEqual(bibrecord.create_record(bibrecord.record_xml_output(rec, tags=["001", "037"]), 1, 1)[0], rec_short)
        self.assertEqual(bibrecord.create_record(bibrecord.record_xml_output(rec, tags=["037"]), 1, 1)[0], rec_short)

class BibRecordCreateFieldTest(InvenioTestCase):
    """ bibrecord - testing for creating field """

    def test_create_valid_field(self):
        """bibrecord - create and check a valid field"""
        bibrecord.create_field()
        bibrecord.create_field([('a', 'testa'), ('b', 'testb')], '2', 'n',
            'controlfield', 15)

    def test_invalid_field_raises_exception(self):
        """bibrecord - exception raised when creating an invalid field"""
        # Invalid subfields.
        self.assertRaises(bibrecord_config.InvenioBibRecordFieldError,
            bibrecord.create_field, 'subfields', '1', '2', 'controlfield', 10)
        self.assertRaises(bibrecord_config.InvenioBibRecordFieldError,
            bibrecord.create_field, ('1', 'value'), '1', '2', 'controlfield', 10)
        self.assertRaises(bibrecord_config.InvenioBibRecordFieldError,
            bibrecord.create_field, [('value')], '1', '2', 'controlfield', 10)
        self.assertRaises(bibrecord_config.InvenioBibRecordFieldError,
            bibrecord.create_field, [('1', 'value', '2')], '1', '2', 'controlfield', 10)
        # Invalid indicators.
        self.assertRaises(bibrecord_config.InvenioBibRecordFieldError,
            bibrecord.create_field, [], 1, '2', 'controlfield', 10)
        self.assertRaises(bibrecord_config.InvenioBibRecordFieldError,
            bibrecord.create_field, [], '1', 2, 'controlfield', 10)
        # Invalid controlfield value
        self.assertRaises(bibrecord_config.InvenioBibRecordFieldError,
            bibrecord.create_field, [], '1', '2', 13, 10)
        # Invalid global position
        self.assertRaises(bibrecord_config.InvenioBibRecordFieldError,
            bibrecord.create_field, [], '1', '2', 'controlfield', 'position')

    def test_compare_fields(self):
        """bibrecord - compare fields"""
        # Identical
        field0 = ([('a', 'test')], '1', '2', '', 0)
        field1 = ([('a', 'test')], '1', '2', '', 3)
        self.assertEqual(True,
            bibrecord._compare_fields(field0, field1, strict=True))
        self.assertEqual(True,
            bibrecord._compare_fields(field0, field1, strict=False))

        # Order of the subfields changed.
        field0 = ([('a', 'testa'), ('b', 'testb')], '1', '2', '', 0)
        field1 = ([('b', 'testb'), ('a', 'testa')], '1', '2', '', 3)
        self.assertEqual(False,
            bibrecord._compare_fields(field0, field1, strict=True))
        self.assertEqual(True,
            bibrecord._compare_fields(field0, field1, strict=False))

        # Different
        field0 = ([], '3', '2', '', 0)
        field1 = ([], '1', '2', '', 3)
        self.assertEqual(False,
            bibrecord._compare_fields(field0, field1, strict=True))
        self.assertEqual(False,
            bibrecord._compare_fields(field0, field1, strict=False))

class BibRecordFindFieldTest(InvenioTestCase):
    """ bibrecord - testing for finding field """

    def setUp(self):
        """Initialize stuff"""
        xml = """
        <record>
        <controlfield tag="001">81</controlfield>
        <datafield tag="037" ind1=" " ind2=" ">
        <subfield code="a">TEST-ARTICLE-2006-001</subfield>
        <subfield code="b">ARTICLE-2007-001</subfield>
        </datafield>
        </record>
        """
        self.rec = bibrecord.create_record(xml)[0]
        self.field0 = self.rec['001'][0]
        self.field1 = self.rec['037'][0]
        self.field2 = (
            [self.field1[0][1], self.field1[0][0]],
            self.field1[1],
            self.field1[2],
            self.field1[3],
            self.field1[4],
            )

    def test_finding_field_strict(self):
        """bibrecord - test finding field strict"""
        self.assertEqual((1, 0),
            bibrecord.record_find_field(self.rec, '001', self.field0,
            strict=True))
        self.assertEqual((2, 0),
            bibrecord.record_find_field(self.rec, '037', self.field1,
            strict=True))
        self.assertEqual((None, None),
            bibrecord.record_find_field(self.rec, '037', self.field2,
            strict=True))

    def test_finding_field_loose(self):
        """bibrecord - test finding field loose"""
        self.assertEqual((1, 0),
            bibrecord.record_find_field(self.rec, '001', self.field0,
            strict=False))
        self.assertEqual((2, 0),
            bibrecord.record_find_field(self.rec, '037', self.field1,
            strict=False))
        self.assertEqual((2, 0),
            bibrecord.record_find_field(self.rec, '037', self.field2,
            strict=False))

class BibRecordSingletonTest(InvenioTestCase):
    """ bibrecord - testing singleton removal """

    def setUp(self):
        """Initialize stuff"""
        self.xml = """<collection>
                       <record>
                         <controlfield tag="001">33</controlfield>
                         <controlfield tag="002" />
                         <datafield tag="99" ind1=" " ind2=" "/>
                         <datafield tag="100" ind1=" " ind2=" ">
                           <subfield code="a" />
                         </datafield>
                         <datafield tag="100" ind1=" " ind2=" ">
                           <subfield code="a">Some value</subfield>
                         </datafield>
                         <tagname />
                       </record>
                       <record />
                      <collection>"""
        self.rec_expected = {
            '001': [([], ' ', ' ', '33', 1)],
            '100': [([('a', 'Some value')], ' ', ' ', '', 2)],
            }

    if parser_minidom_available:
        def test_singleton_removal_minidom(self):
            """bibrecord - enforcing singleton removal with minidom"""
            rec = bibrecord.create_records(self.xml, verbose=1,
                                           correct=1, parser='minidom',
                                           keep_singletons=False)[0][0]
            self.assertEqual(rec, self.rec_expected)

    if parser_4suite_available:
        def test_singleton_removal_4suite(self):
            """bibrecord - enforcing singleton removal with 4suite"""
            rec = bibrecord.create_records(self.xml, verbose=1,
                                           correct=1, parser='4suite',
                                           keep_singletons=False)[0][0]
            self.assertEqual(rec, self.rec_expected)

    if parser_pyrxp_available:
        def test_singleton_removal_pyrxp(self):
            """bibrecord - enforcing singleton removal with pyrxp"""
            rec = bibrecord.create_records(self.xml, verbose=1,
                                           correct=1, parser='pyrxp',
                                           keep_singletons=False)[0][0]
            self.assertEqual(rec, self.rec_expected)

    if parser_lxml_available:
        def test_singleton_removal_lxml(self):
            """bibrecord - enforcing singleton removal with lxml"""
            rec = bibrecord.create_records(self.xml, verbose=1,
                                           correct=1, parser='lxml',
                                           keep_singletons=False)[0][0]
            self.assertEqual(rec, self.rec_expected)

class BibRecordNumCharRefTest(InvenioTestCase):
    """ bibrecord - testing numerical character reference expansion"""

    def setUp(self):
        """Initialize stuff"""
        self.xml = """<?xml version="1.0" encoding="UTF-8"?>
                      <record>
                        <controlfield tag="001">33</controlfield>
                        <datafield tag="123" ind1=" " ind2=" ">
                          <subfield code="a">Σ &amp; &#931;</subfield>
                          <subfield code="a">use &amp;amp; in XML</subfield>
                        </datafield>
                      </record>"""
        self.rec_expected = {
            '001': [([], ' ', ' ', '33', 1)],
            '123': [([('a', '\xce\xa3 & \xce\xa3'), ('a', 'use &amp; in XML'),], ' ', ' ', '', 2)],
            }

    if parser_minidom_available:
        def test_numcharref_expansion_minidom(self):
            """bibrecord - numcharref expansion with minidom"""
            rec = bibrecord.create_records(self.xml, verbose=1,
                                           correct=1, parser='minidom')[0][0]
            self.assertEqual(rec, self.rec_expected)

    if parser_4suite_available:
        def test_numcharref_expansion_4suite(self):
            """bibrecord - numcharref expansion with 4suite"""
            rec = bibrecord.create_records(self.xml, verbose=1,
                                           correct=1, parser='4suite')[0][0]
            self.assertEqual(rec, self.rec_expected)

    if parser_pyrxp_available:
        def test_numcharref_expansion_pyrxp(self):
            """bibrecord - but *no* numcharref expansion with pyrxp (see notes)

            FIXME: pyRXP does not seem to like num char ref entities,
            so this test is mostly left here in a TDD style in order
            to remind us of this fact.  If we want to fix this
            situation, then we should probably use pyRXPU that uses
            Unicode strings internally, hence it is num char ref
            friendly.  Maybe we should use pyRXPU by default, if
            performance is acceptable, or maybe we should introduce a
            flag to govern this behaviour.
            """
            rec = bibrecord.create_records(self.xml, verbose=1,
                                           correct=1, parser='pyrxp')[0][0]
            #self.assertEqual(rec, self.rec_expected)
            self.assertEqual(rec, None)

    if parser_lxml_available:
        def test_numcharref_expansion_lxml(self):
            """bibrecord - numcharref expansion with lxml"""
            rec = bibrecord.create_records(self.xml, verbose=1,
                                           correct=1, parser='lxml')[0][0]
            self.assertEqual(rec, self.rec_expected)

class BibRecordExtractIdentifiersTest(InvenioTestCase):
    """ bibrecord - testing for getting identifiers from record """

    def setUp(self):
        """Initialize stuff"""
        xml_example_record = """
        <record>
        <controlfield tag="001">1</controlfield>
        <datafield tag="100" ind1="C" ind2="5">
        <subfield code="a">val1</subfield>
        </datafield>
        <datafield tag="024" ind1="7" ind2=" ">
        <subfield code="2">doi</subfield>
        <subfield code="a">5555/TEST1</subfield>
        </datafield>
        <datafield tag="024" ind1="7" ind2=" ">
        <subfield code="2">DOI</subfield>
        <subfield code="a">5555/TEST2</subfield>
        </datafield>
        <datafield tag="024" ind1="7" ind2=" ">
        <subfield code="2">nondoi</subfield>
        <subfield code="a">5555/TEST3</subfield>
        </datafield>
        <datafield tag="024" ind1="8" ind2=" ">
        <subfield code="2">doi</subfield>
        <subfield code="a">5555/TEST4</subfield>
        </datafield>
        <datafield tag="%(oai_tag)s" ind1="%(oai_ind1)s" ind2="%(oai_ind2)s">
        <subfield code="%(oai_subcode)s">oai:atlantis:1</subfield>
        </datafield>
        </record>
        """ % {'oai_tag': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[0:3],
               'oai_ind1': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3],
               'oai_ind2': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4],
               'oai_subcode': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[5],
               }
        self.rec = bibrecord.create_record(xml_example_record, 1, 1)[0]

    def test_extract_doi(self):
        """bibrecord - getting DOI identifier(s) from record"""
        self.assertEqual(bibrecord.record_extract_dois(self.rec),
                         ['5555/TEST1', '5555/TEST2'])

    def test_extract_oai_id(self):
        """bibrecord - getting OAI identifier(s) from record"""
        self.assertEqual(bibrecord.record_extract_oai_id(self.rec),
                         'oai:atlantis:1')


TEST_SUITE = make_test_suite(
    BibRecordSuccessTest,
    BibRecordParsersTest,
    BibRecordBadInputTreatmentTest,
    BibRecordGettingFieldValuesTest,
    BibRecordGettingFieldValuesViaWildcardsTest,
    BibRecordAddFieldTest,
    BibRecordDeleteFieldTest,
    BibRecordManageMultipleFieldsTest,
    BibRecordDeleteFieldFromTest,
    BibRecordAddSubfieldIntoTest,
    BibRecordModifyControlfieldTest,
    BibRecordModifySubfieldTest,
    BibRecordDeleteSubfieldFromTest,
    BibRecordMoveSubfieldTest,
    BibRecordCompareSubfieldTest,
    BibRecordAccentedUnicodeLettersTest,
    BibRecordSpecialTagParsingTest,
    BibRecordPrintingTest,
    BibRecordCreateFieldTest,
    BibRecordFindFieldTest,
    BibRecordDeleteSubfieldTest,
    BibRecordSingletonTest,
    BibRecordNumCharRefTest,
    BibRecordExtractIdentifiersTest,
    BibRecordDropDuplicateFieldsTest
    )

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
