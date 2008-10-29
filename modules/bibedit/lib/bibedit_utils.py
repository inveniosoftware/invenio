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

"""
bibedit utilities

Utilities are defined as functions that are needed by many parts of the
bibedit engine, (eg. both the editor and the history). If the engine is
split into several modules or classes, common functionality can be found here.
"""

__revision__ = "$Id$"

import commands
import cPickle
import marshal
import os
import re
import time

from invenio.bibedit_config import CFG_BIBEDIT_TMPFILENAMEPREFIX
from invenio.bibedit_dblayer import get_bibupload_task_opts
from invenio.bibrecord import create_records, record_get_field_value, \
    record_has_field
from invenio.config import CFG_BINDIR, CFG_BIBEDIT_LOCKLEVEL, \
    CFG_BIBEDIT_TIMEOUT, CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG as OAIID_TAG, \
    CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG as SYSNO_TAG, CFG_TMPDIR
from invenio.search_engine import get_fieldvalues

# Precompile regexp:
re_taskid = re.compile('ID="(\d+)"')
re_file_option = re.compile(r'^/')
re_filename_suffix = re.compile('_(\d+)\.xml$')
re_date = re.compile('\.(\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)')

def get_file_path(recid):
    """Return the file path of a records tmp file."""
    return "%s/%s_%s" % (CFG_TMPDIR, CFG_BIBEDIT_TMPFILENAMEPREFIX, recid)

def record_in_use_p(recid):
    """Check if a record is currently being editing."""
    file_path = '%s.tmp' % get_file_path(recid)
    if os.path.isfile(file_path):
        time_tmp_file = os.path.getmtime(file_path)
        time_out_file = int(time.time()) - CFG_BIBEDIT_TIMEOUT
        if time_tmp_file > time_out_file :
            return True
        os.system("rm -f %s" % file_path)
    return False

def get_tmp_record(recid):
    """Loads record dict from a temp file."""
    file_path = file_path = '%s.tmp' % get_file_path(recid)
    file_temp = open(file_path)
    [uid, record] = cPickle.load(file_temp)
    file_temp.close()
    return (uid, record)

def get_tmp_file_owner(recid):
    """Check who is editing a record."""
    file_temp = open('%s.tmp' % get_file_path(recid))
    uid = cPickle.load(file_temp)[0]
    file_temp.close()
    return int(uid)

def record_locked_p(recid):
    """
    Check if record is locked for editing, because of unfinished bibupload
    tasks. The level of checking is based on CFG_BIBEDIT_LOCKLEVEL.
    """
    # Check for *any* scheduled bibupload tasks.
    if CFG_BIBEDIT_LOCKLEVEL == 2:
        return get_bibupload_task_ids()

    filenames = get_bibupload_filenames()
    # Check for match between name of XML-files and record.
    # Assumes that filename ends with _<recid>.xml.
    if CFG_BIBEDIT_LOCKLEVEL == 1:
        recids = []
        for filename in filenames:
            filename_suffix = re_filename_suffix.search(filename)
            if filename_suffix:
                recids.append(int(filename_suffix.group(1)))
        return recid in recids

    # Check for match between content of files and record.
    if CFG_BIBEDIT_LOCKLEVEL == 3:
        while True:
            lock = record_in_files_p(recid, filenames)
            # Check if any new files were added while we were searching
            if not lock:
                filenames_updated = get_bibupload_filenames()
                for filename in filenames_updated:
                    if not filename in filenames:
                        break
                else:
                    return lock
            else:
                return lock

def get_bibupload_task_ids():
    """
    Get and return list of all bibupload task IDs,
    except by user bibreformat.
    """
    cmd = ('%s/bibsched status -t bibupload') % CFG_BINDIR
    (err, out) = commands.getstatusoutput(cmd)
    if err:
        raise StandardError, '%s: %s' % (err, out)
    tasks = out.splitlines()[3:-1]
    res = []
    for task in tasks:
        if task.find('USER="bibreformat"') == -1:
            matchobj = re_taskid.search(task)
            if matchobj:
                res.append(matchobj.group(1))
    return res

def get_bibupload_filenames():
    """
    Get path to all files scheduled for bibupload.
    """
    task_ids = get_bibupload_task_ids()
    filenames = []
    tasks_opts = get_bibupload_task_opts(task_ids)
    for task_opts in tasks_opts:
        if task_opts:
            record_options = marshal.loads(task_opts[0][0])
            for option in record_options[1:]:
                if re_file_option.search(option):
                    filenames.append(option)
    return filenames

def record_in_files_p(recid, filenames):
    """Search XML files for given record."""
    # Get id tags of record in question
    rec_oaiid = rec_sysno = -1
    rec_oaiid_tag = get_fieldvalues(recid, OAIID_TAG)
    if rec_oaiid_tag:
        rec_oaiid = rec_oaiid_tag[0]
    rec_sysno_tag = get_fieldvalues(recid, SYSNO_TAG)
    if rec_sysno_tag:
        rec_sysno = rec_sysno_tag[0]

    # For each record in each file, compare ids and abort if match is found
    for filename in filenames:
        try:
            file_ = open(filename)
            records = create_records(file_.read(), 0, 0)
            for i in range(0, len(records)):
                (record, all_good, errs) = records[i]
                if record and all_good:
                    if record_has_id_p(record, recid, rec_oaiid, rec_sysno):
                        return True
            file_.close()
        except IOError:
            continue
    return False

def record_has_id_p(record, recid, rec_oaiid, rec_sysno):
    """Check if record matches any of the given IDs."""
    if record_has_field(record, '001'):
        if (record_get_field_value(record, '001', '%', '%')
            == str(recid)):
            return True
    if record_has_field(record, OAIID_TAG[0:3]):
        if (record_get_field_value(
                record, OAIID_TAG[0:3], OAIID_TAG[3],
                OAIID_TAG[4], OAIID_TAG[5]) == rec_oaiid):
            return True
    if record_has_field(record, SYSNO_TAG[0:3]):
        if (record_get_field_value(
                record, SYSNO_TAG[0:3], SYSNO_TAG[3],
                SYSNO_TAG[4], SYSNO_TAG[5]) == rec_sysno):
            return True
    return False
