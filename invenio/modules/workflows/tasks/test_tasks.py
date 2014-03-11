# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2012, 2013, 2014 CERN.
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


def task_a(a):
    def _task_a(obj, eng):
        """Function task_a docstring"""
        obj.data += a
        if a > 5:
            obj.extra_data['redis_search']['publisher'] = "CERN"
        else:
            obj.extra_data['redis_search']['publisher'] = "Desy"

    return _task_a


def task_b(obj, eng):
    """Function task_b docstring"""

    if obj.data['data'] < 20:
        eng.log.info("data < 20")
        obj.add_task_result("task_b", {'a': 12, 'b': 13, 'c': 14})
        obj.extra_data['redis_search']['category'] = "lower_than_20"
        eng.halt("Value of filed: data in object is too small.")
    else:
        obj.extra_data['redis_search']['category'] = "higher_than_20"


def add_metadata():
    def _add_metadata(obj, eng):
        if (obj['content_type'] == 'book'):
            obj.add_field("meta1", "elefant")
        else:
            obj.add_field("meta1", "hippo")

    return _add_metadata


def simple_task(times):
    def _simple_task(obj, eng):
        a = times
        while a > 0:
            obj.data -= 1
            a -= 1
        eng.log.info("value" + str(obj.data))

    return _simple_task


def sleep_task(t):
    def _sleep_task(dummy_obj, eng):
        time.sleep(t)

    return _sleep_task


def lower_than_20(obj, eng):
    """Function checks if variable is lower than 20"""
    if obj.data < 20:
        eng.halt("Value of filed: a in object is lower than 20.")


def higher_than_20(obj, eng):
    """Function checks if variable is higher than 20"""
    eng.log.info("value" + str(obj.data))
    if obj.data > 20:
        eng.halt("Value of filed: a in object is higher than 20.")


def subtract(value):
    def _subtract(obj, dummy_eng):
        """Function subtract value from variable"""
        obj.data -= value

    return _subtract


def task_a_bis(a):
    def _task_a(obj, eng):
        """Function task_a docstring"""
        obj.data += a
        eng.log.info("value" + str(obj.data))

    return _task_a


def task_b_bis(obj, eng):
    """Function task_b docstring"""
    eng.log.info("value" + str(obj.data))
    if obj.data < 20:
        obj.add_task_result("task_b", {'a': 12, 'b': 13, 'c': 14})
        eng.halt("Value of filed: data in object is too small.")


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
