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

import datetime


def add_data(a):
    """ Task using closure to allow parameters """
    def _add_data(obj, eng):
        """Function task_a docstring"""
        obj.data = datetime.datetime.now()
    return _add_data


def check_data(obj, eng):
    """ Static task with no parameters """
    if obj.data < 5:
        eng.haltProcessing("Value of data is too small.")


def print_data(obj, eng):
    """ Static task with no parameters """
    print obj.data + datetime.timedelta(days=2)


def set_data(obj, eng):
    """ Static task with no parameters """
    obj.data = 124
