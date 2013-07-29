# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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
Format records using chosen format.

The main APIs are:
  - format_record
  - format_records
  - create_excel
  - get_output_format_content_type

This module wraps the BibFormat engine and its associated
functions. This is also where special formatting functions of multiple
records (that the engine does not handle, as it works on a single
record basis) should be defined, with name C{def create_*}.

@see: bibformat_utils.py
"""

__revision__ = "$Id$"

import zlib

from invenio import bibformat_dblayer
from invenio import bibformat_engine
from invenio import bibformat_utils
from invenio.config import \
     CFG_SITE_LANG, \
     CFG_SITE_URL, \
     CFG_SITE_RECORD
import getopt
import sys

# Functions to format a single record
##
def format_record(recID, of, ln=CFG_SITE_LANG, verbose=0, search_pattern=None,
                  xml_record=None, user_info=None, on_the_fly=False,
                  save_missing=True, force_2nd_pass=False, ot=''):
    """
    Returns the formatted record with id 'recID' and format 'of'

    If corresponding record does not exist for given output format,
    returns ''

    ln specifies which language is used for translations.

    verbose can be increased to display debug output.

    xml_record can be specified to ignore the recID and use the given xml
    instead.

    on_the_fly means we always generate the format, ignoring the cache.

    save_missing can be used to specify to never cache a format after it has
    been generated. By default, we have a list of cached formats and the result
    of these formats is saved in the database.

    force_2nd_pass forces the 2nd pass which is basically a second formatting.
    This is used in case a bibformat element generates new BibFormat tags
    and thus we do not detect them automatically.
    (the normal way is to use nocache="1" in a template to have it treated
     in the 2nd pass instead)

    @param recID: the id of the record to fetch
    @param of: the output format code
    @param ot: output only these MARC tags (e.g. ['100', '999']), only supported for 'xmf' format
    @type ot: list
    @return: formatted record as String, or '' if it does not exist
    """
    out, needs_2nd_pass = bibformat_engine.format_record_1st_pass(
                                        recID=recID,
                                        of=of,
                                        ln=ln,
                                        verbose=verbose,
                                        search_pattern=search_pattern,
                                        xml_record=xml_record,
                                        user_info=user_info,
                                        on_the_fly=on_the_fly,
                                        save_missing=save_missing,
                                        ot=ot)
    if needs_2nd_pass or force_2nd_pass:
        out = bibformat_engine.format_record_2nd_pass(
                                    recID=recID,
                                    of=of,
                                    template=out,
                                    ln=ln,
                                    verbose=verbose,
                                    search_pattern=search_pattern,
                                    xml_record=xml_record,
                                    user_info=user_info,
                                    ot=ot)

    return out


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

    @param recID: the id of the record to retrieve
    @param format: the format to use
    @param decompress: the library to use to decompress cache from DB
    @return: the xml string of the record
    """
    return bibformat_utils.record_get_xml(recID=recID, format=format, decompress=decompress)

# Helper functions to do complex formatting of multiple records
#
# You should not modify format_records when adding a complex
# formatting of multiple records, but add a create_* method
# that relies on format_records to do the formatting.
##

def format_records(recIDs, of, ln=CFG_SITE_LANG, verbose=0, search_pattern=None,
                   xml_records=None, user_info=None, record_prefix=None,
                   record_separator=None, record_suffix=None, prologue="",
                   epilogue="", req=None, on_the_fly=False, ot=''):
    """
    Format records given by a list of record IDs or a list of records
    as xml.  Adds a prefix before each record, a suffix after each
    record, plus a separator between records.

    Also add optional prologue and epilogue to the complete formatted
    list.

    You can either specify a list of record IDs to format, or a list
    of xml records, but not both (if both are specified recIDs is
    ignored).

    'record_separator' is a function that returns a string as
    separator between records.  The function must take an integer as
    unique parameter, which is the index in recIDs (or xml_records) of
    the record that has just been formatted. For example separator(i)
    must return the separator between recID[i] and recID[i+1].
    Alternatively separator can be a single string, which will be used
    to separate all formatted records.  The same applies to
    'record_prefix' and 'record_suffix'.

    'req' is an optional parameter on which the result of the function
    are printed lively (prints records after records) if it is given.
    Note that you should set 'req' content-type by yourself, and send
    http header before calling this function as it will not do it.

    This function takes the same parameters as 'format_record' except for:
    @param recIDs: a list of record IDs
    @type recIDs: list(int)
    @param of: an output format code (or short identifier for the output format)
    @type of: string
    @param ln: the language to use to format the record
    @type ln: string
    @param verbose: the level of verbosity from 0 to 9 (0: silent,
                                                        5: errors,
                                                        7: errors and warnings, stop if error in format elements
                                                        9: errors and warnings, stop if error (debug mode ))
    @type verbose: int
    @param search_pattern: list of strings representing the user request in web interface
    @type search_pattern: list(string)
    @param user_info: the information of the user who will view the formatted page (if applicable)
    @param xml_records: a list of xml string representions of the records to format
    @type xml_records: list(string)
    @param record_prefix: a string printed before B{each} formatted records (n times)
    @type record_prefix: string
    @param record_suffix: a string printed after B{each} formatted records (n times)
    @type record_suffix: string
    @param prologue: a string printed at the beginning of the complete formatted records (1x)
    @type prologue: string
    @param epilogue: a string printed at the end of the complete formatted output (1x)
    @type epilogue: string
    @param record_separator: either a string or a function that returns string to join formatted records
    @param record_separator: string or function
    @param req: an optional request object where to print records
    @param on_the_fly: if False, try to return an already preformatted version of the record in the database
    @type on_the_fly: boolean
    @param ot: output only these MARC tags (e.g. "100,700,909C0b"), only supported for 'xmf' format
    @type ot: string
    @rtype: string
    """
    if req is not None:
        req.write(prologue)
    formatted_records = ''

    #Fill one of the lists with Nones
    if xml_records is not None:
        recIDs = [None for dummy in xml_records]
    else:
        xml_records = [None for dummy in recIDs]

    total_rec = len(recIDs)
    last_iteration = False
    for i in range(total_rec):
        if i == total_rec - 1:
            last_iteration = True

        #Print prefix
        if record_prefix is not None:
            if isinstance(record_prefix, str):
                formatted_records += record_prefix
                if req is not None:
                    req.write(record_prefix)
            else:
                string_prefix = record_prefix(i)
                formatted_records += string_prefix
                if req is not None:
                    req.write(string_prefix)

        #Print formatted record
        formatted_record = format_record(recIDs[i], of, ln, verbose,
                                         search_pattern, xml_records[i],
                                         user_info, on_the_fly, ot=ot)
        formatted_records += formatted_record
        if req is not None:
            req.write(formatted_record)

        #Print suffix
        if record_suffix is not None:
            if isinstance(record_suffix, str):
                formatted_records += record_suffix
                if req is not None:
                    req.write(record_suffix)
            else:
                string_suffix = record_suffix(i)
                formatted_records += string_suffix
                if req is not None:
                    req.write(string_suffix)

        #Print separator if needed
        if record_separator is not None and not last_iteration:
            if isinstance(record_separator, str):
                formatted_records += record_separator
                if req is not None:
                    req.write(record_separator)
            else:
                string_separator = record_separator(i)
                formatted_records += string_separator
                if req is not None:
                    req.write(string_separator)

    if req is not None:
        req.write(epilogue)

    return prologue + formatted_records + epilogue


def format_with_format_template(format_template_filename, bfo,
                                verbose=0, format_template_code=None):
    evaluated_format, dummy = bibformat_engine.format_with_format_template(
                            format_template_filename=format_template_filename,
                            bfo=bfo,
                            verbose=verbose,
                            format_template_code=format_template_code)
    return evaluated_format


def create_excel(recIDs, req=None, ot=None, ot_sep="; ", user_info=None):
    """
    Returns an Excel readable format containing the given recIDs.
    If 'req' is given, also prints the output in 'req' while individual
    records are being formatted.

    This method shows how to create a custom formatting of multiple
    records.
    The excel format is a basic HTML table that most spreadsheets
    applications can parse.

    If 'ot' is given, the BibFormat engine is overridden and the
    output is produced on the basis of the fields that 'ot' defines
    (see search_engine.perform_request_search(..) 'ot' param).

    @param req: the request object
    @param recIDs: a list of record IDs
    @param ln: language
    @param ot: a list of fields that should be included in the excel output as columns(see perform_request_search 'ot' param)
    @param ot_sep: a separator used to separate values for the same record, in the same columns, if any
    @param user_info: the user_info dictionary
    @return: a string in Excel format
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

    # Apply content_type and print column headers
    if req is not None:
        req.content_type = get_output_format_content_type('excel')
        req.headers_out["Content-Disposition"] = "inline; filename=%s" % 'results.xls'
        req.send_http_header()

    if ot is not None and len(ot) > 0:
        # Skip BibFormat engine, produce our own output based on
        # specified fields. Each field will be a column of the
        # output. If a field has multiple values, then they are joined
        # into the same cell.
        out = "<table>"
        if req:
            req.write("<table>")
        for recID in recIDs:
            row = '<tr>'
            row += '<td><a href="%(CFG_SITE_URL)s/%(CFG_SITE_RECORD)s/%(recID)i">%(recID)i</a></td>' % \
                   {'recID': recID, 'CFG_SITE_RECORD': CFG_SITE_RECORD, 'CFG_SITE_URL': CFG_SITE_URL}
            for field in ot:
                row += '<td>' + \
                       ot_sep.join(bibformat_utils.get_all_fieldvalues(recID, field)) + \
                       '</td>'
            row += '</tr>'
            out += row
            if req:
                req.write(row)
        out += '</table>'
        if req:
            req.write('</table>')
        return out

    #Format the records
    excel_formatted_records = format_records(recIDs, 'excel', ln=CFG_SITE_LANG,
                                             record_separator='\n',
                                             prologue='<meta http-equiv="Content-Type" content="text/html; charset=utf-8"><table>',
                                             epilogue=footer,
                                             req=req,
                                             user_info=user_info)

    return excel_formatted_records


def get_output_format_content_type(of, default_content_type="text/html"):
    """
    Returns the content type (for example 'text/html' or 'application/ms-excel') \
    of the given output format.

    @param of: the code of output format for which we want to get the content type
    @param default_content_type: default content-type when content-type was not set up
    @return: the content-type to use for this output format
    """
    content_type = bibformat_dblayer.get_output_format_content_type(of)

    if content_type == '':
        content_type = default_content_type

    return content_type

def usage(exitcode=1, msg=""):
    """
    Prints usage info.

    @param exitcode: exit code to use (eg. 1 for error, 0 for okay)
    @param msg: message to print
    @return: exit the process
    """
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)
    print """BibFormat: outputs the result of the formatting of a record.

    Usage: bibformat required [options]
    Examples:
      $ bibformat -i 10 -o HB
      $ bibformat -i 10,11,13 -o HB
      $ bibformat -i 10:13
      $ bibformat -i 10 -o HB -v 9

    Required:
     -i, --id=ID[ID2,ID3:ID5]  ID (or range of IDs) of the record(s) to be formatted.

    Options:
     -o, --output=CODE          short code of the output format used for formatting (default HB).
     -l, --lang=LN              language used for formatting.
     -y, --onthefly             on-the-fly formatting, avoiding caches created by BibReformat.

    General options:
     -h, --help                 print this help and exit
     -v, --verbose=LEVEL        verbose level (from 0 to 9, default 0)
     -V  --version              print the script version
     """
    sys.exit(exitcode)

def main():
    """
    Main entry point for biformat via command line

    @return: formatted record(s) as specified by options, or help/errors
    """

    options = {} # will hold command-line options
    options["verbose"] = 0
    options["onthefly"] = False
    options["lang"] = CFG_SITE_LANG
    options["output"] = "HB"
    options["recID"] = None

    try:
        opts, dummy_args = getopt.getopt(sys.argv[1:],
                                         "hVv:yl:i:o:",
                                         ["help",
                                          "version",
                                          "verbose=",
                                          "onthefly",
                                          "lang=",
                                          "id=",
                                          "output="])
    except getopt.GetoptError, err:
        usage(1, err)

    try:
        for opt in opts:
            if opt[0] in ["-h", "--help"]:
                usage(0)
            elif opt[0] in ["-V", "--version"]:
                print __revision__
                sys.exit(0)
            elif opt[0] in ["-v", "--verbose"]:
                options["verbose"] = int(opt[1])
            elif opt[0] in ["-y", "--onthefly"]:
                options["onthefly"] = True
            elif opt[0] in ["-l", "--lang"]:
                options["lang"] = opt[1]
            elif opt[0] in ["-i", "--id"]:
                recIDs = []
                for recID in opt[1].split(','):
                    if ":" in recID:
                        start = int(recID.split(':')[0])
                        end = int(recID.split(':')[1])
                        recIDs.extend(range(start, end))
                    else:
                        recIDs.append(int(recID))
                options["recID"] = recIDs
            elif opt[0] in ["-o", "--output"]:
                options["output"] = opt[1]

        if options["recID"] is None:
            usage(1, "-i argument is needed")
    except StandardError, e:
        usage(e)

    print format_records(recIDs=options["recID"],
                         of=options["output"],
                         ln=options["lang"],
                         verbose=options["verbose"],
                         on_the_fly=options["onthefly"])

    return

if __name__ == "__main__":
    main()
