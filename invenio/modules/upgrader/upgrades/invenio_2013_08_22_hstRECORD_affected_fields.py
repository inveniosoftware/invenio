# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013 CERN.
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

depends_on = ['invenio_2012_11_15_hstRECORD_marcxml_longblob']

def info():
    return "New column hstRECORD.affected_fields"

def do_upgrade():
    #first step: change the table
    create_statement = run_sql('SHOW CREATE TABLE hstRECORD')[0][1]
    if 'affected_fields' not in create_statement:
        run_sql("ALTER TABLE hstRECORD ADD COLUMN affected_fields text NOT NULL default '' AFTER job_details")
    #second step: nothing
    #we don't need to fill in the column since empty value
    #is valid and it means that all fields/tags were modified

def estimate():
    """  Estimate running time of upgrade in seconds (optional). """
    return 1

def pre_upgrade():
    pass

def post_upgrade():
    """Check for potentially invalid revisions"""
