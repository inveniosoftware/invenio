# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015 CERN.
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

"""Format records using chosen format.

The main APIs are:
- format_record
- format_records
- create_excel
- get_output_format_content_type

This module wraps the BibFormat engine and its associated
functions. This is also where special formatting functions of multiple
records (that the engine does not handle, as it works on a single
record basis) should be defined, with name C{def create_*}.

.. seealso::

    bibformat_utils.py

"""
from __future__ import print_function

import getopt
import sys
import zlib

from invenio.base.globals import cfg


# Functions to format a single record
#
def format_record(recID, of, ln=None, verbose=0, search_pattern=None,
                  xml_record=None, user_info=None, on_the_fly=False,
                  save_missing=True, force_2nd_pass=False, **kwargs):
    """Format a record in given output format.

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

    :param recID: the ID of record to format.
    :type recID: int
    :param of: an output format code (or short identifier for the output
               format)
    :type of: string
    :param ln: the language to use to format the record
    :type ln: string
    :param verbose: the level of verbosity from 0 to 9.
                    - O: silent
                    - 5: errors
                    - 7: errors and warnings, stop if error in format elements
                    - 9: errors and warnings, stop if error (debug mode)
    :type verbose: int
    :param search_pattern: list of strings representing the user request in web
                           interface
    :type search_pattern: list(string)
    :param xml_record: an xml string represention of the record to format
    :type xml_record: string or None
    :param user_info: the information of the user who will view the formatted
                      page (if applicable)
    :param on_the_fly: if False, try to return an already preformatted version
                       of the record in the database
    :type on_the_fly: boolean
    :return: formatted record
    :rtype: string
    """
    ln = ln or cfg['CFG_SITE_LANG']
    from . import engine as bibformat_engine

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
        **kwargs)
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
            **kwargs)

    return out


def record_get_xml(recID, format='xm', decompress=zlib.decompress):
    """Return an XML string of the record given by recID.

    The function builds the XML directly from the database,
    without using the standard formatting process.

    'format' allows to define the flavour of XML:
        - 'xm' for standard XML
        - 'marcxml' for MARC XML
        - 'oai_dc' for OAI Dublin Core
        - 'xd' for XML Dublin Core

    If record does not exist, returns empty string.

    :param recID: the id of the record to retrieve
    :param format: the format to use
    :param decompress: the library to use to decompress cache from DB
    :return: the xml string of the record
    """
    from . import utils as bibformat_utils
    return bibformat_utils.record_get_xml(recID=recID, format=format,
                                          decompress=decompress)


# Helper functions to do complex formatting of multiple records
#
# You should not modify format_records when adding a complex
# formatting of multiple records, but add a create_* method
# that relies on format_records to do the formatting.
#
def format_records(recIDs, of, ln=None, verbose=0, search_pattern=None,
                   xml_records=None, user_info=None, record_prefix=None,
                   record_separator=None, record_suffix=None, prologue="",
                   epilogue="", req=None, on_the_fly=False,
                   extra_context=None):
    """Format records given by a list of record IDs or a list of records as xml.

    Add a prefix before each record, a suffix after each record, plus a
    separator between records.

    Also add optional prologue and epilogue to the complete formatted list.

    You can either specify a list of record IDs to format, or a list of xml
    records, but not both (if both are specified recIDs is ignored).

    'record_separator' is a function that returns a string as separator between
    records.  The function must take an integer as unique parameter, which is
    the index in recIDs (or xml_records) of the record that has just been
    formatted. For example separator(i) must return the separator between
    recID[i] and recID[i+1]. Alternatively separator can be a single string,
    which will be used to separate all formatted records.  The same applies to
    'record_prefix' and 'record_suffix'.

    'req' is an optional parameter on which the result of the function are
    printed lively (prints records after records) if it is given. Note that you
    should set 'req' content-type by yourself, and send http header before
    calling this function as it will not do it.

    This function takes the same parameters as :meth:`format_record` except
    for:

    :param recIDs: a list of record IDs
    :type recIDs: list(int)
    :param of: an output format code (or short identifier for the output
               format)
    :type of: string
    :param ln: the language to use to format the record
    :type ln: string
    :param verbose: the level of verbosity from 0 to 9.
                    - 0: silent
                    - 5: errors
                    - 7: errors and warnings, stop if error in format elements
                    - 9: errors and warnings, stop if error (debug mode)
    :type verbose: int
    :param search_pattern: list of strings representing the user request in web
                           interface
    :type search_pattern: list(string)
    :param user_info: the information of the user who will view the formatted
                      page (if applicable)
    :param xml_records: a list of xml string representions of the records to
                        format
    :type xml_records: list(string)
    :param record_prefix: a string printed before B{each} formatted records (n
                          times)
    :type record_prefix: string
    :param record_suffix: a string printed after B{each} formatted records (n
                          times)
    :type record_suffix: string
    :param prologue: a string printed at the beginning of the complete
                     formatted records (1x)
    :type prologue: string
    :param epilogue: a string printed at the end of the complete formatted
                     output (1x)
    :type epilogue: string
    :param record_separator: either a string or a function that returns string
                             to join formatted records
    :param record_separator: string or function
    :param req: an optional request object where to print records
    :param on_the_fly: if False, try to return an already preformatted version
                       of the record in the database
    :type on_the_fly: boolean
    :rtype: string
    """
    if req is not None:
        req.write(prologue)

    formatted_records = ''

    # Fill one of the lists with Nones
    if xml_records is not None:
        recIDs = map(lambda x: None, xml_records)
    else:
        xml_records = map(lambda x: None, recIDs)

    total_rec = len(recIDs)
    last_iteration = False
    for i in range(total_rec):
        if i == total_rec - 1:
            last_iteration = True

        # Print prefix
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

        # Print formatted record
        ln = ln or cfg['CFG_SITE_LANG']
        formatted_record = format_record(recIDs[i], of, ln, verbose,
                                         search_pattern, xml_records[i],
                                         user_info, on_the_fly, extra_context)
        formatted_records += formatted_record
        if req is not None:
            req.write(formatted_record)

        # Print suffix
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

        # Print separator if needed
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
    """Wrapper around format template."""
    from . import engine as bibformat_engine
    evaluated_format, dummy = bibformat_engine.format_with_format_template(
        format_template_filename=format_template_filename,
        bfo=bfo,
        verbose=verbose,
        format_template_code=format_template_code)
    return evaluated_format


def create_excel(recIDs, req=None, ln=None, ot=None, ot_sep="; ",
                 user_info=None):
    """Return an Excel readable format containing the given recIDs.

    If 'req' is given, also prints the output in 'req' while individual
    records are being formatted.

    This method shows how to create a custom formatting of multiple
    records.
    The excel format is a basic HTML table that most spreadsheets
    applications can parse.

    If 'ot' is given, the BibFormat engine is overridden and the
    output is produced on the basis of the fields that 'ot' defines
    (see search_engine.perform_request_search(..) 'ot' param).

    :param req: the request object
    :param recIDs: a list of record IDs
    :param ln: language
    :param ot: a list of fields that should be included in the excel output as
               columns(see perform_request_search 'ot' param)
    :param ot_sep: a separator used to separate values for the same record, in
                   the same columns, if any
    :param user_info: the user_info dictionary
    :return: a string in Excel format
    """
    from . import utils as bibformat_utils
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
    column_headers = '</b></td><td style="border-color:black; ' \
                     'border-style:solid; border-width:thin; ' \
                     'background-color:black;color:white"><b>' \
                     .join(column_headers_list) + ''
    column_headers = '<table style="border-collapse: collapse;">\n' \
                     '<td style="border-color:black; border-style:solid; ' \
                     'border-width:thin; background-color:black;color:white">'\
                     '<b>' + column_headers + '</b></td>'
    footer = '</table>'

    # Apply content_type and print column headers
    if req is not None:
        req.content_type = get_output_format_content_type('excel')
        req.headers_out["Content-Disposition"] = "inline; filename=results.xls"
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
            row += '<td><a href="%(CFG_SITE_URL)s/%(CFG_SITE_RECORD)s/' \
                   '%(recID)i">%(recID)i</a></td>' % \
                   {'recID': recID, 'CFG_SITE_RECORD': cfg['CFG_SITE_RECORD'],
                    'CFG_SITE_URL': cfg['CFG_SITE_URL']}
            for field in ot:
                row += '<td>%s</td>' % \
                       ot_sep.join(bibformat_utils.get_all_fieldvalues(
                           recID, field))
            row += '</tr>'
            out += row
            if req:
                req.write(row)
        out += '</table>'
        if req:
            req.write('</table>')
        return out

    # Format the records
    prologue = '<meta http-equiv="Content-Type" content="text/html; ' \
               'charset=utf-8"><table>'
    excel_formatted_records = format_records(recIDs, 'excel',
                                             ln=ln or cfg['CFG_SITE_LANG'],
                                             record_separator='\n',
                                             prologue=prologue,
                                             epilogue=footer,
                                             req=req,
                                             user_info=user_info)

    return excel_formatted_records


def get_output_format_content_type(of, default_content_type="text/html"):
    """
    Return the content type of the given output format.

    For example `text/html` or `application/ms-excel`.

    :param of: the code of output format for which we want to get the content
               type
    :param default_content_type: default content-type when content-type was not
                                 set up
    :return: the content-type to use for this output format
    """
    from . import api
    content_type = api.get_output_format_content_type(of)

    if content_type == '':
        content_type = default_content_type

    return content_type


def print_records(recIDs, of='hb', ln=None, verbose=0,
                  search_pattern='', on_the_fly=False, **ctx):
    """Return records using Jinja template."""
    import time
    from math import ceil
    from flask import request
    from invenio.base.i18n import wash_language
    from invenio.ext.template import render_template_to_string
    from invenio.modules.search.models import Format
    from invenio.utils.pagination import Pagination
    from invenio.modules.formatter.engine import \
        TEMPLATE_CONTEXT_FUNCTIONS_CACHE

    of = of.lower()
    jrec = request.values.get('jrec', ctx.get('jrec', 1), type=int)
    rg = request.values.get('rg', ctx.get('rg', 10), type=int)
    ln = ln or wash_language(request.values.get('ln', cfg['CFG_SITE_LANG']))
    ot = (request.values.get('ot', ctx.get('ot')) or '').split(',')
    records = ctx.get('records', len(recIDs))

    if jrec > records:
        jrec = rg * (records // rg) + 1

    pages = int(ceil(jrec / float(rg))) if rg > 0 else 1

    context = dict(
        of=of, jrec=jrec, rg=rg, ln=ln, ot=ot,
        facets={},
        time=time,
        recids=recIDs,
        pagination=Pagination(pages, rg, records),
        verbose=verbose,
        export_formats=Format.get_export_formats(),
        format_record=format_record,
        **TEMPLATE_CONTEXT_FUNCTIONS_CACHE.template_context_functions
    )
    context.update(ctx)
    return render_template_to_string(
        ['format/records/%s.tpl' % of,
         'format/records/%s.tpl' % of[0],
         'format/records/%s.tpl' % get_output_format_content_type(of).
            replace('/', '_')],
        **context)


def usage(exitcode=1, msg=""):
    """
    Print usage info.

    :param exitcode: exit code to use (eg. 1 for error, 0 for okay)
    :param msg: message to print
    :return: exit the process
    """
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)
    print("""BibFormat: outputs the result of the formatting of a record.

    Usage: bibformat required [options]
    Examples:
      $ bibformat -i 10 -o HB
      $ bibformat -i 10,11,13 -o HB
      $ bibformat -i 10:13
      $ bibformat -i 10 -o HB -v 9

    Required:
     -i, --id=ID[ID2,ID3:ID5]  ID (or range of IDs) of the record(s) to be
                               formatted.

    Options:
     -o, --output=CODE         short code of the output format used for
                               formatting (default HB).
     -l, --lang=LN             language used for formatting.
     -y, --onthefly            on-the-fly formatting, avoiding caches created
                               by BibReformat.

    General options:
     -h, --help                print this help and exit
     -v, --verbose=LEVEL       verbose level (from 0 to 9, default 0)
     """)
    sys.exit(exitcode)


def main():
    """
    Main entry point for biformat via command line.

    :return: formatted record(s) as specified by options, or help/errors

    """
    options = {}  # will hold command-line options
    options["verbose"] = 0
    options["onthefly"] = False
    options["lang"] = cfg['CFG_SITE_LANG']
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
    except getopt.GetoptError as err:
        usage(1, err)
        pass
    try:
        for opt in opts:
            if opt[0] in ["-h", "--help"]:
                usage(0)
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
    except StandardError as e:
        usage(e)

    print(format_records(recIDs=options["recID"],
                         of=options["output"],
                         ln=options["lang"],
                         verbose=options["verbose"],
                         on_the_fly=options["onthefly"]))

    return

if __name__ == "__main__":
    main()
