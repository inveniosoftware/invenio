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

import os

from celery import Celery
from invenio.config import CFG_LOGDIR, \
     CFG_BIBWORKFLOW_MSG_BROKER_URL, \
     CFG_BIBWORKFLOW_MSG_BACKEND_URL
from invenio.bibworkflow_config import add_log, \
     CFG_BIBWORKFLOW_WORKERS_LOGDIR
from invenio.bibworkflow_worker_engine import *

celery = Celery('run_celery', broker=CFG_BIBWORKFLOW_MSG_BROKER_URL,
                backend=CFG_BIBWORKFLOW_MSG_BACKEND_URL)


class worker_celery(object):
    def run(self, wname, data):
        """
        Helper function to get celery task
        decorators to worker_celery
        """
        return self.celery_runit.apply_async([wname, data])

    @celery.task(name='invenio.bibworkflow.workers.worker_celery.runit')
    def celery_runit(wname, data):
        """
        Runs the workflow with Celery
        """
        add_log(os.path.join(CFG_BIBWORKFLOW_WORKERS_LOGDIR,
                             "worker_celery.log"), 'celery')
        runit(wname, data)

    def restart(self, wid, data, restart_point):
        """
        Helper function to get celery task
        decorators to worker_celery
        """
        return self.celery_restartit.apply_async([wid, data, restart_point])

    @celery.task(name='invenio.bibworkflow.workers.worker_celery.restartit')
    def celery_restartit(wid, data=None, restart_point="beginning"):
        """
        Restarts the workflow with Celery
        """
        restartit(wid, data, restart_point)
