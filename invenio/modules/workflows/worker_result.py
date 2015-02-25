# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""Contain the AsynchronousResultWrapper class for asynchronous execution."""

from abc import abstractmethod, ABCMeta
from six import add_metaclass


@add_metaclass(ABCMeta)
class AsynchronousResultWrapper(object):

    """Wrap results from asynchronous results.

    This class is an abstract class. When you inherit it you should
    absolutely implement all the functions.

    This class is here for two reason, get and unified interface for all
    the worker and so allow to switch from one to another seamlessly,
    and also add feature to functions.

    For example the get method now allow a post processing
    on the result.
    """

    def __init__(self, asynchronousresult):
        """Instantiate a AsynchronousResultWrapper around a given result object.

        :param asynchronousresult: the async result that you want to wrap.
        """
        self.asyncresult = asynchronousresult

    @abstractmethod
    def get(self, postprocess=None):
        """Return the value of the process."""
        return

    @abstractmethod
    def status(self):
        """Return the current status of the tasks."""
        return


def uuid_to_workflow(uuid):
    """Return the workflow associated to an uuid."""
    from invenio.modules.workflows.models import Workflow

    return Workflow.query.filter(Workflow.uuid == uuid).first()
