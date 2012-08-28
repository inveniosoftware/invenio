## This file is part of Invenio.
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

"""Invenio Multiple Record Editor web interface."""

__revision__ = "$Id"

__lastupdated__ = """$Date: 2008/08/12 09:26:46 $"""

from invenio.jsonutils import json, json_unicode_to_utf8
from invenio.webinterface_handler import WebInterfaceDirectory, \
                                         wash_urlargd
from invenio.webpage import page
from invenio.messages import gettext_set_language
from invenio import bibeditmulti_engine as multi_edit_engine

from invenio.webuser import page_not_authorized
from invenio.access_control_engine import acc_authorize_action

class _ActionTypes:
    """Define the available action types"""
    test_search = "testSearch"
    display_detailed_record = "displayDetailedRecord"
    preview_results = "previewResults"
    display_detailed_result = "displayDetailedResult"
    submit_changes = "submitChanges"

    def __init__(self):
        """Nothing to init"""
        pass

class _FieldActionTypes:
    """Define the available action types"""
    add = "0"
    delete = "1"
    update = "2"

    def __init__(self):
        """Nothing to init"""
        pass

class _SubfieldActionTypes:
    """Define the available action types"""
    add = "0"
    delete = "1"
    replace_content = "2"
    replace_text = "3"

    def __init__(self):
        """Nothing to init"""
        pass

class WebInterfaceMultiEditPages(WebInterfaceDirectory):
    """Defines the set of /multiedit pages."""

    _exports = [""]

    _action_types = _ActionTypes()

    _field_action_types = _FieldActionTypes()
    _subfield_action_types = _SubfieldActionTypes()


    _JSON_DATA_KEY = "jsondata"

    def index(self, req, form):
        """ The function called by default"""

        argd = wash_urlargd(form, {
                                   self._JSON_DATA_KEY: (str, ""),
                                   })

        # load the right message language
        language = argd["ln"]
        _ = gettext_set_language(language)

        # check user credentials
        (auth_code, auth_msg) = acc_authorize_action(req, "runbibeditmulti")
        if 0 != auth_code:
            return page_not_authorized(req = req,
                                       ln = language,
                                       text = auth_msg)

        if argd[self._JSON_DATA_KEY]:
            return self._process_json_request(form, req)

        body = multi_edit_engine.perform_request_index(language)
        title = _("Multi-Record Editor")
        metaheaderadd = multi_edit_engine.get_scripts()
        metaheaderadd = metaheaderadd + multi_edit_engine.get_css()

        return page(title = title,
            metaheaderadd = metaheaderadd,
            body = body,
            req = req,
            language = language)

    __call__ = index

    def _process_json_request(self, form, req):
        """Takes care about the json requests."""

        argd = wash_urlargd(form, {
                           self._JSON_DATA_KEY: (str, ""),
                           })

        # load json data
        json_data_string = argd[self._JSON_DATA_KEY]
        json_data_unicode = json.loads(json_data_string)
        json_data = json_unicode_to_utf8(json_data_unicode)

        language = json_data["language"]
        search_criteria = json_data["searchCriteria"]
        output_tags = json_data["outputTags"]
        output_tags = output_tags.split(',')
        output_tags = [tag.strip() for tag in output_tags]
        action_type = json_data["actionType"]
        current_record_id = json_data["currentRecordID"]
        commands = json_data["commands"]
        output_format = json_data["outputFormat"]
        page_to_display = json_data["pageToDisplay"]
        collection = json_data["collection"]
        compute_modifications = json_data["compute_modifications"]

        json_response = {}
        if action_type == self._action_types.test_search:
            json_response.update(multi_edit_engine.perform_request_test_search(
                                                    search_criteria,
                                                    [],
                                                    output_format,
                                                    page_to_display,
                                                    language,
                                                    output_tags,
                                                    collection))
            json_response['display_info_box'] = 1
            json_response['info_html'] = ""
            return json.dumps(json_response)

        elif action_type == self._action_types.display_detailed_record:
            json_response.update(multi_edit_engine.perform_request_detailed_record(
                                                    current_record_id,
                                                    [],
                                                    output_format,
                                                    language))
            return json.dumps(json_response)

        elif action_type == self._action_types.preview_results:
            commands_list, upload_mode, tag_list = self._create_commands_list(commands)
            json_response = {}
            json_response.update(multi_edit_engine.perform_request_test_search(
                                                    search_criteria,
                                                    commands_list,
                                                    output_format,
                                                    page_to_display,
                                                    language,
                                                    output_tags,
                                                    collection,
                                                    compute_modifications,
                                                    upload_mode))
            return json.dumps(json_response)

        elif action_type == self._action_types.display_detailed_result:
            commands_list, upload_mode, tag_list = self._create_commands_list(commands)
            json_response.update(multi_edit_engine.perform_request_detailed_record(
                                                    current_record_id,
                                                    commands_list,
                                                    output_format,
                                                    language))
            return json.dumps(json_response)

        elif action_type == self._action_types.submit_changes:
            commands_list, upload_mode, tag_list = self._create_commands_list(commands)
            json_response.update(multi_edit_engine.perform_request_submit_changes(search_criteria, commands_list, language, upload_mode, tag_list, collection, req))
            return json.dumps(json_response)

        # In case we obtain wrong action type we return empty page.
        return " "

    def _create_subfield_commands_list(self, subfields):
        """Creates the list of commands for the given subfields.

        @param subfields: json structure containing information about
        the subfileds. This data is used for creating the commands.

        @return: list of subfield commands.
        """
        commands_list = []

        upload_mode_replace = False

        for current_subfield in subfields:
            action = current_subfield["action"]
            subfield_code = current_subfield["subfieldCode"]
            value = current_subfield["value"]
            new_value = current_subfield["newValue"]
            condition = current_subfield["condition"]
            condition_exact_match = False
            condition_does_not_exist = False
            if int(current_subfield["conditionSubfieldExactMatch"]) == 0:
                condition_exact_match = True
            if int(current_subfield["conditionSubfieldExactMatch"]) == 2:
                condition_does_not_exist = True
            condition_subfield = current_subfield["conditionSubfield"]

            if action == self._subfield_action_types.add:
                subfield_command = multi_edit_engine.AddSubfieldCommand(subfield_code, value, condition=condition, condition_exact_match=condition_exact_match, condition_does_not_exist=condition_does_not_exist, condition_subfield=condition_subfield)
            elif action == self._subfield_action_types.delete:
                subfield_command = multi_edit_engine.DeleteSubfieldCommand(subfield_code, condition=condition, condition_exact_match=condition_exact_match, condition_does_not_exist=condition_does_not_exist, condition_subfield=condition_subfield)
                upload_mode_replace = True
            elif action == self._subfield_action_types.replace_content:
                subfield_command = multi_edit_engine.ReplaceSubfieldContentCommand(subfield_code, value, condition=condition, condition_exact_match=condition_exact_match, condition_does_not_exist=condition_does_not_exist, condition_subfield=condition_subfield)
            elif action == self._subfield_action_types.replace_text:
                subfield_command = multi_edit_engine.ReplaceTextInSubfieldCommand(subfield_code, value, new_value, condition=condition, condition_exact_match=condition_exact_match, condition_does_not_exist=condition_does_not_exist, condition_subfield=condition_subfield)
            else:
                subfield_command = multi_edit_engine.BaseFieldCommand(subfield_code, value, new_value)

            commands_list.append(subfield_command)

        return commands_list, upload_mode_replace


    def _create_commands_list(self, commands_json_structure):
        """Creates a list of commands recognized by multiedit engine"""

        commands_list = []

        upload_mode = '-c'
        tag_list = ["001"]
        for current_field in commands_json_structure:

            tag = current_field["tag"]
            tag_list.append(tag)
            ind1 = current_field["ind1"]
            ind2 = current_field["ind2"]
            action = current_field["action"]
            conditionSubfield = current_field["conditionSubfield"]
            condition = current_field["condition"]
            condition_exact_match = False
            condition_does_not_exist = False
            if int(current_field["conditionSubfieldExactMatch"]) == 0:
                condition_exact_match = True
            if int(current_field["conditionSubfieldExactMatch"]) == 2:
                condition_does_not_exist = True

            subfields = current_field["subfields"]
            subfield_commands, upload_mode_replace = self._create_subfield_commands_list(subfields)
            if upload_mode_replace:
                upload_mode = '-r'
            # create appropriate command depending on the type
            if action == self._field_action_types.add:
                command = multi_edit_engine.AddFieldCommand(tag, ind1, ind2, subfield_commands)
            elif action == self._field_action_types.delete:
                command = multi_edit_engine.DeleteFieldCommand(tag, ind1, ind2, subfield_commands, conditionSubfield, condition, condition_exact_match, condition_does_not_exist)
                upload_mode = '-r'
            elif action == self._field_action_types.update:
                command = multi_edit_engine.UpdateFieldCommand(tag, ind1, ind2, subfield_commands)
            else:
                # if someone send wrong action type, we use empty command
                command = multi_edit_engine.BaseFieldCommand()

            commands_list.append(command)

        return commands_list, upload_mode, tag_list

