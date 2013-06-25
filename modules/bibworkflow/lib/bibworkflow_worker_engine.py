## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

from invenio.bibworkflow_client import run_workflow, continue_execution
from invenio.bibworkflow_engine import BibWorkflowEngine
from invenio.bibworkflow_model import BibWorkflowObject, Workflow
from invenio.bibworkflow_config import CFG_OBJECT_VERSION
from invenio.errorlib import register_exception
from invenio.sqlalchemyutils import db
from invenio.bibworkflow_utils import determineDataType


def runit(wname, data, external_save=None):
    """
    Runs workflow with given name and given data.
    Data can be specified as list of objects or
    single id of WfeObject/BibWorkflowObjects.
    """
    wfe = BibWorkflowEngine(wname, user_id=0, module_name="aa")
    wfe.setWorkflowByName(wname)
    wfe.setCounterInitial(len(data))
    wfe.save()

    run_workflow(wfe=wfe, data=prepare_objects(data, wfe))
    return wfe


def restartit(wid, external_save=None):
    """
    Restarts workflow with given id (wid) and given data. If data are not
    specified then it will load all initial data for workflow.

    Data can be specified as list of objects
    or single id of WfeObject/BibWorkflowObjects.
    """
    data = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == wid,
                                          BibWorkflowObject.version ==
                                          CFG_OBJECT_VERSION.INITIAL).all()

    workflow = Workflow.query.filter(Workflow.uuid == wid).first()

    wfe = BibWorkflowEngine(workflow.name)
    wfe.setWorkflowByName(workflow.name)
    wfe.setCounterInitial(len(data))
    wfe.save()

    obj = prepare_objects(data, wfe)

    try:
        run_workflow(wfe, obj)
    except:
        wfe.log_debug("error in worker engine")
        raise
    return wfe


def continueit(oid, restart_point="next_task", external_save=None):
    """
    Restarts workflow with given id (wid) and given data. If data are not
    specified then it will load all initial data for workflow. Depending on
    restart_point function can load initial or current objects.
    """
    data = [BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                           oid).first()]

    workflow = Workflow.query.filter(Workflow.uuid ==
                                     data[0].workflow_id).first()
    wfe = BibWorkflowEngine(None, uuid=None, user_id=0,
                            workflow_object=workflow,
                            module_name="module")
    wfe.setWorkflowByName(workflow.name)

    wfe.setCounterInitial(len(data))
    wfe.save()

    continue_execution(wfe, data, restart_point)
    return wfe


def parseDictionary(d, wfe_id=None):
    try:
        data = d['data']
    except:
        if not d['id']:
            register_exception(prefix="Data field in dictionary passed to \
                           workflow is empty! You also did not gave any id.")
            raise
        else:
            data = None

    try:
        workflow_id = d['workflow_id']
    except:
        workflow_id = wfe_id

    try:
        version = d['version']
    except:
        version = CFG_OBJECT_VERSION.INITIAL

    try:
        parent_id = d['parent_id']
    except:
        parent_id = None

    try:
        id = d['id']
    except:
        id = None

    try:
        extra_data = d['extra_data']
    except:
        extra_data = None

    try:
        task_counter = d['task_counter']
    except:
        task_counter = [0]

    try:
        user_id = d['user_id']
    except:
        user_id = 0

    try:
        if d['data_type'] == 'auto':
            data_type = determineDataType(d['data'])
        elif isinstance(d['data_type'], str):
            data_type = d['data_type']
    except:
        print 'could not resolve data type'
        data_type = None

    try:
        uri = d['uri']
    except:
        uri = None

    return {'data': data, 'workflow_id': workflow_id, 'version': version,
            'parent_id': parent_id, 'id': id, 'extra_data': extra_data,
            'task_counter': task_counter, 'user_id': user_id,
            'data_type': data_type, 'uri': uri}


def prepare_objects(data, workflow_object):
    objects = []
    for d in data:
        if isinstance(d, BibWorkflowObject):
            if d.id:
                d.log_debug("Object found for process")
                objects.append(_prepare_objects_helper(d, workflow_object))
            else:
                objects.append(d)
        else:
            parsed_dict = parseDictionary(d, workflow_object.uuid)
            if parsed_dict['id']:
                obj = BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                                     parsed_dict['id']).first()
                objects.append(_prepare_objects_helper(obj, workflow_object))
            else:
                new_initial = \
                    BibWorkflowObject(data=parsed_dict['data'],
                                      workflow_id=parsed_dict['workflow_id'],
                                      version=CFG_OBJECT_VERSION.INITIAL,
                                      parent_id=None,
                                      extra_data=parsed_dict['extra_data'],
                                      data_type=parsed_dict['data_type'],
                                      uri=parsed_dict['uri'])
                new_initial._update_db()
                objects.append(
                    BibWorkflowObject(data=parsed_dict['data'],
                                      workflow_id=parsed_dict['workflow_id'],
                                      version=CFG_OBJECT_VERSION.RUNNING,
                                      parent_id=new_initial.id,
                                      extra_data=parsed_dict['extra_data'],
                                      data_type=parsed_dict['data_type'],
                                      uri=parsed_dict['uri']))

    return objects


def _prepare_objects_helper(obj, workflow_object):
    assert obj
    if obj.version == CFG_OBJECT_VERSION.INITIAL:
        obj.log_debug("State: Initial")
        new_id = obj._create_version_obj(workflow_id=workflow_object.uuid,
                                         version=CFG_OBJECT_VERSION.RUNNING,
                                         parent_id=obj.id,
                                         no_update=True)
        return BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                              new_id).first()
    elif obj.version in (CFG_OBJECT_VERSION.HALTED, CFG_OBJECT_VERSION.FINAL):
        obj.log_debug("State: Halted or Final")
        # creating INITIAL object
        # for FINAL version: maybe it should set
        # parent_id to the previous final object
        new_initial = obj._create_version_obj(workflow_id=workflow_object.uuid,
                                              version=CFG_OBJECT_VERSION.INITIAL,
                                              no_update=True)
        new_id = obj._create_version_obj(workflow_id=workflow_object.uuid,
                                         version=CFG_OBJECT_VERSION.RUNNING,
                                         parent_id=new_initial,
                                         no_update=True)
        return BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                              new_id).first()
    elif obj.version == CFG_OBJECT_VERSION.RUNNING:
        # object shuld be deleted restart from INITIAL
        obj.log_debug("State: Running")
        obj.log_info("""WARNING! You want to restart from temporary object.
We can't guaranty that data object is not corrupted.
Workflow will start from associated INITIAL object
and RUNNING object will be deleted.""")

        parent_obj = BibWorkflowObject.query.filter(
            BibWorkflowObject.id == obj.parent_id).first()
        new_initial = parent_obj._create_version_obj(
            workflow_id=workflow_object.uuid,
            version=CFG_OBJECT_VERSION.INITIAL,
            no_update=True)
        new_id = parent_obj._create_version_obj(
            workflow_id=workflow_object.uuid,
            version=CFG_OBJECT_VERSION.RUNNING,
            parent_id=new_initial,
            no_update=True)
        tmp_obj = BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                                 new_id).first()
        db.session.delete(obj)

        return BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                              new_id).first()
    else:
        from Exception import ValueError
        raise ValueError
