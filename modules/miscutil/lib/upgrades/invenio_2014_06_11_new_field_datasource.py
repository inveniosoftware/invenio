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

from invenio.dbquery import run_sql

depends_on = ['invenio_release_1_1_0']


def info():
    return "New datasource field."


def do_upgrade():
    """ Perform upgrade """
    pass


def do_upgrade_atlantis():
    """ Perform upgrade """
    field_id = run_sql(
        """INSERT INTO field SET name='data source', code='datasource'"""
    )
    tag_id = run_sql(
        """INSERT INTO tag SET name='data source', value='786__w'"""
    )
    run_sql(
        """INSERT INTO field_tag VALUES (%s, %s, 10)""",
        (field_id, tag_id)
    )


def estimate():
    """ Return estimate of upgrade time in seconds """
    return 1
