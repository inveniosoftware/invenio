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

from flask import Blueprint
from flask.ext.breadcrumbs import default_breadcrumb_root

from .registry import previews

from invenio.base.decorators import wash_arguments
from invenio.config import CFG_SITE_RECORD
from invenio.modules.records.views import request_record

blueprint = Blueprint('previews', __name__, url_prefix="/" + CFG_SITE_RECORD,
                      static_url_path='/record', template_folder='templates',
                      static_folder='static')

default_breadcrumb_root(blueprint, '.')


@blueprint.route('/<int:recid>/preview', methods=['GET', 'POST'])
@wash_arguments({'embed': (unicode, 'False'), 'filename': (unicode, None)})
@request_record
def preview(recid, embed=False, filename=None):
    from invenio.legacy.bibdocfile.api import BibRecDocs

    files = BibRecDocs(recid).list_latest_files(list_hidden=False)
    f = None

    for f in files:
        if f.name + f.superformat == filename:
            for plugin_id in previews:
                if previews[plugin_id]['can_preview'](f):
                    return previews[plugin_id]['preview'](f, embed == 'true')
    return previews['preview_default']['preview'](filename, embed == 'true')
