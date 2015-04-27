# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
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

"""Implementation of Blueprint for previewers."""

from __future__ import unicode_literals

import itertools
import os

from flask import Blueprint, current_app, request

from flask_breadcrumbs import default_breadcrumb_root

from invenio.base.globals import cfg
from invenio.config import CFG_SITE_RECORD
from invenio.modules.records.views import request_record

from .registry import previewers
from .utils import get_record_documents, get_record_files

blueprint = Blueprint('previewer', __name__, url_prefix="/" + CFG_SITE_RECORD,
                      static_url_path='/record', template_folder='templates',
                      static_folder='static')

default_breadcrumb_root(blueprint, '.')


@blueprint.route('/<int:recid>/preview', methods=['GET', 'POST'])
@request_record
def preview(recid):
    """Preview file for given record."""
    filename = request.args.get('filename', type=str)

    for f in itertools.chain(get_record_documents(recid, filename),
                             get_record_files(recid, filename)):
        if f.name + f.superformat == filename or filename is None:
            extension = os.path.splitext(f.name + f.superformat)[1]
            ordered = previewers.keys()
            if "CFG_PREVIEW_PREFERENCE" in cfg and \
               extension in cfg["CFG_PREVIEW_PREFERENCE"]:
                from collections import OrderedDict
                ordered = OrderedDict.fromkeys(
                    cfg["CFG_PREVIEW_PREFERENCE"][extension] +
                    ordered).keys()

            try:
                for plugin_id in ordered:
                    if previewers[plugin_id]['can_preview'](f):
                        return previewers[plugin_id]['preview'](f)
            except Exception:
                current_app.logger.exception(
                    "Preview plugin {0} failed "
                    "previewing {1} in record {2}".format(
                        plugin_id, filename, recid
                    )
                )
    return previewers['default']['preview'](None)


@blueprint.route('/<int:recid>/preview/pdfmaxpage', methods=['GET', 'POST'])
@request_record
def get_pdf_maxpage(recid):
    """Get maximal page from pdf."""
    from invenio.legacy.bibdocfile.api import BibRecDocs
    from .previewerext.pdftk import maxpage

    return maxpage(BibRecDocs(recid).list_latest_files(list_hidden=False)[0])
