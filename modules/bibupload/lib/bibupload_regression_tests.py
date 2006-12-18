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

# pylint: disable-msg=C0301

"""Regression tests for the BibUpload."""

__revision__ = "$Id$"

import re
import unittest
import time

from invenio.config import CFG_OAI_ID_FIELD
from invenio import bibupload
from bibupload_config import CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG
from invenio.search_engine import print_record
from invenio.dbquery import run_sql
from invenio.dateutils import convert_datestruct_to_datetext
from invenio.testutils import make_test_suite, warn_user_about_tests_and_run

# helper functions:

def compare_xmbuffers(xmbuffer1, xmbuffer2, remove_tag_001_before_test_p=1):
    """Compare two XM (XML MARC)buffers by removing whitespaces before testing.
       Optionally the controlfield 001 is removed too."""

    def remove_blanks_from_xmbuffer(xmbuffer):
        """Remove \n and blanks from XMBUFFER."""
        out = xmbuffer.replace("\n", "")
        out = out.replace(" ", "")
        return out

    # take away 001:
    if remove_tag_001_before_test_p:
        xmbuffer1 = re.sub(r'<controlfield tag="001">.*</controlfield>', '', xmbuffer1)
        xmbuffer2 = re.sub(r'<controlfield tag="001">.*</controlfield>', '', xmbuffer2)

    # take away whitespace:
    xmbuffer1 = remove_blanks_from_xmbuffer(xmbuffer1)
    xmbuffer2 = remove_blanks_from_xmbuffer(xmbuffer2)

    return (xmbuffer1 == xmbuffer2)

def compare_hmbuffers(hmbuffer1, hmbuffer2,
                      remove_tag_001_before_test_p=1):
    """Compare two HM (HTML MARC) buffers by removing whitespaces before
       testing.  Optionally the controlfield 001 is removed too.
    """

    # remove eventual <pre>...</pre> formatting:
    hmbuffer1 = re.sub(r'^<pre>', '', hmbuffer1)
    hmbuffer2 = re.sub(r'^<pre>', '', hmbuffer2)
    hmbuffer1 = re.sub(r'</pre>$', '', hmbuffer1)
    hmbuffer2 = re.sub(r'</pre>$', '', hmbuffer2)

    # remove tag 001 eventually:
    if remove_tag_001_before_test_p:
        hmbuffer1 = re.sub(r'(^|\n)[0-9]{9}\s001__\s\d+($|\n)', '', hmbuffer1)
        hmbuffer2 = re.sub(r'(^|\n)[0-9]{9}\s001__\s\d+($|\n)', '', hmbuffer2)
        
    # remove leading recid, leaving only field values:
    hmbuffer1 = re.sub(r'(^|\n)[0-9]{9}\s', '', hmbuffer1)
    hmbuffer2 = re.sub(r'(^|\n)[0-9]{9}\s', '', hmbuffer2)

    # remove leading whitespace:
    hmbuffer1 = re.sub(r'(^|\n)\s+', '', hmbuffer1)
    hmbuffer2 = re.sub(r'(^|\n)\s+', '', hmbuffer2)

    return (hmbuffer1 == hmbuffer2)
           
class BibUploadInsertModeTest(unittest.TestCase):
    """Testing insert mode."""
    
    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialise the MARCXML variable"""
        self.test = """<record>
        <datafield tag ="245" ind1=" " ind2=" ">
        <subfield code="a">something</subfield>
        </datafield>
        <datafield tag ="700" ind1=" " ind2=" ">
        <subfield code="a">Tester, J Y</subfield>
        <subfield code="u">MIT</subfield>
        </datafield>
        <datafield tag ="700" ind1=" " ind2=" ">
        <subfield code="a">Tester, K J</subfield>
        <subfield code="u">CERN2</subfield>
        </datafield>
        <datafield tag ="700" ind1=" " ind2=" ">
        <subfield code="a">Tester, G</subfield>
        <subfield code="u">CERN3</subfield>
        </datafield>
        <datafield tag ="111" ind1=" " ind2=" ">
        <subfield code="a">test11</subfield>
        <subfield code="c">test31</subfield>
        </datafield>
        <datafield tag ="111" ind1=" " ind2=" ">
        <subfield code="a">test12</subfield>
        <subfield code="c">test32</subfield>
        </datafield>
        <datafield tag ="111" ind1=" " ind2=" ">
        <subfield code="a">test13</subfield>
        <subfield code="c">test33</subfield>
        </datafield>
        <datafield tag ="111" ind1=" " ind2=" ">
        <subfield code="b">test21</subfield>
        <subfield code="d">test41</subfield>
        </datafield>
        <datafield tag ="111" ind1=" " ind2=" ">
        <subfield code="b">test22</subfield>
        <subfield code="d">test42</subfield>
        </datafield>
        <datafield tag ="111" ind1=" " ind2=" ">
        <subfield code="a">test14</subfield>
        </datafield>
        <datafield tag ="111" ind1=" " ind2=" ">
        <subfield code="e">test51</subfield>
        </datafield>
        <datafield tag ="111" ind1=" " ind2=" ">
        <subfield code="e">test52</subfield>
        </datafield>
        <datafield tag ="100" ind1=" " ind2=" ">
        <subfield code="a">Tester, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""
        self.test_hm = """
        100__ $$aTester, T$$uCERN
        111__ $$atest11$$ctest31
        111__ $$atest12$$ctest32
        111__ $$atest13$$ctest33
        111__ $$btest21$$dtest41
        111__ $$btest22$$dtest42
        111__ $$atest14
        111__ $$etest51
        111__ $$etest52
        245__ $$asomething
        700__ $$aTester, J Y$$uMIT
        700__ $$aTester, K J$$uCERN2
        700__ $$aTester, G$$uCERN3
        """
    
    def test_create_record_id(self):
        """bibupload - insert mode, trying to create a new record ID in the database"""
        rec_id = bibupload.create_new_record()
        self.assertNotEqual(-1, rec_id)
    
    def test_no_retrieve_record_id(self):
        """bibupload - insert mode, detection of record ID in the input file"""
        # Initialize the global variable
        bibupload.options['mode'] = 'insert'
        # We create create the record out of the xml marc
        recs = bibupload.xml_marc_to_records(self.test)
        # We call the function which should retrieve the record id
        rec_id = bibupload.retrieve_rec_id(recs[0])
        # We compare the value found with None
        self.assertEqual(None, rec_id)
    
    def test_insert_complete_xmlmarc(self):
        """bibupload - insert mode, trying to insert complete MARCXML file"""
        # Initialize the global variable
        bibupload.options['mode'] = 'insert'
        bibupload.options['verbose'] = 0
        # We create create the record out of the xml marc
        recs = bibupload.xml_marc_to_records(self.test)
        # We call the main function with the record as a parameter
        err, recid = bibupload.bibupload(recs[0])
        # We retrieve the inserted xml
        inserted_xm = print_record(recid, 'xm')
        inserted_hm = print_record(recid, 'hm')
        # Compare if the two MARCXML are the same
        self.failUnless(compare_xmbuffers(inserted_xm, self.test))
        self.failUnless(compare_hmbuffers(inserted_hm, self.test_hm))
    
class BibUploadAppendModeTest(unittest.TestCase):
    """Testing append mode."""
    
    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize the MARCXML variable"""
        self.test_controfield001 = """<record>
        <controlfield tag ="001">002</controlfield>
        <datafield tag ="100" ind1=" " ind2=" ">
        <subfield code="a">Tester, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""
        self.test_append = """<record>
        <datafield tag ="100" ind1=" " ind2=" ">
        <subfield code="a">Tester, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""
        self.test_append_expected_xm = """<record>
        <datafield tag ="100" ind1=" " ind2=" ">
        <subfield code="a">Tester, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        <datafield tag ="100" ind1=" " ind2=" ">
        <subfield code="a">Tester, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""
        self.test_append_expected_hm = """
        100__ $$aTester, T$$uCERN
        100__ $$aTester, T$$uCERN
        """
        
    def test_retrieve_record_id(self):
        """bibupload - append mode, the input file should contain a record ID"""
        # Initialize the global variable
        bibupload.options['mode'] = 'append'
        bibupload.options['verbose'] = 0
        # We create create the record out of the xml marc
        recs = bibupload.xml_marc_to_records(self.test_controfield001)
        # We call the function which should retrieve the record id
        rec_id = bibupload.retrieve_rec_id(recs[0])
        # We compare the value found with None
        self.assertEqual('002', rec_id)
    
    def test_update_modification_record_date(self):
        """bibupload - append mode, checking the update of the modification date"""
        # Initialize the global variable
        bibupload.options['mode'] = 'append'
        bibupload.options['verbose'] = 0
        # We create create the record out of the xml marc
        recs = bibupload.xml_marc_to_records(self.test_controfield001)
        # We call the function which should retrieve the record id
        rec_id = bibupload.retrieve_rec_id(recs[0])
        # Retrieve current localtime
        now = time.localtime()
        # We update the modification date
        bibupload.update_bibrec_modif_date(convert_datestruct_to_datetext(now), rec_id)
        # We retrieve the modification date from the database
        query = """SELECT DATE_FORMAT(modification_date,'%%Y-%%m-%%d %%H:%%i:%%s') FROM bibrec where id = %s"""
        res = run_sql(query % rec_id)
        # We compare the two results
        self.assertEqual(res[0][0], convert_datestruct_to_datetext(now))
        
    def test_append_complete_xml_marc(self):
        """bibupload - append mode, appending complete MARCXML file"""
        # Initialize the global variable
        bibupload.options['mode'] = 'insert'
        bibupload.options['verbose'] = 0
        # We create create the record out of the xml marc
        recs = bibupload.xml_marc_to_records(self.test_append)
        # We call the main function with the record as a parameter
        err, recid = bibupload.bibupload(recs[0])
        # Now we append a datafield
        bibupload.options['mode'] = 'append'
        # We add the controfield 001
        xm_with_controlfield = self.test_controfield001.replace('<controlfield tag ="001">002</controlfield>',
                                                                 '<controlfield tag ="001">'+str(recid)+'</controlfield>')
        # We create create the record out of the xml marc
        recs = bibupload.xml_marc_to_records(xm_with_controlfield)
        # We call the main function with the record as a parameter
        err, recid = bibupload.bibupload(recs[0])
        # We retrieve the inserted xm
        append_xm = print_record(recid, 'xm')
        append_hm = print_record(recid, 'hm')
        # Compare if the two MARCXML are the same
        self.failUnless(compare_xmbuffers(append_xm, self.test_append_expected_xm))
        self.failUnless(compare_hmbuffers(append_hm, self.test_append_expected_hm))

class BibUploadCorrectModeTest(unittest.TestCase):
    """
    Testing correcting a record containing similar tags (identical
    tag, different indicators).  Currently CDS Invenio replaces only
    those tags that have matching indicators too, unlike ALEPH500 that
    does not pay attention to indicators, it corrects all fields with
    the same tag, regardless of the indicator values.
    """
    
    def setUp(self):
        """Initialize the MARCXML test record."""
        self.testrec1_xm = """
        <record>
        <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Test, Jane</subfield>
          <subfield code="u">Test Institute</subfield>
         </datafield>        
         <datafield tag="100" ind1="4" ind2="7">
          <subfield code="a">Test, John</subfield>
          <subfield code="u">Test University</subfield>
         </datafield>        
         <datafield tag="100" ind1="4" ind2="8">
          <subfield code="a">Cool</subfield>
         </datafield>        
         <datafield tag="100" ind1="4" ind2="7">
          <subfield code="a">Test, Jim</subfield>
          <subfield code="u">Test Laboratory</subfield>
         </datafield>        
        </record>
        """
        self.testrec1_hm = """
        003__ SzGeCERN
        100__ $$aTest, Jane$$uTest Institute
        10047 $$aTest, John$$uTest University
        10048 $$aCool
        10047 $$aTest, Jim$$uTest Laboratory
        """
        self.testrec1_xm_to_correct = """
        <record>
         <datafield tag="100" ind1="4" ind2="7">
          <subfield code="a">Test, Joseph</subfield>
          <subfield code="u">Test Academy</subfield>
         </datafield>        
         <datafield tag="100" ind1="4" ind2="7">
          <subfield code="a">Test2, Joseph</subfield>
          <subfield code="u">Test2 Academy</subfield>
         </datafield>        
        </record>
        """
        self.testrec1_corrected_xm = """
        <record>
        <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Test, Jane</subfield>
          <subfield code="u">Test Institute</subfield>
         </datafield>        
         <datafield tag="100" ind1="4" ind2="8">
          <subfield code="a">Cool</subfield>
         </datafield>        
         <datafield tag="100" ind1="4" ind2="7">
          <subfield code="a">Test, Joseph</subfield>
          <subfield code="u">Test Academy</subfield>
         </datafield>        
         <datafield tag="100" ind1="4" ind2="7">
          <subfield code="a">Test2, Joseph</subfield>
          <subfield code="u">Test2 Academy</subfield>
         </datafield>        
        </record>
        """
        self.testrec1_corrected_hm = """
        003__ SzGeCERN
        100__ $$aTest, Jane$$uTest Institute
        10048 $$aCool
        10047 $$aTest, Joseph$$uTest Academy
        10047 $$aTest2, Joseph$$uTest2 Academy
        """

    def test_record_correction(self):
        """bibupload - correct mode, similar MARCXML tags/indicators"""
        # insert original record
        bibupload.options['mode'] = 'insert'
        bibupload.options['verbose'] = 0
        recs = bibupload.xml_marc_to_records(self.testrec1_xm)
        err, recid = bibupload.bibupload(recs[0])
        inserted_xm = print_record(recid, 'xm')
        inserted_hm = print_record(recid, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm, self.testrec1_xm))
        self.failUnless(compare_hmbuffers(inserted_hm, self.testrec1_hm))
        # correct similar tags:
        bibupload.options['mode'] = 'correct'
        recs = bibupload.xml_marc_to_records(self.testrec1_xm_to_correct.replace('<record>',
                                                                                 '<record>\n<controlfield tag ="001">'+str(recid)+'</controlfield>'))
        err, recid = bibupload.bibupload(recs[0])
        corrected_xm = print_record(recid, 'xm')
        corrected_hm = print_record(recid, 'hm')
        self.failUnless(compare_xmbuffers(corrected_xm, self.testrec1_corrected_xm))
        self.failUnless(compare_hmbuffers(corrected_hm, self.testrec1_corrected_hm))
        # clean up after ourselves:
        bibupload.wipe_out_record_from_all_tables(recid)
        return

class BibUploadReplaceModeTest(unittest.TestCase):
    """Testing replace mode."""
    
    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize the MARCXML variable"""
        self.test_replace = """<record>
        <datafield tag ="100" ind1=" " ind2=" ">
        <subfield code="a">Tester, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""
        self.test_replace_expected_xm = """<record>
        <datafield tag ="100" ind1=" " ind2=" ">
        <subfield code="a">Test, T</subfield>
        <subfield code="u">TEST</subfield>
        </datafield>
        </record>"""
        self.test_replace_expected_hm = """
        100__ $$aTest, T$$uTEST
        """

    def test_replace_complete_xml_marc(self):
        """bibupload - replace mode, replacing complete MARCXML file"""
        # Initialize the global variable
        bibupload.options['mode'] = 'insert'
        bibupload.options['verbose'] = 0
        # We create create the record out of the xml marc
        recs = bibupload.xml_marc_to_records(self.test_replace)
        # We call the main function with the record as a parameter
        err, recid = bibupload.bibupload(recs[0])
        # Now we append a datafield
        bibupload.options['mode'] = 'replace'
        # We add the controfield 001
        xm_with_controlfield = self.test_replace_expected_xm.replace('<record>', '<record>\n<controlfield tag ="001">'+str(recid)+'</controlfield>')
        # We create create the record out of the xml marc
        recs = bibupload.xml_marc_to_records(xm_with_controlfield)
        # We call the main function with the record as a parameter
        err, recid = bibupload.bibupload(recs[0])
        # We retrieve the inserted xml
        replace_xm = print_record(recid, 'xm')
        replace_hm = print_record(recid, 'hm')
        # Compare if the two MARCXML are the same
        self.failUnless(compare_xmbuffers(replace_xm, self.test_replace_expected_xm))
        self.failUnless(compare_hmbuffers(replace_hm, self.test_replace_expected_hm))
        
class BibUploadReferencesModeTest(unittest.TestCase):
    """Testing references mode."""
    
    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize the MARCXML variable"""
        self.test_insert = """<record>
        <datafield tag ="100" ind1=" " ind2=" ">
        <subfield code="a">Tester, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""
        self.test_reference = """<record>
        <datafield tag =\"""" + bibupload.CFG_BIBUPLOAD_REFERENCE_TAG + """\" ind1="C" ind2="5">
        <subfield code="m">M. Lüscher and P. Weisz, String excitation energies in SU(N) gauge theories beyond the free-string approximation,</subfield>
        <subfield code="s">J. High Energy Phys. 07 (2004) 014</subfield>
        </datafield>
        </record>"""
        self.test_reference_expected_xm = """<record>
        <datafield tag ="100" ind1=" " ind2=" ">
        <subfield code="a">Tester, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        <datafield tag =\"""" + bibupload.CFG_BIBUPLOAD_REFERENCE_TAG + """\" ind1="C" ind2="5">
        <subfield code="m">M. Lüscher and P. Weisz, String excitation energies in SU(N) gauge theories beyond the free-string approximation,</subfield>
        <subfield code="s">J. High Energy Phys. 07 (2004) 014</subfield>
        </datafield>
        </record>"""
        self.test_reference_expected_hm = """
        100__ $$aTester, T$$uCERN
        %(reference_tag)sC5 $$mM. Lüscher and P. Weisz, String excitation energies in SU(N) gauge theories beyond the free-string approximation,$$sJ. High Energy Phys. 07 (2004) 014
        """ % {'reference_tag': bibupload.CFG_BIBUPLOAD_REFERENCE_TAG}
    
    def test_reference_complete_xml_marc(self):
        """bibupload - reference mode, inserting complete MARCXML file"""
        # Initialize the global variable
        bibupload.options['mode'] = 'insert'
        bibupload.options['verbose'] = 0
        # We create create the record out of the xml marc
        recs = bibupload.xml_marc_to_records(self.test_insert)
        # We call the main function with the record as a parameter
        err, recid = bibupload.bibupload(recs[0])
        # Now we append a datafield
        bibupload.options['mode'] = 'reference'
        # We add the controfield 001
        xm_with_controlfield = self.test_reference.replace('<record>', '<record>\n<controlfield tag ="001">'+str(recid)+'</controlfield>')
        # We create create the record out of the xml marc
        recs = bibupload.xml_marc_to_records(xm_with_controlfield)
        # We call the main function with the record as a parameter
        err, recid = bibupload.bibupload(recs[0])
        # We retrieve the inserted xml
        reference_xm = print_record(recid, 'xm')
        reference_hm = print_record(recid, 'hm')
        # Compare if the two MARCXML are the same
        self.failUnless(compare_xmbuffers(reference_xm, self.test_reference_expected_xm))
        self.failUnless(compare_hmbuffers(reference_hm, self.test_reference_expected_hm))

class BibUploadFMTModeTest(unittest.TestCase):
    """Testing FMT mode."""

    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize the MARCXML variable"""
        self.new_xm_with_fmt = """
        <record>
         <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="FMT" ind1=" " ind2=" ">
          <subfield code="f">HB</subfield>
          <subfield code="g">Test. Okay.</subfield>
         </datafield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Bar, Baz</subfield>
          <subfield code="u">Foo</subfield>
         </datafield>
         <datafield tag="245" ind1=" " ind2=" ">
          <subfield code="a">On the quux and huux</subfield>
         </datafield>
        </record>
        """
        self.expected_xm_after_inserting_new_xm_with_fmt = """
        <record>
         <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Bar, Baz</subfield>
          <subfield code="u">Foo</subfield>
         </datafield>
         <datafield tag="245" ind1=" " ind2=" ">
          <subfield code="a">On the quux and huux</subfield>
         </datafield>
        </record>
        """
        self.expected_hm_after_inserting_new_xm_with_fmt = """
        003__ SzGeCERN
        100__ $$aBar, Baz$$uFoo
        245__ $$aOn the quux and huux
        """
        self.recid3_xm_before_all_the_tests = print_record(3, 'xm')
        self.recid3_hm_before_all_the_tests = print_record(3, 'hm')
        self.recid3_xm_with_fmt = """
        <record>
         <controlfield tag="001">3</controlfield>
         <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="FMT" ind1=" " ind2=" ">
          <subfield code="f">HB</subfield>
          <subfield code="g">Test. Here is some format value.</subfield>
         </datafield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Doe, John</subfield>
          <subfield code="u">CERN</subfield>
         </datafield>
         <datafield tag="245" ind1=" " ind2=" ">
          <subfield code="a">On the foos and bars</subfield>
         </datafield>
        </record>
        """
        self.recid3_xm_with_fmt_only_first = """
        <record>
         <controlfield tag="001">3</controlfield>
         <datafield tag="FMT" ind1=" " ind2=" ">
          <subfield code="f">HB</subfield>
          <subfield code="g">Test. Let us see if this gets inserted well.</subfield>
         </datafield>
        </record>
        """
        self.recid3_xm_with_fmt_only_second = """
        <record>
         <controlfield tag="001">3</controlfield>
         <datafield tag="FMT" ind1=" " ind2=" ">
          <subfield code="f">HB</subfield>
          <subfield code="g">Test. Yet another test, to be run after the first one.</subfield>
         </datafield>
         <datafield tag="FMT" ind1=" " ind2=" ">
          <subfield code="f">HD</subfield>
          <subfield code="g">Test. Let's see what will be stored in the detailed format field.</subfield>
         </datafield>
        </record>
        """
          
    def restore_recid3(self):
        """Helper function that restores recID 3 MARCXML, using the
           value saved before all the tests started to execute.
           (see self.recid3_xm_before_all_the_tests).
           Does not restore HB and HD formats.
        """
        bibupload.options['mode'] = 'replace'
        bibupload.options['verbose'] = 0
        recs = bibupload.xml_marc_to_records(self.recid3_xm_before_all_the_tests)
        err, recid = bibupload.bibupload(recs[0])
        inserted_xm = print_record(recid, 'xm')
        inserted_hm = print_record(recid, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm, self.recid3_xm_before_all_the_tests))
        self.failUnless(compare_hmbuffers(inserted_hm, self.recid3_hm_before_all_the_tests))

    def test_inserting_new_record_containing_fmt_tag(self):
        """bibupload - FMT tag, inserting new record containing FMT tag"""
        bibupload.options['mode'] = 'insert'
        bibupload.options['verbose'] = 0
        recs = bibupload.xml_marc_to_records(self.new_xm_with_fmt)
        (dummy, new_recid) = bibupload.bibupload(recs[0])
        xm_after = print_record(new_recid, 'xm')    
        hm_after = print_record(new_recid, 'hm')    
        hb_after = print_record(new_recid, 'hb')
        self.failUnless(compare_xmbuffers(xm_after,
                                           self.expected_xm_after_inserting_new_xm_with_fmt))
        self.failUnless(compare_hmbuffers(hm_after,
                                          self.expected_hm_after_inserting_new_xm_with_fmt))
        self.failUnless(hb_after.startswith("Test. Okay."))

    def test_updating_existing_record_formats_in_format_mode(self):
        """bibupload - FMT tag, updating existing record via format mode"""
        bibupload.options['mode'] = 'format'
        bibupload.options['verbose'] = 0
        xm_before = print_record(3, 'xm')
        hm_before = print_record(3, 'hm')
        # insert first format value:
        recs = bibupload.xml_marc_to_records(self.recid3_xm_with_fmt_only_first)
        bibupload.bibupload(recs[0])
        xm_after = print_record(3, 'xm')
        hm_after = print_record(3, 'hm')
        hb_after = print_record(3, 'hb')
        self.assertEqual(xm_after, xm_before)
        self.assertEqual(hm_after, hm_before)
        self.failUnless(hb_after.startswith("Test. Let us see if this gets inserted well."))
        # now insert another format value and recheck:
        recs = bibupload.xml_marc_to_records(self.recid3_xm_with_fmt_only_second)
        bibupload.bibupload(recs[0])
        xm_after = print_record(3, 'xm')
        hm_after = print_record(3, 'hm')
        hb_after = print_record(3, 'hb')
        hd_after = print_record(3, 'hd')
        self.assertEqual(xm_after, xm_before)
        self.assertEqual(hm_after, hm_before)
        self.failUnless(hb_after.startswith("Test. Yet another test, to be run after the first one."))
        self.failUnless(hd_after.startswith("Test. Let's see what will be stored in the detailed format field."))
        # restore original record 3:
        self.restore_recid3()
        
    def test_updating_existing_record_formats_in_correct_mode(self):
        """bibupload - FMT tag, updating existing record via correct mode"""
        bibupload.options['mode'] = 'correct'
        bibupload.options['verbose'] = 0
        xm_before = print_record(3, 'xm')
        hm_before = print_record(3, 'hm')
        # insert first format value:
        recs = bibupload.xml_marc_to_records(self.recid3_xm_with_fmt_only_first)
        bibupload.bibupload(recs[0])
        xm_after = print_record(3, 'xm')
        hm_after = print_record(3, 'hm')
        hb_after = print_record(3, 'hb')
        self.assertEqual(xm_after, xm_before)
        self.assertEqual(hm_after, hm_before)
        self.failUnless(hb_after.startswith("Test. Let us see if this gets inserted well."))
        # now insert another format value and recheck:
        recs = bibupload.xml_marc_to_records(self.recid3_xm_with_fmt_only_second)
        bibupload.bibupload(recs[0])
        xm_after = print_record(3, 'xm')
        hm_after = print_record(3, 'hm')
        hb_after = print_record(3, 'hb')
        hd_after = print_record(3, 'hd')
        self.assertEqual(xm_after, xm_before)
        self.assertEqual(hm_after, hm_before)
        self.failUnless(hb_after.startswith("Test. Yet another test, to be run after the first one."))
        self.failUnless(hd_after.startswith("Test. Let's see what will be stored in the detailed format field."))
        # restore original record 3:
        self.restore_recid3()

    def test_updating_existing_record_formats_in_replace_mode(self):
        """bibupload - FMT tag, updating existing record via replace mode"""
        bibupload.options['mode'] = 'replace'
        bibupload.options['verbose'] = 0
        # insert first format value:
        recs = bibupload.xml_marc_to_records(self.recid3_xm_with_fmt_only_first)
        bibupload.bibupload(recs[0])
        xm_after = print_record(3, 'xm')
        hm_after = print_record(3, 'hm')
        hb_after = print_record(3, 'hb')
        self.failUnless(compare_xmbuffers(xm_after,
                                           '<record><controlfield tag="001">3</controlfield></record>'), 0)
        self.failUnless(compare_hmbuffers(hm_after,
                                          '000000003 001__ 3'), 0)
        self.failUnless(hb_after.startswith("Test. Let us see if this gets inserted well."))
        # now insert another format value and recheck:
        recs = bibupload.xml_marc_to_records(self.recid3_xm_with_fmt_only_second)
        bibupload.bibupload(recs[0])
        xm_after = print_record(3, 'xm')
        hm_after = print_record(3, 'hm')
        hb_after = print_record(3, 'hb')
        hd_after = print_record(3, 'hd')
        self.failUnless(compare_xmbuffers(xm_after, """
                                           <record>
                                           <controlfield tag="001">3</controlfield>
                                           </record>""",
                                           0))
        self.failUnless(compare_hmbuffers(hm_after, '000000003 001__ 3',
                                           0))
        self.failUnless(hb_after.startswith("Test. Yet another test, to be run after the first one."))
        self.failUnless(hd_after.startswith("Test. Let's see what will be stored in the detailed format field."))
        # final insertion and recheck:
        recs = bibupload.xml_marc_to_records(self.recid3_xm_with_fmt)
        bibupload.bibupload(recs[0])
        xm_after = print_record(3, 'xm')
        hm_after = print_record(3, 'hm')
        hb_after = print_record(3, 'hb')
        hd_after = print_record(3, 'hd')
        self.failUnless(compare_xmbuffers(xm_after, """
                                           <record>
                                           <controlfield tag="001">3</controlfield>
                                           <controlfield tag="003">SzGeCERN</controlfield>
                                           <datafield tag="100" ind1=" " ind2=" ">
                                           <subfield code="a">Doe, John</subfield>
                                           <subfield code="u">CERN</subfield>
                                           </datafield>
                                           <datafield tag="245" ind1=" " ind2=" ">
                                           <subfield code="a">On the foos and bars</subfield>
                                           </datafield>
                                           </record>
                                           """,
                                           0))
        self.failUnless(compare_hmbuffers(hm_after, """
                                           001__ 3
                                           003__ SzGeCERN
                                           100__ $$aDoe, John$$uCERN
                                           245__ $$aOn the foos and bars
                                           """,
                                           0))
        self.failUnless(hb_after.startswith("Test. Here is some format value."))
        self.failUnless(hd_after.startswith("Test. Let's see what will be stored in the detailed format field."))
        # restore original record 3:
        self.restore_recid3()

class BibUploadRecordsWithSYSNOTest(unittest.TestCase):
    """Testing uploading of records that have external SYSNO present."""

    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize the MARCXML test records."""
        self.verbose = 0
        # Note that SYSNO fields are repeated but with different
        # subfields, this is to test whether bibupload would not
        # mistakenly pick up wrong values.
        self.xm_testrec1 = """
        <record>
         <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Bar, Baz</subfield>
          <subfield code="u">Foo</subfield>
         </datafield>
         <datafield tag="245" ind1=" " ind2=" ">
          <subfield code="a">On the quux and huux 1</subfield>
         </datafield>
         <datafield tag="%(sysnotag)s" ind1="%(sysnoind1)s" ind2="%(sysnoind2)s">
          <subfield code="%(sysnosubfieldcode)s">sysno1</subfield>
         </datafield>
         <datafield tag="%(sysnotag)s" ind1="%(sysnoind1)s" ind2="%(sysnoind2)s">
          <subfield code="0">sysno2</subfield>
         </datafield>
        </record>
        """ % {'sysnotag': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[0:3],
               'sysnoind1': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[3:4] != "_" and \
                            CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[3:4] or " ",
               'sysnoind2': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[4:5] != "_" and \
                            CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[4:5] or " ",
               'sysnosubfieldcode': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[5:6],
               }
        self.hm_testrec1 = """
        003__ SzGeCERN
        100__ $$aBar, Baz$$uFoo
        245__ $$aOn the quux and huux 1
        %(sysnotag)s%(sysnoind1)s%(sysnoind2)s $$%(sysnosubfieldcode)ssysno1
        %(sysnotag)s%(sysnoind1)s%(sysnoind2)s $$0sysno2
        """ % {'sysnotag': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[0:3],
               'sysnoind1': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[3:4],
               'sysnoind2': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[4:5],
               'sysnosubfieldcode': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[5:6],
               }
        self.xm_testrec1_updated = """
        <record>
         <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Bar, Baz</subfield>
          <subfield code="u">Foo</subfield>
         </datafield>
         <datafield tag="245" ind1=" " ind2=" ">
          <subfield code="a">On the quux and huux 1 Updated</subfield>
         </datafield>
         <datafield tag="%(sysnotag)s" ind1="%(sysnoind1)s" ind2="%(sysnoind2)s">
          <subfield code="%(sysnosubfieldcode)s">sysno1</subfield>
         </datafield>
         <datafield tag="%(sysnotag)s" ind1="%(sysnoind1)s" ind2="%(sysnoind2)s">
          <subfield code="0">sysno2</subfield>
         </datafield>
        </record>
        """ % {'sysnotag': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[0:3],
               'sysnoind1': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[3:4] != "_" and \
                            CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[3:4] or " ",
               'sysnoind2': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[4:5] != "_" and \
                            CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[4:5] or " ",
               'sysnosubfieldcode': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[5:6],
               }
        self.hm_testrec1_updated = """
        003__ SzGeCERN
        100__ $$aBar, Baz$$uFoo
        245__ $$aOn the quux and huux 1 Updated
        %(sysnotag)s%(sysnoind1)s%(sysnoind2)s $$%(sysnosubfieldcode)ssysno1
        %(sysnotag)s%(sysnoind1)s%(sysnoind2)s $$0sysno2
        """ % {'sysnotag': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[0:3],
               'sysnoind1': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[3:4],
               'sysnoind2': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[4:5],
               'sysnosubfieldcode': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[5:6],
               }
        self.xm_testrec2 = """
        <record>
         <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Bar, Baz</subfield>
          <subfield code="u">Foo</subfield>
         </datafield>
         <datafield tag="245" ind1=" " ind2=" ">
          <subfield code="a">On the quux and huux 2</subfield>
         </datafield>
         <datafield tag="%(sysnotag)s" ind1="%(sysnoind1)s" ind2="%(sysnoind2)s">
          <subfield code="%(sysnosubfieldcode)s">sysno2</subfield>
         </datafield>
         <datafield tag="%(sysnotag)s" ind1="%(sysnoind1)s" ind2="%(sysnoind2)s">
          <subfield code="0">sysno1</subfield>
         </datafield>
        </record>
        """ % {'sysnotag': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[0:3],
               'sysnoind1': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[3:4] != "_" and \
                            CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[3:4] or " ",
               'sysnoind2': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[4:5] != "_" and \
                            CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[4:5] or " ",
               'sysnosubfieldcode': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[5:6],
               }
        self.hm_testrec2 = """
        003__ SzGeCERN
        100__ $$aBar, Baz$$uFoo
        245__ $$aOn the quux and huux 2
        %(sysnotag)s%(sysnoind1)s%(sysnoind2)s $$%(sysnosubfieldcode)ssysno2
        %(sysnotag)s%(sysnoind1)s%(sysnoind2)s $$0sysno1
        """ % {'sysnotag': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[0:3],
               'sysnoind1': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[3:4],
               'sysnoind2': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[4:5],
               'sysnosubfieldcode': CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[5:6],
               }

    def test_insert_the_same_sysno_record(self):
        """bibupload - SYSNO tag, refuse to insert the same SYSNO record"""
        # initialize bibupload mode:
        bibupload.options['mode'] = 'insert'
        bibupload.options['verbose'] = self.verbose
        if self.verbose:
            print "test_insert_the_same_sysno_record() started"
        # insert record 1 first time:
        recs = bibupload.xml_marc_to_records(self.xm_testrec1)
        err1, recid1 = bibupload.bibupload(recs[0])
        inserted_xm = print_record(recid1, 'xm')
        inserted_hm = print_record(recid1, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec1))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec1))
        # insert record 2 first time:
        recs = bibupload.xml_marc_to_records(self.xm_testrec2)
        err2, recid2 = bibupload.bibupload(recs[0])
        inserted_xm = print_record(recid2, 'xm')
        inserted_hm = print_record(recid2, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec2))        
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec2))
        # try to insert updated record 1, it should fail:
        recs = bibupload.xml_marc_to_records(self.xm_testrec1_updated)
        err1_updated, recid1_updated = bibupload.bibupload(recs[0])
        self.assertEqual(-1, recid1_updated)
        # delete test records
        bibupload.wipe_out_record_from_all_tables(recid1)
        bibupload.wipe_out_record_from_all_tables(recid2)
        bibupload.wipe_out_record_from_all_tables(recid1_updated)
        if self.verbose:
            print "test_insert_the_same_sysno_record() finished"

    def test_insert_or_replace_the_same_sysno_record(self):
        """bibupload - SYSNO tag, allow to insert or replace the same SYSNO record"""
        # initialize bibupload mode:
        bibupload.options['mode'] = 'replace_or_insert'
        bibupload.options['verbose'] = self.verbose
        if self.verbose:
            print "test_insert_or_replace_the_same_sysno_record() started"
        # insert/replace record 1 first time:
        recs = bibupload.xml_marc_to_records(self.xm_testrec1)
        err1, recid1 = bibupload.bibupload(recs[0])
        inserted_xm = print_record(recid1, 'xm')
        inserted_hm = print_record(recid1, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec1))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                          self.hm_testrec1))
        # try to insert/replace updated record 1, it should be okay:
        bibupload.options['mode'] = 'replace_or_insert'
        bibupload.options['verbose'] = self.verbose
        recs = bibupload.xml_marc_to_records(self.xm_testrec1_updated)
        err1_updated, recid1_updated = bibupload.bibupload(recs[0])
        inserted_xm = print_record(recid1_updated, 'xm')
        inserted_hm = print_record(recid1_updated, 'hm')
        self.assertEqual(recid1, recid1_updated)
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec1_updated))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec1_updated))
        # delete test records
        bibupload.wipe_out_record_from_all_tables(recid1)
        bibupload.wipe_out_record_from_all_tables(recid1_updated)
        if self.verbose:
            print "test_insert_or_replace_the_same_sysno_record() finished"

    def test_replace_nonexisting_sysno_record(self):
        """bibupload - SYSNO tag, refuse to replace non-existing SYSNO record"""
        # initialize bibupload mode:
        bibupload.options['mode'] = 'replace_or_insert'
        bibupload.options['verbose'] = self.verbose
        if self.verbose:
            print "test_replace_nonexisting_sysno_record() started"
        # insert record 1 first time:
        recs = bibupload.xml_marc_to_records(self.xm_testrec1)
        err1, recid1 = bibupload.bibupload(recs[0])
        inserted_xm = print_record(recid1, 'xm')
        inserted_hm = print_record(recid1, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec1))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec1))
        # try to replace record 2 it should fail:
        bibupload.options['mode'] = 'replace'
        bibupload.options['verbose'] = self.verbose
        recs = bibupload.xml_marc_to_records(self.xm_testrec2)
        err2, recid2 = bibupload.bibupload(recs[0])
        self.assertEqual(-1, recid2)
        # delete test records
        bibupload.wipe_out_record_from_all_tables(recid1)
        bibupload.wipe_out_record_from_all_tables(recid2)
        if self.verbose:
            print "test_replace_nonexisting_sysno_record() finished"

class BibUploadRecordsWithOAIIDTest(unittest.TestCase):
    """Testing uploading of records that have OAI ID present."""

    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize the MARCXML test records."""
        self.verbose = 0
        # Note that OAI fields are repeated but with different
        # subfields, this is to test whether bibupload would not
        # mistakenly pick up wrong values.
        self.xm_testrec1 = """
        <record>
         <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Bar, Baz</subfield>
          <subfield code="u">Foo</subfield>
         </datafield>
         <datafield tag="245" ind1=" " ind2=" ">
          <subfield code="a">On the quux and huux 1</subfield>
         </datafield>
         <datafield tag="%(oaitag)s" ind1="%(oaiind1)s" ind2="%(oaiind2)s">
          <subfield code="%(oaisubfieldcode)s">oai:foo:1</subfield>
         </datafield>
         <datafield tag="%(oaitag)s" ind1="%(oaiind1)s" ind2="%(oaiind2)s">
          <subfield code="0">oai:foo:2</subfield>
         </datafield>
        </record>
        """ % {'oaitag': CFG_OAI_ID_FIELD[0:3],
               'oaiind1': CFG_OAI_ID_FIELD[3:4] != "_" and \
                          CFG_OAI_ID_FIELD[3:4] or " ",
               'oaiind2': CFG_OAI_ID_FIELD[4:5] != "_" and \
                          CFG_OAI_ID_FIELD[4:5] or " ",
               'oaisubfieldcode': CFG_OAI_ID_FIELD[5:6],
               }
        self.hm_testrec1 = """
        003__ SzGeCERN
        100__ $$aBar, Baz$$uFoo
        245__ $$aOn the quux and huux 1
        %(oaitag)s%(oaiind1)s%(oaiind2)s $$%(oaisubfieldcode)soai:foo:1
        %(oaitag)s%(oaiind1)s%(oaiind2)s $$0oai:foo:2
        """ % {'oaitag': CFG_OAI_ID_FIELD[0:3],
               'oaiind1': CFG_OAI_ID_FIELD[3:4],
               'oaiind2': CFG_OAI_ID_FIELD[4:5],
               'oaisubfieldcode': CFG_OAI_ID_FIELD[5:6],
               }
        self.xm_testrec1_updated = """
        <record>
         <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Bar, Baz</subfield>
          <subfield code="u">Foo</subfield>
         </datafield>
         <datafield tag="245" ind1=" " ind2=" ">
          <subfield code="a">On the quux and huux 1 Updated</subfield>
         </datafield>
         <datafield tag="%(oaitag)s" ind1="%(oaiind1)s" ind2="%(oaiind2)s">
          <subfield code="%(oaisubfieldcode)s">oai:foo:1</subfield>
         </datafield>
         <datafield tag="%(oaitag)s" ind1="%(oaiind1)s" ind2="%(oaiind2)s">
          <subfield code="0">oai:foo:2</subfield>
         </datafield>
        </record>
        """ % {'oaitag': CFG_OAI_ID_FIELD[0:3],
               'oaiind1': CFG_OAI_ID_FIELD[3:4] != "_" and \
                          CFG_OAI_ID_FIELD[3:4] or " ",
               'oaiind2': CFG_OAI_ID_FIELD[4:5] != "_" and \
                          CFG_OAI_ID_FIELD[4:5] or " ",
               'oaisubfieldcode': CFG_OAI_ID_FIELD[5:6],
               }
        self.hm_testrec1_updated = """
        003__ SzGeCERN
        100__ $$aBar, Baz$$uFoo
        245__ $$aOn the quux and huux 1 Updated
        %(oaitag)s%(oaiind1)s%(oaiind2)s $$%(oaisubfieldcode)soai:foo:1
        %(oaitag)s%(oaiind1)s%(oaiind2)s $$0oai:foo:2
        """ % {'oaitag': CFG_OAI_ID_FIELD[0:3],
               'oaiind1': CFG_OAI_ID_FIELD[3:4],
               'oaiind2': CFG_OAI_ID_FIELD[4:5],
               'oaisubfieldcode': CFG_OAI_ID_FIELD[5:6],
               }
        self.xm_testrec2 = """
        <record>
         <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Bar, Baz</subfield>
          <subfield code="u">Foo</subfield>
         </datafield>
         <datafield tag="245" ind1=" " ind2=" ">
          <subfield code="a">On the quux and huux 2</subfield>
         </datafield>
         <datafield tag="%(oaitag)s" ind1="%(oaiind1)s" ind2="%(oaiind2)s">
          <subfield code="%(oaisubfieldcode)s">oai:foo:2</subfield>
         </datafield>
         <datafield tag="%(oaitag)s" ind1="%(oaiind1)s" ind2="%(oaiind2)s">
          <subfield code="0">oai:foo:1</subfield>
         </datafield>
        </record>
        """ % {'oaitag': CFG_OAI_ID_FIELD[0:3],
               'oaiind1': CFG_OAI_ID_FIELD[3:4] != "_" and \
                          CFG_OAI_ID_FIELD[3:4] or " ",
               'oaiind2': CFG_OAI_ID_FIELD[4:5] != "_" and \
                          CFG_OAI_ID_FIELD[4:5] or " ",
               'oaisubfieldcode': CFG_OAI_ID_FIELD[5:6],
               }
        self.hm_testrec2 = """
        003__ SzGeCERN
        100__ $$aBar, Baz$$uFoo
        245__ $$aOn the quux and huux 2
        %(oaitag)s%(oaiind1)s%(oaiind2)s $$%(oaisubfieldcode)soai:foo:2
        %(oaitag)s%(oaiind1)s%(oaiind2)s $$0oai:foo:1
        """ % {'oaitag': CFG_OAI_ID_FIELD[0:3],
               'oaiind1': CFG_OAI_ID_FIELD[3:4],
               'oaiind2': CFG_OAI_ID_FIELD[4:5],
               'oaisubfieldcode': CFG_OAI_ID_FIELD[5:6],
               }

    def test_insert_the_same_oai_record(self):
        """bibupload - OAI tag, refuse to insert the same OAI record"""
        # initialize bibupload mode:
        bibupload.options['mode'] = 'insert'
        bibupload.options['verbose'] = self.verbose
        # insert record 1 first time:
        recs = bibupload.xml_marc_to_records(self.xm_testrec1)
        err1, recid1 = bibupload.bibupload(recs[0])
        inserted_xm = print_record(recid1, 'xm')
        inserted_hm = print_record(recid1, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec1))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec1))
        # insert record 2 first time:
        recs = bibupload.xml_marc_to_records(self.xm_testrec2)
        err2, recid2 = bibupload.bibupload(recs[0])
        inserted_xm = print_record(recid2, 'xm')
        inserted_hm = print_record(recid2, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec2))        
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec2))        
        # try to insert updated record 1, it should fail:
        recs = bibupload.xml_marc_to_records(self.xm_testrec1_updated)
        err1_updated, recid1_updated = bibupload.bibupload(recs[0])
        self.assertEqual(-1, recid1_updated)
        # delete test records
        bibupload.wipe_out_record_from_all_tables(recid1)
        bibupload.wipe_out_record_from_all_tables(recid2)
        bibupload.wipe_out_record_from_all_tables(recid1_updated)

    def test_insert_or_replace_the_same_oai_record(self):
        """bibupload - OAI tag, allow to insert or replace the same OAI record"""
        # initialize bibupload mode:
        bibupload.options['mode'] = 'replace_or_insert'
        bibupload.options['verbose'] = self.verbose
        # insert/replace record 1 first time:
        recs = bibupload.xml_marc_to_records(self.xm_testrec1)
        err1, recid1 = bibupload.bibupload(recs[0])
        inserted_xm = print_record(recid1, 'xm')
        inserted_hm = print_record(recid1, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec1))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec1))
        # try to insert/replace updated record 1, it should be okay:
        bibupload.options['mode'] = 'replace_or_insert'
        bibupload.options['verbose'] = self.verbose
        recs = bibupload.xml_marc_to_records(self.xm_testrec1_updated)
        err1_updated, recid1_updated = bibupload.bibupload(recs[0])
        inserted_xm = print_record(recid1_updated, 'xm')
        inserted_hm = print_record(recid1_updated, 'hm')
        self.assertEqual(recid1, recid1_updated)
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec1_updated))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec1_updated))
        # delete test records
        bibupload.wipe_out_record_from_all_tables(recid1)
        bibupload.wipe_out_record_from_all_tables(recid1_updated)

    def test_replace_nonexisting_oai_record(self):
        """bibupload - OAI tag, refuse to replace non-existing OAI record"""
        # initialize bibupload mode:
        bibupload.options['mode'] = 'replace_or_insert'
        bibupload.options['verbose'] = self.verbose
        # insert record 1 first time:
        recs = bibupload.xml_marc_to_records(self.xm_testrec1)
        err1, recid1 = bibupload.bibupload(recs[0])
        inserted_xm = print_record(recid1, 'xm')
        inserted_hm = print_record(recid1, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec1))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec1))
        # try to replace record 2 it should fail:
        bibupload.options['mode'] = 'replace'
        bibupload.options['verbose'] = self.verbose
        recs = bibupload.xml_marc_to_records(self.xm_testrec2)
        err2, recid2 = bibupload.bibupload(recs[0])
        self.assertEqual(-1, recid2)
        # delete test records
        bibupload.wipe_out_record_from_all_tables(recid1)
        bibupload.wipe_out_record_from_all_tables(recid2)

class BibUploadIndicatorsTest(unittest.TestCase):
    """
    Testing uploading of a MARCXML record with indicators having
    either blank space (as per MARC schema) or empty string value (old
    behaviour).
    """
    
    def setUp(self):
        """Initialize the MARCXML test record."""
        self.testrec1_xm = """
        <record>
        <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Test, John</subfield>
          <subfield code="u">Test University</subfield>
         </datafield>        
        </record>
        """
        self.testrec1_hm = """
        003__ SzGeCERN
        100__ $$aTest, John$$uTest University
        """
        self.testrec2_xm = """
        <record>
        <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1="" ind2="">
          <subfield code="a">Test, John</subfield>
          <subfield code="u">Test University</subfield>
         </datafield>        
        </record>
        """
        self.testrec2_hm = """
        003__ SzGeCERN
        100__ $$aTest, John$$uTest University
        """

    def test_record_with_spaces_in_indicators(self):
        """bibupload - inserting MARCXML with spaces in indicators"""
        bibupload.options['mode'] = 'insert'
        bibupload.options['verbose'] = 0
        recs = bibupload.xml_marc_to_records(self.testrec1_xm)
        err, recid = bibupload.bibupload(recs[0])
        inserted_xm = print_record(recid, 'xm')
        inserted_hm = print_record(recid, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm, self.testrec1_xm))
        self.failUnless(compare_hmbuffers(inserted_hm, self.testrec1_hm))
        bibupload.wipe_out_record_from_all_tables(recid)

    def test_record_with_no_spaces_in_indicators(self):
        """bibupload - inserting MARCXML with no spaces in indicators"""
        bibupload.options['mode'] = 'insert'
        bibupload.options['verbose'] = 0
        recs = bibupload.xml_marc_to_records(self.testrec2_xm)
        err, recid = bibupload.bibupload(recs[0])
        inserted_xm = print_record(recid, 'xm')
        inserted_hm = print_record(recid, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm, self.testrec2_xm))
        self.failUnless(compare_hmbuffers(inserted_hm, self.testrec2_hm))
        bibupload.wipe_out_record_from_all_tables(recid)

# FIXME: "strong tags" tests wanted

# FIXME: FFT tests wanted

test_suite = make_test_suite(BibUploadInsertModeTest,
                             BibUploadAppendModeTest,
                             BibUploadCorrectModeTest,
                             BibUploadReplaceModeTest,
                             BibUploadReferencesModeTest,
                             BibUploadRecordsWithSYSNOTest,
                             BibUploadRecordsWithOAIIDTest,                             
                             BibUploadFMTModeTest,
                             BibUploadIndicatorsTest,)

if __name__ == "__main__":
    warn_user_about_tests_and_run(test_suite)
