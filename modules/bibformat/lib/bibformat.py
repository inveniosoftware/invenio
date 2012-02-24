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
from invenio.errorlib import register_exception
from invenio.config import \
     CFG_SITE_LANG, \
     CFG_PATH_PHP, \
     CFG_SITE_URL, \
     CFG_BIBFORMAT_HIDDEN_TAGS, \
     CFG_SITE_RECORD, \
     CFG_BIBFORMAT_DISABLE_I18N_FOR_CACHED_FORMATS
from invenio.bibformat_config import \
     CFG_BIBFORMAT_USE_OLD_BIBFORMAT
from invenio.access_control_engine import acc_authorize_action
import getopt
import sys

# Functions to format a single record
##

def format_record(recID, of, ln=CFG_SITE_LANG, verbose=0, search_pattern=None,
                  xml_record=None, user_info=None, on_the_fly=False):
    """
    Format a record in given output format.

    Return a formatted version of the record in the specified
    language, search pattern, and with the specified output format.
    The function will define which format template must be applied.

    The record to be formatted can be specified with its ID (with
    'recID' parameter) or given as XML representation (with
    'xml_record' parameter). If 'xml_record' is specified 'recID' is
    ignored (but should still be given for reference. A dummy recid 0
    or -1 could be used).

    'user_info' allows to grant access to some functionalities on a
    page depending on the user's priviledges. The 'user_info' object
    makes sense only in the case of on-the-fly formatting. 'user_info'
    is the same object as the one returned by
    'webuser.collect_user_info(req)'

    @param recID: the ID of record to format.
    @type recID: int
    @param of: an output format code (or short identifier for the output format)
    @type of: string
    @param ln: the language to use to format the record
    @type ln: string
    @param verbose: the level of verbosity from 0 to 9 (O: silent,
                                                       5: errors,
                                                       7: errors and warnings, stop if error in format elements
                                                       9: errors and warnings, stop if error (debug mode ))
    @type verbose: int
    @param search_pattern: list of strings representing the user request in web interface
    @type search_pattern: list(string)
    @param xml_record: an xml string represention of the record to format
    @type xml_record: string or None
    @param user_info: the information of the user who will view the formatted page (if applicable)
    @param on_the_fly: if False, try to return an already preformatted version of the record in the database
    @type on_the_fly: boolean
    @return: formatted record
    @rtype: string
    """
    from invenio.search_engine import record_exists
    if search_pattern is None:
        search_pattern = []

    out = ""

    if verbose == 9:
        out += """\n<span class="quicknote">
        Formatting record %i with output format %s.
        </span>""" % (recID, of)
    ############### FIXME: REMOVE WHEN MIGRATION IS DONE ###############
    if CFG_BIBFORMAT_USE_OLD_BIBFORMAT and CFG_PATH_PHP:
        return bibformat_engine.call_old_bibformat(recID, of=of, on_the_fly=on_the_fly)
    ############################# END ##################################
    if not on_the_fly and \
       (ln == CFG_SITE_LANG or \
        of.lower() == 'xm' or \
        CFG_BIBFORMAT_USE_OLD_BIBFORMAT or \
        (of.lower() in CFG_BIBFORMAT_DISABLE_I18N_FOR_CACHED_FORMATS)) and \
        record_exists(recID) != -1:
        # Try to fetch preformatted record. Only possible for records
        # formatted in CFG_SITE_LANG language (other are never
        # stored), or of='xm' which does not depend on language.
        # Exceptions are made for output formats defined in
        # CFG_BIBFORMAT_DISABLE_I18N_FOR_CACHED_FORMATS, which are
        # always served from the same cache for any language.  Also,
        # do not fetch from DB when record has been deleted: we want
        # to return an "empty" record in that case
        res = bibformat_dblayer.get_preformatted_record(recID, of)
        if res is not None:
            # record 'recID' is formatted in 'of', so return it
            if verbose == 9:
                last_updated = bibformat_dblayer.get_preformatted_record_date(recID, of)
                out += """\n<br/><span class="quicknote">
                Found preformatted output for record %i (cache updated on %s).
                </span><br/>""" % (recID, last_updated)
            if of.lower() == 'xm':
                res = filter_hidden_fields(res, user_info)
            out += res
            return out
        else:
            if verbose == 9:
                out += """\n<br/><span class="quicknote">
                No preformatted output found for record %s.
                </span>"""% recID


    # Live formatting of records in all other cases
    if verbose == 9:
        out += """\n<br/><span class="quicknote">
        Formatting record %i on-the-fly.
        </span>""" % recID

    try:
        out += bibformat_engine.format_record(recID=recID,
                                              of=of,
                                              ln=ln,
                                              verbose=verbose,
                                              search_pattern=search_pattern,
                                              xml_record=xml_record,
                                              user_info=user_info)
        if of.lower() == 'xm':
            out = filter_hidden_fields(out, user_info)
        return out
    except Exception, e:
        register_exception(prefix="An error occured while formatting record %i in %s" % \
                           (recID, of),
                           alert_admin=True)
        #Failsafe execution mode
        import invenio.template
        websearch_templates = invenio.template.load('websearch')
        if verbose == 9:
            out += """\n<br/><span class="quicknote">
            An error occured while formatting record %i. (%s)
            </span>""" % (recID, str(e))
        if of.lower() == 'hd':
            if verbose == 9:
                out += """\n<br/><span class="quicknote">
                Formatting record %i with websearch_templates.tmpl_print_record_detailed.
                </span><br/>""" % recID
                return out + websearch_templates.tmpl_print_record_detailed(
                    ln = ln,
                    recID = recID,
                    )
        if verbose == 9:
            out += """\n<br/><span class="quicknote">
            Formatting record %i with websearch_templates.tmpl_print_record_brief.
            </span><br/>""" % recID
        return out + websearch_templates.tmpl_print_record_brief(ln = ln,
                                                                 recID = recID,
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
                   epilogue="", req=None, on_the_fly=False):
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
    @rtype: string
    """
    if req is not None:
        req.write(prologue)

    formatted_records = ''

    #Fill one of the lists with Nones
    if xml_records is not None:
        recIDs = map(lambda x:None, xml_records)
    else:
        xml_records = map(lambda x:None, recIDs)

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
        formatted_record = format_record(recIDs[i], of, ln, verbose, \
                                         search_pattern, xml_records[i],\
                                         user_info, on_the_fly)
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

def create_excel(recIDs, req=None, ln=CFG_SITE_LANG, ot=None, ot_sep="; "):
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
        if req: req.write("<table>")
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
            if req: req.write(row)
        out += '</table>'
        if req: req.write('</table>')
        return out

    #Format the records
    excel_formatted_records = format_records(recIDs, 'excel', ln=CFG_SITE_LANG,
                                             record_separator='\n',
                                             prologue = '<meta http-equiv="Content-Type" content="text/html; charset=utf-8"><table>',
                                             epilogue = footer,
                                             req=req)

    return excel_formatted_records

# Utility functions
##
def filter_hidden_fields(recxml, user_info=None, filter_tags=CFG_BIBFORMAT_HIDDEN_TAGS,
                         force_filtering=False):
    """
    Filter out tags specified by filter_tags from MARCXML. If the user
    is allowed to run bibedit, then filter nothing, unless
    force_filtering is set to True.

    @param recxml: marcxml presentation of the record
    @param user_info: user information; if None, then assume invoked via CLI with all rights
    @param filter_tags: list of MARC tags to be filtered
    @param force_filtering: do we force filtering regardless of user rights?
    @return: recxml without the hidden fields
    """
    if force_filtering:
        pass
    else:
        if user_info is None:
            #by default
            return recxml
        else:
            if (acc_authorize_action(user_info, 'runbibedit')[0] == 0):
                #no need to filter
                return recxml
    #filter..
    out = ""
    omit = False
    for line in recxml.splitlines(True):
        #check if this block needs to be omitted
        for htag in filter_tags:
            if line.count('datafield tag="'+str(htag)+'"'):
                omit = True
        if not omit:
            out += line
        if omit and line.count('</datafield>'):
            omit = False
    return out

def get_output_format_content_type(of):
    """
    Returns the content type (for example 'text/html' or 'application/ms-excel') \
    of the given output format.

    @param of: the code of output format for which we want to get the content type
    @return: the content-type to use for this output format
    """
    content_type = bibformat_dblayer.get_output_format_content_type(of)

    if content_type == '':
        content_type = 'text/html'

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
        opts, args = getopt.getopt(sys.argv[1:],
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
        pass
    try:
        for opt in opts:
            if opt[0] in ["-h", "--help"]:
                usage(0)
            elif opt[0] in ["-V", "--version"]:
                print __revision__
                sys.exit(0)
            elif opt[0] in ["-v", "--verbose"]:
                options["verbose"]  = int(opt[1])
            elif opt[0] in ["-y", "--onthefly"]:
                options["onthefly"]    = True
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
                options["output"]  = opt[1]

        if options["recID"] == None:
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
