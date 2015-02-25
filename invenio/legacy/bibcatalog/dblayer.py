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

"""BibCatalog db layer."""

from invenio.legacy.dbquery import run_sql


def get_all_new_records(since, last_id):
    """
    Get all the newly inserted records since last run.
    """
    # Fetch all records inserted since last run
    sql = "SELECT `id`, `creation_date` FROM `bibrec` " \
        "WHERE `creation_date` >= %s " \
        "AND `id` > %s " \
        "ORDER BY `creation_date`"
    return run_sql(sql, (since.isoformat(), last_id))


def get_all_modified_records(since, last_id):
    """
    Get all the newly modified records since last run.
    """
    sql = "SELECT `id`, `modification_date` FROM `bibrec` " \
        "WHERE `modification_date` >= %s " \
        "AND `id` > %s " \
        "ORDER BY `modification_date`"
    return run_sql(sql, (since.isoformat(), last_id))


def can_launch_bibupload(taskid):
    """
    Checks if task can be launched.
    """
    if taskid == 0:
        return True

    sql = 'SELECT status FROM schTASK WHERE id = %s'
    if run_sql(sql, [str(taskid)])[0][0] != 'DONE':
        return False
    return True
