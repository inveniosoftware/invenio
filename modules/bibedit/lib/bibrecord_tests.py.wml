## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

<protect># -*- coding: utf-8 -*-</protect>

from config import tmpdir, etcdir
import bibrecord
import unittest
from string import expandtabs, replace

class SanityTest(unittest.TestCase):

### check for sanity -- xml -> create_record -> xml
    def test_for_sanity(self):
        """ bibrecord - checking for sanity """

        f=open(tmpdir + '/demobibdata.xml','r')
        xmltext = f.read()
        f.close()
        rs = bibrecord.create_records(xmltext)
        recs = map((lambda x:x[0]),rs)
        xmlT = bibrecord.records_xml_output(recs)
        x = xmlT.replace('\n','')
        y = xmltext.replace('\n','')
        xx=expandtabs(x)
        yy=expandtabs(y)
        xxx = xx.replace(' ','')
        yyy = yy.replace(' ','')
        xxx = xxx.replace('<!DOCTYPEcollectionSYSTEM"file://%s/bibedit/MARC21slim.dtd"><collection>' % etcdir,
                          '<collectionxmlns="http://www.loc.gov/MARC21/slim">')
        self.assertEqual(xxx,yyy)

### testing for success
        
class SuccessTest(unittest.TestCase):
    """ bibrecord - testing for success """
    def setUp(self):
        f=open(tmpdir + '/demobibdata.xml','r')
        xmltext = f.read()
        f.close()
        self.recs = map((lambda x:x[0]),bibrecord.create_records(xmltext))
    
    def test_records_created(self):
        """ bibrecord - number of records created """
        ## check if it creates every records (the file demobibdata.xml has 75 records)
        self.assertEqual(75,len(self.recs))
        
    def test_tags_created(self):
        """ bibrecord - tags created """
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
        """bibrecord - fields created"""
    ## check if the number of fields for each record is correct

        fields=[13,13, 8, 11, 10,12, 10, 14, 10, 17, 13, 15, 10, 9, 14, 10, 11, 11, 11, 9, 10, 10, 10, 8, 8, 8, 9, 9, 9, 10, 8, 8, 8,8, 14, 13, 14, 14, 15, 12,12, 12,14, 13, 11, 15, 15, 14, 14, 13, 15, 14, 14, 14, 15, 14, 15, 14, 14, 15, 14, 13, 13, 14, 11, 13, 11, 14, 8, 10, 13, 12, 11, 12,6]

        cr=[]
        ret=[]
        for rec in self.recs:
            cr.append(len(rec.values()))
            ret.append(rec)
        self.assertEqual(fields,cr)
  
class BadInputTreatmentTest(unittest.TestCase):
    """ bibrecord - testing for bad input treatment """
    
    
### check bad input treatment ###
    def test_wrong_attribute(self):
        """bibrecord - bad input : Has \'cde\' instead \'code\' in a subfield attribute"""
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
        """ bibrecord - bad input : Missing attribute \"tag\" """
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
        """ bibrecord - bad input : Datafield without any subfield """
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
        """bibrecord - bad input : Missing end \"tag\""""
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
        xml_example_record = """
        <record>
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
        </record>
        """
        (self.rec, st, e) = bibrecord.create_record(xml_example_record,1,1)

    def test_accented_unicode_characters(self):
        """bibrecord - accented Unicode letters"""
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

def create_test_suite():
    """Return test suite for the bibrecord module"""
    return unittest.TestSuite((unittest.makeSuite(SanityTest,'test'),
                               unittest.makeSuite(SuccessTest,'test'),
                               unittest.makeSuite(BadInputTreatmentTest,'test'),
                               unittest.makeSuite(GettingFieldValuesTest,'test'),
                               unittest.makeSuite(AccentedUnicodeLettersTest,'test')))
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())
  
