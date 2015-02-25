# -*- coding: utf-8 -*-
#
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


from invenio.celery import celery
from invenio.ext.sqlalchemy.utils import session_manager
from invenio.base.helpers import with_app_context

from invenio.modules.workflows.worker_result import AsynchronousResultWrapper
from invenio.modules.workflows.errors import WorkflowWorkerError


@celery.task(name='invenio.modules.workflows.workers.worker_celery.run_worker')
@with_app_context()
def celery_run(workflow_name, data, **kwargs):
    """Run the workflow with Celery."""
    from ..worker_engine import run_worker
    from ..utils import BibWorkflowObjectIdContainer

    if isinstance(data, list):
        # For each data item check if dict and then
        # see if the dict contains a BibWorkflowObjectId container
        # generated dict.
        for i in range(0, len(data)):
            if isinstance(data[i], dict):
                if str(BibWorkflowObjectIdContainer().__class__) in data[i]:
                    data[i] = BibWorkflowObjectIdContainer().from_dict(data[i]).get_object()
    else:
        raise WorkflowWorkerError("Data is not a list: %r" % (data,))

    return run_worker(workflow_name, data, **kwargs).uuid


@celery.task(name='invenio.modules.workflows.workers.worker_celery.restart_worker')
@with_app_context()
def celery_restart(wid, **kwargs):
    """Restart the workflow with Celery."""
    from ..worker_engine import restart_worker
    return restart_worker(wid, **kwargs).uuid


@celery.task(name='invenio.modules.workflows.workers.worker_celery.continue_worker')
@with_app_context()
def celery_continue(oid, restart_point, **kwargs):
    """Restart the workflow with Celery."""
    from ..worker_engine import continue_worker

    # We need to return the uuid because of AsynchronousResultWrapper
    return continue_worker(oid, restart_point, **kwargs).uuid


class worker_celery(object):

    """Used by :py:class:`.api.WorkerBackend` to call the worker functions."""

    def run_worker(self, workflow_name, data, **kwargs):
        """Helper function to get celery task decorators to worker_celery.

        :param workflow_name: name of the workflow to be run
        :type workflow_name: str

        :param data: list of objects for the workflow
        :type data: list
        """
        return CeleryResult(celery_run.delay(workflow_name, data, **kwargs))

    def restart_worker(self, wid, **kwargs):
        """Helper function to get celery task decorators to worker_celery.

        :param wid: uuid of the workflow to be run
        :type wid: str
        """
        return CeleryResult(celery_restart.delay(wid, **kwargs))

    def continue_worker(self, oid, restart_point, **kwargs):
        """Helper function to get celery task decorators to worker_celery.

        :param oid: uuid of the object to be started
        :type oid: str

        :param restart_point: sets the start point
        :type restart_point: str
        """
        return CeleryResult(celery_continue.delay(oid, restart_point, **kwargs))


class CeleryResult(AsynchronousResultWrapper):

    """Wrapped asynchronous result from Celery.

    It is presenting a normalized interface to the task enqueued in Celery.
    Since BibWorkflowEngine cannot be serialized, we need this wrapper
    to transform the results (BibWorkflowEngine) back and forth between
    client and queue.

    :param asynchronousresult: the result from Celery
    """

    @property
    def status(self):
        """Return the status."""
        return self.asyncresult.status

    @session_manager
    def get(self, postprocess=None):
        """Return the result of async result that ran in Celery.

        WorkflowEngine cannot be serialized, so we often need to
        postprocess the result from the celery process across
        to the client.

        :param postprocess: function to postprocess the result
        :type postprocess: callable function

        :return: the postprocess result (i.e. BibWorkflowEngine)
        """
        if postprocess is None:
            return self.asyncresult.get()
        else:
            return postprocess(self.asyncresult.get())
