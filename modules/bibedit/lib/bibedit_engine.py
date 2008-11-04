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

"""bibedit engine."""

__revision__ = "$Id$"

import cPickle
import difflib
import os
import re
import time
import zlib

from invenio.bibedit_dblayer import get_marcxml_of_record_revision, \
    get_record_revisions, marc_to_split_tag
from invenio.bibedit_utils import get_file_path, get_tmp_file_owner, \
    get_tmp_record, record_in_use_p, record_locked_p
from invenio.bibrecord import record_xml_output, create_record, \
    field_add_subfield, record_add_field
from invenio.bibtask import task_low_level_submission
from invenio.config import CFG_BIBEDIT_TIMEOUT
from invenio.dateutils import convert_datetext_to_dategui
from invenio.search_engine import print_record, record_exists, get_record as se_get_record
import invenio.template

# Precompile regexp:
re_revid_split = re.compile('^(\d+)\.(\d{14})$')
re_revdate_split = re.compile('^(\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)')

bibedit_templates = invenio.template.load('bibedit')

def perform_request_index(ln, recid, cancel, delete, confirm_delete, uid, format_tag, edit_tag,
                          delete_tag, num_field, add, dict_value=None):
    """Returns the body of main page. """
    errors   = []
    warnings = []
    body     = ''

    if cancel != 0:
        os.system("rm -f %s.tmp" % get_file_path(cancel))

    if delete != 0:
        if confirm_delete != 0:
            body = bibedit_templates.confirm(ln, 'delete', delete, format_tag)
        else:
            (record, junk) = get_record(delete, uid)
            add_field(delete, uid, record, "980", "", "", "c", "DELETED")
            save_temp_record(record, uid, "%s.tmp" % get_file_path(delete))
            return perform_request_submit(ln, delete, deleting=True)

    else:
        if recid != 0 :
            if record_exists(recid) > 0:
                body = ''
                (record, original_record) = get_record(recid, uid)
                if record and not record_locked_p(recid):
                    if edit_tag is not None and dict_value is not None:
                        record = edit_record(recid, uid, record, edit_tag, dict_value, num_field)
                    if delete_tag is not None and num_field is not None:
                        record = delete_field(recid, uid, record, delete_tag, num_field)

                    if add == 4:
                        tag     = dict_value.get("add_tag"    , '')
                        ind1    = dict_value.get("add_ind1"   , '')
                        ind2    = dict_value.get("add_ind2"   , '')
                        subcode = dict_value.get("add_subcode", '')
                        value   = dict_value.get("add_value"  , '')
                        another = dict_value.get("addanother" , '')
                        if tag and subcode and value:
                            (record, new_field_number) = add_field(recid, uid, record, tag, ind1, ind2, subcode, value)
                            if another:
                                #if the user pressed 'another' instead of 'done', take to editing
                                return perform_request_edit(ln, recid, uid, tag, new_field_number, 0, 'marc', None, 0, dict_value)
                    # Compare original record with version in tmp file, to
                    # determine if it has been edited.
                    if record != original_record:
                        tmp = True
                        body = bibedit_templates.editor_warning_temp_file(ln)
                    else:
                        tmp = False
                    revisions = len(get_record_revision_ids(recid)) - 1
                    body += bibedit_templates.editor_table_header(ln, "record", recid, tmp, format_tag, add=add, revisions=revisions)
                    keys = record.keys()
                    keys.sort()
                    for tag in keys:
                        fields = record.get(str(tag), "empty")
                        if fields != "empty":
                            for field in fields:
                                if field[0]: # Only display if has subfield(s)
                                    body += bibedit_templates.editor_table_value(ln, recid, tag,
                                                                               field, format_tag, "record", add)
                    if add == 3:
                        body += bibedit_templates.editor_table_value(ln, recid, '', [], format_tag, "record", add, 1)
                    body += bibedit_templates.editor_table_footer(ln, "record", add, 1)
                elif not record:
                    body = bibedit_templates.record_choice_box(ln, 3)
                else:
                    body = bibedit_templates.record_choice_box(ln, 4)
                    os.system("rm %s.tmp" % get_file_path(recid))
            else:
                if record_exists(recid) == -1:
                    body = bibedit_templates.record_choice_box(ln, 2)
                else:
                    body = bibedit_templates.record_choice_box(ln, 1)
        else:
            body = bibedit_templates.record_choice_box(ln, 0)

    return (body, errors, warnings)

def perform_request_edit(ln, recid, uid, tag, num_field, num_subfield,
                         format_tag, act_subfield, add, dict_value):
    """Returns the body of edit page."""
    errors = []
    warnings = []
    body = ''

    (record, junk) = get_record(recid, uid)

    if act_subfield is not None:
        if act_subfield == 'delete':
            record = delete_subfield(recid, uid, record, tag, num_field, num_subfield)
        if act_subfield == 'move_up':
            record = move_subfield('move_up', recid, uid, record, tag, num_field, num_subfield)
        if act_subfield == 'move_down':
            record = move_subfield('move_down', recid, uid, record, tag, num_field, num_subfield)

    if add == 2:
        subcode = dict_value.get("add_subcode", "empty")
        value   = dict_value.get("add_value"  , "empty")
        if subcode == '':
            subcode = "empty"
        if value   == '':
            value   = "empty"

        if value != "empty" and subcode != "empty":
            record = add_subfield(recid, uid, tag, record, num_field, subcode, value)


    body += bibedit_templates.editor_table_header(ln, "edit", recid, False,
                                                tag=tag, num_field=num_field, add=add)

    tag = tag[:3]
    fields = record.get(str(tag), 'empty')
    if fields != "empty":
        for field in fields:
            if field[4] == int(num_field) :
                body += bibedit_templates.editor_table_value(ln, recid, tag, field, format_tag, "edit", add)
                break

    body += bibedit_templates.editor_table_footer(ln, "edit", add)

    return (body, errors, warnings)

def save_temp_record(record, uid, file_path):
    """Save record dict in tmp file."""
    file_temp = open(file_path, "w")
    cPickle.dump([uid, record], file_temp)
    file_temp.close()

def get_record(recid, uid):
    """
    Returns original and tmp record dict. If returned tmp record dict is
    empty, that indicates another user editing the record.
    """
    original_record = se_get_record(recid)
    tmp_record = ''
    file_path = get_file_path(recid)

    if os.path.isfile("%s.tmp" % file_path):
        (tmp_record_uid, tmp_record) = get_tmp_record(recid)
        if tmp_record_uid != uid:
            time_tmp_file = os.path.getmtime("%s.tmp" % file_path)
            time_out_file = int(time.time()) - CFG_BIBEDIT_TIMEOUT
            if time_tmp_file < time_out_file :
                os.system("rm %s.tmp" % file_path)
                tmp_record = original_record
                save_temp_record(tmp_record, uid, "%s.tmp" % file_path)
            else:
                tmp_record = {}
    else:
        tmp_record = original_record
        save_temp_record(tmp_record, uid, "%s.tmp" % file_path)

    return tmp_record, original_record


######### EDIT #########

def edit_record(recid, uid, record, edit_tag, dict_value, num_field):
    """Edits value of a record."""
    for num_subfield in range( len(dict_value.keys())/3 ): # Iterate over subfield indices of field

        new_subcode = dict_value.get("subcode%s"     % num_subfield, None)
        old_subcode = dict_value.get("old_subcode%s" % num_subfield, None)
        new_value   = dict_value.get("value%s"       % num_subfield, None)
        old_value   = dict_value.get("old_value%s"   % num_subfield, None)

        if new_value is not None and old_value is not None \
               and new_subcode is not None and old_subcode is not None: # Make sure we actually get these values
            if new_value != '' and new_subcode != '': # Forbid empty values
                if new_value != old_value or \
                   new_subcode != old_subcode: # only change when necessary

                    edit_tag = edit_tag[:5]
                    record = edit_subfield(record,
                                           edit_tag,
                                           new_subcode,
                                           new_value,
                                           num_field,
                                           num_subfield)

    save_temp_record(record, uid, "%s.tmp" % get_file_path(recid))

    return record


def edit_subfield(record, tag, new_subcode, new_value, num_field, num_subfield):
    """Edits the value of a subfield."""

    new_value   = bibedit_templates.clean_value(str(new_value),     "html")

    (tag, ind1, ind2, junk) = marc_to_split_tag(tag)

    fields = record.get(str(tag), None)

    if fields is not None:
        i = -1
        for field in fields:
            i += 1
            if field[4] == int(num_field):
                subfields = field[0]
                j = -1
                for subfield in subfields:
                    j += 1

                    if j == num_subfield: # Rely on counted index to identify subfield to edit...
                        record[tag][i][0][j] = (new_subcode, new_value)
                        break
                break
    return record


######### ADD ########

def add_field(recid, uid, record, tag, ind1, ind2, subcode, value_subfield):
    """Adds a new field to the record."""

    tag = tag[:3]

    new_field_number = record_add_field(record, tag, ind1, ind2)
    record = add_subfield(recid, uid, tag, record, new_field_number, subcode, value_subfield)

    save_temp_record(record, uid, "%s.tmp" % get_file_path(recid))

    return record, new_field_number


def add_subfield(recid, uid, tag, record, num_field, subcode, value):
    """Adds a new subfield to a field."""

    tag = tag[:3]
    fields = record.get(str(tag))
    i = -1

    for field in fields:
        i += 1
        if field[4] == int(num_field) :

            subfields = field[0]

            field_add_subfield(record[tag][i], subcode, value)
            break

    save_temp_record(record, uid, "%s.tmp" % get_file_path(recid))

    return record


######### DELETE ########

def delete_field(recid, uid, record, tag, num_field):
    """Deletes field in record."""

    (tag, junk, junk, junk) = marc_to_split_tag(tag)
    tmp = []

    for field in record[tag]:
        if field[4] != int(num_field) :
            tmp.append(field)

    if tmp != []:
        record[tag] = tmp

    else:
        del record[tag]

    save_temp_record(record, uid, "%s.tmp" % get_file_path(recid))

    return record


def delete_subfield(recid, uid, record, tag, num_field, num_subfield):
    """Deletes subfield of a field."""

    (tag, junk, junk, subcode) = marc_to_split_tag(tag)
    tmp = []
    i = -1
    deleted = False
    for field in record[tag]:
        i += 1
        if field[4] == int(num_field):
            j = 0
            for subfield in field[0]:
                if j != num_subfield:
                #if subfield[0] != subcode or deleted == True:
                    tmp.append((subfield[0], subfield[1]))
                #else:
                #    deleted = True
                j += 1
            break

    record[tag][i] = (tmp, record[tag][i][1], record[tag][i][2], record[tag][i][3], record[tag][i][4])
    save_temp_record(record, uid, "%s.tmp" % get_file_path(recid))
    return record

def move_subfield(direction, recid, uid, record, tag, num_field, num_subfield):
    """Moves a subfield up in the field."""
    (tag, junk, junk, subcode) = marc_to_split_tag(tag)
    i = -1
    for field in record[tag]:
        i += 1
        if field[4] == int(num_field):
            j = -1
            mysubfields = field[0]
            for subfield in mysubfields:
                j += 1
                if direction == 'move_up' and num_subfield == j and j > 0:
                    #swap this and the previous..
                    prevsubfield = field[0][j-1]
                    field[0][j-1] = subfield
                    field[0][j] = prevsubfield
                if direction == 'move_down' and num_subfield == j and j < len(mysubfields):
                    #swap this and the next..
                    nextsubfield = field[0][j+1]
                    field[0][j+1] = subfield
                    field[0][j] = nextsubfield
    save_temp_record(record, uid, "%s.tmp" % get_file_path(recid))
    return record

def perform_request_submit(ln, recid, xml_record='', deleting=False):
    """Submits record to the database. """
    if xml_record:
        save_xml_record(recid, xml_record)
    else:
        save_xml_record(recid)
    errors   = []
    warnings = []
    if deleting:
        body = bibedit_templates.record_choice_box(ln, 6)
    else:
        body = bibedit_templates.record_choice_box(ln, 5)
    return (body, errors, warnings)

def save_xml_record(recid, xml_record=''):
    """Saves XML record file to database."""
    file_path = get_file_path(recid)
    os.system("rm -f %s.xml" % file_path)
    file_temp = open("%s.xml" % file_path, 'w')
    if xml_record:
        file_temp.write(xml_record)
    else:
        file_temp.write(record_xml_output(get_tmp_record(recid)[1]))
        os.system("rm %s.tmp" % file_path)
    file_temp.close()
    task_low_level_submission('bibupload', 'bibedit', '-P', '5', '-r',
                              '%s.xml' % file_path)

def perform_request_history(ln, recid, revid, revid_cmp, action, uid,
                            format_tag):
    """Performs historic operations on a record."""
    errors   = []
    warnings = []
    body = ''

    if action == 'revert' and revid:
        body = bibedit_templates.confirm(
            ln, 'revert', recid, format_tag=format_tag, revid=revid,
            revdate=split_revid(revid, 'dategui')[1])
        return (body, errors, warnings)

    if action == 'confirm_revert' and revid:
        # Is the record locked for editing?
        if record_locked_p(recid):
            body = bibedit_templates.record_choice_box(ln, 4)
            return (body, errors, warnings)
        # Is the record being edited?
        if record_in_use_p(recid):
            if get_tmp_file_owner(recid) != uid:
                body = bibedit_templates.record_choice_box(ln, 3)
                return (body, errors, warnings)
            else:
                os.system("rm -f %s" % ('%s.tmp' % get_file_path(recid)))
        # Submit the revision.
        return perform_request_submit(ln, recid,
                                      get_marcxml_of_revision_id(revid))

    revids = get_record_revision_ids(recid)
    if not revid:
        revid = revids[0]
    body = bibedit_templates.history_container('header')
    revdates = [split_revid(some_revid, 'dategui')[1] for some_revid
                in revids]
    revdate = split_revid(revid, 'dategui')[1]

    if action == 'compare' and revid_cmp:
        revdate_cmp = split_revid(revid_cmp, 'dategui')[1]
        xml1 = get_marcxml_of_revision_id(revid)
        xml2 = get_marcxml_of_revision_id(revid_cmp)
        comparison = bibedit_templates.clean_value(
            get_xml_comparison(revid, revid_cmp, xml1, xml2),
            'text').replace('\n', '<br />\n           ')
        body += bibedit_templates.history_comparebox(ln, revdate,
            revdate_cmp, comparison)
        forms = bibedit_templates.history_forms(ln, recid, revids,
            revdates, 'compare', revid, format_tag, revid_cmp)

    else:
        current = revid == revids[0]
        revision = create_record(get_marcxml_of_revision_id(
            revid))[0]
        body += bibedit_templates.history_viewbox(ln, 'header',
            current, recid, revid, revdate)
        body += bibedit_templates.history_revision(ln, recid, format_tag,
                                                        revision)
        body += bibedit_templates.history_viewbox(ln, 'footer',
            current, recid, revid, revdate)
        forms = bibedit_templates.history_forms(ln, recid, revids,
            revdates, 'view', revid, format_tag)

    body += forms
    body += bibedit_templates.history_container('footer')
    return (body, errors, warnings)

def get_marcxml_of_revision_id(revid):
    """
    Return MARCXML string with corresponding to revision REVID
    (=RECID.REVDATE) of a record.  Return empty string if revision
    does not exist.  REVID is assumed to be washed already.
    """
    res = ""
    (recid, job_date) = split_revid(revid, 'datetext')
    tmp_res = get_marcxml_of_record_revision(recid, job_date)
    if tmp_res:
        for row in tmp_res:
            res += zlib.decompress(row[0]) + "\n"
    return res

def get_record_revision_ids(recid):
    """
    Return list of all known record revision ids (=RECID.REVDATE) for
    record RECID in chronologically decreasing order (latest first).
    """
    res = []
    tmp_res =  get_record_revisions(recid)
    for row in tmp_res:
        res.append("%s.%s" % (row[0], row[1]))
    return res

def get_xml_comparison(header1, header2, xml1, xml2):
    """
    Return diffs of two MARCXML records.
    """
    return "".join(difflib.unified_diff(xml1.splitlines(1),
        xml2.splitlines(1), header1, header2))

def split_revid(revid, dateformat=''):
    """
    Split revid and return tuple with (recid, revdate).
    Optional dateformat can be datetext or dategui.
    """
    (recid, revdate) = re_revid_split.search(revid).groups()
    if dateformat:
        datetext = '%s-%s-%s %s:%s:%s' % re_revdate_split.search(
            revdate).groups()
        if dateformat == 'datetext':
            revdate = datetext
        elif dateformat == 'dategui':
            revdate = convert_datetext_to_dategui(datetext, secs=True)
    return (recid, revdate)

def revision_format_valid_p(revid):
    """Predicate to test validity of revision ID format (=RECID.REVDATE)."""
    if re_revid_split.match(revid):
        return True
    return False
