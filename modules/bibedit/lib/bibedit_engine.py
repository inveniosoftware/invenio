## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

import os
import time
import cPickle
from invenio.config import bindir, tmpdir
from invenio.bibedit_dblayer import marc_to_split_tag
from invenio.bibedit_config import *
from invenio.search_engine import print_record, record_exists
from invenio.bibrecord import record_xml_output, create_record, field_add_subfield, record_add_field
import invenio.template

bibedit_templates = invenio.template.load('bibedit')

def perform_request_index(ln, recid, cancel, delete, confirm_delete, uid, temp, format_tag, edit_tag,
                          delete_tag, num_field, add, dict_value=None):    
    """ This function return the body of main page. """
    
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

                if record != '':
                    if add == 3:
                        body = ''

                    if edit_tag != None and dict_value != None:
                        record = edit_record(recid, uid, record, edit_tag, dict_value)

                    if delete_tag != None and num_field != None:
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
                                if tag != '001':
                                    body += bibedit_templates.tmpl_table_value(ln, recid, tag,
                                                                               field, format_tag, "record", add)

                    if add == 3:
                        body += bibedit_templates.tmpl_table_value(ln, recid, '', [], format_tag, "record", add, 1)

                    body += bibedit_templates.tmpl_table_footer(ln, "record", add)

                else:
                    body = bibedit_templates.tmpl_record_choice_box(ln, 2)

            else:
                if record_exists(recid) == -1: 
                    body = bibedit_templates.tmpl_record_choice_box(ln, 3)
                else:
                    body = bibedit_templates.tmpl_record_choice_box(ln, 1)

        else:
            body = bibedit_templates.tmpl_record_choice_box(ln, 0)
        
    return (body, errors, warnings)


def perform_request_edit(ln, recid, uid, tag, num_field, format_tag, temp, del_subfield, add, dict_value):    
    """ This function return the body of edit page. """
    
    errors = []
    warnings = []
    body = ''
    if record_exists(recid) in (-1, 0):
        body = bibedit_templates.tmpl_record_choice_box(ln, 0)
        return (body, errors, warnings)
    
    (record, junk) = get_record(ln, recid, uid, temp)
    
    if del_subfield != None:
        record = delete_subfield(recid, uid, record, tag, num_field)
                
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
    """ This function submit record on database. """
    
    save_xml_record(recid)
    
    errors   = []
    warnings = []
    body     = bibedit_templates.tmpl_submit(ln)
    
    return (body, errors, warnings)


def get_file_path(recid):
    """ return the file path of record. """
    
    return "%s/%s_%s" % (tmpdir, cfg_bibedit_tmpfilenameprefix, str(recid))


def save_xml_record(recid):    
    """ Save XML Record File in database. """
    
    file_path = get_file_path(recid)
    
    file_temp = open("%s.xml" % file_path, 'w')
    file_temp.write(record_xml_output(get_temp_record("%s.tmp" % file_path)[1]))
    file_temp.close()
    
    os.system("%s/bibupload -r %s.xml" % (bindir, file_path))
    os.system("rm %s.tmp" % file_path)
    
def save_temp_record(record, uid, file_path):
    """ Save record dict in temp file. """
    
    file_temp = open(file_path, "w")
    cPickle.dump([uid, record], file_temp)
    file_temp.close()


def get_temp_record(file_path):    
    """ Load record dict from a temp file. """
    
    file_temp = open(file_path)
    [uid, record] = cPickle.load(file_temp)
    file_temp.close()
    
    return (uid, record)


def get_record(ln, recid, uid, temp):    
    """ This function return a record dict,
        and warning message in case of. """

    file_path = get_file_path(recid)
    
    if temp != "false":
        warning_temp_file = bibedit_templates.tmpl_warning_temp_file(ln)         
    else:
        warning_temp_file = ''
    
    if os.path.isfile("%s.tmp" % file_path):

        (uid_record_temp, record) = get_temp_record("%s.tmp" % file_path)
        
        if uid_record_temp != uid:

            time_tmp_file = os.path.getmtime("%s.tmp" % file_path)
            time_out_file = int(time.time()) - cfg_bibedit_timeout
            
            if time_tmp_file < time_out_file :
                
                os.system("rm %s.tmp" % file_path)
                record = create_record(print_record(recid, 'xm'))[0]
                save_temp_record(record, uid, "%s.tmp" % file_path)

            else:
                record = ''

    else:
        record = create_record(print_record(recid, 'xm'))[0]
        save_temp_record(record, uid, "%s.tmp" % file_path)
        
    return (record, warning_temp_file)


######### EDIT #########

def edit_record(recid, uid, record, edit_tag, dict_value):    
    """ This function edit value in record. """
    
    for subfield in range( len(dict_value.keys())/3 ):
        
        subcode     = dict_value.get("subcode%s"     % int(subfield), "empty")
        old_subcode = dict_value.get("old_subcode%s" % int(subfield), "empty")
        value       = dict_value.get("value%s"       % int(subfield), "empty")
        old_value   = dict_value.get("old_value%s"   % int(subfield), "empty")
        
        if value != "empty" and old_value != "empty" and subcode != "empty":
            if value != '' and subcode != '':
                if value != old_value or \
                   subcode != old_subcode:
                
                    edit_tag = edit_tag[:5]                
                    record = edit_subfield(record, edit_tag, subcode, old_subcode, value, old_value)
       
    save_temp_record(record, uid, "%s.tmp" % get_file_path(recid))
    
    return record


def edit_subfield(record, tag, subcode, old_subcode, value, old_value):
    """ This function edit the value of subfield. """

    value       = bibedit_templates.tmpl_clean_value(str(value),     "html")
    old_value   = bibedit_templates.tmpl_clean_value(str(old_value), "html")
    
    (tag, ind1, ind2, junk) = marc_to_split_tag(tag)
    
    fields = record.get(str(tag), "empty")
    
    if fields != "empty":
        i = -1
        for field in fields:
            i += 1
            if field[1] == ind1 and field[2] == ind2:
                subfields = field[0] 
                j = -1
                for subfield in subfields:
                    j += 1
                    if subfield[0] == old_subcode and \
                       subfield[1] == old_value:
                        record[tag][i][0][j] = (subcode, value)
                        break
                    
    return record


######### ADD ########

def add_field(recid, uid, record, tag, ind1, ind2, subcode, value_subfield):
    """ This function add a new field in record. """
    
    tag = tag[:3]

    new_field_number = record_add_field(record, tag, ind1, ind2)
    record  = add_subfield(recid, uid, tag, record, new_field_number, subcode, value_subfield)
    
    save_temp_record(record, uid, "%s.tmp" % get_file_path(recid))
    
    return record


def add_subfield(recid, uid, tag, record, num_field, subcode, value):
    """ This function add a new subfield in a field. """

    tag = tag[:3]
    fields = record.get(str(tag))
    i = -1
    
    for field in fields:
        i += 1
        if field[4] == int(num_field) :

            subfields = field[0]
            same_subfield = False
            for subfield in subfields:
                if subfield[0] == subcode:
                    same_subfield = True

            if same_subfield is False:     
                field_add_subfield(record[tag][i], subcode, value)
                break

    save_temp_record(record, uid, "%s.tmp" % get_file_path(recid))
    
    return record


######### DELETE ########

def delete_field(recid, uid, record, tag, num_field):    
    """ This function delete field in record. """
    
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


def delete_subfield(recid, uid, record, tag, num_field):    
    """ This function delete subfield in field. """
    
    (tag, junk, junk, subcode) = marc_to_split_tag(tag)
    tmp = []
    i = -1
    
    for field in record[tag]:
        i += 1
        if field[4] == int(num_field):
            for subfield in field[0]:
                if subfield[0] != subcode:
                    tmp.append((subfield[0], subfield[1]))
            break
                    
    record[tag][i] = (tmp, record[tag][i][1], record[tag][i][2], record[tag][i][3], record[tag][i][4])
    
    save_temp_record(record, uid, "%s.tmp" % get_file_path(recid))
    
    return record

