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

"""
BFX formatting engine.
For API: see format_with_bfx() docstring below.
"""

__revision__ = "$Id$"

import re
import logging
import copy as p_copy
from xml.dom import minidom, Node
from xml.sax import saxutils

from invenio.bibformat_engine import BibFormatObject, get_format_element, eval_format_element
from invenio.bibformat_bfx_engine_config import CFG_BIBFORMAT_BFX_LABEL_DEFINITIONS, CFG_BIBFORMAT_BFX_TEMPLATES_PATH
from invenio.bibformat_bfx_engine_config import CFG_BIBFORMAT_BFX_FORMAT_TEMPLATE_EXTENSION, CFG_BIBFORMAT_BFX_ELEMENT_NAMESPACE
from invenio.bibformat_bfx_engine_config import InvenioBibFormatBfxError, InvenioBibFormatBfxWarning
from invenio.errorlib import register_exception
from invenio.messages import gettext_set_language
from invenio.config import CFG_SITE_LANG

address_pattern = r'(?P<parent>[a-z_]*):?/?(?P<tag>[0-9_?\w]*)/?(?P<code>[\w_?]?)#?(?P<reg>.*)'

def format_with_bfx(recIDs, out_file, template_name, preprocess=None):
    '''
    Format a set of records according to a BFX template.
    This is the main entry point to the BFX engine.

    @param recIDs: a list of record IDs to format
    @param out_file: an object to write in; this can be every object which has a 'write' method: file, req, StringIO
    @param template_name: the file name of the BFX template without the path and the .bfx extension
    @param preprocess: an optional function; every record is passed through this function for initial preprocessing before formatting
    '''
    trans = MARCTranslator(CFG_BIBFORMAT_BFX_LABEL_DEFINITIONS)
    trans.set_record_ids(recIDs, preprocess)
    parser = BFXParser(trans)
    template_tree = parser.load_template(template_name)
    parser.walk(template_tree, out_file)
    return None

class BFXParser:
    '''
    A general-purpose parser for generating xml/xhtml/text output based on a template system.
    Must be initialised with a translator. A translator is like a blackbox that returns values, calls functions, etc...
    Works with every translator supporting the following simple interface:
        - is_defined(name)
        - get_value(name)
        - iterator(name)
        - call_function(func_name, list_of_parameters)
    Customized for MARC to XML conversion through the use of a MARCTranslator.

    Templates are strict XML files. They are built by combining any tags with the
    special BFX tags living in the http://invenio-software.org/ namespace.
    Easily extensible by tags of your own.
    Defined tags:
        - template: defines a template
        - template_ref: a reference to a template
        - loop structure
        - if, then, elif, else structure
        - text: output text
        - field: query translator for field 'name'
        - element: call external functions
    '''
    def __init__(self, translator):
        '''
        Create an instance of the BFXParser class. Initialize with a translator.
        The BFXparser makes queries to the translator for the values of certain names.
        For the communication it uses the following translator methods:
            - is_defined(name)
            - iterator(name)
            - get_value(name, [display_specifier])
        @param translator: the translator used by the class instance
        '''
        self.translator = translator
        self.known_operators = ['style', 'format', 'template', 'template_ref', 'text', 'field', 'element', 'loop', 'if', 'then', 'else', 'elif']
        self.flags = {} # store flags here;
        self.templates = {} # store templates and formats here
        self.start_template_name = None #the name of the template from which the 'execution' starts;
                                        #this is usually a format or the only template found in a doc

    def load_template(self, template_name, template_source=None):
        '''
        Load a BFX template file.
        A template file can have one of two forms:
            - it is a file with a single template. Root tag is 'template'.
              In an API call the single template element is 'executed'.
            - it is a 'style' file which contains exactly one format and zero or more templates. Root tag is 'style' with children 'format' and 'template'(s).
              In this case only the format code is 'executed'. Naturally, in it, it would have references to other templates in the document.

        Template can be given by name (in that case search path is in
        standard directory for bfx template) or directly using the template source.
        If given, template_source overrides template_name

        @param template_name: the name of the BFX template, the same as the name of the filename without the extension
        @return: a DOM tree of the template
        '''
        _ = gettext_set_language(CFG_SITE_LANG)
        if template_source is None:
            template_file_name = CFG_BIBFORMAT_BFX_TEMPLATES_PATH + '/' + template_name + '.' + CFG_BIBFORMAT_BFX_FORMAT_TEMPLATE_EXTENSION
            #load document
            doc = minidom.parse(template_file_name)
        else:
            doc = minidom.parseString(template_source)
        #set exec flag to false and walk document to find templates and formats
        self.flags['exec'] = False
        self.walk(doc)
        #check found templates
        if self.start_template_name:
            start_template = self.templates[self.start_template_name]['node']
        else:
            #print CFG_BIBFORMAT_BFX_WARNING_MESSAGES['WRN_BFX_NO_FORMAT_FOUND']
            if len(self.templates) == 1:
                # no format found, check if there is a default template
                self.start_template_name = self.templates.keys()[0]
                start_template = self.templates[self.start_template_name]['node']
            else:
                #no formats found, templates either zero or more than one
                if len(self.templates) > 1:
                    try:
                        raise InvenioBibFormatBfxError(_('More than one templates found in the document. No format found.'))
                    except InvenioBibFormatBfxError, exc:
                        register_exception()
                        logging.error(exc.message)
                return None
        self.flags['exec'] = True
        return start_template

    def parse_attribute(self, expression):
        '''
        A function to check if an expression is of the special form [!name:display].
        A short form for saying <bx:field name="name" display="tag">, used in element attributes.
        @param expression: a string, usually taken from an attribute value
        @return: if the string is special, parse it and return the corresponding value; else return the initial expression
        '''
        output = expression
        pattern = '\[!(?P<tmp>[\w_.:]*)\]'
        expr = re.compile(pattern)
        match = expr.match(expression)
        if match:
            tmp = match.group('tmp')
            tmp = tmp.split(':')
            var = tmp[0]
            display = ''
            if len(tmp) == 2:
                display = tmp[1]
            output = self.translator.get_value(var, display)
        output = xml_escape(output)
        return output

    def walk(self, parent, out_file=None):
        '''
        Walk a template DOM tree.
        The main function in the parser. It is recursively called until all the nodes are processed.
        This function is used in two different ways:
           - for initial loading of the template (and validation)
           - for 'execution' of a format/template
        The different behaviour is achieved through the use of flags, which can be set to True or False.

        @param parent: a node to process; in an API call this is the root node
        @param out_file: an object to write to; must have a 'write' method

        @return: None
        '''
        _ = gettext_set_language(CFG_SITE_LANG)
        for node in parent.childNodes:
            if node.nodeType == Node.TEXT_NODE:
                value = get_node_value(node)
                value = value.strip()
                if out_file:
                    out_file.write(value)
            if node.nodeType == Node.ELEMENT_NODE:
                #get values
                name, attributes, element_namespace = get_node_name(node), get_node_attributes(node), get_node_namespace(node)
                # write values
                if element_namespace != CFG_BIBFORMAT_BFX_ELEMENT_NAMESPACE:
                    #parse all the attributes
                    for key in attributes.keys():
                        attributes[key] = self.parse_attribute(attributes[key])
                    if node_has_subelements(node):
                        if out_file:
                            out_file.write(create_xml_element(name=name, attrs=attributes, element_type=xmlopen))
                        self.walk(node, out_file) #walk subnodes
                        if out_file:
                            out_file.write(create_xml_element(name=name, element_type=xmlclose))
                    else:
                        if out_file:
                            out_file.write(create_xml_element(name=name, attrs=attributes, element_type=xmlempty))
                #name is a special name, must fall in one of the next cases:
                elif node.localName == 'style':
                    self.ctl_style(node, out_file)
                elif node.localName == 'format':
                    self.ctl_format(node, out_file)
                elif node.localName == 'template':
                    self.ctl_template(node, out_file)
                elif node.localName == 'template_ref':
                    self.ctl_template_ref(node, out_file)
                elif node.localName == 'element':
                    self.ctl_element(node, out_file)
                elif node.localName == 'field':
                    self.ctl_field(node, out_file)
                elif node.localName == 'text':
                    self.ctl_text(node, out_file)
                elif node.localName == 'loop':
                    self.ctl_loop(node, out_file)
                elif node.localName == 'if':
                    self.ctl_if(node, out_file)
                elif node.localName == 'then':
                    self.ctl_then(node, out_file)
                elif node.localName == 'else':
                    self.ctl_else(node, out_file)
                elif node.localName == 'elif':
                    self.ctl_elif(node, out_file)
                else:
                    if node.localName in self.known_operators:
                        try:
                            raise InvenioBibFormatBfxError(_('Note for programmer: you have not implemented operator %s.') % name)
                        except InvenioBibFormatBfxError, exc:
                            register_exception()
                            logging.error(exc.message)
#                        print 'Note for programmer: you haven\'t implemented operator %s.' % (name)
                    else:
                        try:
                            raise InvenioBibFormatBfxError(_('Name %s is not recognised as a valid operator name.') % name)
                        except InvenioBibFormatBfxError, exc:
                            register_exception()
                            logging.error(exc.message)
        return None

    def ctl_style(self, node, out_file):
        '''
        Process a style root node.
        '''
        #exec mode
        if self.flags['exec']:
            return None
        #test mode
        self.walk(node, out_file)
        return None

    def ctl_format(self, node, out_file):
        '''
        Process a format node.
        Get name, description and content attributes.
        This function is called only in test mode.
        '''
        _ = gettext_set_language(CFG_SITE_LANG)
        #exec mode
        if self.flags['exec']:
            return None
        #test mode
        attrs = get_node_attributes(node)
        #get template name and give control to ctl_template
        if attrs.has_key('name'):
            name = attrs['name']
            if self.templates.has_key(name):
                try:
                    raise InvenioBibFormatBfxError(_('Duplicate name: %s.') % name)
                except InvenioBibFormatBfxError, exc:
                    register_exception()
                    logging.error(exc.message)
                return None
            self.start_template_name = name
            self.ctl_template(node, out_file)
        else:
            try:
                raise InvenioBibFormatBfxError(_('No name defined for the template.'))
            except InvenioBibFormatBfxError, exc:
                register_exception()
                logging.error(exc.message)
            return None
        return None

    def ctl_template(self, node, out_file):
        '''
        Process a template node.
        Get name, description and content attributes.
        Register name and store for later calls from template_ref.
        This function is called only in test mode.
        '''
        _ = gettext_set_language(CFG_SITE_LANG)
        #exec mode
        if self.flags['exec']:
            return None
        #test mode
        attrs = get_node_attributes(node)
        #get template name
        if attrs.has_key('name'):
            name = attrs['name']
            if self.templates.has_key(name):
                try:
                    raise InvenioBibFormatBfxError(_('Duplicate name: %s.') % name)
                except InvenioBibFormatBfxError, exc:
                    register_exception()
                    logging.error(exc.message)
                return None
            self.templates[name] = {}
            self.templates[name]['node'] = node
        else:
            try:
                raise InvenioBibFormatBfxError(_('No name defined for the template.'))
            except InvenioBibFormatBfxError, exc:
                register_exception()
                logging.error(exc.message)
            return None
        #get template description
        if attrs.has_key('description'):
            description = attrs['description']
        else:
            description = ''
            try:
                raise InvenioBibFormatBfxWarning(_('No description entered for the template.'))
            except InvenioBibFormatBfxWarning, exc:
                register_exception(stream='warning')
                logging.warning(exc.message)
        self.templates[name]['description'] = description
        #get content-type of resulting output
        if attrs.has_key('content'):
            content_type = attrs['content']
        else:
            content_type = 'text/xml'
            try:
                raise InvenioBibFormatBfxWarning(_('No content type specified for the template. Using default: text/xml.'))
            except InvenioBibFormatBfxWarning, exc:
                register_exception(stream='warning')
                logging.warning(exc.message)
        self.templates[name]['content_type'] = content_type
        #walk node
        self.walk(node, out_file)
        return None

    def ctl_template_ref(self, node, out_file):
        '''
        Reference to an external template.
        This function is called only in execution mode. Bad references appear as run-time errors.
        '''
        _ = gettext_set_language(CFG_SITE_LANG)
        #test mode
        if not self.flags['exec']:
            return None
        #exec mode
        attrs = get_node_attributes(node)
        if not attrs.has_key('name'):
            try:
                raise InvenioBibFormatBfxError(_('Missing attribute "name" in TEMPLATE_REF.'))
            except InvenioBibFormatBfxError, exc:
                register_exception()
                logging.error(exc.message)
            return None
        name = attrs['name']
        #first check for a template in the same file, that is in the already cached templates
        if self.templates.has_key(name):
            node_to_walk = self.templates[name]['node']
            self.walk(node_to_walk, out_file)
        else:
            #load a file and execute it
            pass
            #template_file_name = CFG_BIBFORMAT_BFX_TEMPLATES_PATH + name + '/' + CFG_BIBFORMAT_BFX_FORMAT_TEMPLATE_EXTENSION
            #try:
            #    node = minidom.parse(template_file_name)
            #except:
            #    print CFG_BIBFORMAT_BFX_ERROR_MESSAGES['ERR_BFX_TEMPLATE_NOT_FOUND'] % (template_file_name)
        return None

    def ctl_element(self, node, out_file):
        '''
        Call an external element (written in Python).
        '''
        _ = gettext_set_language(CFG_SITE_LANG)
        #test mode
        if not self.flags['exec']:
            return None
        #exec mode
        parameters = get_node_attributes(node)
        if not parameters.has_key('name'):
            try:
                raise InvenioBibFormatBfxError(_('Missing attribute "name" in ELEMENT.'))
            except InvenioBibFormatBfxError, exc:
                register_exception()
                logging.error(exc.message)
            return None
        function_name = parameters['name']
        del parameters['name']
        #now run external bfe_name.py, with param attrs
        if function_name:
            value = self.translator.call_function(function_name, parameters)
            value = xml_escape(value)
            out_file.write(value)
        return None

    def ctl_field(self, node, out_file):
        '''
        Get the value of a field by its name.
        '''
        _ = gettext_set_language(CFG_SITE_LANG)
        #test mode
        if not self.flags['exec']:
            return None
        #exec mode
        attrs = get_node_attributes(node)
        if not attrs.has_key('name'):
            try:
                raise InvenioBibFormatBfxError(_('Missing attribute "name" in FIELD.'))
            except InvenioBibFormatBfxError, exc:
                register_exception()
                logging.error(exc.message)
            return None
        display = ''
        if attrs.has_key('display'):
            display = attrs['display']
        var = attrs['name']
        if not self.translator.is_defined(var):
            try:
                raise InvenioBibFormatBfxError(_('Field %s is not defined.') % var)
            except InvenioBibFormatBfxError, exc:
                register_exception()
                logging.error(exc.message)
            return None
        value = self.translator.get_value(var, display)
        value = xml_escape(value)
        out_file.write(value)
        return None

    def ctl_text(self, node, out_file):
        '''
        Output a text
        '''
        _ = gettext_set_language(CFG_SITE_LANG)
        #test mode
        if not self.flags['exec']:
            return None
        #exec mode
        attrs = get_node_attributes(node)
        if not attrs.has_key('value'):
            try:
                raise InvenioBibFormatBfxError(_('Missing attribute "value" in TEXT.'))
            except InvenioBibFormatBfxError, exc:
                register_exception()
                logging.error(exc.message)
            return None
        value = attrs['value']
        value = value.replace(r'\n', '\n')
        #value = xml_escape(value)
        if type(value) == type(u''):
            value = value.encode('utf-8')
        out_file.write(value)
        return None

    def ctl_loop(self, node, out_file):
        '''
        Loop through a set of values.
        '''
        _ = gettext_set_language(CFG_SITE_LANG)
        #test mode
        if not self.flags['exec']:
            self.walk(node, out_file)
            return None
        #exec mode
        attrs = get_node_attributes(node)
        if not attrs.has_key('object'):
            try:
                raise InvenioBibFormatBfxError(_('Missing attribute "object" in LOOP.'))
            except InvenioBibFormatBfxError, exc:
                register_exception()
                logging.error(exc.message)
            return None
        name = attrs['object']
        if not self.translator.is_defined(name):
            try:
                raise InvenioBibFormatBfxError(_('Field %s is not defined.') % name)
            except InvenioBibFormatBfxError, exc:
                register_exception()
                logging.error(exc.message)
            return None
        for new_object in self.translator.iterator(name):
            self.walk(node, out_file)
        return None

    def ctl_if(self, node, out_file):
        '''
        An if/then/elif/.../elif/else construct.
        'If' can have several forms:
        <if name="var"/>                  : True if var is non-empty, eval as string
        <if name="var" eq="value"/>       : True if var=value, eval as string
        <if name="var" lt="value"/>       : True if var<value, try to eval as num, else eval as string
        <if name="var" gt="value"/>       : True if var>value, try to eval as num, else eval as string
        <if name="var" le="value"/>       : True if var<=value, try to eval as num, else eval as string
        <if name="var" ge="value"/>       : True if var>=value, try to eval as num, else eval as string
        <if name="var" in="val1 val2"/>   : True if var in [val1, val2], eval as string
        <if name="var" nin="val1 val2"/>  : True if var not in [val1, val2], eval as string
        <if name="var" neq="value"/>      : True if var!=value, eval as string
        <if name="var" like="regexp"/>    : Match against a regular expression

        Example::
            <if name="author" eq="Pauli">
              <then>Pauli</then>
              <elif name="" eq="Einstein">
                <then>Pauli</then>
                <else>other</else>
              </elif>
            </if>
        '''
        _ = gettext_set_language(CFG_SITE_LANG)
        #test mode
        if not self.flags['exec']:
            self.walk(node, out_file)
            return None
        #exec mode
        attrs = get_node_attributes(node)
        if not attrs.has_key('name'):
            try:
                raise InvenioBibFormatBfxError(_('Missing attrbute "name" in IF.'))
            except InvenioBibFormatBfxError, exc:
                register_exception()
                logging.error(exc.message)
            return None
        #determine result
        var = attrs['name']
        if not self.translator.is_defined(var):
            try:
                raise InvenioBibFormatBfxError(_('Field %s is not defined.') % var)
            except InvenioBibFormatBfxError, exc:
                register_exception()
                logging.error(exc.message)
            return None
        value = self.translator.get_value(var)
        value = value.strip()
        #equal
        if attrs.has_key('eq'):
            pattern = attrs['eq']
            if is_number(pattern) and is_number(value):
                result = (float(value)==float(pattern))
            else:
                result = (value==pattern)
        #not equal
        elif attrs.has_key('neq'):
            pattern = attrs['neq']
            if is_number(pattern) and is_number(value):
                result = (float(value)!=float(pattern))
            else:
                result = (value!=pattern)
        #lower than
        elif attrs.has_key('lt'):
            pattern = attrs['lt']
            if is_number(pattern) and is_number(value):
                result = (float(value)<float(pattern))
            else:
                result = (value<pattern)
        #greater than
        elif attrs.has_key('gt'):
            pattern = attrs['gt']
            if is_number(pattern) and is_number(value):
                result = (float(value)>float(pattern))
            else:
                result = (value>pattern)
        #lower or equal than
        elif attrs.has_key('le'):
            pattern = attrs['le']
            if is_number(pattern) and is_number(value):
                result = (float(value)<=float(pattern))
            else:
                result = (value<=pattern)
        #greater or equal than
        elif attrs.has_key('ge'):
            pattern = attrs['ge']
            if is_number(pattern) and is_number(value):
                result = (float(value)>=float(pattern))
            else:
                result = (value>=pattern)
        #in
        elif attrs.has_key('in'):
            pattern = attrs['in']
            values = pattern.split()
            result = (value in values)
        #not in
        elif attrs.has_key('nin'):
            pattern = attrs['nin']
            values = pattern.split()
            result = (value not in values)
        #match against a regular expression
        elif attrs.has_key('like'):
            pattern = attrs['like']
            try:
                expr = re.compile(pattern)
                result = expr.match(value)
            except:
                try:
                    raise InvenioBibFormatBfxError(_('Invalid regular expression: %s.') % pattern)
                except InvenioBibFormatBfxError, exc:
                    register_exception()
                    logging.error(exc.message)
        #simple form: True if non-empty, otherwise False
        else:
            result = value
        #end of evaluation
        #=================
        #validate subnodes
        then_node = get_node_subelement(node, 'then', CFG_BIBFORMAT_BFX_ELEMENT_NAMESPACE)
        else_node = get_node_subelement(node, 'else', CFG_BIBFORMAT_BFX_ELEMENT_NAMESPACE)
        elif_node = get_node_subelement(node, 'elif', CFG_BIBFORMAT_BFX_ELEMENT_NAMESPACE)
        #having else and elif siblings at the same time is a syntax error
        if (else_node is not None) and (elif_node is not None):
            try:
                raise InvenioBibFormatBfxError(_('Invalid syntax of IF statement.'))
            except InvenioBibFormatBfxError, exc:
                register_exception()
                logging.error(exc.message)
            return None
        #now walk appropriate nodes, according to the result
        if result: #True
            if then_node:
                self.walk(then_node, out_file)
            #todo: add short form, without 'then', just elements within if statement to walk on 'true' and no 'elif' or 'else' elements
        else:      #False
            if elif_node:
                self.ctl_if(elif_node, out_file)
            elif else_node:
                self.walk(else_node, out_file)
        return None

    def ctl_then(self, node, out_file):
        '''
        Calling 'then' directly from the walk function means a syntax error.
        '''
        _ = gettext_set_language(CFG_SITE_LANG)
        #test mode
        if not self.flags['exec']:
            self.walk(node, out_file)
            return None
        #exec mode
        try:
            raise InvenioBibFormatBfxError(_('Invalid syntax of IF statement.'))
        except InvenioBibFormatBfxError, exc:
            register_exception()
            logging.error(exc.message)
        return None

    def ctl_else(self, node, out_file):
        '''
        Calling 'else' directly from the walk function means a syntax error.
        '''
        _ = gettext_set_language(CFG_SITE_LANG)
        #test mode
        if not self.flags['exec']:
            self.walk(node, out_file)
            return None
        #exec mode
        try:
            raise InvenioBibFormatBfxError(_('Invalid syntax of IF statement.'))
        except InvenioBibFormatBfxError, exc:
            register_exception()
            logging.error(exc.message)
        return None

    def ctl_elif(self, node, out_file):
        '''
        Calling 'elif' directly from the walk function means a syntax error.
        '''
        _ = gettext_set_language(CFG_SITE_LANG)
        #test mode
        if not self.flags['exec']:
            self.walk(node, out_file)
            return None
        #exec mode
        try:
            raise InvenioBibFormatBfxError(_('Invalid syntax of IF statement.'))
        except InvenioBibFormatBfxError, exc:
            register_exception()
            logging.error(exc.message)
        return None


class MARCTranslator:
    '''
    memory[name]
    [name]['addresses'] - the set of rules for each of the defined names
    [name]['parent'] - the name of the parent; '' if none;
    [name]['children'] - a list with the name of the children of every variable
    [name]['object'] - stored state of object for performance efficiency
    '''
    def __init__(self, labels=None):
        '''
        Create an instance of the translator and init with the list of the defined labels and their rules.
        '''
        _ = gettext_set_language(CFG_SITE_LANG)
        if labels is None:
            labels = {}
        self.recIDs = []
        self.recID = 0
        self.recID_index = 0
        self.record = None
        self.memory = {}
        pattern = address_pattern
        expr = re.compile(pattern)
        for name in labels.keys():
            self.memory[name] = {}
            self.memory[name]['object'] = None
            self.memory[name]['parent'] = ''
            self.memory[name]['children'] = []
            self.memory[name]['addresses'] = p_copy.deepcopy(labels[name])
        for name in self.memory:
            for i in range(len(self.memory[name]['addresses'])):
                address = self.memory[name]['addresses'][i]
                match = expr.match(address)
                if not match:
                    try:
                        raise InvenioBibFormatBfxError(_('Invalid address: %s %s') % (name, address))
                    except InvenioBibFormatBfxError, exc:
                        register_exception()
                        logging.error(exc.message)
#                    print 'Invalid address: ', name, address
                else:
                    parent_name = match.group('parent')
                    if parent_name:
                        if not self.memory.has_key(parent_name):
                            try:
                                raise InvenioBibFormatBfxError(_('Field %s is not defined.') % parent_name)
                            except InvenioBibFormatBfxError, exc:
                                register_exception()
                                logging.error(exc.message)
                        else:
                            self.memory[name]['parent'] = parent_name
                            #now make parent aware of children
                            if not name in self.memory[parent_name]['children']:
                                self.memory[parent_name]['children'].append(name)
                            level = self.determine_level(parent_name)
                            self.memory[name]['addresses'][i] = self.memory[name]['addresses'][i].replace(parent_name, '/'*level)
        #special case 'record'
        self.memory['record'] = {}
        self.memory['record']['object'] = None
        self.memory['record']['parent'] = ''
        self.memory['record']['children'] = []

    def set_record_ids(self, recIDs, preprocess=None):
        '''
        Initialize the translator with the set of record IDs.
        @param recIDs: a list of the record IDs
        @param preprocess: an optional function which acts on every record structure after creating it
               This can be used to enrich the record with fields not present in the record initially,
               verify the record data or whatever plausible.
               Another solution is to use external function elements.
        '''
        self.record = None
        self.recIDs = recIDs
        self.preprocess = preprocess
        if self.recIDs:
            self.recID_index = 0
            self.recID = self.recIDs[self.recID_index]
            self.record = get_bfx_record(self.recID)
            if self.preprocess:
                self.preprocess(self.record)
        return None

    def determine_level(self, name):
        '''
        Determine the type of the variable, whether this is an instance or a subfield.
        This is done by observing the first provided address for the name.
        todo: define variable types in config file, remove this function, results in a clearer concept
        '''
        level = 0 #default value
        if self.memory.has_key(name):
            expr = re.compile(address_pattern)
            if self.memory[name]['addresses']:
                match = expr.match(self.memory[name]['addresses'][0])
                if match:
                    tag = match.group('tag')
                    code = match.group('code')
                    reg = match.group('reg')
                    if reg:
                        level = 2 #subfield
                    elif code:
                        level = 2 #subfield
                    elif tag:
                        level = 1 #instance
        return level

    #========================================
    #API functions for quering the translator
    #========================================
    def is_defined(self, name):
        '''
        Check whether a variable is defined.
        @param name: the name of the variable
        '''
        return self.memory.has_key(name)

    def get_num_elements(self, name):
        '''
        An API function to get the number of elements for a variable.
        Do not use this function to build loops, Use iterator instead.
        '''
        if name == 'record':
            return len(self.recIDs)
        num = 0
        for part in self.iterator(name):
            num = num + 1
        return num

    def get_value(self, name, display_type='value'):
        '''
        The API function for quering the translator for values of a certain variable.
        Called in a loop will result in a different value each time.
        Objects are cached in memory, so subsequent calls for the same variable take less time.
        @param name: the name of the variable you want the value of
        @param display_type: an optional value for the type of the desired output, one of: value, tag, ind1, ind2, code, fulltag;
               These can be easily added in the proper place of the code (display_value)
        '''
        if name == 'record':
            return ''
        record = self.get_object(name)
        return self.display_record(record, display_type)

    def iterator(self, name):
        '''
        An iterator over the values of a certain name.
        The iterator changes state of internal variables and objects.
        When calling get_value in a loop, this will result each time in a different value.
        '''
        if name == 'record':
            for self.recID in self.recIDs:
                self.record = get_bfx_record(self.recID)
                if self.preprocess:
                    self.preprocess(self.record)
                yield str(self.recID)
        else:
            full_object = self.build_object(name)
            level = self.determine_level(name)
            for new_object in record_parts(full_object, level):
                self.memory[name]['object'] = new_object
                #parent has changed state; also set childs state to None;
                for children_name in self.memory[name]['children']:
                    self.memory[children_name]['object'] = None
                yield new_object
            #the result for a call of the same name after an iterator should be the same as if there was no iterator called before
            self.memory[name]['object'] = None

    def call_function(self, function_name, parameters=None):
        '''
        Call an external element which is a Python file, using BibFormat
        @param function_name: the name of the function to call
        @param parameters: a dictionary of the parameters to pass as key=value pairs
        @return: a string value, which is the result of the function call
        '''
        if parameters is None:
            parameters = {}
        bfo = BibFormatObject(self.recID)
        format_element = get_format_element(function_name)
        (value, dummy) = eval_format_element(format_element, bfo, parameters)
        #to do: check errors from function call
        return value

    #========================================
    #end of API functions
    #========================================

    def get_object(self, name):
        '''
        Responsible for creating the desired object, corresponding to provided name.
        If object is not cached in memory, it is build again.
        Directly called by API function get_value.
        The result is then formatted by display_record according to display_type.
        '''
        if self.memory[name]['object'] is not None:
            return self.memory[name]['object']
        new_object = self.build_object(name)
        #if you have reached here you are not in an iterator; return first non-empty
        level = self.determine_level(name)
        for tmp_object in record_parts(new_object, level):
            #get the first non-empty
            if tmp_object:
                new_object = tmp_object
                break
        self.memory[name]['object'] = new_object
        return new_object

    def build_object(self, name):
        '''
        Build the object from the list of addresses
        A slave function for get_object.
        '''
        new_object = {}
        parent_name = self.memory[name]['parent'];
        has_parent = parent_name
        for address in self.memory[name]['addresses']:
            if not has_parent:
                tmp_object = copy(self.record, address)
                new_object = merge(new_object, tmp_object)
            else: #has parent
                parent_object = self.get_object(parent_name) #already returns the parents instance
                tmp_object = copy(parent_object, address)
                new_object = merge(new_object, tmp_object)
        return new_object


    def display_record(self, record, display_type='value'):
        '''
        Decide what the final output value is according to the display_type.
        @param record: the record structure to display; this is most probably just a single subfield
        @param display_type: a string specifying the desired output; can be one of: value, tag, ind1, ind2, code, fulltag
        @return: a string to output
        '''
        _ = gettext_set_language(CFG_SITE_LANG)
        output = ''
        tag, ind1, ind2, code, value = '', '', '', '', ''
        if record:
            tags = record.keys()
            tags.sort()
            if tags:
                fulltag = tags[0]
                tag, ind1, ind2 = fulltag[0:3], fulltag[3:4], fulltag[4:5]
                field_instances = record[fulltag]
                if field_instances:
                    field_instance = field_instances[0]
                    codes = field_instance.keys()
                    codes.sort()
                    if codes:
                        code = codes[0]
                        value = field_instance[code]
        if not display_type:
            display_type = 'value'
        if display_type == 'value':
            output = value
        elif display_type == 'tag':
            output = tag
        elif display_type == 'ind1':
            ind1 = ind1.replace('_', ' ')
            output = ind1
        elif display_type=='ind2':
            ind2 = ind2.replace('_', ' ')
            output = ind2
        elif display_type == 'code':
            output = code
        elif display_type == 'fulltag':
            output = tag + ind1 + ind2
        else:
            try:
                raise InvenioBibFormatBfxError(_('Invalid display type. Must be one of: value, tag, ind1, ind2, code; received: %s.') % display_type)
            except InvenioBibFormatBfxError, exc:
                register_exception()
                logging.error(exc.message)
        return output

'''
Functions for use with the structure representing a MARC record defined here.
This record structure differs from the one defined in bibrecord.
The reason is that we want a symmetry between controlfields and datafields.
In this format controlfields are represented internally as a subfield value with code ' ' of a datafield.
This allows for easier handling of the fields.
However, there is a restriction associated with this structure and it is that subfields cannot be repeated
in the same instance. If this is the case, the result will be incorrect.

The record structure has the form:

   fields={field_tag:field_instances}
     field_instances=[field_instance]
       field_instance={field_code:field_value}

'''
def convert_record(old_record):
    '''
    Convert a record from the format defined in bibrecord to the format defined here
    @param old_record: the record as returned from bibrecord.create_record()
    @return: a record of the new form
    '''
    _ = gettext_set_language(CFG_SITE_LANG)
    fields = {}
    old_tags = old_record.keys()
    old_tags.sort()
    for old_tag in old_tags:
        if int(old_tag) < 11:
            #controlfields
            new_tag = old_tag
            fields[new_tag] = [{' ':old_record[old_tag][0][3]}]
        else:
            #datafields
            old_field_instances = old_record[old_tag]
            num_fields = len(old_field_instances)
            for i in range(num_fields):
                old_field_instance = old_field_instances[i]
                ind1 = old_field_instance[1]
                if not ind1 or ind1 == ' ':
                    ind1 = '_'
                ind2 = old_field_instance[2]
                if not ind2 or ind2 == ' ':
                    ind2 = '_'
                new_tag = old_tag + ind1 + ind2
                new_field_instance = {}
                for old_subfield in old_field_instance[0]:
                    new_code = old_subfield[0]
                    new_value = old_subfield[1]
                    if new_field_instance.has_key(new_code):
                        try:
                            raise InvenioBibFormatBfxError(_('Repeating subfield codes in the same instance!'))
                        except InvenioBibFormatBfxError, exc:
                            register_exception()
                            logging.error(exc.message)
#                        print 'Error: Repeating subfield codes in the same instance!'
                    new_field_instance[new_code] = new_value
                if not fields.has_key(new_tag):
                    fields[new_tag] = []
                fields[new_tag].append(new_field_instance)
    return fields

def get_bfx_record(recID):
    '''
    Get a record with a specific recID.
    @param recID: the ID of the record
    @return: a record in the structure defined here
    '''
    bfo = BibFormatObject(recID)
    return convert_record(bfo.get_record())

def print_bfx_record(record):
    '''
    Print a record.
    '''
    tags = record.keys()
    tags.sort()
    for tag in tags:
        field_instances = record[tag]
        for field_instance in field_instances:
            print tag, field_instance

def record_fields_value(record, tag, subfield):
    '''
    Return a list of all the fields with a certain tag and subfield code.
    Works on subfield level.
    @param record: a record
    @param tag: a 3 or 5 letter tag; required
    @param subfield: a subfield code; required
    '''
    output = []
    if record.has_key(tag):
        for field_instance in record[tag]:
            if field_instance.has_key(subfield):
                output.append(field_instance[subfield])
    return output


def record_add_field_instance(record, tag, field_instance):
    '''
    Add a field_instance to the beginning of the instances of a corresponding tag.
    @param record: a record
    @param tag: a 3 or 5 letter tag; required
    @param field_instance: the field instance to add
    @return: None
    '''
    if not record.has_key(tag):
        record[tag] = []
    record[tag] = [field_instance] + record[tag]
    return None

def record_num_parts(record, level):
    '''
    Count the number of instances or the number of subfields in the whole record.
    @param record: record to consider for counting
    @param level: either 1 or 2
           level=1 - view record on instance level
           level=2 - view record on subfield level
    @return: the number of parts
    '''
    num = 0
    for part in record_parts(record, level):
        num = num + 1

def record_parts(record, level):
    '''
    An iterator over the instances or subfields of a record.
    @param record: record to consider for iterating
    @param level: either 1 or 2
            - level=1: iterate over instances
            - level=2: iterate over subfields
    @return: a record structure representing the part (instance or subfield)
    '''
    if level == 1:
        names = record.keys()
        names.sort()
        for name in names:
            old_field_instances = record[name]
            for old_field_instance in old_field_instances:
                new_record = {}
                new_field_instances = []
                new_field_instance = {}
                for old_field_code in old_field_instance.keys():
                    new_field_code = old_field_code
                    new_field_value = old_field_instance[old_field_code]
                    new_field_instance[new_field_code] = new_field_value
                new_field_instances.append(new_field_instance)
                new_record[name] = []
                new_record[name].extend(new_field_instances)
                yield new_record
    if level == 2:
        names = record.keys()
        names.sort()
        for name in names:
            old_field_instances = record[name]
            for old_field_instance in old_field_instances:
                old_field_codes = old_field_instance.keys()
                old_field_codes.sort()
                for old_field_code in old_field_codes:
                    new_record = {}
                    new_field_instances = []
                    new_field_instance = {}
                    new_field_code = old_field_code
                    new_field_value = old_field_instance[old_field_code]
                    new_field_instance[new_field_code] = new_field_value
                    new_field_instances.append(new_field_instance)
                    new_record[name] = []
                    new_record[name].extend(new_field_instances)
                    yield new_record


def copy(old_record, address=''):
    '''
    Copy a record by filtering all parts of the old record specified by address
    (A better name for the function is filter.)
    @param old_record: the initial record
    @param address: an address; for examples see bibformat_bfx_engine_config.
           If no address is specified, return the initial record.
    @return: the filtered record
    '''
    if not old_record:
        return {}
    tag_pattern, code_pattern, reg_pattern = '', '', ''
    expr = re.compile(address_pattern)
    match = expr.match(address)
    if match:
        tag_pattern = match.group('tag')
        code_pattern = match.group('code')
        reg_pattern = match.group('reg')
    if tag_pattern:
        tag_pattern = tag_pattern.replace('?','[0-9_\w]')
    else:
        tag_pattern = r'.*'
    if code_pattern:
        code_pattern = code_pattern.replace('?','[\w ]')
    else:
        code_pattern = r'.*'
    tag_expr = re.compile(tag_pattern)
    code_expr = re.compile(code_pattern)
    new_record = {}
    for tag in old_record.keys():
        tag_match = tag_expr.match(tag)
        if tag_match:
            if tag_match.end() == len(tag):
                old_field_instances = old_record[tag]
                new_field_instances = []
                for old_field_instance in old_field_instances:
                    new_field_instance = {}
                    for old_field_code in old_field_instance.keys():
                        new_field_code = old_field_code
                        code_match = code_expr.match(new_field_code)
                        if code_match:
                            new_field_value = old_field_instance[old_field_code]
                            new_field_instance[new_field_code] = new_field_value
                    if new_field_instance:
                        new_field_instances.append(new_field_instance)
                if new_field_instances:
                    new_record[tag] = new_field_instances
    #in new_record pass all subfields through regexp
    if reg_pattern:
        for tag in new_record:
            field_instances = new_record[tag]
            for field_instance in field_instances:
                field_codes = field_instance.keys()
                for field_code in field_codes:
                    field_instance[field_code] = pass_through_regexp(field_instance[field_code], reg_pattern)
    return new_record

def merge(record1, record2):
    '''
    Merge two records.
    Controlfields with the same tag in record2 as in record1 are ignored.

    @param record1: first record to merge
    @param record2: second record to merge
    @return: the merged record
    '''
    new_record = {}
    if record1:
        new_record = copy(record1)
    if not record2:
        return new_record
    for tag in record2.keys():
        #append only datafield tags;
        #if controlfields conflict, leave first;
        old_field_instances = record2[tag]
        new_field_instances = []
        for old_field_instance in old_field_instances:
            new_field_instance = {}
            for old_field_code in old_field_instance.keys():
                new_field_code = old_field_code
                new_field_value = old_field_instance[old_field_code]
                new_field_instance[new_field_code] = new_field_value
            if new_field_instance:
                new_field_instances.append(new_field_instance)
        if new_field_instances:
            #controlfield
            if len(tag) == 3:
                if not new_record.has_key(tag):
                    new_record[tag] = []
                    new_record[tag].extend(new_field_instances)
            #datafield
            if len(tag) == 5:
                if not new_record.has_key(tag):
                    new_record[tag] = []
                new_record[tag].extend(new_field_instances)
    return new_record


#======================
#Help functions
#=====================

xmlopen = 1
xmlclose = 2
xmlfull = 3
xmlempty = 4

def create_xml_element(name, value='', attrs=None, element_type=xmlfull, level=0):
    '''
    Create a XML element as string.
    @param name: the name of the element
    @param value: the element value; default is ''
    @param attrs: a dictionary with the element attributes
    @param element_type: a constant which defines the type of the output
           xmlopen = 1   <element attr="attr_value">
           xmlclose = 2  </element>
           xmlfull = 3   <element attr="attr_value">value</element>
           xmlempty = 4  <element attr="attr_value"/>
    @return: a formatted XML string
    '''
    output = ''
    if attrs is None:
        attrs = {}
    if element_type == xmlempty:
        output += '<'+name
        for attrname in attrs.keys():
            attrvalue = attrs[attrname]
            if type(attrvalue) == type(u''):
                attrvalue = attrvalue.encode('utf-8')
            output += ' %s="%s"' % (attrname, attrvalue)
        output += ' />'
    if element_type == xmlfull:
        output += '<'+name
        for attrname in attrs.keys():
            attrvalue = attrs[attrname]
            if type(attrvalue) == type(u''):
                attrvalue = attrvalue.encode('utf-8')
            output += ' %s="%s"' % (attrname, attrvalue)
        output += '>'
        output += value
        output += '</'+name+'>'
    if element_type == xmlopen:
        output += '<'+name
        for attrname in attrs.keys():
            output += ' '+attrname+'="'+attrs[attrname]+'"'
        output += '>'
    if element_type == xmlclose:
        output += '</'+name+'>'
    output = '  '*level + output
    if type(output) == type(u''):
        output = output.encode('utf-8')
    return output

def xml_escape(value):
    '''
    Escape a string value for use as a xml element or attribute value.
    @param value: the string value to escape
    @return: escaped value
    '''
    return saxutils.escape(value)

def xml_unescape(value):
    '''
    Unescape a string value for use as a xml element.
    @param value: the string value to unescape
    @return: unescaped value
    '''
    return saxutils.unescape(value)

def node_has_subelements(node):
    '''
    Check if a node has any childnodes.
    Check for element or text nodes.
    @return: True if childnodes exist, False otherwise.
    '''
    result = False
    for node in node.childNodes:
        if node.nodeType == Node.ELEMENT_NODE or node.nodeType == Node.TEXT_NODE:
            result = True
    return result

def get_node_subelement(parent_node, name, namespace = None):
    '''
    Get the first childnode with specific name and (optional) namespace
    @param parent_node: the node to check
    @param name: the name to search
    @param namespace: An optional namespace URI. This is usually a URL: http://invenio-software.org/
    @return: the found node; None otherwise
    '''
    output = None
    for node in parent_node.childNodes:
        if node.nodeType == Node.ELEMENT_NODE and node.localName == name and node.namespaceURI == namespace:
            output = node
            return output
    return output

def get_node_value(node):
    '''
    Get the node value of a node. For use with text nodes.
    @param node: a text node
    @return: a string of the nodevalue encoded in utf-8
    '''
    return node.nodeValue.encode('utf-8')

def get_node_namespace(node):
    '''
    Get node namespace. For use with element nodes.
    @param node: an element node
    @return: the namespace of the node
    '''
    return node.namespaceURI

def get_node_name(node):
    '''
    Get the node value of a node. For use with element nodes.
    @param node: an element node
    @return: a string of the node name
    '''
    return node.nodeName

def get_node_attributes(node):
    '''
    Get attributes of an element node.  For use with element nodes
    @param node: an element node
    @return: a dictionary of the attributes as key:value pairs
    '''
    attributes = {}
    attrs = node.attributes
    for attrname in attrs.keys():
        attrnode = attrs.get(attrname)
        attrvalue = attrnode.nodeValue
        attributes[attrname] = attrvalue
    return attributes

def pass_through_regexp(value, regexp):
    '''
    Pass a value through a regular expression.
    @param value: a string
    @param regexp: a regexp with a group 'value' in it. No group named 'value' will result in an error.
    @return: if the string matches the regexp, return named group 'value', otherwise return ''
    '''
    output = ''
    expr = re.compile(regexp)
    match = expr.match(value)
    if match:
        output = match.group('value')
    return output

def is_number(value):
    '''
    Check if a value is a number.
    @param value: the value to check
    @return: True or False
    '''
    result = True
    try:
        float(value)
    except ValueError:
        result = False
    return result
