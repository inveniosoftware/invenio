# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2013, 2014, 2015 CERN.
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

"""Test cases for the BibFormat engine. Also test
some utilities function in bibformat_utils module"""

__revision__ = "$Id$"

# pylint: disable=C0301

import os
import pkg_resources
import sys

from invenio.base.globals import cfg
from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase
from invenio.ext.registry import ModuleAutoDiscoverySubRegistry
from flask_registry import PkgResourcesDirDiscoveryRegistry, RegistryProxy, \
    ImportPathRegistry, ModuleAutoDiscoveryRegistry

bibformat = lazy_import('invenio.modules.formatter')
bibformat_engine = lazy_import('invenio.modules.formatter.engine')
bibformat_utils = lazy_import('invenio.modules.formatter.utils')
bibformat_config = lazy_import('invenio.modules.formatter.config')
bibformatadminlib = lazy_import('invenio.legacy.bibformat.adminlib')
format_templates = lazy_import('invenio.modules.formatter.testsuite.format_templates')
gettext_set_language = lazy_import('invenio.base.i18n:gettext_set_language')

TEST_PACKAGES = [
    'invenio.modules.formatter.testsuite.overlay',
    'invenio.modules.formatter.testsuite',
]


test_registry = RegistryProxy('test_registry', ImportPathRegistry,
                              initial=TEST_PACKAGES)

format_templates_registry = lambda: PkgResourcesDirDiscoveryRegistry(
    'format_templates', registry_namespace=test_registry)

format_elements_registry = lambda: ModuleAutoDiscoverySubRegistry(
    'format_elements', registry_namespace=test_registry, silent=True)

output_formats_directories_registry = lambda: ModuleAutoDiscoveryRegistry(
    'output_formats', registry_namespace=test_registry, silent=True
)


class FormatTemplateTest(InvenioTestCase):
    """ bibformat - tests on format templates"""

    def setUp(self):
        self.app.extensions['registry']['format_templates'] = format_templates_registry()

    def tearDown(self):
        del self.app.extensions['registry']['format_templates']

    def test_get_format_template(self):
        """bibformat - format template parsing and returned structure"""

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
        attrs = bibformat_engine.get_format_template_attrs("Test1.bft")
        self.assertEqual(attrs['name'], "name_test")
        self.assertEqual(attrs['description'], "desc_test")


class FormatElementTest(InvenioTestCase):
    """ bibformat - tests on format templates"""

    def setUp(self):
        # pylint: disable=C0103
        """bibformat - setting python path to test elements"""
        self.app.extensions['registry']['format_elements'] = format_elements_registry()

    def tearDown(self):
        del self.app.extensions['registry']['format_elements']

    def test_resolve_format_element_filename(self):
        """bibformat - resolving format elements filename """
        #Test elements filename starting without bfe_, with underscore instead of space
        filenames = ["test 1", "test 1.py", "bfe_test 1", "bfe_test 1.py", "BFE_test 1",
                     "BFE_TEST 1", "BFE_TEST 1.py", "BFE_TeST 1.py", "BFE_TeST 1",
                     "BfE_TeST 1.py", "BfE_TeST 1", "test_1", "test_1.py", "bfe_test_1",
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
                     "BfE_TeST 2.py", "BfE_TeST 2", "test_2", "test_2.py", "bfe_test_2",
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
        try:
            element_3 = bibformat_engine.get_format_element("test 3", with_built_in_params=True)
        except bibformat_engine.InvenioBibFormatError as e:
            self.assertEqual(str(e), 'Format element test 3 could not be found.')
        else:
            self.fail("Should have raised InvenioBibFormatError")

        try:
            element_4 = bibformat_engine.get_format_element("test 4", with_built_in_params=True)
        except bibformat_engine.InvenioBibFormatError as e:
            self.assertEqual(str(e), 'Format element test 4 could not be found.')
        else:
            self.fail("Should have raised SyntaxError")

        try:
            unknown_element = bibformat_engine.get_format_element("TEST_NO_ELEMENT", with_built_in_params=True)
        except bibformat_engine.InvenioBibFormatError as e:
            self.assertEqual(str(e), 'Format element TEST_NO_ELEMENT could not be found.')
        else:
            self.fail("Should have raised InvenioBibFormatError")

        #Test element without docstring
        element_5 = bibformat_engine.get_format_element("test_5", with_built_in_params=True)
        self.assert_(element_5 is not None)
        self.assertEqual(element_5['attrs']['description'], '')
        self.assert_({'name': "param1",
                     'description': "(no description provided)",
                     'default': ""} in element_5['attrs']['params'])
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
        self.assert_({'name': "param1",
                      'description': "desc 1",
                      'default': ""} in element_1['attrs']['params'])

        self.assert_({'name': "param2",
                      'description': "desc 2",
                      'default': "default value"} in element_1['attrs']['params'])



        #Test non existing element
        try:
            non_existing_element = bibformat_engine.get_format_element("BFE_NON_EXISTING_ELEMENT")
        except bibformat_engine.InvenioBibFormatError as e:
            self.assertEqual(str(e), 'Format element BFE_NON_EXISTING_ELEMENT could not be found.')
        else:
            self.fail("Should have raised InvenioBibFormatError")

    def test_get_format_element_attrs_from_function(self):
        """ bibformat - correct parsing of attributes in 'format' docstring"""
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
        elements = bibformat_engine.get_format_elements()
        self.assert_(isinstance(elements, dict))
        self.assertEqual(elements['TEST_1']['attrs']['name'], "TEST_1")
        self.assertEqual(elements['TEST_2']['attrs']['name'], "TEST_2")
        self.assert_("TEST_3" not in elements.keys())
        self.assert_("TEST_4" not in elements.keys())

    def test_get_tags_used_by_element(self):
        """bibformat - identification of tag usage inside element"""
        del self.app.extensions['registry']['format_elements']
        from invenio.modules.formatter.registry import format_elements
        list(format_elements)
        bibformat_engine.TEMPLATE_CONTEXT_FUNCTIONS_CACHE.bibformat_elements.cache.clear()
        #cfg['CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH'] = self.old_import_path
        tags = bibformatadminlib.get_tags_used_by_element('bfe_abstract.py')
        self.failUnless(len(tags) == 4,
                        'Could not correctly identify tags used in bfe_abstract.py')

class OutputFormatTest(InvenioTestCase):
    """ bibformat - tests on output formats"""

    def setUp(self):
        self.app.extensions['registry']['output_formats_directories'] = \
            output_formats_directories_registry()
        from invenio.modules.formatter.registry import output_formats as ofs
        ofs.expunge()

    def tearDown(self):
        from invenio.modules.formatter.registry import output_formats as ofs
        ofs.expunge()
        del self.app.extensions['registry']['output_formats_directories']

    def test_get_output_format(self):
        """ bibformat - output format parsing and returned structure """
        from invenio.modules.formatter.registry import output_formats as ofs
        output_1 = ofs['test1']

        #self.assertEqual(output_1['attrs']['names']['generic'], "")
        #self.assert_(isinstance(output_1['attrs']['names']['ln'], dict))
        #self.assert_(isinstance(output_1['attrs']['names']['sn'], dict))
        self.assertEqual(output_1['code'], "test1")
        self.assert_(len(output_1['code']) <= 6)
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
        output_2 = ofs['test2']

        #self.assertEqual(output_2['attrs']['names']['generic'], "")
        #self.assert_(isinstance(output_2['attrs']['names']['ln'], dict))
        #self.assert_(isinstance(output_2['attrs']['names']['sn'], dict))
        self.assertEqual(output_2['code'], "test2")
        self.assert_(len(output_2['code']) <= 6)
        self.assertEqual(output_2['rules'], [])
        try:
            unknown_output = bibformat_engine.get_output_format("unknow")
        except bibformat_engine.InvenioBibFormatError:
            pass
        else:
            self.fail("Should have raised the InvenioBibFormatError")

    def test_get_output_formats(self):
        """ bibformat - loading multiple output formats """
        outputs = bibformat_engine.get_output_formats()
        self.assert_(isinstance(outputs, dict))
        self.assert_("test1" in outputs.keys())
        self.assert_("test2" in outputs.keys())
        self.assert_("unknow" not in outputs.keys())

        # Test correct parsing
        output_1 = outputs["test1"]
        #self.assertEqual(output_1['attrs']['names']['generic'], "")
        #self.assert_(isinstance(output_1['attrs']['names']['ln'], dict))
        #self.assert_(isinstance(output_1['attrs']['names']['sn'], dict))
        self.assertEqual(output_1['code'], "test1")
        self.assert_(len(output_1['code']) <= 6)


class PatternTest(InvenioTestCase):
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
            self.assertEqual(match.group('value'), values[param_i])
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

class EscapingAndWashingTest(InvenioTestCase):
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
        self.assert_('mycrappywebsite' not in result.lower() or
                     '<a' not in result.lower())

        result = bibformat_engine.escape_field(text3, mode=3)
        self.assert_('<a' not in result.lower())

        result = bibformat_engine.escape_field(text3, mode=5)
        self.assert_('mycrappywebsite' not in result.lower() or
                     '<a' not in result.lower())

        result = bibformat_engine.escape_field(text3, mode=6)
        self.assert_('<a' not in result.lower())


class MiscTest(InvenioTestCase):
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

class FormatTest(InvenioTestCase):
    """ bibformat - generic tests on function that do the formatting. Main functions"""

    def setUp(self):
        # pylint: disable=C0103
        """ bibformat - prepare BibRecord objects"""
        sys.path.append('%s' % cfg['CFG_TMPDIR'])

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

        self.no_001_record_xml = '''
        <record>
        <datafield tag="041" ind1="" ind2="">
        <subfield code="a">eng</subfield>
        </datafield>
        <datafield tag="100" ind1="" ind2="">
        <subfield code="a">Doe1, John</subfield>
        </datafield>'''
        self.app.extensions['registry']['output_formats_directories'] = \
            output_formats_directories_registry()
        from invenio.modules.formatter.registry import output_formats as ofs
        ofs.expunge()
        self.app.extensions['registry']['format_elements'] = format_elements_registry()
        self.app.extensions['registry']['format_templates'] = format_templates_registry()
        from invenio.modules.formatter.registry import format_templates_lookup
        format_templates_lookup.expunge()
        #self.old_import_path = cfg['CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH']
        #cfg['CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH'] = CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH
        self.old_templates_path = cfg['CFG_BIBFORMAT_TEMPLATES_PATH']
        cfg['CFG_BIBFORMAT_TEMPLATES_PATH'] = format_templates.__path__[0]

    def tearDown(self):
        sys.path.pop()
        del self.app.extensions['registry']['output_formats_directories']
        from invenio.modules.formatter.registry import output_formats
        output_formats.expunge()
        from invenio.modules.formatter.registry import format_templates_lookup
        format_templates_lookup.expunge()
        del self.app.extensions['registry']['format_elements']
        #cfg['CFG_BIBFORMAT_ELEMENTS_IMPORT_PATH'] = self.old_import_path
        cfg['CFG_BIBFORMAT_TEMPLATES_PATH'] = self.old_templates_path

    def test_decide_format_template(self):
        """ bibformat - choice made by function decide_format_template"""
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
        try:
            result = bibformat_engine.decide_format_template(self.bfo_2, "UNKNOW")
        except bibformat_engine.InvenioBibFormatError:
            pass
        else:
            self.fail("Should have raised InvenioBibFormatError")

    def test_format_record(self):
        """ bibformat - correct formatting"""
        #use output format that has no match TEST DISABLED DURING MIGRATION
        #result = bibformat_engine.format_record(recID=None, of="test2", xml_record=self.xml_text_2)
        #self.assertEqual(result.replace("\n", ""),"")

        #use output format that link to unknown template
        result, needs_2nd_pass = bibformat_engine.format_record(recID=None, of="test3", xml_record=self.xml_text_2)
        self.assertEqual(result.replace("\n", ""), "")
        self.assertEqual(needs_2nd_pass, False)

        #Unknown output format TEST DISABLED DURING MIGRATION
        #result = bibformat_engine.format_record(recID=None, of="unkno", xml_record=self.xml_text_3)
        #self.assertEqual(result.replace("\n", ""),"")

        #Default formatting
        result, needs_2nd_pass = bibformat_engine.format_record(recID=None, ln='fr', of="test3", xml_record=self.xml_text_3)
        self.assertEqual(result, '''<h1>hi</h1> this is my template\ntest<bfe_non_existing_element must disappear/><test_1  non prefixed element must stay as any normal tag/>tfrgarbage\n<br/>test me!&lt;b&gt;ok&lt;/b&gt;a default valueeditor\n<br/>test me!<b>ok</b>a default valueeditor\n<br/>test me!&lt;b&gt;ok&lt;/b&gt;a default valueeditor\n''')
        self.assertEqual(needs_2nd_pass, False)

    def test_empty_formatting(self):
        """bibformat - formatting empty record"""
        result = bibformat_engine.format_record(recID=0,
                                                of='hb',
                                                verbose=9,
                                                xml_record=self.empty_record_xml)
        self.assertEqual(result, ('', False))

        # FIXME: The commented test below currently fails, since xm
        # format is generated from the database

#         result = bibformat_engine.format_record(recID=0,
#                                                 of='xm',
#                                                 verbose=9,
#                                                 xml_record=self.empty_record_xml)
#         self.assertEqual(result, self.empty_record_xml)

    def test_format_with_format_template(self):
        """ bibformat - correct formatting with given template"""
        del self.app.extensions['registry']['output_formats_directories']
        from invenio.modules.formatter.registry import output_formats
        output_formats.expunge()
        list(output_formats)
        template = bibformat_engine.get_format_template("Test3.bft")
        result, no_cache = bibformat_engine.format_with_format_template(
                                        format_template_filename=None,
                                        bfo=self.bfo_1,
                                        verbose=0,
                                        format_template_code=template['code'])

        self.assertEqual(result, '''<h1>hi</h1> this is my template\ntest<bfe_non_existing_element must disappear/><test_1  non prefixed element must stay as any normal tag/>tfrgarbage\n<br/>test me!&lt;b&gt;ok&lt;/b&gt;a default valueeditor\n<br/>test me!<b>ok</b>a default valueeditor\n<br/>test me!&lt;b&gt;ok&lt;/b&gt;a default valueeditor\n99999''')
        self.assertEqual(no_cache, False)


    def test_format_2_passes_manually(self):
        result, needs_2nd_pass = bibformat_engine.format_record(
                                                recID=None,
                                                of="test6",
                                                xml_record=self.xml_text_2)
        self.assertEqual(result, "<bfe_test_6 />\n")
        self.assertEqual(needs_2nd_pass, True)

        out = bibformat_engine.format_record_2nd_pass(recID=None,
                                                      xml_record=self.xml_text_2,
                                                      template=result)
        self.assertEqual(out, "helloworld\n")

    def test_format_translations_no_2nd_pass_en(self):
        result, needs_2nd_pass = bibformat_engine.format_record(
                                                recID=None,
                                                of="test7",
                                                xml_record=self.xml_text_2,
                                                ln='en')
        self.assertEqual(result.strip(), 'Title en\n<input type="button" value="Record"/>')
        self.assertEqual(needs_2nd_pass, False)

    def test_format_translations_no_2nd_pass_fr(self):
        ln = 'fr'
        result, needs_2nd_pass = bibformat_engine.format_record(
                                                recID=None,
                                                of="test7",
                                                xml_record=self.xml_text_2,
                                                ln=ln)
        _ = gettext_set_language(ln)
        self.assertEqual(result.strip(), 'Titre fr\n<input type="button" value="%s"/>' % _('Record'))
        self.assertEqual(needs_2nd_pass, False)

    def test_format_translations_with_2nd_pass_en(self):
        result, needs_2nd_pass = bibformat_engine.format_record(
                                                recID=None,
                                                of="test8",
                                                xml_record=self.xml_text_2,
                                                ln='en')
        self.assertEqual(result.strip(), '<lang>\n  <en>Title en</en>\n  <fr>Titre fr</fr>\n</lang>\n<bfe_test_6 />\n<input type="button" value="_(Record)_"/>')
        self.assertEqual(needs_2nd_pass, True)

        out = bibformat_engine.format_record_2nd_pass(recID=None,
                                                      template=result,
                                                      xml_record=self.xml_text_2,
                                                      ln='en')
        self.assertEqual(out, 'Title en\nhelloworld\n<input type="button" value="Record"/>')

    def test_format_translations_with_2nd_pass_fr(self):
        ln = 'fr'
        result, needs_2nd_pass = bibformat_engine.format_record(
                                                recID=None,
                                                of="test8",
                                                xml_record=self.xml_text_2,
                                                ln=ln)
        _ = gettext_set_language(ln)
        self.assertEqual(result.strip(), '<lang>\n  <en>Title en</en>\n  <fr>Titre fr</fr>\n</lang>\n<bfe_test_6 />\n<input type="button" value="_(Record)_"/>')
        self.assertEqual(needs_2nd_pass, True)

        out = bibformat_engine.format_record_2nd_pass(recID=None,
                                                      template=result,
                                                      xml_record=self.xml_text_2,
                                                      ln=ln)
        self.assertEqual(out, 'Titre fr\nhelloworld\n<input type="button" value="%s"/>' % _('Record'))

    def test_engine_xslt_format(self):
        from ..engines import xslt
        template = pkg_resources.resource_filename(
            'invenio.modules.formatter', 'format_templates/RSS.xsl')
        output = xslt.format(self.xml_text_1, template_filename=template)
        assert output.startswith(
            '<item>\n  <title>On the foo and bar1On the foo and bar2</title>\n'
            '  <link/>\n  <description/>\n  '
            '<dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">'
            'Doe2, John</dc:creator>\n  <pubDate'
        )
        assert output.endswith(
            '<guid/>\n</item>\n'
        )

    def test_format_record_no_recid(self):
        from invenio.modules.formatter import format_record
        result = format_record(recID=None, of="test6",
                               xml_record=self.no_001_record_xml)
        self.assertEqual(result, "helloworld\n")


class MarcFilteringTest(InvenioTestCase):
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
        newxml = bibformat_engine.filter_hidden_fields(self.xml_text_4, user_info=None, filter_tags=['595'], force_filtering=True)
        numhfields = newxml.count("595")
        self.assertEqual(numhfields, 0)
        newxml = bibformat_engine.filter_hidden_fields(self.xml_text_4, user_info=None, filter_tags=['595'], force_filtering=False)
        numhfields = newxml.count("595")
        self.assertEqual(numhfields, 1)


class BibFormat2ndPassTest(InvenioTestCase):
    """Check for 2 passes parsing for record"""

    def setUp(self):
        self.app.extensions['registry']['format_templates'] = format_templates_registry()
        self.app.extensions['registry']['format_elements'] = format_elements_registry()
        self.app.extensions['registry']['output_formats_directories'] = output_formats_directories_registry()
        from invenio.modules.formatter.registry import output_formats
        output_formats.expunge()
        self.xml_text = '''<record>
    <controlfield tag="001">33</controlfield>
    <datafield tag="980" ind1="" ind2="">
        <subfield code="b">thesis </subfield>
    </datafield>
</record>'''

    def tearDown(self):
        from invenio.modules.formatter.registry import output_formats
        output_formats.expunge()
        del self.app.extensions['registry']['output_formats_directories']
        del self.app.extensions['registry']['format_templates']
        del self.app.extensions['registry']['format_elements']

    def test_format_2_passes(self):
        from invenio.modules.formatter import format_record
        result = format_record(recID=None, of="test6", xml_record=self.xml_text)
        self.assertEqual(result, "helloworld\n")




TEST_SUITE = make_test_suite(FormatTemplateTest,
                             OutputFormatTest,
                             FormatElementTest,
                             PatternTest,
                             MiscTest,
                             FormatTest,
                             EscapingAndWashingTest,
                             MarcFilteringTest,
                             BibFormat2ndPassTest)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
