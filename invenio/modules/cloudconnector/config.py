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

"""Configuration for all cloud services and general cloudutils config."""

from __future__ import unicode_literals

from invenio.base.config import CFG_SITE_NAME

from werkzeug import secure_filename

# General configuration
CLOUDCONNECTOR_ROWS_PER_PAGE = 10

CLOUDCONNECTOR_SERVICE_NAME_MAPPING = {
    'dropbox': "Dropbox",
    'google_drive': "Google Drive",
    'onedrive': "OneDrive",
}

CLOUDCONNECTOR_UPLOAD_FOLDER = secure_filename(CFG_SITE_NAME)

# OneDrive configuration
CFG_ONEDRIVE_CLIENT_ID = ""
CFG_ONEDRIVE_CLIENT_SECRET = ""
CFG_ONEDRIVE_SCOPE = ["wl.skydrive", "wl.skydrive_update", "wl.offline_access"]
CFG_ONEDRIVE_ROOT = secure_filename(CFG_SITE_NAME)
