# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Improved function for type conversion to int."""


def to_int(probably_a_string):
    """Helper function to convert safely a value to int.

    In case of wrong type returns a value which can be handled by JSONAlchemy.
    It helps in the situation where an integer subfield is optional.

    :param probably_a_string: A value to convert. Doesn't have to be a string.

    :return: The integer value or None in case of error.
    """
    try:
        return int(probably_a_string)
    except TypeError:
        return None
