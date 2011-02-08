## Copyright (C) 2009, 2010, 2011 CERN.
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

"""Invenio Multiple Record Editor Engine.

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

from invenio.config import CFG_TMPSHAREDDIR, CFG_BIBEDITMULTI_LIMIT_INSTANT_PROCESSING,\
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
    def __init__(self, subfield, value = "", new_value = "", condition = "", condition_exact_match=True, condition_subfield = ""):
        """Initialization."""
        self._subfield = subfield
        self._value = value
        self._new_value = new_value
        self._condition = condition
        self._condition_subfield = condition_subfield
        self._condition_exact_match = condition_exact_match
        self._modifications = 0

    def process_field(self, record, tag, field_number):
        """Make changes to a record.

        By default this method is empty.

        Every specific command provides its own implementation"""
        pass

    def _subfield_condition_match(self, subfield_value):
        """Check if the condition is met for the given subfield value
        in order to act only on certain subfields
        @return True if condition match, False if condition does not match
        """
        if self._condition_exact_match:
            # exact matching
            if self._condition == subfield_value:
                return True
        else:
            # partial matching
            if self._condition in subfield_value:
                return True
        return False

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
                        # only modify subfields that match the condition
                        if subfield[0] == self._subfield:
                            for subfield in field[0]:
                                if self._condition_subfield == subfield[0]:
                                    if self._subfield_condition_match(subfield[1]):
                                        self._add_subfield_modification()
                                        callback(record, tag, field_number, subfield_index)
                    elif subfield[0] == self._subfield:
                        self._add_subfield_modification()
                        callback(record, tag, field_number, subfield_index)
                    subfield_index = subfield_index+1

    def _add_subfield_modification(self):
        """Keep a record of the number of modifications made to subfields"""
        self._modifications += 1

# specific commands for subfields

class AddSubfieldCommand(BaseSubfieldCommand):
    """Add subfield to a given field"""
    def _perform_on_all_matching_subfields_add_subfield(self, record, tag, field_number, callback):
        if tag not in record.keys():
            return
        for field in record[tag]:
            if field[4] == field_number:
                for subfield in field[0]:
                    if self._condition_subfield == subfield[0]:
                        if self._subfield_condition_match(subfield[1]):
                            self._add_subfield_modification()
                            callback(record, tag, field_number, None)

    def process_field(self, record, tag, field_number):
        """@see: BaseSubfieldCommand.process_field"""
        action = lambda record, tag, field_number, subfield_index: \
                      bibrecord.record_add_subfield_into(record, tag,
                                         self._subfield, self._value,
                                         None,
                                         field_position_global=field_number)
        if self._condition != 'condition':
            self._perform_on_all_matching_subfields_add_subfield(record, tag,
                                                                field_number, action)
        else:
            self._add_subfield_modification()
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
            #update the subfield if needed
            if new_value != field_value:
                bibrecord.record_modify_subfield(record, tag,
                                                self._subfield, new_value,
                                                subfield_index,
                                                field_position_global=field_number)
            else:
                #No modification ocurred, update modification counter
                self._modifications -= 1

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
        self._modifications = 0

    def process_record(self, record):
        """Make changes to a record.

        By default this method is empty.

        Every specific command provides its own implementation"""
        pass

    def _apply_subfield_commands_to_field(self, record, field_number):
        """Applies all subfield commands to a given field"""
        field_modified = False
        for subfield_command in self._subfield_commands:
            current_modifications = subfield_command._modifications
            subfield_command.process_field(record, self._tag, field_number)
            if subfield_command._modifications > current_modifications:
                field_modified = True
        if field_modified:
            self._modifications += 1

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

    def __init__(self, tag, ind1, ind2, subfield_commands, conditionSubfield="", condition="", condition_exact_match=True):
        BaseFieldCommand.__init__(self, tag, ind1, ind2, subfield_commands)
        self._conditionSubfield = conditionSubfield
        self._condition = condition
        self._condition_exact_match = condition_exact_match

    def _delete_field_condition(self, record):
        """Checks if a subfield meets the condition for the
        field to be deleted
        """
        try:
            for field in record[self._tag]:
                for subfield in field[0]:
                    if subfield[0] == self._conditionSubfield:
                        if self._condition_exact_match:
                            if self._condition == subfield[1]:
                                bibrecord.record_delete_field(record, self._tag, self._ind1, self._ind2, field_position_global=field[4])
                                self._modifications += 1
                                break
                        else:
                            if self._condition in subfield[1]:
                                bibrecord.record_delete_field(record, self._tag, self._ind1, self._ind2, field_position_global=field[4])
                                self._modifications += 1
                                break
        except KeyError:
            pass

    def process_record(self, record):
        """@see: BaseFieldCommand.process_record"""
        if self._condition:
            self._delete_field_condition(record)
        else:
            bibrecord.record_delete_field(record, self._tag, self._ind1, self._ind2)
            self._modifications += 1

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

    response = {}
    record_content = _get_formated_record(record_id=record_id,
                                output_format=output_format,
                                update_commands = update_commands,
                                language=language)

    response['search_html'] = multiedit_templates.detailed_record(record_content, language)
    return response

def perform_request_test_search(search_criteria, update_commands, output_format, page_to_display, 
                                language, outputTags, collection="", compute_modifications = 0):
    """Returns the results of a test search.

    @param search_criteria: search criteria used in the test search
    @type search_criteria: string
    @param update_commands: list of commands used to update record contents
    @type update_commands: list of objects
    @param output_format: specifies the output format as expected from bibformat
    @type output_format: string (hm, hb, hd, xm, xn, hx)
    @param page_to_display: the number of the page that should be displayed to the user
    @type page_to_display: int
    @param language: the language used to format the content
    @param outputTags: list of tags to be displayed in search results
    @type outputTags: list of strings
    @param collection: collection to be filtered in the results
    @type collection: string
    @param compute_modifications: if equals 0 do not compute else compute modifications
    @type compute_modifications: int
    """
    RECORDS_PER_PAGE = 100
    response = {}

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

    if not compute_modifications:
        record_IDs = record_IDs[first_record_to_display:last_record_to_display + 1]

    records_content = []

    record_modifications = 0
    for record_id in record_IDs:
        current_modifications = [current_command._modifications for current_command in update_commands]
        formated_record = _get_formated_record(record_id=record_id,
                             output_format=output_format,
                             update_commands = update_commands,
                             language=language, outputTags=outputTags)
        new_modifications = [current_command._modifications for current_command in update_commands]
        if new_modifications > current_modifications:
            record_modifications += 1

        records_content.append((record_id, formated_record))


    total_modifications = []
    if compute_modifications:
        field_modifications = 0
        subfield_modifications = 0
        for current_command in update_commands:
            field_modifications += current_command._modifications
            for subfield_command in current_command._subfield_commands:
                subfield_modifications += subfield_command._modifications
        if record_modifications:
            total_modifications.append(record_modifications)
            total_modifications.append(field_modifications)
            total_modifications.append(subfield_modifications)
        records_content = records_content[first_record_to_display:last_record_to_display + 1]

    response['display_info_box'] = compute_modifications
    response['info_html'] = multiedit_templates.info_box(language = language,
                                                total_modifications = total_modifications)
    response['search_html'] = multiedit_templates.search_results(records = records_content,
                                                number_of_records = number_of_records,
                                                current_page = page_to_display,
                                                records_per_page = RECORDS_PER_PAGE,
                                                language = language,
                                                output_format=output_format)
    return response

def perform_request_submit_changes(search_criteria, update_commands, language, upload_mode, tag_list, collection, req):
    """Submits changes for upload into database.

    @param search_criteria: search criteria used in the test search
    @param update_commands: list of commands used to update record contents
    @param language: the language used to format the content
    """

    response = {}
    status, file_path = _submit_changes_to_bibupload(search_criteria, update_commands, upload_mode, tag_list, collection, req)

    response['search_html'] = multiedit_templates.changes_applied(status, file_path)
    return response

def _get_record_diff(record_id, record, updated_record):
    """ Returns the new record with formating to display
    changes in the search results
    @param record: Record without modifications
    @type record: Record object
    @param updated_record: Record with modifications
    @type updated_record: Record object
    @return: formated record with changes highlighted
    @rtype: string
    """
    import itertools

    record_xml = bibrecord.record_xml_output(record)
    record_marc = cgi.escape(_create_marc(record_xml))
    record_split = record_marc.split('\n')[:-1]

    updated_record_xml = bibrecord.record_xml_output(updated_record)
    updated_record_marc = cgi.escape(_create_marc(updated_record_xml))
    updated_record_split = updated_record_marc.split('\n')[:-1]
    
    result = ''
    if (len(updated_record_split) == len(record_split)) and (record.keys() == updated_record.keys()):
        for line_updated, line in itertools.izip(updated_record_split, record_split):
            line_updated_split = line_updated.split("$$")
            line_split = line.split("$$")
            for i in xrange(len(line_updated_split)):
                if line_updated_split[i] not in line_split:
                    line_updated_split[i] = "<strong style=\"color: red\">" + line_updated_split[i] + "</strong>"
            new_line = "$$".join(line_updated_split)
            result += "%09d " % record_id + new_line.strip() + '\n'
    else:
        for i in xrange(len(updated_record_split)):
            if updated_record_split[i] not in record_split:
                updated_record_split[i] =  "<strong style=\"color: red\">" + updated_record_split[i].strip() + "</strong>"
            result += "%09d " % record_id + updated_record_split[i].strip() + '\n'
    return result


def _get_formated_record(record_id, output_format, update_commands, language, outputTags=""):
    """Returns a record in a given format

    @param record_id: the ID of record to format
    @param output_format: an output format code (or short identifier for the output format)
    @param update_commands: list of commands used to update record contents
    @param language: the language to use to format the record
    """
    updated_record = _get_updated_record(record_id, update_commands)
    xml_record = bibrecord.record_xml_output(updated_record)

    old_record = search_engine.get_record(recid=record_id)
    if "hm" == output_format:
        result = "<pre>\n"
        if "All tags" not in outputTags or not outputTags:
            diff_result = _get_record_diff(record_id, old_record, updated_record)
            for line in diff_result.split('\n')[:-1]:
                for tag in outputTags:
                    if tag in line.split()[1]:
                        result += line.strip() + '\n'
                    elif '<strong' in line:
                        if tag in line.split()[3]:
                            result += line.strip() + '\n'
        else:
            result += _get_record_diff(record_id, old_record, updated_record)

        result += "</pre>"
        return result

    result = bibformat.format_record(recID=None,
                                     of=output_format,
                                     xml_record=xml_record,
                                     ln=language)
    return result

# FIXME: Remove this method as soon as the formatting for MARC is
# implemented in bibformat

from invenio import xmlmarc2textmarc as xmlmarc2textmarc
def _create_marc(records_xml):
    """Creates MARC from MARCXML.

    @param records_xml: MARCXML containing information about the records

    @return: string containing information about the records
    in MARC format
    """
    aleph_marc_output = ""

    records = bibrecord.create_records(records_xml)
    for (record, status_code, list_of_errors) in records:

        sysno = ""

        options = {"aleph-marc":0, "correct-mode":1, "append-mode":0,
                   "delete-mode":0, "insert-mode":0, "replace-mode":0,
                   "text-marc":1}

        aleph_record = xmlmarc2textmarc.create_marc_record(record,
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
    return "%s/%s_%s%s" % (CFG_TMPSHAREDDIR, "multiedit", current_time, ".xml")

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
