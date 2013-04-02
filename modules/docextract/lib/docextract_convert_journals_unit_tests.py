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

import os

import subprocess
from tempfile import NamedTemporaryFile, mkstemp

from invenio.testutils import make_test_suite, run_test_suite
from invenio.docextract_record import BibRecord
from invenio.refextract_kbs import get_kbs
from invenio.config import CFG_BINDIR, CFG_TMPDIR
from invenio.testutils import XmlTest
from invenio.docextract_convert_journals import USAGE_MESSAGE, convert_journals


class ConverterTests(XmlTest):
    def setUp(self):
        kb = [("TEST JOURNAL NAME", "Converted")]
        kbs_files = {'journals': kb}
        self.kb = get_kbs(custom_kbs_files=kbs_files)['journals']

    def test_simple(self):
        record = BibRecord()
        record.add_subfield('100__a', 'Test Journal Name')
        record.add_subfield('773__p', 'Test Journal Name')
        record.add_subfield('999C5s', 'Test Journal Name,100,10')
        converted_record = convert_journals(self.kb, record)

        expected_record = BibRecord()
        expected_record.add_subfield('100__a', 'Test Journal Name')
        expected_record.add_subfield('773__p', 'Converted')
        expected_record.add_subfield('999C5s', 'Converted,100,10')

        self.assertEqual(expected_record, converted_record)


class ScriptTests(XmlTest):
    def setUp(self):
        self.bin_path = os.path.join(CFG_BINDIR, 'convert_journals')

    def test_usage(self):
        process = subprocess.Popen([self.bin_path, '-h'],
                                   stderr=subprocess.PIPE,
                                   stdout=subprocess.PIPE)
        process.wait()
        self.assert_(USAGE_MESSAGE in process.stderr.read())

    def test_main(self):
        xml = """<record>
            <datafield tag="999" ind1="C" ind2="5">
                <subfield code="s">Test Journal Name,100,10</subfield>
            </datafield>
        </record>"""
        xml_temp_file = NamedTemporaryFile(dir=CFG_TMPDIR)
        xml_temp_file.write(xml)
        xml_temp_file.flush()

        kb = "TEST JOURNAL NAME---Converted"
        kb_temp_file = NamedTemporaryFile(dir=CFG_TMPDIR)
        kb_temp_file.write(kb)
        kb_temp_file.flush()

        dest_temp_fd, dest_temp_path = mkstemp(dir=CFG_TMPDIR)
        try:
            os.close(dest_temp_fd)

            process = subprocess.Popen([self.bin_path, xml_temp_file.name,
                                       '--kb', kb_temp_file.name,
                                       '-o', dest_temp_path],
                                       stderr=subprocess.PIPE,
                                       stdout=subprocess.PIPE)
            process.wait()

            transformed_xml = open(dest_temp_path).read()
            self.assertXmlEqual(transformed_xml, """<?xml version="1.0" encoding="UTF-8"?>
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record><datafield ind1="C" ind2="5" tag="999"><subfield code="s">Converted,100,10</subfield></datafield></record>
</collection>""")
        finally:
            os.unlink(dest_temp_path)


TEST_SUITE = make_test_suite(ScriptTests)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
