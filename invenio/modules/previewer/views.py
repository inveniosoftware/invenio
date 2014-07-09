# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013, 2014 CERN.
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

"""Previews Blueprint"""

from flask import Blueprint, request
from flask.ext.breadcrumbs import default_breadcrumb_root

from invenio.base.globals import cfg
from invenio.config import CFG_SITE_RECORD

from .registry import previewers


blueprint = Blueprint('previewer', __name__, url_prefix="/" + CFG_SITE_RECORD,
                      static_url_path='/record', template_folder='templates',
                      static_folder='static')

default_breadcrumb_root(blueprint, '.')


@blueprint.route('/<int:recid>/preview', methods=['GET', 'POST'])
def preview(recid):
    from invenio.legacy.bibdocfile.api import BibRecDocs

    files = BibRecDocs(recid).list_latest_files(list_hidden=False)
    filename = request.args.get('filename', type=str)

    for f in files:
        if f.name + f.superformat == filename or filename is None:
            ordered = previewers.keys()
            if "CFG_PREVIEW_PREFERENCE" in cfg and \
               f.superformat in cfg["CFG_PREVIEW_PREFERENCE"]:
                from collections import OrderedDict
                ordered = OrderedDict.fromkeys(
                    cfg["CFG_PREVIEW_PREFERENCE"][f.superformat] +
                    ordered).keys()

            for plugin_id in ordered:
                if previewers[plugin_id]['can_preview'](f):
                    return previewers[plugin_id]['preview'](f)
    return previewers['default']['preview'](None)


@blueprint.route('/<int:recid>/preview/pdfmaxpage', methods=['GET', 'POST'])
def get_pdf_maxpage(recid):
    from invenio.legacy.bibdocfile.api import BibRecDocs
    from .previewerext.pdftk import maxpage

    return maxpage(BibRecDocs(recid).list_latest_files(list_hidden=False)[0])
