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

def check_record(record, regexps):
    """
    Checks the record against a set of regular expressions.
    @param regexps: A dict {field: regexp}
    """
    for field, regexp in regexps.items():
        for position, value in record.iterfield(field):
            if not re.match(regexp, value):
                record.set_invalid("Field %s doesn't match regexp %s" %
                        (position[0], regexp))

