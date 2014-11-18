# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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
    return "New note field."


def do_upgrade():
    pass


def do_upgrade_atlantis():
    field_id = run_sql("""INSERT INTO field SET name='note', code='note'""")
    tag_id = run_sql("""INSERT INTO tag SET name='note', value='500__a'""")
    run_sql(
        """INSERT INTO field_tag VALUES (%s, %s, 10)""",
        (field_id, tag_id)
    )


def estimate():
    return 1


def pre_upgrade():
    pass


def post_upgrade():
    pass
