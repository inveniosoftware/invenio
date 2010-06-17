# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002-2010 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

# pylint: disable-msg=E1102

"""Unit tests for bibmatch."""

__revision__ = "$Id$"

from invenio.testutils import make_test_suite, run_test_suite, \
                              test_web_page_content, merge_error_messages
from invenio.bibrecord import create_records
from invenio.bibmatch_engine import match_records
import unittest

class BibMatchTest(unittest.TestCase):
    """Test functions to check the functionality of bibmatch."""

    def setUp(self):
        """setting up helper variables for tests"""
        #this exists in the DB, just some bibliography removed.
        self.recxml1 = """
  <record>
    <controlfield tag="003">SzGeCERN</controlfield>
    <datafield tag="035" ind1=" " ind2=" ">
      <subfield code="a">2341644CERCER</subfield>
    </datafield>
    <datafield tag="035" ind1=" " ind2=" ">
      <subfield code="9">SLAC</subfield>
      <subfield code="a">5208424</subfield>
    </datafield>
    <datafield tag="037" ind1=" " ind2=" ">
      <subfield code="a">hep-th/0209226</subfield>
    </datafield>
    <datafield tag="041" ind1=" " ind2=" ">
      <subfield code="a">eng</subfield>
    </datafield>
    <datafield tag="088" ind1=" " ind2=" ">
      <subfield code="a">PUTP-2002-48</subfield>
    </datafield>
    <datafield tag="088" ind1=" " ind2=" ">
      <subfield code="a">SLAC-PUB-9504</subfield>
    </datafield>
    <datafield tag="088" ind1=" " ind2=" ">
      <subfield code="a">SU-ITP-2002-36</subfield>
    </datafield>
    <datafield tag="100" ind1=" " ind2=" ">
      <subfield code="a">Adams, A</subfield>
      <subfield code="u">Stanford University</subfield>
    </datafield>
    <datafield tag="245" ind1=" " ind2=" ">
      <subfield code="a">Decapitating Tadpoles</subfield>
    </datafield>
    <datafield tag="260" ind1=" " ind2=" ">
      <subfield code="c">2002</subfield>
    </datafield>
    <datafield tag="269" ind1=" " ind2=" ">
      <subfield code="a">Beijing</subfield>
      <subfield code="b">Beijing Univ. Dept. Phys.</subfield>
      <subfield code="c">26 Sep 2002</subfield>
    </datafield>
    <datafield tag="300" ind1=" " ind2=" ">
      <subfield code="a">31 p</subfield>
    </datafield>
    <datafield tag="520" ind1=" " ind2=" ">
      <subfield code="a">We argue that perturbative quantum field theory and string theory can be consistently modified in the infrared to eliminate, in a radiatively stable manner, tadpole instabilities that arise after supersymmetry breaking. This is achieved by deforming the propagators of classically massless scalar fields and the graviton so as to cancel the contribution of their zero modes. In string theory, this modification of propagators is accomplished by perturbatively deforming the world-sheet action with bi-local operators similar to those that arise in double-trace deformations of AdS/CFT. This results in a perturbatively finite and unitary S-matrix (in the case of string theory, this claim depends on standard assumptions about unitarity in covariant string diagrammatics). The S-matrix is parameterized by arbitrary scalar VEVs, which exacerbates the vacuum degeneracy problem. However, for generic values of these parameters, quantum effects produce masses for the nonzero modes of the scalars, lifting the fluctuating components of the moduli.</subfield>
    </datafield>
    <datafield tag="595" ind1=" " ind2=" ">
      <subfield code="a">LANL EDS</subfield>
    </datafield>
    <datafield tag="650" ind1="1" ind2="7">
      <subfield code="2">SzGeCERN</subfield>
      <subfield code="a">Particle Physics - Theory</subfield>
    </datafield>
    <datafield tag="690" ind1="C" ind2=" ">
      <subfield code="a">PREPRINT</subfield>
    </datafield>
    <datafield tag="695" ind1=" " ind2=" ">
      <subfield code="9">LANL EDS</subfield>
      <subfield code="a">High Energy Physics - Theory</subfield>
    </datafield>
    <datafield tag="700" ind1=" " ind2=" ">
      <subfield code="a">McGreevy, J</subfield>
    </datafield>
    <datafield tag="700" ind1=" " ind2=" ">
      <subfield code="a">Silverstein, E</subfield>
    </datafield>
    <datafield tag="720" ind1=" " ind2=" ">
      <subfield code="a">Adams, Allan</subfield>
    </datafield>
    <datafield tag="720" ind1=" " ind2=" ">
      <subfield code="a">Greevy, John Mc</subfield>
    </datafield>
    <datafield tag="720" ind1=" " ind2=" ">
      <subfield code="a">Silverstein, Eva</subfield>
    </datafield>
    <datafield tag="FFT" ind1=" " ind2=" ">
      <subfield code="a">http://cdsware.cern.ch/download/invenio-demo-site-files/0209226.pdf</subfield>
    </datafield>
    <datafield tag="FFT" ind1=" " ind2=" ">
      <subfield code="a">http://cdsware.cern.ch/download/invenio-demo-site-files/0209226.ps.gz</subfield>
    </datafield>
    <datafield tag="859" ind1=" " ind2=" ">
      <subfield code="f">evas@slac.stanford.edu</subfield>
    </datafield>
    <datafield tag="916" ind1=" " ind2=" ">
      <subfield code="s">n</subfield>
      <subfield code="w">200239</subfield>
    </datafield>
    <datafield tag="960" ind1=" " ind2=" ">
      <subfield code="a">11</subfield>
    </datafield>
    <datafield tag="961" ind1=" " ind2=" ">
      <subfield code="c">20060218</subfield>
      <subfield code="h">0013</subfield>
      <subfield code="l">CER01</subfield>
      <subfield code="x">20020927</subfield>
    </datafield>
    <datafield tag="963" ind1=" " ind2=" ">
      <subfield code="a">PUBLIC</subfield>
    </datafield>
    <datafield tag="970" ind1=" " ind2=" ">
      <subfield code="a">002341644CER</subfield>
    </datafield>
    <datafield tag="980" ind1=" " ind2=" ">
      <subfield code="a">PREPRINT</subfield>
    </datafield>
  </record>
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
        #ambig match since there are 2 of these
        self.recxml3 = """
<?xml version="1.0" encoding="UTF-8"?>
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record>
  <controlfield tag="001">26</controlfield>
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
        #missing word in title
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
    <subfield code="a">Quasi-normal Modes of Electromagnetic Perturbations of Four-Dimensional Topological Black Holes</subfield>
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
    <subfield code="u">http://137.138.33.172/record/92/files/0606096.pdf</subfield>
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
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[1]</subfield>
    <subfield code="m">K. D. Kokkotas and B. G. Schmidt,</subfield>
    <subfield code="s">Living Rev. Relativ. 2 (1999) 2</subfield>
    <subfield code="r">gr-qc/9909058</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[2]</subfield>
    <subfield code="m">H.-P. Nollert,</subfield>
    <subfield code="s">Class. Quantum Gravity 16 (1999) R159</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[3]</subfield>
    <subfield code="m">J. S. F. Chan and R. B. Mann,</subfield>
    <subfield code="s">Phys. Rev. D 55 (1997) 7546</subfield>
    <subfield code="r">gr-qc/9612026</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[3]</subfield>
    <subfield code="s">Phys. Rev. D 59 (1999) 064025</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[4]</subfield>
    <subfield code="m">G. T. Horowitz and V. E. Hubeny,</subfield>
    <subfield code="s">Phys. Rev. D 62 (2000) 024027</subfield>
    <subfield code="r">hep-th/9909056</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[5]</subfield>
    <subfield code="m">V. Cardoso and J. P. S. Lemos,</subfield>
    <subfield code="s">Phys. Rev. D 64 (2001) 084017</subfield>
    <subfield code="r">gr-qc/0105103</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[6]</subfield>
    <subfield code="m">B. Wang, C. Y. Lin and E. Abdalla,</subfield>
    <subfield code="s">Phys. Lett. B 481 (2000) 79</subfield>
    <subfield code="r">hep-th/0003295</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[7]</subfield>
    <subfield code="m">E. Berti and K. D. Kokkotas,</subfield>
    <subfield code="s">Phys. Rev. D 67 (2003) 064020</subfield>
    <subfield code="r">gr-qc/0301052</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[8]</subfield>
    <subfield code="m">F. Mellor and I. Moss,</subfield>
    <subfield code="s">Phys. Rev. D 41 (1990) 403</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[9]</subfield>
    <subfield code="m">C. Martinez and J. Zanelli,</subfield>
    <subfield code="s">Phys. Rev. D 54 (1996) 3830</subfield>
    <subfield code="r">gr-qc/9604021</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[10]</subfield>
    <subfield code="m">M. Henneaux, C. Martinez, R. Troncoso and J. Zanelli,</subfield>
    <subfield code="s">Phys. Rev. D 65 (2002) 104007</subfield>
    <subfield code="r">hep-th/0201170</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[11]</subfield>
    <subfield code="m">C. Martinez, R. Troncoso and J. Zanelli,</subfield>
    <subfield code="s">Phys. Rev. D 67 (2003) 024008</subfield>
    <subfield code="r">hep-th/0205319</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[12]</subfield>
    <subfield code="m">N. Bocharova, K. Bronnikov and V. Melnikov, Vestn. Mosk. Univ. Fizika</subfield>
    <subfield code="s">Astronomy 6 (1970) 706</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[12]</subfield>
    <subfield code="m">J. D. Bekenstein,</subfield>
    <subfield code="s">Ann. Phys. 82 (1974) 535</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[12]</subfield>
    <subfield code="s">Ann. Phys. 91 (1975) 75</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[13]</subfield>
    <subfield code="m">T. Torii, K. Maeda and M. Narita,</subfield>
    <subfield code="s">Phys. Rev. D 64 (2001) 044007</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[14]</subfield>
    <subfield code="m">E. Winstanley,</subfield>
    <subfield code="s">Found. Phys. 33 (2003) 111</subfield>
    <subfield code="r">gr-qc/0205092</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[15]</subfield>
    <subfield code="m">T. Hertog and K. Maeda,</subfield>
    <subfield code="s">J. High Energy Phys. 0407 (2004) 051</subfield>
    <subfield code="r">hep-th/0404261</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[16]</subfield>
    <subfield code="m">J. P. S. Lemos,</subfield>
    <subfield code="s">Phys. Lett. B 353 (1995) 46</subfield>
    <subfield code="r">gr-qc/9404041</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[17]</subfield>
    <subfield code="m">R. B. Mann,</subfield>
    <subfield code="s">Class. Quantum Gravity 14 (1997) L109</subfield>
    <subfield code="r">gr-qc/9607071</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[17]</subfield>
    <subfield code="m">R. B. Mann,</subfield>
    <subfield code="s">Nucl. Phys. B 516 (1998) 357</subfield>
    <subfield code="r">hep-th/9705223</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[18]</subfield>
    <subfield code="m">L. Vanzo,</subfield>
    <subfield code="s">Phys. Rev. D 56 (1997) 6475</subfield>
    <subfield code="r">gr-qc/9705004</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[19]</subfield>
    <subfield code="m">D. R. Brill, J. Louko and P. Peldan,</subfield>
    <subfield code="s">Phys. Rev. D 56 (1997) 3600</subfield>
    <subfield code="r">gr-qc/9705012</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[20]</subfield>
    <subfield code="m">D. Birmingham,</subfield>
    <subfield code="s">Class. Quantum Gravity 16 (1999) 1197</subfield>
    <subfield code="r">hep-th/9808032</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[21]</subfield>
    <subfield code="m">R. G. Cai and K. S. Soh,</subfield>
    <subfield code="s">Phys. Rev. D 59 (1999) 044013</subfield>
    <subfield code="r">gr-qc/9808067</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[22]</subfield>
    <subfield code="s">Phys.Rev. D65 (2002) 084006</subfield>
    <subfield code="m">B. Wang, E. Abdalla and R. B. Mann, [arXiv</subfield>
    <subfield code="r">hep-th/0107243</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[23]</subfield>
    <subfield code="s">Phys.Rev. D65 (2002) 084006</subfield>
    <subfield code="m">R. B. Mann, [arXiv</subfield>
    <subfield code="r">gr-qc/9709039</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[24]</subfield>
    <subfield code="m">J. Crisostomo, R. Troncoso and J. Zanelli,</subfield>
    <subfield code="s">Phys. Rev. D 62 (2000) 084013</subfield>
    <subfield code="r">hep-th/0003271</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[25]</subfield>
    <subfield code="m">R. Aros, R. Troncoso and J. Zanelli,</subfield>
    <subfield code="s">Phys. Rev. D 63 (2001) 084015</subfield>
    <subfield code="r">hep-th/0011097</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[26]</subfield>
    <subfield code="m">R. G. Cai, Y. S. Myung and Y. Z. Zhang,</subfield>
    <subfield code="s">Phys. Rev. D 65 (2002) 084019</subfield>
    <subfield code="r">hep-th/0110234</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[27]</subfield>
    <subfield code="m">M. H. Dehghani,</subfield>
    <subfield code="s">Phys. Rev. D 70 (2004) 064019</subfield>
    <subfield code="r">hep-th/0405206</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[28]</subfield>
    <subfield code="m">C. Martinez, R. Troncoso and J. Zanelli,</subfield>
    <subfield code="s">Phys. Rev. D 70 (2004) 084035</subfield>
    <subfield code="r">hep-th/0406111</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[29]</subfield>
    <subfield code="s">Phys.Rev. D74 (2006) 044028</subfield>
    <subfield code="m">C. Martinez, J. P. Staforelli and R. Troncoso, [arXiv</subfield>
    <subfield code="r">hep-th/0512022</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[29]</subfield>
    <subfield code="m">C. Martinez and R. Troncoso, [arXiv</subfield>
    <subfield code="s">Phys.Rev. D74 (2006) 064007</subfield>
    <subfield code="r">hep-th/0606130</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[30]</subfield>
    <subfield code="m">E. Winstanley,</subfield>
    <subfield code="s">Class. Quantum Gravity 22 (2005) 2233</subfield>
    <subfield code="r">gr-qc/0501096</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[30]</subfield>
    <subfield code="m">E. Radu and E. Win-stanley,</subfield>
    <subfield code="s">Phys. Rev. D 72 (2005) 024017</subfield>
    <subfield code="r">gr-qc/0503095</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[30]</subfield>
    <subfield code="m">A. M. Barlow, D. Doherty and E. Winstanley,</subfield>
    <subfield code="s">Phys. Rev. D 72 (2005) 024008</subfield>
    <subfield code="r">gr-qc/0504087</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[31]</subfield>
    <subfield code="m">I. Papadimitriou, [arXiv</subfield>
    <subfield code="s">JHEP 0702 (2007) 008</subfield>
    <subfield code="r">hep-th/0606038</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[32]</subfield>
    <subfield code="m">P. Breitenlohner and D. Z. Freedman,</subfield>
    <subfield code="s">Phys. Lett. B 115 (1982) 197</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[32]</subfield>
    <subfield code="s">Ann. Phys. 144 (1982) 249</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[33]</subfield>
    <subfield code="m">L. Mezincescu and P. K. Townsend,</subfield>
    <subfield code="s">Ann. Phys. 160 (1985) 406</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[34]</subfield>
    <subfield code="m">V. Cardoso, J. Natario and R. Schiappa,</subfield>
    <subfield code="s">J. Math. Phys. 45 (2004) 4698</subfield>
    <subfield code="r">hep-th/0403132</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[35]</subfield>
    <subfield code="m">J. Natario and R. Schiappa,</subfield>
    <subfield code="s">Adv. Theor. Math. Phys. 8 (2004) 1001</subfield>
    <subfield code="r">hep-th/0411267</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[36]</subfield>
    <subfield code="m">S. Musiri, S. Ness and G. Siopsis,</subfield>
    <subfield code="s">Phys. Rev. D 73 (2006) 064001</subfield>
    <subfield code="r">hep-th/0511113</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[37]</subfield>
    <subfield code="m">L. Motl and A. Neitzke,</subfield>
    <subfield code="s">Adv. Theor. Math. Phys. 7 (2003) 307</subfield>
    <subfield code="r">hep-th/0301173</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[38]</subfield>
    <subfield code="m">Astron. J. M. Medved, D. Martin and M. Visser,</subfield>
    <subfield code="s">Class. Quantum Gravity 21 (2004) 2393</subfield>
    <subfield code="r">gr-qc/0310097</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[39]</subfield>
    <subfield code="m">W.-H. Press, S. A. Teukolsky, W. T. Vetterling and B. P. Flannery in Numerical Recipies (Cambridge University Press, Cambridge, England, 1992).</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="o">[40]</subfield>
    <subfield code="m">G. Koutsoumbas, S. Musiri, E. Papantonopoulos and G. Siopsis, in preparation.</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="6">
    <subfield code="a">CDS Invenio/0.92.0.20070116 refextract/0.92.0.20070116-1181414732-0-36-41-0-2</subfield>
  </datafield>
</record>

</collection>
"""
        return


    def test_check_existing(self):
        """bibmatch - check existing record"""
        records = create_records(self.recxml1)
        [dummy1, matchedrecs, dummy2, dummy3] = match_records(records)
        self.assertEqual(1,len(matchedrecs))

    def test_check_new(self):
        """bibmatch - check a new record"""
        records = create_records(self.recxml2)
        [newrecs, dummy1, dummy2, dummy3] = match_records(records)
        self.assertEqual(1,len(newrecs))

    def test_check_ambiguous(self):
        """bibmatch - check an ambiguous record"""
        records = create_records(self.recxml3)
        [dummy1, dummy2, ambig, dummy3] = match_records(records)
        self.assertEqual(1,len(ambig))

    def test_check_fuzzy(self):
        """bibmatch - check fuzzily matched record"""
        records = create_records(self.recxml4)
        [dummy1, dummy2, dummy3, fuzzyrecs] = match_records(records)
        self.assertEqual(1,len(fuzzyrecs))

    def test_check_remote(self):
        """bibmatch - check remote match (Invenio demo site) """
        records = create_records(self.recxml1)
        [dummy1, matchedrecs, dummy3, fuzzyrecs] = match_records(records, server_url="http://invenio-demo.cern.ch")
        self.assertEqual(1,len(matchedrecs))

TEST_SUITE = make_test_suite(BibMatchTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
