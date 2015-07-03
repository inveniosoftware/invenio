# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2014, 2015 CERN.
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

"""Utility functions for message module."""

from invenio.base.globals import cfg
from invenio.ext.login import UserInfo
from invenio.modules.access.control import acc_get_role_id, \
    acc_is_user_in_role


def is_no_quota_user(uid):
    """Return True if the user belongs to any of the no_quota roles."""
    no_quota_role_ids = [acc_get_role_id(role) for role in
                         cfg['CFG_WEBMESSAGE_ROLES_WITHOUT_QUOTA']]
    user_info = UserInfo(uid)
    for role_id in no_quota_role_ids:
        if acc_is_user_in_role(user_info, role_id):
            return True
    return False
