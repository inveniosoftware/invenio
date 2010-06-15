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

"""CDS Invenio Multiple Record Editor Engine.

Every action related to record modification is performed
by specific class (successor of some of the commands).
Every of these classes is designed to perform specific action.

The engine itself receives a list of this classes and after retrieving
the records, asks the commands to perform their changes. This way the
engine itself is independent of the actions for modification of the records.

When we need to perform a new action on the records, we define a new command
and take care to pass it to the engine.


***************************************************************************
Subfield commands represent the actions performed on the subfields
of the record. The interface of these commands is defined in their
base class.
"""

__revision__ = "$Id"

import cgi

from invenio import search_engine
from invenio import bibrecord
from invenio import bibformat

from invenio.config import CFG_TMPDIR, CFG_BIBEDITMULTI_LIMIT_INSTANT_PROCESSING,\
                           CFG_BIBEDITMULTI_LIMIT_DELAYED_PROCESSING,\
                           CFG_BIBEDITMULTI_LIMIT_DELAYED_PROCESSING_TIME
from time import strftime
from invenio.bibtask import task_low_level_submission

from invenio.webuser import collect_user_info, isUserSuperAdmin

from invenio.dbquery import run_sql

from invenio import template
multiedit_templates = template.load('bibeditmulti')

# base command for subfields
class BaseSubfieldCommand:
    """Base class for commands manipulating subfields"""
    def __init__(self, subfield, value = "", new_value = "", condition = "", condition_subfield = ""):
        """Initialization."""
        self._subfield = subfield
        self._value = value
        self._new_value = new_value
        self._condition = condition
        self._condition_subfield = condition_subfield

    def process_field(self, record, tag, field_number):
        """Make changes to a record.

        By default this method is empty.

        Every specific command provides its own implementation"""
        pass

    def _perform_on_all_matching_subfields(self, record, tag, field_number, callback):
        """Perform an action on all subfields of a given field matching
        the subfield represented by the current command.

        e.g. change the value of all subfields 'a' in a given field

        This method is necessary because in order to make changes in the
        subfields of a given field you always have to iterate through all
        of them. This is repetition of code is extracted in this method.

        @param record: record structure representing record to be modified
        @param tag: the tag used to identify the field
        @param field_number: field number used to identify the field
        @param callback: callback method that will be called to
            perform an action on the subfield.
            This callback should accept the following parameters:
            record, tag, field_number, subfield_index
        """
        if tag not in record.keys():
            return
        for field in record[tag]:
            if field[4] == field_number:
                subfield_index = 0
                for subfield in field[0]:
                    if self._condition != 'condition':
                        if (self._condition_subfield == subfield[0]) and (self._condition == subfield[1]):
                            callback(record, tag, field_number, subfield_index)
                    elif subfield[0] == self._subfield:
                        callback(record, tag, field_number, subfield_index)
                    subfield_index = subfield_index+1

# specific commands for subfields

class AddSubfieldCommand(BaseSubfieldCommand):
    """Add subfield to a given field"""
    def process_field(self, record, tag, field_number):
        """@see: BaseSubfieldCommand.process_field"""
        action = lambda record, tag, field_number, subfield_index: \
                      bibrecord.record_add_subfield_into(record, tag,
                                         self._subfield, self._value,
                                         None,
                                         field_position_global=field_number)
        if self._condition != 'condition':
            self._perform_on_all_matching_subfields(record, tag,
                                                    field_number, action)
        else:
            action(record, tag, field_number, None)

class DeleteSubfieldCommand(BaseSubfieldCommand):
    """Delete subfield from a given field"""

    def process_field(self, record, tag, field_number):
        """@see: BaseSubfieldCommand.process_field"""
        action = lambda record, tag, field_number, subfield_index: \
                    bibrecord.record_delete_subfield_from(record, tag,
                                                          subfield_index,
                                      field_position_global=field_number)
        self._perform_on_all_matching_subfields(record, tag,
                                                field_number, action)

class ReplaceSubfieldContentCommand(BaseSubfieldCommand):
    """Replace content of subfield in a given field"""

    def process_field(self, record, tag, field_number):
        """@see: BaseSubfieldCommand.process_field"""
        action = lambda record, tag, field_number, subfield_index: \
                    bibrecord.record_modify_subfield(record, tag,
                                                     self._subfield,
                                                     self._value,
                                                     subfield_index,
                                      field_position_global=field_number)
        self._perform_on_all_matching_subfields(record,
                                                tag,
                                                field_number,
                                                action)

class ReplaceTextInSubfieldCommand(BaseSubfieldCommand):
    """Replace text in content of subfield of a given field"""

    def process_field(self, record, tag, field_number):
        """@see: BaseSubfieldCommand.process_field"""

        def replace_text(record, tag, field_number, subfield_index):
            """Method for replacing the text, performed on
            all the matching fields."""
            #get the field value
            field_value = ""
            for field in record[tag]:
                if field[4] == field_number:
                    subfields = field[0]
                    (field_code, field_value) = subfields[subfield_index]
            #replace text
            new_value = field_value.replace(self._value, self._new_value)
            #update the subfield
            bibrecord.record_modify_subfield(record, tag,
                                             self._subfield, new_value,
                                             subfield_index,
                                    field_position_global=field_number)
        self._perform_on_all_matching_subfields(record,
                                                tag,
                                                field_number,
                                                replace_text)

"""***************************************************************************
Field commands represent the actions performed on the fields
of the record. The interface of these commands is defined in their
base class.

In general the changes related to field's subfields are handled by subfield
commands, that are passed to the field command.
"""

# base command for fields
class BaseFieldCommand:
    """Base class for commands manipulating record fields"""
    def __init__(self, tag, ind1, ind2, subfield_commands):
        """Initialization."""
        self._tag = tag
        self._ind1 = ind1
        self._ind2 = ind2
        self._subfield_commands = subfield_commands

    def process_record(self, record):
        """Make changes to a record.

        By default this method is empty.

        Every specific command provides its own implementation"""
        pass

    def _apply_subfield_commands_to_field(self, record, field_number):
        """Applies all subfield commands to a given field"""
        for subfield_command in self._subfield_commands:
            subfield_command.process_field(record, self._tag, field_number)

# specific commands for fields

class AddFieldCommand(BaseFieldCommand):
    """Deletes given fields from a record"""

    def process_record(self, record):
        """@see: BaseFieldCommand.process_record"""
        # if the tag is empty, we don't make any changes
        if self._tag == "" or self._tag == None:
            return

        field_number = bibrecord.record_add_field(record, self._tag,
                                                  self._ind1, self._ind2)
        self._apply_subfield_commands_to_field(record, field_number)

class DeleteFieldCommand(BaseFieldCommand):
    """Deletes given fields from a record"""

    def process_record(self, record):
        """@see: BaseFieldCommand.process_record"""
        bibrecord.record_delete_field(record, self._tag, self._ind1, self._ind2)
class UpdateFieldCommand(BaseFieldCommand):
    """Deletes given fields from a record"""

    def process_record(self, record):
        """@see: BaseFieldCommand.process_record"""

        # if the tag is empty, we don't make any changes
        if self._tag == "" or self._tag == None:
            return

        matching_field_instances = \
            bibrecord.record_get_field_instances(record, self._tag,
                                                 self._ind1, self._ind2)
        for current_field in matching_field_instances:
            self._apply_subfield_commands_to_field(record, current_field[4])


def perform_request_index(language):
    """Creates the page of MultiEdit

    @param language: language of the page
    """
    collections = ["Any collection"]
    collections.extend([collection[0] for collection in run_sql('SELECT name FROM collection')])
    return multiedit_templates.page_contents(language=language, collections=collections)

def get_scripts():
    """Returns JavaScripts that have to be
    imported in the page"""
    return multiedit_templates.scripts()

def get_css():
    """Returns the local CSS for the pages."""
    return multiedit_templates.styles()

def perform_request_detailed_record(record_id, update_commands, output_format, language):
    """Returns

    @param record_id: the identifier of the record
    @param update_commands: list of commands used to update record contents
    @param output_format: specifies the output format as expected from bibformat
    @param language: language of the page
    """

    record_content = _get_formated_record(record_id=record_id,
                                output_format=output_format,
                                update_commands = update_commands,
                                language=language)

    result = multiedit_templates.detailed_record(record_content, language)

    return result

def perform_request_test_search(search_criteria, update_commands, output_format, page_to_display, language, outputTags, collection=""):
    """Returns the results of a test search.

    @param search_criteria: search criteria used in the test search
    @param update_commands: list of commands used to update record contents
    @param output_format: specifies the output format as expected from bibformat
    @param page_to_display: the number of the page that should be displayed to the user
    @param language: the language used to format the content
    """
    RECORDS_PER_PAGE = 10

    if collection == "Any collection":
        collection = ""
    record_IDs = search_engine.perform_request_search(p=search_criteria, c=collection)

    number_of_records = len(record_IDs)

    if page_to_display < 1:
        page_to_display = 1

    last_page_number = number_of_records/RECORDS_PER_PAGE+1
    if page_to_display > last_page_number:
        page_to_display = last_page_number

    first_record_to_display = RECORDS_PER_PAGE * (page_to_display - 1)
    last_record_to_display = (RECORDS_PER_PAGE*page_to_display) - 1
    record_IDs = record_IDs[first_record_to_display:last_record_to_display]

    records_content = []

    for record_id in record_IDs:
        formated_record = _get_formated_record(record_id=record_id,
                             output_format=output_format,
                             update_commands = update_commands,
                             language=language, outputTags=outputTags)

        records_content.append((record_id, formated_record))


    result = multiedit_templates.search_results(records = records_content,
                                                number_of_records = number_of_records,
                                                current_page = page_to_display,
                                                records_per_page = RECORDS_PER_PAGE,
                                                language = language,
                                                output_format=output_format)
    return result

def perform_request_submit_changes(search_criteria, update_commands, language, upload_mode, tag_list, collection, req):
    """Submits changes for upload into database.

    @param search_criteria: search criteria used in the test search
    @param update_commands: list of commands used to update record contents
    @param language: the language used to format the content
    """

    status, file_path = _submit_changes_to_bibupload(search_criteria, update_commands, upload_mode, tag_list, collection, req)

    return multiedit_templates.changes_applied(status, file_path)

def _get_formated_record(record_id, output_format, update_commands, language, outputTags=""):
    """Returns a record in a given format

    @param record_id: the ID of record to format
    @param output_format: an output format code (or short identifier for the output format)
    @param update_commands: list of commands used to update record contents
    @param language: the language to use to format the record
    """
    updated_record = _get_updated_record(record_id, update_commands)

    xml_record = bibrecord.record_xml_output(updated_record)

    if "hm" == output_format:
        result = "<pre>\n"
        marc_record = _create_marc(xml_record)
        if "All tags" not in outputTags or not outputTags:
            for line in marc_record.split('\n')[:-1]:
                for tag in outputTags:
                    if tag in line.split()[0]:
                        result += "%09d " % record_id + line.strip() + '\n'
        else:
            for line in marc_record.split('\n')[:-1]:
                result += "%09d " % record_id + line.strip() + '\n'

        result += "</pre>"
        return result

    result = bibformat.format_record(recID=None,
                                     of=output_format,
                                     xml_record=xml_record,
                                     ln=language)
    return result

# FIXME: Remove this method as soon as the formatting for MARC is
# implemented in bibformat

from invenio import xmlmarc2textmarclib as xmlmarc2textmarclib
def _create_marc(records_xml):
    """Creates MARC from MARCXML.

    @param records_xml: MARCXML containing information about the records

    @return: string containing information about the records
    in MARC format
    """
    aleph_marc_output = ""

    records = bibrecord.create_records(records_xml)
    for (record, status_code, list_of_errors) in records:
        # The system number is in field 970a
        # By this reason it should exist in the MARC XML
        # otherwise it will be None in the output ALEPH marc
        sysno_options = {"text-marc":0}
        sysno = xmlmarc2textmarclib.get_sysno_from_record(record,
                                                              sysno_options)

        if sysno == None:
            sysno = ""

        options = {"aleph-marc":0, "correct-mode":1, "append-mode":0,
                   "delete-mode":0, "insert-mode":0, "replace-mode":0,
                   "text-marc":1}
        aleph_record = xmlmarc2textmarclib.create_marc_record(record,
                                                              sysno,
                                                              options)
        aleph_marc_output += aleph_record

    return aleph_marc_output

def _submit_changes_to_bibupload(search_criteria, update_commands, upload_mode, tag_list, collection, req):
    """This methods takes care of submitting the changes to the server
    through bibupload.

    @param search_criteria: the search criteria used for filtering the
    records. The changes will be applied to all the records matching
    the criteria

    @param update_commands: the commands defining the changes. These
    commands perform the necessary changes before the records are submitted
    """
    if collection == "Any collection":
        collection = ""
    record_IDs = search_engine.perform_request_search(p=search_criteria, c=collection)
    num_records = len(record_IDs)

    updated_records = []

    for current_id in record_IDs:
        current_updated_record = _get_updated_record(current_id, update_commands)
        updated_records.append(current_updated_record)

    file_path = _get_file_path_for_bibupload()
    _save_records_xml(updated_records, file_path, upload_mode, tag_list)
    return _upload_file_with_bibupload(file_path, upload_mode, num_records, req)

def _get_updated_record(record_id, update_commands):
    """Applies all the changes specified by the commands
    to record identified by record_id and returns resulting record

    @param record_id: identifier of the record that will be updated
    @param update_commands: list of commands used to update record contents
    @return: updated record structure"""

    record = search_engine.get_record(recid=record_id)

    for current_command in update_commands:
        current_command.process_record(record)

    return record

def _upload_file_with_bibupload(file_path, upload_mode, num_records, req):
    """
    Uploads file with bibupload

       @param file_path: path to the file where the XML will be saved.
       @param upload_mode: -c for correct or -r for replace
       @return tuple formed by status of the upload:
           0-changes to be made instantly
           1-changes to be made only in limited hours
           2-user is superadmin. Changes made in limited hours
           3-no rights to upload
           and the upload file path
    """
    if num_records < CFG_BIBEDITMULTI_LIMIT_INSTANT_PROCESSING:
        task_low_level_submission('bibupload', 'multiedit', '-P', '5', upload_mode, '%s' % file_path)
        return (0, file_path)
    elif num_records < CFG_BIBEDITMULTI_LIMIT_DELAYED_PROCESSING:
        task_low_level_submission('bibupload', 'multiedit', '-P', '5', upload_mode, '-L', CFG_BIBEDITMULTI_LIMIT_DELAYED_PROCESSING_TIME,'%s' % file_path)
        return (1, file_path)
    else:
        user_info = collect_user_info(req)
        if isUserSuperAdmin(user_info):
            task_low_level_submission('bibupload', 'multiedit', '-P', '5', upload_mode, '-L', CFG_BIBEDITMULTI_LIMIT_DELAYED_PROCESSING_TIME, '%s' % file_path)
            return (2, file_path)
        return (3, file_path)

def _get_file_path_for_bibupload():
    """Returns file path for saving a file for bibupload """

    current_time = strftime("%Y%m%d%H%M%S")
    return "%s/%s_%s%s" % (CFG_TMPDIR, "multiedit_", current_time, ".xml")

def _save_records_xml(records, file_path, upload_mode, tag_list):
    """Saves records in a file in XML format

    @param records: list of records (record structures)
    @param file_path: path to the file where the XML will be saved."""

    output_file = None
    try:
        output_file = open(file_path, "w")

        if upload_mode == "-c":
            for record in records:
                for tag in record.keys():
                    if tag not in tag_list:
                        del(record[tag])

        records_xml = bibrecord.print_recs(records)

        output_file.write(records_xml)
    finally:
        if not output_file is None:
            output_file.close()
