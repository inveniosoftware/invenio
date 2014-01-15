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


import os
import tempfile
from six.moves import cPickle
import base64
import logging
import six

from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound
from invenio.ext.sqlalchemy import db
from invenio.base.globals import cfg
from .config import CFG_OBJECT_VERSION
from .utils import redis_create_search_entry, WorkflowsTaskResult

from .logger import (get_logger,
                     BibWorkflowLogHandler)


def get_default_data():
    """ Returns the base64 representation of the data default value """
    data_default = {}
    return base64.b64encode(cPickle.dumps(data_default))


def get_default_extra_data():
    """ Returns the base64 representation of the extra_data default value """
    extra_data_default = {"_tasks_results": [],
                          "owner": {},
                          "task_counter": {},
                          "error_msg": "",
                          "_last_task_name": "",
                          "latest_object": -1,
                          "widget": None,
                          "redis_search": {}}
    return base64.b64encode(cPickle.dumps(extra_data_default))


class Workflow(db.Model):

    __tablename__ = "bwlWORKFLOW"

    uuid = db.Column(db.String(36), primary_key=True, nullable=False)

    name = db.Column(db.String(255), default="Default workflow",
                     nullable=False)
    created = db.Column(db.DateTime, default=datetime.now, nullable=False)
    modified = db.Column(db.DateTime, default=datetime.now,
                         onupdate=datetime.now, nullable=False)
    id_user = db.Column(db.Integer, default=0, nullable=False)
    _extra_data = db.Column(db.LargeBinary, nullable=False, default=get_default_extra_data())
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
                             str(self._extra_data),)

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

    def get_extra_data(self, user_id=0, uuid=None, key=None, getter=None):
        """Returns a json of the column extra_data or
        if any of the other arguments are defined,
        a specific value.
        You can define either the key or the getter function.

        @param key: the key to access the desirable value
        @param getter: a callable that takes a dict as param and returns a
        value
        """
        extra_data = Workflow.get(Workflow.id_user == self.id_user,
                                  Workflow.uuid == self.uuid).one()._extra_data

        extra_data = cPickle.loads(base64.b64decode(extra_data))
        if key is not None:
            return extra_data[key]
        elif callable(getter):
            return getter(extra_data)

    def set_extra_data(self, user_id=0, uuid=None,
                       key=None, value=None, setter=None):
        """Modifies the json of the column extra_data or
        if any of the other arguments are defined,
        a specific value.
        You can define either the key, value or the setter function.

        @param key: the key to access the desirable value
        @param value: the new value
        @param setter: a callable that takes a dict as param and modifies it
        """
        extra_data = Workflow.get(Workflow.id_user == user_id,
                                  Workflow.uuid == uuid).one()._extra_data
        extra_data = cPickle.loads(base64.b64decode(extra_data))
        if key is not None and value is not None:
            extra_data[key] = value
        elif callable(setter):
            setter(extra_data)

        Workflow.get(Workflow.uuid == self.uuid).update({'_extra_data': base64.b64encode(cPickle.dumps(extra_data))})

    @classmethod
    def delete(cls, uuid=None):
        cls.get(Workflow.uuid == uuid).delete()
        db.session.commit()


class BibWorkflowObject(db.Model):
    # db table definition
    __tablename__ = "bwlOBJECT"

    id = db.Column(db.Integer, primary_key=True)

    # Our internal data column. Default is encoded dict.
    _data = db.Column(db.LargeBinary, nullable=False, default=get_default_data())
    _extra_data = db.Column(db.LargeBinary, nullable=False, default=get_default_extra_data())

    id_workflow = db.Column(db.String(36),
                            db.ForeignKey("bwlWORKFLOW.uuid"), nullable=True)
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
    persistent_ids = db.Column(db.JSON, default= {} ,nullable=True)
    data_type = db.Column(db.String(150), default=DATA_TYPES.ANY,
                          nullable=True)

    uri = db.Column(db.String(500), default="")
    id_user = db.Column(db.Integer, default=0, nullable=False)
    child_logs = db.relationship("BibWorkflowObjectLog")
    workflow = db.relationship(
        Workflow, foreign_keys=[id_workflow], remote_side=Workflow.uuid
    )

    _log = None

    @property
    def log(self):
        if not self._log:
            db_handler_obj = BibWorkflowLogHandler(BibWorkflowObjectLog, "id")
            self._log = get_logger(logger_name="object.%s_%s" % (self.id_workflow, self.id),
                                   db_handler_obj=db_handler_obj,
                                   loglevel=logging.DEBUG,
                                   obj=self)
        return self._log

    def get_data(self):
        """
        Main method to retrieve data saved to the object.
        """

        return cPickle.loads(base64.b64decode(self._data))

    def set_data(self, value):
        """
        Main method to update data saved to the object.
        """
        self._data = base64.b64encode(cPickle.dumps(value))

    def get_extra_data(self):
        """
        Main method to retrieve data saved to the object.
        """
        return cPickle.loads(base64.b64decode(self._extra_data))

    def set_extra_data(self, value):
        """
        Main method to update data saved to the object.
        """
        self._extra_data = base64.b64encode(cPickle.dumps(value))

    def _create_db_obj(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<BibWorkflowObject(id = %s, data = %s, id_workflow = %s, " \
               "version = %s, id_parent = %s, created = %s, extra_data = %s)" \
               % (str(self.id), str(self.get_data()), str(self.id_workflow),
                  str(self.version), str(self.id_parent), str(self.created),
                  str(self.get_extra_data()))

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
       str(self.get_data()),
       str(self.get_extra_data),)

    def __eq__(self, other):
        if isinstance(other, BibWorkflowObject):
            if self._data == other._data and \
                    self._extra_data == other._extra_data and \
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
        return not self.__eq__(other)

    def add_task_result(self, name, result):
        """
        Adds given task results to extra_data in order to be accessed
        and displayed later on by Holding Pen templates.
        """
        task_name = self.extra_data["_last_task_name"]
        res_obj = WorkflowsTaskResult(task_name, name, result)
        self.extra_data["_tasks_results"].append(res_obj)

    def add_widget(self, widget, message):
        extra_data = self.get_extra_data()
        extra_data["_widget"] = widget
        extra_data["_message"] = message
        self.set_extra_data(extra_data)

    def remove_widget(self):
        extra_data = self.get_extra_data()
        extra_data["_widget"] = None
        extra_data["_message"] = ""
        self.set_extra_data(extra_data)

    def change_status(self, message):
        self.status = message

    def get_current_task(self):
        return self.get_extra_data()["task_counter"]

    def _create_version_obj(self, id_workflow, version, id_parent=None,
                            no_update=False):

        obj = BibWorkflowObject(_data=self._data,
                                id_workflow=id_workflow,
                                version=version,
                                id_parent=id_parent,
                                _extra_data=self._extra_data,
                                status=self.status,
                                data_type=self.data_type)

        db.session.add(obj)
        db.session.commit()
        if version is CFG_OBJECT_VERSION.INITIAL and not no_update:
            self.id_parent = obj.id
            db.session.commit()
        return obj.id

    def _update_db(self):
        db.session.add(self)
        db.session.commit()

    def save(self, version=None, task_counter=[0], id_workflow=None):
        """
        Saved object
        """
        if not self.id:
            db.session.add(self)
            db.session.commit()

        extra_data = self.get_extra_data()
        extra_data["_task_counter"] = task_counter
        self.set_extra_data(extra_data)

        if not id_workflow:
            id_workflow = self.id_workflow

        if version:
            self.version = version
            if version in (CFG_OBJECT_VERSION.FINAL, CFG_OBJECT_VERSION.HALTED):
                redis_create_search_entry(self)
            self._update_db()

    def save_to_file(self, directory=None,
                     prefix="workflow_object_data_", suffix=".obj"):
        """
        Saves the contents of self.data['data'] to file.

        Returns path to saved file.

        Warning: Currently assumes non-binary content.
        """
        if directory is None:
            directory = cfg['CFG_TMPSHAREDIR']
        tmp_fd, filename = tempfile.mkstemp(dir=directory,
                                            prefix=prefix,
                                            suffix=suffix)
        os.write(tmp_fd, self.get_data())
        os.close(tmp_fd)
        return filename

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def copy(self, other):
        """Copies data and metadata except id and id_workflow"""
        self._data = other._data
        self._extra_data = other._extra_data
        self.version = other.version
        self.id_parent = other.id_parent
        self.created = other.created
        self.modified = other.modified
        self.status = other.status
        self.data_type = other.data_type
        self.uri = other.uri

    def get_formatted_data(self, format=None, formatter=None):
        """
        Returns the data in some chewable format.
        """
        from invenio.modules.records.api import Record
        from invenio.modules.formatter.engine import format_record

        data = self.get_data()

        if formatter:
            # A seperate formatter is supplied
            return formatter(data)

        if isinstance(data, dict):
            # Dicts are cool on its own, but maybe its SmartJson (record)
            try:
                new_dict_representation = Record(data)
                data = new_dict_representation.legacy_export_as_marc()
            except Exception as e:
                raise e

        if isinstance(data, six.string_types):
            # Its a string type, lets try to convert
            if format:
                # We can try formatter!
                # If already XML, format_record does not like it.
                if format != 'xm':
                    try:
                        return format_record(recID=None,
                                             of=format,
                                             xml_record=data)
                    except TypeError as e:
                        # Wrong kind of type
                        pass
                else:
                    # So, XML then
                    from xml.dom.minidom import parseString
                    try:
                        pretty_data = parseString(data)
                        return pretty_data.toprettyxml()
                    except TypeError:
                        # Probably not proper XML string then
                        return "Data cannot be parsed: %s" % (data,)
                    except Exception:
                        # Some other parsing error
                        pass
            # Just return raw string
            return data
        # Not any of the above types. How juicy!
        return data


class BibWorkflowObjectLog(db.Model):
    """
    This class represent a record of a log emit by an object
    into the database the object must be saved before using
    this class. Indeed it needs the id of the object into
    the database.
    """
    __tablename__ = 'bwlOBJECTLOGGING'
    id = db.Column(db.Integer, primary_key=True)
    id_object = db.Column(db.Integer(255),
                          db.ForeignKey('bwlOBJECT.id'),
                          nullable=False)
    log_type = db.Column(db.Integer, default=0, nullable=False)
    created = db.Column(db.DateTime, default=datetime.now)
    message = db.Column(db.TEXT, default="", nullable=False)

    def __repr__(self):
        return "<BibWorkflowObjectLog(%i, %s, %s, %s)>" % \
               (self.id, self.id_object, self.message, self.created)

    @classmethod
    def get(cls, *criteria, **filters):
        """ A wrapper for the filter and filter_by functions of sqlalchemy.
        Define a dict with which columns should be filtered by which values.

        look up also sqalchemy BaseQuery's filter and filter_by documentation
        """
        return cls.query.filter(*criteria).filter_by(**filters)

    @classmethod
    def get_most_recent(cls, *criteria, **filters):
        """ Returns the most recently created log. """

        most_recent = cls.get(*criteria, **filters).\
            order_by(desc(BibWorkflowObjectLog.created)).first()
        if most_recent is None:
            raise NoResultFound
        else:
            return most_recent

    @classmethod
    def delete(cls, id=None):
        cls.get(BibWorkflowObjectLog.id == id).delete()
        db.session.commit()


class BibWorkflowEngineLog(db.Model):
    __tablename__ = "bwlWORKFLOWLOGGING"
    id = db.Column(db.Integer, primary_key=True)
    id_object = db.Column(db.String(255), nullable=False)
    log_type = db.Column(db.Integer, default=0, nullable=False)
    created = db.Column(db.DateTime, default=datetime.now)
    message = db.Column(db.TEXT, default="", nullable=False)

    def __repr__(self):
        return "<BibWorkflowEngineLog(%i, %s, %s, %s)>" % \
               (self.id, self.id_object, self.message, self.created)

    @classmethod
    def get(cls, *criteria, **filters):
        """ A wrapper for the filter and filter_by functions of sqlalchemy.
        Define a dict with which columns should be filtered by which values.

        look up also sqalchemy BaseQuery's filter and filter_by documentation
        """
        return cls.query.filter(*criteria).filter_by(**filters)

    @classmethod
    def get_most_recent(cls, *criteria, **filters):
        """ Returns the most recently created log. """

        most_recent = cls.get(*criteria, **filters).\
            order_by(desc(BibWorkflowEngineLog.created)).first()
        if most_recent is None:
            raise NoResultFound
        else:
            return most_recent

    @classmethod
    def delete(cls, uuid=None):
        cls.get(BibWorkflowEngineLog.id == uuid).delete()
        db.session.commit()


__all__ = ['Workflow', 'BibWorkflowObject', 'BibWorkflowObjectLog', 'BibWorkflowEngineLog']
