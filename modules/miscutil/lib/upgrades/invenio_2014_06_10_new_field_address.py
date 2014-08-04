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

from logging import warn
from invenio.dbquery import run_sql

depends_on = ['invenio_release_1_1_0']


def info():
    return "New address field."


def do_upgrade():
    pass


def do_upgrade_atlantis():
    field_id = run_sql(
        """INSERT INTO field SET name='address', code='address')"""
    )
    tag_371x_id = run_sql(
        """INSERT INTO tag SET name='address', value='371__%%')"""
    )
    tag_110x_id = run_sql(
        """INSERT INTO tag SET name='110__(any)', value='110__%%')"""
    )
    tag_410g_id = run_sql(
        """INSERT INTO tag SET name='410__g', value='410__g')"""
    )

    query_410a_id = run_sql(
        """SELECT id FROM tag WHERE value='410__a')"""
    )
    if query_410a_id:
        tag_410a_id = query_410a_id[0][0]
    else:
        warn("Creating the tag '410__a', which doesn't exist")
        tag_410a_id = run_sql(
            """INSERT INTO tag SET name='410__a', value='410__a')"""
        )

    run_sql(
        """INSERT INTO field_tag VALUES (%s, %s, 50)""",
        (field_id, tag_371x_id)
    )
    run_sql(
        """INSERT INTO field_tag VALUES (%s, %s, 50)""",
        (field_id, tag_110x_id)
    )
    run_sql(
        """INSERT INTO field_tag VALUES (%s, %s, 50)""",
        (field_id, tag_410a_id)
    )
    run_sql(
        """INSERT INTO field_tag VALUES (%s, %s, 50)""",
        (field_id, tag_410g_id)
    )


def estimate():
    return 1


def pre_upgrade():
    pass


def post_upgrade():
    pass
