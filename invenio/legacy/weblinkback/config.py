# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011 CERN.
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

"""WebLinkback - Configuration Parameters"""

from __future__ import unicode_literals

CFG_WEBLINKBACK_STATUS = {'APPROVED': 'approved',
                          'PENDING': 'pending',
                          'REJECTED': 'rejected',
                          'INSERTED': 'inserted',
                          'BROKEN': 'broken'}

CFG_WEBLINKBACK_TYPE = {'TRACKBACK': 'trackback',
                        'REFBACK': 'refback',
                        'PINGBACK': 'pingback'}

CFG_WEBLINKBACK_LIST_TYPE = {'WHITELIST': 'whitelist',
                             'BLACKLIST': 'blacklist'}

CFG_WEBLINKBACK_ORDER_BY_INSERTION_TIME = {'ASC': 'ASC',
                                           'DESC': 'DESC'}

CFG_WEBLINKBACK_ADMIN_MODERATION_ACTION = {'REJECT': 'reject',
                                           'APPROVE': 'approve',
                                           'INSERT': 'insert',
                                           'DELETE': 'delete'}

CFG_WEBLINKBACK_ACTION_RETURN_CODE = {'OK': 0,
                                      'INVALID_ACTION': 1,
                                      'DUPLICATE': 2,
                                      'BAD_INPUT': 3}

CFG_WEBLINKBACK_PAGE_TITLE_STATUS = {'NEW': 'n',
                                     'OLD': 'o',
                                     'MANUALLY_SET': 'm'}

CFG_WEBLINKBACK_LATEST_COUNT_VALUES = (10, 20, 50, 100, 200)
CFG_WEBLINKBACK_LATEST_COUNT_DEFAULT = 10

CFG_WEBLINKBACK_BROKEN_COUNT = 5

CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME = 'default'

CFG_WEBLINKBACK_TRACKBACK_SUBSCRIPTION_ERROR_MESSAGE= {'BAD_ARGUMENT': 'Refused: URL argument not set',
                                                       'BLACKLIST': 'Refused: URL in blacklist'}

CFG_WEBLINKBACK_DEFAULT_USER = 0

CFG_WEBLINKBACK_LATEST_FACTOR = 3

CFG_WEBLINKBACK_MAX_LINKBACKS_IN_EMAIL = 100
