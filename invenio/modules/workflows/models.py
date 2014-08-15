# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2012, 2013, 2014 CERN.
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

"""Models for BibWorkflow Objects."""

import os
import tempfile
import base64
import logging
from six.moves import cPickle
from six import iteritems, callable
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound
from invenio.ext.sqlalchemy import db
from invenio.base.globals import cfg

from .utils import (WorkflowsTaskResult,
                    session_manager)
from .logger import get_logger, BibWorkflowLogHandler


class ObjectVersion(object):

    """Specify the different versions possible."""

    INITIAL = 0
    FINAL = 1
    HALTED = 2
    RUNNING = 3
    MAPPING = {0: "New", 1: "Done", 2: "Need action",
               3: "In process"}
    REVERSE_MAPPING = {"New": 0, "Done": 1, "Need action": 2,
                       "In process": 3}


def get_default_data():
    """Return the base64 representation of the data default value."""
    data_default = {}
    return base64.b64encode(cPickle.dumps(data_default))


def get_default_extra_data():
    """Return the base64 representation of the extra_data default value."""
    extra_data_default = {"_tasks_results": {},
                          "owner": {},
                          "_task_counter": {},
                          "_error_msg": None,
                          "_last_task_name": "",
                          "latest_object": -1,
                          "_action": None,
                          "redis_search": {},
                          "source": ""}
    return base64.b64encode(cPickle.dumps(extra_data_default))


class Workflow(db.Model):

    """Represents a workflow instance.

    Used by BibWorkflowEngine to store the state of the workflow.
    """

    __tablename__ = "bwlWORKFLOW"

    uuid = db.Column(db.String(36), primary_key=True, nullable=False)

    name = db.Column(db.String(255), default="Default workflow",
                     nullable=False)
    created = db.Column(db.DateTime, default=datetime.now, nullable=False)
    modified = db.Column(db.DateTime, default=datetime.now,
                         onupdate=datetime.now, nullable=False)
    id_user = db.Column(db.Integer, default=0, nullable=False)
    _extra_data = db.Column(db.LargeBinary,
                            nullable=False,
                            default=get_default_extra_data())
    status = db.Column(db.Integer, default=0, nullable=False)
    current_object = db.Column(db.Integer, default="0", nullable=False)
    objects = db.relationship("BibWorkflowObject", backref="bwlWORKFLOW")
    counter_initial = db.Column(db.Integer, default=0, nullable=False)
    counter_halted = db.Column(db.Integer, default=0, nullable=False)
    counter_error = db.Column(db.Integer, default=0, nullable=False)
    counter_finished = db.Column(db.Integer, default=0, nullable=False)
    module_name = db.Column(db.String(64), nullable=False)

    child_logs = db.relationship("BibWorkflowEngineLog")

    def __repr__(self):
        """Represent a workflow object."""
        return "<Workflow(name: %s, module: %s, cre: %s, mod: %s," \
               "id_user: %s, status: %s)>" % \
               (str(self.name), str(self.module_name), str(self.created),
                str(self.modified), str(self.id_user), str(self.status))

    def __str__(self):
        """Print a workflow object."""
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
        Extra data: %s""" % (str(self.uuid), str(self.name), str(self.id_user),
                             str(self.module_name), str(self.created),
                             str(self.modified), str(self.status),
                             str(self.current_object),
                             str(self.counter_initial),
                             str(self.counter_halted), str(self.counter_error),
                             str(self.counter_finished), str(self._extra_data))

    @classmethod
    def get(cls, *criteria, **filters):
        """Wrapper to get a specified object.

        A wrapper for the filter and filter_by functions of sqlalchemy.
        Define a dict with which columns should be filtered by which values.

        .. code-block:: python

            Workflow.get(uuid=uuid)
            Workflow.get(Workflow.uuid != uuid)

        The function supports also "hybrid" arguments.

        .. code-block:: python

            Workflow.get(Workflow.module_name != 'i_hate_this_module',
                         user_id=user_id)

        See also SQLAlchemy BaseQuery's filter and filter_by documentation.
        """
        return cls.query.filter(*criteria).filter_by(**filters)

    @classmethod
    def get_status(cls, uuid=None):
        """Return the status of the workflow."""
        return cls.get(Workflow.uuid == uuid).one().status

    @classmethod
    def get_most_recent(cls, *criteria, **filters):
        """Return the most recently modified workflow. """
        most_recent = cls.get(*criteria, **filters). \
            order_by(desc(Workflow.modified)).first()
        if most_recent is None:
            raise NoResultFound
        else:
            return most_recent

    @classmethod
    def get_objects(cls, uuid=None):
        """Return the objects of the workflow."""
        return cls.get(Workflow.uuid == uuid).one().objects

    def get_extra_data(self, user_id=0, uuid=None, key=None, getter=None):
        """Get the extra_data for the object.

        Returns a JSON of the column extra_data or
        if any of the other arguments are defined,
        a specific value.

        You can define either the key or the getter function.

        :param key: the key to access the desirable value
        :param getter: a callable that takes a dict as param and returns a value
        """
        extra_data = Workflow.get(Workflow.id_user == self.id_user,
                                  Workflow.uuid == self.uuid).one()._extra_data

        extra_data = cPickle.loads(base64.b64decode(extra_data))
        if key:
            return extra_data[key]
        elif callable(getter):
            return getter(extra_data)
        elif not key:
            return extra_data

    def set_extra_data(self, user_id=0, uuid=None,
                       key=None, value=None, setter=None):
        """Replace extra_data.

        Modifies the JSON of the column extra_data or
        if any of the other arguments are defined, a specific value.
        You can define either the key, value or the setter function.

        :param key: the key to access the desirable value
        :param value: the new value
        :param setter: a callable that takes a dict as param and modifies it
        """
        extra_data = Workflow.get(Workflow.id_user == user_id,
                                  Workflow.uuid == uuid).one()._extra_data
        extra_data = cPickle.loads(base64.b64decode(extra_data))
        if key is not None and value is not None:
            extra_data[key] = value
        elif callable(setter):
            setter(extra_data)

        Workflow.get(Workflow.uuid == self.uuid).update(
            {'_extra_data': base64.b64encode(cPickle.dumps(extra_data))}
        )

    @classmethod
    @session_manager
    def delete(cls, uuid=None):
        """Delete a workflow."""
        cls.get(Workflow.uuid == uuid).delete()

    @session_manager
    def save(self, status):
        """Save object to persistent storage."""
        self.modified = datetime.now()
        if status is not None:
            self.status = status
        db.session.add(self)


class BibWorkflowObject(db.Model):

    """Data model for wrapping data being run in the workflows.

    Main object being passed around in the workflows module
    when using the workflows API.

    It can be instantiated like this:

    .. code-block:: python

        obj = BibWorkflowObject()

    Or, like this:

    .. code-block:: python

        obj = BibWorkflowObject.create_object()

    This object provides some handy functions such as:

    .. code-block:: python

        obj.set_data("<xml ..... />")
        obj.get_data() == "<xml ..... />"
        obj.set_extra_data({"param": value})
        obj.get_extra_data() == {"param": value}
        obj.add_task_result(name="myresult", result=1)

    Then to finally save the object

    .. code-block:: python

        obj.save()

    Now you can for example run it in a workflow:

    .. code-block:: python

        obj.start_workflow("sample_workflow")
    """

    # db table definition
    __tablename__ = "bwlOBJECT"

    id = db.Column(db.Integer, primary_key=True)

    # Our internal data column. Default is encoded dict.
    _data = db.Column(db.LargeBinary,
                      nullable=False,
                      default=get_default_data())
    _extra_data = db.Column(db.LargeBinary,
                            nullable=False,
                            default=get_default_extra_data())

    id_workflow = db.Column(db.String(36),
                            db.ForeignKey("bwlWORKFLOW.uuid"), nullable=True)
    version = db.Column(db.Integer(3),
                        default=ObjectVersion.INITIAL, nullable=False)
    id_parent = db.Column(db.Integer, db.ForeignKey("bwlOBJECT.id"),
                          default=None)
    child_objects = db.relationship("BibWorkflowObject",
                                    remote_side=[id_parent])
    created = db.Column(db.DateTime, default=datetime.now, nullable=False)
    modified = db.Column(db.DateTime, default=datetime.now,
                         onupdate=datetime.now, nullable=False)
    status = db.Column(db.String(255), default="", nullable=False)
    data_type = db.Column(db.String(150), default="",
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
        """Access logger object for this instance."""
        if not self._log:
            db_handler_obj = BibWorkflowLogHandler(BibWorkflowObjectLog, "id")
            self._log = get_logger(logger_name="object.%s" %
                                               (self.id,),
                                   db_handler_obj=db_handler_obj,
                                   loglevel=logging.DEBUG,
                                   obj=self)
        return self._log

    def get_data(self):
        """Get data saved in the object."""
        return cPickle.loads(base64.b64decode(self._data))

    def set_data(self, value):
        """Save data to the object."""
        self._data = base64.b64encode(cPickle.dumps(value))

    def get_extra_data(self):
        """Get extra data saved to the object."""
        return cPickle.loads(base64.b64decode(self._extra_data))

    def set_extra_data(self, value):
        """Save extra data to the object.

        :param value: what you want to replace extra_data with.
        :type value: dict
        """
        self._extra_data = base64.b64encode(cPickle.dumps(value))

    def get_workflow_name(self):
        """Return the workflow name for this object."""
        try:
            if self.id_workflow:
                return Workflow.query.get(self.id_workflow).name
        except AttributeError:
            # Workflow non-existent
            pass
        return

    def get_formatted_data(self, of="hd"):
        """Get the formatted representation for this object."""
        from .registry import workflows
        try:
            workflow_definition = workflows[self.get_workflow_name()]
            formatted_data = workflow_definition().formatter(self, formatter=None, format=of)
        except (KeyError, AttributeError):
            # Somehow the workflow does not exist (.name)
            from invenio.ext.logging import register_exception
            register_exception(alert_admin=True)
            formatted_data = ""
        return formatted_data

    def __repr__(self):
        """Represent a BibWorkflowObject."""
        return "<BibWorkflowObject(id = %s, data = %s, id_workflow = %s, " \
               "version = %s, id_parent = %s, created = %s, extra_data = %s)" \
               % (str(self.id), str(self.get_data()), str(self.id_workflow),
                  str(self.version), str(self.id_parent), str(self.created),
                  str(self.get_extra_data()))

    def __eq__(self, other):
        """Enable equal operators on BibWorkflowObjects."""
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
        """Enable equal operators on BibWorkflowObjects."""
        return not self.__eq__(other)

    def add_task_result(self, name, result):
        """Save a task result.

        Adds given task results to extra_data in order to be accessed
        and displayed later on by Holding Pen templates.
        """
        task_name = self.extra_data["_last_task_name"]
        res_obj = WorkflowsTaskResult(task_name, name, result)
        if isinstance(self.extra_data["_tasks_results"], list):
            if not self.extra_data["_tasks_results"]:
                self.extra_data["_tasks_results"] = {task_name: result}
        else:
            if task_name in self.extra_data["_tasks_results"]:
                self.extra_data["_tasks_results"][task_name].append(res_obj)
            else:
                self.extra_data["_tasks_results"][task_name] = [res_obj]

    def get_tasks_results(self):
        """Return the complete set of tasks results."""
        return self.get_extra_data()["_tasks_results"]

    def add_action(self, action, message):
        """Save an action for holdingpen for this object.

        Assign an special "action" to this object to be taken
        in consideration in holdingpen. The widget is referred to
        by a string with the filename minus extension.

        Ex: 'approval' for an action 'approval.py'.

        A message is also needed to tell the user the action
        required in a textual way.

        :param action: name of the action to add (i.e. "approval")
        :type action: string

        :param message: message to show to the user
        :type message: string
        """
        extra_data = self.get_extra_data()
        extra_data["_action"] = action
        extra_data["_message"] = message
        self.set_extra_data(extra_data)

    def get_action(self):
        """Retrieve the currently assigned action, if any.

        :return: name of action assigned as string, or None
        """
        try:
            return self.get_extra_data()["_action"]
        except KeyError:
            # No widget, try old _widget
            extra_data = self.get_extra_data()
            if "_widget" in extra_data:
                import warnings

                warnings.warn("Widget's are now stored in '_action'",
                              DeprecationWarning)
                # Migrate to new naming
                extra_data["_action"] = extra_data['_widget']
                del extra_data["_widget"]
                self.set_extra_data(extra_data)
                return extra_data["_action"]
            return None

    def get_action_message(self):
        """ Retrieve the currently assigned widget, if any."""
        try:
            return self.get_extra_data()["_message"]
        except KeyError:
            # No widget
            return ""

    def set_error_message(self, msg):
        """Set an error message."""
        extra_data = self.get_extra_data()
        extra_data["_error_msg"] = msg
        self.set_extra_data(extra_data)

    def get_error_message(self):
        """Retrieve the error message, if any."""
        if "error_msg" in self.get_extra_data():
            # Backwards compatibility
            extra_data = self.get_extra_data()
            msg = extra_data["error_msg"]
            del extra_data["error_msg"]
            self.set_extra_data(extra_data)
            self.set_error_message(msg)
        try:
            return self.get_extra_data()["_error_msg"]
        except KeyError:
            # No message
            return ""

    def remove_action(self):
        """Remove the currently assigned action."""
        extra_data = self.get_extra_data()
        extra_data["_action"] = None
        extra_data["_message"] = ""
        if "_widget" in extra_data:
            del extra_data["_widget"]
        self.set_extra_data(extra_data)

    def start_workflow(self, workflow_name, delayed=False, **kwargs):
        """Run the workflow specified on the object.

        Will start workflows execution for the object using
        :py:func:`.api.start` (or :py:func:`.api.start_delayed`
        if `delayed=True`).


        :param workflow_name: name of workflow to run
        :type workflow_name: str

        :param delayed: should the workflow run asynchronously?
        :type delayed: bool

        :return: BibWorkflowEngine (or AsynchronousResultWrapper).
        """
        if delayed:
            from .api import start_delayed as start_func
        else:
            from .api import start as start_func
        self.save()
        return start_func(workflow_name, data=[self], **kwargs)

    def continue_workflow(self, start_point="continue_next",
                          delayed=False, **kwargs):
        """Continue the workflow for this object.

        Will continue a previous execution for the object using
        :py:func:`.api.continue_oid` (or :py:func:`.api.continue_oid_delayed`
        if `delayed=True`).

        The parameter `start_point` allows you to specify the point of where
        the workflow shall continue:

        * restart_prev: will restart from the previous task

        * continue_next: will continue to the next task

        * restart_task: will restart the current task

        :param start_point: where should the workflow start from?
        :type start_point: str

        :param delayed: should the workflow run asynchronously?
        :type delayed: bool

        :return: BibWorkflowEngine (or AsynchronousResultWrapper).
        """
        from .errors import WorkflowAPIError

        self.save()
        if not self.id_workflow:
            raise WorkflowAPIError("No workflow associated with object: %r"
                                   % (repr(self),))
        if delayed:
            from .api import continue_oid_delayed as continue_func
        else:
            from .api import continue_oid as continue_func
        return continue_func(self.id, start_point, **kwargs)

    def change_status(self, message):
        """Change the status."""
        self.status = message

    def get_current_task(self):
        """Return the current task from the workflow engine for this object."""
        extra_data = self.get_extra_data()
        try:
            return extra_data["_task_counter"]
        except KeyError:
            # Assume old version "task_counter"
            return extra_data["task_counter"]

    def save_to_file(self, directory=None,
                     prefix="workflow_object_data_", suffix=".obj"):
        """Save the contents of self.data['data'] to file.

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
        """Pickling needed function."""
        return self.__dict__

    def __setstate__(self, state):
        """ unpickling needed function."""
        self.__dict__ = state

    def copy(self, other):
        """Copy data and metadata except id and id_workflow."""
        self._data = other._data
        self._extra_data = other._extra_data
        self.version = other.version
        self.id_parent = other.id_parent
        self.created = other.created
        self.modified = other.modified
        self.status = other.status
        self.data_type = other.data_type
        self.uri = other.uri

    @session_manager
    def save(self, version=None, task_counter=None, id_workflow=None):
        """Save object to persistent storage."""
        if task_counter is not None:
            self.log.debug("Saving task counter: %s" % (task_counter,))
            extra_data = self.get_extra_data()
            extra_data["_task_counter"] = task_counter
            self.set_extra_data(extra_data)

        if version is not None:
            if version != self.version:
                self.modified = datetime.now()
            self.version = version
        if id_workflow is not None:
            self.id_workflow = id_workflow
        db.session.add(self)
        if self.id is not None:
            self.log.debug("Saving object: %s" % (self.id or "new",))

    @classmethod
    def get(cls, *criteria, **filters):
        """Wrapper of SQLAlchemy to get a BibWorkflowObject.

        A wrapper for the filter and filter_by functions of SQLAlchemy.
        Define a dict with which columns should be filtered by which values.

        .. code-block:: python

            Workflow.get(uuid=uuid)
            Workflow.get(Workflow.uuid != uuid)

        The function supports also "hybrid" arguments.

        .. code-block:: python

            Workflow.get(Workflow.module_name != 'i_hate_this_module',
                         user_id=user_id)

        See also SQLAlchemy BaseQuery's filter and filter_by documentation.
        """
        return cls.query.filter(*criteria).filter_by(**filters)

    @classmethod
    @session_manager
    def delete(cls, oid):
        """Delete a BibWorkflowObject."""
        cls.get(BibWorkflowObject.id == oid).delete()

    @classmethod
    @session_manager
    def create_object(cls, **kwargs):
        """Create a new Workflow Object with given content."""
        obj = BibWorkflowObject(**kwargs)
        db.session.add(obj)
        return obj

    @classmethod
    @session_manager
    def create_object_revision(cls, old_obj, version, **kwargs):
        """Create a Workflow Object copy with customized values."""
        # Create new object and copy it
        obj = BibWorkflowObject(**kwargs)
        obj.copy(old_obj)

        # Overwrite some changes

        obj.version = version
        obj.created = datetime.now()
        obj.modified = datetime.now()
        for key, value in iteritems(kwargs):
            setattr(obj, key, value)
        db.session.add(obj)
        return obj


class BibWorkflowObjectLog(db.Model):

    """Represents a log entry for BibWorkflowObjects.

    This class represent a record of a log emit by an object
    into the database. The object must be saved before using
    this class as it requires the object id.
    """

    __tablename__ = 'bwlOBJECTLOGGING'
    id = db.Column(db.Integer, primary_key=True)
    id_object = db.Column(db.Integer(255),
                          db.ForeignKey('bwlOBJECT.id'),
                          nullable=False)
    log_type = db.Column(db.Integer, default=0, nullable=False)
    created = db.Column(db.DateTime, default=datetime.now)
    message = db.Column(db.TEXT, default="", nullable=False)

    def __str__(self):
        """Print a log."""
        return "%(severity)s: %(created)s - %(message)s" % {
            "severity": self.log_type,
            "created": self.created,
            "message": self.message
        }

    def __repr__(self):
        """Represent a log message."""
        return "BibWorkflowObjectLog(%s)" % (", ".join([
            "log_type='%s'" % self.log_type,
            "created='%s'" % self.created,
            "message='%s'" % self.message,
            "id_object='%s'" % self.id_object,
        ]))

    @classmethod
    def get(cls, *criteria, **filters):
        """SQLAlchemy wrapper to get BibworkflowLogs.

        A wrapper for the filter and filter_by functions of SQLAlchemy.
        Define a dict with which columns should be filtered by which values.

        See also SQLAlchemy BaseQuery's filter and filter_by documentation.
        """
        return cls.query.filter(*criteria).filter_by(**filters)

    @classmethod
    def get_most_recent(cls, *criteria, **filters):
        """ Return the most recently created log. """
        most_recent = cls.get(*criteria, **filters).order_by(
            desc(BibWorkflowObjectLog.created)).first()
        if most_recent is None:
            raise NoResultFound
        else:
            return most_recent

    @classmethod
    def delete(cls, id=None):
        """Delete an instance in database. """
        cls.get(BibWorkflowObjectLog.id == id).delete()
        db.session.commit()


class BibWorkflowEngineLog(db.Model):

    """Represents a log entry for BibWorkflowEngine.

    This class represent a record of a log emit by an object
    into the database. The object must be saved before using
    this class as it requires the object id.
    """

    __tablename__ = "bwlWORKFLOWLOGGING"
    id = db.Column(db.Integer, primary_key=True)
    id_object = db.Column(db.String(255),
                          db.ForeignKey('bwlWORKFLOW.uuid'),
                          nullable=False)
    log_type = db.Column(db.Integer, default=0, nullable=False)
    created = db.Column(db.DateTime, default=datetime.now)
    message = db.Column(db.TEXT, default="", nullable=False)

    def __str__(self):
        """Print a log."""
        return "%(severity)s: %(created)s - %(message)s" % {
            "severity": self.log_type,
            "created": self.created,
            "message": self.message
        }

    def __repr__(self):
        """Represent a log message."""
        return "BibWorkflowEngineLog(%s)" % (", ".join([
            "log_type='%s'" % self.log_type,
            "created='%s'" % self.created,
            "message='%s'" % self.message,
            "id_object='%s'" % self.id_object
        ]))

    @classmethod
    def get(cls, *criteria, **filters):
        """Sqlalchemy wrapper to get BibWorkflowEngineLog.

        A wrapper for the filter and filter_by functions of sqlalchemy.
        Define a dict with which columns should be filtered by which values.

        look up also sqalchemy BaseQuery's filter and filter_by documentation
        """
        return cls.query.filter(*criteria).filter_by(**filters)

    @classmethod
    def get_most_recent(cls, *criteria, **filters):
        """ Return the most recently created log. """
        most_recent = cls.get(*criteria, **filters).order_by(
            desc(BibWorkflowEngineLog.created)).first()
        if most_recent is None:
            raise NoResultFound
        else:
            return most_recent

    @classmethod
    def delete(cls, uuid=None):
        """Delete an instance in database. """
        cls.get(BibWorkflowEngineLog.id == uuid).delete()
        db.session.commit()


__all__ = ('Workflow', 'BibWorkflowObject',
           'BibWorkflowObjectLog', 'BibWorkflowEngineLog')
