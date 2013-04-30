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

from invenio.config import CFG_LOGDIR, \
     CFG_BROKER_URL, \
     CFG_CELERY_RESULT_BACKEND
from invenio.bibworkflow_config import add_log, \
     CFG_BIBWORKFLOW_WORKERS_LOGDIR
from invenio.bibworkflow_worker_engine import *
from invenio.celery import celery

class worker_celery(object):
    def run(self, wname, data, external_save=None):
        """
        Helper function to get celery task
        decorators to worker_celery
        """
        return self.celery_runit.delay(wname, data, external_save)

    @celery.task(name='invenio.bibworkflow.workers.worker_celery.runit')
    def celery_runit(wname, data, external_save=None):
        """
        Runs the workflow with Celery
        """
        add_log(os.path.join(CFG_BIBWORKFLOW_WORKERS_LOGDIR,
                             "worker_celery.log"), 'celery')
        runit(wname, data, external_save=external_save)

    def restart(self, wid, data, restart_point, external_save=None):
        """
        Helper function to get celery task
        decorators to worker_celery
        """
        return self.celery_restartit.delay(wid, data, restart_point, external_save)

    @celery.task(name='invenio.bibworkflow.workers.worker_celery.restartit')
    def celery_restartit(wid, data=None, restart_point="beginning", external_save=None):
        """
        Restarts the workflow with Celery
        """
        restartit(wid, data, restart_point, external_save=external_save)
