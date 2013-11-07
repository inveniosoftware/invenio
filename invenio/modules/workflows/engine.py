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

import cPickle
import sys

from invenio.modules.workflows.models import (Workflow,
                                              BibWorkflowObject,
                                              BibWorkflowEngineLog)
from workflow.engine import (GenericWorkflowEngine,
                             ContinueNextToken,
                             HaltProcessing,
                             StopProcessing,
                             JumpTokenBack,
                             JumpTokenForward,
                             WorkflowError)

from invenio.ext.sqlalchemy import db
from datetime import datetime
from invenio.config import CFG_DEVEL_SITE
from invenio.bibworkflow_utils import get_workflow_definition
from uuid import uuid1 as new_uuid
from invenio.bibworkflow_utils import dictproperty
from invenio.bibworkflow_config import (CFG_WORKFLOW_STATUS,
                                        CFG_OBJECT_VERSION)
from invenio.modules.workflows.logger import (get_logger,
                                              BibWorkflowLogHandler)


DEBUG = CFG_DEVEL_SITE > 0


class BibWorkflowEngine(GenericWorkflowEngine):

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
                self._create_db_obj()

        db_handler_obj = BibWorkflowLogHandler(BibWorkflowEngineLog, "uuid")
        self.log = get_logger(logger_name="workflow.%s" % self.db_obj.uuid,
                              db_handler_obj=db_handler_obj,
                              obj=self)

        self.set_workflow_by_name(self.name)
        self.set_extra_data_params(**kwargs)

    def extra_data_get(self, key):
        if key not in self.db_obj.extra_data.keys():
            raise KeyError
        return self.db_obj.extra_data[key]

    def extra_data_set(self, key, value):
        self.db_obj.extra_data[key] = value

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
        # 1. Save workflow (ourselves).
        if not self.db_obj.uuid:
            self.save()
        self.set_counter_initial(len(objects))
        self.log.info("Workflow has been started")
        # 2. We want to save all the objects as version 0.
        for obj in objects:
            same_workflow = \
                obj.id_workflow and \
                obj.id_workflow == self.db_obj.uuid
            if obj.id and same_workflow:
                # If object exists and we are running the same workflow,
                # do nothing
                obj.log.info("object saving process : was already existing")
                continue
            # Set the current workflow id in the object
            if obj.version == CFG_OBJECT_VERSION.INITIAL \
                    and obj.id_workflow is not None:
                obj.log.info("object saving process : was already existing")
                pass
            else:
                obj.id_workflow = self.uuid
            obj.save(obj.version)
        GenericWorkflowEngine.before_processing(objects, self)

    @staticmethod
    def after_processing(objects, self):
        self._i = [-1, [0]]
        if self.has_completed():
            self.save(CFG_WORKFLOW_STATUS.COMPLETED)
        else:
            self.save(CFG_WORKFLOW_STATUS.FINISHED)

    def _create_db_obj(self):
        db.session.add(self.db_obj)
        db.session.commit()
        self.log.info("Workflow saved to db as new object.")

    def _update_db(self):
        db.session.commit()
        self.log.info("Workflow saved to db.")

    def has_completed(self):
        """
        Returns True of workflow is fully completed meaning
        that all associated objects are in FINAL state.
        """
        number_of_objects = BibWorkflowObject.query.filter(
            BibWorkflowObject.id_workflow == self.uuid,
            BibWorkflowObject.version.in_([CFG_OBJECT_VERSION.HALTED,
                                           CFG_OBJECT_VERSION.RUNNING])
        ).count()
        return number_of_objects == 0

    def save(self, status=CFG_WORKFLOW_STATUS.NEW):
        """
        Save the workflow instance to database.
        Just storing the necessary data.
        No serialization (!).

        Status: 0 - new, 1 - running, 2 - halted, 3 - error, 4 - finished
        """
        if not self.db_obj.uuid:
            # We do not have an ID,
            # so we need to add ourselves (first execution).
            self._create_db_obj()
        else:
            # This workflow continues a previous execution.
            if status in (CFG_WORKFLOW_STATUS.FINISHED,
                          CFG_WORKFLOW_STATUS.HALTED):
                self.db_obj.current_object = 0
            self.db_obj.modified = datetime.now()
            self.db_obj.status = status
            self._update_db()

    def process(self, objects):
        super(BibWorkflowEngine, self).process(objects)

    def restart(self, obj, task):
        """Restart the workflow engine after it was deserialized

        """
        self.log.info("Restarting workflow from %s object and %s task" %
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

        @var objects: list of objects (passed in by self.process())
        @keyword cls: engine object itself, because this method may
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
        while i[0] < len(objects) - 1 and i[0] >= -1:
            i[0] += 1
            obj = objects[i[0]]
            obj.log.info("Object is selected for processing")
            callbacks = self.callback_chooser(obj, self)

            if callbacks:
                try:
                    self.run_callbacks(callbacks, objects, obj)
                    i[1] = [0]  # reset the callbacks pointer
                except StopProcessing:
                    if DEBUG:
                        self.log.debug("Processing was stopped: '%s' "
                                       "(object: %s)" %
                                      (str(callbacks), repr(obj)))
                        obj.log.debug("Processing has stopped")
                    break
                except JumpTokenBack, step:
                    if step.args[0] > 0:
                        raise WorkflowError("JumpTokenBack cannot"
                                            " be positive number")
                    if DEBUG:
                        self.log.debug('Warning, we go back [%s] objects' %
                                       step.args[0])
                        obj.log.debug("Object preempted")
                    i[0] = max(-1, i[0] - 1 + step.args[0])
                    i[1] = [0]  # reset the callbacks pointer
                except JumpTokenForward, step:
                    if step.args[0] < 0:
                        raise WorkflowError("JumpTokenForward cannot"
                                            " be negative number")
                    if DEBUG:
                        self.log.debug('We skip [%s] objects' % step.args[0])
                        obj.log.debug("Object preempted")
                    i[0] = min(len(objects), i[0] - 1 + step.args[0])
                    i[1] = [0]  # reset the callbacks pointer
                except ContinueNextToken:
                    if DEBUG:
                        self.log.debug('Stop processing for this object, '
                                       'continue with next')
                        obj.log.debug("Object preempted")
                    i[1] = [0]  # reset the callbacks pointer
                    continue
                except HaltProcessing:
                    self.increase_counter_halted()
                    extra_data = obj.get_extra_data()
                    extra_data['redis_search']['halt_processing'] = self.getCurrTaskName()
                    obj.set_extra_data(extra_data)

                    if DEBUG:
                        self.log.info('Processing was halted at step: %s' % i)
                        # reraise the exception,
                        #this is the only case when a WFE can be completely
                        # stopped
                        obj.log.info("Object proccesing is halted")
                    raise

                except Exception:
                    self.log.info("Unexpected error: %s", sys.exc_info()[0])
                    obj.log.error("Something terribly wrong"
                                  " happend to this object")
                    extra_data = obj.get_extra_data()
                    extra_data['redis_search']['error'] = self.getCurrTaskName()
                    obj.set_extra_data(extra_data)
                    raise
            # We save the object once it is fully run through
            obj.save(CFG_OBJECT_VERSION.FINAL)
            obj.log.info("Object proccesing is finished")
            self.increase_counter_finished()
            self.log.info("Done saving object: %i" % (obj.id, ))
        self.after_processing(objects, self)

    def getCurrTaskName(self):
        return self._callbacks['*'][0][self.getCurrTaskId()[-1]].func_name

    def execute_callback(self, callback, obj):
        """Executes the callback - override this method to implement logging"""
        obj.data = obj.get_data()
        obj.extra_data = obj.get_extra_data()
        try:
            callback(obj, self)
        finally:
            obj.set_data(obj.data)
            obj.set_extra_data(obj.extra_data)

    def halt(self, msg):
        """Halt the workflow (stop also any parent wfe)"""
        self.log.debug("Processing halted at task %s with message: %s" %
                      (self.getCurrTaskId(), msg, ))
        raise HaltProcessing("Processing halted at task %s with message: %s" %
                             (self.getCurrTaskId(), msg, ))

    def set_counter_initial(self, obj_count):
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
        workflow = get_workflow_definition(workflow_name)
        self.workflow_definition = workflow
        self.setWorkflow(self.workflow_definition.workflow)

    def set_extra_data_params(self, **kwargs):
        for key, value in kwargs.iteritems():
            self.extra_data[key] = value
