# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014 CERN.
#
# Workflow is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Workflow is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Workflow; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Low-level functions to run workflows."""


def run_workflow(wfe, data, stop_on_halt=False, stop_on_error=True,
                 initial_run=True):
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
    wfe.process(data, stop_on_halt=stop_on_halt, stop_on_error=stop_on_error,
                initial_run=initial_run)


def continue_execution(wfe, workflow_object, restart_point="restart_task",
                       stop_on_halt=False):
    """
    Continue execution of workflow for one given object from "restart_point".

    :param workflow_object:
    :param stop_on_halt:
    :param restart_point: can be one of:

    * restart_prev: will restart from the previous task
    * continue_next: will continue to the next task
    * restart_task: will restart the current task

    :type restart_point: str

    You can use stop_on_error to raise exception's and stop the processing.
    Use stop_on_halt to stop processing the workflow
    if HaltProcessing is raised.
    """
    wfe.continue_object(workflow_object, restart_point=restart_point,
                        stop_on_halt=stop_on_halt)
