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

"""Check if some of nicknames are not valid anymore."""

from invenio.modules.accounts.models import User


# Important: Below is only a best guess. You MUST validate which previous
# upgrade you depend on.
depends_on = [u'accounts_2014_11_07_usergroup_name_column_unique']


def info():
    """Info message."""
    return __doc__


def do_upgrade():
    """Implement your upgrades here."""
    pass


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    users = User.query.all()

    not_valid_nicknames = []
    for user in users:
        if not User.check_nickname(user.nickname):
            not_valid_nicknames.append(user)

    if len(not_valid_nicknames) > 0:
        list_users = ', '.join([u.nickname for u in not_valid_nicknames])
        raise RuntimeError(
            "These nicknames are not valid: {list_users}. "
            "Please fix them before continuing.".format(
                list_users=list_users)
        )


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    pass
