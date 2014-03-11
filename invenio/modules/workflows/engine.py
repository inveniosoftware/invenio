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

from six.moves import cPickle
from six import iteritems
from uuid import uuid1 as new_uuid

import base64

from workflow.engine import (GenericWorkflowEngine,
                             ContinueNextToken,
                             HaltProcessing,
                             StopProcessing,
                             JumpTokenBack,
                             JumpTokenForward,
                             WorkflowError)
from invenio.config import CFG_DEVEL_SITE
from .models import (Workflow,
                     BibWorkflowObject,
                     BibWorkflowEngineLog,
                     ObjectVersion)
from .utils import (dictproperty,
                    get_workflow_definition)
from .logger import (get_logger,
                     BibWorkflowLogHandler)
from .errors import WorkflowHalt

DEBUG = CFG_DEVEL_SITE > 0


class WorkflowStatus(object):
    NEW, RUNNING, HALTED, ERROR, COMPLETED = range(5)


class BibWorkflowEngine(GenericWorkflowEngine):
    """
    Subclass of GenericWorkflowEngine representing a workflow in
    the workflows module.

    Adds a SQLAlchemy database model to save workflow states and
    workflow data.

    Overrides key functions in GenericWorkflowEngine to implement
    logging and certain workarounds for storing data before/after
    task calls (This part will be revisited in the future).

    :param name:
    :param uuid:
    :param curr_obj:
    :param workflow_object:
    :param id_user:
    :param module_name:
    :param kwargs:
    """


    def __init__(self, name=None, uuid=None, curr_obj=0,
                 workflow_object=None, id_user=0, module_name="Unknown",
                 **kwargs):
        super(BibWorkflowEngine, self).__init__()

        self.db_obj = None
        if isinstance(workflow_object, Workflow):
            self.db_obj = workflow_object
        else:
            # If uuid is defined we try to get the db object from DB.
            if uuid is not None:
                self.db_obj = \
                    Workflow.get(Workflow.uuid == uuid).first()
            else:
                uuid = new_uuid()
            if self.db_obj is None:
                self.db_obj = Workflow(name=name, id_user=id_user,
                                       current_object=curr_obj,
                                       module_name=module_name, uuid=uuid)
                self.save(status=WorkflowStatus.NEW)

        if not self.db_obj.uuid in self.log.name:
            db_handler_obj = BibWorkflowLogHandler(BibWorkflowEngineLog, "uuid")
            self.log = get_logger(logger_name="workflow.%s" % self.db_obj.uuid,
                                  db_handler_obj=db_handler_obj,
                                  obj=self)

        self.set_workflow_by_name(self.db_obj.name)
        self.set_extra_data_params(**kwargs)

    def get_extra_data(self):
        """
        Main method to retrieve data saved to the object.
        """
        return cPickle.loads(base64.b64decode(self.db_obj._extra_data))

    def set_extra_data(self, value):
        """
        Main method to update data saved to the object.
        :param value:
        """
        self.db_obj._extra_data = base64.b64encode(cPickle.dumps(value))

    def extra_data_get(self, key):
        if key not in self.db_obj.get_extra_data():
            raise KeyError("%s not in extra_data" % (key,))
        return self.db_obj.get_extra_data()[key]

    def extra_data_set(self, key, value):
        tmp = self.db_obj.get_extra_data()
        tmp[key] = value
        self.db_obj.set_extra_data(tmp)

    extra_data = dictproperty(fget=extra_data_get, fset=extra_data_set,
                              doc="Sets up property")

    del extra_data_get, extra_data_set

    @property
    def counter_object(self):
        return self.db_obj.counter_object

    @property
    def uuid(self):
        return self.db_obj.uuid

    @property
    def id_user(self):
        return self.db_obj.id_user

    @property
    def module_name(self):
        return self.db_obj.module_name

    @property
    def name(self):
        return self.db_obj.name

    @property
    def status(self):
        return self.db_obj.status

    def __getstate__(self):
        if not self._picklable_safe:
            raise cPickle.PickleError("The instance of the workflow engine "
                                      "cannot be serialized, "
                                      "because it was constructed with "
                                      "custom, user-supplied callbacks. "
                                      "Either use PickableWorkflowEngine or "
                                      "provide your own __getstate__ method.")
        state = self.__dict__.copy()
        del state['log']
        return state

    def __setstate__(self, state):
        if len(self._objects) < self._i[0]:
            raise cPickle.PickleError("The workflow instance "
                                      "inconsistent state, "
                                      "too few objects")

        db_handler_obj = BibWorkflowLogHandler(BibWorkflowEngineLog, "uuid")
        state['log'] = get_logger(logger_name="workflow.%s" % state['uuid'],
                                  db_handler_obj=db_handler_obj,
                                  obj=self)

        self.__dict__ = state

    def __repr__(self):
        return "<BibWorkflow_engine(%s)>" % (self.db_obj.name,)

    def __str__(self, log=False):
        return """-------------------------------
BibWorkflowEngine
-------------------------------
    %s
-------------------------------
""" % (self.db_obj.__str__(),)

    @staticmethod
    def before_processing(objects, self):
        """
        Executed before processing the workflow.
        """
        self.save(status=WorkflowStatus.RUNNING)
        self.set_counter_initial(len(objects))
        GenericWorkflowEngine.before_processing(objects, self)

    @staticmethod
    def after_processing(objects, self):
        self._i = [-1, [0]]
        if self.has_completed():
            self.save(WorkflowStatus.COMPLETED)
        else:
            self.save(WorkflowStatus.HALTED)

    def has_completed(self):
        """
        Returns True of workflow is fully completed meaning
        that all associated objects are in FINAL state.
        """
        number_of_objects = BibWorkflowObject.query.filter(
            BibWorkflowObject.id_workflow == self.uuid,
            BibWorkflowObject.version.in_([ObjectVersion.HALTED,
                                           ObjectVersion.RUNNING])
        ).count()
        return number_of_objects == 0

    def save(self, status=None):
        """
        Save the workflow instance to database.
        """
        # This workflow continues a previous execution.
        if status == WorkflowStatus.HALTED:
            self.db_obj.current_object = 0
        self.db_obj.save(status)

    def process(self, objects):
        """

        :param objects:
        """
        super(BibWorkflowEngine, self).process(objects)

    def restart(self, obj, task):
        """Restart the workflow engine after it was deserialized
        :param task:
        :param obj:
        """
        self.log.debug("Restarting workflow from %s object and %s task" %
                       (str(obj), str(task),))

        # set the point from which to start processing
        if obj == 'prev':
            # start with the previous object
            self._i[0] -= 2
            #TODO: check if there is any object there
        elif obj == 'current':
            # continue with the current object
            self._i[0] -= 1
        elif obj == 'next':
            pass
        else:
            raise Exception('Unknown start point for object: %s' % obj)

        # set the task that will be executed first
        if task == 'prev':
            # the previous
            self._i[1][-1] -= 1
        elif task == 'current':
            # restart the task again
            self._i[1][-1] -= 0
        elif task == 'next':
            # continue with the next task
            self._i[1][-1] += 1
        else:
            raise Exception('Unknown start pointfor task: %s' % obj)
        self.process(self._objects)
        self._unpickled = False

    @staticmethod
    def processing_factory(objects, self):
        """Default processing factory extended with saving objects
        before succesful processing.

        Default processing factory, will process objects in order

        :param objects: list of objects (passed in by self.process())

        :keyword cls: engine object itself, because this method may
            be implemented by the standalone function, we pass the
            self also as a cls argument

        As the WFE proceeds, it increments the internal counter, the
        first position is the number of the element. This pointer increases
        before the object is taken

        2nd pos is reserved for the array that points to the task position.
        The number there points to the task that is currently executed;
        when error happens, it will be there unchanged. The pointer is
        updated after the task finished running.
        """

        self.before_processing(objects, self)

        i = self._i
        # negative index not allowed, -1 is special
        while len(objects) - 1 > i[0] >= -1:
            i[0] += 1
            obj = objects[i[0]]
            obj.save(version=ObjectVersion.RUNNING,
                     id_workflow=self.db_obj.uuid)
            callbacks = self.callback_chooser(obj, self)

            if callbacks:
                try:
                    self.run_callbacks(callbacks, objects, obj)
                except StopProcessing:
                    if DEBUG:
                        msg = "Processing was stopped: '%s' (object: %s)" % \
                              (str(callbacks), repr(obj))
                        self.log.debug(msg)
                        obj.log.debug(msg)
                    break
                except JumpTokenBack as step:
                    if step.args[0] > 0:
                        raise WorkflowError("JumpTokenBack cannot"
                                            " be positive number")
                    if DEBUG:
                        self.log.debug('Warning, we go back [%s] objects' %
                                       step.args[0])
                    i[0] = max(-1, i[0] - 1 + step.args[0])
                    i[1] = [0]  # reset the callbacks pointer
                except JumpTokenForward as step:
                    if step.args[0] < 0:
                        raise WorkflowError("JumpTokenForward cannot"
                                            " be negative number")
                    if DEBUG:
                        self.log.debug('We skip [%s] objects' % step.args[0])
                    i[0] = min(len(objects), i[0] - 1 + step.args[0])
                    i[1] = [0]  # reset the callbacks pointer
                except ContinueNextToken:
                    if DEBUG:
                        self.log.debug('Stop processing for this object, '
                                       'continue with next')
                    i[1] = [0]  # reset the callbacks pointer
                    continue
                except HaltProcessing as e:
                    self.increase_counter_halted()
                    extra_data = obj.get_extra_data()
                    obj.set_extra_data(extra_data)

                    if DEBUG:
                        msg = 'Processing was halted at step: %s' % (i,)
                        self.log.info(msg)
                        obj.log.info(msg)
                    # Re-raise the exception,
                    # this is the only case when a WFE can be completely
                    # stopped
                    if type(e) == WorkflowHalt:
                        raise e
                    else:
                        raise WorkflowHalt(e)
                except Exception as e:
                    extra_data = obj.get_extra_data()
                    obj.set_extra_data(extra_data)
                    raise e
            # We save the object once it is fully run through
            obj.save(version=ObjectVersion.FINAL)
            self.increase_counter_finished()
            i[1] = [0]  # reset the callbacks pointer
        self.after_processing(objects, self)

    def execute_callback(self, callback, obj):
        """Executes the callback - override this method to implement logging"""
        obj.data = obj.get_data()
        obj.extra_data = obj.get_extra_data()
        obj.extra_data["_last_task_name"] = self.get_current_taskname()
        self.extra_data = self.get_extra_data()
        self.log.debug("Executing callback %s" % (repr(callback),))
        try:
            callback(obj, self)
        finally:
            self.set_extra_data(self.extra_data)
            obj.set_data(obj.data)
            obj.extra_data["_task_counter"] = self._i[1]
            obj.set_extra_data(obj.extra_data)

    def get_current_taskname(self):
        """
        Will attempt to return name of current task/step.
        Otherwise returns None.
        """
        callback_list = self.getCallbacks()
        if callback_list:
            for i in self.getCurrTaskId():
                callback_list = callback_list[i]
            if isinstance(callback_list, list):
                # With operator functions such as IF_ELSE
                # The final value is not a function, but a list.value
                # We currently then just take the __str__ of that list.
                return str(callback_list)
            return callback_list.func_name

    def get_current_object(self):
        """
        Returns the currently active BibWorkflowObject or
        None if no object is active.
        """
        obj_id = self.getCurrObjId()
        if obj_id < 0:
            return None
        return self._objects[obj_id]

    def halt(self, msg, widget=None):
        """Halt the workflow (stop also any parent wfe)"""
        raise WorkflowHalt(message=msg,
                           widget=widget,
                           id_workflow=self.uuid)

    def get_default_data_type(self):
        """
        Returns default data type from workflow
        definition.
        """
        return getattr(self.workflow_definition,
                       "object_type",
                       "")

    def set_counter_initial(self, obj_count):
        """

        :param obj_count:
        """
        self.db_obj.counter_initial = obj_count
        self.db_obj.counter_halted = 0
        self.db_obj.counter_error = 0
        self.db_obj.counter_finished = 0

    def increase_counter_halted(self):
        self.db_obj.counter_halted += 1

    def increase_counter_error(self):
        self.db_obj.counter_error += 1

    def increase_counter_finished(self):
        self.db_obj.counter_finished += 1

    def set_workflow_by_name(self, workflow_name):
        """

        :param workflow_name:
        """
        workflow = get_workflow_definition(workflow_name)
        self.workflow_definition = workflow
        self.setWorkflow(self.workflow_definition.workflow)

    def set_extra_data_params(self, **kwargs):
        """

        :param kwargs:
        """
        tmp = self.get_extra_data()
        if not tmp:
            tmp = {}
        for key, value in iteritems(kwargs):
            tmp[key] = value
        self.set_extra_data(tmp)
