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

"""Regression tests for the bibupload."""

__version__ = "$Id$"

import sre
import unittest
import re
import time
from invenio.bibupload import *
from invenio.search_engine import print_record
from invenio.config import tmpdir, etcdir
from invenio.testutils import make_test_suite, warn_user_about_tests_and_run, \
                              make_url, test_web_page_content, merge_error_messages

# helper functions:

def compare_xmlbuffers(xmlbuffer1, xmlbuffer2):
    """Compare two xml buffers by taking away the controlfield 001."""
    # take away 001:
    xmlbuffer1 = sre.sub(r'<controlfield tag="001">.*</controlfield>', '', xmlbuffer1)
    xmlbuffer1 = remove_blanks_from_xmlbuffer(xmlbuffer1)
    # take away 001:
    xmlbuffer2 = sre.sub(r'<controlfield tag="001">.*</controlfield>', '', xmlbuffer2)
    xmlbuffer2 = remove_blanks_from_xmlbuffer(xmlbuffer2)
    return (xmlbuffer1 == xmlbuffer2)
    
def remove_blanks_from_xmlbuffer(xmlbuffer):
    """Remove \n and blank from XMLBUFFER."""
    out = xmlbuffer.replace("\n", "")
    out = out.replace(" ", "")
    return out
       
#TODO insert Test
class InsertModeTest(unittest.TestCase):
    """Testing proper insert of the xml files"""
    
    def setUp(self):
        """Initialise the xml marc variable"""
        self.test = """<record>
        <datafield tag ="245" ind1="" ind2="">
        <subfield code="a">something</subfield>
        </datafield>
        <datafield tag ="700" ind1="" ind2="">
        <subfield code="a">Le Meur, J Y</subfield>
        <subfield code="u">MIT</subfield>
        </datafield>
        <datafield tag ="700" ind1="" ind2="">
        <subfield code="a">Jedrzejek, K J</subfield>
        <subfield code="u">CERN2</subfield>
        </datafield>
        <datafield tag ="700" ind1="" ind2="">
        <subfield code="a">Favre, G</subfield>
        <subfield code="u">CERN3</subfield>
        </datafield>
        <datafield tag ="111" ind1="" ind2="">
        <subfield code="a">test11</subfield>
        <subfield code="c">test31</subfield>
        </datafield>
        <datafield tag ="111" ind1="" ind2="">
        <subfield code="a">test12</subfield>
        <subfield code="c">test32</subfield>
        </datafield>
        <datafield tag ="111" ind1="" ind2="">
        <subfield code="a">test13</subfield>
        <subfield code="c">test33</subfield>
        </datafield>
        <datafield tag ="111" ind1="" ind2="">
        <subfield code="b">test21</subfield>
        <subfield code="d">test41</subfield>
        </datafield>
        <datafield tag ="111" ind1="" ind2="">
        <subfield code="b">test22</subfield>
        <subfield code="d">test42</subfield>
        </datafield>
        <datafield tag ="111" ind1="" ind2="">
        <subfield code="a">test14</subfield>
        </datafield>
        <datafield tag ="111" ind1="" ind2="">
        <subfield code="e">test51</subfield>
        </datafield>
        <datafield tag ="111" ind1="" ind2="">
        <subfield code="e">test52</subfield>
        </datafield>
        <datafield tag ="100" ind1="" ind2="">
        <subfield code="a">Simko, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""
    
    def test_create_record_id(self):
        """bibupload - try to create a new record ID in the database"""
        rec_id = create_new_record()
        self.assertNotEqual(-1, rec_id)
    
    def test_no_retrieve_record_id(self):
        """bibupload - in insert mode the input file should not contain record ID"""
        #Initialise the global variable
        options['mode'] = 'insert'
        # We create create the record out of the xml marc
        rec = xml_marc_to_records(self.test)
        # We call the function which should retrieve the record id
        rec_id = retrieve_rec_id(rec[0])
        # We compare the value found with None
        self.assertEqual(None, rec_id)
    
    def test_insert_complete_xmlmarc(self):
        """bibupload - insert complete MARCXML file"""
        #Initialise the global variable
        options['mode'] = 'insert'
        options['verbose'] = 0
        # We create create the record out of the xml marc
        rec = xml_marc_to_records(self.test)
        # We call the main function with the record as a parameter
        info = bibupload(rec[0])
        # We retrieve the inserted xml
        inserted_xml = print_record(int(info[1]),'xm')
        #Compare if the two xml MARC are the same
        self.assertEqual(1, compare_xmlbuffers(inserted_xml, self.test))
    
#TODO append Test
class AppendModeTest(unittest.TestCase):
    """Testing proper append of the xml files"""
    
    def setUp(self):
        """Initialise the xml marc variable"""
        self.test_controfield001 = """<record>
        <controlfield tag ="001">002</controlfield>
        <datafield tag ="100" ind1="" ind2="">
        <subfield code="a">Simko, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""
        self.test_append = """<record>
        <datafield tag ="100" ind1="" ind2="">
        <subfield code="a">Simko, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""
        self.test_append_expected = """<record>
        <datafield tag ="100" ind1="" ind2="">
        <subfield code="a">Simko, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        <datafield tag ="100" ind1="" ind2="">
        <subfield code="a">Simko, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""
        
    def test_retrieve_record_id(self):
        """bibupload - in append mode the input file should contain a record ID"""
        #Initialise the global variable
        options['mode'] = 'append'
        options['verbose'] = 0
        # We create create the record out of the xml marc
        rec = xml_marc_to_records(self.test_controfield001)
        # We call the function which should retrieve the record id
        rec_id = retrieve_rec_id(rec[0])
        # We compare the value found with None
        self.assertEqual('002', rec_id)
    
    def test_update_modification_record_date(self):
        """bibupload - check the update of the modification date"""
        #Initialise the global variable
        options['mode'] = 'append'
        options['verbose'] = 0
        # We create create the record out of the xml marc
        rec = xml_marc_to_records(self.test_controfield001)
        # We call the function which should retrieve the record id
        rec_id = retrieve_rec_id(rec[0])
        # Retrieve current localtime
        now = time.localtime()
        # We update the modification date
        update_bibrec_modif_date(convert_datestruct_to_datetext(now), rec_id)
        # We retrieve the modification date from the database
        query = """SELECT DATE_FORMAT(modification_date,'%%Y-%%m-%%d %%H:%%i:%%s') FROM bibrec where id = %s"""
        res = run_sql(query % rec_id)
        # We compare the two results
        self.assertEqual(res[0][0], convert_datestruct_to_datetext(now))
        
    def test_append_complete_xml_marc(self):
        """bibupload - append complete MARCXML file"""
        #Initialise the global variable
        options['mode'] = 'insert'
        options['verbose'] = 0
        # We create create the record out of the xml marc
        rec = xml_marc_to_records(self.test_append)
        # We call the main function with the record as a parameter
        info = bibupload(rec[0])
        #Now we append a datafield
        options['mode'] = 'append'
        # We add the controfield 001
        xml_with_controlfield = self.test_controfield001.replace('<controlfield tag ="001">002</controlfield>', '<controlfield tag ="001">'+str(info[1])+'</controlfield>')
        # We create create the record out of the xml marc
        rec = xml_marc_to_records(xml_with_controlfield)
        # We call the main function with the record as a parameter
        info = bibupload(rec[0])
        # We retrieve the inserted xml
        append_xml = print_record(int(info[1]),'xm')
        #Compare if the two xml MARC are the same
        self.assertEqual(1, compare_xmlbuffers(append_xml, self.test_append_expected))

#TODO correct Test
class CorrectModeTest(unittest.TestCase):
    """Testing proper append of the xml files"""
    
    def setUp(self):
        """Initialise the xml marc variable"""
        self.test_correct = """<record>
        <datafield tag ="100" ind1="" ind2="">
        <subfield code="a">Simko, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""
        self.test_correct_expected = """<record>
        <datafield tag ="100" ind1="" ind2="">
        <subfield code="a">Test, T</subfield>
        <subfield code="u">TEST</subfield>
        </datafield>
        </record>"""
    
    def test_correct_complete_xml_marc(self):
        """bibupload - correct complete MARCXML file"""
        #Initialise the global variable
        options['mode'] = 'insert'
        options['verbose'] = 0
        # We create create the record out of the xml marc
        rec = xml_marc_to_records(self.test_correct)
        # We call the main function with the record as a parameter
        info = bibupload(rec[0])
        #Now we append a datafield
        options['mode'] = 'correct'
        # We add the controfield 001
        xml_with_controlfield = self.test_correct_expected.replace('<record>', '<record>\n<controlfield tag ="001">'+str(info[1])+'</controlfield>')
        # We create create the record out of the xml marc
        rec = xml_marc_to_records(xml_with_controlfield)
        # We call the main function with the record as a parameter
        info = bibupload(rec[0])
        # We retrieve the inserted xml
        correct_xml = print_record(int(info[1]),'xm')
        #Compare if the two xml MARC are the same
        self.assertEqual(1, compare_xmlbuffers(correct_xml, self.test_correct_expected))

#TODO replace Test
class ReplaceModeTest(unittest.TestCase):
    """Testing proper Replace of the xml files"""
    
    def setUp(self):
        """Initialise the xml marc variable"""
        self.test_replace = """<record>
        <datafield tag ="100" ind1="" ind2="">
        <subfield code="a">Simko, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""
        self.test_replace_expected = """<record>
        <datafield tag ="100" ind1="" ind2="">
        <subfield code="a">Test, T</subfield>
        <subfield code="u">TEST</subfield>
        </datafield>
        </record>"""
    
    def test_replace_complete_xml_marc(self):
        """bibupload - replace complete MARCXML file"""
        #Initialise the global variable
        options['mode'] = 'insert'
        options['verbose'] = 0
        # We create create the record out of the xml marc
        rec = xml_marc_to_records(self.test_replace)
        # We call the main function with the record as a parameter
        info = bibupload(rec[0])
        #Now we append a datafield
        options['mode'] = 'replace'
        # We add the controfield 001
        xml_with_controlfield = self.test_replace_expected.replace('<record>', '<record>\n<controlfield tag ="001">'+str(info[1])+'</controlfield>')
        # We create create the record out of the xml marc
        rec = xml_marc_to_records(xml_with_controlfield)
        # We call the main function with the record as a parameter
        info = bibupload(rec[0])
        # We retrieve the inserted xml
        replace_xml = print_record(int(info[1]),'xm')
        #Compare if the two xml MARC are the same
        self.assertEqual(1, compare_xmlbuffers(replace_xml, self.test_replace_expected))
        
#TODO references Test
class ReferencesModeTest(unittest.TestCase):
    """Testing proper References of the xml files"""
    
    def setUp(self):
        """Initialise the xml marc variable"""
        self.test_insert = """<record>
        <datafield tag ="100" ind1="" ind2="">
        <subfield code="a">Simko, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""
        self.test_reference = """<record>
        <datafield tag =\""""+cfg_bibupload_reference_tag+"""\" ind1="C" ind2="5">
        <subfield code="m">M. Lüscher and P. Weisz, String excitation energies in SU(N) gauge theories beyond the free-string approximation,</subfield>
        <subfield code="s">J. High Energy Phys. 07 (2004) 014</subfield>
        </datafield>
        </record>"""
        self.test_reference_expected = """<record>
        <datafield tag ="100" ind1="" ind2="">
        <subfield code="a">Simko, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        <datafield tag =\""""+cfg_bibupload_reference_tag+"""\" ind1="C" ind2="5">
        <subfield code="m">M. Lüscher and P. Weisz, String excitation energies in SU(N) gauge theories beyond the free-string approximation,</subfield>
        <subfield code="s">J. High Energy Phys. 07 (2004) 014</subfield>
        </datafield>
        </record>"""
    
    def test_reference_complete_xml_marc(self):
        """bibupload - reference complete MARCXML file"""
        #Initialise the global variable
        options['mode'] = 'insert'
        options['verbose'] = 0
        # We create create the record out of the xml marc
        rec = xml_marc_to_records(self.test_insert)
        # We call the main function with the record as a parameter
        info = bibupload(rec[0])
        #Now we append a datafield
        options['mode'] = 'reference'
        # We add the controfield 001
        xml_with_controlfield = self.test_reference.replace('<record>', '<record>\n<controlfield tag ="001">'+str(info[1])+'</controlfield>')
        # We create create the record out of the xml marc
        rec = xml_marc_to_records(xml_with_controlfield)
        # We call the main function with the record as a parameter
        info = bibupload(rec[0])
        # We retrieve the inserted xml
        reference_xml = print_record(int(info[1]),'xm')

        #Compare if the two xml MARC are the same
        self.assertEqual(1, compare_xmlbuffers(reference_xml, self.test_reference_expected))

#TODO FMT Test


#TODO FFT Test

test_suite = make_test_suite(InsertModeTest,
                             AppendModeTest,
                             CorrectModeTest,
                             ReplaceModeTest,
                             ReferencesModeTest)

if __name__ == "__main__":
    warn_user_about_tests_and_run(test_suite)
