# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

import traceback
from .errors import (WorkflowHalt, WorkflowError)
from .models import ObjectVersion
from .engine import WorkflowStatus


def run_workflow(wfe, data, stop_on_halt=False, stop_on_error=False,
                 initial_run=True, **kwargs):
    """
    Main function running the workflow.
    """
    while True:
        try:
            if initial_run:
                initial_run = False
                wfe.process(data)
                # We processed the workflow. We're done.
                break
            else:
                wfe._unpickled = True
                wfe.restart('current', 'current')
                # We processed the restarted workflow. We're done.
                break
        except WorkflowHalt as e:
            # Processing was halted. Lets save current object and continue.

            # Save current object progress
            current_obj = wfe.get_current_object()
            if current_obj:
                if e.widget:
                    current_obj.add_widget(e.widget, e.message)
                current_obj.save(version=ObjectVersion.HALTED,
                                 task_counter=wfe.getCurrTaskId(),
                                 id_workflow=wfe.uuid)
            else:
                wfe.log.warning("No active object found!")

            # Save workflow progress
            wfe.save(status=WorkflowStatus.HALTED)
            wfe.setPosition(wfe.getCurrObjId() + 1, [0, 0])

            message = "Workflow '%s' halted at task %s with message: %s" % \
                      (wfe.name,
                       wfe.get_current_taskname() or "Unknown",
                       e.message)
            wfe.log.warning(message)
            if stop_on_halt:
                break
        except Exception as e:
            # We print the stacktrace, save the object and continue
            # unless instructed otherwise.
            msg = "Error: %r\n%s" % (e, traceback.format_exc())
            wfe.log.error(msg)

            # Changing counter should be moved to wfe object
            # together with default exception handling
            wfe.increase_counter_error()
            wfe._objects[wfe.getCurrObjId()].save(ObjectVersion.HALTED,
                                                  wfe.getCurrTaskId(),
                                                  id_workflow=wfe.uuid)
            wfe.save(WorkflowStatus.ERROR)
            wfe.setPosition(wfe.getCurrObjId() + 1, [0, 0])
            # if stop_on_halt or stop_on_error:
            if isinstance(e, WorkflowError):
                raise e
            else:
                raise WorkflowError(message=msg,
                                    id_workflow=wfe.uuid,
                                    id_object=wfe.getCurrObjId())


def continue_execution(wfe, data, restart_point="restart_task",
                       stop_on_halt=False, stop_on_error=False, **kwargs):
    """
    Continue execution of workflow for given object (wfe) from "restart_point".

    restart_point can be one of:

    * restart_prev: will restart from the previous task
    * continue_next: will continue to the next task
    * restart_task: will restart the current task

    You can use stop_on_error to raise exception's and stop the processing.
    Use stop_on_halt to stop processing the workflow
    if HaltProcessing is raised.
    """
    wfe.log.info("Continue execution from: %s" % (str(restart_point),))
    pos = data[0].get_current_task()

    if restart_point == "restart_prev":
        pos[-1] -= 1
        wfe.setPosition(wfe.db_obj.current_object, pos)
    elif restart_point == "continue_next":
        pos[-1] += 1
        wfe.setPosition(wfe.db_obj.current_object, pos)
    else:
        # restart_task
        wfe.setPosition(wfe.db_obj.current_object, pos)
    wfe._objects = data
    run_workflow(wfe, data, stop_on_halt, stop_on_error,
                 initial_run=False, **kwargs)
