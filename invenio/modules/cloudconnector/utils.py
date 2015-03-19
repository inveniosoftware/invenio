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

"""Implement various utils for the cloud services."""

import math

from flask import session, request, render_template
from flask_login import current_user
from flask.helpers import url_for

from sqlalchemy import event

from werkzeug.utils import import_string

from invenio.base.globals import cfg
from invenio.modules.cloudconnector.registry import fsopeners
# TODO from invenio.modules.tags.models import WtgTAGRecord


def get_fsopener_module(key):
    """Register fsopener modules."""
    for module in fsopeners:
        if module.__name__.rsplit(".", 1)[1] == key:
            return import_string(module.__name__+':Factory')


def _build_filesystem(service):
    """Build the filesystem of the cloud application."""
    credentials = {}
    # Every user can have his own root directory
    # inside of every service settings
    root = credentials.get("root", "/")

    callback_url = url_for('cloudutils.callback', service=service,
                           _external=True)

    Factory = get_fsopener_module(service)()
    filesystem = Factory.build_fs(current_user, credentials,
                                  root, callback_url,
                                  request, session
                                  )
    return filesystem


def _build_page(filesystem, service):
    """Build the index page of the cloud service."""
    from operator import itemgetter

    folder_metadata = filesystem.listdirinfo(request.args.get('path', "/"))
    folder_metadata = map(lambda x: x[1], folder_metadata)
    folder_metadata.sort(key=itemgetter('isdir'), reverse=True)

    number_of_pages = int(math.ceil(float(len(folder_metadata)) /
                                    cfg['CLOUDCONNECTOR_ROWS_PER_PAGE']))

    current_page = int(request.args.get('page', '1'))
    account_info = filesystem.about()

    if current_page == 1 and number_of_pages > 1:
        folder_metadata = folder_metadata[0:
                                          cfg['CLOUDCONNECTOR_ROWS_PER_PAGE']]
    elif number_of_pages > 1 and current_page <= number_of_pages:
        folder_metadata = folder_metadata[
            cfg['CLOUDCONNECTOR_ROWS_PER_PAGE']*(current_page-1):
            cfg['CLOUDCONNECTOR_ROWS_PER_PAGE']*current_page]
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


def upload(service, src, dest):
    """Upload a file to the cloud application."""
    fs = _build_filesystem(service)
    f = open(src, 'r')
    n = fs.open(dest, 'w')
    n.write(f.read())
    n.close()


# TODO @event.listens_for(WtgTAGRecord, 'after_insert')
def receive_after_insert(mapper, connection, target):
    """Check 'after_insert' signal for Tags."""
    from invenio.modules.records.api import get_record

    record = get_record(target.id_bibrec)
    if 'files' in record:
        for rec in record['files']:
            if 'full_path' in rec and target.tag.name in \
                    cfg['CLOUDCONNECTOR_SERVICE_NAME_MAPPING']:
                # FIXME make the upload asynchronous
                upload(target.tag.name, rec['full_path'],
                       cfg['CLOUDCONNECTOR_UPLOAD_FOLDER'] + '/' +
                       rec['full_path'])
