## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

# pylint: disable=C0103
"""BibEdit Database Layer."""

__revision__ = "$Id$"

from invenio.legacy.dbquery import run_sql

def get_name_tags_all():
    """Return a dictionary of all MARC tag's textual names."""
    result = run_sql("SELECT name, value FROM tag")

    # Collect names in a dictionary with field codes as keys.
    nametags = {}
    for el in result:
        nametags[el[1]] = el[0]

    return nametags

def get_bibupload_task_opts(task_ids):
    """Return a list with all set options for list of task IDs TASK_IDS."""
    res = []
    for task_id in task_ids:
        res.append(run_sql("SELECT arguments FROM schTASK WHERE id=%s",
                           (task_id, )))
    return res

def get_marcxml_of_record_revision(recid, job_date):
    """Return MARCXML string of record revision specified by RECID and JOB_DATE.

    """
    return run_sql("""SELECT marcxml FROM hstRECORD
                       WHERE id_bibrec=%s AND job_date=%s""",
                   (recid, job_date))

def get_info_of_record_revision(recid, job_date):
    """Return info string regarding record revision specified by RECID and JOB_DATE.

    """
    return run_sql("""SELECT job_id, job_person, job_details FROM hstRECORD
                       WHERE id_bibrec=%s AND job_date=%s""",
                   (recid, job_date))

def get_record_revisions(recid):
    """Return dates for all known revisions of record RECID.
      returns a list of tuples (record_id, revision_date)
    """
    return run_sql("""SELECT id_bibrec,
                             DATE_FORMAT(job_date, '%%Y%%m%%d%%H%%i%%s')
                        FROM hstRECORD WHERE id_bibrec=%s
                    ORDER BY job_date DESC""", (recid, ))

def get_record_last_modification_date(recid):
    """Return last modification date, as timetuple, of record RECID."""
    sql_res = run_sql('SELECT max(job_date) FROM  hstRECORD WHERE id_bibrec=%s',
                      (recid, ))
    if sql_res[0][0] == None:
        return None
    else:
        return sql_res[0][0].timetuple()

def reserve_record_id():
    """Reserve a new record ID in the bibrec table."""
    return run_sql("""INSERT INTO bibrec (creation_date, modification_date)
                       VALUES (NOW(), NOW())""")

def get_related_hp_changesets(recId):
    """
        A function returning the changesets saved in the Holding Pen, related
        to the given record.
    """
    return run_sql("""SELECT changeset_id, changeset_date FROM bibHOLDINGPEN
                      WHERE id_bibrec=%s ORDER BY changeset_date""", (recId, ))

def get_hp_update_xml(changeId):
    """
    Get the MARC XML of the Holding Pen update
    """
    return run_sql("""SELECT  changeset_xml, id_bibrec from bibHOLDINGPEN WHERE
                      changeset_id=%s""", (str(changeId),))[0]

def delete_hp_change(changeId):
    """
    Delete a change of a given number
    """
    return run_sql("""DELETE from bibHOLDINGPEN where changeset_id=%s""",
                   (str(changeId), ))

def delete_related_holdingpen_changes(recId):
    """
    A function removing all the Holding Pen changes related to a given record
    """
    return run_sql("""DELETE FROM bibHOLDINGPEN WHERE id_bibrec=%s""",
                   (recId, ))

def get_record_revision_author(recid, td):
    """
    Returns the author of a specific record revision
    """
    # obtaining job date from the recvision identifier

    datestring = "%04i-%02i-%02i %02i:%02i:%02i" % (td.tm_year, td.tm_mon,
                                                    td.tm_mday, td.tm_hour,
                                                    td.tm_min, td.tm_sec)

    result = run_sql("""SELECT job_person from hstRECORD where id_bibrec=%s
                        AND job_date=%s""", (recid, datestring))
    if result != ():
        return result[0]
    else:
        return ""
