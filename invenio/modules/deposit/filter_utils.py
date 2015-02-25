# -*- coding: utf-8 -*-
#
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA

"""WTForm filters implementation.

Filters can be applied to incoming form data, after process_formdata() has run.

See more information on:
http://wtforms.simplecodes.com/docs/1.0.4/fields.html#wtforms.fields.Field
"""

import six

from invenio.utils.html import HTMLWasher, \
    CFG_HTML_BUFFER_ALLOWED_TAG_WHITELIST


def strip_string(value):
    """Remove leading and trailing spaces from string."""
    if isinstance(value, six.string_types):
        return value.strip()
    else:
        return value


def splitlines_list(value):
    """Split string per line into a list."""
    if isinstance(value, six.string_types):
        newdata = []
        for line in value.splitlines():
            if line.strip():
                newdata.append(line.strip().encode('utf8'))
        return newdata
    else:
        return value


def splitchar_list(c):
    """Return filter function that split string per char into a list.

    :param c: Character to split on.
    """
    def _inner(value):
        """Split string per char into a list."""
        if isinstance(value, six.string_types):
            newdata = []
            for item in value.split(c):
                if item.strip():
                    newdata.append(item.strip().encode('utf8'))
            return newdata
        else:
            return value
    return _inner


def map_func(func):
    """Return filter function that map a function to each item of a list.

    :param func: Function to map.
    """
    # FIXME
    def _mapper(data):
        """Map a function to each item of a list."""
        if isinstance(data, list):
            return map(func, data)
        else:
            return data
    return _mapper


def strip_prefixes(*prefixes):
    """Return a filter function that removes leading prefixes from a string."""
    def _inner(value):
        """Remove a leading prefix from string."""
        if isinstance(value, six.string_types):
            for prefix in prefixes:
                if value.lower().startswith(prefix):
                    return value[len(prefix):]
        return value
    return _inner


def sanitize_html(allowed_tag_whitelist=CFG_HTML_BUFFER_ALLOWED_TAG_WHITELIST):
    """Sanitize HTML."""
    def _inner(value):
        if isinstance(value, six.string_types):
            washer = HTMLWasher()
            return washer.wash(value,
                               allowed_tag_whitelist=allowed_tag_whitelist)
        else:
            return value
    return _inner
