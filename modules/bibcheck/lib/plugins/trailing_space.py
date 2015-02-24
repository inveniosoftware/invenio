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

""" Bibcheck plugin to fix leading/trailing spaces """

import re

def check_record(record, fields, strip=True, normalize_spaces=True):
    """
    Removes the trailing spaces (with strip=True) from the specified field's
    values, and changes multiple spaces into only one (with
    normalize_spaces=True)
    """
    for position, value in record.iterfields(fields):
        if strip:
            value = value.strip()
        if normalize_spaces:
            value = re.sub("[ ]+", " ", value)
        record.amend_field(position, value)

