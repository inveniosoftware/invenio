# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

"""
    invenio.modules.workflows.errors
    ------------------------

    Contains standard error messages for workflows module.
"""

from workflow.engine import HaltProcessing


class WorkflowHalt(HaltProcessing):
    """
    Raised when workflow should be halted.
    Also contains the widget to be displayed.
    """

    def __init__(self, message, widget=None, **kwargs):
        HaltProcessing.__init__(self)
        self.message = message
        self.widget = widget
        self.payload = kwargs

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['widget'] = self.widget
        return rv

    def __str__(self):
        """String representation."""
        return "WorkflowHalt(%s, widget: %s, payload: %r)" % \
               (repr(self.message), repr(self.widget), repr(self.payload))


# class WorkflowError(Exception):
#     """Raised when workflow experiences an error."""
#
#     def __init__(self, message, id_workflow=None, id_object=None, **kwargs):
#         self.message = message
#         self.id_workflow = id_workflow
#         self.id_object = id_object
#         self.payload = kwargs
#         super(WorkflowError, self).__init__(message, id_workflow, id_object, kwargs)
#
#     def to_dict(self):
#         rv = dict(self.payload or ())
#         rv['message'] = self.message
#         rv['id_workflow'] = self.id_workflow
#         rv['id_object'] = self.id_object
#         return rv
#
#     def __str__(self):
#         """String representation."""
#         return "WorkflowError(%s, id_workflow: %s, id_object: %s, payload: %r)" % \
#                (self.message, str(self.id_workflow), str(self.id_object), repr(self.payload))

class WorkflowError(Exception):
    """Raised when workflow experiences an error."""

    def __init__(self, message, id_workflow, id_object, payload=[]):
        self.message = message
        self.id_workflow = id_workflow
        self.id_object = id_object
        self.payload = payload
        Exception.__init__(self, message, message, id_object, payload)  # <-- REQUIRED

    def to_dict(self):
        rv = list(self.payload or [])
        rv['message'] = self.message
        rv['id_workflow'] = self.id_workflow
        rv['id_object'] = self.id_object
        return rv

    def __str__(self):
        """String representation."""
        return "WorkflowError(%s, id_workflow: %s, id_object: %s, payload: %r)" % \
               (self.message, str(self.id_workflow), str(self.id_object), repr(self.payload))

class WorkflowDefinitionError(Exception):
    """Raised when workflow definition is missing."""

    def __init__(self, message, workflow_name, **kwargs):
        Exception.__init__(self)
        self.message = message
        self.workflow_name = workflow_name
        self.payload = kwargs

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['workflow_name'] = self.workflow_name
        return rv

    def __str__(self):
        """String representation."""
        return "WorkflowDefinitionError(%s, workflow_name: %s, payload: %r)" % \
               (repr(self.message), self.workflow_name, repr(self.payload) or "None")


class WorkflowWorkerError(Exception):
    """Raised when there is a problem with workflow workers."""

    def __init__(self, message, worker_name, **kwargs):
        Exception.__init__(self)
        self.message = message
        self.worker_name = worker_name
        self.payload = kwargs

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['worker_name'] = self.worker_name
        return rv

    def __str__(self):
        """String representation."""
        return "WorkflowDefinitionError(%s, worker_name: %s, payload: %r)" % \
               (repr(self.message), self.worker_name, repr(self.payload) or "None")