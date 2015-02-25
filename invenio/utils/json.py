# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012 CERN.
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

"""JSON utilities."""

from __future__ import absolute_import
import json
CFG_JSON_AVAILABLE = True

import re
import six


def json_unicode_to_utf8(data):
    """Change all strings in a JSON structure to UTF-8."""
    if type(data) == unicode:
        return data.encode('utf-8')
    elif type(data) == dict:
        newdict = {}
        for key in data:
            newdict[json_unicode_to_utf8(key)] = json_unicode_to_utf8(data[key])
        return newdict
    elif type(data) == list:
        return [json_unicode_to_utf8(elem) for elem in data]
    else:
        return data

def json_decode_file(filename):
    """
    Parses a textfile using json to build a python object representation
    """
    seq = open(filename).read()
    ## The JSON standard has no comments syntax. We have to remove them
    ## before feeding python's JSON parser
    seq = json_remove_comments(seq)
    ## Parse all the unicode stuff to utf-8
    return json_unicode_to_utf8(json.loads(seq))

def json_remove_comments(text):
    """ Removes C style comments from the given string. Will keep newline
        characters intact. This way parsing errors from json will point to the
        right line.

        This is primarily used to make comments in JSON files possible.
        The JSON standard has no comments syntax, but we want to use
        JSON for our profiles and configuration files. The comments need to be
        removed first, before the text can be feed to the JSON parser of python.

    @param text: JSON string that should be cleaned
    @type text: string
    @return: Cleaned JSON
    @rtype: string
    """
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return ""
        else:
            return s
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, replacer, text)

def wash_for_js(text):
    """
    DEPRECATED: use htmlutils.escape_javascript_string() instead,
    and take note that returned value is no longer enclosed into
    quotes.
    """
    from invenio.utils.html import escape_javascript_string
    if isinstance(text, six.string_types):
        return '"%s"' % escape_javascript_string(text,
                                                 escape_for_html=False,
                                                 escape_CDATA=False,
                                                 escape_script_tag_with_quote=None)
    else:
        return text
