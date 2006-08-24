# -*- coding: utf-8 -*-

## $Id$
## CDS Invenio bibupload unit tests.

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

"""Unit tests for the bibupload."""

__version__ = "$Id$"

import unittest
import re
from invenio.bibupload import *
from invenio.search_engine import print_record
from invenio.config import tmpdir, etcdir
from invenio.testutils import make_test_suite, warn_user_about_tests_and_run, \
                              make_url, test_web_page_content, merge_error_messages

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
    
    def test_createRecordIdTest(self):
        """bibupload - try to create a new record ID in the database"""
        rec_id = create_new_record()
        self.assertNotEqual(-1,rec_id)
    
    def test_NoRetrieveRecordId(self):
        """bibupload - in insert mode the input file should not contain record ID"""
        #Initialise the global variable
        options['mode'] = 'insert'
        # We create create the record out of the xml marc
        rec = xml_marc_to_records(self.test)
        # We call the function which should retrieve the record id
        rec_id = retrieve_rec_id(rec[0])
        # We compare the value found with None
        self.assertEqual(None,rec_id)
    
    def test_insertCompletXmlMarcTest(self):
        """bibupload - insert complete MARCXML file"""
        #Initialise the global variable
        options['mode'] = 'insert'
        #options['verbose'] = 0
        # We create create the record out of the xml marc
        rec = xml_marc_to_records(self.test)
        # We call the main function with the record as a parameter
        error = bibupload(rec[0])
        self.assertEqual(0,error)

#TODO append Test
class AppendModeTest(unittest.TestCase):
    """Testing proper insert of the xml files"""
    
    def test_RetrieveRecordId(self):
        """bibupload - in insert mode the input file should contain record ID"""
        #Initialise the global variable
        options['mode'] = 'append'
        #Initialise the xml marc variable
        test = """<record>
        <controlfield tag ="001">001</controlfield>
        <datafield tag ="100" ind1="" ind2="">
        <subfield code="a">Simko, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""
        # We create create the record out of the xml marc
        rec = xml_marc_to_records(test)
        # We call the function which should retrieve the record id
        rec_id = retrieve_rec_id(rec[0])
        # We compare the value found with None
        self.assertNotEqual(None,rec_id)
    
    def test_appendCompletXmlMarcTest(self):
        """bibupload - append complete MARCXML file"""
        #Initialise the global variable
        options['mode'] = 'append'
        # Create a new record
        rec_id = create_new_record()
        #Initialise the xml marc we want to append
        test = """<collection>
        <record>
        <controlfield tag ="001">"""+str(rec_id)+ """</controlfield>
        <datafield tag ="100" ind1="" ind2="">
        <subfield code="a">Simko, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>
        </collection>"""
        # We create create the record out of the xml marc
        rec = xml_marc_to_records(test)
        # We call the main function with the record as a parameter
        error = bibupload(rec[0])
        self.assertEqual(0,error)

#TODO correct Test
#TODO replace Test
#TODO references Test
#TODO FMT Test
#TODO FFT Test
    
test_suite = make_test_suite(InsertModeTest,
                             AppendModeTest)

if __name__ == "__main__":
    warn_user_about_tests_and_run(test_suite)
