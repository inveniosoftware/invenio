# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2015 CERN.
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

"""WebBasket configuration parameters."""

from __future__ import unicode_literals

__revision__ = "$Id$"

CFG_WEBBASKET_SHARE_LEVELS = {'READITM': 'RI',
                              'READCMT': 'RC',
                              'ADDCMT': 'AC',
                              'ADDITM': 'AI',
                              'DELCMT': 'DC',
                              'DELITM': 'DI',
                              'MANAGE': 'MA'}

CFG_WEBBASKET_SHARE_LEVELS_ORDERED = [CFG_WEBBASKET_SHARE_LEVELS['READITM'],
                                      CFG_WEBBASKET_SHARE_LEVELS['READCMT'],
                                      CFG_WEBBASKET_SHARE_LEVELS['ADDCMT'],
                                      CFG_WEBBASKET_SHARE_LEVELS['ADDITM'],
                                      CFG_WEBBASKET_SHARE_LEVELS['DELCMT'],
                                      CFG_WEBBASKET_SHARE_LEVELS['DELITM'],
                                      CFG_WEBBASKET_SHARE_LEVELS['MANAGE']]

# Keep in mind that the underscore ('_') is a special character. In case you
# want to define new categories, don't use the underscore ('_') anywhere in the
# value! You may use it in the key if you wish.
CFG_WEBBASKET_CATEGORIES = {'PRIVATE':      'P',
                            'GROUP':        'G',
                            'EXTERNAL':     'E',
                            'ALLPUBLIC':    'A'}

CFG_WEBBASKET_ACTIONS = {'DELETE':  'delete',
                         'UP':      'moveup',
                         'DOWN':    'movedown',
                         'COPY':    'copy',
                         'MOVE':    'move'}

# Specify how many levels of indentation discussions can be.  This can
# be used to ensure that discussions will not go into deep levels of
# nesting if users don't understand the difference between "reply to
# comment" and "add comment". When the depth is reached, any "reply to
# comment" is conceptually converted to a "reply to thread"
# (i.e. reply to this parent's comment). Use -1 for no limit, 0 for
# unthreaded (flat) discussions.
CFG_WEBBASKET_MAX_COMMENT_THREAD_DEPTH = 1

CFG_WEBBASKET_DIRECTORY_BOX_NUMBER_OF_COLUMNS = 3

CFG_WEBBASKET_MAX_NUMBER_OF_NOTES = 100
