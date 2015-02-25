# -*- coding: utf-8 -*-
#
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

"""Collection of tasks used for tests."""

import time

from functools import wraps


def add_data(data_param):
    """Add data_param to obj.data."""
    @wraps(add_data)
    def _add_data(obj, eng):
        #due to python 2 way of managing closure
        data = data_param
        obj.data += data

    return _add_data


def generate_error(obj, eng):
    """Generate a ZeroDevisionError."""
    call_a()


def call_a():
    """Used in order to test deep stack trace output."""
    call_b()


def call_b():
    """Used in order to test deep stack trace output."""
    call_c()


def call_c():
    """Used in order to test deep stack trace output."""
    raise ZeroDivisionError


def halt_if_data_less_than(threshold):
    """Static task to halt if data is lesser than threshold.

    Halt workflow execution for this object if its value is less than given
    threshold.
    """
    @wraps(halt_if_data_less_than)
    def _halt_if_data_less_than(obj, eng):
        if obj.data < threshold:
            eng.halt("Value of data is too small.")

    return _halt_if_data_less_than


def set_data(data):
    """Task using closure to allow parameters and change data."""
    @wraps(set_data)
    def _set_data(obj, eng):
        obj.data = data

    return _set_data


def reduce_data_by_one(times):
    """Task to substract one to data."""
    @wraps(reduce_data_by_one)
    def _reduce_data_by_one(obj, eng):
        a = times
        while a > 0:
            obj.data -= 1
            a -= 1

    return _reduce_data_by_one


def add_metadata():
    """Task to add metadata."""
    @wraps(add_metadata)
    def _add_metadata(obj, eng):
        if obj['content_type'] == 'book':
            obj.add_field("meta1", "elefant")
        else:
            obj.add_field("meta1", "hippo")

    return _add_metadata


def task_b(obj, eng):
    """Function task_b docstring."""
    if obj.data < 20:
        eng.log.info("data < 20")
        obj.add_task_result("task_b", {'a': 12, 'b': 13, 'c': 14})


def sleep_task(t):
    """Task to wait t seconds."""
    @wraps(sleep_task)
    def _sleep_task(dummy_obj, eng):
        time.sleep(t)

    return _sleep_task


def lower_than_20(obj, eng):
    """Function checks if variable is lower than 20."""
    if obj.data < 20:
        eng.halt("Value of filed: a in object is lower than 20.")


def halt_if_higher_than_20(obj, eng):
    """Function checks if variable is higher than 20."""
    if obj.data > 20:
        eng.halt("Value of filed: a in object is higher than 20.")


def subtract(value):
    """Function subtract value from variable."""
    @wraps(subtract)
    def _subtract(obj, dummy_eng):
        obj.data -= value

    return _subtract


def halt_whatever(obj, eng):
    """Task to stop processing in halted status."""
    eng.halt("halt!", None)


def task_reduce_and_halt(obj, eng):
    """Task to substract one to data and stop."""
    if obj.data > 0:
        obj.data -= 1
        obj.save()
        eng.halt("test halt")
    else:
        return None
