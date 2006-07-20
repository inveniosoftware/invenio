# -*- coding: utf-8 -*-
## $Id$
## Bibformat. Format records using specified format.

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import zlib
from invenio import bibformat_dblayer
from invenio import bibformat_engine
from invenio.config import cdslang

# Functions to format a single record 
##

def format_record(recID, of, ln=cdslang, verbose=0, search_pattern=None, xml_record=None, uid=None):
    """
    Formats a record given output format.
    
    Returns a formatted version of the record in
    the specified language, search pattern, and with the specified output format.
    The function will define which format template must be applied.

    The record to be formatted can be specified with its ID (with 'recID' parameter) or given
    as XML representation(with 'xml_record' parameter). 

    'uid' allows to grant access to some functionalities on a page depending
    on the user's priviledges. Typically use webuser.getUid(req). This uid has sense
    only in the case of on-the-fly formatting.
    
    @param recID the ID of record to format
    @param of an output format code (or short identifier for the output format)
    @param ln the language to use to format the record
    @param verbose the level of verbosity from 0 to 9 (O: silent,
                                                       5: errors,
                                                       7: errors and warnings, stop if error in format elements
                                                       9: errors and warnings, stop if error (debug mode ))
    @param search_pattern the context in which this record was asked to be formatted (User request in web interface)
    @param record a record (structure as returned by BibRecord) to format
    @param uid the user id of the person who will view the formatted page (if applicable)
    @return formatted record
    """
    return bibformat_engine.format_record(recID=recID,
                                          of=of,
                                          ln=ln,
                                          verbose=verbose,
                                          search_pattern=search_pattern,
                                          xml_record=xml_record,
                                          uid=uid)


def get_xml(recID, format='xm', decompress=zlib.decompress):
    """
    Returns an XML string of the record given by recID.

    The function builds the XML directly from the database,
    without using the standard formatting process.

    'format' allows to define the flavour of XML:
        - 'xm' for standard XML
        - 'marcxml' for MARC XML 
        - 'oai_dc' for OAI Dublin Core
        - 'xd' for XML Dublin Core

    If record does not exist, returns empty string.

    @param recID the id of the record to retrieve
    @return the xml string of the record
    """

    return bibformat_engine.get_xml(recID=recID, format=format)

# Helper functions to do complex formatting of multiple records
##

def create_Excel(recIDs):
    """
    Returns an Excel readable format containing the given recIDs

    @param recIDs a list of record IDs
    @return a string in Excel format
    """
    return ""

# Utility functions
##

def get_output_format_content_type(of):
    """
    Returns the content type (eg. 'text/html' or 'application/ms-excel') \
    of the given output format.

    @param of the code of output format for which we want to get the content type
    """
    content_type = bibformat_dblayer.get_output_format_content_type(of)

    if content_type == '':
        content_type = 'text/html'

    return content_type

def encode_for_xml(s):
    "Encode special chars in string so that it would be XML-compliant."
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    return s
