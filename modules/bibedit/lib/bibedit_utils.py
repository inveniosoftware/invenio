## This file is part of Invenio.
## Copyright (C) 2008, 2009, 2010, 2011 CERN.
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
"""BibEdit Utilities.

This module contains support functions (i.e., those that are not called directly
by the web interface), that might be imported by other modules or that is called
by both the web and CLI interfaces.

"""

__revision__ = "$Id$"

import cPickle
import difflib
import fnmatch
import marshal
import os
import re
import time
import zlib
from datetime import datetime

from invenio.bibedit_config import CFG_BIBEDIT_FILENAME, \
    CFG_BIBEDIT_RECORD_TEMPLATES_PATH, CFG_BIBEDIT_TO_MERGE_SUFFIX, \
    CFG_BIBEDIT_FIELD_TEMPLATES_PATH
from invenio.bibedit_dblayer import get_record_last_modification_date, \
    delete_hp_change
from invenio.bibrecord import create_record, create_records, \
    record_get_field_value, record_has_field, record_xml_output, \
    record_strip_empty_fields, record_strip_empty_volatile_subfields, \
    record_order_subfields, record_get_field_instances, \
    record_add_field, field_get_subfield_codes, field_add_subfield, \
    field_get_subfield_values

from invenio.bibtask import task_low_level_submission
from invenio.config import CFG_BIBEDIT_LOCKLEVEL, \
    CFG_BIBEDIT_TIMEOUT, CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG as OAIID_TAG, \
    CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG as SYSNO_TAG, CFG_TMPSHAREDDIR, \
    CFG_BIBEDIT_QUEUE_CHECK_METHOD, \
    CFG_BIBEDIT_EXTEND_RECORD_WITH_COLLECTION_TEMPLATE
from invenio.dateutils import convert_datetext_to_dategui
from invenio.textutils import wash_for_xml
from invenio.bibedit_dblayer import get_bibupload_task_opts, \
    get_marcxml_of_record_revision, get_record_revisions, \
    get_info_of_record_revision
from invenio.search_engine import print_record, record_exists, get_colID, \
     guess_primary_collection_of_a_record, get_record, \
     get_all_collections_of_a_record
from invenio.search_engine_utils import get_fieldvalues
from invenio.webuser import get_user_info
from invenio.dbquery import run_sql
from invenio.websearchadminlib import get_detailed_page_tabs
from invenio.access_control_engine import acc_authorize_action

# Precompile regexp:
re_file_option = re.compile(r'^%s' % CFG_TMPSHAREDDIR)
re_xmlfilename_suffix = re.compile('_(\d+)_\d+\.xml$')
re_revid_split = re.compile('^(\d+)\.(\d{14})$')
re_revdate_split = re.compile('^(\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)')
re_taskid = re.compile('ID="(\d+)"')
re_tmpl_name = re.compile('<!-- BibEdit-Template-Name: (.*) -->')
re_tmpl_description = re.compile('<!-- BibEdit-Template-Description: (.*) -->')
re_ftmpl_name = re.compile('<!-- BibEdit-Field-Template-Name: (.*) -->')
re_ftmpl_description = re.compile('<!-- BibEdit-Field-Template-Description: (.*) -->')


# Authorization

def user_can_edit_record_collection(req, recid):
    """ Check if user has authorization to modify a collection
    the recid belongs to
    """
    record_collections = get_all_collections_of_a_record(recid)
    if not record_collections:
        # Check if user has access to all collections
        auth_code, auth_message = acc_authorize_action(req, 'runbibedit',
                                                       collection='')
        if auth_code == 0:
            return True
    else:
        for collection in record_collections:
            auth_code, auth_message = acc_authorize_action(req, 'runbibedit',
                                                           collection=collection)
            if auth_code == 0:
                return True
    return False

# Helper functions

def assert_undo_redo_lists_correctness(undo_list, redo_list):
    for undoItem in undo_list:
        assert undoItem != None;
    for redoItem in redo_list:
        assert redoItem != None;

def record_find_matching_fields(key, rec, tag="", ind1=" ", ind2=" ", \
                                exact_match=False):
    """
    This utility function will look for any fieldvalues containing or equal
    to, if exact match is wanted, given keyword string. The found fields will be
    returned as a list of field instances per tag. The fields to search can be
    narrowed down to tag/indicator level.

    @param key: keyword to search for
    @type key: string

    @param rec: a record structure as returned by bibrecord.create_record()
    @type rec: dict

    @param tag: a 3 characters long string
    @type tag: string

    @param ind1: a 1 character long string
    @type ind1: string

    @param ind2: a 1 character long string
    @type ind2: string

    @return: a list of found fields in a tuple per tag: (tag, field_instances) where
        field_instances is a list of (Subfields, ind1, ind2, value, field_position_global)
        and subfields is list of (code, value)
    @rtype: list
    """
    if not tag:
        all_field_instances = rec.items()
    else:
        all_field_instances = [(tag, record_get_field_instances(rec, tag, ind1, ind2))]
    matching_field_instances = []
    for current_tag, field_instances in all_field_instances:
        found_fields = []
        for field_instance in field_instances:
            # Get values to match: controlfield_value + subfield values
            values_to_match = [field_instance[3]] + \
                              [val for code, val in field_instance[0]]
            if exact_match and key in values_to_match:
                found_fields.append(field_instance)
            else:
                for value in values_to_match:
                    if value.find(key) > -1:
                        found_fields.append(field_instance)
                        break
        if len(found_fields) > 0:
            matching_field_instances.append((current_tag, found_fields))
    return matching_field_instances

# Operations on the BibEdit cache file
def cache_exists(recid, uid):
    """Check if the BibEdit cache file exists."""
    return os.path.isfile('%s.tmp' % _get_file_path(recid, uid))

def get_cache_mtime(recid, uid):
    """Get the last modified time of the BibEdit cache file. Check that the
    cache exists before calling this function.

    """
    try:
        return int(os.path.getmtime('%s.tmp' % _get_file_path(recid, uid)))
    except OSError:
        pass

def cache_expired(recid, uid):
    """Has it been longer than the number of seconds given by
    CFG_BIBEDIT_TIMEOUT since last cache update? Check that the
    cache exists before calling this function.

    """
    return get_cache_mtime(recid, uid) < int(time.time()) - CFG_BIBEDIT_TIMEOUT

def create_cache_file(recid, uid, record='', cache_dirty=False, pending_changes=[], disabled_hp_changes = {}, undo_list = [], redo_list=[]):
    """Create a BibEdit cache file, and return revision and record. This will
    overwrite any existing cache the user has for this record.
    datetime.

    """
    if not record:
        record = get_bibrecord(recid)
        # Order subfields alphabetically after loading the record
        record_order_subfields(record)
        if not record:
            return

    file_path = '%s.tmp' % _get_file_path(recid, uid)
    record_revision = get_record_last_modification_date(recid)
    if record_revision == None:
        record_revision = datetime.now().timetuple()

    cache_file = open(file_path, 'w')
    assert_undo_redo_lists_correctness(undo_list, redo_list);
    cPickle.dump([cache_dirty, record_revision, record, pending_changes, disabled_hp_changes, undo_list, redo_list], cache_file)
    cache_file.close()
    return record_revision, record

def touch_cache_file(recid, uid):
    """Touch a BibEdit cache file. This should be used to indicate that the
    user has again accessed the record, so that locking will work correctly.

    """
    if cache_exists(recid, uid):
        os.system('touch %s.tmp' % _get_file_path(recid, uid))

def get_bibrecord(recid):
    """Return record in BibRecord wrapping."""
    if record_exists(recid):
        return create_record(print_record(recid, 'xm'))[0]

def get_cache_file_contents(recid, uid):
    """Return the contents of a BibEdit cache file."""
    cache_file = _get_cache_file(recid, uid, 'r')
    if cache_file:
        cache_dirty, record_revision, record, pending_changes, disabled_hp_changes, undo_list, redo_list = cPickle.load(cache_file)
        cache_file.close()
        assert_undo_redo_lists_correctness(undo_list, redo_list);

        return cache_dirty, record_revision, record, pending_changes, disabled_hp_changes, undo_list, redo_list

def update_cache_file_contents(recid, uid, record_revision, record, pending_changes, disabled_hp_changes, undo_list, redo_list):
    """Save updates to the record in BibEdit cache. Return file modificaton
    time.

    """
    cache_file = _get_cache_file(recid, uid, 'w')
    if cache_file:
        assert_undo_redo_lists_correctness(undo_list, redo_list);
        cPickle.dump([True, record_revision, record, pending_changes, disabled_hp_changes, undo_list, redo_list], cache_file)
        cache_file.close()
        return get_cache_mtime(recid, uid)

def delete_cache_file(recid, uid):
    """Delete a BibEdit cache file."""
    os.remove('%s.tmp' % _get_file_path(recid, uid))


def delete_disabled_changes(used_changes):
    for change_id in used_changes:
        delete_hp_change(change_id)

def save_xml_record(recid, uid, xml_record='', to_upload=True, to_merge=False):
    """Write XML record to file. Default behaviour is to read the record from
    a BibEdit cache file, filter out the unchanged volatile subfields,
    write it back to an XML file and then pass this file to BibUpload.

    @param xml_record: give XML as string in stead of reading cache file
    @param to_upload: pass the XML file to BibUpload
    @param to_merge: prepare an XML file for BibMerge to use

    """
    if not xml_record:
        # Read record from cache file.
        cache = get_cache_file_contents(recid, uid)
        if cache:
            record = cache[2]
            used_changes = cache[4]
#            record_strip_empty_fields(record) # now performed for every record after removing unfilled volatile fields
            xml_record = record_xml_output(record)
            delete_cache_file(recid, uid)
            delete_disabled_changes(used_changes)
    else:
        record = create_record(xml_record)[0]

    # clean the record from unfilled volatile fields
    record_strip_empty_volatile_subfields(record)
    record_strip_empty_fields(record)

    # order subfields alphabetically before saving the record
    record_order_subfields(record)

    xml_to_write = wash_for_xml(record_xml_output(record))

    # Write XML file.
    if not to_merge:
        file_path = '%s.xml' % _get_file_path(recid, uid)
    else:
        file_path = '%s_%s.xml' % (_get_file_path(recid, uid),
                                   CFG_BIBEDIT_TO_MERGE_SUFFIX)
    xml_file = open(file_path, 'w')
    xml_file.write(xml_to_write)
    xml_file.close()

    user_name = get_user_info(uid)[1]
    if to_upload:
        # Pass XML file to BibUpload.
        task_low_level_submission('bibupload', 'bibedit', '-P', '5', '-r',
                                  file_path, '-u', user_name)
    return True


# Security: Locking and integrity
def latest_record_revision(recid, revision_time):
    """Check if timetuple REVISION_TIME matches latest modification date."""
    latest = get_record_last_modification_date(recid)
    # this can be none if the record is new
    return (latest == None) or (revision_time == latest)

def record_locked_by_other_user(recid, uid):
    """Return true if any other user than UID has active caches for record
    RECID.

    """
    active_uids = _uids_with_active_caches(recid)
    try:
        active_uids.remove(uid)
    except ValueError:
        pass
    return bool(active_uids)

def record_locked_by_queue(recid):
    """Check if record should be locked for editing because of the current state
    of the BibUpload queue. The level of checking is based on
    CFG_BIBEDIT_LOCKLEVEL.

    """
    # Check for *any* scheduled bibupload tasks.
    if CFG_BIBEDIT_LOCKLEVEL == 2:
        return _get_bibupload_task_ids()

    filenames = _get_bibupload_filenames()
    # Check for match between name of XML-files and record.
    # Assumes that filename ends with _<recid>.xml.
    if CFG_BIBEDIT_LOCKLEVEL == 1:
        recids = []
        for filename in filenames:
            filename_suffix = re_xmlfilename_suffix.search(filename)
            if filename_suffix:
                recids.append(int(filename_suffix.group(1)))
        return recid in recids

    # Check for match between content of files and record.
    if CFG_BIBEDIT_LOCKLEVEL == 3:
        while True:
            lock = _record_in_files_p(recid, filenames)
            # Check if any new files were added while we were searching
            if not lock:
                filenames_updated = _get_bibupload_filenames()
                for filename in filenames_updated:
                    if not filename in filenames:
                        break
                else:
                    return lock
            else:
                return lock

# History/revisions

def revision_to_timestamp(td):
    """
    Converts the revision date to the timestamp
    """
    return "%04i%02i%02i%02i%02i%02i" % (td.tm_year, td.tm_mon, td.tm_mday, \
                                         td.tm_hour, td.tm_min, td.tm_sec)

def timestamp_to_revision(timestamp):
    """
    Converts the timestamp to a correct revision date
    """
    year = int(timestamp[0:4])
    month = int(timestamp[4:6])
    day = int(timestamp[6:8])
    hour = int(timestamp[8:10])
    minute = int(timestamp[10:12])
    second = int(timestamp[12:14])
    return datetime(year, month, day, hour, minute, second).timetuple()

def get_record_revision_timestamps(recid):
    """return list of timestamps describing teh revisions of a given record"""
    rev_ids = get_record_revision_ids(recid)
    result = []
    for rev_id in rev_ids:
        result.append(rev_id.split(".")[1])
    return result

def get_record_revision_ids(recid):
    """Return list of all record revision IDs.
    Return revision IDs in chronologically decreasing order (latest first).
    """
    res = []
    tmp_res =  get_record_revisions(recid)
    for row in tmp_res:
        res.append('%s.%s' % (row[0], row[1]))
    return res

def get_marcxml_of_revision(recid, revid):
    """Return MARCXML string of revision.
    Return empty string if revision does not exist. REVID should be a string.
    """
    res = ''
    tmp_res = get_marcxml_of_record_revision(recid, revid)
    if tmp_res:
        for row in tmp_res:
            res += zlib.decompress(row[0]) + '\n'
    return res;

def get_marcxml_of_revision_id(revid):
    """Return MARCXML string of revision.
    Return empty string if revision does not exist. REVID should be a string.
    """
    recid, job_date = split_revid(revid, 'datetext')
    return get_marcxml_of_revision(recid, job_date);

def get_info_of_revision_id(revid):
    """Return info string regarding revision.
    Return empty string if revision does not exist. REVID should be a string.
    """
    recid, job_date = split_revid(revid, 'datetext')
    res = ''
    tmp_res = get_info_of_record_revision(recid, job_date)
    if tmp_res:
        task_id = str(tmp_res[0][0])
        author = tmp_res[0][1]
        if not author:
            author = 'N/A'
        res += '%s%s%s' % (revid.ljust(22), task_id.ljust(15), author.ljust(15))
        job_details = tmp_res[0][2].split()
        upload_mode = job_details[0] + job_details[1][:-1]
        upload_file = job_details[2] + job_details[3][:-1]
        res += '%s %s' % (upload_mode, upload_file)
    return res

def revision_format_valid_p(revid):
    """Test validity of revision ID format (=RECID.REVDATE)."""
    if re_revid_split.match(revid):
        return True
    return False

def record_revision_exists(recid, revid):
    results = get_record_revisions(recid)
    for res in results:
        if res[1] == revid:
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

#Templates
def get_templates(templatesDir, tmpl_name, tmpl_description, extractContent = False):
    """Return list of templates [filename, name, description, content*]
       the extractContent variable indicated if the parsed content should
       be included"""
    template_fnames = fnmatch.filter(os.listdir(
            templatesDir), '*.xml')

    templates = []
    for fname in template_fnames:
        filepath = '%s%s%s' % (templatesDir, os.sep, fname)
        template_file = open(filepath,'r')
        template = template_file.read()
        template_file.close()
        fname_stripped = os.path.splitext(fname)[0]
        mo_name = tmpl_name.search(template)
        mo_description = tmpl_description.search(template)
        date_modified = time.ctime(os.path.getmtime(filepath))
        if mo_name:
            name = mo_name.group(1)
        else:
            name = fname_stripped
        if mo_description:
            description = mo_description.group(1)
        else:
            description = ''
        if (extractContent):
            parsedTemplate = create_record(template)[0]
            if parsedTemplate != None:
                # If the template was correct
                templates.append([fname_stripped, name, description, parsedTemplate])
            else:
                raise "Problem when parsing the template %s" % (fname, )
        else:
            templates.append([fname_stripped, name, description, date_modified])

    return templates

# Field templates

def get_field_templates():
    """Returns list of field templates [filename, name, description, content]"""
    return get_templates(CFG_BIBEDIT_FIELD_TEMPLATES_PATH, re_ftmpl_name, re_ftmpl_description, True)

# Record templates
def get_record_templates():
    """Return list of record template [filename, name, description]  ."""
    return get_templates(CFG_BIBEDIT_RECORD_TEMPLATES_PATH, re_tmpl_name, re_tmpl_description, False)


def get_record_template(name):
    """Return an XML record template."""
    filepath = '%s%s%s.xml' % (CFG_BIBEDIT_RECORD_TEMPLATES_PATH, os.sep, name)
    if os.path.isfile(filepath):
        template_file = open(filepath, 'r')
        template = template_file.read()
        template_file.close()
        return template


# Private functions
def _get_cache_file(recid, uid, mode):
    """Return a BibEdit cache file object."""
    if cache_exists(recid, uid):
        return open('%s.tmp' % _get_file_path(recid, uid), mode)

def _get_file_path(recid, uid, filename=''):
    """Return the file path to a BibEdit file (excluding suffix).
    If filename is specified this replaces the config default.

    """
    if not filename:
        return '%s%s%s_%s_%s' % (CFG_TMPSHAREDDIR, os.sep, CFG_BIBEDIT_FILENAME,
                                 recid, uid)
    else:
        return '%s%s%s_%s_%s' % (CFG_TMPSHAREDDIR, os.sep, filename, recid, uid)

def _uids_with_active_caches(recid):
    """Return list of uids with active caches for record RECID. Active caches
    are caches that have been modified a number of seconds ago that is less than
    the one given by CFG_BIBEDIT_TIMEOUT.

    """
    re_tmpfilename = re.compile('%s_%s_(\d+)\.tmp' % (CFG_BIBEDIT_FILENAME,
                                                      recid))
    tmpfiles = fnmatch.filter(os.listdir(CFG_TMPSHAREDDIR), '%s*.tmp' %
                              CFG_BIBEDIT_FILENAME)
    expire_time = int(time.time()) - CFG_BIBEDIT_TIMEOUT
    active_uids = []
    for tmpfile in tmpfiles:
        mo = re_tmpfilename.match(tmpfile)
        if mo and int(os.path.getmtime('%s%s%s' % (
                    CFG_TMPSHAREDDIR, os.sep, tmpfile))) > expire_time:
            active_uids.append(int(mo.group(1)))
    return active_uids

def _get_bibupload_task_ids():
    """Return list of all BibUpload task IDs.
    Ignore tasks submitted by user bibreformat.

    """
    res = run_sql('''SELECT id FROM schTASK WHERE proc LIKE "bibupload%" AND user <> "bibreformat" AND status IN ("WAITING", "SCHEDULED", "RUNNING", "CONTINUING", "ABOUT TO STOP", "ABOUT TO SLEEP", "SLEEPING")''')
    return [row[0] for row in res]

def _get_bibupload_filenames():
    """Return paths to all files scheduled for upload."""
    task_ids = _get_bibupload_task_ids()
    filenames = []
    tasks_opts = get_bibupload_task_opts(task_ids)
    for task_opts in tasks_opts:
        if task_opts:
            record_options = marshal.loads(task_opts[0][0])
            for option in record_options[1:]:
                if re_file_option.search(option):
                    filenames.append(option)
    return filenames

def _record_in_files_p(recid, filenames):
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
            if CFG_BIBEDIT_QUEUE_CHECK_METHOD == 'regexp':
                # check via regexp: this is fast, but may not be precise
                re_match_001 = re.compile('<controlfield tag="001">%s</controlfield>' % (recid))
                re_match_oaiid = re.compile('<datafield tag="%s" ind1=" " ind2=" ">(\s*<subfield code="a">\s*|\s*<subfield code="9">\s*.*\s*</subfield>\s*<subfield code="a">\s*)%s' % (OAIID_TAG[0:3],rec_oaiid))
                re_match_sysno = re.compile('<datafield tag="%s" ind1=" " ind2=" ">(\s*<subfield code="a">\s*|\s*<subfield code="9">\s*.*\s*</subfield>\s*<subfield code="a">\s*)%s' % (SYSNO_TAG[0:3],rec_sysno))
                file_content = open(filename).read()
                if re_match_001.search(file_content):
                    return True
                if rec_oaiid_tag:
                    if re_match_oaiid.search(file_content):
                        return True
                if rec_sysno_tag:
                    if re_match_sysno.search(file_content):
                        return True
            else:
                # by default, check via bibrecord: this is accurate, but may be slow
                file_ = open(filename)
                records = create_records(file_.read(), 0, 0)
                for i in range(0, len(records)):
                    record, all_good = records[i][:2]
                    if record and all_good:
                        if _record_has_id_p(record, recid, rec_oaiid, rec_sysno):
                            return True
                file_.close()
        except IOError:
            continue
    return False

def _record_has_id_p(record, recid, rec_oaiid, rec_sysno):
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


def can_record_have_physical_copies(recid):
    """Determine if the record can have physical copies
    (addable through the bibCirculation module).
    The information is derieved using the tabs displayed for a given record.
    Only records already saved within the collection may have the physical copies
    @return: True or False
    """
    if get_record(recid) == None:
        return False

    col_id = get_colID(guess_primary_collection_of_a_record(recid))
    collections = get_detailed_page_tabs(col_id, recid)

    if (not collections.has_key("holdings")) or \
        (not collections["holdings"].has_key("visible")):
        return False

    return collections["holdings"]["visible"] == True

def extend_record_with_template(recid):
    """ Determine if the record has to be extended with the content
    of a template as defined in CFG_BIBEDIT_EXTEND_RECORD_WITH_COLLECTION_TEMPLATE
    @return: template name to be applied to record or False if no template
    has to be applied
    """
    rec_collection = guess_primary_collection_of_a_record(recid)
    if rec_collection in CFG_BIBEDIT_EXTEND_RECORD_WITH_COLLECTION_TEMPLATE:
        return CFG_BIBEDIT_EXTEND_RECORD_WITH_COLLECTION_TEMPLATE[rec_collection]
    return False

def merge_record_with_template(rec, template_name):
    """ Extend the record rec with the contents of the template and return it"""
    template = get_record_template(template_name)
    template_bibrec = create_record(template)[0]

    for field_tag in template_bibrec:
        if not record_has_field(rec, field_tag):
            for field_instance in template_bibrec[field_tag]:
                record_add_field(rec, field_tag, field_instance[1],
                                 field_instance[2], subfields=field_instance[0])
        else:
            for template_field_instance in template_bibrec[field_tag]:
                subfield_codes_template = field_get_subfield_codes(template_field_instance)
                for field_instance in rec[field_tag]:
                    subfield_codes = field_get_subfield_codes(field_instance)
                    for code in subfield_codes_template:
                        if code not in subfield_codes:
                            field_add_subfield(field_instance, code,
                                               field_get_subfield_values(template_field_instance,
                                               code)[0])
    return rec
