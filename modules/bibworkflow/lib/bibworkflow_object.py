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
     CFG_BIBWORKFLOW_OBJECTS_LOGDIR
from invenio.config import CFG_LOGDIR


class BibWorkflowObject(object):

    def __init__(self, data=None, workflow_id=None, version=0, parent_id=None,
                 id=None, extra_data=None, task_counter=[0], user_id=0):
        if isinstance(data, WfeObject):
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

    def _create_db_obj(self):
        db.session.add(self.db_obj)
        db.session.commit()

    def save(self, version=None, task_counter=[0]):
        """
        .update() should be changed to create new object,
        this will make function more constant and avoid code replication
         => save_object() could return than
        return int(o.id)
        """
        self.db_obj.task_counter = task_counter
        self.db_obj.modified = datetime.now()
        if version == 2:
            # Processing was interrupted or error happened, we save the current state ("error" version)
            if self.db_obj.parent_id is not None:
                # We are a child, so we update ourselves.
                self._update_db()
                return int(self.db_obj.id)
            else:
                # First time this object has an error/interrupt. Add new child from this object. (version error)
                o = WfeObject(data=self.db_obj.data, \
                              workflow_id=self.db_obj.workflow_id, \
                              version=2, \
                              parent_id=int(self.db_obj.id), \
                              task_counter=self.db_obj.task_counter, \
                              user_id=self.db_obj.user_id)
                db.session.add(o)
                db.session.commit()
                return int(o.id)

        elif version == 1:
            # This means the object was successfully run through the workflow. (finished version)
            # We update or insert the final object
            if self.db_obj.version == 1:
                self._update_db()
                return int(self.db_obj.id)
            else:
                if self.db_obj.parent_id is not None:
                    parent_id = self.db_obj.parent_id
                else:
                    parent_id = self.db_obj.id
                o = WfeObject(data=self.db_obj.data, \
                              workflow_id=self.db_obj.workflow_id, \
                              version=1, \
                              parent_id=parent_id, \
                              task_counter=self.db_obj.task_counter, \
                              user_id=self.db_obj.user_id)
                db.session.add(o)
                db.session.commit()
                return int(o.id)

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
        return "<Object(id: %s, data: %s, workflow_id: %s, version: %s)>" % (
        str(self.db_obj.id),
        str(self.db_obj.data),
        str(self.db_obj.workflow_id),
        str(self.db_obj.version),
        )
