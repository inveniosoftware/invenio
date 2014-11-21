# -*- coding: utf-8 -*-

# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

# pylint: disable=C0301

"""WebComment configuration parameters."""

__revision__ = "$Id$"

from invenio.config import CFG_CERN_SITE
from invenio.search_engine_utils import get_fieldvalues
from invenio.webuser import collect_user_info

CFG_WEBCOMMENT_ACTION_CODE = {
    'ADD_COMMENT': 'C',
    'ADD_REVIEW': 'R',
    'VOTE': 'V',
    'REPORT_ABUSE': 'A'
}

CFG_WEBCOMMENT_BODY_FORMATS = {
    "HTML": "HTML",
    "TEXT": "TXT",
    "MARKDOWN": "MD",
}

CFG_WEBCOMMENT_OUTPUT_FORMATS = {
    "HTML": {
        "WEB": "WEB",
        "EMAIL": "HTML_EMAIL",
        "CKEDITOR": "CKEDITOR",
    },
    "TEXT": {
        "EMAIL": "TEXT_EMAIL",
        "TEXTAREA": "TEXTAREA",
    },
}

# Based on CFG_WEBCOMMENT_DEADLINE_CONFIGURATION we can display, but not
# enforce comment submission deadlines. The configuration is composed of rules
# (dictionary items). For a rule to be applied in the currently displayed
# record, the dictionary key has to be in the list of values of the MARC field
# that is the first element of the tuple in that dictionary key's value. If
# that is the case, then the dealine is retrieved as the first value of the
# MARC field that is the second element of the tuple in that dictionary key's
# value. In order to programmatically check if the deadline has passed or not
# we need to know the format of the given deadline, using standard strftime
# conversion specifications <http://linux.die.net/man/3/strftime>. The deadline
# format is the third element of the tuple in that dictionary key's value.
if CFG_CERN_SITE:
    CFG_WEBCOMMENT_DEADLINE_CONFIGURATION = {
        "ATLASPUBDRAFT": (
            "980__a",
            "925__b",
            "%d %b %Y",
        )
    }
else:
    CFG_WEBCOMMENT_DEADLINE_CONFIGURATION = {
    }


def check_user_is_editor(uid, record_id, data):
    """Check if the user is editor.

    :param int uid: The user id
    :param int record_id: The record id
    :param dict data: Extra arguments
    :return: If the user is editor
    :rtype: bool

    .. note::

        The report number is been splited and wrapped with proper suffix and
        prefix for matching CERN's e-groups.

    """
    report_number_field = data.get('report_number_field')
    report_number = get_fieldvalues(record_id, report_number_field)

    if report_number:
        report_number = '-'.join(report_number[0].split('-')[1:-1])
        the_list = "{0}-{1}-{2}".format(
            data.get('prefix'), report_number.lower(), data.get('suffix')
        )
        user_info = collect_user_info(uid)
        user_lists = user_info.get('group', [])
        if the_list in user_lists:
            return True
    return False

# Based on CFG_WEBCOMMENT_USER_EDITOR we can display an extra html element
# for users which are editors. The configuration uses the the collection name
# as a key which holds a tuple with two items. The first one is the MARC field
# which holds the collection and the seccond one is a dictionary. The
# dictionary *MUST* contain a key called `callback` which holds the check
# function. The check function *MUST* have `user_id` as first argument, the
# `record_id` as second and a third which contains any other data.
# Read more `~webcomment_config.check_user_is_editor`
if CFG_CERN_SITE:
    CFG_WEBCOMMENT_EXTRA_CHECKBOX = {
        "ATLAS": (
            "980__a",
            dict(
                report_number_field="037__a",
                label="Post comment as Editor's response",
                callback=check_user_is_editor,
                prefix="atlas",
                suffix="editor [cern]",
                value="Editor response",
            )
        )
    }
else:
    CFG_WEBCOMMENT_EXTRA_CHECKBOX = {}


# Exceptions: errors
class InvenioWebCommentError(Exception):
    """A generic error for WebComment."""
    def __init__(self, message):
        """Initialisation."""
        self.message = message

    def __str__(self):
        """String representation."""
        return repr(self.message)


# Exceptions: warnings
class InvenioWebCommentWarning(Exception):
    """A generic warning for WebComment."""
    def __init__(self, message):
        """Initialisation."""
        self.message = message

    def __str__(self):
        """String representation."""
        return repr(self.message)
