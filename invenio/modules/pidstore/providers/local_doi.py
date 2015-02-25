# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""
    invenio.modules.pid_store.providers.local_doi_provider
    ----------------------------------------------------------

"""

from invenio.base.globals import cfg

from invenio.modules.pidstore.provider import PidProvider, LocalPidProvider

class LocalDOI(LocalPidProvider):
    """
    Provider for locally unmanaged DOIs.
    """
    pid_type = 'doi'

    @classmethod
    def is_provider_for_pid(cls, pid_str):
        """
        Check if DOI is not the local datacite managed one.
        """
        return not pid_str.startswith("%s/" % cfg['CFG_DATACITE_DOI_PREFIX'])
