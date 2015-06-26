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


from .engine import format_record


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
