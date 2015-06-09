# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2015 CERN.
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

"""Unit tests for BibEdit functions"""

import re

import httpretty

from invenio.base.wrappers import lazy_import
from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite

get_xml_from_textmarc = lazy_import('invenio.legacy.bibedit.utils:get_xml_from_textmarc')
perform_doi_search = lazy_import('invenio.legacy.bibedit.engine:perform_doi_search')


class TextmarcToXMLTests(InvenioTestCase):
    """Test utility functions to convert textmarc to XML."""

    def test_get_xml_from_textmarc_success(self):
        textmarc = """100__ $$aDoe, J.$$uCERN
        245__ $$aPion production by 24 GeV/c protons in hydrogen
        260__ $$c1961
        300__ $$a15"""
        output = get_xml_from_textmarc(1, textmarc)
        self.assertEqual(output['resultMsg'], 'textmarc_parsing_success')

        xml_expected_output = """<record>
    <controlfield tag="001">1</controlfield>
        <datafield tag="100" ind1=" " ind2=" ">
            <subfield code="a">Doe, J.</subfield>
            <subfield code="u">CERN</subfield>
        </datafield>
        <datafield tag="245" ind1=" " ind2=" ">
            <subfield code="a">Pion production by 24 GeV/c protons in hydrogen</subfield>
        </datafield>
        <datafield tag="260" ind1=" " ind2=" ">
            <subfield code="c">1961</subfield>
        </datafield>
        <datafield tag="300" ind1=" " ind2=" ">
            <subfield code="a">15</subfield>
        </datafield>
</record>
        """
        self.assertEqual(re.sub("\s+", " ", output['resultXML'].strip()),
                         re.sub("\s+", " ", xml_expected_output.strip()))

    def test_get_xml_from_textmarc_wrong_field(self):
        textmarc = """1sasd00__ $$aDoe, J.$$uCERN
        245__ $$aPion production by 24 GeV/c protons in hydrogen
        260__ $$c1961
        300__ $$a15"""
        output = get_xml_from_textmarc(1, textmarc)
        self.assertEqual(output['resultMsg'], 'textmarc_parsing_error')
        expected_error = [1, "1sasd00__ $$aDoe, J.$$uCERN"]
        self.assertEqual(output['parse_error'][:-1], expected_error)

    def test_get_xml_from_textmarc_wrong_content(self):
        textmarc = """100__ $$a
        245__ $$aPion production by 24 GeV/c protons in hydrogen
        260__ $$c1961
        300__ $$a15"""
        output = get_xml_from_textmarc(1, textmarc)
        self.assertEqual(output['resultMsg'], 'textmarc_parsing_error')

    def test_accept_fft_tags_in_textmarc(self):
        textmarc = """100__ $$aDoe, J.$$uCERN
        FFT__ $$ahttp://scd-theses.u-strasbg.fr/1818/01/RICAUD_Helene_2008.pdf$$dFulltext"""
        output = get_xml_from_textmarc(1, textmarc)

        xml_expected_output = """<record>
        <controlfield tag="001">1</controlfield>
        <datafield tag="100" ind1=" " ind2=" ">
            <subfield code="a">Doe, J.</subfield>
            <subfield code="u">CERN</subfield>
        </datafield>
        <datafield tag="FFT" ind1=" " ind2=" ">
            <subfield code="a">http://scd-theses.u-strasbg.fr/1818/01/RICAUD_Helene_2008.pdf</subfield>
            <subfield code="d">Fulltext</subfield>
        </datafield>
        </record>"""

        self.assertEqual(re.sub("\s+", " ", output['resultXML'].strip()),
                         re.sub("\s+", " ", xml_expected_output.strip()))


class TestPerformDoiSearch(InvenioTestCase):
    """Test the perform_doi_search function.

    It resolves the doi using dx.doi.org page and returns the url of
    the resource.
    """

    @httpretty.activate
    def test_normal(self):
        """Check if some standard doi is working"""
        doi = "10.1007/BF02724522"
        wrong_output = {}

        def response(request, uri, headers):
            headers.update({
                'status': 303,
                'Location': 'http://link.springer.com/10.1007/BF02724522'
            })
            return (303, headers, '')

        httpretty.register_uri(
            httpretty.POST,
            'http://dx.doi.org/?hdl=10.1016%2F0550-3213%2889%2990423-9',
            body=response,
        )

        self.assertNotEqual(perform_doi_search(doi), wrong_output)

    @httpretty.activate
    def test_no_headers(self):
        """Check if the doi that requires 'User-Agent' header is working"""
        doi = "10.1016/0550-3213(89)90423-9"
        wrong_output = {}

        def response(request, uri, headers):
            assert 'user-agent' in request.headers
            headers.update({
                'status': 303,
                'Location': 'http://linkinghub.elsevier.com/retrieve/pii/'
                            '0550321389904239'
            })
            return (303, headers, '')

        httpretty.register_uri(
            httpretty.POST,
            'http://dx.doi.org/',
            body=response,
        )

        self.assertNotEqual(perform_doi_search(doi), wrong_output)

TEST_SUITE = make_test_suite(TextmarcToXMLTests,
                             TestPerformDoiSearch)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
