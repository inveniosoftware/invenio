# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

"""
BibField module regression tests.
"""

__revision__ = "$Id$"

import unittest

from invenio.config import CFG_TMPDIR
from invenio.bibfield import get_record, create_record, create_records
from invenio.bibrecord import record_get_field_values
from invenio.dbquery import run_sql
from invenio.search_engine import get_record as search_engine_get_record

from invenio.testutils import make_test_suite, run_test_suite


class BibFieldRecordFieldValuesTest(unittest.TestCase):
    """
    Check values returned by BibField for record fields are consistent or not
    """

    def test_normal_fields_availability_and_values(self):
        """bibfield - access to normal fields"""
        record = get_record(12)
        self.assertTrue(record.get('asdas') is None)
        self.assertEqual('12', record['recid'])
        self.assertTrue('recid' in record.get_persistent_identifiers())
        self.assertEqual(record['recid'], record.get('recid'))
        self.assertEqual('Physics at the front-end of a neutrino factory : a quantitative appraisal', record['title.title'])
        self.assertEqual('Physics at the front-end of a neutrino factory : a quantitative appraisal', record['title']['title'])
        self.assertFalse('title.subtitle' in record)
        self.assertEqual('Physics at the front-end of a neutrino factory : a quantitative appraisal', record.get('title.title'))
        self.assertEqual('Mangano', record['authors[0].last_name'])
        self.assertEqual('M L', record['authors[0].first_name'])
        self.assertEqual(19, len(record['authors']))
        self.assertEqual(19, len(record['authors.last_name']))

    def test_compare_field_values_with_bibrecord_values(self):
        """bibfield - same value as in bibrecord"""
        record = get_record(1)
        bibrecord_value = record_get_field_values(search_engine_get_record(1), '245', ' ', ' ', 'a')[0]
        self.assertEqual(bibrecord_value, record['title.title'])

    def test_derived_fields_availability_and_values(self):
        """bibfield - values of derived fields"""
        record = get_record(12)
        self.assertEqual(19, record['number_of_authors'])

    def test_calculated_fields_availability_and_values(self):
        """bibfield - values of calculated fields"""
        record = get_record(31)
        self.assertEqual(2, record['_number_of_copies'])
        run_sql("insert into crcITEM(barcode, id_bibrec) VALUES('test',31)")
        self.assertEqual(2, record['_number_of_copies'])
        self.assertEqual(3, record.get('_number_of_copies', reset_cache=True))
        run_sql("delete from crcITEM WHERE barcode='test'")
        record.update_field_cache('_number_of_copies')
        self.assertEqual(2, record['_number_of_copies'])
        self.assertEqual(2, record['number_of_copies'])

    def test_get_using_format_string(self):
        """
        bibfield - format values using format string
        """
        #Only python 2.5 or higher
        #record = get_record(97)
        #self.assertEqual('Treusch, R', record.get('authors[0]', formatstring="{0[last_name]}, {0[first_name]}"))

    def test_get_using_formating_function(self):
        """bibfield - format values using formating function"""
        def dummy(s):
            return s.upper()
        record = get_record(1)
        self.assertEqual('ALEPH EXPERIMENT: CANDIDATE OF HIGGS BOSON PRODUCTION',
                         record.get('title.title', formatfunction=dummy))


class BibFieldCreateRecordTests(unittest.TestCase):
    """
    Bibfield - demo file parsing test
    """

    def setUp(self):
        """Initialize stuff"""
        f = open(CFG_TMPDIR + '/demobibdata.xml', 'r')
        blob = f.read()
        f.close()
        self.recs = [rec for rec in create_records(blob, master_format='marc', schema='xml')]

    def test_records_created(self):
        """ bibfield - demo file how many records are created """
        self.assertEqual(141, len(self.recs))

    def test_create_record_with_collection_tag(self):
        """ bibfield - create_record() for single record in collection"""
        blob = """
        <collection>
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        </datafield>
        </record>
        </collection>
        """
        record = create_record(blob, master_format='marc', schema='xml')
        record1 = create_records(blob, master_format='marc', schema='xml')[0]
        self.assertEqual(record1, record)

    def test_empty_collection(self):
        """bibfield - empty collection"""
        blob_error0 = """<collection></collection>"""
        rec = create_record(blob_error0, master_format='marc', schema='xml')
        self.assertTrue(rec.is_empty())
        records = create_records(blob_error0)
        self.assertEqual(len(records), 0)

    def test_fft_url_tags(self):
        """bibfield - FFT versus URL"""
        marc_blob = """
              <record>
                <datafield tag="037" ind1=" " ind2=" ">
                  <subfield code="a">CERN-HI-6206002</subfield>
                </datafield>
                <datafield tag="041" ind1=" " ind2=" ">
                  <subfield code="a">eng</subfield>
                </datafield>
                <datafield tag="245" ind1=" " ind2=" ">
                  <subfield code="a">At CERN in 1962</subfield>
                  <subfield code="s">eight Nobel prizewinners</subfield>
                </datafield>
                <datafield tag="260" ind1=" " ind2=" ">
                  <subfield code="c">1962</subfield>
                </datafield>
                <datafield tag="506" ind1="1" ind2=" ">
                  <subfield code="a">jekyll_only</subfield>
                </datafield>
                <datafield tag="521" ind1=" " ind2=" ">
                  <subfield code="a">In 1962, CERN hosted the 11th International Conference on High Energy Physics. Among the distinguished visitors were eight Nobel prizewinners.Left to right: Cecil F. Powell, Isidor I. Rabi, Werner Heisenberg, Edwin M. McMillan, Emile Segre, Tsung Dao Lee, Chen Ning Yang and Robert Hofstadter.</subfield>
                </datafield>
                <datafield tag="590" ind1=" " ind2=" ">
                  <subfield code="a">En 1962, le CERN est l'hote de la onzieme Conference Internationale de Physique des Hautes Energies. Parmi les visiteurs eminents se trouvaient huit laureats du prix Nobel.De gauche a droite: Cecil F. Powell, Isidor I. Rabi, Werner Heisenberg, Edwin M. McMillan, Emile Segre, Tsung Dao Lee, Chen Ning Yang et Robert Hofstadter.</subfield>
                </datafield>
                <datafield tag="595" ind1=" " ind2=" ">
                  <subfield code="a">Press</subfield>
                </datafield>
                <datafield tag="650" ind1="1" ind2="7">
                  <subfield code="2">SzGeCERN</subfield>
                  <subfield code="a">Personalities and History of CERN</subfield>
                </datafield>
                <datafield tag="653" ind1="1" ind2=" ">
                  <subfield code="a">Nobel laureate</subfield>
                </datafield>
                <datafield tag="FFT" ind1=" " ind2=" ">
                  <subfield code="a">http://invenio-software.org/download/invenio-demo-site-files/6206002.jpg</subfield>
                  <subfield code="x">http://invenio-software.org/download/invenio-demo-site-files/6206002.gif</subfield>
                </datafield>
                <datafield tag="909" ind1="C" ind2="0">
                  <subfield code="o">0000736PHOPHO</subfield>
                </datafield>
                <datafield tag="909" ind1="C" ind2="0">
                  <subfield code="y">1962</subfield>
                </datafield>
                <datafield tag="909" ind1="C" ind2="0">
                  <subfield code="b">81</subfield>
                </datafield>
                <datafield tag="909" ind1="C" ind2="1">
                  <subfield code="c">1998-07-23</subfield>
                  <subfield code="l">50</subfield>
                  <subfield code="m">2002-07-15</subfield>
                  <subfield code="o">CM</subfield>
                </datafield>
                <datafield tag="856" ind1="4" ind2=" ">
                  <subfield code="u">http://www.nobel.se/physics/laureates/1950/index.html</subfield>
                  <subfield code="y">The Nobel Prize in Physics 1950 : Cecil Frank Powell</subfield>
                </datafield>
                <datafield tag="856" ind1="4" ind2=" ">
                  <subfield code="u">http://www.nobel.se/physics/laureates/1944/index.html</subfield>
                  <subfield code="y">The Nobel Prize in Physics 1944 : Isidor Isaac Rabi</subfield>
                </datafield>
                <datafield tag="856" ind1="4" ind2=" ">
                  <subfield code="u">http://www.nobel.se/physics/laureates/1932/index.html</subfield>
                  <subfield code="y">The Nobel Prize in Physics 1932 : Werner Karl Heisenberg</subfield>
                </datafield>
                <datafield tag="856" ind1="4" ind2=" ">
                  <subfield code="u">http://www.nobel.se/chemistry/laureates/1951/index.html</subfield>
                  <subfield code="y">The Nobel Prize in Chemistry 1951 : Edwin Mattison McMillan</subfield>
                </datafield>
                <datafield tag="856" ind1="4" ind2=" ">
                  <subfield code="u">http://www.nobel.se/physics/laureates/1959/index.html</subfield>
                  <subfield code="y">The Nobel Prize in Physics 1959 : Emilio Gino Segre</subfield>
                </datafield>
                <datafield tag="856" ind1="4" ind2=" ">
                  <subfield code="u">http://www.nobel.se/physics/laureates/1957/index.html</subfield>
                  <subfield code="y">The Nobel Prize in Physics 1957 : Chen Ning Yang and Tsung-Dao Lee</subfield>
                </datafield>
                <datafield tag="856" ind1="4" ind2=" ">
                  <subfield code="u">http://www.nobel.se/physics/laureates/1961/index.html</subfield>
                  <subfield code="y">The Nobel Prize in Physics 1961 : Robert Hofstadter</subfield>
                </datafield>
                <datafield tag="909" ind1="C" ind2="P">
                  <subfield code="s">6206002 (1962)</subfield>
                </datafield>
                <datafield tag="909" ind1="C" ind2="S">
                  <subfield code="s">n</subfield>
                  <subfield code="w">199830</subfield>
                </datafield>
                <datafield tag="980" ind1=" " ind2=" ">
                  <subfield code="a">PICTURE</subfield>
                </datafield>
              </record>"""
        rec = create_record(marc_blob, master_format='marc', schema='xml')
        self.assertTrue('fft' in rec)
        self.assertTrue(len(rec['fft']) == 1)
        self.assertTrue(rec['fft[0].path'] == "http://invenio-software.org/download/invenio-demo-site-files/6206002.jpg")
        self.assertTrue('url' in rec)
        self.assertTrue(len(rec['url']) == 7)
        self.assertTrue(rec['url[0].url'] == "http://www.nobel.se/physics/laureates/1950/index.html")

    def test_bibdoc_integration(self):
        """bibfield - bibdoc integration"""
        rec = get_record(7)

        self.assertTrue('_files' in rec)
        self.assertEquals(len(rec['files']), 2)
        image = rec['files'][1]
        self.assertEquals(image['eformat'], '.jpeg')
        self.assertEquals(image['name'], '9806033')

        bibdoc = rec['bibdocs'].list_latest_files()[1]
        self.assertEquals(image['name'], bibdoc.name)


class BibFieldLegacyTests(unittest.TestCase):
    """
    Legacy functionality tests
    """

    def test_legacy_export_as_marc(self):
        """docstring for test_legacy_export_as_marc"""
        pass

    def test_get_legacy_recstruct(self):
        """bibfield - legacy functions"""
        from invenio.search_engine import get_record as search_engine_get_record
        from invenio.bibrecord import record_get_field_value

        bibfield_recstruct = get_record(8).get_legacy_recstruct()
        bibrecord = search_engine_get_record(8)

        self.assertEqual(record_get_field_value(bibfield_recstruct, '100', code='a'),
                         record_get_field_value(bibrecord, '100', code='a'))
        self.assertEqual(len(bibfield_recstruct['999']), len(bibrecord['999']))

    def test_guess_legacy_field_names(self):
        """bibfied - guess legacy fields"""
        from invenio.bibfield import guess_legacy_field_names

        legacy_fields = guess_legacy_field_names(('100__a', '245'))
        self.assertEqual(legacy_fields['100__a'][0], 'authors[0].full_name')
        self.assertEqual(legacy_fields['245'][0], 'title')

        legacy_fields = guess_legacy_field_names('001', 'marc')
        self.assertEqual(legacy_fields['001'][0], 'recid')

        self.assertEquals(guess_legacy_field_names('foo', 'marc'), {'foo': []})
        self.assertEquals(guess_legacy_field_names('foo', 'bar'), {'foo': []})


class BibFieldProducerTests(unittest.TestCase):
    """
    Low level output tests
    """

    def test_produce_json_for_marc(self):
        """bibfield - produce json marc"""
        record = get_record(1)
        produced_marc = record.produce_json_for_marc()

        self.assertTrue({'001': '1'} in produced_marc)

    def test_produce_json_for_dublin_core(self):
        """bibfield - produce json dublin core"""
        record = get_record(1)
        date = record.get('version_id').strftime('%Y-%m-%dT%H:%M:%SZ')
        produced_dc = record.produce_json_for_dc()

        self.assertTrue({'dc:date': date} in produced_dc)


TEST_SUITE = make_test_suite(BibFieldRecordFieldValuesTest,
                             BibFieldCreateRecordTests,
                             BibFieldLegacyTests
                             )

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
