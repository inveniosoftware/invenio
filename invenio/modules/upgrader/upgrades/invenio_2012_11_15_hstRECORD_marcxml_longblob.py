# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012 CERN.
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

import warnings
from invenio.legacy.dbquery import run_sql

depends_on = ['invenio_release_1_1_0']

def info():
    return "Increase of hstRECORD.marcxml storage to longblob"

def do_upgrade():
    create_statement = run_sql('SHOW CREATE TABLE hstRECORD')[0][1]
    if '`marcxml` longblob' not in create_statement:
        run_sql("ALTER TABLE hstRECORD CHANGE marcxml marcxml longblob NOT NULL")

def estimate():
    """  Estimate running time of upgrade in seconds (optional). """
    count_rows = run_sql("SELECT COUNT(*) FROM hstRECORD")[0][0]
    return count_rows / 20

def pre_upgrade():
    pass

def post_upgrade():
    """Check for potentially invalid revisions"""
    res = run_sql("""SELECT DISTINCT(id_bibrec) FROM hstRECORD
                     WHERE CHAR_LENGTH(marcxml) =  %s""", [2**16-1])
    if res:
        warnings.warn("You have %s records with potentially corrupt history revisions!" % \
                      len(res))
        warnings.warn("You may want to run the following:")
        for row in res:
            warnings.warn("bibedit --fix-revisions %s" % row[0])
