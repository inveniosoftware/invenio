# -*- coding: utf-8 -*-
#
# $Id: search_engine_tests.py,v 1.20 2008/08/11 12:49:27 kaplun Exp $
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2013 CERN.
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

"""Unit tests for the search engine."""

__revision__ = \
    "$Id: search_engine_tests.py,v 1.20 2008/08/11 12:49:27 kaplun Exp $"


from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

QueryResult = lazy_import('invenio.legacy.bibexport.fieldexporter_dblayer:QueryResult')


def _create_record_marc_xml():
    """Creates MARC XML containing one record"""
    xml_text="""
    <record>
      <datafield tag="260" ind1=" " ind2=" ">
        <subfield code="c">14 Dec 1998</subfield>
      </datafield>
      <datafield tag="260" ind1="A" ind2="B">
        <subfield code="c">14 Dec 1999</subfield>
      </datafield>
      <datafield tag="300" ind1=" " ind2=" ">
        <subfield code="a">6 p</subfield>
      </datafield>
      <datafield tag="595" ind1=" " ind2=" ">
        <subfield code="a">LANL EDS</subfield>
      </datafield>
      <datafield tag="650" ind1="1" ind2="7">
        <subfield code="D">SzGeCERN</subfield>
        <subfield code="a">Astrophysics and Astronomy</subfield>
      </datafield>
      <datafield tag="700" ind1=" " ind2=" ">
        <subfield code="a">Bridle, S L</subfield>
      </datafield>
      <datafield tag="856" ind1="0" ind2=" ">
        <subfield code="f">George Efstathiou &lt;gpe@ast.cam.ac.uk></subfield>
      </datafield>
      <datafield tag="909" ind1="C" ind2="0">
        <subfield code="y">1998</subfield>
      </datafield>
      <datafield tag="970" ind1=" " ind2=" ">
        <subfield code="a">002769520CER</subfield>
      </datafield>
    </record>"""

    return xml_text

class TestFieldExporter(InvenioTestCase):
    """Tests for exporting of fields."""
    pass

class TesQueryResult(InvenioTestCase):
    """Tests QueryResult class"""

    def test_get_number_of_records_found(self):
        """Test counting of found recotds in QueryResult"""
        #create MARC XML with multiple records
        records = "<collection>"

        records += _create_record_marc_xml()
        records += _create_record_marc_xml()
        records += _create_record_marc_xml()

        records += "</collection>"

        query_result = QueryResult(None, records)
        self.assertEqual(3, query_result.get_number_of_records_found())

TEST_SUITE = make_test_suite(TestFieldExporter, \
                             TesQueryResult)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
