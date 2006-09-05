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

# pylint: disable-msg=C0301

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

def compare_xmlbuffers(xmlbuffer1, xmlbuffer2, remove_tag_001_before_test_p=1):
    """Compare two xml buffers by removing whitespaces before testing.
       Optionally the controlfield 001 is removed too."""

    def remove_blanks_from_xmlbuffer(xmlbuffer):
        """Remove \n and blanks from XMLBUFFER."""
        out = xmlbuffer.replace("\n", "")
        out = out.replace(" ", "")
        return out

    # take away 001:
    if remove_tag_001_before_test_p:
        xmlbuffer1 = sre.sub(r'<controlfield tag="001">.*</controlfield>', '', xmlbuffer1)
        xmlbuffer2 = sre.sub(r'<controlfield tag="001">.*</controlfield>', '', xmlbuffer2)

    # take away whitespace:
    xmlbuffer1 = remove_blanks_from_xmlbuffer(xmlbuffer1)
    xmlbuffer2 = remove_blanks_from_xmlbuffer(xmlbuffer2)

    return (xmlbuffer1 == xmlbuffer2)
           
class BibUploadInsertModeTest(unittest.TestCase):
    """Testing insert mode."""
    
    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialise the MARCXML variable"""
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
        """bibupload - insert mode, trying to create a new record ID in the database"""
        rec_id = create_new_record()
        self.assertNotEqual(-1, rec_id)
    
    def test_no_retrieve_record_id(self):
        """bibupload - insert mode, detection of record ID in the input file"""
        # Initialize the global variable
        options['mode'] = 'insert'
        # We create create the record out of the xml marc
        recs = xml_marc_to_records(self.test)
        # We call the function which should retrieve the record id
        rec_id = retrieve_rec_id(recs[0])
        # We compare the value found with None
        self.assertEqual(None, rec_id)
    
    def test_insert_complete_xmlmarc(self):
        """bibupload - insert mode, trying to insert complete MARCXML file"""
        # Initialize the global variable
        options['mode'] = 'insert'
        options['verbose'] = 0
        # We create create the record out of the xml marc
        recs = xml_marc_to_records(self.test)
        # We call the main function with the record as a parameter
        info = bibupload(recs[0])
        # We retrieve the inserted xml
        inserted_xml = print_record(int(info[1]),'xm')
        # Compare if the two MARCXML are the same
        self.failUnless(compare_xmlbuffers(inserted_xml, self.test))
    
class BibUploadAppendModeTest(unittest.TestCase):
    """Testing append mode."""
    
    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize the MARCXML variable"""
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
        """bibupload - append mode, the input file should contain a record ID"""
        # Initialize the global variable
        options['mode'] = 'append'
        options['verbose'] = 0
        # We create create the record out of the xml marc
        recs = xml_marc_to_records(self.test_controfield001)
        # We call the function which should retrieve the record id
        rec_id = retrieve_rec_id(recs[0])
        # We compare the value found with None
        self.assertEqual('002', rec_id)
    
    def test_update_modification_record_date(self):
        """bibupload - append mode, checking the update of the modification date"""
        # Initialize the global variable
        options['mode'] = 'append'
        options['verbose'] = 0
        # We create create the record out of the xml marc
        recs = xml_marc_to_records(self.test_controfield001)
        # We call the function which should retrieve the record id
        rec_id = retrieve_rec_id(recs[0])
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
        """bibupload - append mode, appending complete MARCXML file"""
        # Initialize the global variable
        options['mode'] = 'insert'
        options['verbose'] = 0
        # We create create the record out of the xml marc
        recs = xml_marc_to_records(self.test_append)
        # We call the main function with the record as a parameter
        info = bibupload(recs[0])
        # Now we append a datafield
        options['mode'] = 'append'
        # We add the controfield 001
        xml_with_controlfield = self.test_controfield001.replace('<controlfield tag ="001">002</controlfield>', '<controlfield tag ="001">'+str(info[1])+'</controlfield>')
        # We create create the record out of the xml marc
        recs = xml_marc_to_records(xml_with_controlfield)
        # We call the main function with the record as a parameter
        info = bibupload(recs[0])
        # We retrieve the inserted xml
        append_xml = print_record(int(info[1]),'xm')
        # Compare if the two MARCXML are the same
        self.failUnless(compare_xmlbuffers(append_xml, self.test_append_expected))

class BibUploadCorrectModeTest(unittest.TestCase):
    """Testing correct mode."""
    
    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize the MARCXML variable"""
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
        """bibupload - correct mode, correcting complete MARCXML file"""
        # Initialize the global variable
        options['mode'] = 'insert'
        options['verbose'] = 0
        # We create create the record out of the xml marc
        recs = xml_marc_to_records(self.test_correct)
        # We call the main function with the record as a parameter
        info = bibupload(recs[0])
        # Now we append a datafield
        options['mode'] = 'correct'
        # We add the controfield 001
        xml_with_controlfield = self.test_correct_expected.replace('<record>', '<record>\n<controlfield tag ="001">'+str(info[1])+'</controlfield>')
        # We create create the record out of the xml marc
        recs = xml_marc_to_records(xml_with_controlfield)
        # We call the main function with the record as a parameter
        info = bibupload(recs[0])
        # We retrieve the inserted xml
        correct_xml = print_record(int(info[1]),'xm')
        # Compare if the two MARCXML are the same
        self.failUnless(compare_xmlbuffers(correct_xml, self.test_correct_expected))

class BibUploadReplaceModeTest(unittest.TestCase):
    """Testing replace mode."""
    
    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize the MARCXML variable"""
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
        """bibupload - replace mode, replacing complete MARCXML file"""
        # Initialize the global variable
        options['mode'] = 'insert'
        options['verbose'] = 0
        # We create create the record out of the xml marc
        recs = xml_marc_to_records(self.test_replace)
        # We call the main function with the record as a parameter
        info = bibupload(recs[0])
        # Now we append a datafield
        options['mode'] = 'replace'
        # We add the controfield 001
        xml_with_controlfield = self.test_replace_expected.replace('<record>', '<record>\n<controlfield tag ="001">'+str(info[1])+'</controlfield>')
        # We create create the record out of the xml marc
        recs = xml_marc_to_records(xml_with_controlfield)
        # We call the main function with the record as a parameter
        info = bibupload(recs[0])
        # We retrieve the inserted xml
        replace_xml = print_record(int(info[1]),'xm')
        # Compare if the two MARCXML are the same
        self.failUnless(compare_xmlbuffers(replace_xml, self.test_replace_expected))
        
class BibUploadReferencesModeTest(unittest.TestCase):
    """Testing references mode."""
    
    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize the MARCXML variable"""
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
        """bibupload - reference mode, inserting complete MARCXML file"""
        # Initialize the global variable
        options['mode'] = 'insert'
        options['verbose'] = 0
        # We create create the record out of the xml marc
        recs = xml_marc_to_records(self.test_insert)
        # We call the main function with the record as a parameter
        info = bibupload(recs[0])
        # Now we append a datafield
        options['mode'] = 'reference'
        # We add the controfield 001
        xml_with_controlfield = self.test_reference.replace('<record>', '<record>\n<controlfield tag ="001">'+str(info[1])+'</controlfield>')
        # We create create the record out of the xml marc
        recs = xml_marc_to_records(xml_with_controlfield)
        # We call the main function with the record as a parameter
        info = bibupload(recs[0])
        # We retrieve the inserted xml
        reference_xml = print_record(int(info[1]),'xm')

        # Compare if the two MARCXML are the same
        self.failUnless(compare_xmlbuffers(reference_xml, self.test_reference_expected))

class BibUploadFMTModeTest(unittest.TestCase):
    """Testing FMT mode."""

    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize the MARCXML variable"""
        self.new_marcxml_with_fmt = """
        <record>
         <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="FMT" ind1="" ind2="">
          <subfield code="f">HB</subfield>
          <subfield code="g">Okay.</subfield>
         </datafield>
         <datafield tag="100" ind1="" ind2="">
          <subfield code="a">Bar, Baz</subfield>
          <subfield code="u">Foo</subfield>
         </datafield>
         <datafield tag="245" ind1="" ind2="">
          <subfield code="a">On the quux and huux</subfield>
         </datafield>
        </record>
        """
        self.expected_marcxml_after_inserting_new_marcxml_with_fmt = """
        <record>
         <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1="" ind2="">
          <subfield code="a">Bar, Baz</subfield>
          <subfield code="u">Foo</subfield>
         </datafield>
         <datafield tag="245" ind1="" ind2="">
          <subfield code="a">On the quux and huux</subfield>
         </datafield>
        </record>
        """
        self.recid10_marcxml_with_fmt = """
        <record>
         <controlfield tag="001">10</controlfield>
         <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="FMT" ind1="" ind2="">
          <subfield code="f">HB</subfield>
          <subfield code="g">Here is some format value.</subfield>
         </datafield>
         <datafield tag="100" ind1="" ind2="">
          <subfield code="a">Doe, John</subfield>
          <subfield code="u">CERN</subfield>
         </datafield>
         <datafield tag="245" ind1="" ind2="">
          <subfield code="a">On the foos and bars</subfield>
         </datafield>
        </record>
        """
        self.recid10_marcxml_with_fmt_only_first = """
        <record>
         <controlfield tag="001">10</controlfield>
         <datafield tag="FMT" ind1="" ind2="">
          <subfield code="f">HB</subfield>
          <subfield code="g">Let us see if this gets inserted well.</subfield>
         </datafield>
        </record>
        """
        self.recid10_marcxml_with_fmt_only_second = """
        <record>
         <controlfield tag="001">10</controlfield>
         <datafield tag="FMT" ind1="" ind2="">
          <subfield code="f">HB</subfield>
          <subfield code="g">Yet another test, to be run after the first one.</subfield>
         </datafield>
         <datafield tag="FMT" ind1="" ind2="">
          <subfield code="f">HD</subfield>
          <subfield code="g">Let's see what will be stored in the detailed format field.</subfield>
         </datafield>
        </record>
        """

    def test_inserting_new_record_containing_fmt_tag(self):
        """bibupload - FMT tag, inserting new record containing FMT tag"""
        options['mode'] = 'insert'
        options['verbose'] = 0
        recs = xml_marc_to_records(self.new_marcxml_with_fmt)
        (dummy, new_recid) = bibupload(recs[0])
        marcxml_after = print_record(new_recid, 'xm')    
        hb_after = print_record(new_recid, 'hb')
        self.failUnless(compare_xmlbuffers(marcxml_after,
                                           self.expected_marcxml_after_inserting_new_marcxml_with_fmt))
        self.failUnless(hb_after.startswith("Okay."))

    def test_updating_existing_record_formats_in_format_mode(self):
        """bibupload - FMT tag, updating existing record via format mode"""
        options['mode'] = 'format'
        options['verbose'] = 0
        marcxml_before = print_record(10, 'xm')
        # insert first format value:
        recs = xml_marc_to_records(self.recid10_marcxml_with_fmt_only_first)
        bibupload(recs[0])
        marcxml_after = print_record(10, 'xm')
        hb_after = print_record(10, 'hb')
        self.assertEqual(marcxml_after, marcxml_before)
        self.failUnless(hb_after.startswith("Let us see if this gets inserted well."))
        # now insert another format value and recheck:
        recs = xml_marc_to_records(self.recid10_marcxml_with_fmt_only_second)
        bibupload(recs[0])
        marcxml_after = print_record(10, 'xm')
        hb_after = print_record(10, 'hb')
        hd_after = print_record(10, 'hd')
        self.assertEqual(marcxml_after, marcxml_before)
        self.failUnless(hb_after.startswith("Yet another test, to be run after the first one."))
        self.failUnless(hd_after.startswith("Let's see what will be stored in the detailed format field."))

    def test_updating_existing_record_formats_in_correct_mode(self):
        """bibupload - FMT tag, updating existing record via correct mode"""
        options['mode'] = 'correct'
        options['verbose'] = 0
        marcxml_before = print_record(10, 'xm')
        # insert first format value:
        recs = xml_marc_to_records(self.recid10_marcxml_with_fmt_only_first)
        bibupload(recs[0])
        marcxml_after = print_record(10, 'xm')
        hb_after = print_record(10, 'hb')
        self.assertEqual(marcxml_after, marcxml_before)
        self.failUnless(hb_after.startswith("Let us see if this gets inserted well."))
        # now insert another format value and recheck:
        recs = xml_marc_to_records(self.recid10_marcxml_with_fmt_only_second)
        bibupload(recs[0])
        marcxml_after = print_record(10, 'xm')
        hb_after = print_record(10, 'hb')
        hd_after = print_record(10, 'hd')
        self.assertEqual(marcxml_after, marcxml_before)
        self.failUnless(hb_after.startswith("Yet another test, to be run after the first one."))
        self.failUnless(hd_after.startswith("Let's see what will be stored in the detailed format field."))

    def test_updating_existing_record_formats_in_replace_mode(self):
        """bibupload - FMT tag, updating existing record via replace mode"""
        options['mode'] = 'replace'
        options['verbose'] = 0
        # insert first format value:
        recs = xml_marc_to_records(self.recid10_marcxml_with_fmt_only_first)
        bibupload(recs[0])
        marcxml_after = print_record(10, 'xm')
        hb_after = print_record(10, 'hb')
        self.failUnless(compare_xmlbuffers(marcxml_after,
                                           '<record><controlfield tag="001">10</controlfield></record>'), 0)
        self.failUnless(hb_after.startswith("Let us see if this gets inserted well."))
        # now insert another format value and recheck:
        recs = xml_marc_to_records(self.recid10_marcxml_with_fmt_only_second)
        bibupload(recs[0])
        marcxml_after = print_record(10, 'xm')
        hb_after = print_record(10, 'hb')
        hd_after = print_record(10, 'hd')
        self.failUnless(compare_xmlbuffers(marcxml_after, """
                                           <record>
                                           <controlfield tag="001">10</controlfield>
                                           </record>""",
                                           0))
        self.failUnless(hb_after.startswith("Yet another test, to be run after the first one."))
        self.failUnless(hd_after.startswith("Let's see what will be stored in the detailed format field."))
        # final insertion and recheck:
        recs = xml_marc_to_records(self.recid10_marcxml_with_fmt)
        bibupload(recs[0])
        marcxml_after = print_record(10, 'xm')
        hb_after = print_record(10, 'hb')
        hd_after = print_record(10, 'hd')
        self.failUnless(compare_xmlbuffers(marcxml_after, """
                                           <record>
                                           <controlfield tag="001">10</controlfield>
                                           <controlfield tag="003">SzGeCERN</controlfield>
                                           <datafield tag="100" ind1="" ind2="">
                                           <subfield code="a">Doe, John</subfield>
                                           <subfield code="u">CERN</subfield>
                                           </datafield>
                                           <datafield tag="245" ind1="" ind2="">
                                           <subfield code="a">On the foos and bars</subfield>
                                           </datafield>
                                           </record>
                                           """,
                                           0))
        self.failUnless(hb_after.startswith("Here is some format value."))
        self.failUnless(hd_after.startswith("Let's see what will be stored in the detailed format field."))        

# FIXME: FFT tests wanted

test_suite = make_test_suite(BibUploadInsertModeTest,
                             BibUploadAppendModeTest,
                             BibUploadCorrectModeTest,
                             BibUploadReplaceModeTest,
                             BibUploadReferencesModeTest,
                             BibUploadFMTModeTest)

if __name__ == "__main__":
    warn_user_about_tests_and_run(test_suite)
