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

"""OAI harvest config."""


from __future__ import unicode_literals

import os

from invenio.base.config import CFG_DATADIR


OAIHARVESTER_DEFAULT_NAMESPACE_MAP = {
    None: "http://www.openarchives.org/OAI/2.0/",
}
"""The default namespace used when handling OAI-PMH results."""

OAIHARVESTER_STORAGEDIR = os.path.join(CFG_DATADIR, "oaiharvester", "storage")
"""Path to a storage directory where the oaiharvester may put files."""
