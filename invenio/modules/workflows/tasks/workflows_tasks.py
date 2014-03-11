# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of t
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111 1307, USA.

import six

from invenio.modules.workflows.models import (BibWorkflowObject,
                                              BibWorkflowEngineLog)
from invenio.modules.workflows.api import start_delayed
from invenio.modules.workflows.errors import WorkflowError

from time import sleep


def interrupt_workflow(obj, eng):
    eng.halt("interrupting workflow.")

def get_nb_workflow_created(obj, eng):
    """
    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    try:
        return eng.extra_data["_nb_workflow"]
    except KeyError:
        return "0"


def num_workflow_running_greater(num):
    """

    :param num: the number that you want to compare with the number de workflow running
    :type num: number

    """

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
    """
    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    try:
        eng.log.error(str())
        return eng.extra_data["_nb_workflow"] - eng.extra_data["_nb_workflow_finish"]
    except KeyError:
        return "0"


def start_workflow(workflow_to_run="default", data=None, copy=True, **kwargs):
    """
     This function allow you to run a new asynchronous workflow, this
     will be run on the celery node configurer into invenio
     configuration.

     :param workflow_to_run: The first argument is the name of the workflow to run.

     :param data: The second one is the data to use for this workflow.

     :param copy: The copy parameter allow you to pass to the workflow  a copy
     of the obj at the moment of the call .

     :param kwargs: **kargs allow you to add some key:value into the extra data of
     the object.
     """

    def _start_workflow(obj, eng):

        myobject = BibWorkflowObject()

        if copy is True:
            myobject.copy(obj)
        if data is not None:
            myobject.set_data(data)
        extra = myobject.get_extra_data()
        myobject.set_extra_data(extra)
        myobject.data_type = "record"
        myobject.save()
        workflow_id = start_delayed(workflow_to_run, data=[myobject],
                                    stop_on_error=True, **kwargs)

        eng.log.info("Workflow launched")
        try:
            eng.extra_data["_workflow_ids"].append(workflow_id)
        except KeyError:
            eng.extra_data["_workflow_ids"] = [workflow_id]

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

    return _start_workflow


def wait_for_workflows_to_complete(obj, eng):
    """
    This function wait all the asynchronous workflow launched.
    It acts like a barrier

    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    if '_workflow_ids' in eng.extra_data:
        for workflow_id in eng.extra_data['_workflow_ids']:
            try:
                workflow_id.get()
                eng.extra_data["_nb_workflow_finish"] += 1
            except WorkflowError as e:
                eng.log.error(str(e))
                workflowlog = BibWorkflowEngineLog.query.filter(
                    BibWorkflowEngineLog.id_object == e.id_workflow
                ).filter(BibWorkflowEngineLog.log_type == 40).all()
                for log in workflowlog:
                    eng.log.error(log.message)

                eng.extra_data["_nb_workflow_failed"] += 1
                eng.extra_data["_nb_workflow_finish"] += 1
            except Exception as e:
                eng.log.error("Error: Workflow failed %s" % str(e))
                eng.extra_data["_nb_workflow_failed"] += 1
                eng.extra_data["_nb_workflow_finish"] += 1
    else:
        eng.extra_data["_nb_workflow"] = 0
        eng.extra_data["_nb_workflow_failed"] = 0
        eng.extra_data["_nb_workflow_finish"] = 0


def wait_for_a_workflow_to_complete_obj(obj, eng):
    """
    This function wait for the asynchronous workflow specified
    in obj.data ( asyncresult )
    It acts like a barrier

    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    if not obj.data:
        eng.extra_data["_nb_workflow"] = 0
        eng.extra_data["_nb_workflow_failed"] = 0
        eng.extra_data["_nb_workflow_finish"] = 0
        return None
    try:
        obj.data.get()
        eng.extra_data["_nb_workflow_finish"] += 1
    except WorkflowError as e:
        eng.log.error("Error: Workflow failed %s" % str(e))
        workflowlog = BibWorkflowEngineLog.query.filter(
            BibWorkflowEngineLog.id_object == e.id_workflow
        ).filter(BibWorkflowEngineLog.log_type == 40).all()

        for log in workflowlog:
            eng.log.error(log.message)
        eng.extra_data["_nb_workflow_failed"] += 1
        eng.extra_data["_nb_workflow_finish"] += 1
    except Exception as e:
        eng.log.error("Error: Workflow failed %s" % str(e))
        eng.extra_data["_nb_workflow_failed"] += 1
        eng.extra_data["_nb_workflow_finish"] += 1


def wait_for_a_workflow_to_complete(obj, eng):
    """
    This function wait for the asynchronous workflow specified
    in obj.data ( asyncresult )
    It acts like a barrier
    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
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
            sleep(1)
        if not to_wait:
            return None
        try:
            to_wait.get()
            eng.extra_data["_nb_workflow_finish"] += 1
        except WorkflowError as e:
            eng.extra_data["_uuid_workflow_crashed"].append(e.id_workflow)
            eng.extra_data["_nb_workflow_failed"] += 1
            eng.extra_data["_nb_workflow_finish"] += 1
        except:
            eng.extra_data["_nb_workflow_failed"] += 1
            eng.extra_data["_nb_workflow_finish"] += 1

        del eng.extra_data["_workflow_ids"][i]

    else:
        eng.extra_data["_nb_workflow"] = 0
        eng.extra_data["_nb_workflow_failed"] = 0
        eng.extra_data["_nb_workflow_finish"] = 0


def write_something_generic(messagea, func):
    """
    This function allows you to write a message where you want.
    This function support the multicasting.

    Messagea is a string or a list of string  and function that will be concatenate
    in one and only string.

    Func is the list of the functions that will be used to send the message. The function
    should always take in parameter a string which is the message.

    :param func: the list of function that will be used to propagate the message
    :type func: Array of functions
    :param messagea: the message that you want to propagate
    :type messagea: Array of strings and functions.
    """

    def _write_something_generic(obj, eng):
        if isinstance(messagea, six.string_types):
            if isinstance(func, list):
                for function in func:
                    function(messagea)
            else:
                func(messagea)
            return None

        if not isinstance(messagea, list):
            if callable(messagea):
                func_messagea = messagea
                while callable(func_messagea):
                    func_messagea = func_messagea(obj, eng)
                if isinstance(func, list):
                    for function in func:
                        function(func_messagea)
                else:
                    func(func_messagea)
            return None

        if len(messagea) > 0:
            temp = ""
            for func_messagea in messagea:
                if callable(func_messagea):
                    while callable(func_messagea):
                        func_messagea = func_messagea(obj, eng)
                    temp += str(func_messagea)
                elif isinstance(func_messagea, six.string_types):
                    temp += func_messagea
            if isinstance(func, list):
                for function in func:
                    function(temp)
            else:
                func(temp)
            return None

    return _write_something_generic


def get_list_of_workflows_to_wait(obj, eng):
    """
     Return a list of asyncresult corresponding to running
     asynchrnous workflow

    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
     """
    return eng.extra_data["_workflow_ids"]


def get_status_async_result_obj_data(obj, eng):
    """
    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    return obj.data.state


def get_workflows_progress(obj, eng):
    """
    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    try:
        return (eng.extra_data["_nb_workflow_finish"] * 100.0) / (eng.extra_data["_nb_workflow"])
    except KeyError:
        return "No progress (key missing)"
    except ZeroDivisionError:
        return "No workflows"


def workflows_reviews(stop_if_error=False):
    """
    This function just give you a little review of you children workflows.
    This function can be used to stop the workflow if a child has crashed.

    :param stop_if_error: give to the function the indication it it should stop
    if a child workflow has crashed.
    :type stop_if_error: Boolean
    """
    def _workflows_reviews(obj, eng):
        """
         This function write a  little report about
         asynchronous workflows in this main workflow
         Raise an exception if a workflow is gone rogue
         """
        if eng.extra_data["_nb_workflow"] == 0:
            raise WorkflowError("Nothing has been harvested ! Look into logs for errors !", eng.uuid, obj.id)
        eng.log.info("%s / %s failed" % (eng.extra_data["_nb_workflow_failed"], eng.extra_data["_nb_workflow"]))

        if eng.extra_data["_nb_workflow_failed"] and stop_if_error:
            raise WorkflowError(
                "%s / %s failed" % (eng.extra_data["_nb_workflow_failed"], eng.extra_data["_nb_workflow"]),
                eng.uuid, obj.id, payload=eng.extra_data["_uuid_workflow_crashed"])

    return _workflows_reviews


def log_info(message):
    """

    :param message:
    :return:
    """

    def _log_info(obj, eng):
        eng.log.info(message)

    return _log_info
