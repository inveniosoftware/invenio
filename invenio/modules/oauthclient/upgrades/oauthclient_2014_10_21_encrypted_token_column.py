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

from invenio.legacy.dbquery import run_sql


depends_on = [u'oauthclient_2014_08_25_extra_data_nullable']


def info():
    return "Encrypt access tokens in remoteTOKEN table."


def do_upgrade():
    """Implement your upgrades here."""
    from invenio.config import SECRET_KEY
    from sqlalchemy_utils.types.encrypted import AesEngine
    engine = AesEngine(SECRET_KEY)
    for row in run_sql(
            "SELECT id_remote_account, token_type, access_token "
            "FROM remoteTOKEN"):
        run_sql(
            "UPDATE remoteTOKEN SET access_token=%s "
            "WHERE id_remote_account=%s AND "
            "token_type=%s", (engine.encrypt(row[2]), row[0], row[1]))


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return run_sql(
        "SELECT COUNT(*) AS ids FROM remoteTOKEN"
    )[0][0]
