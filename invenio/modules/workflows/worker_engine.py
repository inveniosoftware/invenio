# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2012, 2013, 2014 CERN.
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

from .client import run_workflow, continue_execution
from .engine import BibWorkflowEngine, WorkflowStatus
from .models import BibWorkflowObject, Workflow, ObjectVersion
from .errors import WorkflowObjectVersionError


def run_worker(wname, data, **kwargs):
    """
    Runs workflow with given name and given data.
    Data can be specified as list of objects or
    single id of WfeObject/BibWorkflowObjects.

    :param wname: the name of the workflow which will be run.
    :type wname: String
    :param data: And Array of value and variable which will
    be processed by the workflow specified by wname
    :type data: Array
    :param kwargs: This parameter allow to pass some
    special arguments for the different steps.
    """
    engine = BibWorkflowEngine(wname, **kwargs)
    engine.save()
    objects = get_workflow_object_instances(data, engine)
    run_workflow(wfe=engine, data=objects, **kwargs)
    return engine


def restart_worker(wid, **kwargs):
    """
    Restarts workflow with given id (wid) and given data. If data are not
    specified then it will load all initial data for workflow.

    The workflow will restart from scratch.

    Data can be specified as list of objects or single id of
    BibWorkflowObjects.

    :param wid: workflow id (uuid) of the workflow to be restarted
    :param kwargs: This parameter allow to pass some
    special arguments for the different steps.
    """
    if "data" not in kwargs:
        data = []
        # First we get all initial objects
        initials = BibWorkflowObject.query.filter(
            BibWorkflowObject.id_workflow == wid,
            BibWorkflowObject.version == ObjectVersion.INITIAL
        ).all()

        # Then we reset their children to the same state as initial
        for initial_object in initials:
            running_object = BibWorkflowObject.query.filter(
                BibWorkflowObject.id == initial_object.id_parent
            ).one()
            running_object.copy(initial_object)
            running_object.id_parent = initial_object.id
            running_object.save()
            data.append(running_object)

    workflow = Workflow.query.get(wid)
    engine = BibWorkflowEngine(workflow.name,
                               workflow_object=workflow,
                               **kwargs)
    engine.reset_extra_data()
    engine.save(WorkflowStatus.NEW)
    objects = get_workflow_object_instances(data, engine)
    run_workflow(wfe=engine, data=objects, **kwargs)
    return engine


def continue_worker(oid, restart_point="continue_next",
                    task_offset=1, **kwargs):
    """
    Restarts workflow with given id (wid) at given point.

    :param oid: object id of the object to process
    :param restart_point: can be one of:

    * restart_prev: will restart from the previous task
    * continue_next: will continue to the next task
    * restart_task: will restart the current task

    :param kwargs: This parameter allow to pass some
    special arguments for the different steps.
    """
    workflow_object = BibWorkflowObject.query.get(oid)
    workflow = Workflow.query.get(workflow_object.id_workflow)

    engine = BibWorkflowEngine(workflow.name,
                               workflow_object=workflow,
                               **kwargs)
    engine.save()
    continue_execution(engine, workflow_object, restart_point,
                       task_offset, **kwargs)
    return engine


def get_workflow_object_instances(data, engine):
    """
    Wraps each item in the given list of data objects into BibWorkflowObject
    instances - creating appropriate versions of objects in the database and
    returning a list of these objects.

    This process is necessary to save an initial version of the data before
    running it (and potentially changing it) in the workflow.

    This function also takes into account if given data objects are already
    BibWorkflowObject instances.

    :param data: list of data objects to wrap
    :param engine: instance of BibWorkflowEngine

    :returns: list -- BibWorkflowObject's list
    """
    workflow_objects = []
    data_type = None
    for data_object in data:
        if isinstance(data_object, BibWorkflowObject):
            if data_object.id:
                data_object.log.debug("Existing workflow object found for " +
                                      "this object. Saving a snapshot.")
                workflow_objects.append(
                    generate_snapshot(data_object, engine)
                )
            else:
                workflow_objects.append(data_object)
        else:
            data_type = data_type or engine.get_default_data_type()
            # Data is not already a BibWorkflowObject, we then
            # create initial + running object pairs for each data object.
            # Then we add the running object to run through the workflow.
            current_obj = create_object_pairs_from_data(
                data_object,
                engine,
                data_type
            )
            workflow_objects.append(current_obj)
    return workflow_objects


def generate_snapshot(workflow_object, engine):
    """
    Given a workflow object, generate a snapshot of it's current state
    and return the given instance to work on.

    Also checks if the given workflow instance has a valid version and
    is not in RUNNING state.

    :param workflow_object: Instance of BibWorkflowObject to create
                            snapshot from.
    :param engine: Instance of Workflow that is currently running.

    :returns: BibWorkflowObject -- the given object instance
    :raises: WorkflowObjectVersionError
    """
    if workflow_object.version in (ObjectVersion.INITIAL,
                                   ObjectVersion.FINAL,
                                   ObjectVersion.HALTED):
        # Create initial snapshot
        initial_object = BibWorkflowObject.create_object_revision(
            workflow_object,
            id_workflow=engine.uuid,
            version=workflow_object.version
        )
        initial_object.log.debug("Created new object revision: %s"
                                 % (initial_object.id,))
        # Propagate the parent id
        initial_object.id_parent = workflow_object.id
        workflow_object.save()
    elif workflow_object.version == ObjectVersion.RUNNING:
        # Trying to run an object that is running. Dangerous!
        msg = "Object is already in RUNNING state!"
        workflow_object.log.critical(msg)
        raise WorkflowObjectVersionError(msg,
                                         obj_version=workflow_object.version,
                                         id_object=workflow_object.id)
    else:
        # Ehm, this version does not exist.. ( magic or huge dev error,
        # surely the second one)
        raise WorkflowObjectVersionError("Object version is unknown: %s" %
                                         (workflow_object.version,),
                                         obj_version=workflow_object.version,
                                         id_object=workflow_object.id)

    # Always return the given object to run on.
    return workflow_object


def create_object_pairs_from_data(data_object, engine, data_type):
    """
    Create a new workflow object pair (INITIAL + RUNNING) and return them.

    :param data_object: object containing the data
    :param engine: Instance of Workflow that is currently running.
    :param data_type: the determined type of the data given.

    :returns: tuple -- pair of BibWorkflowObject instances (initial, running)
    """
    # Data is not already a BibWorkflowObject, we first
    # create an initial object for each data object.
    current_obj = BibWorkflowObject.create_object(
        id_workflow=engine.uuid,
        version=ObjectVersion.INITIAL,
        data_type=data_type
    )

    current_obj.set_data(data_object)
    current_obj.save()

    generate_snapshot(current_obj, engine)
    return current_obj
