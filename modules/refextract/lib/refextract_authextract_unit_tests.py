# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2013 CERN.
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

__revision__ = "$Id$"

import unittest
import sys
import re
from invenio.config import CFG_TMPDIR, CFG_ETCDIR

try:
    #try local version first
    import refextract
except ImportError:
    #then get installed version
    print "Using installed refextract\n"
    import invenio.refextract

from invenio.testutils import make_test_suite, run_test_suite, nottest


# pylint: disable-msg=C0301

def setup_files(self):
    self.test_pdfname = CFG_TMPDIR + '/demoextract.pdf'
    self.test_txtname = CFG_TMPDIR + '/demoextract.txt'
    from os.path import exists, getsize
    if (not exists(self.test_pdfname) or getsize(self.test_pdfname) is 0):
        from urllib import urlretrieve
        urlretrieve('http://arxiv.org/pdf/0809.4120', self.test_pdfname)
    self.assert_( exists(self.test_pdfname) and getsize(self.test_pdfname) > 0)


@nottest
def set_test_cli_opts():
    refextract.cli_opts = { 'treat_as_raw_section'       : 0,
                            'output_raw'                 : 0,
                            'verbosity'                  : 1,
                            'xmlfile'


                            : 0,
                            'dictfile'                   : 0,
                            'authors'                    : 0,
                            'first_author'               : "",
    }




class RefExtractPDFTest(unittest.TestCase):
    """ refextract test pdf to text extraction"""

    def setUp(self):
        setup_files(self)
        set_test_cli_opts()


    @nottest
    def test_PDF_extraction(self):
        """ refextract test basic pdf extraction ---necessary for some remaining tests"""
        (docbody, extract_error) = refextract.get_plaintext_document_body(self.test_pdfname)
        self.assert_(len(docbody) > 10)
        self.assert_(len([1 for line in docbody if line.find('babar') > -1])>0)
        from codecs import open
        file = open(self.test_txtname, 'w', 'utf8')
        for line in docbody:
            file.write(line)
        file.close


class RefExtractExtractSectionTest(unittest.TestCase):
    """ refextract - test finding ref and auth sections """

    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize stuff"""
        setup_files(self)
        set_test_cli_opts
        file = open(self.test_txtname, 'r')
        self.textbody = []
        for line in file.readlines():
            self.textbody.append(line.decode("utf-8"))
        file.close()


    @nottest
    def test_reference_finding(self):
        """ find a reference section """
        (references, extract_error, how_start) = refextract.extract_section_from_fulltext(self.textbody,'references')
        self.assertEqual(extract_error, 0)
#        for line in references:
#           print "found -> %s\n" % line
        self.assertEqual(len(references), 17)


    @nottest
    def test_author_finding(self):
        """ find author section """

        (authors, extract_error, how_start) = refextract.extract_section_from_fulltext(self.textbody,'authors')
        for line in authors:
            print "%s" % line.encode("utf8")
        self.assertEqual(len(authors), 530)


class RefExtractAuthorParsingTest(unittest.TestCase):
    def setUp(self):
        self.authlines = [
            """B. Aubert,1"""
            ,"""M. Bona,1"""
            ,"""Y. Karyotakis,1"""
            ,"""J. P. Lees,1"""
            ,"""V. Poireau,1"""
            ,"""E. Prencipe,1"""
            ,"""X. Prudent,1"""
            ,"""V. Tisserand,1"""
            ,"""J. Garra Tico,2"""
            ,"""E. Grauges,2"""
            ,"""L. Lopezab
            """
            ,"""A. Palanoab
            """
            ,"""M. Pappagalloab
            """
            ,"""N. L. Blount,56"""
            ,"""J. Brau,56"""
            ,"""R. Frey,56"""
            ,"""O. Igonkina,56"""
            ,"""J. A. Kolb,56"""
            ,"""M. Lu,56"""
            ,"""R. Rahmat,56"""
            ,"""N. B. Sinev,56"""
            ,"""D. Strom,56"""
            ,"""J. Strube,56"""
            ,"""E. Torrence,56"""
            ,"""G. Castelliab
            """
            ,"""N. Gagliardiab
            """
            ,"""M. Margoniab
            """
            ,"""M. Morandina
            """
            ,"""M. Posoccoa
            """
            ,"""M. Rotondoa
            """
            ,"""F. Simonettoab
            """
            ,"""R. Stroiliab
            """
            ,"""C. Vociab
            """
            ,"""E. Ben"""
            ,"""H. Briand,58"""
            ,"""G. Calderini,58"""
            ,"""J. Chauveau,58"""
            ,"""P. David,58"""
            ,"""L. Del Buono,58"""
            ,"""O. Hamon,58"""
            ,"""J. Ocariz,58"""
            ,"""A. Perez,58"""
            ,"""J. Prendki,58"""
            ,"""S. Sitt,58"""
            ,"""L. Gladney,59"""
            ,"""M. Biasiniab
            """]


    @nottest
    def test_reference_parsing(self):
        """Use a hardcoded set of authors to test the parsing"""
        (processed_authors, count_author, \
         count_aff ) = \
         refextract.create_marc_xml_author_section(self.authlines)
        self.assert_(re.search('<subfield code=\"a\">Biasini, M.\s?</subfield>',processed_authors[44]))
        print processed_authors


class RefExtractReferenceParsingTest(unittest.TestCase):
    """ Test the parsing of reference strings """
    def setUp(self):
        self.reflines = ["""[1] <a href="http://cdsweb.cern.ch/">CERN Document Server</a> J. Maldacena, Adv. Theor. Math. Phys. 2 (1998) 231; hep-th/9711200. http://cdsweb.cern.ch/ then http://www.itp.ucsb.edu/online/susyc99/discussion/. ; L. Susskind, J. Math. Phys. 36 (1995) 6377; hep-th/9409089. hello world a<a href="http://uk.yahoo.com/">Yahoo!</a>. Fin.""",
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
                             """[36] whatever http://cdsware.cern.ch/""",
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
                         ]
        (self.title_search_kb, \
         self.title_search_standardised_titles, \
         self.title_search_keys) = \
         refextract.build_titles_knowledge_base(refextract.CFG_REFEXTRACT_KB_JOURNAL_TITLES)
        (self.preprint_reportnum_sre, \
         self.standardised_preprint_reportnum_categs) = \
         refextract.build_reportnum_knowledge_base(refextract.CFG_REFEXTRACT_KB_REPORT_NUMBERS)

    @nottest
    def test_reference_parsing(self):
        """Use a hardcoded set of refstrings to test the parsing"""
        (processed_references, count_misc, \
             count_title, count_reportnum, \
             count_url, count_doi, record_titles_count) = \
             refextract.create_marc_xml_reference_section(self.reflines,
                                                preprint_repnum_search_kb=\
                                                  self.preprint_reportnum_sre,
                                                preprint_repnum_standardised_categs=\
                                                  self.standardised_preprint_reportnum_categs,
                                                periodical_title_search_kb=\
                                                  self.title_search_kb,
                                                standardised_periodical_titles=\
                                                  self.title_search_standardised_titles,
                                                periodical_title_search_keys=\
                                                  self.title_search_keys)
        self.assertEqual(count_title, 56)
        self.assertEqual(count_reportnum, 45)






## FIXME: all the tests are disabled since they are no longer in sync
## with the current development of Invenio. We keep this file for reference
## in case we want to reimplement them
TEST_SUITE = make_test_suite(#RefExtractPDFTest,
                             #RefExtractExtractSectionTest,
                             #RefExtractAuthorParsingTest,
                             #RefExtractReferenceParsingTest,
                             )

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
