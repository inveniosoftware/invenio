# -*- coding: utf-8 -*-
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

"""WebSearch module regression tests."""

__revision__ = "$Id$"

import unittest

from invenio.config import weburl, cdslang
from invenio.testutils import make_test_suite, \
                              warn_user_about_tests_and_run, \
                              test_web_page_content
from invenio.bibformat import format_record

class BibFormatAPITest(unittest.TestCase):
    """Check BibFormat API"""

    def test_basic_formatting(self):
        """bibformat - Checking BibFormat API"""
        result = format_record(recID=73,
                               of='hx',
                               ln=cdslang,
                               verbose=0,
                               search_pattern=[],
                               xml_record=None,
                               uid=None,
                               on_the_fly=True)

        pageurl = weburl + '/record/73?of=hx'
        result = test_web_page_content(pageurl,
                                       expected_text=result)

class BibFormatBibTeXTest(unittest.TestCase):
    """Check output produced by BibFormat for BibTeX output for
    various records"""

    def setUp(self):
        """Prepare some ideal outputs"""
        self.record_74_hx = '''<pre>
@article{Wang:74,
      author       = "Wang, B and Lin, C Y and Abdalla, E",
      title        = "Quasinormal modes of Reissner-Nordstrom Anti-de Sitter
                      Black Holes",
      journal      = "Phys. Lett., B",
      number       = "hep-th/0003295",
      volume       = "481",
      pages        = "79-88",
      year         = "2000",
}
</pre>'''

    def test_bibtex_output(self):
        """bibformat - BibTeX output"""

        pageurl = weburl + '/record/74?of=hx'
        result = test_web_page_content(pageurl,
                                       expected_text=self.record_74_hx)
        self.assertEqual([], result)

class BibFormatDetailedHTMLTest(unittest.TestCase):
    """Check output produced by BibFormat for detailed HTML ouput for
    various records"""

    def setUp(self):
        """Prepare some ideal outputs"""

        # Record 7 (Article)
        self.record_74_hd_header = '''<table border="0" width="100%">
      <tr>
        <td>Published Article<small> / Particle Physics - Theory</small></td>
        <td><small><strong></strong></small></td>
        <td align="right"><strong>hep-th/0003295</strong></td>
      </tr>
    </table>'''

        self.record_74_hd_title = '''<center><big><big><strong>Quasinormal modes of Reissner-Nordstrom Anti-de Sitter Black Holes</strong></big></big></center>'''

        self.record_74_hd_authors = '''<a href="%(weburl)s/search?f=author&amp;p=Wang%%2C%%20B&amp;ln=%(lang)s">Wang, B</a> ; <a href="%(weburl)s/search?f=author&amp;p=Lin%%2C%%20C%%20Y&amp;ln=%(lang)s">Lin, C Y</a> ; <a href="%(weburl)s/search?f=author&amp;p=Abdalla%%2C%%20E&amp;ln=%(lang)s">Abdalla, E</a><br />'''% \
                                     {'weburl' : weburl,
                                      'lang': cdslang}

        self.record_74_hd_abstract = '''<small><strong>Abstract: </strong>Complex frequencies associated with quasinormal modes for large Reissner-Nordstr$\ddot{o}$m Anti-de Sitter black holes have been computed. These frequencies have close relation to the black hole charge and do not linearly scale withthe black hole temperature as in Schwarzschild Anti-de Sitter case. In terms of AdS/CFT correspondence, we found that the bigger the black hole charge is, the quicker for the approach to thermal equilibrium in the CFT. The propertiesof quasinormal modes for $l&gt;0$ have also been studied.</small><br />'''

        self.record_74_hd_pubinfo = '''<strong>Published in: </strong><a href="http://weblib.cern.ch/cgi-bin/ejournals?publication=Phys.%20Lett.%2C%20B&amp;volume=481&amp;year=2000&amp;page=79">Phys. Lett., B :481 2000 79-88</a>'''

        self.record_74_hd_fulltext = '''0003295.pdf"><img style="border:none"'''

        self.record_74_hd_citations = '''<strong>Cited by:</strong> try citation search for <a href="%(weburl)s/search?f=reference&amp;p=hep-th/0003295&amp;ln=%(lang)s">hep-th/0003295</a>'''% \
                                      {'weburl' : weburl,
                                       'lang': cdslang}
        self.record_74_hd_references = '''<li><small>[17]</small> <small>A. Chamblin, R. Emparan, C. V. Johnson and R. C. Myers, Phys. Rev., D60: 104026 (1999) 5070 90 110 130 150 r+ 130 230 330 50 70 90 110 130 150 r+</small> </li>'''

        # Record 7 (Picture)
        self.record_7_hd_header = '''<table border="0" width="100%">
      <tr>
        <td>Pictures<small> / Life at CERN</small></td>
        <td><small><strong></strong></small></td>
        <td align="right"><strong>CERN-GE-9806033</strong></td>
      </tr>
    </table>'''

        self.record_7_hd_title = '''<center><big><big><strong>Tim Berners-Lee</strong></big></big></center>'''

        self.record_7_hd_date = '''<center>28 Jun 1998</center>'''

        self.record_7_hd_abstract = '''<p><span class="blocknote">
 Caption</span><br /> <small>Conference "Internet, Web, What's next?" on 26 June 1998 at CERN : Tim Berners-Lee, inventor of the World-Wide Web and Director of the W3C, explains how the Web came to be and give his views on the future.</small></p><p><span class="blocknote">
 Légende</span><br /><small>Conference "Internet, Web, What's next?" le 26 juin 1998 au CERN: Tim Berners-Lee, inventeur du World-Wide Web et directeur du W3C, explique comment le Web est ne, et donne ses opinions sur l'avenir.</small></p>'''
        self.record_7_hd_resource = '''<img src="%s/record/7/files/icon-9806033.gif" alt="" /><br /><font size="-2"><b>© CERN Geneva</b></font>''' % weburl
        self.record_7_hd_resource_link = '%s/record/7/files/9806033.jpeg' %  weburl

    def test_detailed_html_output(self):
        """bibformat - Detailed HTML output"""

        # Test record 74 (Article)
        pageurl = weburl + '/record/74?of=hd'
        result = test_web_page_content(pageurl,
                                       expected_text=[self.record_74_hd_header,
                                                      self.record_74_hd_title,
                                                      self.record_74_hd_authors,
                                                      self.record_74_hd_abstract,
                                                      self.record_74_hd_pubinfo,
                                                      self.record_74_hd_fulltext,
                                                      #self.record_74_hd_citations,
                                                      #self.record_74_hd_references
                                                      ])
        self.assertEqual([], result)

        # Test record 7 (Picture)
        pageurl = weburl + '/record/7?of=hd'
        result = test_web_page_content(pageurl,
                                       expected_text=[self.record_7_hd_header,
                                                      self.record_7_hd_title,
                                                      self.record_7_hd_date,
                                                      self.record_7_hd_abstract,
                                                      self.record_7_hd_resource,
                                                      self.record_7_hd_resource_link])
        self.assertEqual([], result)

    def test_detailed_html_edit_record(self):
        """bibformat - Detailed HTML output edit record link presence"""
        pageurl = weburl + '/record/74?of=hd'
        result = test_web_page_content(pageurl, username='admin',
                                       expected_text="Edit This Record")
        self.assertEqual([], result)

    def test_detailed_html_no_error_message(self):
        """bibformat - Detailed HTML output without error message"""
        # No error message should be displayed in the web interface, whatever happens
        pageurl = weburl + '/record/74?of=hd'
        result = test_web_page_content(pageurl, username='admin',
                                       expected_text=["Exception",
                                                      "Could not"])
        self.assertNotEqual([], result)

        pageurl = weburl + '/record/7?of=hd'
        result = test_web_page_content(pageurl, username='admin',
                                       expected_text=["Exception",
                                                      "Could not"])
        self.assertNotEqual([], result)

class BibFormatNLMTest(unittest.TestCase):
    """Check output produced by BibFormat for NLM output for various
    records"""

    def setUp(self):
        """Prepare some ideal outputs"""
        self.record_70_xn = '''<?xml version="1.0" encoding="UTF-8"?>
<articles>
<article xmlns:xlink="http://www.w3.org/1999/xlink/">
  <front>
    <journal-meta>
      <journal-title>J. High Energy Phys.</journal-title>
      <abbrev-journal-title>J. High Energy Phys.</abbrev-journal-title>
      <issn>1126-6708</issn>
    </journal-meta>
    <article-meta>
      <title-group>
        <article-title>AdS/CFT For Non-Boundary Manifolds</article-title>
      </title-group>
      <contrib-group>
        <contrib contrib-type="author">
          <name>
            <surname>McInnes</surname>
            <given-names>B</given-names>
          </name>
        </contrib>
      </contrib-group>
      <pub-date pub-type="pub">
        <year>2000</year>
      </pub-date>
      <volume>05</volume>
      <fpage/>
      <lpage/>
      <self-uri xlink:href="%(weburl)s/record/70"/>
      <self-uri xlink:href="%(weburl)s/record/70/files/0003291.pdf"/>
      <self-uri xlink:href="%(weburl)s/record/70/files/0003291.ps.gz"/>
    </article-meta>
    <abstract>In its Euclidean formulation, the AdS/CFT correspondence begins as a study of Yang-Mills conformal field theories on the sphere, S^4. It has been successfully extended, however, to S^1 X S^3 and to the torus T^4. It is natural tohope that it can be made to work for any manifold on which it is possible to define a stable Yang-Mills conformal field theory. We consider a possible classification of such manifolds, and show how to deal with the most obviousobjection : the existence of manifolds which cannot be represented as boundaries. We confirm Witten's suggestion that this can be done with the help of a brane in the bulk.</abstract>
  </front>
  <article-type>research-article</article-type>
  <ref/>
</article>

</articles>''' % {'weburl': weburl}

    def test_nlm_output(self):
        """bibformat - NLM output"""

        pageurl = weburl + '/record/70?of=xn'
        result = test_web_page_content(pageurl,
                                       expected_text=self.record_70_xn)
        self.assertEqual([], result)

class BibFormatBriefHTMLTest(unittest.TestCase):
    """Check output produced by BibFormat for brief HTML ouput for
    various records"""

    def setUp(self):
        """Prepare some ideal outputs"""

        self.record_76_hb = '''<strong>Ιθάκη</strong>
 / <a href="%s/search?f=author&amp;p=%%CE%%9A%%CE%%B1%%CE%%B2%%CE%%AC%%CF%%86%%CE%%B7%%CF%%82%%2C%%20%%CE%%9A%%20%%CE%%A0&amp;ln=%s">Καβάφης, Κ Π</a>





<br /><small>
Σα βγεις στον πηγαιμό για την Ιθάκη,<br />
να εύχεσαι νάναι μακρύς ο δρόμος,<br />
γεμάτος περιπέτειες, γεμάτος γνώσεις [...] </small>''' % (weburl, cdslang)


    def test_brief_html_output(self):
        """bibformat - Brief HTML output"""
        pageurl = weburl + '/record/76?of=HB'
        result = test_web_page_content(pageurl,
                                       expected_text=self.record_76_hb)
        self.assertEqual([], result)

class BibFormatMARCXMLTest(unittest.TestCase):
    """Check output produced by BibFormat for MARCXML ouput for various records"""

    def setUp(self):
        """Prepare some ideal outputs"""

        self.record_9_xm = '''<?xml version="1.0" encoding="UTF-8"?>
<collection xmlns="http://www.loc.gov/MARC21/slim">
<record>
  <controlfield tag="001">9</controlfield>
  <datafield tag="041" ind1=" " ind2=" ">
    <subfield code="a">eng</subfield>
 </datafield>
  <datafield tag="088" ind1=" " ind2=" ">
    <subfield code="a">PRE-25553</subfield>
 </datafield>
  <datafield tag="088" ind1=" " ind2=" ">
    <subfield code="a">RL-82-024</subfield>
 </datafield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Ellis, J</subfield>
 </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">Grand unification with large supersymmetry breaking</subfield>
 </datafield>
  <datafield tag="260" ind1=" " ind2=" ">
    <subfield code="c">Mar 1982</subfield>
 </datafield>
  <datafield tag="300" ind1=" " ind2=" ">
    <subfield code="a">18 p</subfield>
 </datafield>
  <datafield tag="650" ind1="1" ind2="7">
    <subfield code="2">SzGeCERN</subfield>
    <subfield code="a">General Theoretical Physics</subfield>
 </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Ibanez, L E</subfield>
 </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Ross, G G</subfield>
 </datafield>
  <datafield tag="909" ind1="C" ind2="0">
    <subfield code="y">1982</subfield>
 </datafield>
  <datafield tag="909" ind1="C" ind2="0">
    <subfield code="b">11</subfield>
 </datafield>
  <datafield tag="909" ind1="C" ind2="1">
    <subfield code="u">Oxford Univ.</subfield>
 </datafield>
  <datafield tag="909" ind1="C" ind2="1">
    <subfield code="u">Univ. Auton. Madrid</subfield>
 </datafield>
  <datafield tag="909" ind1="C" ind2="1">
    <subfield code="u">Rutherford Lab.</subfield>
 </datafield>
  <datafield tag="909" ind1="C" ind2="1">
    <subfield code="c">1990-01-28</subfield>
    <subfield code="l">50</subfield>
    <subfield code="m">2002-01-04</subfield>
    <subfield code="o">BATCH</subfield>
 </datafield>
  <datafield tag="909" ind1="C" ind2="S">
    <subfield code="s">h</subfield>
    <subfield code="w">1982n</subfield>
 </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">PREPRINT</subfield>
 </datafield>
</record>
</collection>'''

    def test_marcxml_output(self):
        """bibformat - MARCXML output"""
        pageurl = weburl + '/record/9?of=xm'
        result = test_web_page_content(pageurl,
                                       expected_text=self.record_9_xm)
        self.assertEqual([], result)

class BibFormatMARCTest(unittest.TestCase):
    """Check output produced by BibFormat for MARC ouput for various
    records"""

    def setUp(self):
        """Prepare some ideal outputs"""

        self.record_29_hm = '''000000029 001__ 29
000000029 041__ $$aeng
000000029 080__ $$a517.11
000000029 100__ $$aKleene, Stephen Cole
000000029 245__ $$aIntroduction to metamathematics
000000029 260__ $$aAmsterdam$$bNorth-Holland$$c1952 (repr.1964.)
000000029 300__ $$a560 p
000000029 490__ $$aBibl. Matematica$$v1
000000029 909C0 $$y1952
000000029 909C0 $$b21
000000029 909C1 $$c1990-01-27$$l00$$m2002-04-12$$oBATCH
000000029 909CS $$sm$$w198606
000000029 980__ $$aBOOK'''

    def test_marc_output(self):
        """bibformat - MARC output"""

        pageurl = weburl + '/record/29?of=hm'
        result = test_web_page_content(pageurl,
                                       expected_text=self.record_29_hm)
        self.assertEqual([], result)

class BibFormatTitleFormattingTest(unittest.TestCase):
    """Check title formatting produced by BibFormat."""

    def test_subtitle_in_html_brief(self):
        """bibformat - title subtitle in HTML brief formats"""
	self.assertEqual([],
          test_web_page_content(weburl + '/search?p=statistics+computer',
            expected_text="Statistics: a computer approach"))

    def test_subtitle_in_html_detailed(self):
        """bibformat - title subtitle in HTML detailed formats"""
	self.assertEqual([],
          test_web_page_content(weburl + '/search?p=statistics+computer&of=HD',
            expected_text="Statistics: a computer approach"))

    def test_title_edition_in_html_brief(self):
        """bibformat - title edition in HTML brief formats"""
	self.assertEqual([],
          test_web_page_content(weburl + '/search?p=2nd',
            expected_text="Introductory statistics: a decision map; 2nd ed"))

    def test_title_edition_in_html_detailed(self):
        """bibformat - title edition in HTML detailed formats"""
	self.assertEqual([],
          test_web_page_content(weburl + '/search?p=2nd&of=HD',
            expected_text="Introductory statistics: a decision map; 2nd ed"))

test_suite = make_test_suite(BibFormatBibTeXTest,
                             BibFormatDetailedHTMLTest,
                             BibFormatBriefHTMLTest,
                             BibFormatNLMTest,
                             BibFormatMARCTest,
                             BibFormatMARCXMLTest,
                             BibFormatAPITest,
                             BibFormatTitleFormattingTest)

if __name__ == "__main__":
    warn_user_about_tests_and_run(test_suite)

