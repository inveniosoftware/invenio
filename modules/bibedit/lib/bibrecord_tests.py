# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

__revision__ = "$Id$"

import unittest
from string import expandtabs, replace

from invenio.config import tmpdir, etcdir
from invenio import bibrecord

# pylint: disable-msg=C0301

class BibRecordSanityTest(unittest.TestCase):
    """ bibrecord - sanity test (xml -> create records -> xml)"""
    def test_for_sanity(self):
        """ bibrecord - demo file sanity test (xml -> create records -> xml)"""
        f = open(tmpdir + '/demobibdata.xml', 'r')
        xmltext = f.read()
        f.close()
        # let's try to reproduce the demo XML MARC file by parsing it and printing it back:
        recs = map((lambda x:x[0]), bibrecord.create_records(xmltext))
        xmltext_reproduced = bibrecord.records_xml_output(recs)
        x = xmltext_reproduced
        y = xmltext
        # 'normalize' the two XML MARC files for the purpose of comparing
        x = expandtabs(x)
        y = expandtabs(y)
        x = x.replace(' ', '')
        y = y.replace(' ', '')
        x = x.replace('<!DOCTYPEcollectionSYSTEM"file://%s/bibedit/MARC21slim.dtd">\n<collection>' % etcdir,
                      '<collectionxmlns="http://www.loc.gov/MARC21/slim">')
        x = x.replace('</record><record>', "</record>\n<record>")
        x = x.replace('</record></collection>', "</record>\n</collection>\n")
        x = x[1:100]
        y = y[1:100]
        self.assertEqual(x, y)

class BibRecordSuccessTest(unittest.TestCase):
    """ bibrecord - demo file parsing test """

    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize stuff"""
        f = open(tmpdir + '/demobibdata.xml', 'r')
        xmltext = f.read()
        f.close()
        self.recs = map((lambda x: x[0]), bibrecord.create_records(xmltext))
    
    def test_records_created(self):
        """ bibrecord - demo file how many records are created """
        self.assertEqual(95, len(self.recs))
        
    def test_tags_created(self):
        """ bibrecord - demo file which tags are created """
        ## check if the tags are correct
        # tags = ['020', '037', '041', '080', '088', '100', '245', '246', '250', '260', '270', '300', '340', '490', '500', '502', '520', '590', '595', '650', '653', '690', '700', '710', '856', '909', '980', '999']

        tags = [u'003', u'005', '020', '035', '037', '041', '080', '088', '100', '245', '246', '250', '260', '269', '270', '300', '340', '490', '500', '502', '520', '590', '595', '650', '653', '690', '695', '700', '710', '720', '856', '859', '901', '909', '916', '960', '961', '962', '963', '970', '980', '999', 'FFT']
        
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

        fields = [14, 14, 8, 11, 11, 12, 11, 15, 10, 18, 14, 16, 10, 9, 15, 10, 11, 11, 11, 9, 10, 10, 10, 8, 8, 8, 9, 9, 9, 10, 8, 8, 8, 8, 14, 13, 14, 14, 15, 12, 12, 12, 15, 14, 12, 16, 16, 15, 15, 14, 16, 15, 15, 15, 16, 15, 16, 15, 15, 16, 15, 14, 14, 15, 12, 13, 11, 15, 8, 11, 14, 13, 12, 13, 6, 6, 25, 24, 27, 26, 26, 24, 26, 27, 25, 28, 24, 23, 27, 25, 25, 26, 26, 24]

        cr = []
        ret = []
        for rec in self.recs:
            cr.append(len(rec.values()))
            ret.append(rec)
        self.assertEqual(fields, cr)
  
class BibRecordBadInputTreatmentTest(unittest.TestCase):
    """ bibrecord - testing for bad input treatment """
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
        (rec, st, e) = bibrecord.create_record(xml_error1, 1, 1)
        ee =''
        for i in e:
            if type(i).__name__ == 'str':
                if i.count(ws[3])>0:
                    ee = i
        self.assertEqual(bibrecord.warning((3, '(field number: 4)')), ee)

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
        (rec, st, e) = bibrecord.create_record(xml_error2, 1, 1)
        ee = ''
        for i in e:
            if type(i).__name__ == 'str':
                if i.count(ws[1])>0:
                    ee = i
        self.assertEqual(bibrecord.warning((1, '(field number(s): [2])')), ee)

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
        (rec, st, e) = bibrecord.create_record(xml_error3, 1, 1)
        ee = ''
        for i in e:
            if type(i).__name__ == 'str':
                if i.count(ws[8])>0:
                    ee = i
        self.assertEqual(bibrecord.warning((8, '(field number: 2)')), ee)

    def test_missing_tag(self):
        """bibrecord - bad input missing end \"tag\""""
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
        (rec, st, e) = bibrecord.create_record(xml_error4, 1, 1)
        ee = ''
        for i in e:
            if type(i).__name__ == 'str':
                if i.count(ws[99])>0:
                    ee = i
        self.assertEqual(bibrecord.warning((99, '(Tagname : datafield)')), ee)

class BibRecordAccentedUnicodeLettersTest(unittest.TestCase):
    """ bibrecord - testing accented UTF-8 letters """

    def setUp(self):
        # pylint: disable-msg=C0103
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
        (self.rec, st, e) = bibrecord.create_record(self.xml_example_record, 1, 1)

    def test_accented_unicode_characters(self):
        """bibrecord - accented Unicode letters"""
        self.assertEqual(self.xml_example_record,
                         bibrecord.record_xml_output(self.rec))
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "100", " ", " "),
                         [([('a', 'Döè1, John')], " ", " ", "", 3), ([('a', 'Doe2, J>ohn'), ('b', 'editor')], " ", " ", "", 4)])
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "245", " ", "1"),
                         [([('a', 'Пушкин')], " ", '1', "", 5)])

class BibRecordGettingFieldValuesTest(unittest.TestCase):
    """ bibrecord - testing for getting field/subfield values """

    def setUp(self):
        # pylint: disable-msg=C0103
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
        (self.rec, st, e) = bibrecord.create_record(xml_example_record, 1, 1)

    def test_get_field_instances(self):
        """bibrecord - getting field instances"""
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "100", " ", " "),
                         [([('a', 'Doe1, John')], " ", " ", "", 3), ([('a', 'Doe2, John'), ('b', 'editor')], " ", " ", "", 4)])
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "", " ", " "),
                        [('245', [([('a', 'On the foo and bar1')], " ", '1', "", 5), ([('a', 'On the foo and bar2')], " ", '2', "", 6)]), ('001', [([], " ", " ", '33', 1)]), ('100', [([('a', 'Doe1, John')], " ", " ", "", 3), ([('a', 'Doe2, John'), ('b', 'editor')], " ", " ", "", 4)]), ('041', [([('a', 'eng')], " ", " ", "", 2)])]) 

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

class BibRecordGettingFieldValuesViaWildcardsTest(unittest.TestCase):
    """ bibrecord - testing for getting field/subfield values via wildcards """

    def setUp(self):
        # pylint: disable-msg=C0103
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
        (self.rec, st, e) = bibrecord.create_record(xml_example_record, 1, 1)

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

class BibRecordAddFieldTest(unittest.TestCase):
    """ bibrecord - testing adding field """

    def setUp(self):
        # pylint: disable-msg=C0103
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
        (self.rec, st, e) = bibrecord.create_record(xml_example_record, 1, 1)

    def test_add_controlfield(self):
        """bibrecord - adding controlfield"""
        field_number_1 = bibrecord.record_add_field(self.rec, "003", " ", " ", "SzGeCERN")
        field_number_2 = bibrecord.record_add_field(self.rec, "004", " ", " ", "Test")
        self.assertEqual(field_number_1, 7)
        self.assertEqual(field_number_2, 8)
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "003", " ", " ", ""),
                         ['SzGeCERN'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "004", " ", " ", ""),
                         ['Test'])

    def test_add_datafield(self):
        """bibrecord - adding datafield"""
        field_number_1 = bibrecord.record_add_field(self.rec, "100", " ", " ", "",
                                                    [('a', 'Doe3, John')])
        field_number_2 = bibrecord.record_add_field(self.rec, "100", " ", " ", "",
                                                    [('a', 'Doe4, John'), ('b', 'editor')])
        self.assertEqual(field_number_1, 7)
        self.assertEqual(field_number_2, 8)
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", " ", " ", "a"),
                         ['Doe1, John', 'Doe2, John', 'Doe3, John', 'Doe4, John'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", " ", " ", "b"),
                         ['editor', 'editor'])

    def test_add_controlfield_on_desired_position(self):
        """bibrecord - adding controlfield on desired position"""
        field_number_1 = bibrecord.record_add_field(self.rec, "005", " ", " ", "Foo", [], 0)
        field_number_2 = bibrecord.record_add_field(self.rec, "006", " ", " ", "Bar", [], 0)
        self.assertEqual(field_number_1, 0)
        self.assertEqual(field_number_2, 7)

    def test_add_datafield_on_desired_position(self):
        """bibrecord - adding datafield on desired position"""
        field_number_1 = bibrecord.record_add_field(self.rec, "100", " ", " ", " ",
                                                    [('a', 'Doe3, John')], 0)
        field_number_2 = bibrecord.record_add_field(self.rec, "100", " ", " ", " ",
                                                    [('a', 'Doe4, John'), ('b', 'editor')], 0)
        self.assertEqual(field_number_1, 0)
        self.assertEqual(field_number_2, 7)

class BibRecordDeleteFieldTest(unittest.TestCase):
    """ bibrecord - testing field deletion """

    def setUp(self):
        # pylint: disable-msg=C0103
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
        (self.rec, st, e) = bibrecord.create_record(xml_example_record, 1, 1)

        xml_example_record_empty = """
        <record>
        </record>
        """
        (self.rec_empty, st, e) = bibrecord.create_record(xml_example_record_empty, 1, 1)

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
        field_number_1 = bibrecord.record_add_field(self.rec_empty, "003", " ", " ", "SzGeCERN")
        self.assertEqual(field_number_1, 1)
        self.assertEqual(bibrecord.record_get_field_values(self.rec_empty, "003", " ", " ", ""),
                         ['SzGeCERN'])        
        bibrecord.record_delete_field(self.rec_empty, "003", " ", " ")
        self.assertEqual(bibrecord.record_get_field_values(self.rec_empty, "003", " ", " ", ""),
                         [])        
        field_number_1 = bibrecord.record_add_field(self.rec_empty, "003", " ", " ", "SzGeCERN2")        
        self.assertEqual(field_number_1, 1)
        self.assertEqual(bibrecord.record_get_field_values(self.rec_empty, "003", " ", " ", ""),
                         ['SzGeCERN2'])        

class BibRecordSpecialTagParsingTest(unittest.TestCase):
    """ bibrecord - parsing special tags (FMT, FFT)"""

    def setUp(self):
        # pylint: disable-msg=C0103
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
        rec, st, e = bibrecord.create_record(self.xml_example_record_with_fmt, 1, 1)
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
        rec, st, e = bibrecord.create_record(self.xml_example_record_with_fmt, 1, 0)
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
        rec, st, e = bibrecord.create_record(self.xml_example_record_with_fft, 1, 1)
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
        rec, st, e = bibrecord.create_record(self.xml_example_record_with_fft, 1, 0)
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
        rec, st, e = bibrecord.create_record(self.xml_example_record_with_xyz, 1, 1)
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
        rec, st, e = bibrecord.create_record(self.xml_example_record_with_xyz, 1, 0)
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


class BibRecordPrintingTest(unittest.TestCase):
    """ bibrecord - testing for printing record """

    def setUp(self):
        # pylint: disable-msg=C0103
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
        
    def test_print_rec(self):
        """bibrecord - print rec"""
        rec, st, e = bibrecord.create_record(self.xml_example_record, 1, 1)
        rec_short, st_short, e_short = bibrecord.create_record(self.xml_example_record_short, 1, 1)
        self.assertEqual(bibrecord.create_record(bibrecord.print_rec(rec, tags=[]), 1, 1)[0], rec)
        self.assertEqual(bibrecord.create_record(bibrecord.print_rec(rec, tags=["001", "037"]), 1, 1)[0], rec_short)
        self.assertEqual(bibrecord.create_record(bibrecord.print_rec(rec, tags=["037"]), 1, 1)[0], rec_short)

    def test_print_recs(self):
        """bibrecord - print multiple recs"""
        list_of_recs = bibrecord.create_records(self.xml_example_multi_records, 1, 1)
        list_of_recs_elems = [elem[0] for elem in list_of_recs]
        list_of_recs_short = bibrecord.create_records(self.xml_example_multi_records_short, 1, 1)
        list_of_recs_short_elems = [elem[0] for elem in list_of_recs_short]
        self.assertEqual(bibrecord.create_records(bibrecord.print_recs(list_of_recs_elems, tags=[]), 1, 1), list_of_recs)
        self.assertEqual(bibrecord.create_records(bibrecord.print_recs(list_of_recs_elems, tags=["001", "037"]), 1, 1), list_of_recs_short)
        self.assertEqual(bibrecord.create_records(bibrecord.print_recs(list_of_recs_elems, tags=["037"]), 1, 1), list_of_recs_short)
        
def create_test_suite():
    """Return test suite for the bibrecord module"""
    return unittest.TestSuite((unittest.makeSuite(BibRecordSanityTest, 'test'),
                               unittest.makeSuite(BibRecordSuccessTest, 'test'),
                               unittest.makeSuite(BibRecordBadInputTreatmentTest, 'test'),
                               unittest.makeSuite(BibRecordGettingFieldValuesTest, 'test'),
                               unittest.makeSuite(BibRecordGettingFieldValuesViaWildcardsTest, 'test'),
                               unittest.makeSuite(BibRecordAddFieldTest, 'test'),
                               unittest.makeSuite(BibRecordDeleteFieldTest, 'test'),
                               unittest.makeSuite(BibRecordAccentedUnicodeLettersTest, 'test'),
                               unittest.makeSuite(BibRecordSpecialTagParsingTest, 'test'),
                               unittest.makeSuite(BibRecordPrintingTest, 'test'),
                               ))
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())
