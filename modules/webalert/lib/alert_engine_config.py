# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2010, 2011 CERN.
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

"""Invenio Alert Engine config parameters."""

__revision__ = \
    "$Id$"

# are we debugging?
# 0 = production, nothing on the console, email sent
# 1 = messages on the console, email sent
# 2 = messages on the console, no email sent
# 3 = many messages on the console, no email sent
# 4 = many messages on the console, email sent to CFG_SITE_ADMIN_EMAIL
CFG_WEBALERT_DEBUG_LEVEL = 0

