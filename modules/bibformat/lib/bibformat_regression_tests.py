# -*- coding: utf-8 -*-
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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
        self.record_74_hd = '''<table border="0" width="100%%"><tr class="blocknote"><td valign="left">
    Published Article
    <small> / Particle Physics - Theory</small></td><td align="right"><strong>hep-th/0003295</strong></td></tr></table><br> 
<center><big><big><strong>Quasinormal modes of Reissner-Nordstrom Anti-de Sitter Black Holes</strong></big></big></center> 
<p><center>
<a href="%(weburl)s/search?f=author&amp;p=Wang%%2C%%20B&amp;ln=%(lang)s">Wang, B</a> ; <a href="%(weburl)s/search?f=author&amp;p=Lin%%2C%%20C%%20Y&amp;ln=%(lang)s">Lin, C Y</a> ; <a href="%(weburl)s/search?f=author&amp;p=Abdalla%%2C%%20E&amp;ln=%(lang)s">Abdalla, E</a><br/>






</center></p>

<p style="margin-left: 15%%; width: 70%%">

<small><strong>Abstract: </strong>Complex frequencies associated with quasinormal modes for large Reissner-Nordstr$\ddot{o}$m Anti-de Sitter black holes have been computed. These frequencies have close relation to the black hole charge and do not linearly scale withthe black hole temperature as in Schwarzschild Anti-de Sitter case. In terms of AdS/CFT correspondence, we found that the bigger the black hole charge is, the quicker for the approach to thermal equilibrium in the CFT. The propertiesof quasinormal modes for $l&gt;0$ have also been studied.</small><br/>





<br/><br/><strong>Published in: </strong><a href="http://weblib.cern.ch/cgi-bin/ejournals?publication=Phys.%%20Lett.%%2C%%20B&amp;volume=481&amp;year=2000&amp;page=79">Phys. Lett., B :481 2000 79-88</a>
<br/>
<br/><strong>Fulltext : </strong><small><a  href="http://documents.cern.ch/cgi-bin/setlink?base=preprint&amp;categ=hep-th&amp;id=0003295">http://documents.cern.ch/cgi-bin/setlink?base=preprint&amp;categ=hep-th&amp;id=0003295</a></small>
<br/><br/><strong>Cited by:</strong> try citation search for <a href="%(weburl)s/search?f=reference&p=hep-th/0003295&amp;ln=%(lang)s">hep-th/0003295</a>
</p> 
<blockquote><strong>References:</strong><ul><li><small>[1]</small> <small>K. D. Kokkotas, B. G. Schmidt</small> <small> [<a href="%(weburl)s/search?f=reportnumber&amp;p=gr-qc/9909058&amp;ln=%(lang)s">gr-qc/9909058</a>] </small> <br/><small>and references therein</small> <li><small>[2]</small> <small>W. Krivan</small>  <small> <a href="http://weblib.cern.ch/cgi-bin/ejournals?publication=Phys.+Rev.,+D&amp;volume=60&amp;year=1999&amp;page=101501">Phys. Rev., D: 60 (1999) 101501</a> </small> <br/><li><small>[3]</small> <small>S. Hod</small> <small> [<a href="%(weburl)s/search?f=reportnumber&amp;p=gr-qc/9902072&amp;ln=%(lang)s">gr-qc/9902072</a>] </small> <br/><li><small>[4]</small> <small>P. R. Brady, C. M. Chambers, W. G. Laarakkers and E. Poisson</small>  <small> <a href="http://weblib.cern.ch/cgi-bin/ejournals?publication=Phys.+Rev.,+D&amp;volume=60&amp;year=1999&amp;page=064003">Phys. Rev., D: 60 (1999) 064003</a> </small> <br/><li><small>[5]</small> <small>P. R. Brady, C. M. Chambers, W. Krivan and P. Laguna</small>  <small> <a href="http://weblib.cern.ch/cgi-bin/ejournals?publication=Phys.+Rev.,+D&amp;volume=55&amp;year=1997&amp;page=7538">Phys. Rev., D: 55 (1997) 7538</a> </small> <br/><li><small>[6]</small> <small>G. T. Horowitz and V. E. Hubeny</small> <small> [<a href="%(weburl)s/search?f=reportnumber&amp;p=hep-th/9909056&amp;ln=%(lang)s">hep-th/9909056</a>] </small> <br/><small>G. T. Horowitz</small> <small> [<a href="%(weburl)s/search?f=reportnumber&amp;p=hep-th/9910082&amp;ln=%(lang)s">hep-th/9910082</a>] </small> <br/><li><small>[7]</small> <small>E. S. C. Ching, P. T. Leung, W. M. Suen and K. Young</small>  <small> <a href="http://weblib.cern.ch/cgi-bin/ejournals?publication=Phys.+Rev.,+D&amp;volume=52&amp;year=1995&amp;page=2118">Phys. Rev., D: 52 (1995) 2118</a> </small> <br/><li><small>[8]</small> <small>J. M. Maldacena</small>  <small> Adv. Theor. Math. Phys.21998231 </small> <br/><li><small>[9]</small> <small>E. Witten</small>  <small> Adv. Theor. Math. Phys.21998253 </small> <br/><li><small>[10]</small> <small>S. S. Gubser, I. R. Klebanov and A. M. Polyakov</small>  <small> <a href="http://weblib.cern.ch/cgi-bin/ejournals?publication=Phys.+Lett.,+B&amp;volume=428&amp;year=1998&amp;page=105">Phys. Lett., B: 428 (1998) 105</a> </small> <br/><li><small>[11]</small> <small>A. Chamblin, R. Emparan, C. V. Johnson and R. C. Myers</small>  <small> <a href="http://weblib.cern.ch/cgi-bin/ejournals?publication=Phys.+Rev.,+D&amp;volume=60&amp;year=1999&amp;page=064018">Phys. Rev., D: 60 (1999) 064018</a> </small> <br/><li><small>[12]</small> <small>E. W. Leaver</small>  <small> <a href="http://weblib.cern.ch/cgi-bin/ejournals?publication=J.+Math.+Phys.&amp;volume=27&amp;year=1986&amp;page=1238">J. Math. Phys.: 27 (1986) 1238</a> </small> <br/><li><small>[13]</small> <small>E. W. Leaver</small>  <small> <a href="http://weblib.cern.ch/cgi-bin/ejournals?publication=Phys.+Rev.,+D&amp;volume=41&amp;year=1990&amp;page=2986">Phys. Rev., D: 41 (1990) 2986</a> </small> <br/><li><small>[14]</small> <small>C. O. Lousto</small>  <small> <a href="http://weblib.cern.ch/cgi-bin/ejournals?publication=Phys.+Rev.,+D&amp;volume=51&amp;year=1995&amp;page=1733">Phys. Rev., D: 51 (1995) 1733</a> </small> <br/><li><small>[15]</small> <small>O. Kaburaki</small>  <small> <a href="http://weblib.cern.ch/cgi-bin/ejournals?publication=Phys.+Lett.,+A&amp;volume=217&amp;year=1996&amp;page=316">Phys. Lett., A: 217 (1996) 316</a> </small> <br/><li><small>[16]</small> <small>R. K. Su, R. G. Cai and P. K. N. Yu</small>  <small> <a href="http://weblib.cern.ch/cgi-bin/ejournals?publication=Phys.+Rev.,+D&amp;volume=50&amp;year=1994&amp;page=2932">Phys. Rev., D: 50 (1994) 2932</a> </small> <br/> <small> <a href="http://weblib.cern.ch/cgi-bin/ejournals?publication=Phys.+Rev.,+D&amp;volume=48&amp;year=1993&amp;page=3473">Phys. Rev., D: 48 (1993) 3473</a> </small> <br/> <small> <a href="http://weblib.cern.ch/cgi-bin/ejournals?publication=Phys.+Rev.,+D&amp;volume=52&amp;year=1995&amp;page=6186">Phys. Rev., D: 52 (1995) 6186</a> </small> <br/><small>B. Wang, J. M. Zhu</small>  <small> Mod. Phys. Lett., A1019951269 </small> <br/><li><small>[17]</small> <small>A. Chamblin, R. Emparan, C. V. Johnson and R. C. Myers, Phys. Rev., D60: 104026 (1999) 5070 90 110 130 150 r+ 130 230 330 50 70 90 110 130 150 r+</small> </ul><p><small><i><b>Warning</b>: references are automatically extracted and standardized from the PDF document and may therefore contain errors. If you think they are incorrect or incomplete, look at the fulltext document itself.<br></i></small></blockquote>
</p>''' % {'weburl' : weburl,
           'lang': cdslang}

        self.record_7_hd = '''<table border="0" width="100%"><tr class="blocknote"><td valign="left">
    Pictures
    <small> / Life at CERN</small></td><td align="right"><strong>CERN-GE-9806033</strong></td></tr></table><br>
<center><big><big><strong>Tim Berners-Lee</strong></big></big></center> 


<center>28 Jun 1998</center>

<center>



</center>
<br/>



<table> <tr>
<td valign="top" align="left"> 



<p><table><tr><td class="blocknote"> 
 Caption</td></tr></table> <small>Conference "Internet, Web, What's next?" on 26 June 1998 at CERN : Tim Berners-Lee, inventor of the World-Wide Web and Director of the W3C, explains how the Web came to be and give his views on the future.</small></p><p><table><tr><td class="blocknote">  
 Légende</td></tr></table><small>Conference "Internet, Web, What's next?" le 26 juin 1998 au CERN: Tim Berners-Lee, inventeur du World-Wide Web et directeur du W3C, explique comment le Web est ne, et donne ses opinions sur l'avenir.</small></p>

<p><table><tr><td class="blocknote">See also:</td></tr></table><small><a href="http://www.cern.ch/CERN/Announcements/1998/WebNext.html">"Internet, Web, What's next?" 26 June 1998</a><br/><a href="http://Bulletin.cern.ch/9828/art2/Text_E.html">CERN Bulletin no 28/98 (6 July 1998) (English)</a><br/><a href="http://Bulletin.cern.ch/9828/art2/Text_F.html">CERN Bulletin no 28/98 (6 juillet 1998) (French)</a><br/><a href="http://www.w3.org/People/Berners-Lee/">Biography</a></small></p>

</td>

<td valign="top">
<table><tr><td class="blocknote">Resources</td></tr></table><br/>High resolution: <a href="http://preprints.cern.ch/cgi-bin/setlink?base=PHO&categ=photo-ge&id=9806033">http://preprints.cern.ch/cgi-bin/setlink?base=PHO&categ=photo-ge&id=9806033</a><br/><br/><img src="http://preprints.cern.ch/photo/photo-ge/9806033.gif" alt=""/><br/><font size=-2><b>© CERN Geneva</b></font><br/> <a href=""></a>
</td> 

</tr>

<tr><td colspan="2" class="blocknote">
 <strong>© CERN Geneva: </strong>
<small>The use of photos requires prior authorization (from <a href="http://cern.ch/cern-copyright/">CERN copyright</a>). 
The words CERN Photo must be quoted for each use. </small>
</td>
</tr>

</table>'''
    
    def test_detailed_html_output(self):
        """bibformat - Detailed HTML output""" 

        # Test record 74 (Article)
        pageurl = weburl + '/record/74?of=hd'
        result = test_web_page_content(pageurl,
                                       expected_text=self.record_74_hd)
        self.assertEqual([], result)

        # Test record 7 (Picture)
        pageurl = weburl + '/record/7?of=hd'
        result = test_web_page_content(pageurl,
                                       expected_text=self.record_7_hd)
        self.assertEqual([], result)

class BibFormatNLMTest(unittest.TestCase):
    """Check output produced by BibFormat for NLM output for various
    records"""

    def setUp(self):
        """Prepare some ideal outputs"""
        self.record_70_xn = '''<?xml version="1.0" encoding="UTF-8"?>
<articles>
<article><front><journal-meta><journal-title>J. High Energy Phys.</journal-title><abbrev-journal-title>J. High Energy Phys.</abbrev-journal-title><issn>1126-6708</issn></journal-meta><article-meta><title-group><article-title>AdS/CFT For Non-Boundary Manifolds</article-title></title-group><contrib-group><contrib contrib-type="author"><name><surname>McInnes</surname><given-names>B</given-names></name></contrib></contrib-group><pub-date pub-type="pub"><year>2000</year></pub-date><volume>05</volume><fpage></fpage><lpage></lpage><self-uri xlink:href="%s/record/70" xmlns:xlink="http://www.w3.org/1999/xlink/"/><self-uri xlink:href="http://documents.cern.ch/cgi-bin/setlink?base=preprint&amp;categ=hep-th&amp;id=0003291" xmlns:xlink="http://www.w3.org/1999/xlink/" /></article-meta><abstract>In its Euclidean formulation, the AdS/CFT correspondence begins as a study of Yang-Mills conformal field theories on the sphere, S^4. It has been successfully extended, however, to S^1 X S^3 and to the torus T^4. It is natural tohope that it can be made to work for any manifold on which it is possible to define a stable Yang-Mills conformal field theory. We consider a possible classification of such manifolds, and show how to deal with the most obviousobjection : the existence of manifolds which cannot be represented as boundaries. We confirm Witten's suggestion that this can be done with the help of a brane in the bulk.</abstract></front><article-type>research-article</article-type><ref></ref></article>
    

</articles>''' % weburl
      
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





<br/><small>
Σα βγεις στον πηγαιμό για την Ιθάκη,<br />
να εύχεσαι νάναι μακρύς ο δρόμος,<br />
γεμάτος περιπέτειες, γεμάτος γνώσεις. [...] </small>''' % (weburl, cdslang)

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

test_suite = make_test_suite(BibFormatBibTeXTest,
                             BibFormatDetailedHTMLTest,
                             BibFormatBriefHTMLTest,
                             BibFormatNLMTest,
                             BibFormatMARCTest,
                             BibFormatMARCXMLTest,
                             BibFormatAPITest)


if __name__ == "__main__":
    warn_user_about_tests_and_run(test_suite)
    
