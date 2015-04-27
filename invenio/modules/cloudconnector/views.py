# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Cloud Application Blueprint."""

from __future__ import unicode_literals

from flask import Blueprint, current_app, flash, make_response, redirect, \
    render_template, request, url_for

from flask_breadcrumbs import default_breadcrumb_root, register_breadcrumb

from flask_login import login_required

from flask_menu import register_menu

from invenio.base.i18n import _
from invenio.modules.cloudconnector.utils import (_build_filesystem,
                                                  _build_page)

from .config import CLOUDCONNECTOR_SERVICE_NAME_MAPPING
from .errors import CloudRedirectUrl

blueprint = Blueprint('cloudutils', __name__, url_prefix="/cloud",
                      template_folder='templates', static_folder='static')

default_breadcrumb_root(blueprint, '.webaccount.cloudconnector')


@blueprint.errorhandler(CloudRedirectUrl)
def connect_cloud(error):
    """Connect to the service."""
    url, service = error
    service = service.split('.')[-1]
    prompt = _('Click <a href="%(url)s">here</a> to connect your account'
               ' with %(service)s.',
               url=url,
               service=CLOUDCONNECTOR_SERVICE_NAME_MAPPING.get(service))
    flash(prompt, 'info')
    return redirect(url_for('.index'))


@blueprint.errorhandler(Exception)
def general_error(error):
    """Print 'Error' and redirect to index page."""
    current_app.logger.exception(error)

    flash(_('Unexpected error.'), 'error')
    return redirect(url_for('.index'))


@blueprint.route('/', methods=['GET', 'POST'])
@register_menu(blueprint, 'personalize.cloudconnector',
               _('Your Cloud Applications'))
def index():
    """Index page of the application."""
    return render_template('cloudconnector/browser.html')


@blueprint.route('/<service>', methods=['GET', 'POST'])
@login_required
@register_breadcrumb(blueprint, '.', _('Your Cloud Applications'))
def view(service):
    """View page."""
    try:
        filesystem = _build_filesystem(service)
    except Exception as e:
        current_app.logger.exception(e)
        raise

    return _build_page(filesystem, service)


@blueprint.route('/<service>/callback', methods=['GET', 'POST'])
@login_required
def callback(service):
    """Check that we can build a filesystem from the given service."""
    _build_filesystem(service)
    return redirect(url_for('cloudutils.view', service=service))


@blueprint.route('/<service>/download', methods=['GET', 'POST'])
@login_required
def download(service):
    """Download a file."""
    filesystem = _build_filesystem(service)

    if filesystem.haspathurl(request.args.get('path')):
        url = filesystem.getpathurl(request.args.get('path'))
        return redirect(url)
    else:
        return make_response(filesystem.open(
            request.args.get('path'), 'rb').read())


@blueprint.route('/<service>/delete', methods=['GET', 'POST'])
@login_required
def delete(service):
    """Delete a file."""
    filesystem = _build_filesystem(service)
    if filesystem.isdir(request.args.get('path')):
        filesystem.removedir(request.args.get('path'))
    else:
        filesystem.remove(request.args.get('path'))
    return redirect(url_for('cloudutils.view', service=service))
