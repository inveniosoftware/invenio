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
from invenio.config import CFG_BIBWORKFLOW_WORKER
from invenio.config import CFG_PYLIBDIR, CFG_LOGDIR
import cPickle
from invenio.pluginutils import PluginContainer


USE_TASK_QUEUE = False

if CFG_BIBWORKFLOW_WORKER:
    worker_plugin_path = os.path.join(CFG_PYLIBDIR, 'invenio', 'bibworkflow',
                                      'workers', '*.py')
    workers = PluginContainer(worker_plugin_path, exception_registration=False)
    try:
        WORKER = workers.get_enabled_plugins()[CFG_BIBWORKFLOW_WORKER]
        USE_TASK_QUEUE = True
    except KeyError:
        print 'Could not load Worker'
        ## Let's report about broken plugins
        open(os.path.join(CFG_LOGDIR, 'broken-bibworkflow-workers.log'), 'w').\
            write(pformat(workers.get_broken_plugins()))


def run(wname, data, task_queue=USE_TASK_QUEUE, external_save=None):
    """
    Runs workflow by given name for specified data. Name is uniqe and is the
    same as name of a file containing workflow. Data is a list of objects f.eg
    dict, BibWorkflowObjects, WfeObjects.
    """
    from invenio.bibworkflow_worker_engine import runit

    if task_queue:
        return WORKER().run(wname, data, external_save=external_save)
    else:
        return runit(wname, data, external_save=external_save)
# Will run workflow with specified wid from beginning.
# Objects will be automatically or it will use objects specified in data.
# start_point="beginning" -> take initial objects
# start_point=[?,?] -> take last version of objects
# data - do not pass WfeObjects!!


def run_by_wid(wid, data=None, start_point="beginning",
               task_queue=USE_TASK_QUEUE, external_save=None):
    """
    Runs workflow by given workflow id (wid). It can start from beginning,
    prev, next and continue. Data variable can be list of object ids or list of
    objects.
    """
    from invenio.bibworkflow_worker_engine import restartit

    if task_queue:
        return WORKER().restart(wid, data, start_point, external_save=external_save)
    else:
        return restartit(wid, data, start_point, external_save=external_save)


def run_by_wobject(workflow, data=None, start_point="beginning",
                   task_queue=USE_TASK_QUEUE, external_save=None):
    """
    Runs workflow by given workflow object. If object doesn't have its id
    (a new workflow object) it will save it automatically. It can start from
    beginning, prev, next and continue. Data variable can be list of object ids
    or list of objects.
    """
    from invenio.bibworkflow_worker_engine import restartit

    if workflow.uuid is None:
        workflow.save()
    if task_queue:
        return WORKER().restart(workflow.id, data, start_point, external_save=external_save)
    else:
        return restartit(workflow.id, data, start_point, external_save=external_save)


def run_by_oid(oid, start_point="beginning", task_queue=USE_TASK_QUEUE, external_save=None):
    """
    Runs workflow asociated with object given by object id (oid). It can start
    from beginning, prev, next and continue.
    """
    from invenio.bibworkflow_model import WfeObject
    from invenio.bibworkflow_worker_engine import restartit

    wf_object = WfeObject.query.filter(WfeObject.id == oid).first()
    if start_point == "beginning":
        restart_point = "beginning"

        # restarting from beginning for error and halted objects
        # always choose initial object
        if wf_object.parent_id is not None:
            oid = wf_object.parent_id
    if start_point == "continue":
        restart_point = cPickle.loads(wf_object.task_counter)
    if start_point == "next":
        restart_point = cPickle.loads(wf_object.task_counter)
        restart_point[-1] += 1
    if start_point == "prev":
        restart_point = cPickle.loads(wf_object.task_counter)
        restart_point[-1] -= 1

    if task_queue:
        return WORKER().restart(wf_object.workflow_id, [oid],
                                restart_point, external_save=external_save)
    else:
        return restartit(wf_object.workflow_id, [oid],
                         restart_point, external_save=external_save)


def run_by_object(wf_object, start_point="beginning",
                  task_queue=USE_TASK_QUEUE, external_save=None):
    """
    Runs workflow asociated with object given. If object doens't have id it
    will save it automatically. It can start from beginning, prev, next and
    continue.
    """
    from invenio.bibworkflow_object import BibWorkflowObject
    from invenio.bibworkflow_worker_engine import restartit

    if isinstance(wf_object, BibWorkflowObject):
        if wf_object.id is None:
            wf_object.save()
    if task_queue:
        return WORKER().restart(wf_object.workflow_id, [wf_object.id],
                                start_point, external_save=external_save)
    else:
        return restartit(wf_object.workflow_id, [wf_object.id], start_point,
                         external_save=external_save)
