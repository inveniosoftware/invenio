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

depends_on = ['invenio_2014_08_13_tag_recjsonvalue']


def info():
    """Upgrade recipe information."""
    return "tag.recjson_value NOT NULL"


def do_upgrade():
    """Upgrade recipe procedure."""
    run_sql("UPDATE tag SET recjson_value='' WHERE recjson_value IS NULL")
    run_sql("""ALTER TABLE tag CHANGE COLUMN recjson_value
               recjson_value text NOT NULL""")


def estimate():
    """Upgrade recipe time estimate."""
    return 1
