# -*- coding: utf-8 -*-
##
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
Invenio Celery Loader

The loader's purposes is to load modules defined in invenio.*_tasks modules
"""

# Important for 'from celery import Celery' to find the right celery module.
from __future__ import absolute_import

from celery import Celery
from celery.datastructures import DictAttribute
from celery.loaders.base import BaseLoader

from invenio.importutils import autodiscover_modules


class InvenioLoader(BaseLoader):
    """
    The Invenio Celery loader - modeled after the Django Celery loader.
    """
    def __init__(self, *args, **kwargs):
        super(InvenioLoader, self).__init__(*args, **kwargs)

    def read_configuration(self):
        """ Read configuration defined in invenio.celery_config """
        usercfg = self._import_config_module('invenio.celery_config')
        self.configured = True
        return DictAttribute(usercfg)

    def import_default_modules(self):
        """ Called before on_worker_init """
        super(InvenioLoader, self).import_default_modules()
        self.autodiscover()

    def autodiscover(self):
        """
        Discover task modules named 'invenio.*_tasks'
        """
        self.task_modules.update(mod.__name__ for mod in autodiscover_modules(['invenio'], related_name_re='.+_tasks\.py') or ())


#
#  Create main celery application
#
celery = Celery(
    'invenio',
    loader=InvenioLoader,
)
