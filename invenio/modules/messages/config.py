# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2012, 2013, 2015 CERN.
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

"""WebMessage parameters.

    webmessage config file, here you can manage error messages,
    size of messages, quotas, and some db related fields...
"""

from __future__ import unicode_literals

# from invenio.conf:

# CFG_WEBMESSAGE_MAX_SIZE_OF_MESSAGE -- how large web messages do we
# allow?
CFG_WEBMESSAGE_MAX_SIZE_OF_MESSAGE = 20000

# CFG_WEBMESSAGE_MAX_NB_OF_MESSAGES -- how many messages for a
# regular user do we allow in its inbox?
CFG_WEBMESSAGE_MAX_NB_OF_MESSAGES = 30

# CFG_WEBMESSAGE_DAYS_BEFORE_DELETE_ORPHANS -- how many days before
# we delete orphaned messages?
CFG_WEBMESSAGE_DAYS_BEFORE_DELETE_ORPHANS = 60

# from webmessage_

# status of message (table user_msgMESSAGE)
CFG_WEBMESSAGE_STATUS_CODE = \
    {
        'NEW': 'N',
        'READ': 'R',
        'REMINDER': 'M'
    }
# values indicating which results field to display while writing a message
# TODO: used only in 'master' files
CFG_WEBMESSAGE_RESULTS_FIELD = \
    {
        'USER': 'user',
        'GROUP': 'group',
        'NONE': 'none'
    }

# separator used in every list of recipients
CFG_WEBMESSAGE_SEPARATOR = ','

# list of roles (find them in accROLE table) without quota
CFG_WEBMESSAGE_ROLES_WITHOUT_QUOTA = ['superadmin']

# alert user also by email
CFG_WEBMESSAGE_EMAIL_ALERT = True
