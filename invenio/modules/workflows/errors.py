# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Contains standard error messages for workflows module."""

from workflow.engine import HaltProcessing


class WorkflowHalt(HaltProcessing):

    """
    Used when workflow should be halted.

    Also contains the widget and other information to be displayed.
    """

    def __init__(self, message, action=None, **kwargs):
        """Instanciate a WorkflowHalt object."""
        HaltProcessing.__init__(self)
        self.message = message
        self.action = action
        self.payload = kwargs

    def to_dict(self):
        """Return a dict representation of WorkflowHalt."""
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['action'] = self.action
        return rv

    def __str__(self):
        """String representation."""
        return "WorkflowHalt(%s, action: %s, payload: %r)" % \
               (repr(self.message), repr(self.action), repr(self.payload))


class WorkflowError(Exception):

    """Raised when workflow experiences an error."""

    def __init__(self, message, id_workflow, id_object, payload=[]):
        """Instanciate a WorkflowError object."""
        self.message = message
        self.id_workflow = id_workflow
        self.id_object = id_object
        self.payload = payload
        # Needed for passing an exception through message queue
        Exception.__init__(self, message, message, id_object, payload)

    def to_dict(self):
        """Return a dict representation of WorkflowError."""
        rv = list(self.payload or [])
        rv['message'] = self.message
        rv['id_workflow'] = self.id_workflow
        rv['id_object'] = self.id_object
        return rv

    def __str__(self):
        """String representation."""
        return "WorkflowError(%s, id_workflow: %s, id_object: %s," \
               " payload: %r)" % \
               (str(self.message), str(self.id_workflow), str(self.id_object),
                repr(self.payload))


class WorkflowDefinitionError(Exception):

    """Raised when workflow definition is missing."""

    def __init__(self, message, workflow_name, **kwargs):
        """Instanciate a WorkflowDefinitionError object."""
        Exception.__init__(self)
        # if isinstance(message, unicode):
        #     message = message.encode('utf-8', 'ignore')
        self.message = message
        self.workflow_name = workflow_name
        self.payload = kwargs

    def to_dict(self):
        """Return a dict representation of WorkflowDefinitionError."""
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['workflow_name'] = self.workflow_name
        return rv

    def __str__(self):
        """String representation."""
        return "WorkflowDefinitionError(%s, workflow_name: %s, payload: %r)" % \
               (str(self.message), self.workflow_name, repr(self.payload)
                or "None")


class WorkflowWorkerError(Exception):

    """Raised when there is a problem with workflow workers."""

    def __init__(self, message, worker_name="No Name Given", **kwargs):
        """Instanciate a WorkflowWorkerError object."""
        Exception.__init__(self)
        self.message = message
        self.worker_name = worker_name
        self.payload = kwargs

    def to_dict(self):
        """Return a dict representation of WorkflowWorkerError."""
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['worker_name'] = self.worker_name
        return rv

    def __str__(self):
        """String representation."""
        return "WorkflowWorkerError(%s, worker_name: %s, payload: %r)" % \
               (repr(self.message), self.worker_name, repr(self.payload) or
                "None")


class WorkflowObjectVersionError(Exception):

    """Raised when workflow object has an unknown or missing version."""

    def __init__(self, message, id_object, obj_version):
        """Instanciate a WorkflowObjectVersionError object."""
        self.message = message
        self.obj_version = obj_version
        self.id_object = id_object

    def to_dict(self):
        """Return a dict representation of WorkflowObjectVersionError."""
        rv = {}
        rv['message'] = self.message
        rv['obj_version'] = self.obj_version
        rv['id_object'] = self.id_object
        return rv

    def __str__(self):
        """String representation."""
        return "WorkflowObjectVersionError(%s, obj_version: %s," \
               " id_object: %s)" % \
               (self.message, str(self.obj_version), str(self.id_object))


class WorkflowAPIError(Exception):

    """Raised when there is a problem with parameters at the API level."""

    pass


class SkipToken(Exception):

    """Used by workflow engine to skip the current process of an object."""


class AbortProcessing(Exception):

    """Used by workflow engine to abort the engine execution."""
