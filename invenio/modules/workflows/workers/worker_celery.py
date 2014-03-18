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

from __future__ import print_function

from six import iteritems

from invenio.celery import celery

from invenio.base.helpers import with_app_context
from invenio.modules.workflows.worker_result import AsynchronousResultWrapper, uui_to_workflow


@celery.task(name='invenio.modules.workflows.workers.worker_celery.run_worker')
@with_app_context()
def celery_run(workflow_name, data, **kwargs):
    """
    Runs the workflow with Celery
    """
    from ..worker_engine import run_worker
    from ..utils import BibWorkflowObjectIdContainer

    if isinstance(data, list):
        for i in range(0, len(data)):
            if isinstance(data[i], dict):
                if str(BibWorkflowObjectIdContainer().__class__) in data[i]:
                    data[i] = BibWorkflowObjectIdContainer().from_dict(data[i]).get_object()
                    stack = data[i].get_extra_data().items()
                    while stack:
                        k, v = stack.pop()
                        if isinstance(v, dict):
                            stack.extend(iteritems(v))

    return run_worker(workflow_name, data, **kwargs).uuid


@celery.task(name='invenio.modules.workflows.workers.worker_celery.restart_worker')
@with_app_context()
def celery_restart(wid, **kwargs):
    """
    Restarts the workflow with Celery
    """
    from ..worker_engine import restart_worker

    result = restart_worker(wid, **kwargs).uuid
    return result


@celery.task(name='invenio.modules.workflows.workers.worker_celery.continue_worker')
@with_app_context()
def celery_continue(oid, restart_point, **kwargs):
    """
    Restarts the workflow with Celery
    """
    from ..worker_engine import continue_worker

    return continue_worker(oid, restart_point, **kwargs).uuid



class worker_celery(object):
    def run_worker(self, workflow_name, data, **kwargs):
        """
        Helper function to get celery task
        decorators to worker_celery

        @param workflow_name: name of the workflow to be run
        @type workflow_name: string

        @param data: list of objects for the workflow
        @type data: list
        """
        result = celery_run.delay(workflow_name, data, **kwargs)
        return CeleryResult(result)

    def restart_worker(self, wid, **kwargs):
        """
        Helper function to get celery task
        decorators to worker_celery

        @param wid: uuid of the workflow to be run
        @type wid: string
        """
        result = celery_restart.delay(wid, **kwargs)
        return CeleryResult(result)

    def continue_worker(self, oid, restart_point, **kwargs):
        """
        Helper function to get celery task
        decorators to worker_celery

        @param oid: uuid of the object to be started
        @type oid: string

        @param restart_point: sets the start point
        @type restart_point: string
        """
        result = celery_continue.delay(oid, restart_point, **kwargs)
        return CeleryResult(result)


class CeleryResult(AsynchronousResultWrapper):
    """

    :param asynchronousresult:
    """

    def __init__(self, asynchronousresult):
        super(CeleryResult, self).__init__(asynchronousresult)

    @property
    def status(self):
        return self.asyncresult.status

    def get(self, postprocess=None):
        if postprocess is None:
            return uui_to_workflow(self.asyncresult.get())
        else:
            return postprocess(self.asyncresult.get())
