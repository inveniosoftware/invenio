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

"""Pidstore config."""

from __future__ import unicode_literals

PIDSTORE_PROVIDERS = [
    'invenio.modules.pidstore.providers.datacite:DataCite',
    'invenio.modules.pidstore.providers.local_doi:LocalDOI',
    'invenio.modules.pidstore.providers.recid:RecordID',
]

PIDSTORE_OBJECT_TYPES = ['rec', ]
"""
Definition of supported object types
"""

PIDSTORE_DATACITE_OUTPUTFORMAT = 'dcite'
"""
Output format used to generate the DataCite
"""

PIDSTORE_DATACITE_RECORD_DOI_FIELD = 'doi'
"""
Field name in record model (JSONAlchemy)
"""

PIDSTORE_DATACITE_SITE_URL = None
"""
Site URL to use when minting records. Defaults to CFG_SITE_URL.
"""

#
# Internal configuration values. Normally you will not need to edit
# any of the configuration values below.
#
PIDSTORE_STATUS_NEW = 'N'
"""
The pid has *not* yet been registered with the service provider.
"""

PIDSTORE_STATUS_REGISTERED = 'R'
"""
The pid has been registered with the service provider.
"""

PIDSTORE_STATUS_DELETED = 'D'
"""
The pid has been deleted/inactivated with the service proivider. This should
very rarely happen, and must be kept track of, as the PID should not be
reused for something else.
"""

PIDSTORE_STATUS_RESERVED = 'K'
"""
The pid has been reserved in the service provider but not yet fully
registered.
"""
