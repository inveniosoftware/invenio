# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""Test for workflow tasks used by OAI harvester."""

import os
import tempfile

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class OAIHarvesterUtils(InvenioTestCase):

    """Class to test the OAI XML utils tasks."""

    def test_identifier_extraction(self):
        """Test extracting identifier from OAI XML."""
        from invenio.modules.oaiharvester.utils import identifier_extraction_from_string
        xml_sample = ("<record><test></test>"
                      "<identifier>identifier1</identifier></record>")
        self.assertEqual(identifier_extraction_from_string(xml_sample, oai_namespace=""),
                         "identifier1")

    def test_identifier_extraction_with_namespace(self):
        """Test extracting identifier from OAI XML."""
        from invenio.modules.oaiharvester.utils import identifier_extraction_from_string
        xml_sample = ("<OAI-PMH xmlns='http://www.openarchives.org/OAI/2.0/'>"
                      "<record><test></test>"
                      "<identifier>identifier1</identifier></record>"
                      "</OAI-PMH>")
        self.assertEqual(identifier_extraction_from_string(xml_sample),
                         "identifier1")

    def test_records_extraction_without_namespace(self):
        """Test extracting records from OAI XML without a namespace."""
        from invenio.modules.oaiharvester.utils import record_extraction_from_string
        xml_sample = """
        <OAI-PMH>
        <responseDate>2014-11-05T09:32:51Z</responseDate>
        <request verb="GetRecord" identifier="oai:arXiv.org:0804.2273" metadataPrefix="arXiv">http://export.arxiv.org/oai2</request>
        <GetRecord>
        <record>
        <header>
         <identifier>oai:arXiv.org:0804.2273</identifier>
         <datestamp>2008-04-16</datestamp>
         <setSpec>cs</setSpec>
        </header>
        <metadata>
         <arXiv>
         <id>0804.2273</id><created>2008-04-14</created><authors><author><keyname>Lagoze</keyname><forenames>Carl</forenames></author><author><keyname>Van de Sompel</keyname><forenames>Herbert</forenames></author><author><keyname>Nelson</keyname><forenames>Michael L.</forenames></author><author><keyname>Warner</keyname><forenames>Simeon</forenames></author><author><keyname>Sanderson</keyname><forenames>Robert</forenames></author><author><keyname>Johnston</keyname><forenames>Pete</forenames></author></authors><title>Object Re-Use &amp; Exchange: A Resource-Centric Approach</title><categories>cs.DL cs.NI</categories><acm-class>C.2.3</acm-class><license>http://creativecommons.org/licenses/by/3.0/</license><abstract>  The OAI Object Reuse and Exchange (OAI-ORE) framework recasts the
        repository-centric notion of digital object to a bounded aggregation of Web
        resources. In this manner, digital library content is more integrated with the
        Web architecture, and thereby more accessible to Web applications and clients.
        This generalized notion of an aggregation that is independent of repository
        containment conforms more closely with notions in eScience and eScholarship,
        where content is distributed across multiple services and databases. We provide
        a motivation for the OAI-ORE project, review previous interoperability efforts,
        describe draft ORE specifications and report on promising results from early
        experimentation that illustrate improved interoperability and reuse of digital
        objects.
        </abstract></arXiv>
        </metadata>
        </record>
        </GetRecord>
        </OAI-PMH>
        """
        self.assertEqual(len(record_extraction_from_string(xml_sample, oai_namespace="")),
                         1)

    def test_records_extraction_with_namespace_getrecord(self):
        """Test extracting records from OAI XML with GetRecord."""
        from invenio.modules.oaiharvester.utils import record_extraction_from_string
        xml_sample = """<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><responseDate>2014-11-05T09:32:51Z</responseDate>
        <request verb="GetRecord" identifier="oai:arXiv.org:0804.2273" metadataPrefix="arXiv">http://export.arxiv.org/oai2</request>
        <GetRecord>
        <record>
        <header>
        <identifier>oai:arXiv.org:0804.2273</identifier>
        <datestamp>2008-04-16</datestamp>
        <setSpec>cs</setSpec>
        </header>
        <metadata>
        <arXiv xmlns="http://arxiv.org/OAI/arXiv/">
        <id>0804.2273</id><created>2008-04-14</created><authors><author><keyname>Lagoze</keyname><forenames>Carl</forenames></author><author><keyname>Van de Sompel</keyname><forenames>Herbert</forenames></author><author><keyname>Nelson</keyname><forenames>Michael L.</forenames></author><author><keyname>Warner</keyname><forenames>Simeon</forenames></author><author><keyname>Sanderson</keyname><forenames>Robert</forenames></author><author><keyname>Johnston</keyname><forenames>Pete</forenames></author></authors><title>Object Re-Use &amp; Exchange: A Resource-Centric Approach</title><categories>cs.DL cs.NI</categories><acm-class>C.2.3</acm-class><license>http://creativecommons.org/licenses/by/3.0/</license><abstract>  The OAI Object Reuse and Exchange (OAI-ORE) framework recasts the
        repository-centric notion of digital object to a bounded aggregation of Web
        resources. In this manner, digital library content is more integrated with the
        Web architecture, and thereby more accessible to Web applications and clients.
        This generalized notion of an aggregation that is independent of repository
        containment conforms more closely with notions in eScience and eScholarship,
        where content is distributed across multiple services and databases. We provide
        a motivation for the OAI-ORE project, review previous interoperability efforts,
        describe draft ORE specifications and report on promising results from early
        experimentation that illustrate improved interoperability and reuse of digital
        objects.
        </abstract></arXiv>
        </metadata>
        </record>
        </GetRecord>
        </OAI-PMH>"""
        self.assertEqual(len(record_extraction_from_string(xml_sample)),
                         1)

    def test_records_extraction_with_namespace_listrecords(self):
        """Test extracting records from OAI XML with ListRecords."""
        from invenio.modules.oaiharvester.utils import record_extraction_from_string
        xml_sample = """
        <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
        <responseDate>2014-11-05T09:30:08Z</responseDate><request from="2014-05-01" verb="ListRecords" set="INSPIRE:Conferences" metadataPrefix="marcxml" until="2014-05-02">http://inspirehep.net/oai2d</request><ListRecords>
        <record><header><identifier>oai:inspirehep.net:972855</identifier><datestamp>2014-05-02T12:22:51Z</datestamp><setSpec>INSPIRE:Conferences</setSpec></header><metadata><marc:record xmlns:marc="http://www.loc.gov/MARC21/slim" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd" type="Bibliographic">
             <marc:leader>00000coc  2200000uu 4500</marc:leader>
          <marc:controlfield tag="001">972855</marc:controlfield>
          <marc:controlfield tag="005">20140502142251.0</marc:controlfield>
          <marc:datafield tag="111" ind1=" " ind2=" ">
            <marc:subfield code="a">2000 IEEE Nuclear and Space Radiation Effects Conference</marc:subfield>
            <marc:subfield code="c">Reno, Nevada</marc:subfield>
            <marc:subfield code="d">24-28 Jul 2000</marc:subfield>
            <marc:subfield code="e">NSREC 2000</marc:subfield>
            <marc:subfield code="g">C00-07-24.3</marc:subfield>
            <marc:subfield code="x">2000-07-24</marc:subfield>
          </marc:datafield>
        </marc:record>
        </metadata></record><record><header><identifier>oai:inspirehep.net:974318</identifier><datestamp>2014-05-02T12:22:47Z</datestamp><setSpec>INSPIRE:Conferences</setSpec></header><metadata><marc:record xmlns:marc="http://www.loc.gov/MARC21/slim" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd" type="Bibliographic">
             <marc:leader>00000coc  2200000uu 4500</marc:leader>
          <marc:controlfield tag="001">974318</marc:controlfield>
          <marc:controlfield tag="005">20140502142246.0</marc:controlfield>
          <marc:datafield tag="111" ind1=" " ind2=" ">
            <marc:subfield code="a">2002 IEEE Nuclear and Space Radiation Effects Conference</marc:subfield>
            <marc:subfield code="c">Phoenix, Arizona</marc:subfield>
            <marc:subfield code="d">15-19 Jul 2002</marc:subfield>
            <marc:subfield code="e">NSREC 2002</marc:subfield>
            <marc:subfield code="g">C02-07-15.3</marc:subfield>
            <marc:subfield code="x">2002-07-15</marc:subfield>
          </marc:datafield>
        </marc:record>
        </metadata></record></ListRecords>
        </OAI-PMH>
        """
        self.assertEqual(len(record_extraction_from_string(xml_sample)),
                         2)

    def test_records_extraction_from_file(self):
        """Test extracting records from OAI XML."""
        from invenio.modules.oaiharvester.utils import record_extraction_from_file
        xml_sample = """
        <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
        <responseDate>2014-11-05T09:32:51Z</responseDate>
        <request verb="GetRecord" identifier="oai:arXiv.org:0804.2273" metadataPrefix="arXiv">http://export.arxiv.org/oai2</request>
        <GetRecord>
        <record>
        <header>
         <identifier>oai:arXiv.org:0804.2273</identifier>
         <datestamp>2008-04-16</datestamp>
         <setSpec>cs</setSpec>
        </header>
        <metadata>
         <arXiv xmlns="http://arxiv.org/OAI/arXiv/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://arxiv.org/OAI/arXiv/ http://arxiv.org/OAI/arXiv.xsd">
         <id>0804.2273</id><created>2008-04-14</created><authors><author><keyname>Lagoze</keyname><forenames>Carl</forenames></author><author><keyname>Van de Sompel</keyname><forenames>Herbert</forenames></author><author><keyname>Nelson</keyname><forenames>Michael L.</forenames></author><author><keyname>Warner</keyname><forenames>Simeon</forenames></author><author><keyname>Sanderson</keyname><forenames>Robert</forenames></author><author><keyname>Johnston</keyname><forenames>Pete</forenames></author></authors><title>Object Re-Use &amp; Exchange: A Resource-Centric Approach</title><categories>cs.DL cs.NI</categories><acm-class>C.2.3</acm-class><license>http://creativecommons.org/licenses/by/3.0/</license><abstract>  The OAI Object Reuse and Exchange (OAI-ORE) framework recasts the
        repository-centric notion of digital object to a bounded aggregation of Web
        resources. In this manner, digital library content is more integrated with the
        Web architecture, and thereby more accessible to Web applications and clients.
        This generalized notion of an aggregation that is independent of repository
        containment conforms more closely with notions in eScience and eScholarship,
        where content is distributed across multiple services and databases. We provide
        a motivation for the OAI-ORE project, review previous interoperability efforts,
        describe draft ORE specifications and report on promising results from early
        experimentation that illustrate improved interoperability and reuse of digital
        objects.
        </abstract></arXiv>
        </metadata>
        </record>
        </GetRecord>
        </OAI-PMH>
        """
        fd_tmp, path_tmp = tempfile.mkstemp()
        os.write(fd_tmp, xml_sample)
        os.close(fd_tmp)

        self.assertEqual(len(record_extraction_from_file(path_tmp)), 1)


TEST_SUITE = make_test_suite(OAIHarvesterUtils)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
