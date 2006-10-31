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
Format records using specified format.

API functions: format_record, format_records, create_excel, get_output_format_content_type

Used to wrap the BibFormat engine and associated functions. This is also where
special formatting of multiple records (that the engine does not handle, as it works
on a single record basis) should be put, with name create_*.

SEE: bibformat_utils.py

FIXME: currently copies record_exists() code from search engine.  Refactor later.
"""

__revision__ = "$Id$"

import zlib

from invenio import bibformat_dblayer
from invenio import bibformat_engine
from invenio import bibformat_utils
from invenio.config import cdslang, weburl, CFG_PATH_PHP
from invenio.bibformat_config import CFG_BIBFORMAT_USE_OLD_BIBFORMAT
try:
    import invenio.template
    websearch_templates = invenio.template.load('websearch')
except:
    pass

# Functions to format a single record 
##

def format_record(recID, of, ln=cdslang, verbose=0, search_pattern=[], xml_record=None, uid=None, on_the_fly=False):
    """
    Formats a record given output format.
    
    Returns a formatted version of the record in
    the specified language, search pattern, and with the specified output format.
    The function will define which format template must be applied.

    The record to be formatted can be specified with its ID (with 'recID' parameter) or given
    as XML representation(with 'xml_record' parameter). If both are specified 'recID' is ignored.

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
    @param search_pattern list of strings representing the user request in web interface
    @param xml_record an xml string represention of the record to format
    @param uid the user id of the person who will view the formatted page (if applicable)
    @param on_the_fly if False, try to return an already preformatted version of the record in the database
    @return formatted record
    """
    ############### FIXME: REMOVE WHEN MIGRATION IS DONE ###############
    if CFG_BIBFORMAT_USE_OLD_BIBFORMAT and CFG_PATH_PHP:
        return bibformat_engine.call_old_bibformat(recID, format=of, on_the_fly=on_the_fly)
    ############################# END ##################################

    if on_the_fly == False:
	# Try to fetch preformatted record
        out = bibformat_dblayer.get_preformatted_record(recID, of)
        if out != None:
            # record 'recID' is formatted in 'of', so return it
            return out

    # Live formatting of records in all other cases
    try:
        out = bibformat_engine.format_record(recID=recID,
					     of=of,
					     ln=ln,
					     verbose=verbose,
					     search_pattern=search_pattern,
					     xml_record=xml_record,
					     uid=uid)
        return out
    except:
        #Failsafe execution mode
        if of == 'hd':
            return websearch_templates.tmpl_print_record_detailed(
                ln = ln,
                recID = recID,
                weburl = weburl,
                )
        
        return websearch_templates.tmpl_print_record_brief(ln = ln,
                                                           recID = recID,
                                                           weburl = weburl,
                                                           )
        

def record_get_xml(recID, format='xm', decompress=zlib.decompress):
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
    return bibformat_utils.record_get_xml(recID=recID, format=format, decompress=decompress)

# Helper functions to do complex formatting of multiple records
#
# You should not modify format_records when adding a complex
# formatting of multiple records, but add a create_* method
# that relies on format_records to do the formatting.
##

def format_records(recIDs, of, ln=cdslang, verbose=0, search_pattern=None, xml_records=None, uid=None,
                   record_prefix=None, record_separator=None, record_suffix=None,
                   prologue="", epilogue="", req=None, on_the_fly=False):
    """
    Returns a list of formatted records given by a list of record IDs or a list of records as xml.
    Adds a prefix before each record, a suffix after each record, plus a separator between records.

    Also add optional prologue and epilogue to the complete formatted list.
    
    You can either specify a list of record IDs to format, or a list of xml records,
    but not both (if both are specified recIDs is ignored).
    
    'record_separator' is a function that returns a string as separator between records.
    The function must take an integer as unique parameter, which is the index
    in recIDs (or xml_records) of the record that has just been formatted. For example
    separator(i) must return the separator between recID[i] and recID[i+1].
    Alternatively separator can be a single string, which will be used to separate
    all formatted records.
    The same applies to 'record_prefix' and 'record_suffix'.

    'req' is an optional parameter on which the result of the function
    are printed lively (prints records after records) if it is given.
    Note that you should set 'req' content-type by yourself, and send http header before calling
    this function as it will not do it. 
    
    This function takes the same parameters as 'format_record' except for:
    @param recIDs a list of record IDs
    @param xml_records a list of xml string representions of the records to format
    @param header a string printed before all formatted records
    @param separator either a string or a function that returns string to separate formatted records
    @param req an optional request object where to print records
    @param on_the_fly if False, try to return an already preformatted version of the record in the database
    """
    if req != None:
        req.write(prologue)
    
    formatted_records = ''

    #Fill one of the lists with Nones
    if xml_records != None:
        recIDs = map(lambda x:None, xml_records)
    else:
        xml_records = map(lambda x:None, recIDs)
    
    total_rec = len(recIDs)
    last_iteration = False
    for i in range(total_rec):
        if i == total_rec - 1:
            last_iteration = True
       
        #Print prefix
        if record_prefix != None:
            if isinstance(record_prefix, str):
                formatted_records += record_prefix
                if req != None:
                    req.write(record_prefix)
            else:
                string_prefix = record_prefix(i)
                formatted_records += string_prefix
                if req != None:
                    req.write(string_prefix)

        #Print formatted record
        formatted_record = format_record(recIDs[i], of, ln, verbose, search_pattern, xml_records[i], uid, on_the_fly)
        formatted_records += formatted_record
        if req != None:
            req.write(formatted_record)
            
        #Print suffix
        if record_suffix != None:
            if isinstance(record_suffix, str):
                formatted_records += record_suffix
                if req != None:
                    req.write(record_suffix)
            else:
                string_suffix = record_suffix(i)
                formatted_records += string_suffix
                if req != None:
                    req.write(string_suffix)
                
        #Print separator if needed
        if record_separator != None and not last_iteration:
            if isinstance(record_separator, str):
                formatted_records += record_separator
                if req != None:
                    req.write(record_separator)
            else:
                string_separator = record_separator(i)
                formatted_records += string_separator
                if req != None:
                    req.write(string_separator)

    if req != None:
        req.write(epilogue)
  
    return prologue + formatted_records + epilogue

def create_excel(recIDs, req=None, ln=cdslang):
    """
    Returns an Excel readable format containing the given recIDs.
    If 'req' is given, also prints the output in 'req' while individual
    records are being formatted.

    This method shows how to create a custom formatting of multiple
    records.
    The excel format is a basic HTML table that most spreadsheets
    applications can parse.

    @param recIDs a list of record IDs
    @return a string in Excel format
    """
    # Prepare the column headers to display in the Excel file
    column_headers_list = ['Title',
                           'Authors',
                           'Addresses',
                           'Affiliation',
                           'Date',
                           'Publisher',
                           'Place',
                           'Abstract',
                           'Keywords',
                           'Notes']

    # Prepare Content
    column_headers = '</b></td><td style="border-color:black; border-style:solid; border-width:thin; background-color:black;color:white"><b>'.join(column_headers_list) + ''
    column_headers = '<table style="border-collapse: collapse;">\n'+ '<td style="border-color:black; border-style:solid; border-width:thin; background-color:black;color:white"><b>' + column_headers + '</b></td>'
    footer = '</table>'

    #Apply content_type and print column headers
    if req != None:
        req.content_type = get_output_format_content_type('excel')
        req.headers_out["Content-Disposition"] = "inline; filename=%s" % 'results.xls'
        req.send_http_header()

    #Format the records
    excel_formatted_records = format_records(recIDs, 'excel', ln=cdslang,
                                             record_separator='\n',
                                             prologue = column_headers,
                                             epilogue = footer,
                                             req=req)
    
    return excel_formatted_records

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
