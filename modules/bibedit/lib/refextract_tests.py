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

"""
The Refextract test suite.
"""

import unittest
from invenio.testutils import make_test_suite, run_test_suite
## Import the minimal necessary methods and variables needed to run Refextract
from invenio.refextract import CFG_REFEXTRACT_KB_JOURNAL_TITLES, \
                               CFG_REFEXTRACT_KB_REPORT_NUMBERS, \
                               CFG_REFEXTRACT_SUBFIELD_MISC, \
                               create_marc_xml_reference_section, \
                               build_titles_knowledge_base, \
                               build_reportnum_knowledge_base, \
                               display_xml_record, \
                               compress_m_subfields, \
                               restrict_m_subfields

class RefextractTest(unittest.TestCase):
    """ bibrecord - testing output of refextract """

    def setUp(self):
        """Initialize the example reference section, and the expected output"""

        self.rec_id = "1234"

        self.example_references = ["""[1] <a href="http://cdsweb.cern.ch/">CERN Document Server</a> J. Maldacena, Adv. Theor. Math. Phys. 2 (1998) 231; hep-th/9711200. http://cdsweb.cern.ch/ then http://www.itp.ucsb.edu/online/susyc99/discussion/. ; L. Susskind, J. Math. Phys. 36 (1995) 6377; hep-th/9409089. hello world a<a href="http://uk.yahoo.com/">Yahoo!</a>. Fin.""",
                """[1] J. Maldacena, Adv. Theor. Math. Phys. 2 (1998) 231; hep-th/9711200. http://cdsweb.cern.ch/""",
                """[2] S. Gubser, I. Klebanov and A. Polyakov, Phys. Lett. B428 (1998) 105; hep-th/9802109. http://cdsweb.cern.ch/search.py?AGE=hello-world&ln=en""",
                """[3] E. Witten, Adv. Theor. Math. Phys. 2 (1998) 253; hep-th/9802150.""",
                """[4] O. Aharony, S. Gubser, J. Maldacena, H. Ooguri and Y. Oz, hep-th/9905111.""",
                """[5] L. Susskind, J. Math. Phys. 36 (1995) 6377; hep-th/9409089.""",
                """[6] L. Susskind and E. Witten, hep-th/9805114.""",
                """[7] W. Fischler and L. Susskind, hep-th/9806039; N. Kaloper and A. Linde, Phys. Rev. D60 (1999) 105509, hep-th/9904120.""",
                """[8] R. Bousso, JHEP 9906:028 (1999); hep-th/9906022.""",
                """[9] R. Penrose and W. Rindler, Spinors and Spacetime, volume 2, chapter 9 (Cambridge University Press, Cambridge, 1986).""",
                """[10] R. Britto-Pacumio, A. Strominger and A. Volovich, JHEP 9911:013 (1999); hep-th/9905211. blah hep-th/9905211 blah hep-ph/9711200""",
                """[11] V. Balasubramanian and P. Kraus, Commun. Math. Phys. 208 (1999) 413; hep-th/9902121.""",
                """[12] V. Balasubramanian and P. Kraus, Phys. Rev. Lett. 83 (1999) 3605; hep-th/9903190.""",
                """[13] P. Kraus, F. Larsen and R. Siebelink, hep-th/9906127.""",
                """[14] L. Randall and R. Sundrum, Phys. Rev. Lett. 83 (1999) 4690; hep-th/9906064. this is a test RN of a different type: CERN-LHC-Project-Report-2006-003. more text.""",
                """[15] S. Gubser, hep-th/9912001.""",
                """[16] H. Verlinde, hep-th/9906182; H. Verlinde, hep-th/9912018; J. de Boer, E. Verlinde and H. Verlinde, hep-th/9912012.""",
                """[17] E. Witten, remarks at ITP Santa Barbara conference, "New dimensions in field theory and string theory": http://www.itp.ucsb.edu/online/susyc99/discussion/.""",
                """[18] D. Page and C. Pope, Commun. Math. Phys. 127 (1990) 529.""",
                """[19] M. Duff, B. Nilsson and C. Pope, Physics Reports 130 (1986), chapter 9.""",
                """[20] D. Page, Phys. Lett. B79 (1978) 235.""",
                """[21] M. Cassidy and S. Hawking, Phys. Rev. D57 (1998) 2372, hep-th/9709066; S. Hawking, Phys. Rev. D52 (1995) 5681.""",
                """[22] K. Skenderis and S. Solodukhin, hep-th/9910023.""",
                """[23] M. Henningson and K. Skenderis, JHEP 9807:023 (1998), hep-th/9806087.""",
                """[24] C. Fefferman and C. Graham, "Conformal Invariants", in Elie Cartan et les Mathematiques d'aujourd'hui (Asterisque, 1985) 95.""",
                """[25] C. Graham and J. Lee, Adv. Math. 87 (1991) 186. <a href="http://cdsweb.cern.ch/">CERN Document Server</a>""",
                """[26] E. Witten and S.-T. Yau, hep-th/9910245.""",
                """[27] R. Emparan, JHEP 9906:036 (1999); hep-th/9906040.""",
                """[28] A. Chamblin, R. Emparan, C. Johnson and R. Myers, Phys. Rev. D59 (1999) 64010, hep-th/9808177; S. Hawking, C. Hunter and D. Page, Phys. Rev. D59 (1999) 44033, hep-th/9809035.""",
                """[29] S. Sethi and L. Susskind, Phys. Lett. B400 (1997) 265, hep-th/9702101; T. Banks and N. Seiberg, Nucl. Phys. B497 (1997) 41, hep-th/9702187.""",
                """[30] R. Emparan, C. Johnson and R. Myers, Phys. Rev. D60 (1999) 104001; hep-th/9903238.""",
                """[31] S. Hawking, C. Hunter and M. Taylor-Robinson, Phys. Rev. D59 (1999) 064005; hep-th/9811056.""",
                """[32] J. Dowker, Class. Quant. Grav. 16 (1999) 1937; hep-th/9812202.""",
                """[33] J. Brown and J. York, Phys. Rev. D47 (1993) 1407.""",
                """[34] D. Freedman, S. Mathur, A. Matsuis and L. Rastelli, Nucl. Phys. B546 (1999) 96; hep-th/9804058. More text, followed by an IBID A 546 (1999) 96""",
                """[35] D. Freedman, S. Mathur, A. Matsuis and L. Rastelli, Nucl. Phys. B546 (1999) 96; hep-th/9804058. More text, followed by an IBID A""",
                """[37] some misc  lkjslkdjlksjflksj [hep-th/9804058] lkjlkjlkjlkj [hep-th/0001567], hep-th/1212321, some more misc, Nucl. Phys. B546 (1999) 96""",
                """[38] R. Emparan, C. Johnson and R.... Myers, Phys. Rev. D60 (1999) 104001; this is :: .... misc! hep-th/9903238. and some ...,.,.,.,::: more hep-ph/9912000""",
                """[10] A. Ceresole, G. Dall Agata and R. D Auria, JHEP 11(1999) 009, [hep-th/9907216].""",
                """[12] D.P. Jatkar and S. Randjbar-Daemi, Phys. Lett. B460, 281 (1999) [hep-th/9904187].""",
                """[14] G. DallAgata, Phys. Lett. B460, (1999) 79, [hep-th/9904198].""",
                """[13] S.M. Donaldson, Instantons and Geometric Invariant Theory, Comm. Math. Phys., 93, (1984), 453-460.""",
                """[16] Becchi C., Blasi A., Bonneau G., Collina R., Delduc F., Commun. Math. Phys., 1988, 120, 121.""",
                """[26]: N. Nekrasov, A. Schwarz, Instantons on noncommutative R4 and (2, 0) superconformal six-dimensional theory, Comm. Math. Phys., 198, (1998), 689-703.""",
                """[2] H. J. Bhabha, Rev. Mod. Phys. 17, 200(1945); ibid, 21, 451(1949); S. Weinberg, Phys. Rev. 133, B1318(1964); ibid, 134, 882(1964); D. L. Pursey, Ann. Phys(N. Y)32, 157(1965); W. K. Tung, Phys, Rev. Lett. 16, 763(1966); Phys. Rev. 156, 1385(1967); W. J. Hurley, Phys. Rev. Lett. 29, 1475(1972).""",
                """[21] E. Schrodinger, Sitzungsber. Preuss. Akad. Wiss. Phys. Math. Kl. 24, 418(1930); ibid, 3, 1(1931); K. Huang, Am. J. Phys. 20, 479(1952); H. Jehle, Phys, Rev. D3, 306(1971); G. A. Perkins, Found. Phys. 6, 237(1976); J. A. Lock, Am. J. Phys. 47, 797(1979); A. O. Barut et al, Phys. Rev. D23, 2454(1981); ibid, D24, 3333(1981); ibid, D31, 1386(1985); Phys. Rev. Lett. 52, 2009(1984).""",
                """[1] P. A. M. Dirac, Proc. R. Soc. London, Ser. A155, 447(1936); ibid, D24, 3333(1981).""",
                """[40] O.O. Vaneeva, R.O. Popovych and C. Sophocleous, Enhanced Group Analysis and Exact Solutions of Vari-able Coefficient Semilinear Diffusion Equations with a Power Source, Acta Appl. Math., doi:10.1007/s10440-008-9280-9, 46 p., arXiv:0708.3457.""",
                """[41] M. I. Trofimov, N. De Filippis and E. A. Smolenskii. Application of the electronegativity indices of organic molecules to tasks of chemical informatics. Russ. Chem. Bull., 54:2235-2246, 2005. http://dx.doi.org/10.1007/s11172-006-0105-6.""",
                """[42] M. Gell-Mann, P. Ramon ans R. Slansky, in Supergravity, P. van Niewenhuizen and D. Freedman (North-Holland 1979); T. Yanagida, in Proceedings of the Workshop on the Unified Thoery and the Baryon Number in teh Universe, ed. O. Sawaga and A. Sugamoto (Tsukuba 1979); R.N. Mohapatra and G. Senjanovic, Phys. Rev. Lett. 44, 912, (1980).
                """,
               ]

        self.references_expected = u"""<record>
   <controlfield tag="001">1234</controlfield>
      <subfield code="u">http://uk.yahoo.com/</subfield>
      <subfield code="z">Yahoo!</subfield>
      <subfield code="m">Fin</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="h">J. Maldacena</subfield>
      <subfield code="s">Adv. Theor. Math. Phys. 2 (1998) 231</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="r">hep-th/9711200</subfield>
      <subfield code="u">http://cdsweb.cern.ch/</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="h">S. Gubser, I. Klebanov and A. Polyakov</subfield>
      <subfield code="s">Phys. Lett. B 428 (1998) 105</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="r">hep-th/9802109</subfield>
      <subfield code="u">http://cdsweb.cern.ch/search.py</subfield>
      <subfield code="m">?AGE=hello-world&amp;ln=en</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[3]</subfield>
      <subfield code="h">E. Witten</subfield>
      <subfield code="s">Adv. Theor. Math. Phys. 2 (1998) 253</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[3]</subfield>
      <subfield code="r">hep-th/9802150</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[4]</subfield>
      <subfield code="h">O. Aharony, S. Gubser, J. Maldacena, H. Ooguri and Y. Oz</subfield>
      <subfield code="r">hep-th/9905111</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[5]</subfield>
      <subfield code="h">L. Susskind</subfield>
      <subfield code="s">J. Math. Phys. 36 (1995) 6377</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[5]</subfield>
      <subfield code="r">hep-th/9409089</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[6]</subfield>
      <subfield code="h">L. Susskind and E. Witten</subfield>
      <subfield code="r">hep-th/9805114</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[7]</subfield>
      <subfield code="h">W. Fischler and L. Susskind</subfield>
      <subfield code="r">hep-th/9806039</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[7]</subfield>
      <subfield code="h">N. Kaloper and A. Linde</subfield>
      <subfield code="s">Phys. Rev. D 60 (1999) 105509</subfield>
      <subfield code="r">hep-th/9904120</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[8]</subfield>
      <subfield code="h">R. Bousso</subfield>
      <subfield code="s">J. High Energy Phys. 9906 (1999) 028</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[8]</subfield>
      <subfield code="r">hep-th/9906022</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[9]</subfield>
      <subfield code="h">R. Penrose and W. Rindler</subfield>
      <subfield code="m">Spinors and Spacetime, volume 2, chapter 9 (Cambridge University Press, Cambridge, 1986)</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[10]</subfield>
      <subfield code="h">R. Britto-Pacumio, A. Strominger and A. Volovich</subfield>
      <subfield code="s">J. High Energy Phys. 9911 (1999) 013</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[10]</subfield>
      <subfield code="r">hep-th/9905211</subfield>
      <subfield code="m">blah</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[10]</subfield>
      <subfield code="r">hep-th/9905211</subfield>
      <subfield code="m">blah</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[10]</subfield>
      <subfield code="r">hep-ph/9711200</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[11]</subfield>
      <subfield code="h">V. Balasubramanian and P. Kraus</subfield>
      <subfield code="s">Commun. Math. Phys. 208 (1999) 413</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[11]</subfield>
      <subfield code="r">hep-th/9902121</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[12]</subfield>
      <subfield code="h">V. Balasubramanian and P. Kraus</subfield>
      <subfield code="s">Phys. Rev. Lett. 83 (1999) 3605</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[12]</subfield>
      <subfield code="r">hep-th/9903190</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[13]</subfield>
      <subfield code="h">P. Kraus, F. Larsen and R. Siebelink</subfield>
      <subfield code="r">hep-th/9906127</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[14]</subfield>
      <subfield code="h">L. Randall and R. Sundrum</subfield>
      <subfield code="s">Phys. Rev. Lett. 83 (1999) 4690</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[14]</subfield>
      <subfield code="r">hep-th/9906064</subfield>
      <subfield code="m">this is a test RN of a different type</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[14]</subfield>
      <subfield code="r">CERN-LHC-Project-Report-2006-003</subfield>
      <subfield code="m">more text</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[15]</subfield>
      <subfield code="h">S. Gubser</subfield>
      <subfield code="r">hep-th/9912001</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[16]</subfield>
      <subfield code="h">H. Verlinde</subfield>
      <subfield code="r">hep-th/9906182</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[16]</subfield>
      <subfield code="h">H. Verlinde</subfield>
      <subfield code="r">hep-th/9912018</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[16]</subfield>
      <subfield code="h">J. de Boer, E. Verlinde and H. Verlinde</subfield>
      <subfield code="r">hep-th/9912012</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[17]</subfield>
      <subfield code="h">E. Witten</subfield>
      <subfield code="m">remarks at ITP Santa Barbara conference, "New dimensions in field theory and string theory":</subfield>
      <subfield code="u">http://www.itp.ucsb.edu/online/susyc99/discussion/</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[18]</subfield>
      <subfield code="h">D. Page and C. Pope</subfield>
      <subfield code="s">Commun. Math. Phys. 127 (1990) 529</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[19]</subfield>
      <subfield code="h">M. Duff, B. Nilsson and C. Pope</subfield>
      <subfield code="m">Phys. Rep. 130 (1986), chapter 9</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[20]</subfield>
      <subfield code="h">D. Page</subfield>
      <subfield code="s">Phys. Lett. B 79 (1978) 235</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[21]</subfield>
      <subfield code="h">M. Cassidy and S. Hawking</subfield>
      <subfield code="s">Phys. Rev. D 57 (1998) 2372</subfield>
      <subfield code="r">hep-th/9709066</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[21]</subfield>
      <subfield code="h">S. Hawking</subfield>
      <subfield code="s">Phys. Rev. D 52 (1995) 5681</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[22]</subfield>
      <subfield code="h">K. Skenderis and S. Solodukhin</subfield>
      <subfield code="r">hep-th/9910023</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[23]</subfield>
      <subfield code="h">M. Henningson and K. Skenderis</subfield>
      <subfield code="s">J. High Energy Phys. 9807 (1998) 023</subfield>
      <subfield code="r">hep-th/9806087</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[24]</subfield>
      <subfield code="h">C. Fefferman and C. Graham</subfield>
      <subfield code="m">"Conformal Invariants", in Elie Cartan et les Mathematiques d'aujourd'hui (Asterisque, 1985) 95</subfield>
   </datafield>
      <subfield code="u">http://cdsweb.cern.ch/</subfield>
      <subfield code="z">CERN Document Server</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[26]</subfield>
      <subfield code="h">E. Witten and S.-T. Yau</subfield>
      <subfield code="r">hep-th/9910245</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[27]</subfield>
      <subfield code="h">R. Emparan</subfield>
      <subfield code="s">J. High Energy Phys. 9906 (1999) 036</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[27]</subfield>
      <subfield code="r">hep-th/9906040</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[28]</subfield>
      <subfield code="h">A. Chamblin, R. Emparan, C. Johnson and R. Myers</subfield>
      <subfield code="s">Phys. Rev. D 59 (1999) 64010</subfield>
      <subfield code="r">hep-th/9808177</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[28]</subfield>
      <subfield code="h">S. Hawking, C. Hunter and D. Page</subfield>
      <subfield code="s">Phys. Rev. D 59 (1999) 44033</subfield>
      <subfield code="r">hep-th/9809035</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[29]</subfield>
      <subfield code="h">S. Sethi and L. Susskind</subfield>
      <subfield code="s">Phys. Lett. B 400 (1997) 265</subfield>
      <subfield code="r">hep-th/9702101</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[29]</subfield>
      <subfield code="h">T. Banks and N. Seiberg</subfield>
      <subfield code="s">Nucl. Phys. B 497 (1997) 41</subfield>
      <subfield code="r">hep-th/9702187</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[30]</subfield>
      <subfield code="h">R. Emparan, C. Johnson and R. Myers</subfield>
      <subfield code="s">Phys. Rev. D 60 (1999) 104001</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[30]</subfield>
      <subfield code="r">hep-th/9903238</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[31]</subfield>
      <subfield code="h">S. Hawking, C. Hunter and M. Taylor-Robinson</subfield>
      <subfield code="s">Phys. Rev. D 59 (1999) 064005</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[31]</subfield>
      <subfield code="r">hep-th/9811056</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[32]</subfield>
      <subfield code="h">J. Dowker</subfield>
      <subfield code="s">Class. Quantum Gravity 16 (1999) 1937</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[32]</subfield>
      <subfield code="r">hep-th/9812202</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[33]</subfield>
      <subfield code="h">J. Brown and J. York</subfield>
      <subfield code="s">Phys. Rev. D 47 (1993) 1407</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[34]</subfield>
      <subfield code="h">D. Freedman, S. Mathur, A. Matsuis and L. Rastelli</subfield>
      <subfield code="s">Nucl. Phys. B 546 (1999) 96</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[34]</subfield>
      <subfield code="r">hep-th/9804058</subfield>
      <subfield code="m">More text, followed by an</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[34]</subfield>
      <subfield code="s">Nucl. Phys. A 546 (1999) 96</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[35]</subfield>
      <subfield code="h">D. Freedman, S. Mathur, A. Matsuis and L. Rastelli</subfield>
      <subfield code="s">Nucl. Phys. B 546 (1999) 96</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[35]</subfield>
      <subfield code="r">hep-th/9804058</subfield>
      <subfield code="m">More text, followed by an IBID A</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[37]</subfield>
      <subfield code="m">some misc lkjslkdjlksjflksj  lkjlkjlkjlkj</subfield>
      <subfield code="r">hep-th/9804058</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[37]</subfield>
      <subfield code="r">hep-th/0001567</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[37]</subfield>
      <subfield code="r">hep-th/1212321</subfield>
      <subfield code="m">some more misc</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[37]</subfield>
      <subfield code="s">Nucl. Phys. B 546 (1999) 96</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[38]</subfield>
      <subfield code="h">R. Emparan, C. Johnson</subfield>
      <subfield code="s">Phys. Rev. D 60 (1999) 104001</subfield>
      <subfield code="m">and R.... Myers</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[38]</subfield>
      <subfield code="r">hep-th/9903238</subfield>
      <subfield code="m">this is.... misc! . and some...,.,.,., more</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[38]</subfield>
      <subfield code="r">hep-ph/9912000</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[10]</subfield>
      <subfield code="h">A. Ceresole, G. Dall</subfield>
      <subfield code="s">J. High Energy Phys. 11 (1999) 009</subfield>
      <subfield code="r">hep-th/9907216</subfield>
      <subfield code="m">Agata and R. D Auria</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[12]</subfield>
      <subfield code="h">D.P. Jatkar and S. Randjbar-Daemi</subfield>
      <subfield code="s">Phys. Lett. B 460 (1999) 281</subfield>
      <subfield code="r">hep-th/9904187</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[14]</subfield>
      <subfield code="h">G. DallAgata</subfield>
      <subfield code="s">Phys. Lett. B 460 (1999) 79</subfield>
      <subfield code="r">hep-th/9904198</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[13]</subfield>
      <subfield code="h">S.M. Donaldson</subfield>
      <subfield code="s">Commun. Math. Phys. 93 (1984) 453</subfield>
      <subfield code="m">Instantons and Geometric Invariant Theory</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[16]</subfield>
      <subfield code="s">Commun. Math. Phys. 120 (1988) 121</subfield>
      <subfield code="m">Becchi C., Blasi A., Bonneau G., Collina R., Delduc F</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[26]</subfield>
      <subfield code="h">N. Nekrasov, A. Schwarz</subfield>
      <subfield code="s">Commun. Math. Phys. 198 (1998) 689</subfield>
      <subfield code="m">Instantons on noncommutative R4 and (2, 0) superconformal six-dimensional theory</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="h">H. J. Bhabha</subfield>
      <subfield code="s">Rev. Mod. Phys. 17 (1945) 200</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="s">Rev. Mod. Phys. 21 (1949) 451</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="h">S. Weinberg</subfield>
      <subfield code="s">Phys. Rev. 134 (1964) 882</subfield>
      <subfield code="m">Phys. Rev. 133, B1318(1964);</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="h">D. L. Pursey</subfield>
      <subfield code="s">Ann. Phys. (San Diego) 32 (1965) 157</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="h">W. K. Tung</subfield>
      <subfield code="s">Phys. Rev. Lett. 16 (1966) 763</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="s">Phys. Rev. 156 (1967) 1385</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="h">W. J. Hurley</subfield>
      <subfield code="s">Phys. Rev. Lett. 29 (1972) 1475</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[21]</subfield>
      <subfield code="h">E. Schrodinger</subfield>
      <subfield code="s">Sitzungsber. Königl. Preuss. Akad. Wiss. 3 (1931) 1</subfield>
      <subfield code="m">Sitzungsber. Sitzungsber. Königl. Preuss. Akad. Wiss. Phys. Math. Kl. : 24 (1930) 418;</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[21]</subfield>
      <subfield code="h">K. Huang</subfield>
      <subfield code="s">Am. J. Phys. 20 (1952) 479</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[21]</subfield>
      <subfield code="h">H. Jehle</subfield>
      <subfield code="s">Phys. Rev. D 3 (1971) 306</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[21]</subfield>
      <subfield code="h">G. A. Perkins</subfield>
      <subfield code="s">Found. Phys. 6 (1976) 237</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[21]</subfield>
      <subfield code="h">J. A. Lock</subfield>
      <subfield code="s">Am. J. Phys. 47 (1979) 797</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[21]</subfield>
      <subfield code="h">A. O. Barut et al</subfield>
      <subfield code="s">Phys. Rev. D 23 (1981) 2454</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[21]</subfield>
      <subfield code="s">Phys. Rev. D 24 (1981) 3333</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[21]</subfield>
      <subfield code="s">Phys. Rev. D 31 (1985) 1386</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[21]</subfield>
      <subfield code="s">Phys. Rev. Lett. 52 (1984) 2009</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="h">P. A. M. Dirac</subfield>
      <subfield code="s">Proc. R. Soc. Lond., A 155 (1936) 447</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="s">Proc. R. Soc. Lond., D 24 (1981) 3333</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[40]</subfield>
      <subfield code="h">O.O. Vaneeva, R.O. Popovych and C. Sophocleous</subfield>
      <subfield code="a">10.1007/s10440-008-9280-9</subfield>
      <subfield code="r">arXiv:0708.3457</subfield>
      <subfield code="m">Enhanced Group Analysis and Exact Solutions of Vari-able Coefficient Semilinear Diffusion Equations with a Power Source, Acta Appl. Math., , 46 p</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[41]</subfield>
      <subfield code="h">M. I. Trofimov, N. De Filippis and E. A. Smolenskii</subfield>
      <subfield code="u">http://dx.doi.org/10.1007/s11172-006-0105-6</subfield>
      <subfield code="a">10.1007/s11172-006-0105-6</subfield>
      <subfield code="m">Application of the electronegativity indices of organic molecules to tasks of chemical informatics. Russ. Chem. Bull.: 54 (2005) 2235</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[42]</subfield>
      <subfield code="h">M. Gell-Mann, P. Ramon and R. Slansky</subfield>
      <subfield code="m">in Supergravity</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[42]</subfield>
      <subfield code="h">P. van Niewenhuizen and D. Freedman</subfield>
      <subfield code="m">(North-Holland 1979);</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[42]</subfield>
      <subfield code="h">T. Yanagida</subfield>
      <subfield code="m">in Proceedings of the Workshop on the Unified Thoery and the Baryon Number in teh Universe, ed. O. Sawaga and A. Sugamoto (Tsukuba 1979);</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[42]</subfield>
      <subfield code="h">R.N. Mohapatra and G. Senjanovic</subfield>
      <subfield code="s">Phys. Rev. Lett. 44 (1980) 912</subfield>
   </datafield>"""

    def test_refextract(self):
        """refextract - test comprehensive example"""

        # Build the titles knowledge base
        (title_search_kb, \
         title_search_standardised_titles, \
         title_search_keys) = build_titles_knowledge_base(CFG_REFEXTRACT_KB_JOURNAL_TITLES)

        # Build the report numbers knowledge base
        (preprint_reportnum_sre, \
         standardised_preprint_reportnum_categs) = build_reportnum_knowledge_base(CFG_REFEXTRACT_KB_REPORT_NUMBERS)

        # Identify journal titles, report numbers, URLs, DOIs, and authors
        # Also, generate marc xml using the example reference lines
        (processed_references, count_misc, \
         count_title, count_reportnum, \
         count_url, count_doi, record_titles_count) = \
         create_marc_xml_reference_section(map(lambda x: unicode(x,'utf-8'), self.example_references), \
                                            preprint_reportnum_sre, \
                                            standardised_preprint_reportnum_categs, \
                                            title_search_kb, \
                                            title_search_standardised_titles, \
                                            title_search_keys)

        # Generate the xml string to be outputted
        tmp_out = display_xml_record(0, \
                                 count_reportnum, \
                                 count_title, \
                                 count_url, \
                                 count_doi, \
                                 count_misc, \
                                 self.rec_id, \
                                 processed_references)

        # Remove redundant misc subfields
        (m_restricted, ref_lines) = restrict_m_subfields(tmp_out.split('\n'))

        # Build the final xml string of the output of Refextract
        out = ''
        for rec in ref_lines:
            rec = rec.rstrip()
            if rec:
                out += rec + '\n'

        # Compress mulitple 'm' subfields in a datafield
        out = compress_m_subfields(out)

        # Remove the ending statistical datafield from the final extracted references
        out = out[:out.find('<datafield tag="999" ind1="C" ind2="6">')].rstrip()

        # Compare the recieved output with the expected references
        self.assertEqual(out, self.references_expected)

TEST_SUITE = make_test_suite(RefextractTest)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
