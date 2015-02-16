# -*- coding: utf-8 -*
##
## This file is part of Invenio.
## Copyright (C) 2015 CERN.
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
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA

"""Utility functions for Celery."""

import time

from invenio.celery import celery


def get_queues():
    """Return a list of current active Celery queues."""
    res = celery.control.inspect().active_queues() or dict()
    return [result.get("name") for host in res.values() for result in host]


def disable_queue(name):
    """Disable given Celery queue."""
    celery.control.cancel_consumer(name)


def enable_queue(name):
    """Enable given Celery queue."""
    celery.control.add_consumer(name)


def get_active_tasks():
    """Return a list of UUIDs of active tasks."""
    current_tasks = celery.control.inspect().active() or dict()
    return [task.get("id") for host in current_tasks.values() for task in host]


def suspend_queues(active_queues, sleep_time=10.0):
    """Suspend given Celery queues and wait for running tasks to complete."""
    for queue in active_queues:
        disable_queue(queue)
    while get_active_tasks():
        time.sleep(sleep_time)
