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

""" WebNews module configuration """

__revision__ = "$Id$"

# Should we generally display tooltips or not?
CFG_WEBNEWS_TOOLTIPS_DISPLAY = True

# The tooltips session param name
#CFG_WEBNEWS_TOOLTIPS_SESSION_PARAM_NAME = "has_user_seen_tooltips"

# Tooltips cookie settings
# The cookie name
CFG_WEBNEWS_TOOLTIPS_COOKIE_NAME      = "INVENIOTOOLTIPS"
# the cookie longevity in days
CFG_WEBNEWS_TOOLTIPS_COOKIE_LONGEVITY = 14
