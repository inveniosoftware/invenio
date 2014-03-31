# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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
Collection of tasks used for tests.
"""

from __future__ import print_function

import time


def add_data(data):
    """ Task using closure to allow parameters """
    def _add_data(obj, eng):
        """ Adds data to obj.data """
        obj.data += data
    return _add_data


def halt_if_data_less_than(threshold):
    """ Static task with no parameters """
    def _halt_if_data_less_than(obj, eng):
        """
        Halts workflow execution for this object
        if its value is less than given threshold.
        """
        if obj.data < threshold:
            eng.halt("Value of data is too small.")
    return _halt_if_data_less_than


def print_data(obj, eng):
    """ Static task with no parameters """
    print(obj.data)


def set_data(data):
    """ Task using closure to allow parameters """
    def _set_data(obj, eng):
        """ Sets obj.data to given data """
        obj.data = data
    return _set_data


def reduce_data_by_one(times):
    def _reduce_data_by_one(obj, eng):
        a = times
        while a > 0:
            obj.data -= 1
            a -= 1
        obj.log.info("value is now: " + str(obj.data))

    return _reduce_data_by_one


def add_metadata():
    def _add_metadata(obj, eng):
        if (obj['content_type'] == 'book'):
            obj.add_field("meta1", "elefant")
        else:
            obj.add_field("meta1", "hippo")

    return _add_metadata


def task_b(obj, eng):
    """Function task_b docstring"""
    if obj.data < 20:
        eng.log.info("data < 20")
        obj.add_task_result("task_b", {'a': 12, 'b': 13, 'c': 14})


def sleep_task(t):
    def _sleep_task(dummy_obj, eng):
        time.sleep(t)

    return _sleep_task


def lower_than_20(obj, eng):
    """Function checks if variable is lower than 20"""
    if obj.data < 20:
        eng.halt("Value of filed: a in object is lower than 20.")


def halt_if_higher_than_20(obj, eng):
    """Function checks if variable is higher than 20"""
    eng.log.info("value" + str(obj.data))
    if obj.data > 20:
        eng.halt("Value of filed: a in object is higher than 20.")


def subtract(value):
    def _subtract(obj, dummy_eng):
        """Function subtract value from variable"""
        obj.data -= value

    return _subtract


def task_reduce_and_halt(obj, eng):
    eng.log.info("value" + str(obj.data))
    if obj.data > 0:
        eng.log.error(obj.data)
        obj.data -= 1
        eng.log.error(obj.data)
        obj.save()
        eng.halt("test halt")
    else:
        return None
