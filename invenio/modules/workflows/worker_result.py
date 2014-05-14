# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

from abc import abstractmethod, ABCMeta


class AsynchronousResultWrapper(object):
    """
    This class is an abstract class. When you inherit it you should
    absolutely implement all the functions.

    This class is here for two reason, get and unified interface for all
    the worker and so allow to switch from one to another seemslessly,
    and also add feature to functions.

    For example the get method now allow a post processing
    on the result.

    :param asynchronousresult: the async result that you want to wrap.
    """
    __metaclass__ = ABCMeta

    def __init__(self, asynchronousresult):
        self.asyncresult = asynchronousresult

    @abstractmethod
    def get(self, postprocess=None):
        return

    @abstractmethod
    def status(self):
        return


def uuid_to_workflow(uuid):
    from invenio.modules.workflows.models import Workflow

    return Workflow.query.filter(Workflow.uuid == uuid).first()
