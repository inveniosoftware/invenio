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
"""CDS Invenio BibEdit utilities.

Utilities are support functions (i.e., those that are not called directly
by the web interface), that might be imported by other modules or that is called
by both the web and CLI interfaces.

"""

__revision__ = "$Id$"

import commands
import cPickle
import difflib
import marshal
import os
import re
import time
import zlib

from invenio.bibedit_config import CFG_BIBEDIT_TMPFILENAMEPREFIX
from invenio.bibrecord import create_record, create_records, \
    record_get_field_value, record_has_field, record_xml_output
from invenio.bibtask import task_low_level_submission
from invenio.config import CFG_BINDIR, CFG_BIBEDIT_LOCKLEVEL, \
    CFG_BIBEDIT_TIMEOUT, CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG as OAIID_TAG, \
    CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG as SYSNO_TAG, CFG_TMPDIR
from invenio.dateutils import convert_datetext_to_dategui
from invenio.bibedit_dblayer import get_bibupload_task_opts, \
    get_marcxml_of_record_revision, get_record_revisions
from invenio.search_engine import get_fieldvalues, print_record

# Precompile regexp:
re_file_option = re.compile(r'^/')
re_filename_suffix = re.compile('_(\d+)\.xml$')
re_revid_split = re.compile('^(\d+)\.(\d{14})$')
re_revdate_split = re.compile('^(\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)')
re_taskid = re.compile('ID="(\d+)"')

# Operations on the BibEdit cache file
def get_file_path(recid):
    """Return the file path of the BibEdit cache."""
    return '%s/%s_%s' % (CFG_TMPDIR, CFG_BIBEDIT_TMPFILENAMEPREFIX, recid)

def get_tmp_record(recid):
    """Return the BibEdit cache (no questions asked). Unsafe, use get_record."""
    file_path = file_path = '%s.tmp' % get_file_path(recid)
    file_temp = open(file_path)
    [uid, record] = cPickle.load(file_temp)
    file_temp.close()
    return uid, record

def get_record(recid, uid):
    """Conditionally create and/or return the record from the BibEdit cache.

    Create the BibEdit cache if it doesn't exist or if it exists and belongs to
    another user, but is outdated. Then return the record.
    If it exists and belongs to the requesting uid, just return it.
    If it exists, but belongs to another user and is not outdated, return an
    empty dictionary.

    """
    file_path = get_file_path(recid)

    if os.path.isfile('%s.tmp' % file_path):
        (tmp_record_uid, tmp_record) = get_tmp_record(recid)
        if tmp_record_uid != uid:
            time_tmp_file = os.path.getmtime('%s.tmp' % file_path)
            time_out_file = int(time.time()) - CFG_BIBEDIT_TIMEOUT
            if time_tmp_file < time_out_file :
                os.system('rm %s.tmp' % file_path)
                tmp_record = create_record(print_record(recid, 'xm'))[0]
                save_temp_record(tmp_record, uid, '%s.tmp' % file_path)
            else:
                tmp_record = {}

    else:
        tmp_record = create_record(print_record(recid, 'xm'))[0]
        save_temp_record(tmp_record, uid, '%s.tmp' % file_path)

    return tmp_record

def save_temp_record(record, uid, file_path):
    """Save record in BibEdit cache."""
    file_temp = open(file_path, 'w')
    cPickle.dump([uid, record], file_temp)
    file_temp.close()

def save_xml_record(recid, xml_record=''):
    """Create XML record file from BibEdit cache. Then pass it to BibUpload.

    Optionally pass XML record directly to function.

    """
    file_path = get_file_path(recid)
    os.system('rm -f %s.xml' % file_path)
    file_temp = open('%s.xml' % file_path, 'w')
    if xml_record:
        file_temp.write(xml_record)
    else:
        file_temp.write(record_xml_output(get_tmp_record(recid)[1]))
        os.system('rm %s.tmp' % file_path)
    file_temp.close()
    task_low_level_submission('bibupload', 'bibedit', '-P', '5', '-r',
                              '%s.xml' % file_path)


# Locking
def record_in_use_p(recid):
    """Check if a record is currently being edited."""
    file_path = '%s.tmp' % get_file_path(recid)
    if os.path.isfile(file_path):
        time_tmp_file = os.path.getmtime(file_path)
        time_out_file = int(time.time()) - CFG_BIBEDIT_TIMEOUT
        if time_tmp_file > time_out_file :
            return True
        os.system('rm -f %s' % file_path)
    return False

def record_locked_p(recid):
    """Check if BibUpload queue state locks record.

    Check if record should be locked for editing because of the current state
    of the BibUpload queue. The level of checking is based on
    CFG_BIBEDIT_LOCKLEVEL.

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
    """Get and return list of all BibUpload task IDs.

    Ignore tasks submitted by user bibreformat.

    """
    cmd = '%s/bibsched status -t bibupload' % CFG_BINDIR
    err, out = commands.getstatusoutput(cmd)
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
    """Get path to all files scheduled for upload."""
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
                record, all_good, errs = records[i]
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


# JSON
def json_unicode_to_utf8(data):
    """Change all strings in a JSON structure to UTF-8."""
    if type(data) == unicode:
        return data.encode('utf-8')
    elif type(data) == dict:
        newdict = {}
        for key in data:
            newdict[json_unicode_to_utf8(key)] = json_unicode_to_utf8(data[key])
        return newdict
    elif type(data) == list:
        return [json_unicode_to_utf8(elem) for elem in data]
    else:
        return data


# History/revisions
def get_record_revision_ids(recid):
    """Return list of all record revision IDs.

    Return revision IDs in chronologically decreasing order (latest first).

    """
    res = []
    tmp_res =  get_record_revisions(recid)
    for row in tmp_res:
        res.append('%s.%s' % (row[0], row[1]))
    return res

def get_marcxml_of_revision_id(revid):
    """Return MARCXML string of revision.

    Return empty string if revision does not exist. revid should be a string.

    """
    res = ''
    recid, job_date = split_revid(revid, 'datetext')
    tmp_res = get_marcxml_of_record_revision(recid, job_date)
    if tmp_res:
        for row in tmp_res:
            res += zlib.decompress(row[0]) + '\n'
    return res

def revision_format_valid_p(revid):
    """Predicate to test validity of revision ID format (=RECID.REVDATE)."""
    if re_revid_split.match(revid):
        return True
    return False

def split_revid(revid, dateformat=''):
    """Split revid and return tuple (recid, revdate).

    Optional dateformat can be datetext or dategui.

    """
    recid, revdate = re_revid_split.search(revid).groups()
    if dateformat:
        datetext = '%s-%s-%s %s:%s:%s' % re_revdate_split.search(
            revdate).groups()
        if dateformat == 'datetext':
            revdate = datetext
        elif dateformat == 'dategui':
            revdate = convert_datetext_to_dategui(datetext, secs=True)
    return recid, revdate

def get_xml_comparison(header1, header2, xml1, xml2):
    """Return diff of two MARCXML records."""
    return ''.join(difflib.unified_diff(xml1.splitlines(1),
        xml2.splitlines(1), header1, header2))
