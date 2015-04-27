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

"""Format records using chosen format."""

from invenio.base.globals import cfg


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
    from invenio.utils.pagination import Pagination
    from .registry import export_formats
    from .engine import TEMPLATE_CONTEXT_FUNCTIONS_CACHE

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
        export_formats=export_formats,
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
