# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2014, 2015 CERN.
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

"""
bibconvert_xslt_engine - Wrapper for an XSLT engine.

Customized to support BibConvert functions through the
use of XPath 'format' function.

Used by: bibconvert.in

FIXME: - Find better namespace for functions
       - Find less bogus URI (given as param to processor)
         for source and template
       - Implement command-line options
       - Think about better handling of 'value' parameter
         in bibconvert_function_*
"""

from __future__ import print_function

import os
import sys
from StringIO import StringIO

from lxml import etree
from invenio.utils.text import encode_for_xml

from .api import FormatField
from .registry import templates

CFG_BIBCONVERT_FUNCTION_NS = "http://cdsweb.cern.ch/bibconvert/fn"
"""The namespace used for BibConvert functions"""


class FileResolver(etree.Resolver):

    """Local file resolver."""

    def resolve(self, url, pubid, context):
        """Resolve local name."""
        return self.resolve_filename(url, context)


def _bibconvert_function(dummy_ctx, value, func):
    """
    Bridge between BibConvert formatting functions and XSL stylesheets.

    Can be used in that way in XSL stylesheet (provided
    ``xmlns:fn="http://cdsweb.cern.ch/bibconvert/fn"`` has been declared):
    ``<xsl:value-of select="fn:format(., 'ADD(mypref,mysuff)')"/>``
    (Adds strings ``mypref`` and ``mysuff`` as prefix/suffix to current node
    value, using BibConvert ADD function)

    if value is int, value is converted to string
    if value is Node (PyCObj), first child node (text node) is taken as value

    """
    try:
        if isinstance(value, str):
            string_value = value
        elif isinstance(value, (int, long)):
            string_value = str(value)
        elif isinstance(value, list):
            value = value[0]
            if isinstance(value, str):
                string_value = value
            elif isinstance(value, (int, long)):
                string_value = str(value)
            else:
                string_value = value.text
        else:
            string_value = value.text

        return FormatField(string_value, func).rstrip('\n')

    except Exception as err:
        print("Error during formatting function evaluation: {0}".format(err),
              file=sys.stderr)

    return ''


def _bibconvert_escape(dummy_ctx, value):
    """Bridge to lxml to escape the provided value."""
    try:
        if isinstance(value, str):
            string_value = value
        elif isinstance(value, (int, long)):
            string_value = str(value)
        elif isinstance(value, list):
            value = value[0]
            if isinstance(value, str):
                string_value = value
            elif isinstance(value, (int, long)):
                string_value = str(value)
            else:
                string_value = value.text
        else:
            string_value = value.text

        return encode_for_xml(string_value)

    except Exception as err:
        print("Error during formatting function evaluation: {0}".format(err),
              file=sys.stderr)

    return ''


def convert(xmltext, template_filename=None, template_source=None):
    """
    Process an XML text according to a template, and returns the result.

    The template can be given either by name (or by path) or by source.
    If source is given, name is ignored.

    bibconvert_xslt_engine will look for template_filename in standard
    directories for templates. If not found, template_filename will be assumed
    to be a path to a template. If none can be found, return None.

    :param xmltext: The string representation of the XML to process
    :param template_filename: The name of the template to use for the processing
    :param template_source: The configuration describing the processing.
    :return: the transformed XML text, or None if an error occured

    """
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
                raise Exception(template_filename + ' does not exist.')
        except IOError:
            raise Exception(template_filename + ' could not be read.')
    else:
        raise Exception(template_filename + ' was not given.')

    result = ""

    parser = etree.XMLParser()
    parser.resolvers.add(FileResolver())
    try:
        try:
            if (-1 < xmltext.index('?') < 3):
                xmltext = xmltext[xmltext.index('>') + 1:]
        except ValueError:
            # if index doesn't find the '?' then it raises a useless exception
            pass

        xml = etree.parse(StringIO(xmltext), parser)
    except etree.XMLSyntaxError as e:
        error = 'The XML code given is invalid. [%s]' % e
        raise Exception(error)
    except Exception as e:
        error = 'Failed to process the XML code.' + str(e)
        raise Exception(error)

    try:
        xsl = etree.parse(StringIO(template), parser)
    except etree.XMLSyntaxError as e:
        error = 'The XSL code given is invalid. [%s]' % e
        raise Exception(error)
    except Exception as e:
        error = 'Failed to process the XSL code.' + str(e)
        raise Exception(error)

    try:
        fns = etree.FunctionNamespace(CFG_BIBCONVERT_FUNCTION_NS)
        fns["format"] = _bibconvert_function
        fns["escape"] = _bibconvert_escape
    except etree.NamespaceRegistryError as e:
        error = 'Failed registering the XPath extension function. [%s]' % e
        raise Exception(error)

    try:
        xslt = etree.XSLT(xsl)
    except etree.XSLTParseError as e:
        error = 'The XSL code given is invalid. [%s]' % e
        raise Exception(error)

    temporary_result = xslt(xml)
    result = str(temporary_result)

    # Housekeeping
    del temporary_result
    del xslt
    del xsl
    del xml

    return result
