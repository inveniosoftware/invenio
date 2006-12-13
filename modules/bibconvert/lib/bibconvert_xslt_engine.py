# -*- coding: utf-8 -*-
##
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

"""
bibconvert_xslt_engine - Wrapper for an XSLT engine.

Customized to support BibConvert functions through the
use of XPath 'format' function.

Dependencies: Need one of the following XSLT processors:
              - libxml2 & libxslt
              - 4suite

Used by: bibconvert.in

FIXME: - find better namespace for functions
       - find less bogus URI (given as param to processor)
         for source and template
       - Implement command-line options
"""

__revision__ = "$Id$"

import sys
import os

from invenio.config import \
     etcdir, \
     weburl
from invenio.bibconvert import FormatField

# The namespace used for BibConvert functions
CFG_BIBCONVERT_FUNCTION_NS = "http://cdsweb.cern.ch/bibconvert/fn"

# Import one XSLT processor
#
# processor_type:
#       -1 : No processor found
#        0 : libxslt
#        1 : 4suite
processor_type = -1
try:
    # libxml2 & libxslt
    processor_type = 0
    import libxml2
    import libxslt
except ImportError:
    pass

if processor_type == -1:
    try:
        # 4suite
        processor_type = 1
        from Ft.Xml.Xslt import Processor
        from Ft.Xml import InputSource
    except ImportError:
        pass

if processor_type == -1:
    # No XSLT processor found
    sys.stderr.write('No XSLT processor could be found.\n' \
                     'No output produced.\n')
    sys.exit(1)

CFG_BIBCONVERT_XSL_PATH = "%s%sbibconvert%sconfig" % (etcdir, os.sep, os.sep)

def bibconvert_function(ctx, value, func):
    """
    libxslt extension function:
    Bridge between BibConvert formatting functions and XSL stylesheets.

    Can be used in that way in XSL stylesheet
    (provided xmlns:fn="http://cdsweb.cern.ch/bibconvert/fn" has been declared):
    <xsl:value-of select="fn:format(string(.), 'ADD(mypref,mysuff)')"/>
    (Adds strings 'mypref' and 'mysuff' as prefix/suffix to current node value,
    using BibConvert ADD function)
    """
    return FormatField(value, func)

def convert(xmltext, template_filename=None, template_source=None):
    """
    Processes an XML text according to a template, and returns the result.

    The template can be given either by name (or by path) or by source.
    If source is given, name is ignored.

    bibconvert_xslt_engine will look for template_filename in standard directories
    for templates. If not found, template_filename will be assumed to be a path to
    a template. If none can be found, return None.

    @param xmltext The string representation of the XML to process
    @param template_filename The name of the template to use for the processing
    @param template_source The configuration describing the processing.
    @return the transformed XML text.
    """
    
    if processor_type == -1:
        # No XSLT processor found
        sys.stderr.write('No XSLT processor could be found.')
        sys.exit(1)

    # Retrieve template and read it
    if template_source:
        template = template_source
    elif template_filename:
        try:
            path_to_templates = (CFG_BIBCONVERT_XSL_PATH + os.sep +
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

    result = ""
    if processor_type == 0:
        # libxml2 & libxslt
        
        # Register BibConvert functions for use in XSL
        libxslt.registerExtModuleFunction("format",
                                          CFG_BIBCONVERT_FUNCTION_NS,
                                          bibconvert_function)

        # Load template and source
        template_xml = libxml2.parseDoc(template)
        processor = libxslt.parseStylesheetDoc(template_xml)
        source = libxml2.parseDoc(xmltext)

        # Transform
        result_object = processor.applyStylesheet(source, None)
        result = processor.saveResultToString(result_object)

        # Deallocate
        processor.freeStylesheet()
        source.freeDoc()
        result_object.freeDoc()

    elif processor_type == 1:
        # 4suite

        # Init
        processor = Processor.Processor()
        
        # Register BibConvert functions for use in XSL
        processor.registerExtensionFunction(CFG_BIBCONVERT_FUNCTION_NS,
                                            "format",
                                            bibconvert_function)

        # Load template and source
        transform = InputSource.DefaultFactory.fromString(template,
                                                       uri=weburl)
        source = InputSource.DefaultFactory.fromString(xmltext,
                                                       uri=weburl)
        processor.appendStylesheet(transform)

        # Transform
        result = processor.run(source)
    else:
        sys.stderr.write("No XSLT processor could be found")
        
    return result

## def bc_profile():
##     """
##     Runs a benchmark
##     """
##     global xmltext

##     convert(xmltext, 'oaidc2marcxml.xsl')
##     return

## def benchmark():
##     """
##     Benchmark the module, using profile and pstats
##     """
##     import profile
##     import pstats
##     from invenio.bibformat import record_get_xml

##     global xmltext
    
##     xmltext = record_get_xml(10, 'oai_dc')
##     profile.run('bc_profile()', "bibconvert_xslt_profile")
##     p = pstats.Stats("bibconvert_xslt_profile")
##     p.strip_dirs().sort_stats("cumulative").print_stats()
    
if __name__ == "__main__":
    pass

