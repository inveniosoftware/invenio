# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""Test cases for the BibFormat engine. Also test
some utilities function in bibformat_utils module"""

__revision__ = "$Id$"

# pylint: disable=C0301

import unittest
import os
import sys

from invenio import bibformat
from invenio import bibformat_engine
from invenio import bibformat_utils
from invenio import bibformat_config
from invenio import bibformatadminlib
from invenio.config import CFG_TMPDIR
from invenio.testutils import make_test_suite, run_test_suite

#CFG_BIBFORMAT_OUTPUTS_PATH = "..%setc%soutput_formats" % (os.sep, os.sep)
#CFG_BIBFORMAT_TEMPLATES_PATH = "..%setc%sformat_templates" % (os.sep, os.sep)
#CFG_BIBFORMAT_ELEMENTS_PATH = "elements"
CFG_BIBFORMAT_OUTPUTS_PATH = "%s" % (CFG_TMPDIR)
CFG_BIBFORMAT_TEMPLATES_PATH = "%s" % (CFG_TMPDIR)
CFG_BIBFORMAT_ELEMENTS_PATH = "%s%stests_bibformat_elements" % (CFG_TMPDIR, os.sep)
CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH = "tests_bibformat_elements"

class FormatTemplateTest(unittest.TestCase):
    """ bibformat - tests on format templates"""

    def test_get_format_template(self):
        """bibformat - format template parsing and returned structure"""

        bibformat_engine.CFG_BIBFORMAT_TEMPLATES_PATH = CFG_BIBFORMAT_TEMPLATES_PATH

        #Test correct parsing and structure
        template_1 = bibformat_engine.get_format_template("Test1.bft", with_attributes=True)
        self.assert_(template_1 is not None)
        self.assertEqual(template_1['code'],  "test\n<name>this value should stay as it is</name>\n<description>this one too</description>\n")
        self.assertEqual(template_1['attrs']['name'], "name_test")
        self.assertEqual(template_1['attrs']['description'], "desc_test")

        #Test correct parsing and structure of file without description or name
        template_2 = bibformat_engine.get_format_template("Test_2.bft", with_attributes=True)
        self.assert_(template_2 is not None)
        self.assertEqual(template_2['code'],  "test")
        self.assertEqual(template_2['attrs']['name'], "Test_2.bft")
        self.assertEqual(template_2['attrs']['description'], "")

        #Test correct parsing and structure of file without description or name
        unknown_template = bibformat_engine.get_format_template("test_no_template.test", with_attributes=True)
        self.assertEqual(unknown_template,  None)


    def test_get_format_templates(self):
        """ bibformat - loading multiple format templates"""
        bibformat_engine.CFG_BIBFORMAT_TEMPLATES_PATH = CFG_BIBFORMAT_TEMPLATES_PATH

        templates = bibformat_engine.get_format_templates(with_attributes=True)
        #test correct loading
        self.assert_("Test1.bft" in templates.keys())
        self.assert_("Test_2.bft" in templates.keys())
        self.assert_("Test3.bft" in templates.keys())
        self.assert_("Test_no_template.test" not in templates.keys())

        #Test correct pasrsing and structure
        self.assertEqual(templates['Test1.bft']['code'],  "test\n<name>this value should stay as it is</name>\n<description>this one too</description>\n")
        self.assertEqual(templates['Test1.bft']['attrs']['name'], "name_test")
        self.assertEqual(templates['Test1.bft']['attrs']['description'], "desc_test")

    def test_get_format_template_attrs(self):
        """ bibformat - correct parsing of attributes in format template"""
        bibformat_engine.CFG_BIBFORMAT_TEMPLATES_PATH = CFG_BIBFORMAT_TEMPLATES_PATH
        attrs = bibformat_engine.get_format_template_attrs("Test1.bft")
        self.assertEqual(attrs['name'], "name_test")
        self.assertEqual(attrs['description'], "desc_test")


    def test_get_fresh_format_template_filename(self):
        """ bibformat - getting fresh filename for format template"""
        bibformat_engine.CFG_BIBFORMAT_TEMPLATES_PATH = CFG_BIBFORMAT_TEMPLATES_PATH
        filename_and_name_1 = bibformat_engine.get_fresh_format_template_filename("Test")
        self.assert_(len(filename_and_name_1) >= 2)
        self.assertEqual(filename_and_name_1[0], "Test.bft")
        filename_and_name_2 = bibformat_engine.get_fresh_format_template_filename("Test1")
        self.assert_(len(filename_and_name_2) >= 2)
        self.assert_(filename_and_name_2[0] != "Test1.bft")
        path = bibformat_engine.CFG_BIBFORMAT_TEMPLATES_PATH + os.sep + filename_and_name_2[0]
        self.assert_(not os.path.exists(path))

class FormatElementTest(unittest.TestCase):
    """ bibformat - tests on format templates"""

    def setUp(self):
        # pylint: disable=C0103
        """bibformat - setting python path to test elements"""
        sys.path.append('%s' % CFG_TMPDIR)

    def test_resolve_format_element_filename(self):
        """bibformat - resolving format elements filename """
        bibformat_engine.CFG_BIBFORMAT_ELEMENTS_PATH = CFG_BIBFORMAT_ELEMENTS_PATH

        #Test elements filename starting without bfe_, with underscore instead of space
        filenames = ["test 1", "test 1.py", "bfe_test 1", "bfe_test 1.py", "BFE_test 1",
                     "BFE_TEST 1", "BFE_TEST 1.py", "BFE_TeST 1.py", "BFE_TeST 1",
                     "BfE_TeST 1.py", "BfE_TeST 1","test_1", "test_1.py", "bfe_test_1",
                     "bfe_test_1.py", "BFE_test_1",
                     "BFE_TEST_1", "BFE_TEST_1.py", "BFE_Test_1.py", "BFE_TeST_1",
                     "BfE_TeST_1.py", "BfE_TeST_1"]

        for i in range(len(filenames)-2):
            filename_1 = bibformat_engine.resolve_format_element_filename(filenames[i])
            self.assert_(filename_1 is not None)

            filename_2 = bibformat_engine.resolve_format_element_filename(filenames[i+1])
            self.assertEqual(filename_1, filename_2)


        #Test elements filename starting with bfe_, and with underscores instead of spaces
        filenames = ["test 2", "test 2.py", "bfe_test 2", "bfe_test 2.py", "BFE_test 2",
                     "BFE_TEST 2", "BFE_TEST 2.py", "BFE_TeST 2.py", "BFE_TeST 2",
                     "BfE_TeST 2.py", "BfE_TeST 2","test_2", "test_2.py", "bfe_test_2",
                     "bfe_test_2.py", "BFE_test_2",
                     "BFE_TEST_2", "BFE_TEST_2.py", "BFE_TeST_2.py", "BFE_TeST_2",
                     "BfE_TeST_2.py", "BfE_TeST_2"]

        for i in range(len(filenames)-2):
            filename_1 = bibformat_engine.resolve_format_element_filename(filenames[i])
            self.assert_(filename_1 is not None)

            filename_2 = bibformat_engine.resolve_format_element_filename(filenames[i+1])
            self.assertEqual(filename_1, filename_2)

        #Test non existing element
        non_existing_element = bibformat_engine.resolve_format_element_filename("BFE_NON_EXISTING_ELEMENT")
        self.assertEqual(non_existing_element, None)

    def test_get_format_element(self):
        """bibformat - format elements parsing and returned structure"""
        bibformat_engine.CFG_BIBFORMAT_ELEMENTS_PATH = CFG_BIBFORMAT_ELEMENTS_PATH
        bibformat_engine.CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH = CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH


        #Test loading with different kind of names, for element with spaces in name, without bfe_
        element_1 = bibformat_engine.get_format_element("test 1", with_built_in_params=True)
        self.assert_(element_1 is not None)
        element_1_bis = bibformat_engine.get_format_element("bfe_tEst_1.py", with_built_in_params=True)
        self.assertEqual(element_1, element_1_bis)

        #Test loading with different kind of names, for element without spaces in name, wit bfe_
        element_2 = bibformat_engine.get_format_element("test 2", with_built_in_params=True)
        self.assert_(element_2 is not None)
        element_2_bis = bibformat_engine.get_format_element("bfe_tEst_2.py", with_built_in_params=True)
        self.assertEqual(element_2, element_2_bis)

        #Test loading incorrect elements
        element_3 = bibformat_engine.get_format_element("test 3", with_built_in_params=True)
        self.assertEqual(element_3, None)
        element_4 = bibformat_engine.get_format_element("test 4", with_built_in_params=True)
        self.assertEqual(element_4, None)
        unknown_element = bibformat_engine.get_format_element("TEST_NO_ELEMENT", with_built_in_params=True)
        self.assertEqual(unknown_element, None)

        #Test element without docstring
        element_5 = bibformat_engine.get_format_element("test_5", with_built_in_params=True)
        self.assert_(element_5 is not None)
        self.assertEqual(element_5['attrs']['description'], '')
        self.assert_({'name':"param1",
                     'description':"(no description provided)",
                     'default':""} in element_5['attrs']['params'] )
        self.assertEqual(element_5['attrs']['seealso'], [])

        #Test correct parsing:

        #Test type of element
        self.assertEqual(element_1['type'], "python")
        #Test name = element filename, with underscore instead of spaces,
        #without BFE_ and uppercase
        self.assertEqual(element_1['attrs']['name'], "TEST_1")
        #Test description parsing
        self.assertEqual(element_1['attrs']['description'], "Prints test")
        #Test @see: parsing
        self.assertEqual(element_1['attrs']['seealso'], ["element2.py", "unknown_element.py"])
        #Test @param parsing
        self.assert_({'name':"param1",
                      'description':"desc 1",
                      'default':""} in element_1['attrs']['params'] )

        self.assert_({'name':"param2",
                      'description':"desc 2",
                      'default':"default value"} in element_1['attrs']['params'] )



        #Test non existing element
        non_existing_element = bibformat_engine.get_format_element("BFE_NON_EXISTING_ELEMENT")
        self.assertEqual(non_existing_element, None)

    def test_get_format_element_attrs_from_function(self):
        """ bibformat - correct parsing of attributes in 'format' docstring"""
        bibformat_engine.CFG_BIBFORMAT_ELEMENTS_PATH = CFG_BIBFORMAT_ELEMENTS_PATH
        bibformat_engine.CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH = CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH
        element_1 = bibformat_engine.get_format_element("test 1", with_built_in_params=True)
        function = element_1['code']
        attrs = bibformat_engine.get_format_element_attrs_from_function(function,
                                                                        element_1['attrs']['name'],
                                                                        with_built_in_params=True)

        self.assertEqual(attrs['name'], "TEST_1")
        #Test description parsing
        self.assertEqual(attrs['description'], "Prints test")
        #Test @see: parsing
        self.assertEqual(attrs['seealso'], ["element2.py", "unknown_element.py"])

    def test_get_format_elements(self):
        """bibformat - multiple format elements parsing and returned structure"""
        bibformat_engine.CFG_BIBFORMAT_ELEMENTS_PATH = CFG_BIBFORMAT_ELEMENTS_PATH
        bibformat_engine.CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH = CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH

        elements = bibformat_engine.get_format_elements()
        self.assert_(isinstance(elements, dict))
        self.assertEqual(elements['TEST_1']['attrs']['name'], "TEST_1")
        self.assertEqual(elements['TEST_2']['attrs']['name'], "TEST_2")
        self.assert_("TEST_3" not in elements.keys())
        self.assert_("TEST_4" not in elements.keys())

    def test_get_tags_used_by_element(self):
        """bibformat - identification of tag usage inside element"""
        bibformat_engine.CFG_BIBFORMAT_ELEMENTS_PATH = bibformat_config.CFG_BIBFORMAT_ELEMENTS_PATH
        bibformat_engine.CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH = bibformat_config.CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH
        tags = bibformatadminlib.get_tags_used_by_element('bfe_abstract.py')
        self.failUnless(len(tags) == 4,
                        'Could not correctly identify tags used in bfe_abstract.py')

class OutputFormatTest(unittest.TestCase):
    """ bibformat - tests on output formats"""

    def test_get_output_format(self):
        """ bibformat - output format parsing and returned structure """
        bibformat_engine.CFG_BIBFORMAT_OUTPUTS_PATH = CFG_BIBFORMAT_OUTPUTS_PATH

        filename_1 = bibformat_engine.resolve_output_format_filename("test1")
        output_1 = bibformat_engine.get_output_format(filename_1, with_attributes=True)

        self.assertEqual(output_1['attrs']['names']['generic'], "")
        self.assert_(isinstance(output_1['attrs']['names']['ln'], dict))
        self.assert_(isinstance(output_1['attrs']['names']['sn'], dict))
        self.assertEqual(output_1['attrs']['code'], "TEST1")
        self.assert_(len(output_1['attrs']['code']) <= 6)
        self.assertEqual(len(output_1['rules']), 4)
        self.assertEqual(output_1['rules'][0]['field'], '980.a')
        self.assertEqual(output_1['rules'][0]['template'], 'Picture_HTML_detailed.bft')
        self.assertEqual(output_1['rules'][0]['value'], 'PICTURE ')
        self.assertEqual(output_1['rules'][1]['field'], '980.a')
        self.assertEqual(output_1['rules'][1]['template'], 'Article.bft')
        self.assertEqual(output_1['rules'][1]['value'], 'ARTICLE')
        self.assertEqual(output_1['rules'][2]['field'], '980__a')
        self.assertEqual(output_1['rules'][2]['template'], 'Thesis_detailed.bft')
        self.assertEqual(output_1['rules'][2]['value'], 'THESIS ')
        self.assertEqual(output_1['rules'][3]['field'], '980__a')
        self.assertEqual(output_1['rules'][3]['template'], 'Pub.bft')
        self.assertEqual(output_1['rules'][3]['value'], 'PUBLICATION ')
        filename_2 = bibformat_engine.resolve_output_format_filename("TEST2")
        output_2 = bibformat_engine.get_output_format(filename_2, with_attributes=True)

        self.assertEqual(output_2['attrs']['names']['generic'], "")
        self.assert_(isinstance(output_2['attrs']['names']['ln'], dict))
        self.assert_(isinstance(output_2['attrs']['names']['sn'], dict))
        self.assertEqual(output_2['attrs']['code'], "TEST2")
        self.assert_(len(output_2['attrs']['code']) <= 6)
        self.assertEqual(output_2['rules'], [])
        unknown_output = bibformat_engine.get_output_format("unknow", with_attributes=True)
        self.assertEqual(unknown_output, {'rules':[],
                                          'default':"",
                                          'attrs':{'names':{'generic':"", 'ln':{}, 'sn':{}},
                                                   'description':'',
                                                   'code':"UNKNOW",
                                                   'visibility': 1,
                                                   'content_type':""}})

    def test_get_output_formats(self):
        """ bibformat - loading multiple output formats """
        bibformat_engine.CFG_BIBFORMAT_OUTPUTS_PATH = CFG_BIBFORMAT_OUTPUTS_PATH
        outputs = bibformat_engine.get_output_formats(with_attributes=True)
        self.assert_(isinstance(outputs, dict))
        self.assert_("TEST1.bfo" in outputs.keys())
        self.assert_("TEST2.bfo" in outputs.keys())
        self.assert_("unknow.bfo" not in outputs.keys())

        #Test correct parsing
        output_1 = outputs["TEST1.bfo"]
        self.assertEqual(output_1['attrs']['names']['generic'], "")
        self.assert_(isinstance(output_1['attrs']['names']['ln'], dict))
        self.assert_(isinstance(output_1['attrs']['names']['sn'], dict))
        self.assertEqual(output_1['attrs']['code'], "TEST1")
        self.assert_(len(output_1['attrs']['code']) <= 6)

    def test_get_output_format_attrs(self):
        """ bibformat - correct parsing of attributes in output format"""
        bibformat_engine.CFG_BIBFORMAT_OUTPUTS_PATH = CFG_BIBFORMAT_OUTPUTS_PATH

        attrs= bibformat_engine.get_output_format_attrs("TEST1")

        self.assertEqual(attrs['names']['generic'], "")
        self.assert_(isinstance(attrs['names']['ln'], dict))
        self.assert_(isinstance(attrs['names']['sn'], dict))
        self.assertEqual(attrs['code'], "TEST1")
        self.assert_(len(attrs['code']) <= 6)

    def test_resolve_output_format(self):
        """ bibformat - resolving output format filename"""
        bibformat_engine.CFG_BIBFORMAT_OUTPUTS_PATH = CFG_BIBFORMAT_OUTPUTS_PATH

        filenames = ["test1", "test1.bfo", "TEST1", "TeST1", "TEST1.bfo", "<b>test1"]
        for i in range(len(filenames)-2):
            filename_1 = bibformat_engine.resolve_output_format_filename(filenames[i])
            self.assert_(filename_1 is not None)

            filename_2 = bibformat_engine.resolve_output_format_filename(filenames[i+1])
            self.assertEqual(filename_1, filename_2)

    def test_get_fresh_output_format_filename(self):
        """ bibformat - getting fresh filename for output format"""
        bibformat_engine.CFG_BIBFORMAT_OUTPUTS_PATH = CFG_BIBFORMAT_OUTPUTS_PATH

        filename_and_name_1 = bibformat_engine.get_fresh_output_format_filename("test")
        self.assert_(len(filename_and_name_1) >= 2)
        self.assertEqual(filename_and_name_1[0], "TEST.bfo")

        filename_and_name_1_bis = bibformat_engine.get_fresh_output_format_filename("<test>")
        self.assert_(len(filename_and_name_1_bis) >= 2)
        self.assertEqual(filename_and_name_1_bis[0], "TEST.bfo")

        filename_and_name_2 = bibformat_engine.get_fresh_output_format_filename("test1")
        self.assert_(len(filename_and_name_2) >= 2)
        self.assert_(filename_and_name_2[0] != "TEST1.bfo")
        path = bibformat_engine.CFG_BIBFORMAT_OUTPUTS_PATH + os.sep + filename_and_name_2[0]
        self.assert_(not os.path.exists(path))

        filename_and_name_3 = bibformat_engine.get_fresh_output_format_filename("test1testlong")
        self.assert_(len(filename_and_name_3) >= 2)
        self.assert_(filename_and_name_3[0] != "TEST1TESTLONG.bft")
        self.assert_(len(filename_and_name_3[0]) <= 6 + 1 + len(bibformat_config.CFG_BIBFORMAT_FORMAT_OUTPUT_EXTENSION))
        path = bibformat_engine.CFG_BIBFORMAT_OUTPUTS_PATH + os.sep + filename_and_name_3[0]
        self.assert_(not os.path.exists(path))

class PatternTest(unittest.TestCase):
    """ bibformat - tests on re patterns"""

    def test_pattern_lang(self):
        """ bibformat - correctness of pattern 'pattern_lang'"""
        text = ''' <h1>Here is my test text</h1>
        <p align="center">
        <lang><en><b>Some words</b></en><fr>Quelques mots</fr><de>Einige Wörter</de> garbage </lang>
        Here ends the middle of my test text
        <lang><en><b>English</b></en><fr><b>Français</b></fr><de><b>Deutsch</b></de></lang>
        <b>Here ends my test text</b></p>'''

        result = bibformat_engine.pattern_lang.search(text)
        self.assertEqual(result.group("langs"), "<en><b>Some words</b></en><fr>Quelques mots</fr><de>Einige Wörter</de> garbage ")

        text = ''' <h1>Here is my test text</h1>
        <BFE_test param="
        <lang><en><b>Some words</b></en><fr>Quelques mots</fr><de>Einige Wörter</de> garbage </lang>" />

        '''

        result = bibformat_engine.pattern_lang.search(text)
        self.assertEqual(result.group("langs"), "<en><b>Some words</b></en><fr>Quelques mots</fr><de>Einige Wörter</de> garbage ")

    def test_ln_pattern(self):
        """ bibformat - correctness of pattern 'ln_pattern'"""

        text = "<en><b>Some words</b></en><fr>Quelques mots</fr><de>Einige Wörter</de> garbage "
        result = bibformat_engine.ln_pattern.search(text)
        self.assertEqual(result.group(1), "en")
        self.assertEqual(result.group(2), "<b>Some words</b>")


    def test_pattern_format_template_name(self):
        """ bibformat - correctness of pattern 'pattern_format_template_name'"""
        text = '''
        garbage
        <name><b>a name</b></name>
        <description>a <b>description</b> on
        2 lines </description>
        <h1>the content of the template</h1>
        content
        '''
        result = bibformat_engine.pattern_format_template_name.search(text)
        self.assertEqual(result.group('name'), "<b>a name</b>")

    def test_pattern_format_template_desc(self):
        """ bibformat - correctness of pattern 'pattern_format_template_desc'"""
        text = '''
        garbage
        <name><b>a name</b></name>
        <description>a <b>description</b> on
        2 lines </description>
        <h1>the content of the template</h1>
        content
        '''
        result = bibformat_engine.pattern_format_template_desc.search(text)
        self.assertEqual(result.group('desc'), '''a <b>description</b> on
        2 lines ''')

    def test_pattern_tag(self):
        """ bibformat - correctness of pattern 'pattern_tag'"""
        text = '''
        garbage but part of content
        <name><b>a name</b></name>
        <description>a <b>description</b> on
        2 lines </description>
        <h1>the content of the template</h1>
        <BFE_tiTLE param1="<b>value1</b>"
        param2=""/>
        my content is so nice!
        <BFE_title param1="value1"/>
        <BFE_title param1="value1"/>
        '''
        result = bibformat_engine.pattern_tag.search(text)
        self.assertEqual(result.group('function_name'), "tiTLE")
        self.assertEqual(result.group('params').strip(), '''param1="<b>value1</b>"
        param2=""''')

    def test_pattern_function_params(self):
        """ bibformat - correctness of pattern 'test_pattern_function_params'"""
        text = '''
        param1=""  param2="value2"
        param3="<b>value3</b>" garbage

        '''
        names = ["param1", "param2", "param3"]
        values = ["", "value2", "<b>value3</b>"]
        results = bibformat_engine.pattern_format_element_params.finditer(text) #TODO
        param_i = 0
        for match in results:
            self.assertEqual(match.group('param'), names[param_i])
            self.assertEqual(match.group('value'), values [param_i])
            param_i += 1

    def test_pattern_format_element_params(self):
        """ bibformat - correctness of pattern 'pattern_format_element_params'"""
        text = '''
        a description for my element
        some text
        @param param1: desc1
        @param param2: desc2
        @see: seethis, seethat
        '''
        names = ["param1", "param2"]
        descriptions = ["desc1", "desc2"]
        results = bibformat_engine.pattern_format_element_params.finditer(text) #TODO
        param_i = 0
        for match in results:
            self.assertEqual(match.group('name'), names[param_i])
            self.assertEqual(match.group('desc'), descriptions[param_i])
            param_i += 1

    def test_pattern_format_element_seealso(self):
        """ bibformat - correctness of pattern 'pattern_format_element_seealso' """
        text = '''
        a description for my element
        some text
        @param param1: desc1
        @param param2: desc2
        @see: seethis, seethat
        '''
        result = bibformat_engine.pattern_format_element_seealso.search(text)
        self.assertEqual(result.group('see').strip(), 'seethis, seethat')

class EscapingAndWashingTest(unittest.TestCase):
    """ bibformat - test escaping and washing metadata"""

    def test_escaping(self):
        """ bibformat - tests escaping HTML characters"""

        text = "Is 5 < 6 ? For sure! And what about True && False == True?"
        result = bibformat_engine.escape_field(text, mode=0)
        self.assertEqual(result, text)

        result = bibformat_engine.escape_field(text, mode=1)
        self.assertEqual(result, 'Is 5 &lt; 6 ? For sure! And what about True &amp;&amp; False == True?')

    def test_washing(self):
        """ bibformat - test washing HTML tags"""

        text = '''Hi dude, <br>, <strong>please login</strong>:<br/>
        <a onclick="http://www.mycrappywebsite.com" href="login.html">login here</a></a><SCRIPT>alert("XSS");</SCRIPT>'''

        # Keep only basic tags
        result = bibformat_engine.escape_field(text, mode=2)
        self.assert_('script' not in result.lower())
        self.assert_('onclick' not in result.lower())
        self.assert_('mycrappywebsite' not in result.lower())
        self.assert_('<br>' in result.lower())
        self.assert_('<br/>' in result.lower().replace(' ', ''))

        # Keep only basic tags only if value starts with <!--HTML-->
        # directive. Otherwise escape (which is the case here)
        result = bibformat_engine.escape_field(text, mode=3)
        self.assert_('<script' not in result.lower())
        self.assert_('<' not in result.lower())

        result = bibformat_engine.escape_field(text, mode=5)
        self.assert_('<script' not in result.lower())
        self.assert_('<br' in result.lower())

        # Remove all HTML tags
        result = bibformat_engine.escape_field(text, mode=4)
        self.assert_('script' not in result.lower())
        self.assert_('onclick' not in result.lower())
        self.assert_('mycrappywebsite' not in result.lower())
        self.assert_('strong' not in result.lower())
        self.assert_('<br>' not in result.lower())
        self.assert_('<br/>' not in result.lower().replace(' ', ''))
        self.assert_('login here' in result.lower())

        # Keep basic tags + some others (like <img>)
        result = bibformat_engine.escape_field(text, mode=5)
        self.assert_('script' not in result.lower())
        self.assert_('onclick' not in result.lower())
        self.assert_('mycrappywebsite' not in result.lower())
        self.assert_('<br' in result.lower())
        self.assert_('login here' in result.lower())

        text2 = text + ' <img src="loginicon" alt="login icon"/>'
        result = bibformat_engine.escape_field(text2, mode=5)
        self.assert_('<img' in result.lower())
        self.assert_('src=' in result.lower())
        self.assert_('alt="login icon"' in result.lower())

        # Keep some tags only if value starts with <!--HTML-->
        # directive. Otherwise escape (which is the case here)
        result = bibformat_engine.escape_field(text, mode=6)
        self.assert_('<script' not in result.lower())
        self.assert_('<' not in result.lower())

        result = bibformat_engine.escape_field('<!--HTML-->'+text, mode=6)
        self.assert_('<script' not in result.lower())
        self.assert_('<br>' in result.lower())
        self.assert_('mycrappywebsite' not in result.lower())

        # When the value cannot be parsed by our not so smart parser,
        # just escape everything
        text3 = """Ok, let't try with something unparsable < hehe <a onclick="http://www.mycrappywebsite.com" href="login.html">login</a>"""
        result = bibformat_engine.escape_field(text3, mode=2)
        self.assert_('mycrappywebsite' not in result.lower() or \
                     '<a' not in result.lower())

        result = bibformat_engine.escape_field(text3, mode=3)
        self.assert_('<a' not in result.lower())

        result = bibformat_engine.escape_field(text3, mode=5)
        self.assert_('mycrappywebsite' not in result.lower() or \
                     '<a' not in result.lower())

        result = bibformat_engine.escape_field(text3, mode=6)
        self.assert_('<a' not in result.lower())


class MiscTest(unittest.TestCase):
    """ bibformat - tests on various functions"""

    def test_parse_tag(self):
        """ bibformat - result of parsing tags"""
        tags_and_parsed_tags = ['245COc',   ['245', 'C', 'O', 'c'],
                                '245C_c',   ['245', 'C', '' , 'c'],
                                '245__c',   ['245', '' , '' , 'c'],
                                '245__$$c', ['245', '' , '' , 'c'],
                                '245__$c',  ['245', '' , '' , 'c'],
                                '245  $c',  ['245', '' , '' , 'c'],
                                '245  $$c', ['245', '' , '' , 'c'],
                                '245__.c',  ['245', '' , '' , 'c'],
                                '245  .c',  ['245', '' , '' , 'c'],
                                '245C_$c',  ['245', 'C', '' , 'c'],
                                '245CO$$c', ['245', 'C', 'O', 'c'],
                                '245CO.c',  ['245', 'C', 'O', 'c'],
                                '245$c',    ['245', '' , '' , 'c'],
                                '245.c',    ['245', '' , '' , 'c'],
                                '245$$c',   ['245', '' , '' , 'c'],
                                '245__%',   ['245', '' , '' , '%'],
                                '245__$$%', ['245', '' , '' , '%'],
                                '245__$%',  ['245', '' , '' , '%'],
                                '245  $%',  ['245', '' , '' , '%'],
                                '245  $$%', ['245', '' , '' , '%'],
                                '245$%',    ['245', '' , '' , '%'],
                                '245.%',    ['245', '' , '' , '%'],
                                '245_O.%',  ['245', '' , 'O', '%'],
                                '245.%',    ['245', '' , '' , '%'],
                                '245$$%',   ['245', '' , '' , '%'],
                                '2%5$$a',   ['2%5', '' , '' , 'a'],
                                '2%%%%a',   ['2%%', '%', '%', 'a'],
                                '2%%__a',   ['2%%', '' , '' , 'a'],
                                '2%%a',     ['2%%', '' , '' , 'a']]

        for i in range(0, len(tags_and_parsed_tags), 2):
            parsed_tag = bibformat_utils.parse_tag(tags_and_parsed_tags[i])
            self.assertEqual(parsed_tag, tags_and_parsed_tags[i+1])

class FormatTest(unittest.TestCase):
    """ bibformat - generic tests on function that do the formatting. Main functions"""

    def setUp(self):
        # pylint: disable=C0103
        """ bibformat - prepare BibRecord objects"""

        self.xml_text_1 = '''
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="980" ind1="" ind2="">
        <subfield code="a">thesis</subfield>
        </datafield>
        <datafield tag="950" ind1="" ind2="">
        <subfield code="b">Doe1, John</subfield>
        </datafield>
        <datafield tag="100" ind1="" ind2="">
        <subfield code="a">Doe2, John</subfield>
        <subfield code="b">editor</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="1">
        <subfield code="a">On the foo and bar1</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="2">
        <subfield code="a">On the foo and bar2</subfield>
        </datafield>
        <datafield tag="088" ind1="" ind2="">
        <subfield code="a">99999</subfield>
        </datafield>
        </record>
        '''

        #rec_1 = bibrecord.create_record(self.xml_text_1)
        self.bfo_1 = bibformat_engine.BibFormatObject(recID=None,
                                                      ln='fr',
                                                      xml_record=self.xml_text_1)

        self.xml_text_2 = '''
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="980" ind1="" ind2="">
        <subfield code="b">thesis </subfield>
        </datafield>
        <datafield tag="950" ind1="" ind2="">
        <subfield code="b">Doe1, John</subfield>
        </datafield>
        <datafield tag="100" ind1="" ind2="">
        <subfield code="a">Doe2, John</subfield>
        <subfield code="b">editor</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="1">
        <subfield code="b">On the foo and bar1</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="2">
        <subfield code="b">On the foo and bar2</subfield>
        </datafield>
        </record>
        '''
        #self.rec_2 = bibrecord.create_record(xml_text_2)
        self.bfo_2 = bibformat_engine.BibFormatObject(recID=None,
                                                      ln='fr',
                                                      xml_record=self.xml_text_2)


        self.xml_text_3 = '''
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1="" ind2="">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1="" ind2="">
        <subfield code="a">Doe1, John</subfield>
        </datafield>
        <datafield tag="100" ind1="" ind2="">
        <subfield code="a">Doe2, John</subfield>
        <subfield code="b">editor</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="1">
        <subfield code="a">On the foo and bar1</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="2">
        <subfield code="a">On the foo and bar2</subfield>
        </datafield>
        <datafield tag="980" ind1="" ind2="">
        <subfield code="a">article</subfield>
        </datafield>
        </record>
        '''
        #self.rec_3 = bibrecord.create_record(xml_text_3)
        self.bfo_3 = bibformat_engine.BibFormatObject(recID=None,
                                                      ln='fr',
                                                      xml_record=self.xml_text_3)

        self.empty_record_xml = '''
        <record>
        <controlfield tag="001">555</controlfield>
        </record>'''

    def test_decide_format_template(self):
        """ bibformat - choice made by function decide_format_template"""
        bibformat_engine.CFG_BIBFORMAT_OUTPUTS_PATH = CFG_BIBFORMAT_OUTPUTS_PATH

        result = bibformat_engine.decide_format_template(self.bfo_1, "test1")
        self.assertEqual(result, "Thesis_detailed.bft")

        result = bibformat_engine.decide_format_template(self.bfo_3, "test3")
        self.assertEqual(result, "Test3.bft")

        #Only default matches
        result = bibformat_engine.decide_format_template(self.bfo_2, "test1")
        self.assertEqual(result, "Default_HTML_detailed.bft")

        #No match at all for record
        result = bibformat_engine.decide_format_template(self.bfo_2, "test2")
        self.assertEqual(result, None)

        #Non existing output format
        result = bibformat_engine.decide_format_template(self.bfo_2, "UNKNOW")
        self.assertEqual(result, None)

    def test_format_record(self):
        """ bibformat - correct formatting"""
        bibformat_engine.CFG_BIBFORMAT_OUTPUTS_PATH = CFG_BIBFORMAT_OUTPUTS_PATH
        bibformat_engine.CFG_BIBFORMAT_ELEMENTS_PATH = CFG_BIBFORMAT_ELEMENTS_PATH
        bibformat_engine.CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH = CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH
        bibformat_engine.CFG_BIBFORMAT_TEMPLATES_PATH = CFG_BIBFORMAT_TEMPLATES_PATH

        #use output format that has no match TEST DISABLED DURING MIGRATION
        #result = bibformat_engine.format_record(recID=None, of="test2", xml_record=self.xml_text_2)
        #self.assertEqual(result.replace("\n", ""),"")

        #use output format that link to unknown template
        result = bibformat_engine.format_record(recID=None, of="test3", xml_record=self.xml_text_2)
        self.assertEqual(result.replace("\n", ""),"")

        #Unknown output format TEST DISABLED DURING MIGRATION
        #result = bibformat_engine.format_record(recID=None, of="unkno", xml_record=self.xml_text_3)
        #self.assertEqual(result.replace("\n", ""),"")

        #Default formatting
        result = bibformat_engine.format_record(recID=None, ln='fr', of="test3", xml_record=self.xml_text_3)
        self.assertEqual(result,'''<h1>hi</h1> this is my template\ntest<bfe_non_existing_element must disappear/><test_1  non prefixed element must stay as any normal tag/>tfrgarbage\n<br/>test me!&lt;b&gt;ok&lt;/b&gt;a default valueeditor\n<br/>test me!<b>ok</b>a default valueeditor\n<br/>test me!&lt;b&gt;ok&lt;/b&gt;a default valueeditor\n''')

    def test_empty_formatting(self):
        """bibformat - formatting empty record"""
        result = bibformat_engine.format_record(recID=0,
                                                of='hb',
                                                verbose=9,
                                                xml_record=self.empty_record_xml)
        self.assertEqual(result, '')

        # FIXME: The commented test below currently fails, since xm
        # format is generated from the database

##         result = bibformat_engine.format_record(recID=0,
##                                                 of='xm',
##                                                 verbose=9,
##                                                 xml_record=self.empty_record_xml)
##         self.assertEqual(result, self.empty_record_xml)

    def test_format_with_format_template(self):
        """ bibformat - correct formatting with given template"""
        bibformat_engine.CFG_BIBFORMAT_ELEMENTS_PATH = CFG_BIBFORMAT_ELEMENTS_PATH
        bibformat_engine.CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH = CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH
        bibformat_engine.CFG_BIBFORMAT_TEMPLATES_PATH = CFG_BIBFORMAT_TEMPLATES_PATH

        template = bibformat_engine.get_format_template("Test3.bft")
        result = bibformat_engine.format_with_format_template(format_template_filename = None,
                                                              bfo=self.bfo_1,
                                                              verbose=0,
                                                              format_template_code=template['code'])

        self.assertEqual(result,'''<h1>hi</h1> this is my template\ntest<bfe_non_existing_element must disappear/><test_1  non prefixed element must stay as any normal tag/>tfrgarbage\n<br/>test me!&lt;b&gt;ok&lt;/b&gt;a default valueeditor\n<br/>test me!<b>ok</b>a default valueeditor\n<br/>test me!&lt;b&gt;ok&lt;/b&gt;a default valueeditor\n99999''')


class MarcFilteringTest(unittest.TestCase):
    """ bibformat - MARC tag filtering tests"""

    def setUp(self):
        """bibformat - prepare MARC filtering tests"""

        self.xml_text_4 = '''
        <record>
        <controlfield tag="001">33</controlfield>
        <datafield tag="041" ind1="" ind2="">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1="" ind2="">
        <subfield code="a">Doe1, John</subfield>
        </datafield>
        <datafield tag="100" ind1="" ind2="">
        <subfield code="a">Doe2, John</subfield>
        <subfield code="b">editor</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="1">
        <subfield code="a">On the foo and bar1</subfield>
        </datafield>
        <datafield tag="245" ind1="" ind2="2">
        <subfield code="a">On the foo and bar2</subfield>
        </datafield>
        <datafield tag="595" ind1="" ind2="2">
        <subfield code="a">Confidential comment</subfield>
        </datafield>
        <datafield tag="980" ind1="" ind2="">
        <subfield code="a">article</subfield>
        </datafield>
        </record>
        '''
    def test_filtering(self):
        """bibformat - filter hidden fields"""
        newxml = bibformat.filter_hidden_fields(self.xml_text_4, user_info=None, filter_tags=['595',], force_filtering=True)
        numhfields = newxml.count("595")
        self.assertEqual(numhfields, 0)
        newxml = bibformat.filter_hidden_fields(self.xml_text_4, user_info=None, filter_tags=['595',], force_filtering=False)
        numhfields = newxml.count("595")
        self.assertEqual(numhfields, 1)


TEST_SUITE = make_test_suite(FormatTemplateTest,
                             OutputFormatTest,
                             FormatElementTest,
                             PatternTest,
                             MiscTest,
                             FormatTest,
                             EscapingAndWashingTest,
                             MarcFilteringTest)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)

