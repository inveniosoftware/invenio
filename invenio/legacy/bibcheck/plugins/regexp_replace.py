# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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

""" Bibcheck plugin to check fields against a regular expression """

import re

def check_record(record, find, replace, fields, count=0):
    """
    Replaces the occurrences of a regular expression by a string

    @param find: Regular expression to look for
    @param replace: String to substitute. Supports backreferences.
    @param fields: Fields to make the substitution on
    @param count: Maximum number of replacements to make (0 = unlimited)
    """
    for position, value in record.iterfields(fields):
        newval = re.sub(find, replace, value, count)
        record.amend_field(position, newval)

