## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

# pylint: disable-msg=C0103
"""CDS Invenio BibEdit Database Layer."""

__revision__ = "$Id$"

from invenio.dbquery import run_sql

def get_name_tags_all():
    """This function returns a dictionary of all MARC tag's textual names."""
    result = run_sql("SELECT name, value FROM tag")

    # Collect names in a dictionary with field codes as keys.
    nametags = {}
    for el in result:
        nametags[el[1]] = el[0]

    return nametags

def get_bibupload_task_opts(task_ids):
    """Returns a list with all options for a given list of task IDs."""
    res = []
    for task_id in task_ids:
        res.append(run_sql("SELECT arguments FROM schTASK WHERE id=%s" %
                           task_id))
    return res

def get_marcxml_of_record_revision(recid, job_date):
    """Return MARCXML string of revision.

    Revision specified by recid and job date.

    """
    return run_sql("""SELECT marcxml FROM hstRECORD
                       WHERE id_bibrec=%s AND job_date=%s""",
                   (recid, job_date))

def get_record_revisions(recid):
    """Return dates for all known revisions of the given record."""
    return run_sql("""SELECT id_bibrec,
                             DATE_FORMAT(job_date, '%%Y%%m%%d%%H%%i%%s')
                        FROM hstRECORD WHERE id_bibrec=%s
                    ORDER BY job_date DESC""",
                   (str(recid),))
