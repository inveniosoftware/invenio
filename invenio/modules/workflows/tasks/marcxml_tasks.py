# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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

"""Set of function for harvesting."""

import os
import glob
import traceback

from six import callable


def approve_record(obj, eng):
    """Will add the approval widget to the record.

    The workflow need to be halted to use the
    action in the holdingpen.
    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    try:
        eng.halt(action="approval",
                 msg='Record needs approval')
    except KeyError:
        # Log the error
        obj.extra_data["_error_msg"] = 'Could not assign action'


def convert_record_to_bibfield(obj, eng):
    """Convert a record in data into a 'dictionary' thanks to BibField.

    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    from invenio.modules.workflows.utils import convert_marcxml_to_bibfield
    obj.data = convert_marcxml_to_bibfield(obj.data)
    eng.log.info("Field conversion succeeded")


def get_files_list(path, parameter):
    """Function returning the list of file in a directory."""
    def _get_files_list(obj, eng):
        if callable(parameter):
            unknown = parameter
            while callable(unknown):
                unknown = unknown(obj, eng)

        else:
            unknown = parameter
        result = glob.glob1(path, unknown)
        for i in range(0, len(result)):
            result[i] = path + os.sep + result[i]
        return result

    return _get_files_list


def set_obj_extra_data_key(key, value):
    """Task setting the value of an object extra data key."""
    def _set_obj_extra_data_key(obj, eng):
        my_value = value
        my_key = key
        if callable(my_value):
            while callable(my_value):
                my_value = my_value(obj, eng)
        if callable(my_key):
            while callable(my_key):
                my_key = my_key(obj, eng)
        obj.extra_data[str(my_key)] = my_value

    return _set_obj_extra_data_key


def get_obj_extra_data_key(name):
    """Task returning the value of an object extra data key."""
    def _get_obj_extra_data_key(obj, eng):
        return obj.extra_data[name]

    return _get_obj_extra_data_key


def get_eng_extra_data_key(name):
    """Task returning the value of an engine extra data key."""
    def _get_eng_extra_data_key(obj, eng):
        return eng.extra_data[name]

    return _get_eng_extra_data_key


def get_data(obj, eng):
    """Task returning data of the object."""
    return obj.data


def convert_record(stylesheet="oaidc2marcxml.xsl"):
    """Convert the object data, if XML, using the given stylesheet.

    :param stylesheet: which stylesheet to use
    :return: function to convert record
    :raise WorkflowError:
    """
    def _convert_record(obj, eng):
        from invenio.modules.workflows.errors import WorkflowError
        from invenio.legacy.bibconvert.xslt_engine import convert

        eng.log.info("Starting conversion using %s stylesheet" %
                     (stylesheet,))

        try:
            obj.data = convert(obj.data, stylesheet)
        except Exception as e:
            msg = "Could not convert record: %s\n%s" % \
                  (str(e), traceback.format_exc())
            obj.extra_data["_error_msg"] = msg
            raise WorkflowError("Error: %s" % (msg,),
                                id_workflow=eng.uuid,
                                id_object=obj.id)

    return _convert_record


def update_last_update(repository_list):
    """Perform the update of the update date."""
    from invenio.legacy.oaiharvest.dblayer import update_lastrun

    def _update_last_update(obj, eng):
        if "_should_last_run_be_update" in obj.extra_data:
            if obj.extra_data["_should_last_run_be_update"]:
                repository_list_to_process = repository_list
                if not isinstance(repository_list_to_process, list):
                    if callable(repository_list_to_process):
                        while callable(repository_list_to_process):
                            repository_list_to_process = repository_list_to_process(
                                obj, eng)
                    else:
                        repository_list_to_process = [
                            repository_list_to_process]
                for repository in repository_list_to_process:
                    update_lastrun(repository["id"])

    return _update_last_update


def quick_match_record(obj, eng):
    """Retrieve the record Id from a record.

    Retrieve the record Id from a record by using tag 001 or SYSNO or OAI ID or
    DOI tag. opt_mod is the desired mode.

    001 fields even in the insert mode

    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    from invenio.legacy.bibupload.engine import (find_record_from_recid,
                                                 find_record_from_sysno,
                                                 find_records_from_extoaiid,
                                                 find_record_from_oaiid,
                                                 find_record_from_doi)
    from invenio.modules.records.api import Record

    identifier_function_to_check = {'recid': find_record_from_recid,
                                    'system_number': find_record_from_sysno,
                                    'oaiid': find_record_from_oaiid,
                                    'system_control_number': find_records_from_extoaiid,
                                    'doi': find_record_from_doi}

    record = Record(obj.data.dumps())
    try:
        identifiers = record.persistent_identifiers
    except Exception as e:
        # if anything goes wrong, assume we need to get it manually.
        eng.log.error("Problem with getting identifiers: %s\n%s"
                      % (str(e), traceback.format_exc()))
        identifiers = []

    obj.extra_data["persistent_ids"] = identifiers

    identifier_dict = {}
    for name, value in identifiers:
        value_dict = {}
        for dic in value:
            value_dict.update(dic)
        identifier_dict[name] = value_dict

    if "recid" in identifier_dict:
        # If there is a recid, we are good, right?
        obj.extra_data["persistent_ids"]["recid"] = identifier_dict["recid"]
        return True

    # So if there is no explicit recid key, then maybe we can find the record
    # using any of the other stable identifiers defined.
    found_recid = False
    for name, func in identifier_function_to_check.iteritems():
        if name in identifier_dict:
            if name in identifier_dict[name]:
                # To get {"doi": {"doi": val}}
                found_recid = func(identifier_dict[name][name])
            elif "value" in identifier_dict[name]:
                # To get {"doi": {"value": val}}
                found_recid = func(identifier_dict[name]["value"])

            if found_recid:
                break

    if found_recid:
        obj.extra_data["persistent_ids"]["recid"] = found_recid
        return True
    return False


def upload_record(mode="ir"):
    """Perform the upload step."""
    def _upload_record(obj, eng):
        from invenio.legacy.bibsched.bibtask import task_low_level_submission
        eng.log_info("Saving data to temporary file for upload")
        filename = obj.save_to_file()
        params = ["-%s" % (mode,), filename]
        task_id = task_low_level_submission("bibupload", "bibworkflow",
                                            *tuple(params))
        eng.log_info("Submitted task #%s" % (task_id,))

    return _upload_record
