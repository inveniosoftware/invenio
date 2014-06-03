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

""" Configuration for all cloud services and general cloudutils config."""

# General configuration
CFG_CLOUD_UTILS_ROWS_PER_PAGE = 10

CFG_SERVICE_PRETTY_NAME = { 'dropbox': "Dropbox", 
                            'google_drive': "Google Drive",
                            'skydrive': "SkyDrive"
                           }

CFG_CLOUD_UTILS_ENABLED_SERVICES = ['dropbox', 'google_drive', 'skydrive']

# Dropbox configuration
CFG_DROPBOX_KEY = "123"
CFG_DROPBOX_SECRET = "123"
CFG_DROPBOX_ACCESS_TYPE = "app_folder"
CFG_DROPBOX_ROOT = "/"
CFG_DROPBOX_CSRF_TOKEN = "dropbox_auth_csrf_token"



# Google drive configuration
CFG_GOOGLE_DRIVE_CLIENT_ID = "123"
CFG_GOOGLE_DRIVE_CLIENT_SECRET = "123" 
CFG_GOOGLE_DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"
CFG_GOOGLE_DRIVE_ROOT = "invenio"


# SkyDrive configuration
CFG_SKYDRIVE_CLIENT_ID = "123"
CFG_SKYDRIVE_CLIENT_SECRET = "123"
CFG_SKYDRIVE_SCOPE = ["wl.skydrive_update", "wl.offline_access"]
CFG_SKYDRIVE_ROOT = "invenio"