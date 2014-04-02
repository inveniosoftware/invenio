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
"""
    invenio.modules.workflows.api
    -----------------------------

    This is the main API for the workflows module.

    If you want to run a workflow using the workflows module,
    this is the high level API you will want to use.
"""


from werkzeug.utils import (import_string,
                            cached_property,
                            )

from invenio.base.globals import cfg
from invenio.base.config import CFG_BIBWORKFLOW_WORKER

from .utils import BibWorkflowObjectIdContainer
from .models import BibWorkflowObject
from .errors import WorkflowWorkerError


class WorkerBackend(object):
    @cached_property
    def worker(self):
        try:
            return import_string('invenio.modules.workflows.workers.%s:%s' % (
                cfg['CFG_BIBWORKFLOW_WORKER'], cfg['CFG_BIBWORKFLOW_WORKER']))
        except:
            from invenio.ext.logging import register_exception
            ## Let's report about broken plugins
            register_exception(alert_admin=True)

    def __call__(self, *args, **kwargs):
        if not self.worker:
            raise WorkflowWorkerError('No worker configured')
        return self.worker(*args, **kwargs)


WORKER = WorkerBackend()


def start(workflow_name, data, **kwargs):
    """
    Starts a workflow by given name for specified data *immediately*
    in the current process.

    The name of the workflow to start is considered unique and it is
    equal to the name of a file containing the workflow definition.

    The data passed should be a list of object(s) to run through the
    workflow. For example: a list of dict, JSON string, BibWorkflowObjects
    etc.

    Special custom keyword arguments can be given to the workflow engine
    in order to pass certain variables to the tasks in the workflow execution,
    such as a taskid from BibSched, the current user etc.

    The workflow engine object generated is returned upon completion.

    :param workflow_name: the workflow name to run. Ex: "my_workflow"
    :type workflow_name: str or String

    :param data: the workflow name to run. Ex: "my_workflow"
    :type data: list of objects/dicts

    :return: BibWorkflowEngine that ran the workflow.
    """
    from .worker_engine import run_worker

    return run_worker(workflow_name, data, **kwargs)


def start_delayed(workflow_name, data, **kwargs):
    """
    Starts a *delayed* workflow by using one of the defined workers
    available. For example, enqueueing the execution of the workflow in
    a task queue such as Celery (http://celeryproject.org).

    Otherwise, see documentation of start().

    :param workflow_name: the workflow name to run. Ex: "my_workflow"
    :type workflow_name:  String or str

    :param data: the workflow name to run. Ex: "my_workflow"
    :type data: list of objects/dicts

    :return: BibWorkflowEngine that ran the workflow.
    """
    if not CFG_BIBWORKFLOW_WORKER:
        raise WorkflowWorkerError('No worker configured')

    #The goal of this part is to avoid a SQLalchemy decoherence in case
    #some one try to send a Bibworkflow object. To avoid to send the
    #complete object and get SQLAlchemy error of mapping, we save the id
    #into our Id container, In the celery process the object is reloaded
    #from the database !
    if isinstance(data, list):
        for i in range(0, len(data)):
            if isinstance(data[i], BibWorkflowObject):
                data[i] = BibWorkflowObjectIdContainer(data[i]).to_dict()
    else:
        if isinstance(data, BibWorkflowObject):
            data = BibWorkflowObjectIdContainer(data).to_dict()

    return WORKER().run_worker(workflow_name, data, **kwargs)


def start_by_wid(wid, **kwargs):
    """
    Will re-start given workflow, by workflow uuid (wid),
    from the beginning with the original data given.

    Special custom keyword arguments can be given to the workflow engine
    in order to pass certain variables to the tasks in the workflow execution,
    such as a taskid from BibSched, the current user etc.

    :param wid: the workflow uuid. Ex: "550e8400-e29b-41d4-a716-446655440000"
    :type wid: str

    :return: BibWorkflowEngine that ran the workflow.
    """
    from .worker_engine import restart_worker

    return restart_worker(wid, **kwargs)


def start_by_wid_delayed(wid, **kwargs):
    """
    Will re-start given workflow, by workflow uuid (wid),
    from the beginning with the original data given.

    Starts the workflow *delayed* by using one of the defined workers
    available. For example, enqueueing the execution of the workflow in
    a task queue such as Celery (http://celeryproject.org).

    Special custom keyword arguments can be given to the workflow engine
    in order to pass certain variables to the tasks in the workflow execution,
    such as a taskid from BibSched, the current user etc.

    :param wid: the workflow uuid. Ex: "550e8400-e29b-41d4-a716-446655440000"
    :type wid: str

    :return: BibWorkflowEngine that ran the workflow.
    """
    return WORKER().restart_worker(wid, **kwargs)


def start_by_oids(workflow_name, oids, **kwargs):
    """
    Will start given workflow, by name, using the given
    list of BibWorkflowObject ids (oids) from beginning.

    Special custom keyword arguments can be given to the workflow engine
    in order to pass certain variables to the tasks in the workflow execution,
    such as a taskid from BibSched, the current user etc.

    :param workflow_name: the workflow name to run. Ex: "my_workflow"
    :type workflow_name: str

    :param oids: list of BibWorkflowObject id's to run.
    :type oids: list of str or integers

    :return: BibWorkflowEngine that ran the workflow.
    """
    from .models import BibWorkflowObject

    if not oids:
        # oids is not defined!
        from .errors import WorkflowAPIError
        raise WorkflowAPIError("No Object IDs are defined")

    objects = BibWorkflowObject.query.filter(
        BibWorkflowObject.id.in_(list(oids))
    ).all()
    return start(workflow_name, objects, **kwargs)


def start_by_oids_delayed(workflow_name, oids, **kwargs):
    """
    Will start given workflow, by name, using the given
    list of BibWorkflowObject ids (oids) from beginning.

    Special custom keyword arguments can be given to the workflow engine
    in order to pass certain variables to the tasks in the workflow execution,
    such as a taskid from BibSched, the current user etc.

    Starts the workflow *delayed* by using one of the defined workers
    available. For example, enqueueing the execution of the workflow in
    a task queue such as Celery (http://celeryproject.org).

    :param workflow_name: the workflow name to run. Ex: "my_workflow"
    :type workflow_name: str

    :param oids: list of BibWorkflowObject id's to run.
    :type oids: list of str or int

    :return: BibWorkflowEngine that ran the workflow.
    """
    from .models import BibWorkflowObject

    objects = BibWorkflowObject.query.filter(
        BibWorkflowObject.id.in_(list(oids))
    ).all()

    return start_delayed(workflow_name, objects, **kwargs)


def continue_oid(oid, start_point="continue_next", **kwargs):
    """
    Continue workflow asociated with object given by object id (oid).
    It can start from previous, current or next task.

    Special custom keyword arguments can be given to the workflow engine
    in order to pass certain variables to the tasks in the workflow execution,
    such as a taskid from BibSched, the current user etc.

    Starts the workflow *delayed* by using one of the defined workers
    available. For example, enqueueing the execution of the workflow in
    a task queue such as Celery (http://celeryproject.org).

    :param oid: id of BibWorkflowObject to run.
    :type oid: str

    :param start_point: where should the workflow start from? One of:
        * restart_prev: will restart from the previous task
        * continue_next: will continue to the next task
        * restart_task: will restart the current task
    :type start_point: str

    :return: BibWorkflowEngine that ran the workflow
    """
    from .worker_engine import continue_worker

    return continue_worker(oid, start_point, **kwargs)


def continue_oid_delayed(oid, start_point="continue_next", **kwargs):
    """
    Continue workflow associated with object given by object id (oid).
    It can start from previous, current or next task.

    Special custom keyword arguments can be given to the workflow engine
    in order to pass certain variables to the tasks in the workflow execution,
    such as a taskid from BibSched, the current user etc.

    Starts the workflow *delayed* by using one of the defined workers
    available. For example, enqueueing the execution of the workflow in
    a task queue such as Celery (http://celeryproject.org).

    :param oid: id of BibWorkflowObject to run.
    :type oid: str

    :param start_point: where should the workflow start from? One of:
        * restart_prev: will restart from the previous task
        * continue_next: will continue to the next task
        * restart_task: will restart the current task
    :type start_point: str

    :return: BibWorkflowEngine that ran the workflow
    """
    return WORKER().continue_worker(oid, start_point, **kwargs)



def resume_objects_in_workflow(id_workflow, start_point="continue_next",
                               **kwargs):
    """
    Resume workflow for any halted or failed objects from given workflow.

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
    from .models import BibWorkflowObject, ObjectVersion

    # Resume workflow if there are objects to resume
    objects = BibWorkflowObject.query.filter(
        BibWorkflowObject.id_workflow == id_workflow,
        BibWorkflowObject.version == ObjectVersion.HALTED
    ).all()
    for obj in objects:
        yield continue_oid(oid=obj.id, start_point=start_point,
                           **kwargs)
