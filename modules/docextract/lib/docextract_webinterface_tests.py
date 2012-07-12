# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

import unittest
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from invenio.config import CFG_SITE_URL, CFG_ETCDIR

IGNORE_LINE = '      <subfield code="a">Invenio'
EXPECTED_RESPONSE = """<record>
   <controlfield tag="001">1</controlfield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">1</subfield>
      <subfield code="h">D. Clowe, A. Gonzalez, and M. Markevitch</subfield>
      <subfield code="s">Astrophys.J.,604,596</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">2</subfield>
      <subfield code="h">C. L. Sarazin, X-Ray Emission</subfield>
      <subfield code="m">from Clusters of Galaxies (Cambridge University Press, Cambridge 1988)</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">3</subfield>
      <subfield code="h">M. Girardi, G. Giuricin, F. Mardirossian, M. Mezzetti, and W. Boschin</subfield>
      <subfield code="s">Astrophys.J.,505,74</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">4</subfield>
      <subfield code="h">D. A. White, C. Jones, and W. Forman</subfield>
      <subfield code="s">Mon.Not.Roy.Astron.Soc.,292,419</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">5</subfield>
      <subfield code="h">V.C. Rubin, N. Thonnard, and W. K. Ford</subfield>
      <subfield code="s">Astrophys.J.,238,471</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">6</subfield>
      <subfield code="h">A. Bosma</subfield>
      <subfield code="s">Astron.J.,86,1825</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">7</subfield>
      <subfield code="h">S.M. Faber and J.S. Gallagher</subfield>
      <subfield code="s">Ann.Rev.Astron.Astrophys.,17,135</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">8</subfield>
      <subfield code="h">M. Persic, P. Salucci, and F. Stel</subfield>
      <subfield code="s">Mon.Not.Roy.Astron.Soc.,281,27</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">9</subfield>
      <subfield code="h">M. Lowewnstein and R. E. White</subfield>
      <subfield code="s">Astrophys.J.,518,50</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">10</subfield>
      <subfield code="h">D. P. Clemens</subfield>
      <subfield code="s">Astrophys.J.,295,422</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="6">
      <subfield code="a">Invenio/1.0.0-rc0.735-eb90d refextract/1.0.0-rc0.735-eb90d-1326974791-0-0-9-10-0-0-1</subfield>
   </datafield>
</record>"""


def compare_references(test, a, b):
    def filter_lines(lines):
        return '\n'.join(
            [l for l in lines.split('\n') if not l.startswith(IGNORE_LINE)]
        )
    a = filter_lines(a)
    b = filter_lines(b)
    test.assertEqual(a, b)


class DocExtractTest(unittest.TestCase):
    def setUp(self):
        #setup_loggers(verbosity=1)
        self.maxDiff = 10000

    if HAS_REQUESTS:
        def test_upload(self):
            url = CFG_SITE_URL + '/textmining/api/extract-references-pdf'

            pdf = open("%s/docextract/example.pdf" % CFG_ETCDIR, 'rb')
            response = requests.post(url, files={'pdf': pdf})
            compare_references(self, response.content, EXPECTED_RESPONSE)

        def test_url(self):
            url = CFG_SITE_URL + '/textmining/api/extract-references-pdf-url'

            pdf = CFG_SITE_URL + '/textmining/example.pdf'
            response = requests.post(url, data={'url': pdf})
            print response.content
            compare_references(self, response.content, EXPECTED_RESPONSE)

        def test_txt(self):
            url = CFG_SITE_URL + '/textmining/api/extract-references-txt'

            pdf = open("%s/docextract/example.txt" % CFG_ETCDIR, 'rb')
            response = requests.post(url, files={'txt': pdf})
            compare_references(self, response.content, EXPECTED_RESPONSE)
