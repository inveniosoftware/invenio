# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2015 CERN.
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

"""Unit tests for the hepdatautils library."""
__revision__ = "$Id$"

import os
import cPickle

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

hepdatautils = lazy_import('invenio.utils.hepdata.api')
Dataset = lazy_import('invenio.utils.hepdata.api:Dataset')
bibrecord = lazy_import('invenio.legacy.bibrecord')


class TestParsingSystematics(InvenioTestCase):
    """ Systematics strings to be parsed (we check only that they parse
    at all not generating exceptions)
    """

    def test_guess_minimum_encoding(self):
        """textutils - guess_minimum_encoding."""
#        self.assertEqual(guess_minimum_encoding('patata'), ('patata', 'ascii'))
#        self.assertEqual(False, True, "ble")
        # we make sure that this does not cauase any exception !
        pass

class TestDatasetPaperLogic(InvenioTestCase):
    """ Testing the business logic classes
    """

    def test_parse_systematics(self):
        """
        To be filled when it becomes more clear how to treat systematics
        http://hepdata.cedar.ac.uk/view/ins1720
        http://hepdata.cedar.ac.uk/view/ins215359
        """
        pass

    def test_copy_245_fields_correct_caption(self):
        """Test the case when original record contains already some
           instances of 245 field and we want to extend by the HEPDATA
           caption """
        rec_string = """<record>
  <controlfield tag="001">123456</controlfield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">Some caption</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="z">Some ridiculous caption</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">Hepdata caption</subfield>
    <subfield code="9">HEPDATA</subfield>
  </datafield>
  <!--some other fields-->
  <datafield tag="520" ind1="" ind2=" ">
    <subfield code="9">HEPDATA</subfield>
  </datafield>
  <datafield tag="245" ind1="z" ind2=" ">
    <subfield code="z">Some ridiculous caption</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="z">Some other entry not following even the semantics 2</subfield>
    <subfield code="3">ANOTHER</subfield>
  </datafield>
  </record>"""
        rec = bibrecord.create_record(rec_string)[0]
        paper = hepdatautils.Paper.create_from_record(rec)
        self.assertEqual(None, paper.get_diff_marcxml(rec), \
                            "There should not be need of a patch on the same record")
        paper.comment = "azerty"
        diff_xml = paper.get_diff_marcxml(rec)
        self.assertTrue(diff_xml.find(">Some caption") == -1, \
                        "One of existing captions not found")
        self.assertTrue(diff_xml.find(">Some ridiculous caption") == -1, \
                        "One of existing captions not found")
        self.assertTrue(diff_xml.find(">azerty") != -1, \
                        "New caption not found")

    def test_copy_245_fields_add_caption(self):
        """ Test adding a completely new caption"""
        rec_string = """<record>
  <controlfield tag="001">123456</controlfield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">Some caption</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="z">Some ridiculous caption</subfield>
  </datafield>
  <!--some other fields-->
  <datafield tag="520" ind1="" ind2=" ">
    <subfield code="9">HEPDATA</subfield>
  </datafield>
  <datafield tag="245" ind1="z" ind2=" ">
    <subfield code="z">Some ridiculous caption</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="z">Some other entry not following even the semantics 2</subfield>
    <subfield code="3">ANOTHER</subfield>
  </datafield>
  </record>"""
        rec = bibrecord.create_record(rec_string)[0]
        paper = hepdatautils.Paper.create_from_record(rec)
        self.assertEqual(None, paper.get_diff_marcxml(rec), \
                            "There should not be need of a patch on the same record")
        paper.comment = "azerty"
        diff_xml = paper.get_diff_marcxml(rec)
        self.assertTrue(diff_xml.find(">Some caption") == -1, \
                        "One of existing captions not found")
        self.assertTrue(diff_xml.find(">Some ridiculous caption") == -1, \
                        "One of existing captions not found")
        self.assertTrue(diff_xml.find(">azerty") != -1, \
                        "New caption not found")


    def test_copy_245_fields_remove_caption(self):
        """ Test the case when the caption exists but
        it should be removed"""

        rec_string = """<record>
  <controlfield tag="001">123456</controlfield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">Some caption</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="z">Some ridiculous caption</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">Caption to remove</subfield>
    <subfield code="9">HEPDATA</subfield>
  </datafield>

  <!--some other fields-->
  <datafield tag="520" ind1="" ind2=" ">
    <subfield code="9">HEPDATA</subfield>
  </datafield>
  <datafield tag="245" ind1="z" ind2=" ">
    <subfield code="z">Some ridiculous caption</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="z">Some other entry not following even the semantics 2</subfield>
    <subfield code="3">ANOTHER</subfield>
  </datafield>
  </record>"""
        rec = bibrecord.create_record(rec_string)[0]
        paper = hepdatautils.Paper.create_from_record(rec)
        self.assertEqual(None, paper.get_diff_marcxml(rec), \
                            "There should not be need of a patch on the same record")
        paper.comment = "" # empty caption should not be uploaded
        diff_xml = paper.get_diff_marcxml(rec)
        self.assertTrue(diff_xml is None, "Expected empty output")

    def test_paper_logic(self):
        """Test the case when the main record has to be updated.
           Only fields refering to HEPData directly have to be modified,
           which means copying all fields not being directly related"""
        rec_string = """<record>
  <controlfield tag="001">123456</controlfield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="z">Some other entry not following even the semantics</subfield>
    <subfield code="3">ADDITIONAL HEPDATA</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="z">Some other entry not following even the semantics 2</subfield>
    <subfield code="3">ANOTHER</subfield>
  </datafield>

  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="u">http://google.com</subfield>
    <subfield code="y">This is the link text</subfield>

    <subfield code="3">ADDITIONAL HEPDATA</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="u">http://invenio-software.org</subfield>
    <subfield code="y">This is some other completely unrelated field</subfield>
    <subfield code="3">Different type</subfield>
  </datafield>
  <datafield tag="856" ind1=" " ind2=" ">
    <subfield code="u">http://invenio-software.net</subfield>
    <subfield code="y">This should not be copied</subfield>
    <subfield code="3">Different type</subfield>
  </datafield>

  <!-- now fields similar to the one marking existence of HEPDATA -->
  <datafield tag="520" ind1=" " ind2=" ">
    <subfield code="9">SOMETHING</subfield>
  </datafield>

  <!-- Now an incorrect caption -->
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">Some incorrect caption</subfield>
    <subfield code="9">HEPDATA</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">Some other comment</subfield>
    <subfield code="9">SOMETHING ELSE</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="u">Something not following the schema</subfield>
  </datafield>

  <!-- some completely unrelated fields that should not be copied -->

  <datafield tag="764" ind1=" " ind2=" ">
    <subfield code="u">Something not to repeat</subfield>
  </datafield>
  <datafield tag="764" ind1=" " ind2=" ">
    <subfield code="u">Something not to repeat 2</subfield>
  </datafield>
  <datafield tag="200" ind1="C" ind2=" ">
    <subfield code="a">Something not to repeat 3</subfield>
  </datafield>
</record>"""
        rec = bibrecord.create_record(rec_string)[0]
        # generate entries that differ on title, additional data etc...
        paper = hepdatautils.Paper()
        paper.additional_data_links = \
            [{"description": "This is the first dataset", \
              "href": "http://something.com"}, \
             {"description": "This is another description", \
              "href" : "https://invenio-software.org"}, \
             {"description" : "Yet something else", \
              "href" : "http://and.now.for.something.completely.different"}]

        diff_xml = paper.get_diff_marcxml(rec)
        self.assertTrue(not(diff_xml is None),
                        "According to the diffing algorithm, records are the same")

#        print diff_xml

        # test the case of uploading an empty set !

    def test_read_empty_dataset(self):
        """Assure that the case of empty dataset does not cause any problems
        ... this might be the case for example with
        http://hepdata.cedar.ac.uk/view/ins215359"""
        # Trying to generate columns on an empty dataset
        dataset = cPickle.loads("ccopy_reg\n_reconstructor\np1\n(cinvenio.utils.hepdata.api\nDataset\np2\nc__builtin__\nobject\np3\nNtRp4\n(dp5\nS'name'\np6\nS'Table 7'\np7\nsS'column_titles'\np8\n(lp9\nsS'additional_files'\np10\n(lp11\n(lp12\nS'ins1720/d7/plain.txt'\np13\naS'plain text'\np14\naa(lp15\nS'ins1720/d7/aida'\np16\naS'AIDA'\np17\naa(lp18\nS'ins1720/d7/pyroot.py'\np19\naS'PYROOT'\np20\naa(lp21\nS'ins1720/d7/yoda'\np22\naS'YODA'\np23\naa(lp24\nS'ins1720/d7/root'\np25\naS'ROOT'\np26\naa(lp27\nS'ins1720/d7/mpl'\np28\naS'mpl'\np29\naa(lp30\nS'ins1720/d7/jhepwork.py'\np31\naS'jhepwork'\np32\naasS'comments'\np33\nS'<br >Location: F 20<br >Additional systematic error: (RES-DEF(RES=DEL(1232P33)++,BACK=CORRECTED,C=P-WAVE BREIT-WIGNER)//RES-DEF(RES=N(1470P11)+,BACK=CORRECTED,C=P-WAVE BREIT-WIGNER, C=FITTED MASS//RES-DEF(RES=N(1520D13)+,BACK=CORRECTED,C=P-WAVE BREIT-WIGNER, C=FITTED MASS//RES-DEF(RES=N(1688F15)+,BACK=CORRECTED,C=F-WAVE BREIT-WIGNER, C=FITTED MASS)'\np34\nsS'data_qualifiers'\np35\n(lp36\nsS'location'\np37\nS''\nsS'num_columns'\np38\nI2\nsS'position'\np39\nI0\nsS'column_headers'\np40\n(lp41\n(dp42\nS'content'\np43\nS''\nsS'colspan'\np44\nI1\nsa(dp45\ng43\nS'No data is encoded for this table'\np46\nsg44\nI1\nsasS'data'\np47\n(lp48\nsS'additional_data_links'\np49\n(lp50\nsb.")
        dataset.generate_columns()


    def test_generate_columns(self):
        """Test the method generating columns of a given dataset"""
        def generate_columns_longer(ds):
            """ a much longer implemntation of the column generation"""
            from invenio.legacy.bibrecord import record_add_field
            rec = {}
            columns = [[num, "", ""] for num in xrange(ds.num_columns)]
            # (number, header, title)
            cur_col = 0
            for hd in ds.column_headers:
                for i in xrange(hd["colspan"]):
                    columns[cur_col][1] = hd["content"].strip()
                    cur_col += 1
            cur_col = 0
            for ct in ds.column_titles:
                for i in xrange(ct["colspan"]):
                    columns[cur_col][2] = ct["content"].strip()
                    cur_col += 1
            for col in columns:
                subfields = [("n", str(col[0]))]
                if col[2] != "":
                    subfields.append(("t", col[2]))
                if col[1] != "":
                    subfields.append(("d", col[1]))

                record_add_field(rec, "910", subfields = subfields)
            return rec

        ds = Dataset()
        ds.column_headers = [{"content": "header1", "colspan" : 1},
                      {"content": "header2", "colspan" : 3}]

        ds.column_titles = [{"content": "title1", "colspan" : 2},
                            {"content": "title2", "colspan" : 1}]
        ds.num_columns = 6

        self.assertEqual(ds.generate_columns(), generate_columns_longer(ds), \
                             "Incorrectly generated columns")
    def test_write_xml(self):
        """Tests the capability of writing xml files"""
        fname = hepdatautils.write_xml_stream_to_tmpfile(\
            ["<entry1></entry1>", "<entry2></entry2>"], "testing")
        self.assertTrue(os.path.exists(fname), "results file does not exist")
        f = open(fname, "r")
        content = f.read()
        f.close()
        self.assertTrue(content.find("<entry1></entry1>") != -1, \
                        "Can not find required string entry1")
        self.assertTrue(content.find("<entry2></entry2>") != -1, \
                        "Can not find required string entry2")
        self.assertTrue(content.find("<?xml") != -1, \
                        "Can not find required XML structure")


    def test_update_the_same_record(self):
        """Tests parsing Paper from a record and diffing with the same
           hepdata entry.
           """
        rec_string = """<record>
  <controlfield tag="001">123456</controlfield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="z">Some other entry not following even the semantics 2</subfield>
    <subfield code="3">ANOTHER</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="u">http://google.com</subfield>
    <subfield code="y">1 This is the link text</subfield>
    <subfield code="3">ADDITIONAL HEPDATA</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="u">http://invenio-software.org</subfield>
    <subfield code="y">2 This is some other completely unrelated field</subfield>
    <subfield code="3">ADDITIONAL HEPDATA</subfield>
  </datafield>
  <datafield tag="856" ind1=" " ind2=" ">
    <subfield code="u">http://invenio-software.net</subfield>
    <subfield code="y">This should not be copied</subfield>
    <subfield code="3">Different type</subfield>
  </datafield>
  <datafield tag="520" ind1=" " ind2=" ">
    <subfield code="9">HEPDATA</subfield>
  </datafield>
</record>
"""
        rec = bibrecord.create_record(rec_string)[0]
        paper = hepdatautils.Paper.create_from_record(rec)
        diff_xml = paper.get_diff_marcxml(rec)

        self.assertTrue(diff_xml is None,
                        "Expecting empty XML in the case of the same dataset. Produced XML: %s" % (diff_xml, ))

        self.assertEqual(len(paper.additional_data_links), 2,
                         "Incorrect number of recognised additional data links")

        if paper.additional_data_links[0]["description"][0] > \
                paper.additional_data_links[1]["description"][0]:
            l1 = paper.additional_data_links[1]
            l2 = paper.additional_data_links[0]
        else:
            l1 = paper.additional_data_links[0]
            l2 = paper.additional_data_links[1]

        self.assertEqual(l1["description"], "1 This is the link text", "Incorrect first parsed link")
        self.assertEqual(l1["href"], "http://google.com", "Incorrect first parsed link")
        self.assertEqual(l2["description"], "2 This is some other completely unrelated field",
                         "Incorrect second parsed link")
        self.assertEqual(l2["href"], "http://invenio-software.org",
                         "Incorrect second parsed link")


    def test_parse_record(self):
        """Tests building record form the MARC XML"""
        rec_string = """<record>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">This is the caption</subfield>
    <subfield code="9">HEPDATA</subfield>
  </datafield>
  <datafield tag="520" ind1=" " ind2=" ">
    <subfield code="9">HEPDATA</subfield>
  </datafield>
  <datafield tag="710" ind1=" " ind2=" ">
    <subfield code="g">ATLAS</subfield>
  </datafield>
  <datafield tag="786" ind1=" " ind2=" ">
    <subfield code="w">214657</subfield>
    <subfield code="r">arXiv:something</subfield>
    <subfield code="h">F1</subfield>
  </datafield>
  <datafield tag="336" ind1=" " ind2=" ">
    <subfield code="t">DATASET</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">DATA</subfield>
  </datafield>
  <!-- definitions of columns -->
  <datafield tag="911" ind1=" " ind2=" ">
    <subfield code="x">1</subfield>
    <subfield code="y">2</subfield>
  </datafield>

  <datafield tag="910" ind1=" " ind2=" ">
    <subfield code="t">column title</subfield>
    <subfield code="d">column description</subfield>
    <subfield code="n">0</subfield>
  </datafield>

  <datafield tag="910" ind1=" " ind2=" ">
    <subfield code="t">title2</subfield>
    <subfield code="d">column description</subfield>
    <subfield code="n">1</subfield>
  </datafield>

  <datafield tag="910" ind1=" " ind2=" ">
    <subfield code="t">title2</subfield>
    <subfield code="d">description2</subfield>
    <subfield code="n">2</subfield>
  </datafield>

  <!-- encoding data qualifiers -->
  <datafield tag="653" ind1="1" ind2=" ">
    <subfield code="r">1</subfield>
    <subfield code="c">0</subfield>
    <subfield code="c">1</subfield>
  </datafield>
  <datafield tag="653" ind1="1" ind2=" ">
    <subfield code="k">m</subfield>
    <subfield code="v">v</subfield>
    <subfield code="c">2</subfield>
  </datafield>
  <datafield tag="653" ind1="1" ind2=" ">
    <subfield code="k">p</subfield>
    <subfield code="v">q</subfield>
    <subfield code="c">0</subfield>
  </datafield>
  <datafield tag="653" ind1="1" ind2=" ">
    <subfield code="k">w</subfield>
    <subfield code="v">g</subfield>
    <subfield code="c">1</subfield>
    <subfield code="c">2</subfield>
  </datafield>
  <datafield tag="653" ind1="1" ind2=" ">
    <subfield code="r">2</subfield>
    <subfield code="c">0</subfield>
    <subfield code="c">1</subfield>
  </datafield>
  <datafield tag="653" ind1="1" ind2=" ">
    <subfield code="k">z</subfield>
    <subfield code="v">v</subfield>
    <subfield code="c">2</subfield>
  </datafield>
</record>
"""
        rec = bibrecord.create_record(rec_string)
#        print "The record string: %s\n" % (str(rec), )

        ds = Dataset.create_from_record(rec[0], '(l.', 214657, "")
#        print str(ds.data_qualifiers)

        self.assertEqual(3, ds.num_columns, \
                             "Incorrect number of columns has been read")


        # asserting column titles:
        self.assertEqual(2, len(ds.column_headers), "Incorrect number of headers")
        self.assertEqual("column title", ds.column_titles[0]["content"], \
                         "Incorrect content of the first column")
        self.assertEqual(1, ds.column_titles[0]["colspan"], \
                             "Incorrect colspan of the title of first column")
        self.assertEqual("title2", ds.column_titles[1]["content"], \
                             "Incorrect content of the second and third column")
        self.assertEqual(2, ds.column_titles[1]["colspan"], \
                             "Incorrect colspan of the title of second and " + \
                             "third column")

        # asserting on column descriptions

        self.assertEqual(2, len(ds.column_titles), \
                         "Incorrect number of column titles")
        self.assertEqual("column description", ds.column_headers[0]["content"], \
                             "Incorrect description of the first andsecond" + \
                             " column")
        self.assertEqual(2, ds.column_headers[0]["colspan"], \
                             "Incorrect colspan of the description first" + \
                             " and second column")

        self.assertEqual("description2", ds.column_headers[1]["content"], \
                             "Incorrect description of the third column")
        self.assertEqual(1, ds.column_headers[1]["colspan"], \
                             "Incorrect colspan of the description thirdcolumn")

        self.assertEqual(3, len(ds.data_qualifiers), \
                             "Incorrect number of detected dscriptor rows")

        existing_qual = []
        for q_line in ds.data_qualifiers:
            l_pos = 0
            for q in q_line:
                existing_qual.append((l_pos, q))
                l_pos += 1

        self.assertTrue((0, {"content": "RE : 1", "colspan" : 2 }) in \
                            existing_qual)
        self.assertTrue((1, {"content": "m : v", "colspan" : 1 }) in \
                            existing_qual)
        self.assertTrue((0, {"content": "p : q", "colspan" : 1 }) in \
                            existing_qual)
        self.assertTrue((1, {"content": "w : g", "colspan" : 2 }) in \
                            existing_qual)
        self.assertTrue((0, {"content": "RE : 2", "colspan" : 2 }) in \
                            existing_qual)
        self.assertTrue((1, {"content": "z : v", "colspan" : 1 }) in \
                            existing_qual)


        # now testing the comparison function ... on the same dataset
        ds2 = Dataset.create_from_record(rec[0], '(l.', 214657, "")
#        print str(ds.get_diff_marcxml(rec[0], None))
#        print str(ds.get_diff_marcxml({}, None))


TEST_SUITE = make_test_suite(TestParsingSystematics, TestDatasetPaperLogic)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

