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

""" Plugin to correct and validate dates """

from datetime import datetime

try:
    from dateutil import parser
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False

def check_record(record, fields, dayfirst=True, yearfirst=False,
        date_format="%Y-%m-%d", allow_future=True,
        minimum_date=datetime(1800,1,1)):
    """
    Corrects and validates date fields

    For detailed explanation of how dayfirst and yearfirst works, visit
    http://labix.org/python-dateutil#head-b95ce2094d189a89f80f5ae52a05b4ab7b41af47

    For detailed explanation of the date_format placeholders, visit
    http://docs.python.org/2/library/datetime.html#strftime-strptime-behavior

    This plugin needs the python-dateutil library to work.

    @param dayfirst Consider the day first if ambiguous
    @type dayfirst boolean

    @param yearfirst Consider year first if ambiguous
    @type yearfirst boolean

    @param date_format normalized date format
    @type date_format string

    @param allow_future If False, dates in the future will be marked as invalid
    @type allow_future boolean

    @param minimum_date dates older than this will be rejected. Default Jan 1 1800
    @type minimum_date datetime.datetime
    """
    if not HAS_DATEUTIL:
        return

    for position, value in record.iterfields(fields):
        try:
            new_date = parser.parse(value, dayfirst=dayfirst, yearfirst=yearfirst)
        except (ValueError, TypeError):
            record.set_invalid("Non-parseable date format in field %s" % position[0])
            continue

        if not allow_future and new_date > datetime.now():
            record.set_invalid("Date in the future in field %s" % position[0])

        if new_date < minimum_date:
            record.set_invalid("Date too old (less than minimum_date) in field %s" % position[0])

        if new_date < datetime(1900, 1, 1):
            continue # strftime doesn't accept older dates

        new_date_str = new_date.strftime(date_format)
        record.amend_field(position, new_date_str)

