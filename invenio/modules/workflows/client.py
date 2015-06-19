# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Low-level functions to run workflows."""

import traceback

from .engine import WorkflowStatus
from .errors import WorkflowError, WorkflowHalt
from .models import ObjectVersion
from .signals import workflow_error, workflow_halted


def run_workflow(wfe, data, stop_on_halt=False,
                 stop_on_error=True,
                 initial_run=True, **kwargs):
    """
    Main function running the workflow.

    :param stop_on_error: Stop the workflow on an exception and raise this one
    to an upper level for a future processing.
    :param data: Data to process
    :param stop_on_halt:
    :param initial_run:
    :param kwargs: additionnal keywords arguements
    :param wfe: workflow engine in charge of workflow execution
    """
    while True:
        try:
            if initial_run:
                initial_run = False
                wfe.process(data)
                break
            else:
                wfe.restart('next', 'first')
                break
        except WorkflowHalt as workflowhalt_triggered:
            current_obj = wfe.get_current_object()
            if current_obj:
                if workflowhalt_triggered.action:
                    current_obj.set_action(workflowhalt_triggered.action,
                                           workflowhalt_triggered.message)
                    current_obj.version = ObjectVersion.HALTED
                    current_obj.save(version=ObjectVersion.HALTED,
                                     task_counter=wfe.getCurrTaskId(),
                                     id_workflow=wfe.uuid)
                else:
                    current_obj.version = ObjectVersion.WAITING
                    current_obj.save(version=ObjectVersion.WAITING,
                                     task_counter=wfe.getCurrTaskId(),
                                     id_workflow=wfe.uuid)
            else:
                wfe.log.warning("No active object found!")

            wfe.save(status=WorkflowStatus.HALTED)
            message = "Workflow '%s' halted at task %s with message: %s" % \
                      (wfe.name,
                       wfe.get_current_taskname() or "Unknown",
                       workflowhalt_triggered.message)
            wfe.log.warning(message)
            workflow_halted.send(current_obj)
            if stop_on_halt:
                break
        except Exception as exception_triggered:
            msg = "Error: %r\n%s" % \
                  (exception_triggered, traceback.format_exc())
            wfe.log.error(msg)
            current_obj = wfe.get_current_object()
            if current_obj:
                # Sets an error message as a tuple (title, details)
                current_obj.set_error_message((str(exception_triggered), msg))
                current_obj.save(
                    ObjectVersion.ERROR,
                    wfe.getCurrTaskId(),
                    id_workflow=wfe.uuid
                )
            wfe.save(status=WorkflowStatus.ERROR)
            workflow_error.send(current_obj)
            if stop_on_error:
                if isinstance(exception_triggered, WorkflowError):
                    raise exception_triggered
                else:
                    raise WorkflowError(
                        message=msg,
                        id_workflow=wfe.uuid,
                        id_object=wfe.getCurrObjId(),
                    )


def continue_execution(wfe, workflow_object, restart_point="restart_task",
                       task_offset=1, stop_on_halt=False, **kwargs):
    """
    Continue execution of workflow for one given object from "restart_point".

    :param kwargs:
    :param workflow_object:
    :param task_offset:
    :param stop_on_halt:
    :param restart_point: can be one of:

    * restart_prev: will restart from the previous task
    * continue_next: will continue to the next task

    :type restart_point: str

    You can use stop_on_error to raise exception's and stop the processing.
    Use stop_on_halt to stop processing the workflow
    if HaltProcessing is raised.
    """
    pos = workflow_object.get_current_task()
    if not pos:
        pos = [0]
    wfe._objects = [workflow_object]

    if restart_point == "restart_prev":
        pos[-1] -= task_offset
    elif restart_point == "continue_next":
        pos[-1] += task_offset

    wfe.reset()
    wfe.set_task_position(pos)
    run_workflow(wfe, wfe._objects, stop_on_halt,
                 initial_run=True, stop_on_error=True, **kwargs)
