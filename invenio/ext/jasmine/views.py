# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Views for Jasmine test runner."""

from __future__ import unicode_literals

from flask import Blueprint, abort, render_template, send_file, url_for

from .registry import specs

blueprint = Blueprint(
    'jasmine',
    __name__,
    url_prefix='/jasmine',
    static_folder='static',
    template_folder='templates',
)


@blueprint.route('/specrunner/', methods=['GET'])
def specrunner():
    """Render Jasmine test runner page."""
    modules = sorted([url_for('jasmine.spec', specpath=x)
                     for x in specs.keys() if x.endswith(".spec.js")])
    return render_template('jasmine/specrunner.html', modules=modules)


@blueprint.route('/spec/<path:specpath>', methods=['GET'])
def spec(specpath):
    """Send a single spec file."""
    if specpath not in specs:
        abort(404)

    mimetype = "text/html" if specpath.endswith(".html") else \
               "application/javascript"

    return send_file(
        specs[specpath],
        mimetype=mimetype,
        conditional=False,
        add_etags=False,
    )
