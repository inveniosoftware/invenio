# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014 CERN.
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

"""Mediator between API and workers responsible for running the workflows."""

from invenio.modules.workflows.client import run_workflow, continue_execution
from .engine import BibWorkflowEngine
from invenio.modules.workflows.models import DbWorkflowObject, Workflow
from workflow.errors import WorkflowObjectStatusError


def run_worker(wname, data, **kwargs):
    """Run a workflow by name with list of data objects.

    The list of data can also contain DbWorkflowObjects.

    ``**kwargs`` can be used to pass custom arguments to the engine/object.

    :param wname: name of workflow to run.
    :type wname: str

    :param data: objects to run through the workflow.
    :type data: list

    :return: BibWorkflowEngine instance
    """
    engine = BibWorkflowEngine.with_name(wname, **kwargs)
    engine.save()
    objects = get_workflow_object_instances(data, engine)
    run_workflow(engine, objects)
    return engine


def restart_worker(wid, **kwargs):
    """Restart workflow from beginning with given id (wid) and any data.

    ``**kwargs`` can be used to pass custom arguments to the engine/object such
    as ``data``. If ``data`` is not specified then it will load all
    initial data for the data objects.

    Data can be specified as list of objects or single id of
    DbWorkflowObjects.

    :param wid: workflow id (uuid) of the workflow to be restarted
    :type wid: str

    :return: BibWorkflowEngine instance
    """
    engine = BibWorkflowEngine.from_uuid(uuid=wid, **kwargs)

    if "data" not in kwargs:
        objects = []
        # First we get all initial objects
        initials = DbWorkflowObject.query.filter(
            DbWorkflowObject.id_workflow == wid,
            DbWorkflowObject.status == DbWorkflowObject.known_statuses.INITIAL
        ).all()

        # Then we reset their children to the same state as initial
        for initial_object in initials:
            running_object = DbWorkflowObject.query.filter(
                DbWorkflowObject.id == initial_object.id_parent
            ).one()
            old_id_parent = running_object.id_parent
            running_object.copy(initial_object)
            running_object.id_parent = old_id_parent
            running_object.save()

            objects.append(running_object)
    else:
        objects = get_workflow_object_instances(kwargs["data"], engine)
    run_workflow(wfe=engine, data=objects)
    return engine


def continue_worker(oid, restart_point="continue_next", **kwargs):
    """Restart workflow with given id (wid) at given point.

    By providing the ``restart_point`` you can change the
    point of which the workflow will continue from.

    * restart_prev: will restart from the previous task
    * continue_next: will continue to the next task (default)
    * restart_task: will restart the current task

    ``**kwargs`` can be used to pass custom arguments to the engine/object.

    :param oid: object id of the object to process
    :type oid: int

    :param restart_point: point to continue from
    :type restart_point: str

    :return: BibWorkflowEngine instance
    """
    workflow_object = DbWorkflowObject.query.get(oid)
    workflow = Workflow.query.get(workflow_object.id_workflow)

    engine = BibWorkflowEngine(workflow, **kwargs)
    engine.save()
    continue_execution(engine, workflow_object, restart_point=restart_point)
    return engine


def get_workflow_object_instances(data, engine):
    """Analyze data and create corresponding DbWorkflowObjects.

    Wrap each item in the given list of data objects into DbWorkflowObject
    instances - creating appropriate status of objects in the database and
    returning a list of these objects.

    This process is necessary to save an initial status of the data before
    running it (and potentially changing it) in the workflow.

    This function also takes into account if given data objects are already
    DbWorkflowObject instances.

    :param data: list of data objects to wrap
    :type data: list

    :param engine: instance of BibWorkflowEngine
    :type engine: py:class:`.engine.BibWorkflowEngine`

    :return: list of DbWorkflowObject
    """
    workflow_objects = []
    data_type = None
    if isinstance(data, DbWorkflowObject):
        # A DbWorkflowObject was passed directly, put it in a list.
        data = [data]
    for data_object in data:
        if isinstance(data_object, DbWorkflowObject):
            data_object.data_type = data_type = data_type or engine.get_default_data_type()
            if data_object.id:
                data_object.log.debug("Existing workflow object found for "
                                      "this object. Saving a snapshot.")
                if data_object.status == data_object.known_statuses.COMPLETED:
                    data_object.status = data_object.known_statuses.INITIAL
                workflow_objects.append(
                    generate_snapshot(data_object, engine)
                )
            else:
                workflow_objects.append(data_object)
        else:
            data_type = data_type or engine.get_default_data_type()
            # Data is not already a DbWorkflowObject, we then
            # create initial + running object pairs for each data object.
            # Then we add the running object to run through the workflow.
            current_obj = create_data_object_from_data(
                data_object,
                engine,
                data_type
            )
            workflow_objects.append(current_obj)

    return workflow_objects


def generate_snapshot(workflow_object, engine):
    """Save a status of the DbWorkflowObject passed in parameter.

    Given a workflow object, generate a snapshot of it's current state
    and return the given instance to work on.

    Also checks if the given workflow instance has a valid status and
    is not in RUNNING state.

    :param workflow_object: DbWorkflowObject to create snapshot from.
    :type workflow_object: py:class:`workflow.models.DbWorkflowObject`

    :param engine: Instance of Workflow that is currently running.
    :type engine: py:class:`.engine.BibWorkflowEngine`

    :returns: DbWorkflowObject -- workflow_object instance
    :raises: WorkflowObjectStatusError
    """
    if workflow_object.status == workflow_object.known_statuses.RUNNING:
        # Trying to run an object that is running. Dangerous!
        msg = "Object is already in RUNNING state!"
        workflow_object.log.debug(msg)
        raise WorkflowObjectStatusError(msg,
                                        obj_status=workflow_object.status,
                                        id_object=workflow_object.id)
    else:
        # Create initial snapshot
        initial_object = DbWorkflowObject.create_object_revision(
            workflow_object,
            id_workflow=engine.uuid,
            status=workflow_object.status
        )
        initial_object.log.debug("Created new object revision: %s"
                                 % (initial_object.id,))
        # Propagate the parent id
        initial_object.id_parent = workflow_object.id
        workflow_object.save()

    # Always return the given object to run on.
    return workflow_object


def create_data_object_from_data(data_object, engine, data_type):
    """Create a new DbWorkflowObject from given data and return it.

    Returns a data object wrapped around data_object given. In addition
    it creates an initial snapshot.

    :param data_object: object containing the data
    :type data_object: object

    :param engine: Instance of Workflow that is currently running.
    :type engine: py:class:`.engine.BibWorkflowEngine`

    :param data_type: type of the data given as taken from workflow definition.
    :type data_type: str

    :returns: new DbWorkflowObject
    """
    # Data is not already a DbWorkflowObject, we first
    # create an initial object for each data object.
    current_obj = DbWorkflowObject.create_object(
        id_workflow=engine.uuid,
        status=DbWorkflowObject.known_statuses.INITIAL,
        data_type=data_type
    )

    current_obj.set_data(data_object)
    current_obj.save()

    generate_snapshot(current_obj, engine)
    return current_obj
