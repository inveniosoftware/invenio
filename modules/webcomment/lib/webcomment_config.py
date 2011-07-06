# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

# pylint: disable=C0301

"""WebComment configuration parameters."""

__revision__ = "$Id$"

# Which field of the record define email addresses that should be
# notified of newly submitted comments, and for which collection.
CFG_WEBCOMMENT_EMAIL_REPLIES_TO = \
{'Articles': ['506__d', '506__m']
}

# Which field of the record define the restriction (must be linked to
# WebAccess 'viewrestrcomment') to apply to newly submitted comments,
# and for which collection.
CFG_WEBCOMMENT_RESTRICTION_DATAFIELD = \
{'Articles': '5061_a',
 'Pictures': '5061_a',
 'Theses': '5061_a',
}

# Which field of the record define the current round of comment for
# which collection?
CFG_WEBCOMMENT_ROUND_DATAFIELD = \
{'Articles': '562__c',
 'Pictures': '562__c'
}

# Max file size per attached file, in bytes.
# Choose 0 if you don't want to limit the size
CFG_WEBCOMMENT_MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024

# Maxium number of files that can be attached per comment.
# Choose 0 if you don't want to limit the number of files.
# File uploads can be restricted with action "attachcommentfile".
CFG_WEBCOMMENT_MAX_ATTACHED_FILES = 5

# Specify how many levels of indentation discussions can be.  This can
# be used to ensure that discussions will not go into deep levels of
# nesting if users don't understand the difference between "reply to
# comment" and "add comment". When the depth is reached, any "reply to
# comment" is conceptually converted to a "reply to thread"
# (i.e. reply to this parent's comment). Use -1 for no limit, 0 for
# unthreaded (flat) discussions.
CFG_WEBCOMMENT_MAX_COMMENT_THREAD_DEPTH = 1

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
