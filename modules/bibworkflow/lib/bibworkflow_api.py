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

"""
BibWorkflow API - functions to run workflows
"""

import os
from pprint import pformat
from werkzeug.utils import import_string
from invenio.config import CFG_BIBWORKFLOW_WORKER
from invenio.config import CFG_PYLIBDIR, CFG_LOGDIR
from invenio.errorlib import register_exception
import cPickle


USE_TASK_QUEUE = False

if CFG_BIBWORKFLOW_WORKER:
    try:
        WORKER = import_string('invenio.bibworkflow.workers.%s:%s' % (
            CFG_BIBWORKFLOW_WORKER, CFG_BIBWORKFLOW_WORKER))
        USE_TASK_QUEUE = True
    except:
        ## Let's report about broken plugins
        register_exception(alert_admin=True)


def start(workflow_name, data, task_queue=USE_TASK_QUEUE, external_save=None):
    """
    Runs workflow by given name for specified data. The workflow name is
    considered unique and it is the equal to thename of a file containing
    a workflow definition. Data is a list of objects to run through the
    workflow. For example: a list of dict, JSON string, BibWorkflowObjects etc.
    """
    from invenio.bibworkflow_worker_engine import runit

    if task_queue:
        return WORKER().run(workflow_name, data, external_save=external_save)
    else:
        return runit(workflow_name, data, external_save=external_save)


def start_by_wid(wid, task_queue=USE_TASK_QUEUE, external_save=None):
    """
    Runs workflow by given workflow id (wid). It can start from beginning,
    prev, next and continue. Data variable can be list of object ids or list of
    objects.
    """
    from invenio.bibworkflow_worker_engine import restartit

    if task_queue:
        return WORKER().restart(wid, external_save=external_save)
    else:
        return restartit(wid, external_save=external_save)


def start_by_oids(workflow_name, oids, task_queue=USE_TASK_QUEUE, external_save=None):
    from invenio.bibworkflow_model import BibWorkflowObject
    objects = BibWorkflowObject.query.filter(BibWorkflowObject.id.in_(list(oids))).all()

    return start(workflow_name, objects, task_queue, external_save)


def continue_oid(oid, start_point="beginning",
                 task_queue=USE_TASK_QUEUE, external_save=None):
    """
    Continue workflow asociated with object given by object id (oid).
    It can start from beginning, prev, next and continue.
    """
    from invenio.bibworkflow_worker_engine import continueit

    if task_queue:
        return WORKER().continueit(oid, start_point,
                                   external_save=external_save)
    else:
        return continueit(oid, start_point, external_save=external_save)
