# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

import unittest
from string import expandtabs, replace

from invenio.config import tmpdir, etcdir
from invenio import bibrecord

class SanityTest(unittest.TestCase):
    """ bibrecord - sanity test (xml -> create records -> xml)"""
    def test_for_sanity(self):
        """ bibrecord - demo file sanity test (xml -> create records -> xml)"""
        f=open(tmpdir + '/demobibdata.xml','r')
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
        x = x.replace(' ','')
        y = y.replace(' ','')
        x = x.replace('<!DOCTYPEcollectionSYSTEM"file://%s/bibedit/MARC21slim.dtd">\n<collection>' % etcdir,
                      '<collectionxmlns="http://www.loc.gov/MARC21/slim">')
        x = x.replace('</record><record>', "</record>\n<record>")
        x = x.replace('</record></collection>', "</record>\n</collection>\n")
        self.assertEqual(x,y)

class SuccessTest(unittest.TestCase):
    """ bibrecord - demo file parsing test """
    def setUp(self):
        f=open(tmpdir + '/demobibdata.xml','r')
        xmltext = f.read()
        f.close()
        self.recs = map((lambda x:x[0]),bibrecord.create_records(xmltext))
    
    def test_records_created(self):
        """ bibrecord - demo file how many records are created """
        self.assertEqual(76,len(self.recs))
        
    def test_tags_created(self):
        """ bibrecord - demo file which tags are created """
        ## check if the tags are correct
        tags= ['020', '037', '041', '080', '088', '100', '245', '246', '250', '260', '270', '300', '340', '490', '500', '502', '520', '590', '595', '650', '653', '690', '700', '710', '856','909','980','999']
        t=[]
        for rec in self.recs:
            t.extend(rec.keys())
        t.sort()
        #eliminate the elements repeated
        tt = []
        for x in t:
            if not x in tt:
                tt.append(x)
        self.assertEqual(tags,tt)

    def test_fields_created(self):
        """bibrecord - demo file how many fields are created"""
        ## check if the number of fields for each record is correct

        fields=[13,13, 8, 11, 10,12, 10, 14, 10, 17, 13, 15, 10, 9, 14, 10, 11, 11, 11, 9, 10, 10, 10, 8, 8, 8, 9, 9, 9, 10, 8, 8, 8,8, 14, 13, 14, 14, 15, 12,12, 12,14, 13, 11, 15, 15, 14, 14, 13, 15, 14, 14, 14, 15, 14, 15, 14, 14, 15, 14, 13, 13, 14, 11, 13, 11, 14, 8, 10, 13, 12, 11, 12, 6, 6]

        cr=[]
        ret=[]
        for rec in self.recs:
            cr.append(len(rec.values()))
            ret.append(rec)
        self.assertEqual(fields,cr)
  
class BadInputTreatmentTest(unittest.TestCase):
    """ bibrecord - testing for bad input treatment """
    def test_wrong_attribute(self):
        """bibrecord - bad input subfield \'cde\' instead of \'code\'"""
        ws = bibrecord.cfg_bibrecord_warning_msgs
        xml_error1 = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1="" ind2="">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1="" ind2="">
        <subfield code="a">Doe, John</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="">
        <subfield cde="a">On the foo and bar</subfield>
        </datafield>
        </record>
        """
        (rec,st,e) = bibrecord.create_record(xml_error1,1,1)
        ee=''
        for i in e:
            if type(i).__name__ == 'str':
                if i.count(ws[3])>0:
                    ee = i
        self.assertEqual(bibrecord.warning((3,'(field number: 4)')),ee)

    def test_missing_attribute(self):
        """ bibrecord - bad input missing \"tag\" """
        ws = bibrecord.cfg_bibrecord_warning_msgs
        xml_error2 = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield ind1="" ind2="">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1="" ind2="">
        <subfield code="a">Doe, John</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="">
        <subfield code="a">On the foo and bar</subfield>
        </datafield>
        </record>
        """        
        (rec,st,e) = bibrecord.create_record(xml_error2,1,1)
        ee=''
        for i in e:
            if type(i).__name__ == 'str':
                if i.count(ws[1])>0:
                    ee = i
        self.assertEqual(bibrecord.warning((1,'(field number(s): [2])')),ee)

    def test_empty_datafield(self):
        """ bibrecord - bad input no subfield """
        ws = bibrecord.cfg_bibrecord_warning_msgs
        xml_error3 = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1="" ind2="">
        </datafield>
        <datafield tag="100" ind1="" ind2="">
        <subfield code="a">Doe, John</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="">
	<subfield code="a">On the foo and bar</subfield>
        </datafield>
        </record>
        """
        (rec,st,e) = bibrecord.create_record(xml_error3,1,1)
        ee=''
        for i in e:
            if type(i).__name__ == 'str':
                if i.count(ws[8])>0:
                    ee = i
        self.assertEqual(bibrecord.warning((8,'(field number: 2)')),ee)


    def test_missing_tag(self):
        """bibrecord - bad input missing end \"tag\""""
        ws = bibrecord.cfg_bibrecord_warning_msgs
        xml_error4 = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1="" ind2="">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1="" ind2="">
        <subfield code="a">Doe, John</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="">
        <subfield code="a">On the foo and bar</subfield>
        </record>
        """
        (rec,st,e) = bibrecord.create_record(xml_error4,1,1)
        ee = ''
        for i in e:
            if type(i).__name__ == 'str':
                if i.count(ws[99])>0:
                    ee = i
        self.assertEqual(bibrecord.warning((99,'(Tagname : datafield)')),ee)

class AccentedUnicodeLettersTest(unittest.TestCase):
    """ bibrecord - testing accented UTF-8 letters """

    def setUp(self):
        self.xml_example_record = """<record>
  <controlfield tag="001">33</controlfield>
  <datafield tag="041" ind1="" ind2="">
    <subfield code="a">eng</subfield>
 </datafield>
  <datafield tag="100" ind1="" ind2="">
    <subfield code="a">Döè1, John</subfield>
 </datafield>
  <datafield tag="100" ind1="" ind2="">
    <subfield code="a">Doe2, J>ohn</subfield>
    <subfield code="b">editor</subfield>
 </datafield>
  <datafield tag="245" ind1="" ind2="1">
    <subfield code="a">Пушкин</subfield>
 </datafield>
  <datafield tag="245" ind1="" ind2="2">
    <subfield code="a">On the foo and bar2</subfield>
 </datafield>
</record>"""
        (self.rec, st, e) = bibrecord.create_record(self.xml_example_record,1,1)

    def test_accented_unicode_characters(self):
        """bibrecord - accented Unicode letters"""
        self.assertEqual(self.xml_example_record,
                         bibrecord.record_xml_output(self.rec))
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "100", "", ""),
                         [([('a', 'Döè1, John')], '', '', '', 3), ([('a', 'Doe2, J>ohn'), ('b', 'editor')], '', '', '', 4)])
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "245", "", "1"),
                         [([('a', 'Пушкин')], '', '1', '', 5)])

class GettingFieldValuesTest(unittest.TestCase):
    """ bibrecord - testing for getting field/subfield values """

    def setUp(self):
        xml_example_record = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1="" ind2="">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1="" ind2="">
        <subfield code="a">Doe1, John</subfield>
        </datafield>
        <datafield tag="100" ind1="" ind2="">
        <subfield code="a">Doe2, John</subfield>
        <subfield code="b">editor</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="1">
        <subfield code="a">On the foo and bar1</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="2">
        <subfield code="a">On the foo and bar2</subfield>
        </datafield>
        </record>
        """
        (self.rec, st, e) = bibrecord.create_record(xml_example_record,1,1)

    def test_get_field_instances(self):
        """bibrecord - getting field instances"""
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "100", "", ""),
                         [([('a', 'Doe1, John')], '', '', '', 3), ([('a', 'Doe2, John'), ('b', 'editor')], '', '', '', 4)])
        self.assertEqual(bibrecord.record_get_field_instances(self.rec, "", "", ""),
                        [('245', [([('a', 'On the foo and bar1')], '', '1', '', 5), ([('a', 'On the foo and bar2')], '', '2', '', 6)]), ('001', [([], '', '', '33', 1)]), ('100', [([('a', 'Doe1, John')], '', '', '', 3), ([('a', 'Doe2, John'), ('b', 'editor')], '', '', '', 4)]), ('041', [([('a', 'eng')], '', '', '', 2)])]) 

    def test_get_field_values(self):
        """bibrecord - getting field values"""
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", "", "", "a"),
                         ['Doe1, John', 'Doe2, John'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", "", "", "b"),
                         ['editor'])

    def test_get_subfield_values(self):
        """bibrecord - getting subfield values"""
        fi1, fi2 = bibrecord.record_get_field_instances(self.rec, "100", "", "")
        self.assertEqual(bibrecord.field_get_subfield_values(fi1, "b"), [])
        self.assertEqual(bibrecord.field_get_subfield_values(fi2, "b"), ["editor"])

class AddFieldTest(unittest.TestCase):
    """ bibrecord - testing adding field """

    def setUp(self):
        xml_example_record = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1="" ind2="">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1="" ind2="">
        <subfield code="a">Doe1, John</subfield>
        </datafield>
        <datafield tag="100" ind1="" ind2="">
        <subfield code="a">Doe2, John</subfield>
        <subfield code="b">editor</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="1">
        <subfield code="a">On the foo and bar1</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="2">
        <subfield code="a">On the foo and bar2</subfield>
        </datafield>
        </record>
        """
        (self.rec, st, e) = bibrecord.create_record(xml_example_record,1,1)

    def test_add_controlfield(self):
        """bibrecord - adding controlfield"""
        field_number_1 = bibrecord.record_add_field(self.rec, "003", "", "", "SzGeCERN")
        field_number_2 = bibrecord.record_add_field(self.rec, "004", "", "", "Test")
        self.assertEqual(field_number_1, 7)
        self.assertEqual(field_number_2, 8)
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "003", "", "", ""),
                         ['SzGeCERN'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "004", "", "", ""),
                         ['Test'])

    def test_add_datafield(self):
        """bibrecord - adding datafield"""
        field_number_1 = bibrecord.record_add_field(self.rec, "100", "", "", "",
                                                    [('a', 'Doe3, John')])
        field_number_2 = bibrecord.record_add_field(self.rec, "100", "", "", "",
                                                    [('a', 'Doe4, John'), ('b', 'editor')])
        self.assertEqual(field_number_1, 7)
        self.assertEqual(field_number_2, 8)
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", "", "", "a"),
                         ['Doe1, John', 'Doe2, John', 'Doe3, John', 'Doe4, John'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", "", "", "b"),
                         ['editor', 'editor'])

class DeleteFieldTest(unittest.TestCase):
    """ bibrecord - testing field deletion """

    def setUp(self):
        xml_example_record = """
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1="" ind2="">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1="" ind2="">
        <subfield code="a">Doe1, John</subfield>
        </datafield>
        <datafield tag="100" ind1="" ind2="">
        <subfield code="a">Doe2, John</subfield>
        <subfield code="b">editor</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="1">
        <subfield code="a">On the foo and bar1</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="2">
        <subfield code="a">On the foo and bar2</subfield>
        </datafield>
        </record>
        """
        (self.rec, st, e) = bibrecord.create_record(xml_example_record,1,1)

        xml_example_record_empty = """
        <record>
        </record>
        """
        (self.rec_empty, st, e) = bibrecord.create_record(xml_example_record_empty,1,1)

    def test_delete_controlfield(self):
        """bibrecord - deleting controlfield"""
        bibrecord.record_delete_field(self.rec, "001", "", "")
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "001", "", "", ""),
                         [])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", "", "", "b"),
                         ['editor'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "245", "", "2", "a"),
                         ['On the foo and bar2'])

    def test_delete_datafield(self):
        """bibrecord - deleting datafield"""
        bibrecord.record_delete_field(self.rec, "100", "", "")
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "001", "", "", ""),
                         ['33'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "100", "", "", "b"),
                         [])
        bibrecord.record_delete_field(self.rec, "245", "", "")
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "245", "", "1", "a"),
                         ['On the foo and bar1'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "245", "", "2", "a"),
                         ['On the foo and bar2'])
        bibrecord.record_delete_field(self.rec, "245", "", "2")
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "245", "", "1", "a"),
                         ['On the foo and bar1'])
        self.assertEqual(bibrecord.record_get_field_values(self.rec, "245", "", "2", "a"),
                         [])

    def test_add_delete_add_field_to_empty_record(self):
        """bibrecord - adding, deleting, and adding back a field to an empty record"""
        field_number_1 = bibrecord.record_add_field(self.rec_empty, "003", "", "", "SzGeCERN")
        self.assertEqual(field_number_1, 1)
        self.assertEqual(bibrecord.record_get_field_values(self.rec_empty, "003", "", "", ""),
                         ['SzGeCERN'])        
        bibrecord.record_delete_field(self.rec_empty, "003", "", "")
        self.assertEqual(bibrecord.record_get_field_values(self.rec_empty, "003", "", "", ""),
                         [])        
        field_number_1 = bibrecord.record_add_field(self.rec_empty, "003", "", "", "SzGeCERN2")        
        self.assertEqual(field_number_1, 1)
        self.assertEqual(bibrecord.record_get_field_values(self.rec_empty, "003", "", "", ""),
                         ['SzGeCERN2'])        

def create_test_suite():
    """Return test suite for the bibrecord module"""
    return unittest.TestSuite((unittest.makeSuite(SanityTest,'test'),
                               unittest.makeSuite(SuccessTest,'test'),
                               unittest.makeSuite(BadInputTreatmentTest,'test'),
                               unittest.makeSuite(GettingFieldValuesTest,'test'),
                               unittest.makeSuite(AddFieldTest,'test'),
                               unittest.makeSuite(DeleteFieldTest,'test'),
                               unittest.makeSuite(AccentedUnicodeLettersTest,'test')))
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())
  
