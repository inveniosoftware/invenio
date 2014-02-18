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

from celery import Celery, signals
from celery.datastructures import DictAttribute
from celery.loaders.base import BaseLoader

from invenio.base.utils import autodiscover_celery_tasks
from invenio.base.factory import with_app_context


class InvenioLoader(BaseLoader):
    """
    The Invenio Celery loader - modeled after the Django Celery loader.
    """
    def __init__(self, *args, **kwargs):
        super(InvenioLoader, self).__init__(*args, **kwargs)
        self._install_signal_handlers()
        self.flask_app = None
        self.db = None

    def _install_signal_handlers(self):
        # Need to close any open database connection after
        # any embedded celerybeat process forks.
        signals.beat_embedded_init.connect(self.close_database)
        # Handlers for settings Flask request context
        signals.task_prerun.connect(self.on_task_prerun)
        signals.task_postrun.connect(self.on_task_postrun)

    def _init_flask(self):
        """
        Initialize Flask application.

        The Flask application should only be created in the workers, thus
        this method should not be called from the __init__ method.
        """
        if not self.flask_app:
            from flask import current_app
            if current_app:
                self.flask_app = current_app
            else:
                from invenio.base.factory import create_app
                self.flask_app = create_app()
                from invenio.ext.sqlalchemy import db
                self.db = db

    def on_task_init(self, task_id, task):
        """Called before every task."""
        try:
            is_eager = task.request.is_eager
        except AttributeError:
            is_eager = False
        if not is_eager:
            self.close_database()

    def on_task_prerun(self, task=None, **dummy_kwargs):
        """
        Called before a task is run - pushes a new Flask request context
        for the task.
        """
        app = self.flask_app
        if not app:
            from flask import current_app
            app = current_app
        task.request.flask_ctx = app.test_request_context()
        task.request.flask_ctx.push()

    def on_task_postrun(self, task=None, **dummy_kwargs):
        """
        Called after a task is run - pops the pushed Flask request context
        for the task.
        """
        task.request.flask_ctx.pop()

    def on_process_cleanup(self):
        """Does everything necessary for Invenio to work in a long-living,
        multiprocessing environment. Called after on_task_postrun.
        """
        self.close_database()

    def on_worker_init(self):
        """Called when the worker starts.

        Automatically discovers any ``*_tasks.py`` files in the Invenio module.
        """
        self.close_database()

    def on_worker_process_init(self):
        self.close_database()

    def read_configuration(self):
        """ Read configuration defined in invenio.celery.config """
        from invenio.celery.config import default_config
        self._init_flask()
        self.configured = True
        return default_config(self.flask_app.config)

    def close_database(self, **dummy_kwargs):
        if self.db:
            self.db.session.remove()

    def import_default_modules(self):
        """ Called before on_worker_init """
        # First setup Flask application
        self._init_flask()
        # Next import all task modules with a request context (otherwise
        # the SQLAlchemy models cannot be imported).
        with self.flask_app.test_request_context():
            super(InvenioLoader, self).import_default_modules()
            self.autodiscover()

    def autodiscover(self):
        """
        Discover task modules named 'invenio.modules.*.tasks'
        """
        from invenio.celery import tasks
        self.task_modules.update(tasks.__name__)
        self.task_modules.update(
            mod.__name__ for mod in autodiscover_celery_tasks() or ())


#
#  Create main celery application
#
celery = Celery(
    'invenio',
    loader=InvenioLoader,
)
