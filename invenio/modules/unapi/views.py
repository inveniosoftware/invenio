# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""UnAPI service hooks implementation."""

from flask import (Blueprint, make_response, redirect, render_template,
                   request, url_for)

from invenio.base.globals import cfg
from invenio.modules.formatter.registry import output_formats

from six import iteritems

blueprint = Blueprint('unapi', __name__, url_prefix="/unapi",
                      template_folder='templates', static_folder='static')


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    """Handle /unapi set of pages."""
    # Prepare mappings from configuration.
    mapping = cfg['UNAPI_FORMAT_MAPPING']
    names = {mapping[k]: k for k in mapping}
    # Clean request arguments.
    identifier = request.values.get('id', type=int)
    format_ = request.values.get('format')
    format_ = mapping.get(format_, format_)
    # Redirect to correct record format.
    if identifier and format_:
        return redirect(url_for('record.metadata', recid=identifier,
                                of=format_))

    formats = [{
        'name': names[of],
        'type': values['content_type'],
        'docs': values.get('url'),
    } for of, values in iteritems(output_formats) if of in names]

    response = make_response(render_template(
        'unapi/index.xml', identifier=identifier, formats=formats))
    response.headers['Content-Type'] = 'application/xml'
    return response
