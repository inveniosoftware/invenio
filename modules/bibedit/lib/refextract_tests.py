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
                               create_marc_xml_reference_section, \
                               build_titles_knowledge_base, \
                               build_reportnum_knowledge_base, \
                               display_xml_record, \
                               compress_subfields, \
                               restrict_m_subfields, \
                               cli_opts

# Initially, build the titles knowledge base
(title_search_kb, \
 title_search_standardised_titles, \
 title_search_keys) = build_titles_knowledge_base(CFG_REFEXTRACT_KB_JOURNAL_TITLES)

# Initially, build the report numbers knowledge base
(preprint_reportnum_sre, \
 standardised_preprint_reportnum_categs) = build_reportnum_knowledge_base(CFG_REFEXTRACT_KB_REPORT_NUMBERS)


class RefextractTest(unittest.TestCase):
    """ bibrecord - testing output of refextract """

    def setUp(self):
        """Initialize the example reference section, and the expected output"""

        # Set the record id to be solely used inside the '001' controlfield
        self.rec_id = "1234"

        # Set the output journal title format to match that of INVENIO's
        cli_opts['inspire'] = 0

    def extract_references(self, reference_lines):
        """ Given a list of raw reference lines, output the MARC-XML content extracted version"""

        # Identify journal titles, report numbers, URLs, DOIs, and authors...
        # Generate marc xml using the example reference lines
        (processed_references, count_misc, \
         count_title, count_reportnum, \
         count_url, count_doi, count_auth_group, record_titles_count) = \
         create_marc_xml_reference_section(map(lambda x: unicode(x, 'utf-8'), reference_lines), \
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
                                 count_auth_group, \
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

        # Compress mulitple 'm' and 'h' subfields in a datafield
        out = compress_subfields(out, 'm')
        out = compress_subfields(out, 'h')

        # Remove the ending statistical datafield from the final extracted references
        out = out[:out.find('<datafield tag="999" ind1="C" ind2="6">')].rstrip()

        return out

    def test_author_recognition(self):
        """ refextract - test author example """

        ex_author_lines = ["""[1] M. I. Trofimov, N. De Filippis and E. A. Smolenskii. Application of the electronegativity indices of organic molecules to tasks of chemical informatics.""",
                """[2] M. Gell-Mann, P. Ramon ans R. Slansky, in Supergravity, P. van Niewenhuizen and D. Freedman (North-Holland 1979); T. Yanagida, in Proceedings of the Workshop on the Unified Thoery and the Baryon Number in teh Universe, ed. O. Sawaga and A. Sugamoto (Tsukuba 1979); R.N. Mohapatra and G. Senjanovic, some more misc text. Smith W.H., L. Altec et al some personal communication.""",
                """[3] S. Hawking, C. Hunter and M. Taylor-Robinson.""",
                """[4] E. Schrodinger, Sitzungsber. Preuss. Akad. Wiss. Phys. Math. Kl. 24, 418(1930); K. Huang, Am. J. Phys. 20, 479(1952); H. Jehle, Phys, Rev. D3, 306(1971); G. A. Perkins, Found. Phys. 6, 237(1976); J. A. Lock, Am. J. Phys. 47, 797(1979); A. O. Barut et al, Phys. Rev. D23, 2454(1981); ibid, D24, 3333(1981); ibid, D31, 1386(1985); Phys. Rev. Lett. 52, 2009(1984).""",
                """[5] Hawking S., P. van Niewenhuizen, L.S. Durkin, D. Freeman, some title of some journal""",
                """[6] Hawking S., D. Freeman, some title of some journal""",
                """[7] Hawking S. and D. Freeman, another random title of some random journal""",
                """[8] L.S. Durkin and P. Langacker, Phys. Lett B166, 436 (1986); Amaldi et al., Phys. Rev. D36, 1385 (1987); Hayward and Yellow et al., eds. Phys. Lett B245, 669 (1990); Nucl. Phys. B342, 15 (1990);
                """,
                """[9] M. I. Moli_ero, and J. C. Oller, Performance test of the CMS link alignment system
                """,
                """[10] Hush, D.R., R.Leighton, and B.G. Horne, 1993. "Progress in supervised Neural Netw. Whats new since Lippmann?" IEEE Signal Process. Magazine 10, 8-39
                """,
                """[11] T.G. Rizzo, Phys. Rev. D40, 3035 (1989); Proceedings of the 1990 Summer Study on High Energy Physics. ed E. Berger, June 25-July 13, 1990, Snowmass Colorado (World Scientific, Singapore, 1992) p. 233; V. Barger, J.L. Hewett and T.G. Rizzo, Phys. Rev. D42, 152 (1990); J.L. Hewett, Phys. Lett. B238, 98 (1990);
                """]

        references_expected = u"""<record>
   <controlfield tag="001">1234</controlfield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="h">M. I. Trofimov, N. De Filippis and E. A. Smolenskii</subfield>
      <subfield code="m">Application of the electronegativity indices of organic molecules to tasks of chemical informatics</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="h">M. Gell-Mann, P. Ramon</subfield>
      <subfield code="m">ans R. Slansky in Supergravity</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="h">P. van Niewenhuizen and D. Freedman</subfield>
      <subfield code="m">(North-Holland 1979);</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="h">T. Yanagida (O. Sawaga and A. Sugamoto (eds.))</subfield>
      <subfield code="m">in Proceedings of the Workshop on the Unified Thoery and the Baryon Number in teh Universe, (Tsukuba 1979);</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="h">R.N. Mohapatra and G. Senjanovic</subfield>
      <subfield code="m">some more misc text</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="h">Smith W.H., L. Altec et al</subfield>
      <subfield code="m">some personal communication</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[3]</subfield>
      <subfield code="h">S. Hawking, C. Hunter and M. Taylor-Robinson</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[4]</subfield>
      <subfield code="h">E. Schrodinger</subfield>
      <subfield code="m">Sitzungsber. Sitzungsber. K\xf6nigl. Preuss. Akad. Wiss. Phys. Math. Kl. : 24 (1930) 418;</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[4]</subfield>
      <subfield code="h">K. Huang</subfield>
      <subfield code="s">Am. J. Phys. 20 (1952) 479</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[4]</subfield>
      <subfield code="h">H. Jehle</subfield>
      <subfield code="s">Phys. Rev D 3 (1971) 306</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[4]</subfield>
      <subfield code="h">G. A. Perkins</subfield>
      <subfield code="s">Found. Phys. 6 (1976) 237</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[4]</subfield>
      <subfield code="h">J. A. Lock</subfield>
      <subfield code="s">Am. J. Phys. 47 (1979) 797</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[4]</subfield>
      <subfield code="h">A. O. Barut et al</subfield>
      <subfield code="s">Phys. Rev D 23 (1981) 2454</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[4]</subfield>
      <subfield code="s">Phys. Rev D 24 (1981) 3333</subfield>
      <subfield code="h">A. O. Barut et al</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[4]</subfield>
      <subfield code="s">Phys. Rev D 31 (1985) 1386</subfield>
      <subfield code="h">A. O. Barut et al</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[4]</subfield>
      <subfield code="s">Phys. Rev. Lett. 52 (1984) 2009</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[5]</subfield>
      <subfield code="h">Hawking S., P. van Niewenhuizen, L.S. Durkin, D. Freeman</subfield>
      <subfield code="m">some title of some journal</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[6]</subfield>
      <subfield code="h">Hawking S., D. Freeman</subfield>
      <subfield code="m">some title of some journal</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[7]</subfield>
      <subfield code="h">Hawking S. and D. Freeman</subfield>
      <subfield code="m">another random title of some random journal</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[8]</subfield>
      <subfield code="h">L.S. Durkin and P. Langacker</subfield>
      <subfield code="s">Phys. Lett B 166 (1986) 436</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[8]</subfield>
      <subfield code="h">Amaldi et al</subfield>
      <subfield code="s">Phys. Rev D 36 (1987) 1385</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[8]</subfield>
      <subfield code="h">(Hayward and Yellow et al (ed.))</subfield>
      <subfield code="s">Phys. Lett B 245 (1990) 669</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[8]</subfield>
      <subfield code="s">Nucl. Phys B 342 (1990) 15</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[9]</subfield>
      <subfield code="m">M. I. Moli_ero, and J. C. Oller, Performance test of the CMS link alignment system</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[10]</subfield>
      <subfield code="m">Hush, D.R., 1993. "Progress in supervised Neural Netw. Whats new since Lippmann?" IEEE Signal Process. Magazine 10, 8-39</subfield>
      <subfield code="h">R.Leighton, and B.G. Horne</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[11]</subfield>
      <subfield code="h">T.G. Rizzo</subfield>
      <subfield code="s">Phys. Rev D 40 (1989) 3035</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[11]</subfield>
      <subfield code="m">Proceedings of the 1990 Summer Study on High Energy Physics June 25-July 13, 1990, Snowmass Colorado (World Scientific, Singapore, 1992) p. 233;</subfield>
      <subfield code="h">(E. Berger (ed.))</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[11]</subfield>
      <subfield code="h">V. Barger, J.L. Hewett and T.G. Rizzo</subfield>
      <subfield code="s">Phys. Rev D 42 (1990) 152</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[11]</subfield>
      <subfield code="h">J.L. Hewett</subfield>
      <subfield code="s">Phys. Lett B 238 (1990) 98</subfield>
   </datafield>"""
        out = self.extract_references(ex_author_lines)
        #Compare the recieved output with the expected references
        self.assertEqual(out, references_expected)

    def test_doi_recognition(self):
        """ refextract - test doi example """

        ex_doi_lines = ["""[1] Some example misc text, for this doi: http://dx.doi.org/10.1007/s11172-006-0105-6""",
                """[2] 10.1007/s11172-006-0105-6."""]

        references_expected = u"""<record>
   <controlfield tag="001">1234</controlfield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="m">Some example misc text, for this doi:</subfield>
      <subfield code="a">10.1007/s11172-006-0105-6</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="a">10.1007/s11172-006-0105-6</subfield>
   </datafield>"""

        out = self.extract_references(ex_doi_lines)
        #Compare the recieved output with the expected references
        self.assertEqual(out, references_expected)

    def test_url_recognition(self):
        """ refextract - test url example """

        ex_url_lines = ["""[1] <a href="http://cdsweb.cern.ch/">CERN Document Server</a>; http://cdsweb.cern.ch/ then http://www.itp.ucsb.edu/online/susyc99/discussion/; hello world <a href="http://uk.yahoo.com/">Yahoo!</a>""",
                """[2] CERN Document Server <a href="http://cdsweb.cern.ch/">CERN Document Server</a>""",
                """[3] A list of authors, and a title. http://cdsweb.cern.ch/"""]

        references_expected = u"""<record>
   <controlfield tag="001">1234</controlfield>
      <subfield code="u">http://uk.yahoo.com/</subfield>
      <subfield code="z">Yahoo!</subfield>
   </datafield>
      <subfield code="u">http://cdsweb.cern.ch/</subfield>
      <subfield code="z">CERN Document Server</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[3]</subfield>
      <subfield code="m">A list of authors, and a title</subfield>
      <subfield code="u">http://cdsweb.cern.ch/</subfield>
   </datafield>"""
        out = self.extract_references(ex_url_lines)
        #Compare the recieved output with the expected references
        self.assertEqual(out, references_expected)

    def test_report_number_recognition(self):
        """ refextract - test report number example """
        ex_repno_lines = ["""[1] hep-th/9806087""",
                """[2] arXiv:0708.3457""",
                """[3] some misc  lkjslkdjlksjflksj [hep-th/9804058] arXiv:0708.3457, hep-th/1212321, some more misc,"""]

        references_expected = u"""<record>
   <controlfield tag="001">1234</controlfield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="m">hep-th/9806087</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="m">arXiv 0708.3457</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[3]</subfield>
      <subfield code="m">some misc lkjslkdjlksjflksj</subfield>
      <subfield code="r">hep-th/9804058</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[3]</subfield>
      <subfield code="r">arXiv:0708.3457</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[3]</subfield>
      <subfield code="r">hep-th/1212321</subfield>
      <subfield code="m">some more misc</subfield>
   </datafield>"""
        out = self.extract_references(ex_repno_lines)
        #Compare the recieved output with the expected references
        self.assertEqual(out, references_expected)

    def test_journal_title_recognition(self):
        """ refextract - test journal title example """

        ex_journal_title_lines = ["""[1] Phys. Rev. D52 (1995) 5681.""",
                """[2] Phys. Rev. D59 (1999) 064005;""",
                """[3] Am. J. Phys. 47, 797(1979);""",
                """[4] R. Soc. London, Ser. A155, 447(1936); ibid, D24, 3333(1981).""",
                """[5] Commun. Math. Phys. 208 (1999) 413;""",
                """[6] Phys. Rev. D23, 2454(1981); ibid, D24, 3333(1981); ibid, D31, 1386(1985); More text, followed by an IBID A 546 (1999) 96""",
                """[7] Phys. Math. Kl. 24, 418(1930); Am. J. Phys. 20, 479(1952); Phys, Rev. D3, 306(1971); Phys. 6, 237(1976); Am. J. Phys. 47, 797(1979); Phys. Rev. D23, 2454(1981); ibid, D24, 3333(1981); ibid, D31, 1386(1985); Phys. Rev. Lett. 52, 2009(1984)."""]


        references_expected = u"""<record>
   <controlfield tag="001">1234</controlfield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="s">Phys. Rev D 52 (1995) 5681</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="s">Phys. Rev D 59 (1999) 064005</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[3]</subfield>
      <subfield code="s">Am. J. Phys. 47 (1979) 797</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[4]</subfield>
      <subfield code="h">R. Soc</subfield>
      <subfield code="m">London, Ser. A : 155 (1936) 447; ibid, D : 24 (1981) 3333</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[5]</subfield>
      <subfield code="s">Commun. Math. Phys. 208 (1999) 413</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[6]</subfield>
      <subfield code="s">Phys. Rev D 23 (1981) 2454</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[6]</subfield>
      <subfield code="s">Phys. Rev D 24 (1981) 3333</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[6]</subfield>
      <subfield code="s">Phys. Rev D 31 (1985) 1386</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[6]</subfield>
      <subfield code="m">More text, followed by an</subfield>
      <subfield code="s">Phys. Rev A 546 (1999) 96</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[7]</subfield>
      <subfield code="m">Phys. Math. Kl. : 24 (1930) 418;</subfield>
      <subfield code="s">Am. J. Phys. 20 (1952) 479</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[7]</subfield>
      <subfield code="s">Phys. Rev D 3 (1971) 306</subfield>
      <subfield code="m">Phys. : 6 (1976) 237;</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[7]</subfield>
      <subfield code="s">Am. J. Phys. 47 (1979) 797</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[7]</subfield>
      <subfield code="s">Phys. Rev D 23 (1981) 2454</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[7]</subfield>
      <subfield code="s">Phys. Rev D 24 (1981) 3333</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[7]</subfield>
      <subfield code="s">Phys. Rev D 31 (1985) 1386</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[7]</subfield>
      <subfield code="s">Phys. Rev. Lett. 52 (1984) 2009</subfield>
   </datafield>"""
        out = self.extract_references(ex_journal_title_lines)
        #Compare the recieved output with the expected references
        self.assertEqual(out, references_expected)

    def test_mixed(self):
        """ refextract - test mixed content example """

        ex_mixed_lines = ["""[1] E. Schrodinger, Sitzungsber. Preuss. Akad. Wiss. Phys. Math. Kl. 24, 418(1930); ibid, 3, 1(1931); K. Huang, Am. J. Phys. 20, 479(1952); H. Jehle, Phys, Rev. D3, 306(1971); G. A. Perkins, Found. Phys. 6, 237(1976); J. A. Lock, Am. J. Phys. 47, 797(1979); A. O. Barut et al, Phys. Rev. D23, 2454(1981); ibid, D24, 3333(1981); ibid, D31, 1386(1985); Phys. Rev. Lett. 52, 2009(1984).""",
                """[2] P. A. M. Dirac, Proc. R. Soc. London, Ser. A155, 447(1936); ibid, D24, 3333(1981).""",
                """[3] O.O. Vaneeva, R.O. Popovych and C. Sophocleous, Enhanced Group Analysis and Exact Solutions of Vari-able Coefficient Semilinear Diffusion Equations with a Power Source, Acta Appl. Math., doi:10.1007/s10440-008-9280-9, 46 p., arXiv:0708.3457.""",
                """[4] M. I. Trofimov, N. De Filippis and E. A. Smolenskii. Application of the electronegativity indices of organic molecules to tasks of chemical informatics. Russ. Chem. Bull., 54:2235-2246, 2005. http://dx.doi.org/10.1007/s11172-006-0105-6.""",
                """[5] M. Gell-Mann, P. Ramon and R. Slansky, in Supergravity, P. van Niewenhuizen and D. Freedman (North-Holland 1979); T. Yanagida, in Proceedings of the Workshop on the Unified Thoery and the Baryon Number in teh Universe, ed. O. Sawaga and A. Sugamoto (Tsukuba 1979); R.N. Mohapatra and G. Senjanovic, Phys. Rev. Lett. 44, 912, (1980).
                """,
                """[6] L.S. Durkin and P. Langacker, Phys. Lett B166, 436 (1986); Amaldi et al., Phys. Rev. D36, 1385 (1987); Hayward and Yellow et al., eds. Phys. Lett B245, 669 (1990); Nucl. Phys. B342, 15 (1990);
                """,
                """[7] Wallet et al, Some preceedings on Higgs Phys. Rev. Lett. 44, 912, (1980) 10.1007/s11172-006-0105-6; Pod I., C. Jennings, et al, Blah blah blah blah blah blah blah blah blah blah, Nucl. Phys. B342, 15 (1990)"""]

        references_expected = u"""<record>
   <controlfield tag="001">1234</controlfield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="h">E. Schrodinger</subfield>
      <subfield code="m">Sitzungsber. Sitzungsber. K\xf6nigl. Preuss. Akad. Wiss. Phys. Math. Kl. : 24 (1930) 418;</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="s">Sitzungsber. K\xf6nigl. Preuss. Akad. Wiss. 3 (1931) 1</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="h">K. Huang</subfield>
      <subfield code="s">Am. J. Phys. 20 (1952) 479</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="h">H. Jehle</subfield>
      <subfield code="s">Phys. Rev D 3 (1971) 306</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="h">G. A. Perkins</subfield>
      <subfield code="s">Found. Phys. 6 (1976) 237</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="h">J. A. Lock</subfield>
      <subfield code="s">Am. J. Phys. 47 (1979) 797</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="h">A. O. Barut et al</subfield>
      <subfield code="s">Phys. Rev D 23 (1981) 2454</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="s">Phys. Rev D 24 (1981) 3333</subfield>
      <subfield code="h">A. O. Barut et al</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="s">Phys. Rev D 31 (1985) 1386</subfield>
      <subfield code="h">A. O. Barut et al</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[1]</subfield>
      <subfield code="s">Phys. Rev. Lett. 52 (1984) 2009</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="h">P. A. M. Dirac</subfield>
      <subfield code="s">Proc. R. Soc. Lond., A 155 (1936) 447</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[2]</subfield>
      <subfield code="s">Proc. R. Soc. Lond., D 24 (1981) 3333</subfield>
      <subfield code="h">P. A. M. Dirac</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[3]</subfield>
      <subfield code="h">O.O. Vaneeva, R.O. Popovych and C. Sophocleous</subfield>
      <subfield code="m">Enhanced Group Analysis and Exact Solutions of Vari-able Coefficient Semilinear Diffusion Equations with a Power Source, Acta Appl. Math., , 46 p</subfield>
      <subfield code="a">10.1007/s10440-008-9280-9</subfield>
      <subfield code="r">arXiv:0708.3457</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[4]</subfield>
      <subfield code="h">M. I. Trofimov, N. De Filippis and E. A. Smolenskii</subfield>
      <subfield code="m">Application of the electronegativity indices of organic molecules to tasks of chemical informatics. Russ. Chem. Bull.: 54 (2005) 2235</subfield>
      <subfield code="a">10.1007/s11172-006-0105-6</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[5]</subfield>
      <subfield code="h">M. Gell-Mann, P. Ramon and R. Slansky</subfield>
      <subfield code="m">in Supergravity</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[5]</subfield>
      <subfield code="h">P. van Niewenhuizen and D. Freedman</subfield>
      <subfield code="m">(North-Holland 1979);</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[5]</subfield>
      <subfield code="h">T. Yanagida (O. Sawaga and A. Sugamoto (eds.))</subfield>
      <subfield code="m">in Proceedings of the Workshop on the Unified Thoery and the Baryon Number in teh Universe, (Tsukuba 1979);</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[5]</subfield>
      <subfield code="h">R.N. Mohapatra and G. Senjanovic</subfield>
      <subfield code="s">Phys. Rev. Lett. 44 (1980) 912</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[6]</subfield>
      <subfield code="h">L.S. Durkin and P. Langacker</subfield>
      <subfield code="s">Phys. Lett B 166 (1986) 436</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[6]</subfield>
      <subfield code="h">Amaldi et al</subfield>
      <subfield code="s">Phys. Rev D 36 (1987) 1385</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[6]</subfield>
      <subfield code="h">(Hayward and Yellow et al (ed.))</subfield>
      <subfield code="s">Phys. Lett B 245 (1990) 669</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[6]</subfield>
      <subfield code="s">Nucl. Phys B 342 (1990) 15</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[7]</subfield>
      <subfield code="h">Wallet et al</subfield>
      <subfield code="m">Some preceedings on Higgs</subfield>
      <subfield code="s">Phys. Rev. Lett. 44 (1980) 912</subfield>
      <subfield code="a">10.1007/s11172-006-0105-6;</subfield>
   </datafield>
   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">[7]</subfield>
      <subfield code="h">Pod I., C. Jennings, et al</subfield>
      <subfield code="m">Blah blah blah blah blah blah blah blah blah blah</subfield>
      <subfield code="s">Nucl. Phys B 342 (1990) 15</subfield>
   </datafield>"""
        out = self.extract_references(ex_mixed_lines)
        #Compare the recieved output with the expected references
        self.assertEqual(out, references_expected)

TEST_SUITE = make_test_suite(RefextractTest)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
