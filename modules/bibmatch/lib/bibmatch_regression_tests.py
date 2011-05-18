# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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

# pylint: disable=E1102

"""Unit tests for bibmatch."""

__revision__ = "$Id$"

from invenio.config import CFG_SITE_RECORD
from invenio.testutils import make_test_suite, run_test_suite
from invenio.bibrecord import create_records, record_has_field
from invenio.bibmatch_engine import match_records, transform_input_to_marcxml, \
                                    Querystring
import unittest

class BibMatchTest(unittest.TestCase):
    """Test functions to check the functionality of bibmatch."""

    def setUp(self):
        """setting up helper variables for tests"""
        self.textmarc = """
000000020 001__ 20
000000020 041__ $$aeng
000000020 088__ $$aJYFL-RR-82-7
000000020 100__ $$aArje, J$$uUniversity of Jyvaskyla
000000020 245__ $$aCharge creation and reset mechanisms in an ion guide isotope separator (IGIS)
000000020 260__ $$aJyvaskyla$$bFinland Univ. Dept. Phys.$$cJul 1982
000000020 300__ $$a18 p
000000020 65017 $$2SzGeCERN$$aDetectors and Experimental Techniques
000000020 909C0 $$y1982
000000020 909C0 $$b19
000000020 909C1 $$uJyväsklä Univ.
000000020 909C1 $$c1990-01-28$$l50$$m2002-01-04$$oBATCH
000000020 909CS $$sn$$w198238n
000000020 980__ $$aREPORT

000000019 001__ 19
000000019 041__ $$aeng
000000019 088__ $$aSTAN-CS-81-898-MF
000000019 100__ $$aWhang, K$$uStanford University
000000019 245__ $$aSeparability as a physical database design methodology
000000019 260__ $$aStanford, CA$$bStanford Univ. Comput. Sci. Dept.$$cOct 1981
000000019 300__ $$a60 p
000000019 65017 $$2SzGeCERN$$aComputing and Computers
000000019 700__ $$aWiederhold, G
000000019 700__ $$aSagalowicz, D
000000019 909C0 $$y1981
000000019 909C0 $$b19
000000019 909C1 $$uStanford Univ.
000000019 909C1 $$c1990-01-28$$l50$$m2002-01-04$$oBATCH
000000019 909CS $$sn$$w198238n
000000019 980__ $$aREPORT
        """
        #ambig match:  Changed Atlantis (Timaeus) ->Atlantis
        self.recxml1 = """
<?xml version="1.0" encoding="UTF-8"?>
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record>
  <controlfield tag="001">101</controlfield>
  <datafield tag="037" ind1=" " ind2=" ">
    <subfield code="a">BUL-NEWS-2009-003</subfield>
  </datafield>
  <datafield tag="041" ind1=" " ind2=" ">
    <subfield code="a">eng</subfield>
  </datafield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Plato</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">Atlantis (Timaeus)</subfield>
  </datafield>
  <datafield tag="520" ind1=" " ind2=" ">
    <subfield code="b">&lt;!--HTML-->&lt;p class="articleHeader">This great island lay over against the Pillars of Heracles, in extent greater than Libya and Asia put together, and was the passage to other islands and to a great ocean of which the Mediterranean sea was only the harbour; and within the Pillars the empire of Atlantis reached in Europe to Tyrrhenia and in Libya to Egypt.&lt;/p>&lt;p>This mighty power was arrayed against Egypt and Hellas and all the countries&lt;/p>&lt;div class="phrwithcaption">&lt;div class="imageScale">&lt;img src="http://invenio-software.org/download/invenio-demo-site-files/icon-journal_Athanasius_Kircher_Atlantis_image.gif" alt="" />&lt;/div>&lt;p>Representation of Atlantis by Athanasius Kircher (1669)&lt;/p>&lt;/div>bordering on the Mediterranean. Then your city did bravely, and won renown over the whole earth. For at the peril of her own existence, and when the other Hellenes had deserted her, she repelled the invader, and of her own accord gave liberty to all the nations within the Pillars. A little while afterwards there were great earthquakes and floods, and your warrior race all sank into the earth; and the great island of Atlantis also disappeared in the sea. This is the explanation of the shallows which are found in that part of the Atlantic ocean. &lt;p>&lt;/p>(Excerpt from TIMAEUS, By Plato, translated By Jowett, Benjamin)&lt;br /></subfield>
  </datafield>
  <datafield tag="590" ind1=" " ind2=" ">
    <subfield code="b">&lt;!--HTML-->&lt;br /></subfield>
  </datafield>
  <datafield tag="773" ind1=" " ind2=" ">
    <subfield code="c">1</subfield>
    <subfield code="n">02/2009</subfield>
    <subfield code="t">Atlantis Times</subfield>
  </datafield>
  <datafield tag="773" ind1=" " ind2=" ">
    <subfield code="c">1</subfield>
    <subfield code="n">03/2009</subfield>
    <subfield code="t">Atlantis Times</subfield>
  </datafield>
  <datafield tag="773" ind1=" " ind2=" ">
    <subfield code="c">1</subfield>
    <subfield code="n">04/2009</subfield>
    <subfield code="t">Atlantis Times</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="u">http://localhost/record/101/files/journal_Athanasius_Kircher_Atlantis_image.gif</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="u">http://localhost/record/101/files/journal_Athanasius_Kircher_Atlantis_image.gif?subformat=icon</subfield>
    <subfield code="x">icon</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">ATLANTISTIMESNEWS</subfield>
  </datafield>
</record>
</collection>
"""
        #this is not in the collection
        self.recxml2 = """
<?xml version="1.0" encoding="UTF-8"?>
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record>
  <controlfield tag="001">9124</controlfield>
  <datafield tag="970" ind1=" " ind2=" ">
    <subfield code="a">SPIRES-5726484</subfield>
  </datafield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Schulz, Michael B.</subfield>
    <subfield code="u">Caltech</subfield>
  </datafield>
  <datafield tag="773" ind1=" " ind2=" ">
    <subfield code="w">C02/06/25.2</subfield>
    <subfield code="t">Prepared for</subfield>
    <subfield code="c">477-480</subfield>
  </datafield>
  <datafield tag="650" ind1="1" ind2="7">
    <subfield code="a">Theory-HEP</subfield>
    <subfield code="2">INSPIRE</subfield>
  </datafield>
  <datafield tag="690" ind1="C" ind2=" ">
    <subfield code="a">Conference Paper</subfield>
    <subfield code="2">INSPIRE</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="s">Phys.Rev.,D61,022001</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="r">hep-th/9601083</subfield>
    <subfield code="s">Phys.Rev.,D53,4129</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="r">hep-th/0201029</subfield>
    <subfield code="s">Phys.Rev.,D65,126009</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="r">hep-th/0105097</subfield>
    <subfield code="s">Phys.Rev.,D66,106006</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="r">hep-th/9906070</subfield>
    <subfield code="s">Nucl.Phys.,B584,69</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="r">hep-th/0211182</subfield>
    <subfield code="s">JHEP,0303,061</subfield>
  </datafield>
  <datafield tag="520" ind1=" " ind2=" ">
    <subfield code="a">A brief overview of hep-th/0201028 prepared for NATO Advanced Study Institute and EC Summer School on Progress in String, Field and Particle Theory, Cargese, Corsica, France, 25 June - 11 July 2002.</subfield>
    <subfield code="9">arXiv</subfield>
  </datafield>
  <datafield tag="037" ind1=" " ind2=" ">
    <subfield code="a">arXiv:0810.5197</subfield>
    <subfield code="9">arXiv</subfield>
    <subfield code="c">hep-th</subfield>
  </datafield>
  <datafield tag="035" ind1=" " ind2=" ">
    <subfield code="z">oai:arXiv.org:0810.5197</subfield>
    <subfield code="9">arXiv</subfield>
  </datafield>
  <datafield tag="037" ind1=" " ind2=" ">
    <subfield code="a">CALT-68-2441</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">Moduli stabilization from fluxes</subfield>
  </datafield>
  <datafield tag="300" ind1=" " ind2=" ">
    <subfield code="a">5</subfield>
  </datafield>
  <datafield tag="695" ind1=" " ind2=" ">
    <subfield code="a">talk: Cargese 2002/06/25</subfield>
    <subfield code="2">INSPIRE</subfield>
  </datafield>
  <datafield tag="695" ind1=" " ind2=" ">
    <subfield code="a">string model</subfield>
    <subfield code="2">INSPIRE</subfield>
  </datafield>
  <datafield tag="695" ind1=" " ind2=" ">
    <subfield code="a">compactification</subfield>
    <subfield code="2">INSPIRE</subfield>
  </datafield>
  <datafield tag="695" ind1=" " ind2=" ">
    <subfield code="a">moduli: stability</subfield>
    <subfield code="2">INSPIRE</subfield>
  </datafield>
  <datafield tag="695" ind1=" " ind2=" ">
    <subfield code="a">orientifold</subfield>
    <subfield code="2">INSPIRE</subfield>
  </datafield>
  <datafield tag="695" ind1=" " ind2=" ">
    <subfield code="a">membrane model: D-brane</subfield>
    <subfield code="2">INSPIRE</subfield>
  </datafield>
  <datafield tag="695" ind1=" " ind2=" ">
    <subfield code="a">flux</subfield>
    <subfield code="2">INSPIRE</subfield>
  </datafield>
  <datafield tag="695" ind1=" " ind2=" ">
    <subfield code="a">supersymmetry</subfield>
    <subfield code="2">INSPIRE</subfield>
  </datafield>
  <datafield tag="035" ind1=" " ind2=" ">
    <subfield code="z">D04-00603</subfield>
    <subfield code="9">DESY</subfield>
  </datafield>
  <datafield tag="035" ind1=" " ind2=" ">
    <subfield code="z">Schulz:2002eh</subfield>
    <subfield code="9">SPIRESTeX</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">Conference</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">arXiv</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">Citeable</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">CORE</subfield>
  </datafield>
  <datafield tag="269" ind1=" " ind2=" ">
    <subfield code="c">2008-10</subfield>
  </datafield>
  <datafield tag="961" ind1=" " ind2=" ">
    <subfield code="x">2003-11-17</subfield>
  </datafield>
  <datafield tag="961" ind1=" " ind2=" ">
    <subfield code="c">2009-12-11</subfield>
  </datafield>
</record>
</collection>
"""
        #exact match: using all titles to disambiguate
        self.recxml3 = """
<?xml version="1.0" encoding="UTF-8"?>
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record>
  <datafield tag="020" ind1=" " ind2=" ">
    <subfield code="a">2225350574</subfield>
  </datafield>
  <datafield tag="041" ind1=" " ind2=" ">
    <subfield code="a">fre</subfield>
  </datafield>
  <datafield tag="080" ind1=" " ind2=" ">
    <subfield code="a">518.5:62.01</subfield>
  </datafield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Dasse, Michel</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">Analyse informatique</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="n">t.2</subfield>
    <subfield code="p">L'accomplissement</subfield>
  </datafield>
  <datafield tag="260" ind1=" " ind2=" ">
    <subfield code="a">Paris</subfield>
    <subfield code="b">Masson</subfield>
    <subfield code="c">1972</subfield>
  </datafield>
  <datafield tag="490" ind1=" " ind2=" ">
    <subfield code="a">Informatique</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="0">
    <subfield code="y">1972</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="0">
    <subfield code="b">21</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="1">
    <subfield code="c">1990-01-27</subfield>
    <subfield code="l">00</subfield>
    <subfield code="m">2002-04-12</subfield>
    <subfield code="o">BATCH</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="S">
    <subfield code="s">m</subfield>
    <subfield code="w">198604</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">BOOK</subfield>
  </datafield>
</record>

</collection>
"""
        #fuzzy matched: quasi-normal -> quasi normal + missing word in title
        self.recxml4 = """
<?xml version="1.0" encoding="UTF-8"?>
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record>
  <controlfield tag="001">92</controlfield>
  <controlfield tag="003">SzGeCERN</controlfield>
  <controlfield tag="005">20060616163757.0</controlfield>
  <datafield tag="037" ind1=" " ind2=" ">
    <subfield code="a">hep-th/0606096</subfield>
  </datafield>
  <datafield tag="041" ind1=" " ind2=" ">
    <subfield code="a">eng</subfield>
  </datafield>
  <datafield tag="088" ind1=" " ind2=" ">
    <subfield code="a">UTHET-2006-05-01</subfield>
  </datafield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Koutsoumbas, G</subfield>
    <subfield code="u">National Technical University of Athens</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">Quasi normal Modes of Electromagnetic Perturbations of Four-Dimensional Topological Black Holes</subfield>
  </datafield>
  <datafield tag="260" ind1=" " ind2=" ">
    <subfield code="c">2006</subfield>
  </datafield>
  <datafield tag="269" ind1=" " ind2=" ">
    <subfield code="c">10 Jun 2006</subfield>
  </datafield>
  <datafield tag="300" ind1=" " ind2=" ">
    <subfield code="a">17 p</subfield>
  </datafield>
  <datafield tag="520" ind1=" " ind2=" ">
    <subfield code="a">We study the perturbative behaviour of topological black holes with scalar hair. We calculate both analytically and numerically the quasi-normal modes of the electromagnetic perturbations. In the case of small black holes we find clear evidence of a second-order phase transition of a topological black hole to a hairy configuration. We also find evidence of a second-order phase transition of the AdS vacuum solution to a topological black hole.</subfield>
  </datafield>
  <datafield tag="650" ind1="1" ind2="7">
    <subfield code="2">SzGeCERN</subfield>
    <subfield code="a">Particle Physics - Theory</subfield>
  </datafield>
  <datafield tag="690" ind1="C" ind2=" ">
    <subfield code="a">ARTICLE</subfield>
  </datafield>
  <datafield tag="695" ind1=" " ind2=" ">
    <subfield code="9">LANL EDS</subfield>
    <subfield code="a">High Energy Physics - Theory</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Musiri, S</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Papantonopoulos, E</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Siopsis, G</subfield>
  </datafield>
  <datafield tag="720" ind1=" " ind2=" ">
    <subfield code="a">Koutsoumbas, George</subfield>
  </datafield>
  <datafield tag="720" ind1=" " ind2=" ">
    <subfield code="a">Musiri, Suphot</subfield>
  </datafield>
  <datafield tag="720" ind1=" " ind2=" ">
    <subfield code="a">Papantonopoulos, Eleftherios</subfield>
  </datafield>
  <datafield tag="720" ind1=" " ind2=" ">
    <subfield code="a">Siopsis, George</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="u">http://137.138.33.172/%s/92/files/0606096.pdf</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="4">
    <subfield code="c">006</subfield>
    <subfield code="p">J. High Energy Phys.</subfield>
    <subfield code="v">10</subfield>
    <subfield code="y">2006</subfield>
  </datafield>
  <datafield tag="916" ind1=" " ind2=" ">
    <subfield code="s">n</subfield>
    <subfield code="w">200624</subfield>
  </datafield>
  <datafield tag="960" ind1=" " ind2=" ">
    <subfield code="a">13</subfield>
  </datafield>
  <datafield tag="961" ind1=" " ind2=" ">
    <subfield code="c">20070425</subfield>
    <subfield code="h">1021</subfield>
    <subfield code="l">CER01</subfield>
    <subfield code="x">20060613</subfield>
  </datafield>
  <datafield tag="963" ind1=" " ind2=" ">
    <subfield code="a">PUBLIC</subfield>
  </datafield>
  <datafield tag="970" ind1=" " ind2=" ">
    <subfield code="a">002628325CER</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">ARTICLE</subfield>
  </datafield>
</record>

</collection>
""" % CFG_SITE_RECORD
        return


    def test_check_existing(self):
        """bibmatch - check existing record"""
        records = create_records(self.recxml3)
        [dummy1, matchedrecs, dummy2, dummy3] = match_records(records)
        self.assertEqual(1, len(matchedrecs))

    def test_check_new(self):
        """bibmatch - check a new record"""
        records = create_records(self.recxml2)
        [newrecs, dummy1, dummy2, dummy3] = match_records(records)
        self.assertEqual(1, len(newrecs))

    def test_check_ambiguous(self):
        """bibmatch - check an ambiguous record"""
        records = create_records(self.recxml1)
        [dummy1, dummy2, ambigrecs, dummy3] = match_records(records, qrystrs=[("", "[100__a]")])
        self.assertEqual(1, len(ambigrecs))

    def test_check_fuzzy(self):
        """bibmatch - check fuzzily matched record"""
        records = create_records(self.recxml4)
        [dummy1, dummy2, dummy3, fuzzyrecs] = match_records(records)
        self.assertEqual(1, len(fuzzyrecs))

    def test_check_remote(self):
        """bibmatch - check remote match (Invenio demo site)"""
        records = create_records(self.recxml3)
        [dummy1, matchedrecs, dummy3, dummy4] = match_records(records, server_url="http://invenio-demo.cern.ch")
        self.assertEqual(1, len(matchedrecs))

    def test_check_textmarc(self):
        """bibmatch - check textmarc as input"""
        marcxml = transform_input_to_marcxml("", self.textmarc)
        records = create_records(marcxml)
        [dummy1, matchedrecs, dummy3, dummy4] = match_records(records, server_url="http://invenio-demo.cern.ch")
        self.assertEqual(2, len(matchedrecs))

    def test_check_altered(self):
        """bibmatch - check altered match"""
        records = create_records(self.recxml3)
        self.assertTrue(not record_has_field(records[0][0], '001'))
        [dummy1, matchedrecs, dummy3, dummy4] = match_records(records, modify=1)
        self.assertTrue(record_has_field(matchedrecs[0][0], '001'))

    def test_check_qrystr(self):
        """bibmatch - check querystrings"""
        operator = "and"
        qrystr_old = "title||author"
        qrystr_new = "[title] %s [author]" % (operator,)
        querystring = Querystring(operator)
        records = create_records(self.recxml3)
        old_query = querystring.create_query(records[0], qrystr_old)
        new_query = querystring.create_query(records[0], qrystr_new)
        self.assertEqual(old_query, new_query)

    def test_check_completeness(self):
        """bibmatch - check query completeness"""
        records = create_records(self.recxml4)
        [dummy1, dummy2, ambigrecs, dummy3] = match_records(records, qrystrs=[("", "[088__a] [035__a]")])
        self.assertEqual(1, len(ambigrecs))

    def test_check_collection(self):
        """bibmatch - check collection"""
        records = create_records(self.recxml3)
        [nomatchrecs, dummy1, dummy2, dummy3] = match_records(records, collections=["Articles"])
        self.assertEqual(1, len(nomatchrecs))
        [dummy1, matchedrecs, dummy2, dummy3] = match_records(records, collections=["Books"])
        self.assertEqual(1, len(matchedrecs))

TEST_SUITE = make_test_suite(BibMatchTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
