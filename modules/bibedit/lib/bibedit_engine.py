## $Id$
##
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

__revision__ = "$Id$"

import cPickle
import marshal
import os
import sre
import time

from invenio.bibedit_config import CFG_BIBEDIT_TMPFILENAMEPREFIX
from invenio.bibedit_dblayer import marc_to_split_tag
from invenio.bibformat_engine import BibFormatObject
from invenio.bibrecord import record_xml_output, create_record, create_records, \
    field_add_subfield, record_add_field, record_has_field, record_get_field_value
from invenio.bibtask import task_low_level_submission
from invenio.config import CFG_BINDIR, CFG_TMPDIR, CFG_BIBEDIT_TIMEOUT, CFG_BIBEDIT_LOCKLEVEL
from invenio.dbquery import run_sql
from invenio.shellutils import run_shell_command
from invenio.search_engine import print_record, record_exists
import invenio.template

bibedit_templates = invenio.template.load('bibedit')

def perform_request_index(ln, recid, cancel, delete, confirm_delete, uid, temp, format_tag, edit_tag,
                          delete_tag, num_field, add, dict_value=None):
    """Returns the body of main page. """

    errors   = []
    warnings = []
    body     = ''

    if cancel != 0:
        os.system("rm %s.tmp" % get_file_path(cancel))

    if delete != 0:
        if confirm_delete != 0:
            body = bibedit_templates.tmpl_deleted(ln, 1, delete, temp, format_tag)
        else:
            (record, junk) = get_record(ln, delete, uid, "false")
            add_field(delete, uid, record, "980", "", "", "c", "DELETED")
            save_temp_record(record, uid, "%s.tmp" % get_file_path(delete))
            save_xml_record(delete)
            body = bibedit_templates.tmpl_deleted(ln)

    else:
        if recid != 0 :
            if record_exists(recid) > 0:
                (record, body) = get_record(ln, recid, uid, temp)

                if record != '' and not record_locked_b(recid):
                    if add == 3:
                        body = ''

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

                        if tag != '' and subcode != '' and value != '':
                            record = add_field(recid, uid, record, tag, ind1, ind2, subcode, value)

                    body += bibedit_templates.tmpl_table_header(ln, "record", recid, temp, format_tag, add=add)

                    keys = record.keys()
                    keys.sort()

                    for tag in keys:

                        fields = record.get(str(tag), "empty")

                        if fields != "empty":
                            for field in fields:
                                if field[0]: # Only display if has subfield(s)
                                    body += bibedit_templates.tmpl_table_value(ln, recid, tag,
                                                                               field, format_tag, "record", add)

                    if add == 3:
                        body += bibedit_templates.tmpl_table_value(ln, recid, '', [], format_tag, "record", add, 1)

                    body += bibedit_templates.tmpl_table_footer(ln, "record", add)

                elif record == '':
                    body = bibedit_templates.tmpl_record_choice_box(ln, 2)

                elif CFG_BIBEDIT_LOCKLEVEL == 2:
                    os.system("rm %s.tmp" % get_file_path(recid))
                    body = bibedit_templates.tmpl_record_choice_box(ln, 4)

                else:
                    os.system("rm %s.tmp" % get_file_path(recid))
                    body = bibedit_templates.tmpl_record_choice_box(ln, 5)

            else:
                if record_exists(recid) == -1:
                    body = bibedit_templates.tmpl_record_choice_box(ln, 3)
                else:
                    body = bibedit_templates.tmpl_record_choice_box(ln, 1)

        else:
            body = bibedit_templates.tmpl_record_choice_box(ln, 0)

    return (body, errors, warnings)


def perform_request_edit(ln, recid, uid, tag, num_field, num_subfield,
                         format_tag, temp, act_subfield, add, dict_value):
    """Returns the body of edit page. """

    errors = []
    warnings = []
    body = ''
    if record_exists(recid) in (-1, 0):
        body = bibedit_templates.tmpl_record_choice_box(ln, 0)
        return (body, errors, warnings)

    (record, junk) = get_record(ln, recid, uid, temp)

    if act_subfield is not None:
        if act_subfield == bibedit_templates.DELETE: #delete
            record = delete_subfield(recid, uid, record, tag, num_field, num_subfield)
        if act_subfield == bibedit_templates.MOVE_UP: #move up
            record = move_subfield(bibedit_templates.MOVE_UP, recid, uid, record, tag, num_field, num_subfield)
        if act_subfield == bibedit_templates.MOVE_DOWN: #move down
            record = move_subfield(bibedit_templates.MOVE_DOWN, recid, uid, record, tag, num_field, num_subfield)

    if add == 2:
        subcode = dict_value.get("add_subcode", "empty")
        value   = dict_value.get("add_value"  , "empty")
        if subcode == '':
            subcode = "empty"
        if value   == '':
            value   = "empty"

        if value != "empty" and subcode != "empty":
            record = add_subfield(recid, uid, tag, record, num_field, subcode, value)

    body += bibedit_templates.tmpl_table_header(ln, "edit", recid, temp=temp,
                                                tag=tag, num_field=num_field, add=add)

    tag = tag[:3]
    fields = record.get(str(tag), "empty")

    if fields != "empty":
        for field in fields:
            if field[4] == int(num_field) :
                body += bibedit_templates.tmpl_table_value(ln, recid, tag, field, format_tag, "edit", add)
                break

    body += bibedit_templates.tmpl_table_footer(ln, "edit", add)

    return (body, errors, warnings)


def perform_request_submit(ln, recid):
    """Submits record to the database. """

    save_xml_record(recid)

    errors   = []
    warnings = []
    body     = bibedit_templates.tmpl_submit(ln)

    return (body, errors, warnings)


def get_file_path(recid):
    """ return the file path of record. """

    return "%s/%s_%s" % (CFG_TMPDIR, CFG_BIBEDIT_TMPFILENAMEPREFIX, str(recid))


def save_xml_record(recid):
    """Saves XML record file to database. """

    file_path = get_file_path(recid)

    file_temp = open("%s.xml" % file_path, 'w')
    file_temp.write(record_xml_output(get_temp_record("%s.tmp" % file_path)[1]))
    file_temp.close()
    task_low_level_submission('bibupload', 'bibedit', '-P', '5', '-r', '%s.xml' % file_path)
    os.system("rm %s.tmp" % file_path)

def save_temp_record(record, uid, file_path):
    """ Save record dict in temp file. """

    file_temp = open(file_path, "w")
    cPickle.dump([uid, record], file_temp)
    file_temp.close()


def get_temp_record(file_path):
    """Loads record dict from a temp file. """

    file_temp = open(file_path)
    [uid, record] = cPickle.load(file_temp)
    file_temp.close()

    return (uid, record)


def get_record(ln, recid, uid, temp):
    """Returns a record dict, and warning message in case of error. """
    #FIXME: User doesn't get submit button if reloading BibEdit-page

    warning_temp_file = ''
    file_path = get_file_path(recid)

    if temp != "false":
        warning_temp_file = bibedit_templates.tmpl_warning_temp_file(ln)

    if os.path.isfile("%s.tmp" % file_path):

        (uid_record_temp, record) = get_temp_record("%s.tmp" % file_path)
        if uid_record_temp != uid:

            time_tmp_file = os.path.getmtime("%s.tmp" % file_path)
            time_out_file = int(time.time()) - CFG_BIBEDIT_TIMEOUT

            if time_tmp_file < time_out_file :
                os.system("rm %s.tmp" % file_path)
                record = create_record(print_record(recid, 'xm'))[0]
                save_temp_record(record, uid, "%s.tmp" % file_path)

            else:
                record = ''

        else:
            warning_temp_file = bibedit_templates.tmpl_warning_temp_file(ln)

    else:
        record = create_record(print_record(recid, 'xm'))[0]
        save_temp_record(record, uid, "%s.tmp" % file_path)

    return (record, warning_temp_file)


######### EDIT #########

def edit_record(recid, uid, record, edit_tag, dict_value, num_field):
    """Edits value of a record. """

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
    """Edits the value of a subfield. """

    new_value   = bibedit_templates.tmpl_clean_value(str(new_value),     "html")

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
    """Adds a new field to the record. """

    tag = tag[:3]

    new_field_number = record_add_field(record, tag, ind1, ind2)
    record  = add_subfield(recid, uid, tag, record, new_field_number, subcode, value_subfield)

    save_temp_record(record, uid, "%s.tmp" % get_file_path(recid))

    return record


def add_subfield(recid, uid, tag, record, num_field, subcode, value):
    """Adds a new subfield to a field. """

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
    """Deletes field in record. """

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
    """Deletes subfield of a field. """

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
    """moves a subfield up in the field """
    (tag, junk, junk, subcode) = marc_to_split_tag(tag)
    i = -1
    for field in record[tag]:
        i += 1
        if field[4] == int(num_field):
            j = -1
            mysubfields = field[0]
            for subfield in mysubfields:
                j += 1
                if direction == bibedit_templates.MOVE_UP and num_subfield == j and j > 0:
                    #swap this and the previous..
                    prevsubfield = field[0][j-1]
                    field[0][j-1] = subfield
                    field[0][j] = prevsubfield
                if direction == bibedit_templates.MOVE_DOWN and num_subfield == j and j < len(mysubfields):
                    #swap this and the next..
                    nextsubfield = field[0][j+1]
                    field[0][j+1] = subfield
                    field[0][j] = nextsubfield
    save_temp_record(record, uid, "%s.tmp" % get_file_path(recid))
    return record

def record_locked_b(recid):
    """Checks if record should be locked for editing, method based on CFG_BIBEDIT_LOCKLEVEL. """

    # Check only for tmp-file (done in get_record).
    if CFG_BIBEDIT_LOCKLEVEL == 0:
        return 0

    cmd = """%s/bibsched status -t bibupload | grep -v 'USER="bibreformat"'""" % CFG_BINDIR
    (junk, bibsched_status, junk) = run_shell_command(cmd)

    # Check for any scheduled bibupload tasks.
    if CFG_BIBEDIT_LOCKLEVEL == 2:
        return bibsched_status.find('PROC="bibupload"') + 1

    # Collect path to all files scheduled for upload.
    find_tasks = sre.compile('ID="(\d+)"')
    find_file_option = sre.compile(r'^/')
    tasks = find_tasks.findall(bibsched_status)
    filenames = []
    for task in tasks:
        res = run_sql("SELECT arguments FROM schTASK WHERE id=%s" % task)
        if res:
            record_options = marshal.loads(res[0][0])
            for option in record_options[1:]:
                if find_file_option.search(option):
                    filenames.append(option)

    # Check for match between name of XML-file and record.
    # Assumes that filename ends with _<recid>.xml.
    if CFG_BIBEDIT_LOCKLEVEL == 1:
        recids = []
        find_filename_suffix = sre.compile('_(\d+)\.xml$')
        for filename in filenames:
            filename_suffix = find_filename_suffix.search(filename)
            if filename_suffix:
                recids.append(int(filename_suffix.group(1)))
        return recid in recids

    # Check for match between content of files and record.
    if CFG_BIBEDIT_LOCKLEVEL == 3:
        recs_field_001 = []
        recs_field_035__a = []
        recs_field_970__a = []
        for filename in filenames:
            try:
                file_ = open(filename)
                records = create_records(file_.read(), 0, 0)
                for i in range(0, len(records)):
                    (record, er, junk) = records[i]
                    if record != None and er != 0:
                        if record_has_field(record, '001'):
                            recs_field_001.append(record_get_field_value(record, '001', '%', '%'))
                        if record_has_field(record, '035'):
                            recs_field_035__a.append(record_get_field_value(record, '035', '%', '%', 'a'))
                        if record_has_field(record, '970'):
                            recs_field_970__a.append(record_get_field_value(record, '970', '%', '%', 'a'))
                file_.close()
            except IOError:
                continue
            bfo = BibFormatObject(recid)
        return (bfo.control_field('001') in recs_field_001 or bfo.field('035__a')
            in recs_field_035__a or bfo.field('970__a') in recs_field_970__a)
