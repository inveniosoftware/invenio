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

from inveniomanage import db
from datetime import datetime


class TaskLogging(db.Model):
    __tablename__ = "bwlTASKLOGGING"
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(255), nullable=False)
    data = db.Column(db.String(255), nullable=False)
    created = db.Column(db.DateTime, nullable=False)
    workflow_name = db.Column(db.String(255), nullable=False)

    def __init__(self, task_name, data, created, workflow_name):
        self.task_name = task_name
        self.data = data
        self.created = created
        self.workflow_name = workflow_name

    def __repr__(self):
        return "<Task(%i, %s, %s, %s, %s)>" % (self.id, self.task_name,
                                               self.data, self.created,
                                               self.workflow_name)


class AuditLogging(db.Model):
    __tablename__ = "bwlAUDITLOGGING"
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(255), nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    user = db.Column(db.String(255), nullable=False)

    def __init__(self, action, time, user):
        self.action = action
        self.time = time
        self.user = user

    def __repr__(self):
        return "<Task(%s, %s, %s)>" % (self.action, self.time, self.user)


class WorkflowLogging(db.Model):
    __tablename__ = "bwlWORKFLOWLOGGING"
    id = db.Column(db.Integer, primary_key=True)
    workflow_name = db.Column(db.String(255), nullable=False)
    data = db.Column(db.String(255), nullable=False)
    created = db.Column(db.DateTime, nullable=False)

    def __init__(self, workflow_name, data, created):
        self.workflow_name = workflow_name
        self.data = data
        self.created = created

    def __repr__(self):
        return "<Task(%i, %s, %s, %s)>" % (self.id, self.workflow_name, self.data, self.created)


class Workflow(db.Model):
    __tablename__ = "bwlWORKFLOW"
    uuid = db.Column(db.String(36), primary_key=True, nullable=False)
    name = db.Column(db.String(255), default="Default workflow", nullable=False)
    created = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    modified = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    user_id = db.Column(db.Integer, default=0, nullable=False)
    extra_data = db.Column(db.JSON, default={})
    status = db.Column(db.Integer, default=0, nullable=False)
    current_object = db.Column(db.Integer, default="0", nullable=False)
    objects = db.relationship("WfeObject", backref="bwlWORKFLOW")
    counter_initial = db.Column(db.Integer, default=0, nullable=False)
    counter_halted = db.Column(db.Integer, default=0, nullable=False)
    counter_error = db.Column(db.Integer, default=0, nullable=False)
    counter_finished = db.Column(db.Integer, default=0, nullable=False)
    module_name = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return "<Workflow(name: %s, module: %s, cre: %s, mod: %s, user_id: %s, status: %s)>" % \
            (str(self.name),
             str(self.module_name),
             str(self.created),
             str(self.modified),
             str(self.user_id),
             str(self.status))


class WfeObject(db.Model):
    __tablename__ = "bwlOBJECT"
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.JSON, nullable=False)
    extra_data = db.Column(db.JSON, default={"tasks_results":{}})
    workflow_id = db.Column(db.String(36), db.ForeignKey("bwlWORKFLOW.uuid"), nullable=False)
    version = db.Column(db.Integer(3), default=0, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("bwlOBJECT.id"), default=None)
    child_objects = db.relationship("WfeObject", remote_side=[parent_id])
    created = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    modified = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    owner = db.Column(db.String(255))
    status = db.Column(db.String(255), default="", nullable=False)
    user_id = db.Column(db.String(255), default=0, nullable=False)
    task_counter = db.Column(db.JSON, nullable=False)
    error_msg = db.Column(db.String(500), default="", nullable=False)
    last_task_name = db.Column(db.String(60), default="")

    def __repr__(self):
        repr = "<WfeObject(id = %s, data = %s, workflow_id = %s, " \
               "version = %s, parent_id = %s, created = %s)" \
               % (str(self.id), str(self.data), str(self.workflow_id),
                  str(self.version), str(self.parent_id), str(self.created))
        return repr

    def __eq__(self, other):
        if isinstance(other, WfeObject):
            if self.data == other.data and \
                    self.extra_data == other.extra_data and \
                    self.workflow_id == other.workflow_id and \
                    self.version == other.version and \
                    self.parent_id == other.parent_id and \
                    isinstance(self.created, datetime) and \
                    isinstance(self.modified, datetime):
                return True
            else:
                return False
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, WfeObject):
            if self.data == other.data and \
                    self.extra_data == other.extra_data and \
                    self.workflow_id == other.workflow_id and \
                    self.version == other.version and \
                    self.parent_id == other.parent_id and \
                    isinstance(self.created, datetime) and \
                    isinstance(self.modified, datetime):
                return False
            else:
                return True
        return False

    def __getstate__(self):
        return {"data": self.data,
                "workflow_id": self.workflow_id,
                "version": self.version,
                "parent_id": self.parent_id,
                "created": self.created,
                "modified": self.modified,
                "owner": self.owner,
                "status": self.status,
                "user_id": self.user_id,
                "task_counter": self.task_counter,
                "error_msg": self.error_msg}

    def __setstate__(self, state):
        self.data = state["data"]
        self.workflow_id = state["workflow_id"]
        self.version = state["version"]
        self.parent_id = state["parent_id"]
        self.created = state["created"]
        self.modified = state["modified"]  # should we update
        self.owner = state["owner"]        # the modification date??
        self.status = state["status"]
        self.user_id = state["user_id"]
        self.task_counter = state["task_counter"]
        self.error_msg = state["error_msg"]

    def copy(self, other):
        """Copies data and metadata except id and workflow_id"""
        self.data = other.data
        self.extra_data = other.extra_data 
        self.version = other.version 
        self.parent_id = other.parent_id 
        self.created = other.created 
        self.modified = datetime.now()
        self.owner = other.owner 
        self.status = other.status 
        self.user_id = other.user_id 
        self.task_counter = other.task_counter 
        self.error_msg = other.error_msg 

__all__ = ['Workflow', 'WfeObject', 'WorkflowLogging',
           'AuditLogging', 'TaskLogging']
