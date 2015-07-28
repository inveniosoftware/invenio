# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
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

from workflow.errors import with_str, HaltProcessing

@with_str(('message', ('action', 'payload')))
class WaitProcessing(HaltProcessing):  # Used to be WorkflowHalt
    def __init__(self, message="", action=None, payload=None):
        super(WaitProcessing, self).__init__(message=message, action=action, payload=payload)


@with_str(('message', ('worker_name', 'payload')))
class WorkflowWorkerError(Exception):
    """Raised when there is a problem with workflow workers."""

    def __init__(self, message, worker_name="No Name Given", payload=None):
        """Instanciate a WorkflowWorkerError object."""
        super(WorkflowWorkerError, self).__init__()
        self.message = message
        self.worker_name = worker_name
        self.payload = payload
