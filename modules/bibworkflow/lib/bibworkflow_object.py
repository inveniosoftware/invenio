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

from invenio.bibworkflow_model import WfeObject
from datetime import datetime
from invenio.sqlalchemyutils import db
from invenio.bibworkflow_utils import dictproperty
from invenio.bibworkflow_config import add_log, \
     CFG_BIBWORKFLOW_OBJECTS_LOGDIR, CFG_OBJECT_VERSION
from invenio.config import CFG_LOGDIR



class BibWorkflowObject(object):

    def __init__(self, data=None, workflow_id=None, version=CFG_OBJECT_VERSION.INITIAL, parent_id=None,
                 id=None, extra_data=None, task_counter=[0], user_id=0, extra_object_class=None):
        self.extra_object_class = extra_object_class
        if isinstance(data, WfeObject):
            print "Create BibWorkflowObject, is instance and looks like = " + str(data)
            self.db_obj = data
        else:
            if id is not None:
                self.db_obj = WfeObject.query.filter(WfeObject.id == id).first()
            else:
                self.db_obj = WfeObject(data=data, workflow_id=workflow_id, \
                                        version=version, parent_id=parent_id, \
                                        task_counter=task_counter, user_id=user_id)
                self._create_db_obj()
        self.add_log()

    def add_log(self):
        self.log = add_log(os.path.join(CFG_BIBWORKFLOW_OBJECTS_LOGDIR,
            "object_%s_%s.log" % (self.db_obj.id, self.db_obj.workflow_id)),
            'object.%s' % self.db_obj.id)

    @property
    def data(self):
        return self.db_obj.data

    @data.setter
    def data(self, value):
        self.db_obj.data = value

    def extra_data_get(self, key):
        if key not in self.db_obj.extra_data.keys():
            raise KeyError
        return self.db_obj.extra_data[key]

    def extra_data_set(self, key, value):
        self.db_obj.extra_data[key] = value

    extra_data = dictproperty(fget=extra_data_get, fset=extra_data_set,
                      doc= "Sets up property")

    del extra_data_get, extra_data_set

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['log']
        return state

    def __setstate__(self, state):
        self.__dict__ = state
        self.add_log()

    def _update_db(self):
        db.session.commit()
        if self.extra_object_class:
            extra_obj = self.extra_object_class(self.db_obj)
            extra_obj.update()

    def _create_db_obj(self):
        db.session.add(self.db_obj)
        db.session.commit()
        if self.extra_object_class:
            extra_obj = self.extra_object_class(self.db_obj)
            extra_obj.save()
    
    def _create_version_obj(self, workflow_id, version, parent_id):
        obj = WfeObject(data=self.db_obj.data, \
                              workflow_id=workflow_id, \
                              version=version, \
                              parent_id=parent_id, \
                              task_counter=self.db_obj.task_counter, \
                              user_id=self.db_obj.user_id, \
                              extra_data=self.db_obj.extra_data)
        db.session.add(obj)
        db.session.commit()
        # Run extra save method
        if self.extra_object_class:
            extra_obj = self.extra_object_class(obj)
            extra_obj.save()
        
        return obj.id

    def save(self, version=None, task_counter=[0], workflow_id=None):
        """
        .update() should be changed to create new object,
        this will make function more constant and avoid code replication
         => save_object() could return than
        return int(o.id)
        """
        print "Parent id before save is: " + str(self.db_obj.parent_id)
        self.db_obj.task_counter = task_counter
        self.db_obj.modified = datetime.now()
        
        if not workflow_id:
            workflow_id = self.db_obj.workflow_id
        
        if version == CFG_OBJECT_VERSION.HALTED:
            # Processing was interrupted or error happened, we save the current state ("error" version)
            if self.db_obj.parent_id is not None:
                # We are a child, so we update ourselves.
                self._update_db()
                return int(self.db_obj.id)
            else:
                # First time this object has an error/interrupt. Add new child from this object. (version error)
                return int(self._create_version_obj(workflow_id, CFG_OBJECT_VERSION.HALTED, int(self.db_obj.id)))

        elif version == CFG_OBJECT_VERSION.FINAL:
            # This means the object was successfully run through the workflow. (finished version)
            # We update or insert the final object
            if self.db_obj.version == CFG_OBJECT_VERSION.FINAL:
                self._update_db()
                return int(self.db_obj.id)
            else:
                if self.db_obj.parent_id is not None:
                    parent_id = self.db_obj.parent_id
                else:
                    parent_id = self.db_obj.id
                return int(self._create_version_obj(workflow_id, CFG_OBJECT_VERSION.FINAL, parent_id))

        else:
            # version == 0
            # First save of the object (original version)
            self._create_db_obj()
            self.get_log().info('Saved in db')

    def changeStatus(self, message, save=False):
        return

    def set_log(self, log):
        self.log = log

    def get_log(self):
        return self.log

    def __repr__(self):
        return "<BibWorkflowObject(id: %s, data: %s, workflow_id: %s, version: %s, parent_id: %s)>" % (
        str(self.db_obj.id),
        str(self.db_obj.data),
        str(self.db_obj.workflow_id),
        str(self.db_obj.version),
        str(self.db_obj.parent_id)
        )
    
    def add_task_result(self, task_name, result):
        self.extra_data["tasks_results"][task_name] = result
        
    def add_metadata(self, key, value):
        self.extra_data[key] = value
        
    def changeStatus(self, message, save=False):
        self.db_obj.status = message
        
        if(save==True):
            self._update_db()
