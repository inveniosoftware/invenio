# -*- coding: utf-8 -*-
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Basic simplified data test functions - NOT FOR XML."""

from functools import wraps


def task_a(a):
    """Function task_a docstring."""
    @wraps(task_a)
    def _task_a(obj, eng):
        eng.log.info("executing task a " + str(a))
        obj.data += a
    return _task_a


def task_b(obj, eng):
    """Function task_b docstring."""
    eng.log.info("executing task b")
    if obj.data < 20:
        eng.log.info("data < 20")
        obj.add_task_result("task_b", {'a': 12, 'b': 13, 'c': 14})
        eng.halt("Value of filed: data in object is too small.")
