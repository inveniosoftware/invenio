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

# pylint: disable-msg=C0301

"""Regression tests for the BibUpload."""

__revision__ = "$Id$"

import re
import unittest
import time

from invenio.config import CFG_OAI_ID_FIELD, CFG_PREFIX, weburl
from invenio import bibupload
from bibupload_config import CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG, \
                             CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG, \
                             CFG_BIBUPLOAD_STRONG_TAGS
from invenio.search_engine import print_record
from invenio.dbquery import run_sql
from invenio.dateutils import convert_datestruct_to_datetext
from invenio.testutils import make_test_suite, warn_user_about_tests_and_run
from invenio.bibtask import task_set_option

# helper functions:

def remove_tag_001_from_xmbuffer(xmbuffer):
    """Remove tag 001 from MARCXML buffer.  Useful for testing two
       MARCXML buffers without paying attention to recIDs attributed
       during the bibupload.
    """
    return re.sub(r'<controlfield tag="001">.*</controlfield>', '', xmbuffer)

def compare_xmbuffers(xmbuffer1, xmbuffer2):
    """Compare two XM (XML MARC) buffers by removing whitespaces
       before testing.
    """

    def remove_blanks_from_xmbuffer(xmbuffer):
        """Remove \n and blanks from XMBUFFER."""
        out = xmbuffer.replace("\n", "")
        out = out.replace(" ", "")
        return out

    # remove whitespace:
    xmbuffer1 = remove_blanks_from_xmbuffer(xmbuffer1)
    xmbuffer2 = remove_blanks_from_xmbuffer(xmbuffer2)

    if xmbuffer1 != xmbuffer2:
        print "\n=" + xmbuffer1 + "=\n"
        print "\n=" + xmbuffer2 + "=\n"

    return (xmbuffer1 == xmbuffer2)

def remove_tag_001_from_hmbuffer(hmbuffer):
    """Remove tag 001 from HTML MARC buffer.  Useful for testing two
       HTML MARC buffers without paying attention to recIDs attributed
       during the bibupload.
    """
    return re.sub(r'(^|\n)(<pre>)?[0-9]{9}\s001__\s\d+($|\n)', '', hmbuffer)

def compare_hmbuffers(hmbuffer1, hmbuffer2):
    """Compare two HM (HTML MARC) buffers by removing whitespaces
       before testing.
    """

    # remove eventual <pre>...</pre> formatting:
    hmbuffer1 = re.sub(r'^<pre>', '', hmbuffer1)
    hmbuffer2 = re.sub(r'^<pre>', '', hmbuffer2)
    hmbuffer1 = re.sub(r'</pre>$', '', hmbuffer1)
    hmbuffer2 = re.sub(r'</pre>$', '', hmbuffer2)

    # remove leading recid, leaving only field values:
    hmbuffer1 = re.sub(r'(^|\n)[0-9]{9}\s', '', hmbuffer1)
    hmbuffer2 = re.sub(r'(^|\n)[0-9]{9}\s', '', hmbuffer2)

    # remove leading whitespace:
    hmbuffer1 = re.sub(r'(^|\n)\s+', '', hmbuffer1)
    hmbuffer2 = re.sub(r'(^|\n)\s+', '', hmbuffer2)

    if hmbuffer1 != hmbuffer2:
        print "\n=" + hmbuffer1 + "=\n"
        print "\n=" + hmbuffer2 + "=\n"

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
        # We create create the record out of the xml marc
        recs = bibupload.xml_marc_to_records(self.test)
        # We call the function which should retrieve the record id
        rec_id = bibupload.retrieve_rec_id(recs[0], 'insert')
        # We compare the value found with None
        self.assertEqual(None, rec_id)

    def test_insert_complete_xmlmarc(self):
        """bibupload - insert mode, trying to insert complete MARCXML file"""
        # Initialize the global variable
        task_set_option('verbose', 0)
        # We create create the record out of the xml marc
        recs = bibupload.xml_marc_to_records(self.test)
        # We call the main function with the record as a parameter
        err, recid = bibupload.bibupload(recs[0], opt_mode='insert')
        # We retrieve the inserted xml
        inserted_xm = print_record(recid, 'xm')
        inserted_hm = print_record(recid, 'hm')
        # Compare if the two MARCXML are the same
        self.failUnless(compare_xmbuffers(remove_tag_001_from_xmbuffer(inserted_xm),
                                          self.test))
        self.failUnless(compare_hmbuffers(remove_tag_001_from_hmbuffer(inserted_hm),
                                          self.test_hm))

class BibUploadAppendModeTest(unittest.TestCase):
    """Testing append mode."""

    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize the MARCXML variable"""
        self.test_existing = """<record>
        <controlfield tag="001">123456789</controlfield>
        <datafield tag ="100" ind1=" " ind2=" ">
        <subfield code="a">Tester, T</subfield>
        <subfield code="u">DESY</subfield>
        </datafield>
        </record>"""
        self.test_to_append = """<record>
        <controlfield tag="001">123456789</controlfield>
        <datafield tag ="100" ind1=" " ind2=" ">
        <subfield code="a">Tester, U</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""
        self.test_expected_xm = """<record>
        <controlfield tag="001">123456789</controlfield>
        <datafield tag ="100" ind1=" " ind2=" ">
        <subfield code="a">Tester, T</subfield>
        <subfield code="u">DESY</subfield>
        </datafield>
        <datafield tag ="100" ind1=" " ind2=" ">
        <subfield code="a">Tester, U</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""
        self.test_expected_hm = """
        001__ 123456789
        100__ $$aTester, T$$uDESY
        100__ $$aTester, U$$uCERN
        """
        # insert test record:

        test_to_upload =  self.test_existing.replace('<controlfield tag="001">123456789</controlfield>',
                                                     '')
        recs = bibupload.xml_marc_to_records(test_to_upload)
        err, recid = bibupload.bibupload(recs[0], opt_mode='insert')
        self.test_recid = recid
        # replace test buffers with real recid of inserted test record:
        self.test_existing = self.test_existing.replace('123456789',
                                                        str(self.test_recid))
        self.test_to_append = self.test_to_append.replace('123456789',
                                                          str(self.test_recid))
        self.test_expected_xm = self.test_expected_xm.replace('123456789',
                                                              str(self.test_recid))
        self.test_expected_hm = self.test_expected_hm.replace('123456789',
                                                              str(self.test_recid))

    def test_retrieve_record_id(self):
        """bibupload - append mode, the input file should contain a record ID"""
        task_set_option('verbose', 0)
        # We create create the record out of the xml marc
        recs = bibupload.xml_marc_to_records(self.test_to_append)
        # We call the function which should retrieve the record id
        rec_id = bibupload.retrieve_rec_id(recs[0], 'append')
        # We compare the value found with None
        self.assertEqual(str(self.test_recid), rec_id)
        # clean up after ourselves:
        bibupload.wipe_out_record_from_all_tables(self.test_recid)
        return

    def test_update_modification_record_date(self):
        """bibupload - append mode, checking the update of the modification date"""
        # Initialize the global variable
        task_set_option('verbose', 0)
        # We create create the record out of the xml marc
        recs = bibupload.xml_marc_to_records(self.test_existing)
        # We call the function which should retrieve the record id
        rec_id = bibupload.retrieve_rec_id(recs[0], opt_mode='append')
        # Retrieve current localtime
        now = time.localtime()
        # We update the modification date
        bibupload.update_bibrec_modif_date(convert_datestruct_to_datetext(now), rec_id)
        # We retrieve the modification date from the database
        query = """SELECT DATE_FORMAT(modification_date,'%%Y-%%m-%%d %%H:%%i:%%s') FROM bibrec where id = %s"""
        res = run_sql(query % rec_id)
        # We compare the two results
        self.assertEqual(res[0][0], convert_datestruct_to_datetext(now))
        # clean up after ourselves:
        bibupload.wipe_out_record_from_all_tables(self.test_recid)
        return

    def test_append_complete_xml_marc(self):
        """bibupload - append mode, appending complete MARCXML file"""
        # Now we append a datafield
        # We create create the record out of the xml marc
        recs = bibupload.xml_marc_to_records(self.test_to_append)
        # We call the main function with the record as a parameter
        err, recid = bibupload.bibupload(recs[0], opt_mode='append')
        # We retrieve the inserted xm
        after_append_xm = print_record(recid, 'xm')
        after_append_hm = print_record(recid, 'hm')
        # Compare if the two MARCXML are the same
        self.failUnless(compare_xmbuffers(after_append_xm, self.test_expected_xm))
        self.failUnless(compare_hmbuffers(after_append_hm, self.test_expected_hm))
        # clean up after ourselves:
        bibupload.wipe_out_record_from_all_tables(self.test_recid)
        return

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
        <controlfield tag="001">123456789</controlfield>
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
        001__ 123456789
        003__ SzGeCERN
        100__ $$aTest, Jane$$uTest Institute
        10047 $$aTest, John$$uTest University
        10048 $$aCool
        10047 $$aTest, Jim$$uTest Laboratory
        """
        self.testrec1_xm_to_correct = """
        <record>
        <controlfield tag="001">123456789</controlfield>
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
        <controlfield tag="001">123456789</controlfield>
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
        001__ 123456789
        003__ SzGeCERN
        100__ $$aTest, Jane$$uTest Institute
        10048 $$aCool
        10047 $$aTest, Joseph$$uTest Academy
        10047 $$aTest2, Joseph$$uTest2 Academy
        """
        # insert test record:
        task_set_option('verbose', 0)
        test_record_xm = self.testrec1_xm.replace('<controlfield tag="001">123456789</controlfield>',
                                                  '')
        recs = bibupload.xml_marc_to_records(test_record_xm)
        err, recid = bibupload.bibupload(recs[0], opt_mode='insert')
        # replace test buffers with real recID:
        self.testrec1_xm = self.testrec1_xm.replace('123456789', str(recid))
        self.testrec1_hm = self.testrec1_hm.replace('123456789', str(recid))
        self.testrec1_xm_to_correct = self.testrec1_xm_to_correct.replace('123456789', str(recid))
        self.testrec1_corrected_xm = self.testrec1_corrected_xm.replace('123456789', str(recid))
        self.testrec1_corrected_hm = self.testrec1_corrected_hm.replace('123456789', str(recid))
        # test of the inserted record:
        inserted_xm = print_record(recid, 'xm')
        inserted_hm = print_record(recid, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm, self.testrec1_xm))
        self.failUnless(compare_hmbuffers(inserted_hm, self.testrec1_hm))

    def test_record_correction(self):
        """bibupload - correct mode, similar MARCXML tags/indicators"""
        # correct some tags:
        recs = bibupload.xml_marc_to_records(self.testrec1_xm_to_correct)
        err, recid = bibupload.bibupload(recs[0], opt_mode='correct')
        corrected_xm = print_record(recid, 'xm')
        corrected_hm = print_record(recid, 'hm')
        # did it work?
        self.failUnless(compare_xmbuffers(corrected_xm, self.testrec1_corrected_xm))
        self.failUnless(compare_hmbuffers(corrected_hm, self.testrec1_corrected_hm))
        # clean up after ourselves:
        bibupload.wipe_out_record_from_all_tables(recid)
        return

class BibUploadReplaceModeTest(unittest.TestCase):
    """Testing replace mode."""

    def setUp(self):
        """Initialize the MARCXML test record."""
        self.testrec1_xm = """
        <record>
        <controlfield tag="001">123456789</controlfield>
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
        001__ 123456789
        003__ SzGeCERN
        100__ $$aTest, Jane$$uTest Institute
        10047 $$aTest, John$$uTest University
        10048 $$aCool
        10047 $$aTest, Jim$$uTest Laboratory
        """
        self.testrec1_xm_to_replace = """
        <record>
        <controlfield tag="001">123456789</controlfield>
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
        self.testrec1_replaced_xm = """
        <record>
        <controlfield tag="001">123456789</controlfield>
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
        self.testrec1_replaced_hm = """
        001__ 123456789
        10047 $$aTest, Joseph$$uTest Academy
        10047 $$aTest2, Joseph$$uTest2 Academy
        """
        # insert test record:
        task_set_option('verbose', 0)
        test_record_xm = self.testrec1_xm.replace('<controlfield tag="001">123456789</controlfield>',
                                                  '')
        recs = bibupload.xml_marc_to_records(test_record_xm)
        err, recid = bibupload.bibupload(recs[0], opt_mode='insert')
        # replace test buffers with real recID:
        self.testrec1_xm = self.testrec1_xm.replace('123456789', str(recid))
        self.testrec1_hm = self.testrec1_hm.replace('123456789', str(recid))
        self.testrec1_xm_to_replace = self.testrec1_xm_to_replace.replace('123456789', str(recid))
        self.testrec1_replaced_xm = self.testrec1_replaced_xm.replace('123456789', str(recid))
        self.testrec1_replaced_hm = self.testrec1_replaced_hm.replace('123456789', str(recid))
        # test of the inserted record:
        inserted_xm = print_record(recid, 'xm')
        inserted_hm = print_record(recid, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm, self.testrec1_xm))
        self.failUnless(compare_hmbuffers(inserted_hm, self.testrec1_hm))

    def test_record_replace(self):
        """bibupload - replace mode, similar MARCXML tags/indicators"""
        # replace some tags:
        recs = bibupload.xml_marc_to_records(self.testrec1_xm_to_replace)
        err, recid = bibupload.bibupload(recs[0], opt_mode='replace')
        replaced_xm = print_record(recid, 'xm')
        replaced_hm = print_record(recid, 'hm')
        # did it work?
        self.failUnless(compare_xmbuffers(replaced_xm, self.testrec1_replaced_xm))
        self.failUnless(compare_hmbuffers(replaced_hm, self.testrec1_replaced_hm))
        # clean up after ourselves:
        bibupload.wipe_out_record_from_all_tables(recid)
        return

class BibUploadReferencesModeTest(unittest.TestCase):
    """Testing references mode."""

    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize the MARCXML variable"""
        self.test_insert = """<record>
        <controlfield tag="001">123456789</controlfield>
        <datafield tag ="100" ind1=" " ind2=" ">
        <subfield code="a">Tester, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""
        self.test_reference = """<record>
        <controlfield tag="001">123456789</controlfield>
        <datafield tag =\"""" + bibupload.CFG_BIBUPLOAD_REFERENCE_TAG + """\" ind1="C" ind2="5">
        <subfield code="m">M. Lüscher and P. Weisz, String excitation energies in SU(N) gauge theories beyond the free-string approximation,</subfield>
        <subfield code="s">J. High Energy Phys. 07 (2004) 014</subfield>
        </datafield>
        </record>"""
        self.test_reference_expected_xm = """<record>
        <controlfield tag="001">123456789</controlfield>
        <datafield tag ="100" ind1=" " ind2=" ">
        <subfield code="a">Tester, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        <datafield tag =\"""" + bibupload.CFG_BIBUPLOAD_REFERENCE_TAG + """\" ind1="C" ind2="5">
        <subfield code="m">M. Lüscher and P. Weisz, String excitation energies in SU(N) gauge theories beyond the free-string approximation,</subfield>
        <subfield code="s">J. High Energy Phys. 07 (2004) 014</subfield>
        </datafield>
        </record>"""
        self.test_insert_hm = """
        001__ 123456789
        100__ $$aTester, T$$uCERN
        """
        self.test_reference_expected_hm = """
        001__ 123456789
        100__ $$aTester, T$$uCERN
        %(reference_tag)sC5 $$mM. Lüscher and P. Weisz, String excitation energies in SU(N) gauge theories beyond the free-string approximation,$$sJ. High Energy Phys. 07 (2004) 014
        """ % {'reference_tag': bibupload.CFG_BIBUPLOAD_REFERENCE_TAG}
        # insert test record:
        task_set_option('verbose', 0)
        test_insert = self.test_insert.replace('<controlfield tag="001">123456789</controlfield>',
                                               '')
        recs = bibupload.xml_marc_to_records(test_insert)
        err, recid = bibupload.bibupload(recs[0], opt_mode='insert')
        # replace test buffers with real recID:
        self.test_insert = self.test_insert.replace('123456789', str(recid))
        self.test_insert_hm = self.test_insert_hm.replace('123456789', str(recid))
        self.test_reference = self.test_reference.replace('123456789', str(recid))
        self.test_reference_expected_xm = self.test_reference_expected_xm.replace('123456789', str(recid))
        self.test_reference_expected_hm = self.test_reference_expected_hm.replace('123456789', str(recid))
        # test of the inserted record:
        inserted_xm = print_record(recid, 'xm')
        inserted_hm = print_record(recid, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm, self.test_insert))
        self.failUnless(compare_hmbuffers(inserted_hm, self.test_insert_hm))
        self.test_recid = recid

    def test_reference_complete_xml_marc(self):
        """bibupload - reference mode, inserting references MARCXML file"""
        # We create create the record out of the xml marc
        recs = bibupload.xml_marc_to_records(self.test_reference)
        # We call the main function with the record as a parameter
        err, recid = bibupload.bibupload(recs[0], opt_mode='reference')
        # We retrieve the inserted xml
        reference_xm = print_record(recid, 'xm')
        reference_hm = print_record(recid, 'hm')
        # Compare if the two MARCXML are the same
        self.failUnless(compare_xmbuffers(reference_xm, self.test_reference_expected_xm))
        self.failUnless(compare_hmbuffers(reference_hm, self.test_reference_expected_hm))
        # clean up after ourselves:
        bibupload.wipe_out_record_from_all_tables(self.test_recid)
        return

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
         <controlfield tag="001">123456789</controlfield>
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
        001__ 123456789
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
        recs = bibupload.xml_marc_to_records(self.recid3_xm_before_all_the_tests)
        err, recid = bibupload.bibupload(recs[0], opt_mode='replace')
        inserted_xm = print_record(recid, 'xm')
        inserted_hm = print_record(recid, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm, self.recid3_xm_before_all_the_tests))
        self.failUnless(compare_hmbuffers(inserted_hm, self.recid3_hm_before_all_the_tests))

    def test_inserting_new_record_containing_fmt_tag(self):
        """bibupload - FMT tag, inserting new record containing FMT tag"""
        recs = bibupload.xml_marc_to_records(self.new_xm_with_fmt)
        (dummy, new_recid) = bibupload.bibupload(recs[0], opt_mode='insert')
        xm_after = print_record(new_recid, 'xm')
        hm_after = print_record(new_recid, 'hm')
        hb_after = print_record(new_recid, 'hb')
        self.failUnless(compare_xmbuffers(xm_after,
                                          self.expected_xm_after_inserting_new_xm_with_fmt.replace('123456789', str(new_recid))))
        self.failUnless(compare_hmbuffers(hm_after,
                                          self.expected_hm_after_inserting_new_xm_with_fmt.replace('123456789', str(new_recid))))
        self.failUnless(hb_after.startswith("Test. Okay."))

    def test_updating_existing_record_formats_in_format_mode(self):
        """bibupload - FMT tag, updating existing record via format mode"""
        xm_before = print_record(3, 'xm')
        hm_before = print_record(3, 'hm')
        # insert first format value:
        recs = bibupload.xml_marc_to_records(self.recid3_xm_with_fmt_only_first)
        bibupload.bibupload(recs[0], opt_mode='format')
        xm_after = print_record(3, 'xm')
        hm_after = print_record(3, 'hm')
        hb_after = print_record(3, 'hb')
        self.assertEqual(xm_after, xm_before)
        self.assertEqual(hm_after, hm_before)
        self.failUnless(hb_after.startswith("Test. Let us see if this gets inserted well."))
        # now insert another format value and recheck:
        recs = bibupload.xml_marc_to_records(self.recid3_xm_with_fmt_only_second)
        bibupload.bibupload(recs[0], opt_mode='format')
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
        xm_before = print_record(3, 'xm')
        hm_before = print_record(3, 'hm')
        # insert first format value:
        recs = bibupload.xml_marc_to_records(self.recid3_xm_with_fmt_only_first)
        bibupload.bibupload(recs[0], opt_mode='correct')
        xm_after = print_record(3, 'xm')
        hm_after = print_record(3, 'hm')
        hb_after = print_record(3, 'hb')
        self.assertEqual(xm_after, xm_before)
        self.assertEqual(hm_after, hm_before)
        self.failUnless(hb_after.startswith("Test. Let us see if this gets inserted well."))
        # now insert another format value and recheck:
        recs = bibupload.xml_marc_to_records(self.recid3_xm_with_fmt_only_second)
        bibupload.bibupload(recs[0], opt_mode='correct')
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
        # insert first format value:
        recs = bibupload.xml_marc_to_records(self.recid3_xm_with_fmt_only_first)
        bibupload.bibupload(recs[0], opt_mode='replace')
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
        bibupload.bibupload(recs[0], opt_mode='replace')
        xm_after = print_record(3, 'xm')
        hm_after = print_record(3, 'hm')
        hb_after = print_record(3, 'hb')
        hd_after = print_record(3, 'hd')
        self.failUnless(compare_xmbuffers(xm_after, """
                                           <record>
                                           <controlfield tag="001">3</controlfield>
                                           </record>"""))
        self.failUnless(compare_hmbuffers(hm_after, '000000003 001__ 3'))
        self.failUnless(hb_after.startswith("Test. Yet another test, to be run after the first one."))
        self.failUnless(hd_after.startswith("Test. Let's see what will be stored in the detailed format field."))
        # final insertion and recheck:
        recs = bibupload.xml_marc_to_records(self.recid3_xm_with_fmt)
        bibupload.bibupload(recs[0], opt_mode='replace')
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
                                           """))
        self.failUnless(compare_hmbuffers(hm_after, """
                                           001__ 3
                                           003__ SzGeCERN
                                           100__ $$aDoe, John$$uCERN
                                           245__ $$aOn the foos and bars
                                           """))
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
         <controlfield tag="001">123456789</controlfield>
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
        001__ 123456789
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
        self.xm_testrec1_to_update = """
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
        self.xm_testrec1_updated = """
        <record>
         <controlfield tag="001">123456789</controlfield>
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
        001__ 123456789
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
         <controlfield tag="001">987654321</controlfield>
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
        001__ 987654321
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
        if self.verbose:
            print "test_insert_the_same_sysno_record() started"
        # insert record 1 first time:
        testrec_to_insert_first = self.xm_testrec1.replace('<controlfield tag="001">123456789</controlfield>',
                                                           '')
        recs = bibupload.xml_marc_to_records(testrec_to_insert_first)
        err1, recid1 = bibupload.bibupload(recs[0], opt_mode='insert')
        inserted_xm = print_record(recid1, 'xm')
        inserted_hm = print_record(recid1, 'hm')
        # use real recID when comparing whether it worked:
        self.xm_testrec1 =  self.xm_testrec1.replace('123456789', str(recid1))
        self.hm_testrec1 =  self.hm_testrec1.replace('123456789', str(recid1))
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec1))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec1))
        # insert record 2 first time:
        testrec_to_insert_first = self.xm_testrec2.replace('<controlfield tag="001">987654321</controlfield>',
                                                           '')
        recs = bibupload.xml_marc_to_records(testrec_to_insert_first)
        err2, recid2 = bibupload.bibupload(recs[0], opt_mode='insert')
        inserted_xm = print_record(recid2, 'xm')
        inserted_hm = print_record(recid2, 'hm')
        # use real recID when comparing whether it worked:
        self.xm_testrec2 =  self.xm_testrec2.replace('987654321', str(recid2))
        self.hm_testrec2 =  self.hm_testrec2.replace('987654321', str(recid2))
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec2))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec2))
        # try to insert updated record 1, it should fail:
        recs = bibupload.xml_marc_to_records(self.xm_testrec1_to_update)
        err1_updated, recid1_updated = bibupload.bibupload(recs[0], opt_mode='insert')
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
        task_set_option('verbose', self.verbose)
        if self.verbose:
            print "test_insert_or_replace_the_same_sysno_record() started"
        # insert/replace record 1 first time:
        testrec_to_insert_first = self.xm_testrec1.replace('<controlfield tag="001">123456789</controlfield>',
                                                           '')
        recs = bibupload.xml_marc_to_records(testrec_to_insert_first)
        err1, recid1 = bibupload.bibupload(recs[0], opt_mode='replace_or_insert')
        inserted_xm = print_record(recid1, 'xm')
        inserted_hm = print_record(recid1, 'hm')
        # use real recID in test buffers when comparing whether it worked:
        self.xm_testrec1 =  self.xm_testrec1.replace('123456789', str(recid1))
        self.hm_testrec1 =  self.hm_testrec1.replace('123456789', str(recid1))
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec1))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                          self.hm_testrec1))
        # try to insert/replace updated record 1, it should be okay:
        task_set_option('verbose', self.verbose)
        recs = bibupload.xml_marc_to_records(self.xm_testrec1_to_update)
        err1_updated, recid1_updated = bibupload.bibupload(recs[0],
            opt_mode='replace_or_insert')
        inserted_xm = print_record(recid1_updated, 'xm')
        inserted_hm = print_record(recid1_updated, 'hm')
        self.assertEqual(recid1, recid1_updated)
        # use real recID in test buffers when comparing whether it worked:
        self.xm_testrec1_updated =  self.xm_testrec1_updated.replace('123456789', str(recid1))
        self.hm_testrec1_updated =  self.hm_testrec1_updated.replace('123456789', str(recid1))
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
        task_set_option('verbose', self.verbose)
        if self.verbose:
            print "test_replace_nonexisting_sysno_record() started"
        # insert record 1 first time:
        testrec_to_insert_first = self.xm_testrec1.replace('<controlfield tag="001">123456789</controlfield>',
                                                           '')
        recs = bibupload.xml_marc_to_records(testrec_to_insert_first)
        err1, recid1 = bibupload.bibupload(recs[0], opt_mode='replace_or_insert')
        inserted_xm = print_record(recid1, 'xm')
        inserted_hm = print_record(recid1, 'hm')
        # use real recID in test buffers when comparing whether it worked:
        self.xm_testrec1 =  self.xm_testrec1.replace('123456789', str(recid1))
        self.hm_testrec1 =  self.hm_testrec1.replace('123456789', str(recid1))
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec1))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec1))
        # try to replace record 2 it should fail:
        testrec_to_insert_first = self.xm_testrec2.replace('<controlfield tag="001">987654321</controlfield>',
                                                           '')
        recs = bibupload.xml_marc_to_records(testrec_to_insert_first)
        err2, recid2 = bibupload.bibupload(recs[0], opt_mode='replace')
        self.assertEqual(-1, recid2)
        # delete test records
        bibupload.wipe_out_record_from_all_tables(recid1)
        bibupload.wipe_out_record_from_all_tables(recid2)
        if self.verbose:
            print "test_replace_nonexisting_sysno_record() finished"

class BibUploadRecordsWithEXTOAIIDTest(unittest.TestCase):
    """Testing uploading of records that have external EXTOAIID present."""

    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize the MARCXML test records."""
        self.verbose = 0
        # Note that EXTOAIID fields are repeated but with different
        # subfields, this is to test whether bibupload would not
        # mistakenly pick up wrong values.
        self.xm_testrec1 = """
        <record>
         <controlfield tag="001">123456789</controlfield>
         <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="%(extoaiidtag)s" ind1="%(extoaiidind1)s" ind2="%(extoaiidind2)s">
          <subfield code="%(extoaiidsubfieldcode)s">extoaiid1</subfield>
         </datafield>
         <datafield tag="%(extoaiidtag)s" ind1="%(extoaiidind1)s" ind2="%(extoaiidind2)s">
          <subfield code="0">extoaiid2</subfield>
         </datafield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Bar, Baz</subfield>
          <subfield code="u">Foo</subfield>
         </datafield>
         <datafield tag="245" ind1=" " ind2=" ">
          <subfield code="a">On the quux and huux 1</subfield>
         </datafield>
        </record>
        """ % {'extoaiidtag': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[0:3],
               'extoaiidind1': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3:4] != "_" and \
                            CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3:4] or " ",
               'extoaiidind2': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4:5] != "_" and \
                            CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4:5] or " ",
               'extoaiidsubfieldcode': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[5:6],
               }
        self.hm_testrec1 = """
        001__ 123456789
        003__ SzGeCERN
        %(extoaiidtag)s%(extoaiidind1)s%(extoaiidind2)s $$%(extoaiidsubfieldcode)sextoaiid1
        %(extoaiidtag)s%(extoaiidind1)s%(extoaiidind2)s $$0extoaiid2
        100__ $$aBar, Baz$$uFoo
        245__ $$aOn the quux and huux 1
        """ % {'extoaiidtag': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[0:3],
               'extoaiidind1': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3:4],
               'extoaiidind2': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4:5],
               'extoaiidsubfieldcode': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[5:6],
               }
        self.xm_testrec1_to_update = """
        <record>
         <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="%(extoaiidtag)s" ind1="%(extoaiidind1)s" ind2="%(extoaiidind2)s">
          <subfield code="%(extoaiidsubfieldcode)s">extoaiid1</subfield>
         </datafield>
         <datafield tag="%(extoaiidtag)s" ind1="%(extoaiidind1)s" ind2="%(extoaiidind2)s">
          <subfield code="0">extoaiid2</subfield>
         </datafield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Bar, Baz</subfield>
          <subfield code="u">Foo</subfield>
         </datafield>
         <datafield tag="245" ind1=" " ind2=" ">
          <subfield code="a">On the quux and huux 1 Updated</subfield>
         </datafield>
        </record>
        """ % {'extoaiidtag': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[0:3],
               'extoaiidind1': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3:4] != "_" and \
                            CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3:4] or " ",
               'extoaiidind2': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4:5] != "_" and \
                            CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4:5] or " ",
               'extoaiidsubfieldcode': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[5:6],
               }
        self.xm_testrec1_updated = """
        <record>
         <controlfield tag="001">123456789</controlfield>
         <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="%(extoaiidtag)s" ind1="%(extoaiidind1)s" ind2="%(extoaiidind2)s">
          <subfield code="%(extoaiidsubfieldcode)s">extoaiid1</subfield>
         </datafield>
         <datafield tag="%(extoaiidtag)s" ind1="%(extoaiidind1)s" ind2="%(extoaiidind2)s">
          <subfield code="0">extoaiid2</subfield>
         </datafield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Bar, Baz</subfield>
          <subfield code="u">Foo</subfield>
         </datafield>
         <datafield tag="245" ind1=" " ind2=" ">
          <subfield code="a">On the quux and huux 1 Updated</subfield>
         </datafield>
        </record>
        """ % {'extoaiidtag': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[0:3],
               'extoaiidind1': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3:4] != "_" and \
                            CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3:4] or " ",
               'extoaiidind2': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4:5] != "_" and \
                            CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4:5] or " ",
               'extoaiidsubfieldcode': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[5:6],
               }
        self.hm_testrec1_updated = """
        001__ 123456789
        003__ SzGeCERN
        %(extoaiidtag)s%(extoaiidind1)s%(extoaiidind2)s $$%(extoaiidsubfieldcode)sextoaiid1
        %(extoaiidtag)s%(extoaiidind1)s%(extoaiidind2)s $$0extoaiid2
        100__ $$aBar, Baz$$uFoo
        245__ $$aOn the quux and huux 1 Updated
        """ % {'extoaiidtag': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[0:3],
               'extoaiidind1': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3:4],
               'extoaiidind2': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4:5],
               'extoaiidsubfieldcode': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[5:6],
               }
        self.xm_testrec2 = """
        <record>
         <controlfield tag="001">987654321</controlfield>
         <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="%(extoaiidtag)s" ind1="%(extoaiidind1)s" ind2="%(extoaiidind2)s">
          <subfield code="%(extoaiidsubfieldcode)s">extoaiid2</subfield>
         </datafield>
         <datafield tag="%(extoaiidtag)s" ind1="%(extoaiidind1)s" ind2="%(extoaiidind2)s">
          <subfield code="0">extoaiid1</subfield>
         </datafield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Bar, Baz</subfield>
          <subfield code="u">Foo</subfield>
         </datafield>
         <datafield tag="245" ind1=" " ind2=" ">
          <subfield code="a">On the quux and huux 2</subfield>
         </datafield>
        </record>
        """ % {'extoaiidtag': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[0:3],
               'extoaiidind1': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3:4] != "_" and \
                            CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3:4] or " ",
               'extoaiidind2': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4:5] != "_" and \
                            CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4:5] or " ",
               'extoaiidsubfieldcode': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[5:6],
               }
        self.hm_testrec2 = """
        001__ 987654321
        003__ SzGeCERN
        %(extoaiidtag)s%(extoaiidind1)s%(extoaiidind2)s $$%(extoaiidsubfieldcode)sextoaiid2
        %(extoaiidtag)s%(extoaiidind1)s%(extoaiidind2)s $$0extoaiid1
        100__ $$aBar, Baz$$uFoo
        245__ $$aOn the quux and huux 2
        """ % {'extoaiidtag': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[0:3],
               'extoaiidind1': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3:4],
               'extoaiidind2': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4:5],
               'extoaiidsubfieldcode': CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[5:6],
               }

    def test_insert_the_same_extoaiid_record(self):
        """bibupload - EXTOAIID tag, refuse to insert the same EXTOAIID record"""
        # initialize bibupload mode:
        task_set_option('verbose', self.verbose)
        if self.verbose:
            print "test_insert_the_same_extoaiid_record() started"
        # insert record 1 first time:
        testrec_to_insert_first = self.xm_testrec1.replace('<controlfield tag="001">123456789</controlfield>',
                                                           '')
        recs = bibupload.xml_marc_to_records(testrec_to_insert_first)
        err1, recid1 = bibupload.bibupload(recs[0], opt_mode='insert')
        inserted_xm = print_record(recid1, 'xm')
        inserted_hm = print_record(recid1, 'hm')
        # use real recID when comparing whether it worked:
        self.xm_testrec1 =  self.xm_testrec1.replace('123456789', str(recid1))
        self.hm_testrec1 =  self.hm_testrec1.replace('123456789', str(recid1))
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec1))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec1))
        # insert record 2 first time:
        testrec_to_insert_first = self.xm_testrec2.replace('<controlfield tag="001">987654321</controlfield>',
                                                           '')
        recs = bibupload.xml_marc_to_records(testrec_to_insert_first)
        err2, recid2 = bibupload.bibupload(recs[0], opt_mode='insert')
        inserted_xm = print_record(recid2, 'xm')
        inserted_hm = print_record(recid2, 'hm')
        # use real recID when comparing whether it worked:
        self.xm_testrec2 =  self.xm_testrec2.replace('987654321', str(recid2))
        self.hm_testrec2 =  self.hm_testrec2.replace('987654321', str(recid2))
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec2))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec2))
        # try to insert updated record 1, it should fail:
        recs = bibupload.xml_marc_to_records(self.xm_testrec1_to_update)
        err1_updated, recid1_updated = bibupload.bibupload(recs[0], opt_mode='insert')
        self.assertEqual(-1, recid1_updated)
        # delete test records
        bibupload.wipe_out_record_from_all_tables(recid1)
        bibupload.wipe_out_record_from_all_tables(recid2)
        bibupload.wipe_out_record_from_all_tables(recid1_updated)
        if self.verbose:
            print "test_insert_the_same_extoaiid_record() finished"

    def test_insert_or_replace_the_same_extoaiid_record(self):
        """bibupload - EXTOAIID tag, allow to insert or replace the same EXTOAIID record"""
        # initialize bibupload mode:
        task_set_option('verbose', self.verbose)
        if self.verbose:
            print "test_insert_or_replace_the_same_extoaiid_record() started"
        # insert/replace record 1 first time:
        testrec_to_insert_first = self.xm_testrec1.replace('<controlfield tag="001">123456789</controlfield>',
                                                           '')
        recs = bibupload.xml_marc_to_records(testrec_to_insert_first)
        err1, recid1 = bibupload.bibupload(recs[0], opt_mode='replace_or_insert')
        inserted_xm = print_record(recid1, 'xm')
        inserted_hm = print_record(recid1, 'hm')
        # use real recID in test buffers when comparing whether it worked:
        self.xm_testrec1 =  self.xm_testrec1.replace('123456789', str(recid1))
        self.hm_testrec1 =  self.hm_testrec1.replace('123456789', str(recid1))
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec1))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                          self.hm_testrec1))
        # try to insert/replace updated record 1, it should be okay:
        recs = bibupload.xml_marc_to_records(self.xm_testrec1_to_update)
        err1_updated, recid1_updated = bibupload.bibupload(recs[0], opt_mode='replace_or_insert')
        inserted_xm = print_record(recid1_updated, 'xm')
        inserted_hm = print_record(recid1_updated, 'hm')
        self.assertEqual(recid1, recid1_updated)
        # use real recID in test buffers when comparing whether it worked:
        self.xm_testrec1_updated =  self.xm_testrec1_updated.replace('123456789', str(recid1))
        self.hm_testrec1_updated =  self.hm_testrec1_updated.replace('123456789', str(recid1))
        self.failUnless(compare_xmbuffers(inserted_xm,
                                          self.xm_testrec1_updated))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                          self.hm_testrec1_updated))
        # delete test records
        bibupload.wipe_out_record_from_all_tables(recid1)
        bibupload.wipe_out_record_from_all_tables(recid1_updated)
        if self.verbose:
            print "test_insert_or_replace_the_same_extoaiid_record() finished"

    def test_replace_nonexisting_extoaiid_record(self):
        """bibupload - EXTOAIID tag, refuse to replace non-existing EXTOAIID record"""
        # initialize bibupload mode:
        task_set_option('verbose', self.verbose)
        if self.verbose:
            print "test_replace_nonexisting_extoaiid_record() started"
        # insert record 1 first time:
        testrec_to_insert_first = self.xm_testrec1.replace('<controlfield tag="001">123456789</controlfield>',
                                                           '')
        recs = bibupload.xml_marc_to_records(testrec_to_insert_first)
        err1, recid1 = bibupload.bibupload(recs[0], opt_mode='replace_or_insert')
        inserted_xm = print_record(recid1, 'xm')
        inserted_hm = print_record(recid1, 'hm')
        # use real recID in test buffers when comparing whether it worked:
        self.xm_testrec1 =  self.xm_testrec1.replace('123456789', str(recid1))
        self.hm_testrec1 =  self.hm_testrec1.replace('123456789', str(recid1))
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec1))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec1))
        # try to replace record 2 it should fail:
        testrec_to_insert_first = self.xm_testrec2.replace('<controlfield tag="001">987654321</controlfield>',
                                                           '')
        recs = bibupload.xml_marc_to_records(testrec_to_insert_first)
        err2, recid2 = bibupload.bibupload(recs[0], opt_mode='replace')
        self.assertEqual(-1, recid2)
        # delete test records
        bibupload.wipe_out_record_from_all_tables(recid1)
        bibupload.wipe_out_record_from_all_tables(recid2)
        if self.verbose:
            print "test_replace_nonexisting_extoaiid_record() finished"

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
         <controlfield tag="001">123456789</controlfield>
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
        001__ 123456789
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
        self.xm_testrec1_to_update = """
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
        self.xm_testrec1_updated = """
        <record>
         <controlfield tag="001">123456789</controlfield>
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
        001__ 123456789
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
         <controlfield tag="001">987654321</controlfield>
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
        001__ 987654321
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
        """bibupload - OAIID tag, refuse to insert the same OAI record"""
        task_set_option('verbose', self.verbose)
        # insert record 1 first time:
        testrec_to_insert_first = self.xm_testrec1.replace('<controlfield tag="001">123456789</controlfield>',
                                                           '')
        recs = bibupload.xml_marc_to_records(testrec_to_insert_first)
        err1, recid1 = bibupload.bibupload(recs[0], opt_mode='insert')
        inserted_xm = print_record(recid1, 'xm')
        inserted_hm = print_record(recid1, 'hm')
        # use real recID when comparing whether it worked:
        self.xm_testrec1 =  self.xm_testrec1.replace('123456789', str(recid1))
        self.hm_testrec1 =  self.hm_testrec1.replace('123456789', str(recid1))
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec1))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec1))
        # insert record 2 first time:
        testrec_to_insert_first = self.xm_testrec2.replace('<controlfield tag="001">987654321</controlfield>',
                                                           '')
        recs = bibupload.xml_marc_to_records(testrec_to_insert_first)
        err2, recid2 = bibupload.bibupload(recs[0], opt_mode='insert')
        inserted_xm = print_record(recid2, 'xm')
        inserted_hm = print_record(recid2, 'hm')
        # use real recID when comparing whether it worked:
        self.xm_testrec2 =  self.xm_testrec2.replace('987654321', str(recid2))
        self.hm_testrec2 =  self.hm_testrec2.replace('987654321', str(recid2))
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec2))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec2))
        # try to insert updated record 1, it should fail:
        recs = bibupload.xml_marc_to_records(self.xm_testrec1_to_update)
        err1_updated, recid1_updated = bibupload.bibupload(recs[0], opt_mode='insert')
        self.assertEqual(-1, recid1_updated)
        # delete test records
        bibupload.wipe_out_record_from_all_tables(recid1)
        bibupload.wipe_out_record_from_all_tables(recid2)
        bibupload.wipe_out_record_from_all_tables(recid1_updated)

    def test_insert_or_replace_the_same_oai_record(self):
        """bibupload - OAIID tag, allow to insert or replace the same OAI record"""
        # initialize bibupload mode:
        task_set_option('verbose', self.verbose)
        # insert/replace record 1 first time:
        testrec_to_insert_first = self.xm_testrec1.replace('<controlfield tag="001">123456789</controlfield>',
                                                           '')
        recs = bibupload.xml_marc_to_records(testrec_to_insert_first)
        err1, recid1 = bibupload.bibupload(recs[0], opt_mode='replace_or_insert')
        inserted_xm = print_record(recid1, 'xm')
        inserted_hm = print_record(recid1, 'hm')
        # use real recID in test buffers when comparing whether it worked:
        self.xm_testrec1 =  self.xm_testrec1.replace('123456789', str(recid1))
        self.hm_testrec1 =  self.hm_testrec1.replace('123456789', str(recid1))
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec1))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec1))
        # try to insert/replace updated record 1, it should be okay:
        recs = bibupload.xml_marc_to_records(self.xm_testrec1_to_update)
        err1_updated, recid1_updated = bibupload.bibupload(recs[0], opt_mode='replace_or_insert')
        inserted_xm = print_record(recid1_updated, 'xm')
        inserted_hm = print_record(recid1_updated, 'hm')
        self.assertEqual(recid1, recid1_updated)
        # use real recID in test buffers when comparing whether it worked:
        self.xm_testrec1_updated =  self.xm_testrec1_updated.replace('123456789', str(recid1))
        self.hm_testrec1_updated =  self.hm_testrec1_updated.replace('123456789', str(recid1))
        self.failUnless(compare_xmbuffers(inserted_xm,
                                          self.xm_testrec1_updated))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                          self.hm_testrec1_updated))
        # delete test records
        bibupload.wipe_out_record_from_all_tables(recid1)
        bibupload.wipe_out_record_from_all_tables(recid1_updated)

    def test_replace_nonexisting_oai_record(self):
        """bibupload - OAIID tag, refuse to replace non-existing OAI record"""
        task_set_option('verbose', self.verbose)
        # insert record 1 first time:
        testrec_to_insert_first = self.xm_testrec1.replace('<controlfield tag="001">123456789</controlfield>',
                                                           '')
        recs = bibupload.xml_marc_to_records(testrec_to_insert_first)
        err1, recid1 = bibupload.bibupload(recs[0], opt_mode='replace_or_insert')
        inserted_xm = print_record(recid1, 'xm')
        inserted_hm = print_record(recid1, 'hm')
        # use real recID in test buffers when comparing whether it worked:
        self.xm_testrec1 =  self.xm_testrec1.replace('123456789', str(recid1))
        self.hm_testrec1 =  self.hm_testrec1.replace('123456789', str(recid1))
        self.failUnless(compare_xmbuffers(inserted_xm,
                                           self.xm_testrec1))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                           self.hm_testrec1))
        # try to replace record 2 it should fail:
        testrec_to_insert_first = self.xm_testrec2.replace('<controlfield tag="001">987654321</controlfield>',
                                                           '')
        recs = bibupload.xml_marc_to_records(testrec_to_insert_first)
        err2, recid2 = bibupload.bibupload(recs[0], opt_mode='replace')
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
        task_set_option('verbose', 0)
        recs = bibupload.xml_marc_to_records(self.testrec1_xm)
        err, recid = bibupload.bibupload(recs[0], opt_mode='insert')
        inserted_xm = print_record(recid, 'xm')
        inserted_hm = print_record(recid, 'hm')
        self.failUnless(compare_xmbuffers(remove_tag_001_from_xmbuffer(inserted_xm),
                                          self.testrec1_xm))
        self.failUnless(compare_hmbuffers(remove_tag_001_from_hmbuffer(inserted_hm),
                                          self.testrec1_hm))
        bibupload.wipe_out_record_from_all_tables(recid)

    def test_record_with_no_spaces_in_indicators(self):
        """bibupload - inserting MARCXML with no spaces in indicators"""
        task_set_option('verbose', 0)
        recs = bibupload.xml_marc_to_records(self.testrec2_xm)
        err, recid = bibupload.bibupload(recs[0], opt_mode='insert')
        inserted_xm = print_record(recid, 'xm')
        inserted_hm = print_record(recid, 'hm')
        self.failUnless(compare_xmbuffers(remove_tag_001_from_xmbuffer(inserted_xm),
                                          self.testrec2_xm))
        self.failUnless(compare_hmbuffers(remove_tag_001_from_hmbuffer(inserted_hm),
                                          self.testrec2_hm))
        bibupload.wipe_out_record_from_all_tables(recid)

class BibUploadUpperLowerCaseTest(unittest.TestCase):
    """
    Testing treatment of similar records with only upper and lower
    case value differences in the bibxxx table.
    """

    def setUp(self):
        """Initialize the MARCXML test records."""
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
          <subfield code="a">TeSt, JoHn</subfield>
          <subfield code="u">Test UniVeRsity</subfield>
         </datafield>
        </record>
        """
        self.testrec2_hm = """
        003__ SzGeCERN
        100__ $$aTeSt, JoHn$$uTest UniVeRsity
        """

    def test_record_with_upper_lower_case_letters(self):
        """bibupload - inserting similar MARCXML records with upper/lower case"""
        task_set_option('verbose', 0)
        # insert test record #1:
        recs = bibupload.xml_marc_to_records(self.testrec1_xm)
        err1, recid1 = bibupload.bibupload(recs[0], opt_mode='insert')
        recid1_inserted_xm = print_record(recid1, 'xm')
        recid1_inserted_hm = print_record(recid1, 'hm')
        # insert test record #2:
        recs = bibupload.xml_marc_to_records(self.testrec2_xm)
        err1, recid2 = bibupload.bibupload(recs[0], opt_mode='insert')
        recid2_inserted_xm = print_record(recid2, 'xm')
        recid2_inserted_hm = print_record(recid2, 'hm')
        # let us compare stuff now:
        self.failUnless(compare_xmbuffers(remove_tag_001_from_xmbuffer(recid1_inserted_xm),
                                          self.testrec1_xm))
        self.failUnless(compare_hmbuffers(remove_tag_001_from_hmbuffer(recid1_inserted_hm),
                                          self.testrec1_hm))
        self.failUnless(compare_xmbuffers(remove_tag_001_from_xmbuffer(recid2_inserted_xm),
                                          self.testrec2_xm))
        self.failUnless(compare_hmbuffers(remove_tag_001_from_hmbuffer(recid2_inserted_hm),
                                          self.testrec2_hm))
        # clean up after ourselves:
        bibupload.wipe_out_record_from_all_tables(recid1)
        bibupload.wipe_out_record_from_all_tables(recid2)

class BibUploadStrongTagsTest(unittest.TestCase):
    """Testing treatment of strong tags and the replace mode."""

    def setUp(self):
        """Initialize the MARCXML test record."""
        self.testrec1_xm = """
        <record>
        <controlfield tag="001">123456789</controlfield>
        <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Test, Jane</subfield>
          <subfield code="u">Test Institute</subfield>
         </datafield>
         <datafield tag="245" ind1=" " ind2=" ">
          <subfield code="a">Test title</subfield>
         </datafield>
         <datafield tag="%(strong_tag)s" ind1=" " ind2=" ">
          <subfield code="a">A value</subfield>
          <subfield code="b">Another value</subfield>
         </datafield>
        </record>
        """ % {'strong_tag': bibupload.CFG_BIBUPLOAD_STRONG_TAGS[0]}
        self.testrec1_hm = """
        001__ 123456789
        003__ SzGeCERN
        100__ $$aTest, Jane$$uTest Institute
        245__ $$aTest title
        %(strong_tag)s__ $$aA value$$bAnother value
        """ % {'strong_tag': bibupload.CFG_BIBUPLOAD_STRONG_TAGS[0]}
        self.testrec1_xm_to_replace = """
        <record>
        <controlfield tag="001">123456789</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Test, Joseph</subfield>
          <subfield code="u">Test Academy</subfield>
         </datafield>
        </record>
        """
        self.testrec1_replaced_xm = """
        <record>
        <controlfield tag="001">123456789</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Test, Joseph</subfield>
          <subfield code="u">Test Academy</subfield>
         </datafield>
         <datafield tag="%(strong_tag)s" ind1=" " ind2=" ">
          <subfield code="a">A value</subfield>
          <subfield code="b">Another value</subfield>
         </datafield>
        </record>
        """ % {'strong_tag': bibupload.CFG_BIBUPLOAD_STRONG_TAGS[0]}
        self.testrec1_replaced_hm = """
        001__ 123456789
        100__ $$aTest, Joseph$$uTest Academy
        %(strong_tag)s__ $$aA value$$bAnother value
        """ % {'strong_tag': bibupload.CFG_BIBUPLOAD_STRONG_TAGS[0]}
        # insert test record:
        task_set_option('verbose', 0)
        test_record_xm = self.testrec1_xm.replace('<controlfield tag="001">123456789</controlfield>',
                                                  '')
        recs = bibupload.xml_marc_to_records(test_record_xm)
        err, recid = bibupload.bibupload(recs[0], opt_mode='insert')
        # replace test buffers with real recID:
        self.testrec1_xm = self.testrec1_xm.replace('123456789', str(recid))
        self.testrec1_hm = self.testrec1_hm.replace('123456789', str(recid))
        self.testrec1_xm_to_replace = self.testrec1_xm_to_replace.replace('123456789', str(recid))
        self.testrec1_replaced_xm = self.testrec1_replaced_xm.replace('123456789', str(recid))
        self.testrec1_replaced_hm = self.testrec1_replaced_hm.replace('123456789', str(recid))
        # test of the inserted record:
        inserted_xm = print_record(recid, 'xm')
        inserted_hm = print_record(recid, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm, self.testrec1_xm))
        self.failUnless(compare_hmbuffers(inserted_hm, self.testrec1_hm))

    def test_strong_tags_persistence(self):
        """bibupload - strong tags, persistence in replace mode"""
        # replace all metadata tags; will the strong tags be kept?
        recs = bibupload.xml_marc_to_records(self.testrec1_xm_to_replace)
        err, recid = bibupload.bibupload(recs[0], opt_mode='replace')
        replaced_xm = print_record(recid, 'xm')
        replaced_hm = print_record(recid, 'hm')
        # did it work?
        self.failUnless(compare_xmbuffers(replaced_xm, self.testrec1_replaced_xm))
        self.failUnless(compare_hmbuffers(replaced_hm, self.testrec1_replaced_hm))
        # clean up after ourselves:
        bibupload.wipe_out_record_from_all_tables(recid)
        return

class BibUploadFFTModeTest(unittest.TestCase):
    """
    Testing treatment of fulltext file transfer import mode.
    """

    def test_simple_fft_insert_via_http(self):
        """bibupload - simple FFT insert via HTTP"""
        # define the test case:
        test_to_upload = """
        <record>
        <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Test, John</subfield>
          <subfield code="u">Test University</subfield>
         </datafield>
         <datafield tag="FFT" ind1=" " ind2=" ">
          <subfield code="a">http://cds.cern.ch/img/cds.gif</subfield>
         </datafield>
        </record>
        """
        testrec_expected_xm = """
        <record>
        <controlfield tag="001">123456789</controlfield>
        <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Test, John</subfield>
          <subfield code="u">Test University</subfield>
         </datafield>
         <datafield tag="856" ind1="4" ind2=" ">
          <subfield code="u">%(weburl)s/record/123456789/files/cds.gif</subfield>
         </datafield>
        </record>
        """ % { 'weburl': weburl}
        testrec_expected_hm = """
        001__ 123456789
        003__ SzGeCERN
        100__ $$aTest, John$$uTest University
        8564_ $$u%(weburl)s/record/123456789/files/cds.gif
        """ % { 'weburl': weburl}
        # insert test record:
        task_set_option('verbose', 0)
        recs = bibupload.xml_marc_to_records(test_to_upload)
        err, recid = bibupload.bibupload(recs[0], opt_mode='insert')
        # replace test buffers with real recid of inserted test record:
        testrec_expected_xm = testrec_expected_xm.replace('123456789',
                                                          str(recid))
        testrec_expected_hm = testrec_expected_hm.replace('123456789',
                                                          str(recid))
        # compare expected results:
        inserted_xm = print_record(recid, 'xm')
        inserted_hm = print_record(recid, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm,
                                          testrec_expected_xm))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                          testrec_expected_hm))
        # FIXME: compare also var/data/files/.../ content
        # clean up after ourselves:
        bibupload.wipe_out_record_from_all_tables(recid)

    def test_multiple_fft_insert_via_http(self):
        """bibupload - multiple FFT insert via HTTP and FILE"""
        # define the test case:
        test_to_upload = """
        <record>
        <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Test, John</subfield>
          <subfield code="u">Test University</subfield>
         </datafield>
         <datafield tag="FFT" ind1=" " ind2=" ">
          <subfield code="a">http://cds.cern.ch/img/cds.gif</subfield>
         </datafield>
         <datafield tag="FFT" ind1=" " ind2=" ">
          <subfield code="a">http://cdsweb.cern.ch/img/head.gif</subfield>
          <subfield code="a">http://doc.cern.ch/archive/electronic/hep-th/0101/0101001.pdf</subfield>
         </datafield>
         <datafield tag="FFT" ind1=" " ind2=" ">
          <subfield code="a">%(prefix)s/var/tmp/demobibdata.xml</subfield>
         </datafield>
         <datafield tag="FFT" ind1=" " ind2=" ">
          <subfield code="a">/etc/passwd</subfield>
         </datafield>
        </record>
        """ % { 'prefix': CFG_PREFIX }
        testrec_expected_xm = """
        <record>
        <controlfield tag="001">123456789</controlfield>
        <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Test, John</subfield>
          <subfield code="u">Test University</subfield>
         </datafield>
         <datafield tag="856" ind1="4" ind2=" ">
          <subfield code="u">%(weburl)s/record/123456789/files/cds.gif</subfield>
         </datafield>
         <datafield tag="856" ind1="4" ind2=" ">
          <subfield code="u">%(weburl)s/record/123456789/files/head.gif</subfield>
         </datafield>
         <datafield tag="856" ind1="4" ind2=" ">
          <subfield code="u">%(weburl)s/record/123456789/files/0101001.pdf</subfield>
         </datafield>
         <datafield tag="856" ind1="4" ind2=" ">
          <subfield code="u">%(weburl)s/record/123456789/files/demobibdata.xml</subfield>
         </datafield>
        </record>
        """ % { 'weburl': weburl}
        testrec_expected_hm = """
        001__ 123456789
        003__ SzGeCERN
        100__ $$aTest, John$$uTest University
        8564_ $$u%(weburl)s/record/123456789/files/cds.gif
        8564_ $$u%(weburl)s/record/123456789/files/head.gif
        8564_ $$u%(weburl)s/record/123456789/files/0101001.pdf
        8564_ $$u%(weburl)s/record/123456789/files/demobibdata.xml
        """ % { 'weburl': weburl}
        # insert test record:
        task_set_option('verbose', 0)
        recs = bibupload.xml_marc_to_records(test_to_upload)
        err, recid = bibupload.bibupload(recs[0], opt_mode='insert')
        # replace test buffers with real recid of inserted test record:
        testrec_expected_xm = testrec_expected_xm.replace('123456789',
                                                          str(recid))
        testrec_expected_hm = testrec_expected_hm.replace('123456789',
                                                          str(recid))
        # compare expected results:
        inserted_xm = print_record(recid, 'xm')
        inserted_hm = print_record(recid, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm,
                                          testrec_expected_xm))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                          testrec_expected_hm))
        # FIXME: compare also var/data/files/.../ content
        # clean up after ourselves:
        bibupload.wipe_out_record_from_all_tables(recid)

    def test_simple_fft_correct_via_http(self):
        """bibupload - simple FFT correct via HTTP"""
        # define the test case:
        test_to_upload = """
        <record>
        <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Test, John</subfield>
          <subfield code="u">Test University</subfield>
         </datafield>
         <datafield tag="FFT" ind1=" " ind2=" ">
          <subfield code="a">http://cds.cern.ch/img/cds.gif</subfield>
         </datafield>
        </record>
        """
        test_to_correct = """
        <record>
        <controlfield tag="001">123456789</controlfield>
         <datafield tag="FFT" ind1=" " ind2=" ">
          <subfield code="a">http://cds.cern.ch/img/cds.gif</subfield>
         </datafield>
        </record>
        """

        testrec_expected_xm = """
        <record>
        <controlfield tag="001">123456789</controlfield>
        <controlfield tag="003">SzGeCERN</controlfield>
         <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Test, John</subfield>
          <subfield code="u">Test University</subfield>
         </datafield>
         <datafield tag="856" ind1="4" ind2=" ">
          <subfield code="u">%(weburl)s/record/123456789/files/cds.gif</subfield>
         </datafield>
        </record>
        """ % { 'weburl': weburl}
        testrec_expected_hm = """
        001__ 123456789
        003__ SzGeCERN
        100__ $$aTest, John$$uTest University
        8564_ $$u%(weburl)s/record/123456789/files/cds.gif
        """ % { 'weburl': weburl}
        # insert test record:
        task_set_option('verbose', 0)
        recs = bibupload.xml_marc_to_records(test_to_upload)
        err, recid = bibupload.bibupload(recs[0], opt_mode='insert')
        # replace test buffers with real recid of inserted test record:
        testrec_expected_xm = testrec_expected_xm.replace('123456789',
                                                          str(recid))
        testrec_expected_hm = testrec_expected_hm.replace('123456789',
                                                          str(recid))
        test_to_correct = test_to_correct.replace('123456789',
                                                          str(recid))
        # correct test record with new FFT:
        task_set_option('verbose', 0)
        recs = bibupload.xml_marc_to_records(test_to_upload)
        bibupload.bibupload(recs[0], opt_mode='correct')

        # compare expected results:
        inserted_xm = print_record(recid, 'xm')
        inserted_hm = print_record(recid, 'hm')
        self.failUnless(compare_xmbuffers(inserted_xm,
                                          testrec_expected_xm))
        self.failUnless(compare_hmbuffers(inserted_hm,
                                          testrec_expected_hm))

        #print "\nRecid: " + str(recid) + "\n"
        #print testrec_expected_hm + "\n"
        #print print_record(recid, 'hm') + "\n"

        # FIXME: compare also var/data/files/.../ content
        # clean up after ourselves:
        bibupload.wipe_out_record_from_all_tables(recid)

test_suite = make_test_suite(BibUploadInsertModeTest,
                             BibUploadAppendModeTest,
                             BibUploadCorrectModeTest,
                             BibUploadReplaceModeTest,
                             BibUploadReferencesModeTest,
                             BibUploadRecordsWithSYSNOTest,
                             BibUploadRecordsWithEXTOAIIDTest,
                             BibUploadRecordsWithOAIIDTest,
                             BibUploadFMTModeTest,
                             BibUploadIndicatorsTest,
                             BibUploadUpperLowerCaseTest,
                             BibUploadStrongTagsTest,
                             BibUploadFFTModeTest)

#test_suite = make_test_suite(BibUploadStrongTagsTest,)

if __name__ == "__main__":
    warn_user_about_tests_and_run(test_suite)
