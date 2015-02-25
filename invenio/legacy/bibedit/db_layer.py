# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2014 CERN.
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

# pylint: disable=C0103
"""BibEdit Database Layer."""

__revision__ = "$Id$"

try:
    import cPickle as Pickle
except ImportError:
    import Pickle
import zlib

from datetime import datetime, timedelta

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
    if sql_res[0][0] is None:
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
    res = run_sql("""SELECT  changeset_xml, id_bibrec from bibHOLDINGPEN WHERE
                      changeset_id=%s""", (changeId,))
    if res:
        try:
            changeset_xml = zlib.decompress(res[0][0])
            return changeset_xml, res[0][1]
        except zlib.error:
            # Legacy: the xml can be in TEXT format, leave it unchanged
            pass
        return res[0]

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


# Cache Related functions

def cache_exists(recid, uid):
    """Check if the BibEdit cache file exists."""
    r = run_sql("""SELECT 1 FROM bibEDITCACHE
                   WHERE id_bibrec = %s AND uid = %s""", (recid, uid))
    return bool(r)


def cache_active(recid, uid):
    """Check if the BibEdit cache is active (an editor is opened)."""
    r = run_sql("""SELECT 1 FROM bibEDITCACHE
                   WHERE id_bibrec = %s AND uid = %s
                   AND is_active = 1""", (recid, uid))
    return bool(r)


def deactivate_cache(recid, uid):
    """Mark BibEdit cache as non active."""
    return run_sql("""UPDATE bibEDITCACHE SET is_active = 0
                      WHERE id_bibrec = %s AND uid = %s""", (recid, uid))


def update_cache_post_date(recid, uid):
    """Touch a BibEdit cache file. This should be used to indicate that the
    user has again accessed the record, so that locking will work correctly.

    """
    run_sql("""UPDATE bibEDITCACHE SET post_date = NOW(), is_active = 1
               WHERE id_bibrec = %s AND uid = %s""", (recid, uid))

def get_cache(recid, uid):
    """Return a BibEdit cache object from the database."""
    r = run_sql("""SELECT data FROM bibEDITCACHE
                   WHERE id_bibrec = %s AND uid = %s""", (recid, uid))
    if r:
        return Pickle.loads(r[0][0])

def update_cache(recid, uid, data):
    data_str = Pickle.dumps(data)
    run_sql("""INSERT INTO bibEDITCACHE (id_bibrec, uid, data, post_date)
            VALUES (%s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE data = %s, post_date = NOW(), is_active = 1""",
            (recid, uid, data_str, data_str))

def get_cache_post_date(recid, uid):
    r = run_sql("""SELECT post_date FROM bibEDITCACHE
                   WHERE id_bibrec = %s AND uid = %s""", (recid, uid))
    if r:
        return r[0][0]

def delete_cache(recid, uid):
    run_sql("""DELETE FROM bibEDITCACHE
               WHERE id_bibrec = %s AND uid = %s""", (recid, uid))

def uids_with_active_caches(recid):
    """Return list of uids with active caches for record RECID. Active caches
    are caches that have been modified a number of seconds ago that is less than
    the one given by CFG_BIBEDIT_TIMEOUT.

    """
    from invenio.config import CFG_BIBEDIT_TIMEOUT
    datecut = datetime.now() - timedelta(seconds=CFG_BIBEDIT_TIMEOUT)
    rows = run_sql("""SELECT uid FROM bibEDITCACHE
                   WHERE id_bibrec = %s AND post_date > %s""",
                   (recid, datecut))
    return [int(row[0]) for row in rows]

# End of cache related functions
