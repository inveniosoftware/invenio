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

"""
bibconvert_bfx_engine - XML processing library for Invenio
                        using bfx stylesheets.

Does almost what an XSLT processor does, but using a special
syntax for the transformation stylesheet: a combination of
'BibFormat for XML' (bibformat bfx) templates and XPath is
used.

Dependencies: bibformat_bfx_engine.py

Used by: bibconvert.in
"""

__revision__ = "$Id$"

import sys
import os

from cStringIO import StringIO
processor_type = -1
try:
    # Try to load
    from xml.xpath import Evaluate
    from xml.dom import minidom, Node
    from xml.xpath.Context import Context
    processor_type = 0
except ImportError:
    pass

# TODO: Try to explicitely load 4suite Xpath
# <http://4suite.org/docs/howto/UNIX.xml#PyXML>
# From <http://uche.ogbuji.net/tech/akara/nodes/2003-01-01/basic-xpath>:
## 1. PyXML usage (do not use with 4Suite)
##        * import xml.xslt
##        * import xml.xpath
## 2. 4Suite usage (use these imports)
##        * import Ft.Xml.XPath
##        * import Ft.Xml.Xslt

from invenio.modules.formatter.engines import bfx as bibformat_bfx_engine

from .registry import templates


def convert(xmltext, template_filename=None, template_source=None):
    """
    Processes an XML text according to a template, and returns the result.

    The template can be given either by name (or by path) or by source.
    If source is given, name is ignored.

    bibconvert_bfx_engine will look for template_filename in standard directories
    for templates. If not found, template_filename will be assumed to be a path to
    a template. If none can be found, return None.

    Raises an exception if cannot find an appropriate XPath module.

    @param xmltext: The string representation of the XML to process
    @param template_filename: The name of the template to use for the processing
    @param template_source: The configuration describing the processing.
    @return: the transformed XML text.
    """
    if processor_type == -1:
        # No XPath processor found
        raise "No XPath processor could be found"

    # Retrieve template and read it
    if template_source:
        template = template_source
    elif template_filename:
        try:
            path_to_templates = templates.get(template_filename, '')
            if os.path.exists(path_to_templates):
                template = file(path_to_templates).read()
            elif os.path.exists(template_filename):
                template = file(template_filename).read()
            else:
                sys.stderr.write(template_filename +' does not exist.')
                return None
        except IOError:
            sys.stderr.write(template_filename +' could not be read.')
            return None
    else:
        sys.stderr.write(template_filename +' was not given.')
        return None

    # Prepare some variables
    out_file = StringIO() # Virtual file-like object to write result in
    trans = XML2XMLTranslator()
    trans.set_xml_source(xmltext)
    parser = bibformat_bfx_engine.BFXParser(trans)

    # Load template
    # This might print some info. Redirect to stderr
    # but do no print on standard output
    standard_output = sys.stdout
    sys.stdout = sys.stderr
    # Always set 'template_name' to None, otherwise
    # bibformat for XML will look for it in wrong directory
    template_tree = parser.load_template(template_name=None,
                                         template_source=template)
    sys.stdout = standard_output

    # Transform the source using loaded template
    parser.walk(template_tree, out_file)
    output = out_file.getvalue()
    return output

class XML2XMLTranslator:
    """
    Generic translator for XML.
    """
    def __init__(self):
        '''
        Create an instance of the translator and init with the list of the defined labels and their rules.
        '''
        self.xml_source = ''
        self.dom = None
        self.current_node = None
        self.namespaces = {}

    def is_defined(self, name):
        '''
        Check whether a variable is defined.

        Accept all names. get_value will return empty string if not exist

        @param name: the name of the variable
        '''
        return True
##         context = Context(self.current_node, processorNss=self.namespaces)

##         results_list = Evaluate(name, context=context)
##         if results_list != []:
##             return True
##         else:
##             return False

    def get_num_elements(self, name):
        '''
        An API function to get the number of elements for a variable.
        Do not use this function to build loops, Use iterator instead.
        '''
        context = Context(self.current_node, processorNss=self.namespaces)
        results_list = Evaluate(name, context=context)
        return len(results_list)

    def get_value(self, name, display_type='value'):
        '''
        The API function for quering the translator for values of a certain variable.
        Called in a loop will result in a different value each time.

        @param name: the name of the variable you want the value of
        @param display_type: an optional value for the type of the desired output, one of: value, tag, ind1, ind2, code, fulltag;
               These can be easily added in the proper place of the code (display_value)
        '''
        context = Context(self.current_node, processorNss=self.namespaces)
        results_list = Evaluate(name, context=context)
        if len(results_list) == 0:
            return ''
        # Select text node value of selected nodes
        # and concatenate
        return ' '.join([node.childNodes[0].nodeValue.encode( "utf-8" )
                for node in results_list])

    def iterator(self, name):
        '''
        An iterator over the values of a certain name.
        The iterator changes state of interenal variables and objects.
        When calling get_value in a loop, this will result each time in a different value.
        '''
        saved_node = self.current_node
        context = Context(self.current_node, processorNss=self.namespaces)
        results_list = Evaluate(name, context=context)
        for node in results_list:
            self.current_node = node
            yield node
        self.current_node = saved_node

    def call_function(self, function_name, parameters=None):
        '''
        Call an external element which is a Python file, using BibFormat
        @param function_name: the name of the function to call
        @param parameters: a dictionary of the parameters to pass as key=value pairs
        @return: a string value, which is the result of the function call
        '''
        #No support for this in bibconvert_bfx_engine
        ## if parameters is None:
##             parameters = {}
##         bfo = BibFormatObject(self.recID)
##         format_element = get_format_element(function_name)
##         (value, errors) = eval_format_element(format_element, bfo, parameters)
##         #to do: check errors from function call
##        return value
        return ""

    def set_xml_source(self, xmltext):
        """
        Specify the source XML for this transformer

        @param xmltext: the XML text representation to use as source
        """
        self.xml_source = xmltext
        self.dom = minidom.parseString(xmltext)
        self.current_node = self.dom
        self.namespaces = build_namespaces(self.dom)

def doc_order_iter_filter(node, filter_func):
    """
    Iterates over each node in document order,
    applying the filter function to each in turn,
    starting with the given node, and yielding each node in
    cases where the filter function computes true
    @param node: the starting point (subtree rooted at node will be iterated over document order)
    @param filter_func: a callable object taking a node and returning true or false
    """
    if filter_func(node):
        yield node
    for child in node.childNodes:
        for cn in doc_order_iter_filter(child, filter_func):
            yield cn
    return


def get_all_elements(node):
    """
    Returns an iterator (using document order) over all element nodes
    that are descendants of the given one
    """
    return doc_order_iter_filter(
        node, lambda n: n.nodeType == Node.ELEMENT_NODE
        )

def build_namespaces(dom):
    """
    Build the namespaces present in dom tree.

    Necessary to use prior processing an XML file
    in order to execute XPath queries correctly.

    @param dom: the dom tree to parse to discover namespaces
    @return: a dictionary with prefix as key and namespace as value
    """
    namespaces = {}
    for elem in get_all_elements(dom):
        if elem.prefix is not None:
            namespaces[elem.prefix] = elem.namespaceURI

        for attr in elem.attributes.values():
            if attr.prefix is not None:
                namespaces[attr.prefix] = attr.namespaceURI
    return namespaces

def bc_profile():
    """
    Runs a benchmark
    """
    global xmltext

    convert(xmltext, 'oaidc2marcxml.bfx')
    return

def benchmark():
    """
    Benchmark the module, using profile and pstats
    """
    import profile
    import pstats
    from invenio.modules.formatter import record_get_xml

    global xmltext

    xmltext = record_get_xml(10, 'oai_dc')
    profile.run('bc_profile()', "bibconvert_xslt_profile")
    p = pstats.Stats("bibconvert_xslt_profile")
    p.strip_dirs().sort_stats("cumulative").print_stats()

if __name__ == "__main__":
    # FIXME: Implement command line options
    pass
