# -*- coding: utf-8 -*-
# Invenio elmsubmit unit tests.

# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2013 CERN.
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

"""Unit tests for the elmsubmit."""

__revision__ = "$Id$"


import os
from string import expandtabs
import xml.dom.minidom

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class ElmTestCase(InvenioTestCase):

    def setUp(self):
        from invenio.config import CFG_TMPDIR
        from invenio.legacy.elmsubmit import api as elmsubmit
        import invenio.legacy.elmsubmit.config as elmsubmit_config
        self.f1 = None
        if os.path.exists(elmsubmit_config.CFG_ELMSUBMIT_FILES['test_case_1']):
            self.f1 = open(elmsubmit_config.CFG_ELMSUBMIT_FILES['test_case_1'], 'r')

        self.f2 = None
        if os.path.exists(elmsubmit_config.CFG_ELMSUBMIT_FILES['test_case_2']):
            self.f2 = open(elmsubmit_config.CFG_ELMSUBMIT_FILES['test_case_2'], 'r')

        self.elmsubmit = elmsubmit

    def tearDown(self):
        if self.f1:
            self.f1.close()
        if self.f2:
            self.f2.close()


class MarcTest(ElmTestCase):
    """ elmsubmit - test for sanity """

    def test_simple_marc(self):
        """elmsubmit - parsing simple email"""
        if not self.f1:
            return

        email = self.f1.read()

        # let's try to parse an example email and compare it with the appropriate marc xml
        x = self.elmsubmit.process_email(email)
        y  = """<record>
        <datafield tag ="245" ind1="" ind2="">
        <subfield code="a">something</subfield>
        </datafield>
        <datafield tag ="100" ind1="" ind2="">
        <subfield code="a">Simko, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""

        # in order to properly compare the marc files we have to remove the FFT node, it includes a random generated file path

        dom_x = xml.dom.minidom.parseString(x)
        datafields = dom_x.getElementsByTagName("datafield")

        #remove all the FFT datafields
        for node in datafields:
            if (node.hasAttribute("tag") and  node.getAttribute("tag") == "FFT"):
                node.parentNode.removeChild(node)
                node.unlink()

        new_x = dom_x.toprettyxml("","\n")

        dom_y = xml.dom.minidom.parseString(y)
        new_y = dom_y.toprettyxml("","\n")

        # 'normalize' the two XML MARC files for the purpose of comparing
        new_x = expandtabs(new_x)
        new_y = expandtabs(new_y)

        new_x = new_x.replace(' ','')
        new_y = new_y.replace(' ','')

        new_x = new_x.replace('\n','')
        new_y = new_y.replace('\n','')

        # compare the two xml marcs
        self.assertEqual(new_x,new_y)

    def test_complex_marc(self):
        """elmsubmit - parsing complex email with multiple fields"""
        if not self.f2:
            return

        email = self.f2.read()

        # let's try to reproduce the demo XML MARC file by parsing it and printing it back:
        x = self.elmsubmit.process_email(email)
        y = """<record>
        <datafield tag ="245" ind1="" ind2="">
        <subfield code="a">something</subfield>
        </datafield>
        <datafield tag ="700" ind1="" ind2="">
        <subfield code="a">Le Meur, J Y</subfield>
        <subfield code="u">MIT</subfield>
        </datafield>
        <datafield tag ="700" ind1="" ind2="">
        <subfield code="a">Jedrzejek, K J</subfield>
        <subfield code="u">CERN2</subfield>
        </datafield>
        <datafield tag ="700" ind1="" ind2="">
        <subfield code="a">Favre, G</subfield>
        <subfield code="u">CERN3</subfield>
        </datafield>
        <datafield tag ="111" ind1="" ind2="">
        <subfield code="a">test11</subfield>
        <subfield code="c">test31</subfield>
        </datafield>
        <datafield tag ="111" ind1="" ind2="">
        <subfield code="a">test12</subfield>
        <subfield code="c">test32</subfield>
        </datafield>
        <datafield tag ="111" ind1="" ind2="">
        <subfield code="a">test13</subfield>
        <subfield code="c">test33</subfield>
        </datafield>
        <datafield tag ="111" ind1="" ind2="">
        <subfield code="b">test21</subfield>
        <subfield code="d">test41</subfield>
        </datafield>
        <datafield tag ="111" ind1="" ind2="">
        <subfield code="b">test22</subfield>
        <subfield code="d">test42</subfield>
        </datafield>
        <datafield tag ="111" ind1="" ind2="">
        <subfield code="a">test14</subfield>
        </datafield>
        <datafield tag ="111" ind1="" ind2="">
        <subfield code="e">test51</subfield>
        </datafield>
        <datafield tag ="111" ind1="" ind2="">
        <subfield code="e">test52</subfield>
        </datafield>
        <datafield tag ="100" ind1="" ind2="">
        <subfield code="a">Simko, T</subfield>
        <subfield code="u">CERN</subfield>
        </datafield>
        </record>"""

        # in order to properly compare the marc files we have to remove the FFT node, it includes a random generated file path

        dom_x = xml.dom.minidom.parseString(x)
        datafields = dom_x.getElementsByTagName("datafield")

        #remove all the FFT datafields
        for node in datafields:
            if (node.hasAttribute("tag") and  node.getAttribute("tag") == "FFT"):
                node.parentNode.removeChild(node)
                node.unlink()


        new_x = dom_x.toprettyxml("","\n")

        dom_y = xml.dom.minidom.parseString(y)
        new_y = dom_y.toprettyxml("","\n")
        # 'normalize' the two XML MARC files for the purpose of comparing
        new_x = expandtabs(new_x)
        new_y = expandtabs(new_y)

        new_x = new_x.replace(' ','')
        new_y = new_y.replace(' ','')

        new_x = new_x.replace('\n','')
        new_y = new_y.replace('\n','')

        # compare the two xml marcs
        self.assertEqual(new_x,new_y)


class FileStorageTest(ElmTestCase):
    """ testing proper storage of files """

    def test_read_text_files(self):
        """elmsubmit - reading text files"""
        if not self.f2:
            return

        email = self.f2.read()

        # let's try to see if the files were properly stored:
        xml_marc = self.elmsubmit.process_email(email)

        dom = xml.dom.minidom.parseString(xml_marc)
        datafields = dom.getElementsByTagName("datafield")

        # get the file addresses
        file_list = []

        for node in datafields:
            if (node.hasAttribute("tag") and  node.getAttribute("tag") == "FFT"):
                children = node.childNodes
                for child in children:
                    if (child.hasChildNodes()):
                        file_list.append(child.firstChild.nodeValue)

        f=open(file_list[0], 'r')
        x = f.read()
        f.close()

        x.lstrip()
        x.rstrip()

        y = """second attachment\n"""

        self.assertEqual(x,y)

        f=open(file_list[1], 'r')
        x = f.read()
        f.close()

        x.lstrip()
        x.rstrip()

        y = """some attachment\n"""
        self.assertEqual(x,y)

TEST_SUITE = make_test_suite(MarcTest,
                             FileStorageTest,)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
