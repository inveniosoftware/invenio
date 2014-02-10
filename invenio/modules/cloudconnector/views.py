# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

"""Cloud Application Blueprint"""

import math

from fs.opener import fsopen
from flask import Blueprint, render_template, session, request, flash, \
    redirect, url_for, current_app
from flask.ext.login import login_required

from invenio.base.globals import cfg
from invenio.base.i18n import _
from flask_breadcrumbs import default_breadcrumb_root, register_breadcrumb
from flask_menu import register_menu

from .factory import CloudServiceFactory
from .errors import CloudRedirectUrl


blueprint = Blueprint('cloudutils', __name__, url_prefix="/cloud",
                      template_folder='templates', static_folder='static')

default_breadcrumb_root(blueprint, '.webaccount.cloudconnector')


def service_pretty_name(service):
    return cfg.get('CFG_SERVICE_PRETTY_NAME', {}).get(service, service)


@blueprint.errorhandler(CloudRedirectUrl)
def connect_cloud(error):
    url, service = error
    service = service.split('.')[-1]
    if service.endswith('_factory'):
        service = service[:-len('_factory')]
    prompt = _('Click <a href="%(url)s">here</a> to connect your account with %(service)s.',
               url=url,
               service=service_pretty_name(service))
    flash(prompt, 'info')
    return redirect(url_for('.index'))


@blueprint.errorhandler(Exception)
def general_error(error):
    #FIXME add logging
    #register_exception()
    flash(_('Unexpected error.'), 'error')
    return redirect(url_for('.index'))


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/<service>', methods=['GET', 'POST'])
@login_required
@register_breadcrumb(blueprint, '.', _('Your Cloud Applications'))
@register_menu(blueprint, 'personalize.cloudconnector',
               _('Your Cloud Applications'))
def index(service=None):
    if service is None:
        return render_template('cloudconnector/browser.html')

    #FIXME [dict(text=service_pretty_name(service),
    #             url=url_for('cloudutils.index', service=service))]

    filesystem = _build_file_system(service)

    if 'files_to_upload' in session:
        return upload(service)

    return _build_page(filesystem, service)


@blueprint.route('/<service>/callback', methods=['GET', 'POST'])
@login_required
def callback(service):
    # Check that we can build filesystem for given service.
    _build_file_system(service)
    return redirect(url_for('cloudutils.index', service=service))


@blueprint.route('/<service>/download', methods=['GET', 'POST'])
@login_required
def download(service):
    filesystem = _build_file_system(service)
    return filesystem.getcontents(request.args.get('path'))


@blueprint.route('/<service>/delete', methods=['GET', 'POST'])
@login_required
def delete(service):
    filesystem = _build_file_system(service)

    if filesystem.isdir(request.args.get('path')):
        filesystem.removedir(request.args.get('path'))
    else:
        filesystem.remove(request.args.get('path'))
    return redirect(url_for('cloudutils.index', service=service))


@blueprint.route('/<service>/upload', methods=['GET', 'POST'])
@login_required
def upload(service):
    if request.form.has_key('files'):
        session['return_url'] = request.form['return_url']
        files = request.form['files']
        session['files_to_upload'] = files[2:-2].split("', '")

    filesystem = _build_file_system(service)

    files = session.pop('files_to_upload')
    from invenio.legacy.bibdocfile.api import bibdocfile_url_to_bibdocfile

    try:
        for one in files:
            docfile = bibdocfile_url_to_bibdocfile(one)
            f = fsopen(docfile.get_full_path(), 'r')
            n = filesystem.open(docfile.get_full_name(), "w")
            n.write(f.read())
            n.close()
        flash("All files uploaded successfully", 'info')
    except:
        flash("Something went wrong, please try again", 'error')

    return redirect(session.pop('return_url'))


def _build_file_system(service):
    return CloudServiceFactory().get_fs('%s://' % (service, ))


def _build_page(filesystem, service):
    folder_metadata = filesystem.listdirinfo(request.args.get('path', ""))
    number_of_pages = int(math.ceil(float(len(folder_metadata)) /
                                    cfg['CFG_CLOUD_UTILS_ROWS_PER_PAGE']))
    current_page = int(request.args.get('page', '1'))
    account_info = filesystem.about()

    if current_page == 1 and number_of_pages > 1:
        folder_metadata = folder_metadata[0:cfg['CFG_CLOUD_UTILS_ROWS_PER_PAGE']]
    elif number_of_pages > 1 and current_page <= number_of_pages:
        folder_metadata = folder_metadata[
            cfg['CFG_CLOUD_UTILS_ROWS_PER_PAGE']*(current_page-1):
            cfg['CFG_CLOUD_UTILS_ROWS_PER_PAGE']*current_page]

    return render_template('cloudconnector/browser.html',
                           service_name=[service, filesystem.__name__],
                           service=service,
                           parent="/".join(
                               request.args.get('path', "/").split("/")[:-1]),
                           folder_metadata=folder_metadata,
                           account_info=account_info,
                           number_of_pages=number_of_pages,
                           current_page=current_page,
                           )
