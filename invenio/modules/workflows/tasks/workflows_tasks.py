# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of t
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111 1307, USA.

"""Set of function for sub workflows management."""

from functools import wraps
from time import sleep

from invenio.modules.workflows.errors import WorkflowError
from invenio.modules.workflows.models import BibWorkflowEngineLog

from six import callable, string_types


def interrupt_workflow(obj, eng):
    """
    Small function mailny for testing which stops the workflow.

    The object will be in the state HALTED.

    :param obj: BibworkflowObject to process
    :param eng: BibWorkflowEngine processing the object
    """
    eng.halt("interrupting workflow.")


def get_nb_workflow_created(obj, eng):
    """Return the number of workflows created.

    :param obj: BibworkflowObject to process
    :param eng: BibWorkflowEngine processing the object
    :return the number of workflow created since the last clean.
    """
    try:
        return eng.extra_data["_nb_workflow"]
    except KeyError:
        return "0"


def num_workflow_running_greater(num):
    """Correct the problem of saturation.

    Function has been created to correct the problem of saturation
    of messaging queue which  can lead to the complete destruction of
    the computing node.

    This function should be used with the function to create workflow and wait
    for workflow to finish.

    This allows to control the number of workflow in the messaging queue

    This function will just return True if the number of workflow
    in the messaging queue is higher than num or False.

    :param num: the number that you want to compare with the number of workflows in
    the message queue
    :type num: number
    :return True if you need to wait ( number of workflow in message queue greater
    than num) or false if you don't need to wait.
    """
    @wraps(num_workflow_running_greater)
    def _num_workflow_running_greater(obj, eng):
        try:
            if (eng.extra_data["_nb_workflow"] - eng.extra_data["_nb_workflow_finish"]) > num:
                return True
            else:
                return False
        except KeyError:
            return False

    return _num_workflow_running_greater


def get_nb_workflow_running(obj, eng):
    """Get number of workflow in the message queue."""
    try:
        return eng.extra_data["_nb_workflow"] - eng.extra_data["_nb_workflow_finish"]
    except KeyError:
        return "0"


def start_async_workflow(workflow_to_run="",
                         preserve_data=True,
                         preserve_extra_data_keys=None,
                         get_workflow_from=None,
                         **kwargs):
    """Run a new asynchronous workflow on new objects.

    This function allows you to run a new asynchronous workflow. This
    will be run asynchronously.

    The current object data will be preserved in the new object by default.

    Any extra data you with to transfer over from the current object to the
    new object should be specified via extra_data keys.

    :param workflow_to_run: name of the workflow to run.
    :type workflow_to_run: str

    :param preserve_data: should current object data be passed to new object?
    :type preserve_data: bool

    :param preserve_extra_data_keys: extra data from current object to preserve.
    :type preserve_extra_data_keys: list

    :param get_workflow_from_engine_definition: function that returns which
        workflow to run (optional).
    :type get_workflow_from_engine_definition: function
    """
    from ...workflows.models import BibWorkflowObject
    from invenio.modules.workflows.api import start_delayed

    @wraps(start_async_workflow)
    def _start_workflow(obj, eng):
        record_object = BibWorkflowObject.create_object()
        record_object.save()  # Saving to set default extra_data and data

        if preserve_extra_data_keys:
            record_object.extra_data = record_object.get_extra_data()
            for extra_data_key in preserve_extra_data_keys:
                record_object.extra_data[extra_data_key] = obj.extra_data[extra_data_key]
            record_object.set_extra_data(record_object.extra_data)

        if preserve_data:
            record_object.set_data(obj.data)
        if not workflow_to_run and get_workflow_from:
            # We get the workflow from the definition variables
            workflow = get_workflow_from(eng)
        else:
            workflow = workflow_to_run

        workflow_id = start_delayed(
            workflow,
            data=[record_object],
            stop_on_error=True,
            module_name=eng.module_name,
            **kwargs
        )

        eng.log.debug("New workflow '{0}' launched".format(workflow_to_run))
        try:
            eng.extra_data["_workflow_ids"].append(workflow_id)
            obj.extra_data["objects_spawned"].append(record_object.id)
        except KeyError:
            eng.extra_data["_workflow_ids"] = [workflow_id]
            obj.extra_data["objects_spawned"] = [record_object.id]

        try:
            eng.extra_data["_nb_workflow"] += 1
        except KeyError:
            eng.extra_data["_nb_workflow"] = 1

        if "_nb_workflow_failed" not in eng.extra_data:
            eng.extra_data["_nb_workflow_failed"] = 0
        if "_nb_workflow_finish" not in eng.extra_data:
            eng.extra_data["_nb_workflow_finish"] = 0
        if "_uuid_workflow_crashed" not in eng.extra_data:
            eng.extra_data["_uuid_workflow_crashed"] = []
        if "_uuid_workflow_succeed" not in eng.extra_data:
            eng.extra_data["_uuid_workflow_succeed"] = []

    return _start_workflow


def wait_for_workflows_to_complete(obj, eng):
    """Wait all the asynchronous workflow launched.

    This function wait all the asynchronous workflow launched.
    It acts like a barrier.

    :param obj: BibworkflowObject being process
    :param eng: BibWorkflowEngine processing the object
    """
    if '_workflow_ids' in eng.extra_data:
        for workflow_id in eng.extra_data['_workflow_ids']:
            workflow_result_management(workflow_id, eng)
    else:
        eng.extra_data["_nb_workflow"] = 0
        eng.extra_data["_nb_workflow_failed"] = 0
        eng.extra_data["_nb_workflow_finish"] = 0


def wait_for_a_workflow_to_complete_obj(obj, eng):
    """Wait for the asynchronous workflow specified in obj.data (asyncresult).

    This function wait for the asynchronous workflow specified
    in obj.data (asyncresult)
    It acts like a barrier

    :param obj: BibworkflowObject to process
    :param eng: BibWorkflowEngine processing the object
    """
    if not obj.data:
        eng.extra_data["_nb_workflow"] = 0
        eng.extra_data["_nb_workflow_failed"] = 0
        eng.extra_data["_nb_workflow_finish"] = 0
        return None
    workflow_result_management(obj.data, eng)


def wait_for_a_workflow_to_complete(scanning_time=5.0):
    """Wait for a children workflow finished processing.

    This function wait for the asynchronous workflow specified in obj.data
    (asyncresult). It acts like a barrier.

    :param scanning_time: time value in second to define which interval
    is used, to look into the message queue for finished workflows.
    :type scanning_time: number
    :return:
    """
    @wraps(wait_for_a_workflow_to_complete)
    def _wait_for_a_workflow_to_complete(obj, eng):
        if '_workflow_ids' in eng.extra_data:
            to_wait = None
            i = 0
            while not to_wait and len(eng.extra_data["_workflow_ids"]) > 0:
                for i in range(0, len(eng.extra_data["_workflow_ids"])):
                    if eng.extra_data["_workflow_ids"][i].status == "SUCCESS":
                        to_wait = eng.extra_data["_workflow_ids"][i]
                        break
                    if eng.extra_data["_workflow_ids"][i].status == "FAILURE":
                        to_wait = eng.extra_data["_workflow_ids"][i]
                        break
                sleep(scanning_time)
            if not to_wait:
                return None
            workflow_result_management(to_wait, eng)

            del eng.extra_data["_workflow_ids"][i]
        else:
            eng.extra_data["_nb_workflow"] = 0
            eng.extra_data["_nb_workflow_failed"] = 0
            eng.extra_data["_nb_workflow_finish"] = 0

        obj.update_task_results(
            "wait_for_a_workflow_to_complete",
            [
                {"name": "wait_for_a_workflow_to_complete",
                 "template": "workflows/results/default.html",
                 "result": {"finished": eng.extra_data["_nb_workflow_finish"],
                            "failed": eng.extra_data["_nb_workflow_failed"],
                            "total": eng.extra_data["_nb_workflow"]}}
            ]
        )

    return _wait_for_a_workflow_to_complete


def workflow_result_management(async_result, eng):
    """Factorize the code for delayed workflow management.

    :param async_result: asynchronous result that we want to query to
    get data.
    :param eng: workflow engine for logging and state change.
    """
    from invenio.modules.workflows.worker_result import uuid_to_workflow
    try:
        engine = async_result.get(uuid_to_workflow)
        eng.extra_data["_nb_workflow_finish"] += 1
        eng.extra_data["_uuid_workflow_succeed"].append(engine.uuid)
    except WorkflowError as e:
        eng.log.error("Error: Workflow failed %s" % str(e))
        workflowlog = BibWorkflowEngineLog.query.filter(
            BibWorkflowEngineLog.id_object == e.id_workflow
        ).filter(BibWorkflowEngineLog.log_type >= 40).all()

        for log in workflowlog:
            eng.log.error(log.message)

        for i in e.payload:
            eng.log.error(str(i))
        eng.extra_data["_uuid_workflow_crashed"].append(e.id_workflow)
        eng.extra_data["_nb_workflow_failed"] += 1
        eng.extra_data["_nb_workflow_finish"] += 1
    except Exception as e:
        eng.log.error("Error: Workflow failed %s" % str(e))
        eng.extra_data["_nb_workflow_failed"] += 1
        eng.extra_data["_nb_workflow_finish"] += 1


def write_something_generic(message, func):
    """Allow to write a message where you want.

    This function allows you to write a message where you want.
    This function support the multi-casting.

    Message is a string or a list of string  and function that will be concatenate
    in one and only string.

    Func is the list of the functions that will be used to send the message. The function
    should always take in parameter a string which is the message.

    :param func: the list of function that will be used to propagate the message
    :type func: list of functions or a functions.
    :param message: the message that you want to propagate
    :type message: list of strings and functions.
    """
    @wraps(write_something_generic)
    def _write_something_generic(obj, eng):
        if isinstance(message, string_types):
            if isinstance(func, list):
                for function in func:
                    function(message)
            else:
                func(message)
            return None

        if not isinstance(message, list):
            if callable(message):
                func_message = message
                while callable(func_message):
                    func_message = func_message(obj, eng)
                if isinstance(func, list):
                    for function in func:
                        function(func_message)
                else:
                    func(func_message)
            return None

        if len(message) > 0:
            temp = ""
            for func_message in message:
                if callable(func_message):
                    while callable(func_message):
                        func_message = func_message(obj, eng)
                    temp += str(func_message)
                elif isinstance(func_message, string_types):
                    temp += func_message
            if isinstance(func, list):
                for function in func:
                    function(temp)
            else:
                func(temp)
            return None

    _write_something_generic.hide = True
    return _write_something_generic


def get_list_of_workflows_to_wait(obj, eng):
    """Return a list of asyncresult.

     Return a list of asyncresult corresponding to running
     asynchrnous workflow.

    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    return eng.extra_data["_workflow_ids"]


def get_status_async_result_obj_data(obj, eng):
    """Return the status of the asyncresult in data.

    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    return obj.data.state


def get_workflows_progress(obj, eng):
    """Return the progress of sub workflows.

    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    try:
        return (eng.extra_data["_nb_workflow_finish"] * 100.0) / (eng.extra_data["_nb_workflow"])
    except KeyError:
        return "No progress (key missing)"
    except ZeroDivisionError:
        return "No workflows"


def workflows_reviews(stop_if_error=False, clean=True):
    """Give you a little review of you children workflows.

    This function can be used to stop the workflow if a child has crashed.

    :param clean: optional, allows the cleaning of data about workflow for example
    start again from clean basis.
    :type clean: bool
    :param stop_if_error: give to the function the indication it it should stop
    if a child workflow has crashed.
    :type stop_if_error: bool
    """
    @wraps(workflows_reviews)
    def _workflows_reviews(obj, eng):
        obj.update_task_results(
            "review_workflow",
            [
                {"name": "wait_for_a_workflow_to_complete",
                 "template": "workflows/results/default.html",
                 "result": {"finished": eng.extra_data["_nb_workflow_finish"],
                            "failed": eng.extra_data["_nb_workflow_failed"],
                            "total": eng.extra_data["_nb_workflow"]}}
            ]
        )

        eng.log.info("{0}/{1} finished successfully".format(
            eng.extra_data["_nb_workflow_finish"], eng.extra_data["_nb_workflow"]
        ))

        if eng.extra_data["_nb_workflow"] == 0:
            # Nothing has been harvested!
            eng.log.info("Nothing harvested.")
            return

        if eng.extra_data["_nb_workflow_failed"] and stop_if_error:
            raise WorkflowError(
                "%s / %s failed" % (eng.extra_data["_nb_workflow_failed"], eng.extra_data["_nb_workflow"]),
                eng.uuid, obj.id, payload=eng.extra_data["_uuid_workflow_crashed"])

        if clean:
            eng.extra_data["_nb_workflow_failed"] = 0
            eng.extra_data["_nb_workflow"] = 0
            eng.extra_data["_nb_workflow_finish"] = 0

    _workflows_reviews.description = 'Workflows reviews'
    return _workflows_reviews


def log_info(message):
    """A simple function to log a simple thing.

    If you want more sophisticated way, thanks to see
    the function write_something_generic.

    :param message: this value represent what we want to log,
    if message is a function then it will be executed.
    :type message: str or function
    :return:
    """
    @wraps(log_info)
    def _log_info(obj, eng):
        message_buffer = message
        while callable(message_buffer):
            message_buffer = message_buffer(obj, eng)
        eng.log.info(message_buffer)

    _log_info.description = "Log info"
    return _log_info


def get_workflow_from_engine_definition(eng):
    """Get the record_workflow defined in `WorkflowDefinitino.record_workflow`."""
    from ..registry import workflows
    from ..errors import WorkflowDefinitionError

    if eng.name not in workflows:
        # No workflow with that name exists
        raise WorkflowDefinitionError("Workflow '%s' does not exist"
                                      % (eng.name,),
                                      workflow_name=eng.name)
    workflow_name = workflows[eng.name].record_workflow
    eng.log.info("Found workflow '{0}' to execute.".format(workflow_name))
    return workflow_name
