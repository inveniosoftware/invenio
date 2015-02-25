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

from invenio.legacy.dbquery import run_sql
from invenio.modules.upgrader.api import op


depends_on = [u'oauth2server_2014_02_17_initial']


def info():
    return "Encrypt access and refresh tokens in oauth2TOKEN table."


def do_upgrade():
    """Implement your upgrades here."""
    from invenio.config import SECRET_KEY
    from sqlalchemy_utils.types.encrypted import AesEngine
    engine = AesEngine()
    engine._update_key(SECRET_KEY)

    for row in run_sql(
            "SELECT id, access_token, refresh_token FROM oauth2TOKEN"):
        run_sql(
            "UPDATE oauth2TOKEN SET access_token=%s, "
            "refresh_token=%s WHERE id=%s",
            (engine.encrypt(row[1]),
             engine.encrypt(row[2]) if row[2] else None,
             row[0]))


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    if op.has_table('oauth2TOKEN'):
        return run_sql(
            "SELECT COUNT(id) AS ids FROM oauth2TOKEN"
        )[0][0]
    return 1
