# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
from invenio.testutils import make_test_suite, run_test_suite, InvenioXmlTestCase
from invenio.config import CFG_SITE_URL, CFG_ETCDIR, CFG_INSPIRE_SITE
from invenio.bibrecord import create_record, record_xml_output, record_delete_field

if CFG_INSPIRE_SITE:
    EXPECTED_RESPONSE = """<record>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">1</subfield>
    <subfield code="h">D. Clowe, A. Gonzalez, and M. Markevitch</subfield>
    <subfield code="s">Astrophys. J.,604,596</subfield>
    <subfield code="y">2004</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">2</subfield>
    <subfield code="h">C. L. Sarazin, X-Ray Emission</subfield>
    <subfield code="m">from Clusters of Galaxies (Cambridge University Press, Cambridge)</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">3</subfield>
    <subfield code="h">M. Girardi, G. Giuricin, F. Mardirossian, M. Mezzetti, and W. Boschin</subfield>
    <subfield code="s">Astrophys. J.,505,74</subfield>
    <subfield code="y">1998</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">4</subfield>
    <subfield code="h">D. A. White, C. Jones, and W. Forman</subfield>
    <subfield code="s">Mon. Not. R. Astron. Soc.,292,419</subfield>
    <subfield code="y">1997</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">5</subfield>
    <subfield code="h">V.C. Rubin, N. Thonnard, and W. K. Ford</subfield>
    <subfield code="s">Astrophys. J.,238,471</subfield>
    <subfield code="y">1980</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">6</subfield>
    <subfield code="h">A. Bosma</subfield>
    <subfield code="s">Astron. J.,86,1825</subfield>
    <subfield code="y">1981</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">7</subfield>
    <subfield code="h">S.M. Faber and J.S. Gallagher</subfield>
    <subfield code="s">Annu. Rev. Astron. Astrophys.,17,135</subfield>
    <subfield code="y">1979</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">8</subfield>
    <subfield code="h">M. Persic, P. Salucci, and F. Stel</subfield>
    <subfield code="s">Mon. Not. R. Astron. Soc.,281,27</subfield>
    <subfield code="y">1996</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">9</subfield>
    <subfield code="h">M. Lowewnstein and R. E. White</subfield>
    <subfield code="s">Astrophys. J.,518,50</subfield>
    <subfield code="y">1999</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">10</subfield>
    <subfield code="h">D. P. Clemens</subfield>
    <subfield code="s">Astrophys. J.,295,422</subfield>
    <subfield code="y">1985</subfield>
  </datafield>
</record>
"""
else:
    EXPECTED_RESPONSE = """<record>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">1</subfield>
      <subfield code="h">D. Clowe, A. Gonzalez, and M. Markevitch</subfield>
      <subfield code="s">Astrophys. J. 604 (2004) 596</subfield>
      <subfield code="y">2004</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">2</subfield>
      <subfield code="h">C. L. Sarazin, X-Ray Emission</subfield>
      <subfield code="m">from Clusters of Galaxies (Cambridge University Press, Cambridge)</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">3</subfield>
      <subfield code="h">M. Girardi, G. Giuricin, F. Mardirossian, M. Mezzetti, and W. Boschin</subfield>
      <subfield code="s">Astrophys. J. 505 (1998) 74</subfield>
      <subfield code="y">1998</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">4</subfield>
      <subfield code="h">D. A. White, C. Jones, and W. Forman</subfield>
      <subfield code="s">Mon. Not. R. Astron. Soc. 292 (1997) 419</subfield>
      <subfield code="y">1997</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">5</subfield>
      <subfield code="h">V.C. Rubin, N. Thonnard, and W. K. Ford</subfield>
      <subfield code="s">Astrophys. J. 238 (1980) 471</subfield>
      <subfield code="y">1980</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">6</subfield>
      <subfield code="h">A. Bosma</subfield>
      <subfield code="s">Astron. J. 86 (1981) 1825</subfield>
      <subfield code="y">1981</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">7</subfield>
      <subfield code="h">S.M. Faber and J.S. Gallagher</subfield>
      <subfield code="s">Annu. Rev. Astron. Astrophys. 17 (1979) 135</subfield>
      <subfield code="y">1979</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">8</subfield>
      <subfield code="h">M. Persic, P. Salucci, and F. Stel</subfield>
      <subfield code="s">Mon. Not. R. Astron. Soc. 281 (1996) 27</subfield>
      <subfield code="y">1996</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">9</subfield>
      <subfield code="h">M. Lowewnstein and R. E. White</subfield>
      <subfield code="s">Astrophys. J. 518 (1999) 50</subfield>
      <subfield code="y">1999</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">10</subfield>
      <subfield code="h">D. P. Clemens</subfield>
      <subfield code="s">Astrophys. J. 295 (1985) 422</subfield>
      <subfield code="y">1985</subfield>
   </datafield>
</record>"""


def compare_references(test, a, b):
    ## Let's normalize records to remove the Invenio refextract signature
    a = create_record(a)[0]
    b = create_record(b)[0]
    record_delete_field(a, '999', 'C', '6')
    a = record_xml_output(a)
    b = record_xml_output(b)
    test.assertXmlEqual(a, b)


class DocExtractTest(InvenioXmlTestCase):
    if HAS_REQUESTS:
        def test_upload(self):
            url = CFG_SITE_URL + '/textmining/api/extract-references-pdf'

            pdf = open("%s/docextract/example.pdf" % CFG_ETCDIR, 'rb')
            response = requests.post(url, files={'pdf': pdf})
            # Remove stats tag
            lines = response.content.split('\n')
            lines[-6:-1] = []
            compare_references(self, '\n'.join(lines), EXPECTED_RESPONSE)

        def test_url(self):
            url = CFG_SITE_URL + '/textmining/api/extract-references-pdf-url'

            pdf = CFG_SITE_URL + '/textmining/example.pdf'
            response = requests.post(url, data={'url': pdf})
            compare_references(self, response.content, EXPECTED_RESPONSE)

        def test_txt(self):
            url = CFG_SITE_URL + '/textmining/api/extract-references-txt'

            pdf = open("%s/docextract/example.txt" % CFG_ETCDIR, 'rb')
            response = requests.post(url, files={'txt': pdf})
            # Remove stats tag
            lines = response.content.split('\n')
            lines[-6:-1] = []
            compare_references(self, '\n'.join(lines), EXPECTED_RESPONSE)

TEST_SUITE = make_test_suite(DocExtractTest)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
