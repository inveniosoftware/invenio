# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

CFG_PROVIDER_LIST = ['invenio.modules.pidstore.providers.datacite:DataCite',
                      'invenio.modules.pidstore.providers.local_doi:LocalDOI',
                     ]

CFG_OBJECT_TYPES = ['rec', ]

CFG_STATUS_NEW = 'N'
"""
The pid has *not* yet been registered with the service provider.
"""

CFG_STATUS_REGISTERED = 'R'
"""
The pid has been registered with the service provider.
"""

CFG_STATUS_DELETED = 'D'
"""
The pid has been deleted with the service proivider. This should
very rarely happen, and must be kept track of, as the PID should not be
reused for something else.
"""

CFG_STATUS_RESERVED = 'K'
"""
The pid has been reserved in the service provider but not yet fully
registered.
"""
