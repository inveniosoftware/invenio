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
"""
Main API for the workflows.

If you want to run a workflow using the workflows module,
this is the high level API you will want to use.
"""

from werkzeug.utils import import_string, cached_property, ImportStringError
from invenio.base.globals import cfg
from .utils import BibWorkflowObjectIdContainer
from invenio.modules.workflows.models import DbWorkflowObject
from invenio.modules.workflows.errors import WorkflowWorkerError


class WorkerBackend(object):
    """WorkerBackend is a class representing the worker.

    It will automatically get the worker thanks to the configuration
    when called.
    """
    @cached_property
    def worker_modspec(self):
        return 'invenio.modules.workflows.workers.%s:%s' % (
            cfg['CFG_BIBWORKFLOW_WORKER'], cfg['CFG_BIBWORKFLOW_WORKER'])

    @cached_property
    def worker(self):
        """Represent the worker.

        This cached property is the one which is returning the worker
        to use.

        :return: the worker configured into the configuration file.
        """
        try:
            return import_string(self.worker_modspec)
        except:
            from invenio.ext.logging import register_exception
            ## Let's report about broken plugins
            register_exception(alert_admin=True)

    def __call__(self):
        """Action on call."""
        return self.worker()


WORKER = WorkerBackend()


def start(workflow_name, data, **kwargs):
    """Start a workflow by given name for specified data.

    The name of the workflow to start is considered unique and it is
    equal to the name of a file containing the workflow definition.

    The data passed should be a list of object(s) to run through the
    workflow. For example: a list of dict, JSON string, DbWorkflowObjects
    etc.

    Special custom keyword arguments can be given to the workflow engine
    in order to pass certain variables to the tasks in the workflow execution,
    such as a taskid from BibSched, the current user etc.

    The workflow engine object generated is returned upon completion.

    :param workflow_name: the workflow name to run. Ex: "my_workflow".
    :type workflow_name: str

    :param data: the workflow name to run. Ex: "my_workflow".
    :type data: list

    :return: DbWorkflowEngine that ran the workflow.
    """
    from .worker_engine import run_worker
    if not isinstance(data, list):
        data = [data]

    return run_worker(workflow_name, data, **kwargs)


def start_delayed(workflow_name, data, **kwargs):
    """Start a workflow by given name for specified data, asynchronously.

    Similar behavior as :py:func:`.start`, except it starts the
    workflow *delayed* by using one of the defined workers available.

    For example, it may enqueue the execution of the workflow in
    a task queue such as Celery (http://celeryproject.org).

    This function returns a sub-classed AsynchronousResultWrapper that
    holds a reference to the workflow id via the object
    `AsynchronousResultWrapper.get`.

    :param workflow_name: the workflow name to run. Ex: "my_workflow".
    :type workflow_name:  str

    :param data: the workflow name to run. Ex: "my_workflow".
    :type data: list

    :return: AsynchronousResultWrapper
    """

    # The goal of this part is to avoid a SQLalchemy decoherence in case
    # some one try to send a Bibworkflow object. To avoid to send the
    # complete object and get SQLAlchemy error of mapping, we save the id
    # into our Id container, In the celery process the object is reloaded
    # from the database !

    if isinstance(data, list):
        for i in range(0, len(data)):
            if isinstance(data[i], DbWorkflowObject):
                data[i] = BibWorkflowObjectIdContainer(data[i]).to_dict()
    else:
        if isinstance(data, DbWorkflowObject):
            data = [BibWorkflowObjectIdContainer(data).to_dict()]
    return WORKER().run_worker(workflow_name, data, **kwargs)


def start_by_wid(wid, **kwargs):
    """Re-start given workflow, by workflow uuid (wid).

    It is restarted from the beginning with the original data given.

    Special custom keyword arguments can be given to the workflow engine
    in order to pass certain variables to the tasks in the workflow execution,
    such as a task-id from BibSched, the current user etc.

    :param wid: the workflow uuid. Ex: "550e8400-e29b-41d4-a716-446655440000".
    :type wid: str

    :return: BibWorkflowEngine that ran the workflow.
    """
    from .worker_engine import restart_worker

    return restart_worker(wid, **kwargs)


def start_by_wid_delayed(wid, **kwargs):
    """Re-start given workflow, by workflow uuid (wid), asynchronously.

    Similar behavior as :py:func:`.start_by_wid`, except it starts the
    workflow *delayed* by using one of the defined workers available.

    For example, it may enqueue the execution of the workflow in
    a task queue such as Celery (http://celeryproject.org).

    This function returns a sub-classed AsynchronousResultWrapper that
    holds a reference to the workflow id via the function
    `AsynchronousResultWrapper.get`.

    :param wid: the workflow uuid. Ex: "550e8400-e29b-41d4-a716-446655440000".
    :type wid: str

    :return: AsynchronousResultWrapper
    """
    return WORKER().restart_worker(wid, **kwargs)


def start_by_oids(workflow_name, oids, **kwargs):
    """Start workflow by name with :py:class:`invenio.modules.workflows.models.DbWorkflowObject`
    ids.

    Wrapper to call :py:func:`.start` with list of
    :py:class:`invenio.modules.workflows.models.DbWorkflowObject` ids.

    Special custom keyword arguments can be given to the workflow engine
    in order to pass certain variables to the tasks in the workflow execution,
    such as a task-id from BibSched, the current user etc.

    :param workflow_name: the workflow name to run. Ex: "my_workflow".
    :type workflow_name: str

    :param oids: DbWorkflowObject id's to run.
    :type oids: list

    :return: BibWorkflowEngine that ran the workflow.
    """
    if not oids:
        from workflow.errors import WorkflowAPIError
        raise WorkflowAPIError("No Object IDs are defined")

    objects = DbWorkflowObject.query.filter(
        DbWorkflowObject.id.in_(list(oids))
    ).all()
    return start(workflow_name, objects, **kwargs)


def start_by_oids_delayed(workflow_name, oids, **kwargs):
    """Start asynchronously workflow by name with
    :py:class:`invenio.modules.workflows.models.DbWorkflowObject` ids.

    Similar behavior as :py:func:`.start_by_oids`, except it calls
    :py:func:`.start_delayed`.

    For example, it may enqueue the execution of the workflow in
    a task queue such as Celery (http://celeryproject.org).

    This function returns a sub-classed AsynchronousResultWrapper that
    holds a reference to the workflow id via the function
    `AsynchronousResultWrapper.get`.

    :param workflow_name: the workflow name to run. Ex: "my_workflow".
    :type workflow_name: str

    :param oids: list of DbWorkflowObject id's to run.
    :type oids: list

    :return: AsynchronousResultWrapper.
    """
    if not oids:
        from workflow.errors import WorkflowAPIError
        raise WorkflowAPIError("No Object IDs are defined")

    objects = DbWorkflowObject.query.filter(
        DbWorkflowObject.id.in_(list(oids))
    ).all()
    return start_delayed(workflow_name, objects, **kwargs)


def continue_oid(oid, start_point="continue_next", **kwargs):
    """Continue workflow for given object id (oid).

    Depending on `start_point` it may start from previous, current or
    next task.

    Special custom keyword arguments can be given to the workflow engine
    in order to pass certain variables to the tasks in the workflow execution,
    such as a task-id from BibSched, the current user etc.

    :param oid: id of DbWorkflowObject to run.
    :type oid: str

    :param start_point: where should the workflow start from? One of:
        * restart_prev: will restart from the previous task
        * continue_next: will continue to the next task
        * restart_task: will restart the current task
    :type start_point: str

    :return: BibWorkflowEngine that ran the workflow
    """
    from .worker_engine import continue_worker
    return continue_worker(oid, restart_point=start_point, **kwargs)


def continue_oid_delayed(oid, start_point="continue_next", **kwargs):
    """Continue workflow for given object id (oid), asynchronously.

    Similar behavior as :py:func:`.continue_oid`, except it runs it
    asynchronously.

    For example, it may enqueue the execution of the workflow in
    a task queue such as Celery (http://celeryproject.org).

    This function returns a sub-classed AsynchronousResultWrapper that
    holds a reference to the workflow id via the function
    `AsynchronousResultWrapper.get`.

    :param oid: id of DbWorkflowObject to run.
    :type oid: str

    :param start_point: where should the workflow start from? One of:
        * restart_prev: will restart from the previous task
        * continue_next: will continue to the next task
        * restart_task: will restart the current task
    :type start_point: str

    :return: AsynchronousResultWrapper.
    """
    return WORKER().continue_worker(oid, start_point, **kwargs)


def resume_objects_in_workflow(id_workflow, start_point="continue_next",
                               **kwargs):
    """Resume workflow for any halted or failed objects from given workflow.

    This is a generator function and will yield every workflow created per
    object which needs to be resumed.

    To identify the original workflow containing the halted objects,
    the ID (or UUID) of the workflow is required. The starting point
    to resume the objects from can optionally be given. By default,
    the objects resume with their next task in the workflow.

    :param id_workflow: id of Workflow with objects to resume.
    :type id_workflow: str

    :param start_point: where should the workflow start from? One of:
        * restart_prev: will restart from the previous task
        * continue_next: will continue to the next task
        * restart_task: will restart the current task
    :type start_point: str

    yield: BibWorkflowEngine that ran the workflow
    """
    # Resume workflow if there are objects to resume
    objects = DbWorkflowObject.query.filter(
        DbWorkflowObject.id_workflow == id_workflow,
        DbWorkflowObject.version == DbWorkflowObject.version.type.choices.HALTED
    ).all()
    for obj in objects:
        yield continue_oid(oid=obj.id, start_point=start_point,
                           **kwargs)
