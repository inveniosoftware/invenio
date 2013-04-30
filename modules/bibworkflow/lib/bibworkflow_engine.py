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
import cPickle
import traceback

from invenio.bibworkflow_model import Workflow
from workflow.engine import GenericWorkflowEngine, \
    ContinueNextToken, \
    HaltProcessing, \
    StopProcessing, \
    JumpTokenBack, \
    JumpTokenForward, \
    WorkflowError
from datetime import datetime

from invenio.sqlalchemyutils import db
from invenio.config import CFG_DEVEL_SITE
from invenio.bibworkflow_utils import getWorkflowDefinition
from uuid import uuid1 as new_uuid
from invenio.bibworkflow_utils import dictproperty
from invenio.bibworkflow_config import add_log, \
    CFG_BIBWORKFLOW_WORKFLOWS_LOGDIR, \
    CFG_WORKFLOW_STATUS, \
    CFG_OBJECT_VERSION
DEBUG = CFG_DEVEL_SITE > 0


class BibWorkflowEngine(GenericWorkflowEngine):

    def __init__(self, name="Default workflow", uuid=None, curr_obj=0,
                 workflow_object=None, user_id=0, module_name="Unknown"):
        self.db_obj = None
        if isinstance(workflow_object, Workflow):
            self.db_obj = workflow_object
        else:
            # If uuid is defined we try to get the db object from DB.
            if uuid is not None:
                self.db_obj = \
                    Workflow.query.filter(Workflow.uuid == uuid).first()
            else:
                uuid = new_uuid()

            if self.db_obj is None:
                self.db_obj = Workflow(name=name, user_id=user_id,
                                       current_object=curr_obj,
                                       module_name=module_name, uuid=uuid)
                self._create_db_obj()

        super(BibWorkflowEngine, self).__init__()
        self.add_log()

    def add_log(self):
        self.log = add_log(os.path.join(CFG_BIBWORKFLOW_WORKFLOWS_LOGDIR,
                           "workflow_%s.log" % (self.db_obj.uuid, )),
                           'workflow.%s' % self.db_obj.uuid)

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
            raise cPickle.PickleError("The workflow instance inconsistent state, "
                                      "too few objects")
        self.__dict__ = state
        self.add_log()

    def __repr__(self):
        return "<BibWorkflow_engine(%s)>" % (self.db_obj.name,)

    @staticmethod
    def before_processing(objects, self):
        """
        Executed before processing the workflow.
        """
        # 1. Save workflow (ourselves).
        if not self.db_obj.uuid:
            self.save()
        self.setCounterInitial(objects)
        self.log.info("[%s], %s has been started" % (str(datetime.now()),
                      str(self.db_obj.name)))
        # 2. We want to save all the objects as version 0.
        for o in objects:
            same_workflow = \
                o.db_obj.workflow_id and \
                o.db_obj.workflow_id == self.db_obj.uuid
            if o.db_obj.id and same_workflow:
                # If object exists and we are running the same workflow,
                # do nothing
                continue
            # Set the current workflow id in the object

            if o.db_obj.version == CFG_OBJECT_VERSION.INITIAL \
               and o.db_obj.workflow_id is not None:
                pass
            else:
                o.db_obj.workflow_id = self.db_obj.uuid
            o.save(CFG_OBJECT_VERSION.INITIAL)
        GenericWorkflowEngine.before_processing(objects, self)

    @staticmethod
    def after_processing(objects, self):
        GenericWorkflowEngine.after_processing(objects, self)
        self.save(CFG_WORKFLOW_STATUS.FINISHED)

    def _create_db_obj(self):
        db.session.add(self.db_obj)
        db.session.commit()

    def _update_db(self):
        db.session.commit()

    def save(self, status=CFG_WORKFLOW_STATUS.NEW, e=""):
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
            if status in (CFG_WORKFLOW_STATUS.FINISHED, CFG_WORKFLOW_STATUS.HALTED):
                self.db_obj.current_object = 0
            self.db_obj.modified = datetime.now()
            self.db_obj.status = status
            self._update_db()

    def process(self, objects, external_save=None):
        self.external_save = external_save
        super(BibWorkflowEngine, self).process(objects)

    def restart(self, obj, task, objects=None, external_save=None):
        """Restart the workflow engine after it was deserialized

        """

        if self._unpickled is not True:
            raise Exception("You can call this method only after loading serialized engine")
        if len(self.getCallbacks(key=None)) == 0:
            raise Exception("The callbacks are empty, did you set workflows?")

        # set the point from which to start processing
        if obj == 'prev': # start with the previous object
            self._i[0] -= 2 #TODO: check if there is any object there
        elif obj == 'current': # continue with the current object
            self._i[0] -= 1
        elif obj == 'next':
            pass
        else:
            raise Exception('Unknown start point for object: %s' % obj)

        # set the task that will be executed first
        if task == 'prev': # the previous
            self._i[1][-1] -= 1
        elif task == 'current': # restart the task again
            self._i[1][-1] -= 0
        elif task == 'next': # continue with the next task
            self._i[1][-1] += 1
        else:
            raise Exception('Unknown start pointfor task: %s' % obj)

        if objects:
            self.process(objects, external_save=external_save)
        else:
            self.process(self._objects, external_save=external_save)

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
                        obj.get_log().info("Processing has stopped")
                    break
                except JumpTokenBack, step:
                    if step.args[0] > 0:
                        raise WorkflowError("JumpTokenBack cannot be positive number")
                    if DEBUG:
                        self.log.debug('Warning, we go back [%s] objects' %
                                       step.args[0])
                    i[0] = max(-1, i[0] - 1 + step.args[0])
                    i[1] = [0]  # reset the callbacks pointer
                except JumpTokenForward, step:
                    if step.args[0] < 0:
                        raise WorkflowError("JumpTokenForward cannot be negative number")
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
                except HaltProcessing:
                    self.increaseCounterHalted()
                    if DEBUG:
                        self.log.debug('Processing was halted at step: %s' % i)
                        # reraise the exception,
                        #this is the only case when a WFE can be completely
                        # stopped
                    raise
            # We save the object once it is fully run through
            obj.save(CFG_OBJECT_VERSION.FINAL)
            self.increaseCounterFinished()

            ##### Update the workflow
            ####self.save()

            obj.get_log().info('Success!')
            self.log.debug("Done saving object in: %s" % (self,))

        self.after_processing(objects, self)

    def halt(self, msg):
        """Halt the workflow (stop also any parent wfe)"""
        raise HaltProcessing("Processing halted at task %s with message: %s" %
                             (self.getCurrTaskId(), msg, ))

    def setCounterInitial(self, obj_list):
        self.db_obj.counter_initial = len(obj_list)
        self.db_obj.counter_halted = 0
        self.db_obj.counter_error = 0
        self.db_obj.counter_finished = 0

    def increaseCounterHalted(self):
        self.db_obj.counter_halted += 1

    def increaseCounterError(self):
        self.db_obj.counter_error += 1

    def increaseCounterFinished(self):
        self.db_obj.counter_finished += 1

    def setWorkflowByName(self, workflow_name):
        workflow = getWorkflowDefinition(workflow_name)
        self.setWorkflow(workflow)
