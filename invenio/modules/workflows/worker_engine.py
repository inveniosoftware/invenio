# -*- coding: utf-8 -*-
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

from invenio.ext.sqlalchemy import db
from .client import run_workflow, continue_execution
from .engine import BibWorkflowEngine
from .models import BibWorkflowObject, Workflow
from .config import CFG_OBJECT_VERSION


class InvenioBibWorkflowValueError(Exception):
    pass


def run_worker(wname, data, **kwargs):
    """
    Runs workflow with given name and given data.
    Data can be specified as list of objects or
    single id of WfeObject/BibWorkflowObjects.
    """
    wfe = BibWorkflowEngine(wname, **kwargs)
    wfe.save()

    objects = prepare_objects(data, wfe)
    run_workflow(wfe=wfe, data=objects, **kwargs)
    return wfe


def restart_worker(wid, **kwargs):
    """
    Restarts workflow with given id (wid) and given data. If data are not
    specified then it will load all initial data for workflow.

    Data can be specified as list of objects
    or single id of WfeObject/BibWorkflowObjects.
    """
    data = BibWorkflowObject.query.filter(BibWorkflowObject.id_workflow == wid,
                                          BibWorkflowObject.version ==
                                          CFG_OBJECT_VERSION.INITIAL).all()

    workflow = Workflow.query.filter(Workflow.uuid == wid).first()

    wfe = BibWorkflowEngine(workflow.name, **kwargs)
    wfe.save()

    objects = prepare_objects(data, wfe)
    run_workflow(wfe=wfe, data=objects, **kwargs)

    return wfe


def continue_worker(oid, restart_point="continue_next", **kwargs):
    """
    Restarts workflow with given id (wid) at given point.

    restart_point can be one of:

    * restart_prev: will restart from the previous task
    * continue_next: will continue to the next task
    * restart_task: will restart the current task
    """
    data = [BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                           oid).first()]

    workflow = Workflow.query.filter(Workflow.uuid ==
                                     data[0].id_workflow).first()
    wfe = BibWorkflowEngine(workflow.name, uuid=None, id_user=0,
                            workflow_object=workflow, **kwargs)
    wfe.save()

    continue_execution(wfe, data, restart_point, **kwargs)
    return wfe


def prepare_objects(data, workflow_object):
    objects = []
    for obj in data:
        if isinstance(obj, BibWorkflowObject):
            if obj.id:
                obj.log.debug("Object found for process")
                objects.append(_prepare_objects_helper(obj, workflow_object))
            else:
                objects.append(obj)
        else:
            # First we create an initial object for each data item
            new_initial = \
                BibWorkflowObject(id_workflow=workflow_object.uuid,
                                  version=CFG_OBJECT_VERSION.INITIAL
                                  )
            new_initial.set_data(obj)
            new_initial._update_db()

            # Then we create another object to actually work on
            current_obj = BibWorkflowObject(id_workflow=workflow_object.uuid,
                                            version=CFG_OBJECT_VERSION.RUNNING,
                                            id_parent=new_initial.id)
            current_obj.set_data(obj)
            objects.append(current_obj)

    return objects


def _prepare_objects_helper(obj, workflow_object):
    assert obj
    if obj.version == CFG_OBJECT_VERSION.INITIAL:
        obj.log.debug("State: Initial")
        new_id = obj._create_version_obj(id_workflow=workflow_object.uuid,
                                         version=CFG_OBJECT_VERSION.RUNNING,
                                         id_parent=obj.id,
                                         no_update=True)
        return BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                              new_id).first()
    elif obj.version in (CFG_OBJECT_VERSION.HALTED, CFG_OBJECT_VERSION.FINAL):
        obj.log.debug("State: Halted or Final")
        # creating INITIAL object
        # for FINAL version: maybe it should set
        # id_parent to the previous final object
        new_initial = obj._create_version_obj(id_workflow=workflow_object.uuid,
                                              version=CFG_OBJECT_VERSION.INITIAL,
                                              no_update=True)
        new_id = obj._create_version_obj(id_workflow=workflow_object.uuid,
                                         version=CFG_OBJECT_VERSION.RUNNING,
                                         id_parent=new_initial,
                                         no_update=True)
        return BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                              new_id).first()
    elif obj.version == CFG_OBJECT_VERSION.RUNNING:
        # object shuld be deleted restart from INITIAL
        obj.log.debug("State: Running")

        if obj.id_workflow is not None:
            obj.log.info("""WARNING! You want to restart from temporary object.
We can't guarantee that data object is not corrupted.
Workflow will start from associated INITIAL object
and RUNNING object will be deleted.""")

            parent_obj = BibWorkflowObject.query.filter(
                BibWorkflowObject.id == obj.id_parent).first()
            new_initial = parent_obj._create_version_obj(
                id_workflow=workflow_object.uuid,
                version=CFG_OBJECT_VERSION.INITIAL,
                no_update=True)
            new_id = parent_obj._create_version_obj(
                id_workflow=workflow_object.uuid,
                version=CFG_OBJECT_VERSION.RUNNING,
                id_parent=new_initial,
                no_update=True)
            db.session.delete(obj)

            return BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                                  new_id).first()
        else:
            obj.log.info("""You are running workflow on a object created manualy
outside of the workflow. Workflow will execute on THIS object (it will change
its state and/or data) but it would also create INITIAL version of the object to
 keep its oryginal state.""")

            # We assume that there is no parent object, so we create a new
            # INITIAL object, which will become a parent.
            new_parent = obj._create_version_obj(
                id_workflow=workflow_object.uuid,
                version=CFG_OBJECT_VERSION.INITIAL,
                no_update=True)
            # We add an id_workflow to our object
            obj.id_workflow = workflow_object.uuid
            obj.id_parent = new_parent
            obj._update_db()

            return obj
    else:
        raise InvenioBibWorkflowValueError("Object version is unknown: %s" %
                                           (obj.version,))
