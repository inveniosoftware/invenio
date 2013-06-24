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

"""Basic test functions - NOT FOR XML """

import time
from invenio.bibworkflow_config import CFG_OBJECT_STATUS


def task_a(a):
    def _task_a(obj, eng):
        """Function task_a docstring"""
        print "executing task a " + str(a)
        eng.log_info("executing task a " + str(a))
        obj.data['data'] += a
        #obj.add_metadata("foo", "bar")
    return _task_a


def task_b(obj, eng):
    """Function task_b docstring"""
    print "executing task b"
    eng.log_info("executing task b")
    if obj.data['data'] < 20:
        obj.changeStatus(CFG_OBJECT_STATUS.ERROR)
        eng.log_info("Object status %s" % (obj.status,))
        eng.log_info("data < 20")
        obj.add_task_result("task_b", {'a': 12, 'b': 13, 'c': 14})
        eng.halt("Value of filed: data in object is too small.")


def add_metadata():
    def _add_metadata(obj, eng):
        eng.log_info("executing task add_metadata on obj.type %s" %
                     (obj.content_type,))
        if(obj['content_type'] == 'book'):
            obj.add_field("meta1", "elefant")
        else:
            obj.add_field("meta1", "hippo")
    return _add_metadata


def simple_task(times):
    def _simple_task(obj, eng):
        a = times
        eng.log_info("Running simple task %i times" % (times,))
        while a > 0:
            obj.data['data'] -= 1
            a -= 1
    return _simple_task


def sleep_task(t):
    def _sleep_task(dummy_obj, eng):
        eng.log_info("Going to sleep...")
        time.sleep(t)
        eng.log_info("I've woken up :)")
    return _sleep_task


def lower_than_20(obj, eng):
    """Function checks if variable is lower than 20"""
    if obj.data['data'] < 20:
        eng.log_info("data < 20")
        eng.halt("Value of filed: a in object is lower than 20.")


def higher_than_20(obj, eng):
    """Function checks if variable is higher than 20"""
    if obj.data['data'] > 20:
        eng.log_info("data > 20")
        eng.halt("Value of filed: a in object is higher than 20.")


def add(value):
    def _add(obj, dummy_eng):
        """Function adds value to variable"""
        obj.data['data'] += value
    return _add


def subtract(value):
    def _subtract(obj, dummy_eng):
        """Function subtract value from variable"""
        obj.data['data'] -= value
    return _subtract
