# This file is part of Invenio.
# Copyright (C) 2012 CERN.
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

from redis import Redis
from rq.decorators import job
from invenio.modules.workflows.worker_result import AsynchronousResultWrapper
from ..worker_engine import run_worker, restart_worker, continue_worker

#FIXME: add configuration variables
redis_conn = Redis()


class worker_redis(object):
    def run_worker(self, workflow_name, data, **kwargs):
        """
        Registers run_worker function as a new task in RQ
        The delay method executes it asynchronously

        :param workflow_name: name of the workflow to be run
        :type workflow_name: string

        :param data: list of objects for the workflow
        :type data: list
        """
        return RedisResult(
            job(queue='default', connection=redis_conn)(run_worker).delay(
                workflow_name, data, **kwargs
            )
        )

    def restart_worker(self, wid, **kwargs):
        """
        Registers restart_worker as a new task in RQ
        The delay method executes it asynchronously

        :param wid: uuid of the workflow to be run
        :type wid: string
        """
        return RedisResult(
            job(queue='default', connection=redis_conn)(restart_worker).delay(
                wid, **kwargs
            )
        )

    def continue_worker(self, oid, restart_point, **kwargs):
        """
        Registers continue_worker as a new task in RQ
        The delay method executes it asynchronously

        ;param oid: uuid of the object to be started
        :type oid: string

        :param restart_point: sets the start point
        :type restart_point: string
        """
        return RedisResult(
            job(queue='default', connection=redis_conn)(continue_worker).delay(
                oid, restart_point, **kwargs
            )
        )


class RedisResult(AsynchronousResultWrapper):

    def __init__(self, asynchronousresult):
        super(RedisResult, self).__init__(asynchronousresult)

    @property
    def status(self):
        return self.asyncresult.get_status()

    def get(self, postprocess=None):
        if postprocess is None:
            return self.asyncresult.result
        else:
            return postprocess(self.asyncresult.result)
