# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2013, 2015 CERN.
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

from __future__ import unicode_literals

__revision__ = "$Id$"

CFG_WEBCOMMENT_ACTION_CODE = {
    'ADD_COMMENT': 'C',
    'ADD_REVIEW': 'R',
    'VOTE': 'V',
    'REPORT_ABUSE': 'A'
}


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
