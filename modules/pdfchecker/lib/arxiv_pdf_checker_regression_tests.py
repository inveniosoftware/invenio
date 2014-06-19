# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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
from datetime import datetime
from tempfile import mkstemp

from invenio.testutils import make_test_suite, run_test_suite, InvenioTestCase
from invenio import bibupload
from invenio import bibtask
from invenio.dbquery import run_sql
from invenio.search_engine_utils import get_fieldvalues
from invenio import oai_harvest_daemon, \
                    oai_harvest_dblayer
from invenio.bibdocfile import BibRecDocs, \
                               InvenioBibDocFileError


EXAMPLE_PDF_URL_1 = "http://invenio-software.org/download/" \
                                          "invenio-demo-site-files/9812226.pdf"

EXAMPLE_PDF_URL_2 = "http://invenio-software.org/download/" \
                                          "invenio-demo-site-files/0105155.pdf"

RECID = 20
ARXIV_ID = '1005.1481'

ARXIV_OAI_RECORD_INFO = """<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
<responseDate>2013-04-16T13:50:10Z</responseDate>
<request verb="GetRecord" identifier="oai:arXiv.org:1304.4214" metadataPrefix="arXivRaw">http://export.arxiv.org/oai2</request>
<GetRecord>
<record>
<header>
 <identifier>oai:arXiv.org:1304.4214</identifier>
 <datestamp>2013-04-16</datestamp>
 <setSpec>physics:cond-mat</setSpec>
</header>
<metadata>
 <arXivRaw xmlns="http://arxiv.org/OAI/arXivRaw/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://arxiv.org/OAI/arXivRaw/ http://arxiv.org/OAI/arXivRaw.xsd">
 <id>1304.4214</id><submitter>John M. Tranquada</submitter><version version="v%s"><date>Mon, 15 Apr 2013 19:33:21 GMT</date><size>609kb</size><source_type>D</source_type></version><title>Neutron Scattering and Its Application to Strongly Correlated Systems</title><authors>Igor A. Zaliznyak and John M. Tranquada</authors><categories>cond-mat.str-el</categories><comments>31 pages, chapter for &quot;Strongly Correlated Systems: Experimental
  Techniques&quot;, edited by A. Avella and F. Mancini</comments><license>http://arxiv.org/licenses/nonexclusive-distrib/1.0/</license><abstract>  Neutron scattering is a powerful probe of strongly correlated systems. It can
directly detect common phenomena such as magnetic order, and can be used to
determine the coupling between magnetic moments through measurements of the
spin-wave dispersions. In the absence of magnetic order, one can detect diffuse
scattering and dynamic correlations. Neutrons are also sensitive to the
arrangement of atoms in a solid (crystal structure) and lattice dynamics
(phonons). In this chapter, we provide an introduction to neutrons and neutron
sources. The neutron scattering cross section is described and formulas are
given for nuclear diffraction, phonon scattering, magnetic diffraction, and
magnon scattering. As an experimental example, we describe measurements of
antiferromagnetic order, spin dynamics, and their evolution in the
La(2-x)Ba(x)CuO(4) family of high-temperature superconductors.
</abstract></arXivRaw>
</metadata>
</record>
</GetRecord>
</OAI-PMH>
"""

ARXIV_OAI_IDENTIFIERS = """<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
<responseDate>2014-06-19T15:07:18Z</responseDate>
<request verb="ListIdentifiers" until="2014-05-07" from="2014-05-05" metadataPrefix="arXiv">http://export.arxiv.org/oai2</request>
<ListIdentifiers>
<header>
 <identifier>oai:arXiv.org:0705.1765</identifier>
 <datestamp>2014-05-06</datestamp>
 <setSpec>physics:gr-qc</setSpec>
</header>
<header>
 <identifier>oai:arXiv.org:0705.3619</identifier>
 <datestamp>2014-05-06</datestamp>
 <setSpec>physics:gr-qc</setSpec>
</header>
<header>
 <identifier>oai:arXiv.org:0705.3623</identifier>
 <datestamp>2014-05-06</datestamp>
 <setSpec>physics:gr-qc</setSpec>
</header>
</ListIdentifiers>
</OAI-PMH>
"""

class TestTask(InvenioTestCase):
    def setUp(self, recid=RECID, arxiv_id=ARXIV_ID):
        self.recid = recid
        self.arxiv_id = arxiv_id
        self.arxiv_version = 1
        self.bibupload_xml = """<record>
            <controlfield tag="001">%s</controlfield>
            <datafield tag="037" ind1=" " ind2=" ">
                <subfield code="a">arXiv:%s</subfield>
                <subfield code="9">arXiv</subfield>
                <subfield code="c">hep-ph</subfield>
            </datafield>
        </record>""" % (recid, arxiv_id)

        bibtask.setup_loggers()
        bibtask.task_set_task_param('verbose', 0)
        recs = bibupload.xml_marc_to_records(self.bibupload_xml)
        status, dummy, err = bibupload.bibupload(recs[0], opt_mode='correct')
        assert status == 0, err.strip()
        assert len(get_fieldvalues(recid, '037__a')) == 1

        def mocked_oai_harvest_get(prefix, baseurl, harvestpath,
                                   verb, identifier, fro=None):
            temp_fd, temp_path = mkstemp()
            if verb == 'GetRecord':
                content = ARXIV_OAI_RECORD_INFO % self.arxiv_version
            elif verb == 'ListIdentifiers':
                content = ARXIV_OAI_IDENTIFIERS
            else:
                raise Exception()
            os.write(temp_fd, content)
            os.close(temp_fd)
            return [temp_path]

        self.oai_harvest_get = oai_harvest_daemon.oai_harvest_get
        oai_harvest_daemon.oai_harvest_get = mocked_oai_harvest_get

        def mocked_get_oai_src(params={}):
            return [{'baseurl': ''}]

        self.get_oai_src = oai_harvest_dblayer.get_oai_src
        oai_harvest_dblayer.get_oai_src = mocked_get_oai_src

    def tearDown(self):
        """Helper function that restores recID 3 MARCXML"""
        recs = bibupload.xml_marc_to_records(self.bibupload_xml)
        bibupload.bibupload(recs[0], opt_mode='delete')
        oai_harvest_daemon.oai_harvest_get = self.oai_harvest_get
        oai_harvest_dblayer.get_oai_src = self.get_oai_src

    def clean_bibtask(self):
        from invenio.arxiv_pdf_checker import NAME
        run_sql("""DELETE FROM schTASK
                   WHERE user = %s
                   ORDER BY id DESC LIMIT 1
        """, [NAME])

    def clean_bibupload_fft(self):
        run_sql("""DELETE FROM schTASK
                   WHERE proc = 'bibupload:FFT'
                   ORDER BY id DESC LIMIT 1""")


    def test_fetch_records(self):
        from invenio.arxiv_pdf_checker import fetch_updated_arxiv_records
        date = datetime(year=1900, month=1, day=1)
        fetch_updated_arxiv_records(date)

    def test_task_run_core(self):
        from invenio.arxiv_pdf_checker import task_run_core
        self.assert_(task_run_core())
        self.clean_bibtask()
        self.clean_bibupload_fft()

    def test_extract_arxiv_ids_from_recid(self):
        from invenio.arxiv_pdf_checker import extract_arxiv_ids_from_recid
        self.assertEqual(list(extract_arxiv_ids_from_recid(self.recid)), [self.arxiv_id])

    def test_build_arxiv_url(self):
        from invenio.arxiv_pdf_checker import build_arxiv_url
        self.assert_('1012.0299' in build_arxiv_url('1012.0299', 1))

    def test_record_has_fulltext(self):
        from invenio.arxiv_pdf_checker import record_has_fulltext
        record_has_fulltext(1)

    def test_download_external_url_invalid_content_type(self):
        from invenio.filedownloadutils import (download_external_url,
                                               InvenioFileDownloadError)
        from invenio.config import CFG_SITE_URL
        temp_fd, temp_path = mkstemp()
        os.close(temp_fd)
        try:
            try:
                download_external_url(CFG_SITE_URL,
                                      temp_path,
                                      content_type='pdf')
                self.fail()
            except InvenioFileDownloadError:
                pass
        finally:
            os.unlink(temp_path)

    def test_download_external_url(self):
        from invenio.filedownloadutils import (download_external_url,
                                               InvenioFileDownloadError)

        temp_fd, temp_path = mkstemp()
        os.close(temp_fd)
        try:
            try:
                download_external_url(EXAMPLE_PDF_URL_1,
                                      temp_path,
                                      content_type='pdf')
            except InvenioFileDownloadError, e:
                self.fail(str(e))
        finally:
            os.unlink(temp_path)

    def test_process_one(self):
        from invenio import arxiv_pdf_checker
        from invenio.arxiv_pdf_checker import process_one, \
                                              FoundExistingPdf, \
                                              fetch_arxiv_pdf_status, \
                                              STATUS_OK, \
                                              AlreadyHarvested
        arxiv_pdf_checker.CFG_ARXIV_URL_PATTERN = EXAMPLE_PDF_URL_1 + "?%s%s"

        # Make sure there is no harvesting state stored or this test will fail
        run_sql('DELETE FROM bibARXIVPDF WHERE id_bibrec = %s', [self.recid])

        def look_for_fulltext(recid):
            """Look for fulltext pdf (bibdocfile) for a given recid"""
            rec_info = BibRecDocs(recid)
            docs = rec_info.list_bibdocs()

            for doc in docs:
                for d in doc.list_all_files():
                    if d.get_format().strip('.') in ['pdf', 'pdfa', 'PDF']:
                        try:
                            yield doc, d
                        except InvenioBibDocFileError:
                            pass


        # Remove all pdfs from record 3
        for doc, docfile in look_for_fulltext(self.recid):
            doc.delete_file(docfile.get_format(), docfile.get_version())
            if not doc.list_all_files():
                doc.expunge()

        try:
            process_one(self.recid)
        finally:
            self.clean_bibtask()

        # Check for existing pdf
        docs = list(look_for_fulltext(self.recid))
        if not docs:
            self.fail()

        # Check that harvesting state is stored
        status, version = fetch_arxiv_pdf_status(self.recid)
        self.assertEqual(status, STATUS_OK)
        self.assertEqual(version, 1)

        try:
            process_one(self.recid)
            self.fail()
        except AlreadyHarvested:
            pass

        # Even though the version is changed the md5 is the same
        self.arxiv_version = 2
        try:
            process_one(self.recid)
            self.fail()
        except FoundExistingPdf:
            pass

        arxiv_pdf_checker.CFG_ARXIV_URL_PATTERN = EXAMPLE_PDF_URL_2 + "?%s%s"
        self.arxiv_version = 3
        try:
            process_one(self.recid)
        finally:
            self.clean_bibtask()

        # We know the PDF is attached, run process_one again
        # and it needs to raise an error
        try:
            process_one(self.recid)
            self.fail()
        except AlreadyHarvested:
            run_sql('DELETE FROM bibARXIVPDF WHERE id_bibrec = %s',
                    [self.recid])

        # Restore state
        for doc, docfile in docs:
            doc.delete_file(docfile.get_format(), docfile.get_version())
            if not doc.list_all_files():
                doc.expunge()

        self.clean_bibupload_fft()


TEST_SUITE = make_test_suite(TestTask)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
