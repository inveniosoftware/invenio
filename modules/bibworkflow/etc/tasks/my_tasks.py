## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

import time
from invenio.bibworkflow_config import CFG_OBJECT_STATUS


def task_a(a):
    def _task_a(obj, eng):
        """Function task_a docstring"""
        print "executing task a " + str(a)
        print obj.data
        obj.data['a'] += a
        print obj
        obj.add_metadata("foo", "bar")
        return
    return _task_a


def task_b():
    def _task_b(obj, eng):
        """Function task_b docstring"""
        print "executing task b"
        print obj
        if obj.data['a'] < 20:
            obj.changeStatus(CFG_OBJECT_STATUS.ERROR)
            print obj.db_obj.status
            print "a < 20"
            obj.add_task_result("task_b", {'a': 12, 'b': 13, 'c': 14})
            eng.haltProcessing("Value of filed: a in object is too small.")
        return
    return _task_b


def add_new_record():
    def _add_new_record(obj, eng):
        print "executing task add_new_record on obj " + str(obj)
        obj.object_isd = 123
        print str(obj.created) + "  " + str(obj.modified)
        return obj
    return _add_new_record


def add_metadata():
    def _add_metadata(obj, eng):
        print "executing task add_metadata on obj.type " + obj.content_type
        if(obj['content_type'] == 'book'):
            obj.add_field("meta1", "elefant")
        else:
            obj.add_field("meta1", "hippo")
        return obj
    return _add_metadata


def simple_task(times):
    def _simple_task(obj, eng):
        a = times
        while a > 0:
            print "Running simple task %i times" % (times,)
            a = a - 1
        return
    return _simple_task


def sleep_task(t):
    def _sleep_task(obj, eng):
        print "Going to sleep..."
        time.sleep(t)
        print "I've woken up:)"
    return _sleep_task


def save_workflow():
    def _save_workflow(obj, eng):
        """Function save_workflow docstring."""
        eng.save()
        print "Workflow saved from task"
    return _save_workflow
