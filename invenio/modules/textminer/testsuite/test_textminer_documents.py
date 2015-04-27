# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2013 CERN.
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

import pkg_resources
import sys
pyv = sys.version_info
if pyv[0] == 2 and pyv[1] < 7:
    import unittest2 as unittest
else:
    import unittest
try:
    import requests
    from werkzeug.local import LocalProxy
    from flask import url_for
    def has_request():
        try:
            return requests.get(
                url_for('collections.index', _external=True)).status_code == 200
        except:
            return False
    HAS_REQUESTS = LocalProxy(has_request)
except ImportError:
    HAS_REQUESTS = False
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

def expected_response():
    from invenio.config import CFG_INSPIRE_SITE
    if CFG_INSPIRE_SITE:
        EXPECTED_RESPONSE = """<record>
      <controlfield tag="001">1</controlfield>
      <datafield tag="999" ind1="C" ind2="5">
        <subfield code="o">1</subfield>
        <subfield code="h">D. Clowe, A. Gonzalez, and M. Markevitch</subfield>
        <subfield code="s">Astrophys. J.,604,596</subfield>
        <subfield code="y">2004</subfield>
      </datafield>
      <datafield tag="999" ind1="C" ind2="5">
        <subfield code="o">2</subfield>
        <subfield code="h">C. L. Sarazin, X-Ray Emission</subfield>
        <subfield code="m">from Clusters of Galaxies (Cambridge University Press, Cambridge 1988)</subfield>
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
       <controlfield tag="001">1</controlfield>
       <datafield tag="999" ind1="C" ind2="5">
          <subfield code="o">1</subfield>
          <subfield code="h">D. Clowe, A. Gonzalez, and M. Markevitch</subfield>
          <subfield code="s">Astrophys. J. 604 (2004) 596</subfield>
          <subfield code="y">2004</subfield>
       </datafield>
       <datafield tag="999" ind1="C" ind2="5">
          <subfield code="o">2</subfield>
          <subfield code="h">C. L. Sarazin, X-Ray Emission</subfield>
          <subfield code="m">from Clusters of Galaxies (Cambridge University Press, Cambridge 1988)</subfield>
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
    return EXPECTED_RESPONSE

def compare_references(test, a, b):
    from invenio.legacy.bibrecord import create_record, record_xml_output, \
        record_delete_field
    ## Let's normalize records to remove the Invenio refextract signature
    a = create_record(a)[0]
    b = create_record(b)[0]
    record_delete_field(a, '999', 'C', '6')
    a = record_xml_output(a)
    b = record_xml_output(b)
    test.assertEqual(a, b)


class DocExtractTest(InvenioTestCase):
    def setUp(self):
        #setup_loggers(verbosity=1)
        self.maxDiff = 10000

    @unittest.skipUnless(HAS_REQUESTS, 'no request')
    def test_upload(self):
        from invenio.config import CFG_SITE_URL, CFG_ETCDIR
        url = CFG_SITE_URL + '/textmining/api/extract-references-pdf'

        pdf = open(pkg_resources.resource_filename(
            'invenio.modules.textminer.testsuite',
            'data/example.pdf'), 'rb')
        response = requests.post(url, files={'pdf': pdf})
        # Remove stats tag
        lines = response.content.split('\n')
        lines[-6:-1] = []
        compare_references(self, '\n'.join(lines), expected_response())

    @unittest.skipUnless(HAS_REQUESTS, 'no request')
    def test_url(self):
        from invenio.config import CFG_SITE_URL
        url = CFG_SITE_URL + '/textmining/api/extract-references-pdf-url'

        pdf = CFG_SITE_URL + '/textmining/example.pdf'
        response = requests.post(url, data={'url': pdf})
        compare_references(self, response.content, expected_response())

    @unittest.skipUnless(HAS_REQUESTS, 'no request')
    def test_txt(self):
        from invenio.config import CFG_SITE_URL
        url = CFG_SITE_URL + '/textmining/api/extract-references-txt'

        pdf = open(pkg_resources.resource_filename(
            'invenio.modules.textminer.testsuite',
            'data/example.txt'), 'rb')
        response = requests.post(url, files={'txt': pdf})
        # Remove stats tag
        lines = response.content.split('\n')
        lines[-6:-1] = []
        compare_references(self, '\n'.join(lines), expected_response())

TEST_SUITE = make_test_suite(DocExtractTest)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
