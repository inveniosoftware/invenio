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

"""Babel datetime localization template filters for Jinja.

See full documentation of corresponding methods in Flask-Babel:
https://pythonhosted.org/Flask-Babel/
"""

from flask_babel import format_date, format_datetime, format_time, \
    format_timedelta, to_user_timezone, to_utc


def filter_to_user_timezone(dt):
    """Convert a datetime object to the user's timezone."""
    return to_user_timezone(dt)


def filter_to_utc(dt):
    """Convert a datetime object to UTC and drop tzinfo."""
    return to_utc(dt)


def filter_format_datetime(dt, format=None, rebase=True):
    """Return a date formatted according to the given pattern.

    The format parameter can either be ``short``, ``medium``, ``long`` or
    ``full``.
    """
    return format_datetime(dt, format=format, rebase=rebase)


def filter_format_date(dt, format=None, rebase=True):
    """Return a date formatted according to the given pattern."""
    return format_date(dt, format=format, rebase=rebase)


def filter_format_time(dt, format=None, rebase=True):
    """Return a date formatted according to the given pattern."""
    return format_time(dt, format=format, rebase=rebase)


def filter_format_timedelta(dt, format=None, rebase=True):
    """Return a date formatted according to the given pattern."""
    return format_timedelta(dt, format=format, rebase=rebase)
