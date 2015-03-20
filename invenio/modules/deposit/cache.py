# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Implementation of allowed deposit type caching."""

from .acl import usedeposit
from .registry import deposit_types


def get_authorized_deposition_types(user_info):
    """Return a list of allowed deposition types for a certain user."""
    from invenio.modules.access.engine import acc_authorize_action

    return {
        key for key in deposit_types.mapping().keys()
        if acc_authorize_action(user_info, usedeposit.name, type=key)[0] == 0
    }
