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
import tempfile
import json

from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound
from invenio.sqlalchemyutils import db
from invenio.bibworkflow_config import CFG_OBJECT_VERSION,\
    CFG_LOG_TYPE
from invenio.config import CFG_TMPSHAREDDIR
from invenio.bibworkflow_utils import determineDataType


class WorkflowLogging(db.Model):
    __tablename__ = "bwlWORKFLOWLOGGING"
    id = db.Column(db.Integer, primary_key=True)
    id_workflow = db.Column(db.String(255), nullable=False)
    log_type = db.Column(db.Integer, default=0, nullable=False)
    created = db.Column(db.DateTime, default=datetime.now)
    message = db.Column(db.String(500), default="", nullable=False)
    error_msg = db.Column(db.TEXT, default="", nullable=False)
    extra_data = db.Column(db.JSON, default={})

    def __repr__(self):
        return "<WorkflowLog(%i, %s, %s, %s)>" % \
               (self.id, self.id_workflow, self.message, self.created)


class BibWorkflowObjectLogging(db.Model):
    """
    This class represent a record of a log emit by an object
    into the database the object must be saved before using
    this class. Indeed it needs the id of the object into
    the database.
    """
    #db table definition
    __tablename__ = 'bwlOBJECTLOGGING'
    id = db.Column(db.Integer, primary_key=True)
    id_bibworkflowobject = db.Column(db.Integer(255),
                                     db.ForeignKey('bwlOBJECT.id'),
                                     nullable=False)
    log_type = db.Column(db.Integer, default=0, nullable=False)
    created = db.Column(db.DateTime, default=datetime.now)
    message = db.Column(db.String(500), default="", nullable=False)
    error_msg = db.Column(db.TEXT, default="", nullable=False)
    extra_data = db.Column(db.JSON, default={})

    ###
    #This function should be use only for debug purpose
    #Normal log acces should be done throught the database
    #That's all
    ###
    def __repr__(self):
        return "<ObjectLog(%i, %s, %s, %s)>" % \
               (self.id, self.id_bibworkflowobject, self.message, self.created)


class Workflow(db.Model):
    __tablename__ = "bwlWORKFLOW"
    uuid = db.Column(db.String(36), primary_key=True, nullable=False)
    name = db.Column(db.String(255), default="Default workflow",
                     nullable=False)
    created = db.Column(db.DateTime, default=datetime.now, nullable=False)
    modified = db.Column(db.DateTime, default=datetime.now,
                         onupdate=datetime.now, nullable=False)
    id_user = db.Column(db.Integer, default=0, nullable=False)
    extra_data = db.Column(db.JSON, default={})
    status = db.Column(db.Integer, default=0, nullable=False)
    current_object = db.Column(db.Integer, default="0", nullable=False)
    objects = db.relationship("BibWorkflowObject", backref="bwlWORKFLOW")
    counter_initial = db.Column(db.Integer, default=0, nullable=False)
    counter_halted = db.Column(db.Integer, default=0, nullable=False)
    counter_error = db.Column(db.Integer, default=0, nullable=False)
    counter_finished = db.Column(db.Integer, default=0, nullable=False)
    module_name = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return "<Workflow(name: %s, module: %s, cre: %s, mod: %s," \
               "id_user: %s, status: %s)>" % \
            (str(self.name),
             str(self.module_name),
             str(self.created),
             str(self.modified),
             str(self.id_user),
             str(self.status))

    def __str__(self):
        return """Workflow:

        Uuid: %s
        Name: %s
        User id: %s
        Module name: %s
        Created: %s
        Modified: %s
        Status: %s
        Current object: %s
        Counters: initial=%s, halted=%s, error=%s, finished=%s
        Extra data: %s""" % (str(self.uuid),
                             str(self.name),
                             str(self.id_user),
                             str(self.module_name),
                             str(self.created),
                             str(self.modified),
                             str(self.status),
                             str(self.current_object),
                             str(self.counter_initial),
                             str(self.counter_halted),
                             str(self.counter_error),
                             str(self.counter_finished),
                             str(self.extra_data),)

    @classmethod
    def get(cls, *criteria, **filters):
        """ A wrapper for the filter and filter_by functions of sqlalchemy.
        Define a dict with which columns should be filtered by which values.

        e.g. Workflow.get(uuid=uuid)
             Workflow.get(Workflow.uuid != uuid)

        The function supports also "hybrid" arguments.
        e.g. Workflow.get(Workflow.module_name != 'i_hate_this_module',
                          user_id=user_id)

        look up also sqalchemy BaseQuery's filter and filter_by documentation
        """
        return cls.query.filter(*criteria).filter_by(**filters)

    @classmethod
    def get_status(cls, uuid=None):
        """ Returns the status of the workflow """
        return cls.get(Workflow.uuid == uuid).one().status

    @classmethod
    def get_most_recent(cls, *criteria, **filters):
        """ Returns the most recently modified workflow. """

        most_recent = cls.get(*criteria, **filters).\
                          order_by(desc(Workflow.modified)).first()
        if most_recent is None:
            raise NoResultFound
        else:
            return most_recent

    @classmethod
    def get_objects(cls, uuid=None):
        """ Returns the objects of the workflow """
        return cls.get(Workflow.uuid == uuid).one().objects

    @classmethod
    def get_extra_data(cls, user_id=None, uuid=None, key=None, getter=None):
        """Returns a json of the column extra_data or
        if any of the other arguments are defined,
        a specific value.
        You can define either the key or the getter function.

        @param key: the key to access the desirable value
        @param getter: a callable that takes a dict as param and returns a
        value
        """
        extra_data = cls.get(Workflow.id_user == user_id,
                             Workflow.uuid == uuid).one().extra_data

        if key is not None:
            return extra_data[key]
        elif callable(getter):
            return getter(extra_data)

    @classmethod
    def set_extra_data(cls, user_id=None, uuid=None,
                       key=None, value=None, setter=None):
        """Modifies the json of the column extra_data or
        if any of the other arguments are defined,
        a specific value.
        You can define either the key, value or the setter function.

        @param key: the key to access the desirable value
        @param value: the new value
        @param setter: a callable that takes a dict as param and modifies it
        """
        extra_data = cls.get(Workflow.id_user == user_id,
                             Workflow.uuid == uuid).one().extra_data

        if key is not None and value is not None:
            extra_data[key] = value
        elif callable(setter):
            setter(extra_data)

        cls.get(Workflow.uuid == uuid).update({'extra_data': extra_data})

    @classmethod
    def delete(cls, uuid=None):
        cls.get(Workflow.uuid == uuid).delete()
        db.session.commit()


class BibWorkflowObject(db.Model):
    # db table definition
    __tablename__ = "bwlOBJECT"
    id = db.Column(db.Integer, primary_key=True)
    _data = db.Column(db.JSON, nullable=False)
    extra_data = db.Column(db.JSON,
                           nullable=False, default={"tasks_results": {},
                                                    "owner": {},
                                                    "task_counter": {},
                                                    "error_msg": "",
                                                    "last_task_name": "",
                                                    "latest_object": -1})
    id_workflow = db.Column(db.String(36),
                            db.ForeignKey("bwlWORKFLOW.uuid"), nullable=False)
    version = db.Column(db.Integer(3),
                        default=CFG_OBJECT_VERSION.RUNNING, nullable=False)
    id_parent = db.Column(db.Integer, db.ForeignKey("bwlOBJECT.id"),
                          default=None)
    child_objects = db.relationship("BibWorkflowObject",
                                    remote_side=[id_parent])
    created = db.Column(db.DateTime, default=datetime.now, nullable=False)
    modified = db.Column(db.DateTime, default=datetime.now,
                         onupdate=datetime.now, nullable=False)
    status = db.Column(db.String(255), default="", nullable=False)
    data_type = db.Column(db.String(50), default=determineDataType,
                          nullable=False)
    uri = db.Column(db.String(500), default="")
    child_logs = db.relationship("BibWorkflowObjectLogging")
    _old_data = None

    def get_data_by_id(self, id):
        return self.query.filter(BibWorkflowObject.id == id).first()

    @property
    def data(self):
        return self._data['data']

    @data.setter
    def data(self, data):
        self._data = {'data': data}

    def log_info(self, message, error_msg=""):
        log_obj = BibWorkflowObjectLogging(id_bibworkflowobject=self.id,
                                           log_type=CFG_LOG_TYPE.INFO,
                                           message=message,
                                           error_msg=error_msg,
                                           extra_data=self.extra_data)
        db.session.add(log_obj)

    def log_error(self, message, error_msg=""):
        log_obj = BibWorkflowObjectLogging(id_bibworkflowobject=self.id,
                                           log_type=CFG_LOG_TYPE.ERROR,
                                           message=message,
                                           error_msg=error_msg,
                                           extra_data=self.extra_data)
        db.session.add(log_obj)

    def log_debug(self, message, error_msg=""):
        log_obj = BibWorkflowObjectLogging(id_bibworkflowobject=self.id,
                                           log_type=CFG_LOG_TYPE.DEBUG,
                                           message=message,
                                           error_msg=error_msg,
                                           extra_data=self.extra_data)
        db.session.add(log_obj)

    def _create_db_obj(self):
        db.session.add(self)
        db.session.commit()
        #if self.extra_object_class:
        #    extra_obj = self.extra_object_class(self.db_obj)
        #    extra_obj.save()

    def __repr__(self):
        repr = "<BibWorkflowObject(id = %s, data = %s, id_workflow = %s, " \
               "version = %s, id_parent = %s, created = %s, extra_data = %s)" \
               % (str(self.id), str(self.data), str(self.id_workflow),
                  str(self.version), str(self.id_parent), str(self.created),
                  str(self.extra_data))
        return repr

    def __str__(self, log=False):
        return """
-------------------------------
BibWorkflowObject
-------------------------------
    Extra object class:
    Self status: %s
-------------------------------
    BibWorkflowObject:

        Id: %s
        Parent id: %s
        Workflow id: %s
        Created: %s
        Modified: %s
        Version: %s
        DB_obj status: %s
        Data type: %s
        URI: %s
        Data: %s
        Extra data: %s
-------------------------------
""" % (str(self.status),
       str(self.id),
       str(self.id_parent),
       str(self.id_workflow),
       str(self.created),
       str(self.modified),
       str(self.version),
       str(self.status),
       str(self.data_type),
       str(self.uri),
       str(self.data),
       str(self.extra_data),)
       # str(self.extra_object_class),

    def __eq__(self, other):
        if isinstance(other, BibWorkflowObject):
            if self.data == other.data and \
                    self.extra_data == other.extra_data and \
                    self.id_workflow == other.id_workflow and \
                    self.version == other.version and \
                    self.id_parent == other.id_parent and \
                    isinstance(self.created, datetime) and \
                    isinstance(self.modified, datetime):
                return True
            else:
                return False
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, BibWorkflowObject):
            if self.data == other.data and \
                    self.extra_data == other.extra_data and \
                    self.id_workflow == other.id_workflow and \
                    self.version == other.version and \
                    self.id_parent == other.id_parent and \
                    isinstance(self.created, datetime) and \
                    isinstance(self.modified, datetime):
                return False
            else:
                return True
        return False

    def add_task_result(self, task_name, result):
        self.extra_data["tasks_results"][task_name] = result

    def add_metadata(self, key, value):
        self.extra_data[key] = value

    def changeStatus(self, message):
        self.status = message

    def getCurrentTask(self):
        return self.extra_data["task_counter"]

    def _create_version_obj(self, id_workflow, version, id_parent=None,
                            no_update=False):
        obj = BibWorkflowObject(data=self.data,
                                id_workflow=id_workflow,
                                version=version,
                                id_parent=id_parent,
                                extra_data=self.extra_data,
                                status=self.status,
                                data_type=self.data_type)
        db.session.add(obj)
        db.session.commit()
        if version is CFG_OBJECT_VERSION.INITIAL and not no_update:
            self.id_parent = obj.id
            db.session.commit()
        return obj.id

    def _update_db(self):
        new_data = hash(json.dumps(self._data))
        if self._old_data != new_data:
            self._old_data = new_data
            self._data.changed()
        db.session.add(self)
        db.session.commit()
        self.log_info("Object saved")

        #if self.extra_object_class:
        #    extra_obj = self.extra_object_class(self)
        #    extra_obj.update()

    def save(self, version=None, task_counter=[0], id_workflow=None):
        """
        Saved object
        """
        if not self.id:
            db.session.add(self)
            db.session.commit()
        self.extra_data["task_counter"] = task_counter

        if not id_workflow:
            id_workflow = self.id_workflow

        if version:
            self.version = version
            self._update_db()

    def save_to_file(self, directory=CFG_TMPSHAREDDIR,
                     prefix="bibworkflow_object_data_", suffix=".obj"):
        """
        Saves the contents of self.data['data'] to file.

        Returns path to saved file.

        Warning: Currently assumes non-binary content.
        """
        if "data" in self.data:
            tmp_fd, filename = tempfile.mkstemp(dir=directory,
                                                prefix=prefix,
                                                suffix=suffix)
            os.write(tmp_fd, self.data['data'])
            os.close(tmp_fd)
        return filename

    def __getstate__(self):
        return {"data": self.data,
                "id_workflow": self.id_workflow,
                "version": self.version,
                "id_parent": self.id_parent,
                "created": self.created,
                "modified": self.modified,
                "status": self.status,
                "data_type": self.data_type,
                "uri": self.uri,
                "extra_data": self.extra_data}

    def __setstate__(self, state):
        self.data = state["data"]
        self.id_workflow = state["id_workflow"]
        self.version = state["version"]
        self.id_parent = state["id_parent"]
        self.created = state["created"]
        self.modified = state["modified"]
        self.extra_data = state["extra_data"]
        self.status = state["status"]
        self.data_type = state["data_type"]
        self.uri = state["uri"]

    def copy(self, other):
        """Copies data and metadata except id and id_workflow"""
        self.data = other.data
        self.extra_data = other.extra_data
        self.version = other.version
        self.id_parent = other.id_parent
        self.created = other.created
        self.modified = datetime.now()
        self.owner = other.owner
        self.status = other.status
        self.data_type = other.data_type
        self.uri = other.uri


def load_a(*args, **kwargs):
    args[0]._old_data = json.dumps(args[0]._data)
    pass

from sqlalchemy import event
from sqlalchemy.orm.events import InstanceEvents
event.listen(BibWorkflowObject, 'load', load_a)


__all__ = ['Workflow', 'BibWorkflowObject', 'WorkflowLogging',
           'AuditLogging', 'TaskLogging', 'BibWorkflowObjectLogging']
