# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import os

import subprocess
from tempfile import NamedTemporaryFile, mkstemp

from invenio.testsuite import InvenioXmlTestCase
from invenio.testsuite import make_test_suite, run_test_suite
from invenio.base.utils import run_py_func


class ConverterTests(InvenioXmlTestCase):

    def setUp(self):
        from invenio.legacy.refextract.kbs import get_kbs
        kb = [("TEST JOURNAL NAME", "Converted")]
        kbs_files = {'journals': kb}
        self.kb = get_kbs(custom_kbs_files=kbs_files)['journals']

    def test_simple(self):
        from invenio.legacy.docextract.record import BibRecord
        from invenio.legacy.docextract.convert_journals import convert_journals
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


class ScriptTests(InvenioXmlTestCase):

    def test_usage(self):
        from invenio.legacy.docextract.convert_journals import USAGE_MESSAGE
        from invenio.legacy.docextract.scripts.convert_journals import main

        err = run_py_func(main, ["convert_journals", "-h"]).err
        self.assert_(USAGE_MESSAGE in err)

    def test_main(self):
        from invenio.config import CFG_TMPDIR
        from invenio.legacy.docextract.scripts.convert_journals import main
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
            run_py_func(main, ['convert_journals', xml_temp_file.name,
                               '--kb', kb_temp_file.name,
                               '-o', dest_temp_path])

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
