# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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
bibformat_xslt_engine - Wrapper for an XSLT engine.

Some functions are registered in order to be used in XSL code:
  - creation_date(recID)
  - modification_date(recID)

Dependencies: Need one of the following XSLT processors:
              - libxml2 & libxslt
              - 4suite

Used by: bibformat_engine.py
"""

__revision__ = "$Id$"

import sys
import os

from invenio.config import \
     CFG_SITE_URL
from invenio.bibformat_config import \
     CFG_BIBFORMAT_TEMPLATES_PATH
from invenio.bibformat_dblayer import \
     get_creation_date, \
     get_modification_date

# The namespace used for BibFormat function
CFG_BIBFORMAT_FUNCTION_NS = "http://cdsweb.cern.ch/bibformat/fn"

# Import one XSLT processor
#
# processor_type:
#       -1 : No processor found
#        0 : libxslt
#        1 : 4suite
processor_type = -1
try:
    # libxml2 & libxslt
    import libxml2
    import libxslt
    processor_type = 0
except ImportError:
    pass

if processor_type == -1:
    try:
        # 4suite
        from Ft.Xml.Xslt import Processor
        from Ft.Xml import InputSource
        from xml.dom import Node
        processor_type = 1
    except ImportError:
        pass

if processor_type == -1:
    # No XSLT processor found
    sys.stderr.write('No XSLT processor could be found.\n' \
                     'No output produced.\n')
    #sys.exit(1)

##################################################################
# Support for 'creation_date' and 'modification_date' functions  #

def get_creation_date_libxslt(ctx, recID, fmt="%Y-%m-%dT%H:%M:%SZ"):
    """
    libxslt extension function:
    Bridge between BibFormat and XSL stylesheets.
    Returns record creation date.

    Can be used in that way in XSL stylesheet
    (provided xmlns:fn="http://cdsweb.cern.ch/bibformat/fn" has been declared):
    <xsl:value-of select="fn:creation_date(445)"/> where 445 is a recID

    if recID is string, value is converted to int
    if recID is Node, first child node (text node) is taken as value

    @param ctx: context as passed by libxslt
    @param recID: record ID
    @param fmt: format of the returned date
    @return: creation date of X{recID}
    @rtype: string
    """
    try:
        if isinstance(recID, str):
            recID_int = int(recID)
        elif isinstance(recID, (int, long)):
            recID_int = recID
        else:
            recID_int = libxml2.xmlNode(_obj=recID[0]).children.content

        if isinstance(fmt, str):
            fmt_str = fmt
        else:
            fmt_str = libxml2.xmlNode(_obj=recID[0]).children.content

        return get_creation_date(recID_int, fmt_str)
    except Exception, err:
        sys.stderr.write("Error during formatting function evaluation: " + \
                         str(err) + \
                         '\n')

        return ''

def get_creation_date_4suite(ctx, recID, fmt="%Y-%m-%dT%H:%M:%SZ"):
    """
    4suite extension function:
    Bridge between BibFormat and XSL stylesheets.
    Returns record creation date.

    Can be used in that way in XSL stylesheet
    (provided xmlns:fn="http://cdsweb.cern.ch/bibformat/fn" has been declared):
    <xsl:value-of select="fn:creation_date(445)"/>

    if value is int, value is converted to string
    if value is Node, first child node (text node) is taken as value

    @param ctx: context as passed by 4suite
    @param recID: record ID
    @param fmt: format of the returned date
    @return: creation date of X{recID}
    @rtype: string
    """
    try:
        if len(recID) > 0 and isinstance(recID[0], Node):
            recID_int = recID[0].firstChild.nodeValue
            if recID_int is None:
                return ''
        else:
            recID_int = int(recID)

        if len(fmt) > 0 and isinstance(fmt[0], Node):
            fmt_str = fmt[0].firstChild.nodeValue
            if fmt_str is None:
                fmt_str = "%Y-%m-%dT%H:%M:%SZ"
        else:
            fmt_str = str(fmt)

        return get_creation_date(recID_int, fmt_str)
    except Exception, err:
        sys.stderr.write("Error during formatting function evaluation: " + \
                         str(err) + \
                         '\n')

        return ''

def get_modification_date_libxslt(ctx, recID, fmt="%Y-%m-%dT%H:%M:%SZ"):
    """
    libxslt extension function:
    Bridge between BibFormat and XSL stylesheets.
    Returns record modification date.

    Can be used in that way in XSL stylesheet
    (provided xmlns:fn="http://cdsweb.cern.ch/bibformat/fn" has been declared):
    <xsl:value-of select="fn:creation_date(445)"/> where 445 is a recID

    if recID is string, value is converted to int
    if recID is Node, first child node (text node) is taken as value

    @param ctx: context as passed by libxslt
    @param recID: record ID
    @param fmt: format of the returned date
    @return: modification date of X{recID}
    @rtype: string
    """
    try:
        if isinstance(recID, str):
            recID_int = int(recID)
        elif isinstance(recID, (int, long)):
            recID_int = recID
        else:
            recID_int = libxml2.xmlNode(_obj=recID[0]).children.content

        if isinstance(fmt, str):
            fmt_str = fmt
        else:
            fmt_str = libxml2.xmlNode(_obj=recID[0]).children.content

        return get_modification_date(recID_int, fmt_str)
    except Exception, err:
        sys.stderr.write("Error during formatting function evaluation: " + \
                         str(err) + \
                         '\n')

        return ''

def get_modification_date_4suite(ctx, recID, fmt="%Y-%m-%dT%H:%M:%SZ"):
    """
    4suite extension function:
    Bridge between BibFormat and XSL stylesheets.
    Returns record modification date.

    Can be used in that way in XSL stylesheet
    (provided xmlns:fn="http://cdsweb.cern.ch/bibformat/fn" has been declared):
    <xsl:value-of select="fn:modification_date(445)"/>

    if value is int, value is converted to string
    if value is Node, first child node (text node) is taken as value

    @param ctx: context as passed by 4suite
    @param recID: record ID
    @param fmt: format of the returned date
    @return: modification date of X{recID}
    @rtype: string
    """
    try:
        if len(recID) > 0 and isinstance(recID[0], Node):
            recID_int = recID[0].firstChild.nodeValue
            if recID_int is None:
                return ''
        else:
            recID_int = int(recID_int)

        if len(fmt) > 0 and isinstance(fmt[0], Node):
            fmt_str = fmt[0].firstChild.nodeValue
            if fmt_str is None:
                fmt_str = "%Y-%m-%dT%H:%M:%SZ"
        else:
            fmt_str = str(fmt)

        return get_modification_date(recID_int, fmt_str)
    except Exception, err:
        sys.stderr.write("Error during formatting function evaluation: " + \
                         str(err) + \
                         '\n')

        return ''

def eval_bibformat_libxslt(ctx, recID, template_code):
    """
    libxslt extension function:
    Bridge between BibFormat and XSL stylesheets.
    Returns the evaluation of the given piece of format template

    Can be used in that way in XSL stylesheet
    (provided xmlns:fn="http://cdsweb.cern.ch/bibformat/fn" has been declared):
    <xsl:value-of select="fn:eval_bibformat(marc:controlfield[@tag='001'],'&lt;BFE_SERVER_INFO var=&quot;recurl&quot;>')" />

    if recID is string, value is converted to int
    if recID is Node, first child node (text node) is taken as value
    template_code is evaluated as a format template piece of code. '<'
    and '"' need to be escaped with '&lt;' and '&quot;'

    @param ctx: context as passed by libxslt
    @param recID: record ID
    @param template_code: the code calling a BFE_ as it would be use in format template
    @return: the evalued call to a format template (usually a call to a format element)
    @rtype: string
    """ #'
    from invenio.bibformat_engine import \
    format_with_format_template, \
    BibFormatObject
    try:
        if isinstance(recID, str):
            recID_int = int(recID)
        elif isinstance(recID, (int, long)):
            recID_int = recID
        else:
            recID_int = libxml2.xmlNode(_obj=recID[0]).children.content

        bfo = BibFormatObject(recID_int)
        return format_with_format_template(None, bfo,
                                           verbose=0,
                                           format_template_code=template_code)
    except Exception, err:
        sys.stderr.write("Error during formatting function evaluation: " + \
                         str(err) + \
                         '\n')

        return ''


def eval_bibformat_4suite(ctx, recID, template_code):
    """
    4suite extension function:
    Bridge between BibFormat and XSL stylesheets.
    Returns the evaluation of the given piece of format template

    Can be used in that way in XSL stylesheet
    (provided xmlns:fn="http://cdsweb.cern.ch/bibformat/fn" has been declared):
    <xsl:value-of select="fn:eval_bibformat(marc:controlfield[@tag='001'],'&lt;BFE_SERVER_INFO var=&quot;recurl&quot;>')" />

    if recID is string, value is converted to int
    if recID is Node, first child node (text node) is taken as value
    template_code is evaluated as a format template piece of code. '<'
    and '"' need to be escaped with '&lt;' and '&quot;'

    @param ctx: context as passed by 4suite
    @param recID: record ID
    @param template_code: the code calling a BFE_ as it would be use in format template
    @return: the evalued call to a format template (usually a call to a format element)
    @rtype: string
    """ #'
    from invenio.bibformat_engine import \
    format_with_format_template, \
    BibFormatObject
    try:
        if len(recID) > 0 and isinstance(recID[0], Node):
            recID_int = recID[0].firstChild.nodeValue
            if recID_int is None:
                return ''
        else:
            recID_int = int(recID_int)

        bfo = BibFormatObject(recID_int)
        return format_with_format_template(None, bfo,
                                           verbose=0,
                                           format_template_code=template_code)
    except Exception, err:
        sys.stderr.write("Error during formatting function evaluation: " + \
                         str(err) + \
                         '\n')

        return ''

# End of date-related functions                                  #
##################################################################

def format(xmltext, template_filename=None, template_source=None):
    """
    Processes an XML text according to a template, and returns the result.

    The template can be given either by name (or by path) or by source.
    If source is given, name is ignored.

    bibformat_xslt_engine will look for template_filename in standard directories
    for templates. If not found, template_filename will be assumed to be a path to
    a template. If none can be found, return None.

    @param xmltext: The string representation of the XML to process
    @param template_filename: The name of the template to use for the processing
    @param template_source: The configuration describing the processing.
    @return: the transformed XML text.
    """
    if processor_type == -1:
        # No XSLT processor found
        sys.stderr.write('No XSLT processor could be found.')
        #sys.exit(1)

    # Retrieve template and read it
    if template_source:
        template = template_source
    elif template_filename:
        try:
            path_to_templates = (CFG_BIBFORMAT_TEMPLATES_PATH + os.sep +
                                 template_filename)
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

    # Some massaging of the input to avoid the default namespace issue
    # in XPath. More elegant solution might be found though.
    xmltext = xmltext.replace('xmlns="http://www.loc.gov/MARC21/slim"', '')

    # For older MARCXML records stored in bibfmt with empty indicators
    xmltext = xmltext.replace('ind1=""', 'ind1=" "')
    xmltext = xmltext.replace('ind2=""', 'ind2=" "')

    result = ""
    if processor_type == 0:
        # libxml2 & libxslt

        # Register BibFormat functions for use in XSL
        libxslt.registerExtModuleFunction("creation_date",
                                          CFG_BIBFORMAT_FUNCTION_NS,
                                          get_creation_date_libxslt)
        libxslt.registerExtModuleFunction("modification_date",
                                          CFG_BIBFORMAT_FUNCTION_NS,
                                          get_modification_date_libxslt)
        libxslt.registerExtModuleFunction("eval_bibformat",
                                          CFG_BIBFORMAT_FUNCTION_NS,
                                          eval_bibformat_libxslt)
        # Load template and source
        template_xml = libxml2.parseDoc(template)
        processor = libxslt.parseStylesheetDoc(template_xml)
        source = libxml2.parseDoc(xmltext)

        # Transform
        result_object = processor.applyStylesheet(source, None)
        try:
            result = processor.saveResultToString(result_object)
        except SystemError :
            # Catch an exception thrown when result is empty,
            # due to a bug in libxslt
            result = ''

        # Deallocate
        processor.freeStylesheet()
        source.freeDoc()
        result_object.freeDoc()

    elif processor_type == 1:
        # 4suite

        # Init
        processor = Processor.Processor()

        # Register BibFormat functions for use in XSL
        processor.registerExtensionFunction(CFG_BIBFORMAT_FUNCTION_NS,
                                            "creation_date",
                                            get_creation_date_4suite)
        processor.registerExtensionFunction(CFG_BIBFORMAT_FUNCTION_NS,
                                            "modification_date",
                                            get_modification_date_4suite)
        processor.registerExtensionFunction(CFG_BIBFORMAT_FUNCTION_NS,
                                            "eval_bibformat",
                                            eval_bibformat_4suite)
        # Load template and source
        transform = InputSource.DefaultFactory.fromString(template,
                                                       uri=CFG_SITE_URL)
        source = InputSource.DefaultFactory.fromString(xmltext,
                                                       uri=CFG_SITE_URL)
        processor.appendStylesheet(transform)

        # Transform
        result = processor.run(source)
    else:
        sys.stderr.write("No XSLT processor could be found")

    return result

if __name__ == "__main__":
    pass

